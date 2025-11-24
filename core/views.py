"""
Views for the meal management system.

These views provide the user interface for registration, dashboard
display, meal entry, expenses, deposits, manager assignments, member
management, and settings. Permissions are enforced at the view level
using helper functions from ``services``.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
import os
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from . import forms, models, services


def register_view(request: HttpRequest) -> HttpResponse:
    """Handle new user registration.

    Creates a new user, a default mess for that user, and assigns the
    super admin role. After successful registration, the new user is
    logged in and redirected to the dashboard.
    """
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = forms.UserRegistrationForm(request.POST)
        if form.is_valid():
            user: User = form.save()
            # Create default mess for the user
            mess = models.Mess.objects.create(name=f"{user.username}'s Mess", owner=user)
            # Assign super admin role
            models.MessUser.objects.create(
                mess=mess,
                user=user,
                role=models.MessUser.ROLE_SUPER_ADMIN,
            )
            # Create a corresponding Member entry for the user
            models.Member.objects.create(mess=mess, user=user, name=user.username)
            # Authenticate and log in the user
            raw_password = form.cleaned_data.get("password1")
            authenticated_user = authenticate(username=user.username, password=raw_password)
            if authenticated_user:
                login(request, authenticated_user)
            messages.success(request, "Registration successful. Welcome!")
            return redirect("core:dashboard")
    else:
        form = forms.UserRegistrationForm()

    return render(request, "core/register.html", {"form": form})


def get_user_mess(user: User) -> Optional[models.Mess]:
    """Return the mess associated with the current user."""
    mess_user = models.MessUser.objects.filter(user=user).select_related("mess").first()
    return mess_user.mess if mess_user else None


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    """Display the main dashboard for the current mess."""
    mess = get_user_mess(request.user)
    if not mess:
        messages.error(request, "No mess associated with your account.")
        return redirect("login")

    today = date.today()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))

    data = services.calculate_dashboard(mess, year, month)

    context = {
        "mess": mess,
        "year": year,
        "month": month,
        "data": data,
        "manager_stats": data.get("manager_stats"),
        "user_is_super_admin": services.is_mess_super_admin(request.user, mess),
        "active_nav": "dashboard",
    }
    return render(request, "core/dashboard.html", context)


@login_required
def meals_view(request: HttpRequest) -> HttpResponse:
    """Add or edit meals for all members on a specific date."""
    mess = get_user_mess(request.user)
    if not mess:
        return redirect("login")

    # Determine selected date
    if request.method == "POST":
        date_str = request.POST.get("date")
    else:
        date_str = request.GET.get("date")
    try:
        selected_date = date.fromisoformat(date_str) if date_str else date.today()
    except (TypeError, ValueError):
        selected_date = date.today()

    # Permission check
    user_is_super_admin = services.is_mess_super_admin(request.user, mess)
    user_is_manager_for_date = services.is_meal_manager_for_date(request.user, mess, selected_date)
    date_not_allowed = False
    assignment_info = None

    if not user_is_super_admin and not user_is_manager_for_date:
        date_not_allowed = True

    # Fetch assignment info for the user (most recent assignment covering date)
    if user_is_manager_for_date:
        assignment_info = (
            mess.manager_assignments.filter(
                manager_user=request.user,
                start_date__lte=selected_date,
                end_date__gte=selected_date,
            )
            .order_by("-start_date")
            .first()
        )

    # Build members meal data (with default pattern support)
    members = mess.members.filter(is_active=True)
    members_meals = []
    existing_meals = {
        m.member_id: m
        for m in mess.meals.filter(date=selected_date, member__in=members)
    }

    for member in members:
        meal = existing_meals.get(member.id)

        if meal:
            # Use existing record
            had_breakfast = meal.had_breakfast
            had_lunch = meal.had_lunch
            had_dinner = meal.had_dinner
            extra = meal.extra_meals
        else:
            # Use default pattern from Member (if defined)
            pattern = getattr(member, "default_meal_pattern", "NONE") or "NONE"
            had_breakfast = "B" in pattern
            had_lunch = "L" in pattern
            had_dinner = "D" in pattern
            extra = 0

        members_meals.append(
            {
                "member": member,
                "had_breakfast": had_breakfast,
                "had_lunch": had_lunch,
                "had_dinner": had_dinner,
                "extra_meals": extra,
            }
        )

    # Recent history (last 7 days up to selected_date) - grouped by date
    history_start = selected_date - timedelta(days=6)
    history_qs = (
        mess.meals.filter(
            date__range=(history_start, selected_date),
            member__is_active=True,
        )
        .select_related("member")
        .order_by("-date", "member__name")
    )

    date_stats: dict[date, dict] = {}

    for meal in history_qs:
        d = meal.date
        if d not in date_stats:
            date_stats[d] = {
                "date": d,
                "member_count": 0,
                "breakfast_count": 0,
                "lunch_count": 0,
                "dinner_count": 0,
                "total_extra_meals": Decimal("0"),
                "total_meals": Decimal("0"),
                "seen_members": set(),
            }

        stats = date_stats[d]

        # count unique members
        if meal.member_id not in stats["seen_members"]:
            stats["seen_members"].add(meal.member_id)
            stats["member_count"] += 1

        if meal.had_breakfast:
            stats["breakfast_count"] += 1
            if mess.include_breakfast:
                stats["total_meals"] += mess.breakfast_weight

        if meal.had_lunch:
            stats["lunch_count"] += 1
            stats["total_meals"] += Decimal("1")

        if meal.had_dinner:
            stats["dinner_count"] += 1
            stats["total_meals"] += Decimal("1")

        stats["total_extra_meals"] += meal.extra_meals
        stats["total_meals"] += meal.extra_meals

    recent_meals = [
        {
            "date": s["date"],
            "member_count": s["member_count"],
            "breakfast_count": s["breakfast_count"],
            "lunch_count": s["lunch_count"],
            "dinner_count": s["dinner_count"],
            "total_extra_meals": s["total_extra_meals"],
            "total_meals": s["total_meals"],
        }
        for _, s in sorted(date_stats.items(), key=lambda x: x[0], reverse=True)
    ]

    # Save on POST (if allowed)
    if request.method == "POST" and not date_not_allowed:
        for member in members:
            prefix = f"member_{member.id}_"
            had_breakfast = bool(request.POST.get(prefix + "breakfast"))
            had_lunch = bool(request.POST.get(prefix + "lunch"))
            had_dinner = bool(request.POST.get(prefix + "dinner"))
            try:
                extra_meals_value = request.POST.get(prefix + "extra", "0")
                extra_meals = Decimal(str(extra_meals_value))
            except Exception:
                extra_meals = Decimal("0")

            meal_obj, created = models.Meal.objects.get_or_create(
                mess=mess,
                member=member,
                date=selected_date,
                defaults={
                    "had_breakfast": had_breakfast,
                    "had_lunch": had_lunch,
                    "had_dinner": had_dinner,
                    "extra_meals": extra_meals,
                },
            )
            if not created:
                meal_obj.had_breakfast = had_breakfast
                meal_obj.had_lunch = had_lunch
                meal_obj.had_dinner = had_dinner
                meal_obj.extra_meals = extra_meals
                meal_obj.save()

        messages.success(request, "Meals saved successfully.")
        return redirect(f"/meals/add/?date={selected_date.isoformat()}")

    context = {
        "selected_date": selected_date,
        "members_meals": members_meals,
        "assignment_info": assignment_info,
        "date_not_allowed": date_not_allowed,
        "user_is_super_admin": user_is_super_admin,
        "recent_meals": recent_meals,
        "today": date.today(),  # for max attribute in date input
        "active_nav": "meals",
    }
    return render(request, "core/meals_form.html", context)


@login_required
def expense_view(request: HttpRequest) -> HttpResponse:
    """Record a new meal-related expense and show recent daily totals."""
    mess = get_user_mess(request.user)
    if not mess:
        return redirect('login')
    if not services.is_mess_super_admin(request.user, mess):
        return HttpResponseForbidden('You do not have permission to add expenses.')

    if request.method == 'POST':
        form = forms.ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.mess = mess
            expense.save()
            messages.success(request, 'Expense recorded.')
            return redirect('core:expense_add')
    else:
        form = forms.ExpenseForm()
        form.fields['paid_by_member'].queryset = mess.members.filter(is_active=True)

    # 🔹 Recent expenses grouped by date (latest first)
    expense_qs = (
        models.Expense.objects.filter(mess=mess)
        .order_by('-date')[:200]  # limit to avoid huge table
    )

    date_totals: dict[date, Decimal] = {}
    for exp in expense_qs:
        d = exp.date
        if d not in date_totals:
            date_totals[d] = Decimal("0")
        date_totals[d] += exp.amount

    recent_expense_days = [
        {"date": d, "total_amount": total}
        for d, total in sorted(date_totals.items(), key=lambda x: x[0], reverse=True)
    ]

    context = {
        'form': form,
        'recent_expense_days': recent_expense_days,
        'active_nav': 'expenses',
    }
    return render(request, 'core/expense_form.html', context)


@login_required
def deposit_view(request: HttpRequest) -> HttpResponse:
    """Record a deposit from a member and show recent daily totals."""
    mess = get_user_mess(request.user)
    if not mess:
        return redirect('login')
    if not services.is_mess_super_admin(request.user, mess):
        return HttpResponseForbidden('You do not have permission to add deposits.')

    if request.method == 'POST':
        form = forms.DepositForm(request.POST)
        if form.is_valid():
            deposit = form.save(commit=False)
            deposit.mess = mess
            deposit.save()
            messages.success(request, 'Deposit recorded.')
            return redirect('core:deposit_add')
    else:
        form = forms.DepositForm()
        form.fields['member'].queryset = mess.members.filter(is_active=True)

    # 🔹 Recent deposits grouped by date with depositor names
    deposit_qs = (
        models.Deposit.objects.filter(mess=mess)
        .select_related('member')
        .order_by('-date')[:200]
    )

    date_stats: dict[date, dict] = {}

    for dep in deposit_qs:
        d = dep.date
        if d not in date_stats:
            date_stats[d] = {
                "date": d,
                "total_amount": Decimal("0"),
                "members": set(),
            }
        stats = date_stats[d]
        stats["total_amount"] += dep.amount
        if dep.member:
            stats["members"].add(dep.member.name)

    recent_deposit_days = [
        {
            "date": s["date"],
            "total_amount": s["total_amount"],
            "members_str": ", ".join(sorted(s["members"])) if s["members"] else "—",
        }
        for _, s in sorted(date_stats.items(), key=lambda x: x[0], reverse=True)
    ]

    context = {
        'form': form,
        'recent_deposit_days': recent_deposit_days,
        'active_nav': 'deposits',
    }
    return render(request, 'core/deposit_form.html', context)


@login_required
def settings_view(request: HttpRequest) -> HttpResponse:
    """View and edit mess settings (breakfast rules)."""
    mess = get_user_mess(request.user)
    if not mess:
        return redirect("login")
    if not services.is_mess_super_admin(request.user, mess):
        return HttpResponseForbidden("You do not have permission to edit settings.")

    if request.method == "POST":
        include_breakfast = bool(request.POST.get("include_breakfast"))
        mess.include_breakfast = include_breakfast
        weight_str = request.POST.get("breakfast_weight", "0.5")
        try:
            mess.breakfast_weight = Decimal(str(weight_str))
        except Exception:
            # ignore invalid input and keep previous value
            pass
        mess.save()
        messages.success(request, "Settings updated.")
        return redirect("core:settings")

    context = {
        "mess": mess,
        "active_nav": "settings",
    }
    return render(request, "core/settings.html", context)


@login_required
def manager_assignments_view(request: HttpRequest) -> HttpResponse:
    """View and create meal manager assignments."""
    mess = get_user_mess(request.user)
    if not mess:
        return redirect("login")
    if not services.is_mess_super_admin(request.user, mess):
        return HttpResponseForbidden("You do not have permission to manage assignments.")

    if request.method == "POST":
        form = forms.MealManagerAssignmentForm(request.POST)
        form.fields["manager_user"].queryset = User.objects.filter(
            mess_roles__mess=mess
        ).distinct()
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.mess = mess
            period_choice = form.cleaned_data["period_choice"]

            if period_choice.endswith("week") or period_choice.endswith("weeks"):
                assignment.assignment_type = (
                    models.MealManagerAssignment.ASSIGNMENT_TYPE_WEEK
                )
            elif period_choice.endswith("days"):
                assignment.assignment_type = (
                    models.MealManagerAssignment.ASSIGNMENT_TYPE_DAYS
                )
            else:
                assignment.assignment_type = (
                    models.MealManagerAssignment.ASSIGNMENT_TYPE_CUSTOM
                )

            assignment.period_choice = period_choice
            assignment.created_by = request.user
            assignment.save()
            messages.success(request, "Assignment created.")
            return redirect("core:manager_assignments")
    else:
        form = forms.MealManagerAssignmentForm()
        form.fields["manager_user"].queryset = User.objects.filter(
            mess_roles__mess=mess
        ).distinct()
        form.fields["start_date"].initial = date.today()

    assignments = mess.manager_assignments.all()

    context = {
        "form": form,
        "assignments": assignments,
        "active_nav": "managers",
    }
    return render(request, "core/manager_assignments.html", context)


@login_required
def members_view(request: HttpRequest) -> HttpResponse:
    """List members of the current mess."""
    mess = get_user_mess(request.user)
    if not mess:
        return redirect("login")
    if not services.is_mess_super_admin(request.user, mess):
        return HttpResponseForbidden("You do not have permission to view members.")

    members = mess.members.all().order_by("name")

    context = {
        "members": members,
        "active_nav": "members",
    }
    return render(request, "core/members.html", context)

from django.conf import settings
from django.http import HttpResponse

# ... keep your other imports & views ...


@login_required
def bootstrap_superuser_view(request: HttpRequest) -> HttpResponse:
    """
    ONE-TIME helper view to create an initial superuser + mess + member
    on Render when you don't have shell access.

    Protect it with a secret token in the URL, then delete it after use.
    """
    # Simple protection: require ?token=... in the URL
    token_from_url = request.GET.get("token")
    expected_token = os.environ.get("BOOTSTRAP_TOKEN", "changeme")

    if token_from_url != expected_token:
        return HttpResponse("Invalid or missing token.", status=403)

    from django.contrib.auth.models import User
    from . import models

    # If any superuser already exists, don't create another
    if User.objects.filter(is_superuser=True).exists():
        return HttpResponse("Superuser already exists. Nothing to do.")

    # Create a superuser
    username = "admin"
    password = "Admin12345"  # you can change this, but remember it
    user = User.objects.create_superuser(
        username=username,
        email="admin@example.com",
        password=password,
    )

    # Create a default mess
    mess = models.Mess.objects.create(
        name=f"{username}'s Mess",
        owner=user,
    )

    # Link as super admin
    models.MessUser.objects.create(
        mess=mess,
        user=user,
        role=models.MessUser.ROLE_SUPER_ADMIN,
    )

    # Create a Member entry for this user
    models.Member.objects.create(
        mess=mess,
        user=user,
        name=user.username,
    )

    return HttpResponse(
        f"Bootstrap done. Superuser created: username='{superadmin}', password='{123456}'. "
        "Now log in at /admin/ and then DELETE this view + URL."
    )

@login_required
def member_detail_view(request: HttpRequest, member_id: int) -> HttpResponse:
    """Show detailed meal and deposit history for a single member in the current mess."""
    mess = get_user_mess(request.user)
    if not mess:
        return redirect("login")

    member = get_object_or_404(models.Member, id=member_id, mess=mess)

    # Permissions: super admin OR the member themself (if linked to user)
    if not services.is_mess_super_admin(request.user, mess):
        if not (member.user and member.user == request.user):
            return HttpResponseForbidden(
                "You are not allowed to view this member's details."
            )

    # Meals history for this member (all dates, latest first)
    meal_qs = models.Meal.objects.filter(mess=mess, member=member).order_by("-date")

    meal_rows = []
    total_meals_sum = Decimal("0")

    for meal in meal_qs:
        total = Decimal("0")
        if mess.include_breakfast and meal.had_breakfast:
            total += mess.breakfast_weight
        if meal.had_lunch:
            total += Decimal("1")
        if meal.had_dinner:
            total += Decimal("1")
        total += meal.extra_meals

        total_meals_sum += total

        meal_rows.append(
            {
                "date": meal.date,
                "had_breakfast": meal.had_breakfast,
                "had_lunch": meal.had_lunch,
                "had_dinner": meal.had_dinner,
                "extra_meals": meal.extra_meals,
                "total_meals": total,
            }
        )

    # Deposit history for this member (all dates, latest first)
    deposit_qs = mess.deposits.filter(member=member).order_by("-date")

    deposit_rows = []
    total_deposit_sum = Decimal("0")

    for dep in deposit_qs:
        total_deposit_sum += dep.amount
        deposit_rows.append(
            {
                "date": dep.date,
                "amount": dep.amount,
                "note": getattr(dep, "note", ""),
            }
        )

    context = {
        "mess": mess,
        "member": member,
        "meals": meal_rows,
        "deposits": deposit_rows,
        "total_meals": total_meals_sum,
        "total_deposits": total_deposit_sum,
        "active_nav": "members",
    }
    return render(request, "core/member_detail.html", context)


@login_required
def member_add_view(request: HttpRequest) -> HttpResponse:
    """Add a new member to the mess."""
    mess = get_user_mess(request.user)
    if not mess:
        return redirect("login")
    if not services.is_mess_super_admin(request.user, mess):
        return HttpResponseForbidden("You do not have permission to add members.")

    if request.method == "POST":
        form = forms.MemberForm(request.POST)
        if form.is_valid():
            member = form.save(commit=False)
            member.mess = mess
            member.save()
            messages.success(request, "Member added.")
            return redirect("core:members")
    else:
        form = forms.MemberForm()
        form.fields["user"].queryset = User.objects.exclude(mess_roles__mess=mess)

    context = {
        "form": form,
        "active_nav": "members",
    }
    return render(request, "core/member_form.html", context)
