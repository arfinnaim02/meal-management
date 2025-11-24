"""
Service layer for meal calculation and permission checks.

Centralizes business logic that shouldn't live in views or models,
including dashboard calculations, role checking, and manager stats.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from calendar import monthrange
from collections import defaultdict

from django.db.models import Sum, Q

from .models import Mess, Member, Meal, Expense, Deposit, MealManagerAssignment, MessUser


def get_month_date_range(year: int, month: int) -> tuple[date, date]:
    """Return the first and last day of the given month."""
    _, last_day = monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)
    return start_date, end_date


def calculate_dashboard(mess: Mess, year: int, month: int) -> dict[str, object]:
    """Compute dashboard summary, member balances and manager stats.

    Args:
        mess: The mess instance to summarize.
        year: The year of the summary period.
        month: The month of the summary period (1–12).

    Returns:
        A dictionary with ``summary``, ``members`` and ``manager_stats`` keys.
    """
    start_date, end_date = get_month_date_range(year, month)

    # Fetch totals for expenses and deposits in the period
    total_expense = mess.expenses.filter(date__range=(start_date, end_date)).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_collected = mess.deposits.filter(date__range=(start_date, end_date)).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Active members
    members_qs = mess.members.filter(is_active=True)

    # Pre-compute meal counts per member and overall
    include_breakfast = mess.include_breakfast
    breakfast_weight = mess.breakfast_weight if include_breakfast else Decimal('0')

    meal_entries = mess.meals.filter(date__range=(start_date, end_date), member__in=members_qs).select_related('member')
    meals_per_member: dict[int, Decimal] = defaultdict(lambda: Decimal('0'))
    total_meals_all = Decimal('0')

    for meal in meal_entries:
        meals_for_entry = (
            (breakfast_weight if meal.had_breakfast else Decimal('0')) +
            (Decimal('1') if meal.had_lunch else Decimal('0')) +
            (Decimal('1') if meal.had_dinner else Decimal('0')) +
            (meal.extra_meals or Decimal('0'))
        )
        meals_per_member[meal.member_id] += meals_for_entry
        total_meals_all += meals_for_entry

    # Meal rate
    meal_rate: Decimal = Decimal('0')
    if total_meals_all > 0:
        meal_rate = (total_expense / total_meals_all).quantize(Decimal('0.01'))

    # Deposits per member
    deposits_per_member = mess.deposits.filter(date__range=(start_date, end_date)).values('member_id').annotate(total=Sum('amount'))
    deposits_map: dict[int, Decimal] = {row['member_id']: row['total'] or Decimal('0') for row in deposits_per_member}

    # Build member rows
    member_rows = []
    for member in members_qs:
        total_meals = meals_per_member.get(member.id, Decimal('0'))
        meal_cost = (total_meals * meal_rate).quantize(Decimal('0.01'))
        deposited = deposits_map.get(member.id, Decimal('0'))
        net = (deposited - meal_cost).quantize(Decimal('0.01'))
        status = 'due' if net < 0 else 'advance' if net > 0 else 'settled'
        member_rows.append({
            'id': member.id,
            'name': member.name,
            'meals': float(total_meals),
            'meal_cost': float(meal_cost),
            'deposited': float(deposited),
            'net': float(net),
            'status': status,
        })

    # Mess-level balance
    mess_balance = (total_collected - total_expense).quantize(Decimal('0.01'))

    # Manager stats: count total days managed per user
    manager_stats_list = []
    assignments = mess.manager_assignments.all().select_related('manager_user', 'manager_member')
    manager_data: dict[int, dict[str, object]] = {}
    for assignment in assignments:
        user_id = assignment.manager_user_id
        data = manager_data.setdefault(user_id, {
            'name': assignment.manager_member.name if assignment.manager_member else assignment.manager_user.username,
            'total_days': 0,
            'assignment_count': 0,
            'last_start': assignment.start_date,
            'last_end': assignment.end_date,
        })
        data['total_days'] += assignment.total_days
        data['assignment_count'] += 1
        # Update last period if this is more recent
        if assignment.start_date > data['last_start']:
            data['last_start'] = assignment.start_date
            data['last_end'] = assignment.end_date
    for data in manager_data.values():
        manager_stats_list.append({
            'name': data['name'],
            'total_days': data['total_days'],
            'assignment_count': data['assignment_count'],
            'last_start': data['last_start'],
            'last_end': data['last_end'],
        })

    return {
        'summary': {
            'year': year,
            'month': month,
            'total_meals': float(total_meals_all),
            'total_expense': float(total_expense),
            'total_collected': float(total_collected),
            'meal_rate': float(meal_rate),
            'mess_balance': float(mess_balance),
            'active_members': members_qs.count(),
            'include_breakfast': include_breakfast,
            'breakfast_weight': float(breakfast_weight),
        },
        'members': member_rows,
        'manager_stats': manager_stats_list,
    }


def is_mess_super_admin(user, mess: Mess) -> bool:
    """Return True if the user is a super admin for the given mess."""
    return MessUser.objects.filter(mess=mess, user=user, role=MessUser.ROLE_SUPER_ADMIN).exists()


def is_meal_manager_for_date(user, mess: Mess, target_date: date) -> bool:
    """Check if the user is assigned as meal manager for the given date."""
    return MealManagerAssignment.objects.filter(
        mess=mess,
        manager_user=user,
        start_date__lte=target_date,
        end_date__gte=target_date,
    ).exists()