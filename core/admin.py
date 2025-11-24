"""
Admin configuration for the core app.

Registers models with the Django admin site and provides basic
list-display options for easier management from the admin interface.
"""

from __future__ import annotations

from django.contrib import admin

from . import models


@admin.register(models.Mess)
class MessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'include_breakfast', 'breakfast_weight', 'created_at')
    list_filter = ('include_breakfast',)


@admin.register(models.MessUser)
class MessUserAdmin(admin.ModelAdmin):
    list_display = ('mess', 'user', 'role')
    list_filter = ('role',)


@admin.register(models.Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'mess', 'phone', 'is_active', 'created_at')
    list_filter = ('mess', 'is_active')
    search_fields = ('name', 'phone')


@admin.register(models.Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ('member', 'date', 'had_breakfast', 'had_lunch', 'had_dinner', 'extra_meals')
    list_filter = ('mess', 'date')
    search_fields = ('member__name',)


@admin.register(models.Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('date', 'mess', 'amount', 'category', 'paid_by_member', 'note')
    list_filter = ('mess', 'category')
    search_fields = ('note',)


@admin.register(models.Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('date', 'mess', 'member', 'amount', 'method')
    list_filter = ('mess', 'method')
    search_fields = ('member__name',)


@admin.register(models.MealManagerAssignment)
class MealManagerAssignmentAdmin(admin.ModelAdmin):
    list_display = ('mess', 'manager_user', 'start_date', 'end_date', 'assignment_type', 'period_choice')
    list_filter = ('mess', 'assignment_type')
    search_fields = ('manager_user__username', 'manager_member__name')