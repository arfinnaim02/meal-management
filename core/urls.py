"""
URL routes for the core application.

Maps endpoint names to view callables, providing a clean separation
between URL configuration and business logic. Most views require
authentication to protect sensitive operations.
"""

from __future__ import annotations

from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views


app_name = 'core'

urlpatterns = [
    # Dashboard
    path('', login_required(views.dashboard_view), name='dashboard'),
    # Meals CRUD
    path('meals/add/', login_required(views.meals_view), name='meals_add'),
    # Expenses
    path('expenses/add/', login_required(views.expense_view), name='expense_add'),
    # Deposits
    path('deposits/add/', login_required(views.deposit_view), name='deposit_add'),
    # Members (super admin)
    path('members/', login_required(views.members_view), name='members'),
    path('members/add/', login_required(views.member_add_view), name='member_add'),
    # Manager assignments
    path('managers/', login_required(views.manager_assignments_view), name='manager_assignments'),
    # Settings
    path('settings/', login_required(views.settings_view), name='settings'),
    path("members/<int:member_id>/", views.member_detail_view, name="member_detail"),
    path("bootstrap-superuser/", views.bootstrap_superuser_view, name="bootstrap_superuser"),

]
