"""
Database models for the meal management system.

These models capture the state of messes, members, meals, expenses,
deposits, and the assignment of meal managers to particular date
ranges. Most of the heavy lifting (calculations) is performed by the
services module.
"""

from __future__ import annotations

from decimal import Decimal
from datetime import date

from django.conf import settings
from django.db import models


class Mess(models.Model):
    """Represents a mess (household) that tracks meals and expenses."""

    name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_messes',
    )
    currency = models.CharField(max_length=10, default='BDT')
    include_breakfast = models.BooleanField(default=True)
    breakfast_weight = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.50'))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class MessUser(models.Model):
    """Associates users with messes and assigns a role within each mess."""

    ROLE_SUPER_ADMIN = 'super_admin'
    ROLE_MANAGER = 'manager'
    ROLE_MEMBER = 'member'
    ROLE_CHOICES = [
        (ROLE_SUPER_ADMIN, 'Super Admin'),
        (ROLE_MANAGER, 'Meal Manager'),
        (ROLE_MEMBER, 'Member'),
    ]

    mess = models.ForeignKey(Mess, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mess_roles')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)

    class Meta:
        unique_together = ('mess', 'user')

    def __str__(self) -> str:
        return f"{self.user.username} – {self.role} @ {self.mess.name}"


class Member(models.Model):
    """Represents a boarder (member) within a mess.

    Each member may optionally be linked to a Django user account. This
    model is used to track meal and financial data on a per-person basis.
    """

    # NEW FIELD (Your requirement)
    DEFAULT_MEAL_CHOICES = [
        ("NONE", "No default"),
        ("B", "Breakfast only"),
        ("L", "Lunch only"),
        ("D", "Dinner only"),
        ("BL", "Breakfast + Lunch"),
        ("LD", "Lunch + Dinner"),
        ("BD", "Breakfast + Dinner"),
        ("BLD", "Breakfast + Lunch + Dinner"),
    ]

    mess = models.ForeignKey(Mess, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='member_profiles',
    )
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Added Field
    default_meal_pattern = models.CharField(
        max_length=10,
        choices=DEFAULT_MEAL_CHOICES,
        default="NONE",
    )

    class Meta:
        unique_together = ('mess', 'name')

    def __str__(self) -> str:
        return f"{self.name} ({self.mess.name})"


class Meal(models.Model):
    """Records the meals consumed by a member on a given date."""

    mess = models.ForeignKey(Mess, on_delete=models.CASCADE, related_name='meals')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='meals')
    date = models.DateField()
    had_breakfast = models.BooleanField(default=False)
    had_lunch = models.BooleanField(default=False)
    had_dinner = models.BooleanField(default=False)
    extra_meals = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        unique_together = ('mess', 'member', 'date')
        ordering = ['date']

    def __str__(self) -> str:
        return f"{self.member} on {self.date}"


class Expense(models.Model):
    """Represents a meal-related expense (bazar purchase)."""

    CATEGORY_RICE = 'rice'
    CATEGORY_MEAT = 'meat'
    CATEGORY_VEG = 'veg'
    CATEGORY_FISH = 'fish'
    CATEGORY_OTHER = 'other'

    CATEGORY_CHOICES = [
        (CATEGORY_RICE, 'Rice'),
        (CATEGORY_MEAT, 'Meat'),
        (CATEGORY_VEG, 'Vegetables'),
        (CATEGORY_FISH, 'Fish'),
        (CATEGORY_OTHER, 'Other'),
    ]

    mess = models.ForeignKey(Mess, on_delete=models.CASCADE, related_name='expenses')
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_OTHER)
    paid_by_member = models.ForeignKey(
        Member,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='paid_expenses',
    )
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Expense {self.amount} on {self.date} ({self.get_category_display()})"


class Deposit(models.Model):
    """Represents a deposit of money by a member into the mess fund."""

    mess = models.ForeignKey(Mess, on_delete=models.CASCADE, related_name='deposits')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='deposits')
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50, blank=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Deposit {self.amount} by {self.member} on {self.date}"


class MealManagerAssignment(models.Model):
    """Tracks periods where a user is assigned to manage meals."""

    ASSIGNMENT_TYPE_WEEK = 'week'
    ASSIGNMENT_TYPE_DAYS = 'days'
    ASSIGNMENT_TYPE_CUSTOM = 'custom'

    ASSIGNMENT_TYPE_CHOICES = [
        (ASSIGNMENT_TYPE_WEEK, 'Week-based'),
        (ASSIGNMENT_TYPE_DAYS, 'Day-based'),
        (ASSIGNMENT_TYPE_CUSTOM, 'Custom'),
    ]

    mess = models.ForeignKey(Mess, on_delete=models.CASCADE, related_name='manager_assignments')
    manager_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='meal_manager_assignments',
    )
    manager_member = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='manager_assignments',
    )
    assignment_type = models.CharField(max_length=10, choices=ASSIGNMENT_TYPE_CHOICES)
    period_choice = models.CharField(max_length=20, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_manager_assignments',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self) -> str:
        manager_name = self.manager_member.name if self.manager_member else self.manager_user.username
        return f"{manager_name}: {self.start_date} → {self.end_date}"

    @property
    def total_days(self) -> int:
        return (self.end_date - self.start_date).days + 1
