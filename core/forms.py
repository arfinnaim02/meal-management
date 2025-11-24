"""
Forms for the meal management system.

Provide Django ``ModelForm`` classes for creating and editing
expenses, deposits, members, and meal manager assignments. The forms
leverage Django’s built-in validation and widget rendering.
"""

from __future__ import annotations

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from . import models


class UserRegistrationForm(UserCreationForm):
    """A simple user registration form.

    Extends Django's built-in ``UserCreationForm`` by adding a field
    for the user's email address. All fields are required.
    """

    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class MemberForm(forms.ModelForm):
    """Form for creating and editing members."""

    class Meta:
        model = models.Member
        fields = ['name', 'phone', 'user', 'is_active', 'default_meal_pattern']
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded-lg'}),
        }


class ExpenseForm(forms.ModelForm):
    """Form for recording a meal-related expense."""

    class Meta:
        model = models.Expense
        fields = ['date', 'amount', 'category', 'paid_by_member', 'note']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'border rounded-lg px-3 py-2 w-full'}),
            'amount': forms.NumberInput(attrs={'class': 'border rounded-lg px-3 py-2 w-full', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'border rounded-lg px-3 py-2 w-full'}),
            'paid_by_member': forms.Select(attrs={'class': 'border rounded-lg px-3 py-2 w-full'}),
            'note': forms.TextInput(attrs={'class': 'border rounded-lg px-3 py-2 w-full'}),
        }


class DepositForm(forms.ModelForm):
    """Form for recording a deposit of funds by a member."""

    class Meta:
        model = models.Deposit
        fields = ['date', 'member', 'amount', 'method', 'note']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'border rounded-lg px-3 py-2 w-full'}),
            'amount': forms.NumberInput(attrs={'class': 'border rounded-lg px-3 py-2 w-full', 'step': '0.01'}),
            'member': forms.Select(attrs={'class': 'border rounded-lg px-3 py-2 w-full'}),
            'method': forms.TextInput(attrs={'class': 'border rounded-lg px-3 py-2 w-full'}),
            'note': forms.TextInput(attrs={'class': 'border rounded-lg px-3 py-2 w-full'}),
        }


class MealManagerAssignmentForm(forms.ModelForm):
    """Form for assigning a meal manager to a date range."""

    PERIOD_CHOICES = [
        ('1_week', '1 Week'),
        ('2_weeks', '2 Weeks'),
        ('3_weeks', '3 Weeks'),
        ('4_weeks', '4 Weeks'),
        ('15_days', '15 Days'),
        ('30_days', '30 Days'),
        ('custom', 'Custom'),
    ]

    period_choice = forms.ChoiceField(
        choices=PERIOD_CHOICES,
        initial='1_week',
        help_text='Select a preset period or choose custom.',
        widget=forms.Select(attrs={'class': 'border rounded-lg px-3 py-2 w-full'}),
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'border rounded-lg px-3 py-2 w-full'}),
    )

    class Meta:
        model = models.MealManagerAssignment
        fields = ['manager_user', 'period_choice', 'start_date', 'end_date']
        widgets = {
            'manager_user': forms.Select(attrs={'class': 'border rounded-lg px-3 py-2 w-full'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'border rounded-lg px-3 py-2 w-full'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        period_choice = cleaned_data.get('period_choice')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if not start_date:
            return cleaned_data
        # Determine end_date if not provided and preset selected
        if period_choice != 'custom' and not end_date:
            from datetime import timedelta
            if period_choice.endswith('_week'):
                weeks = int(period_choice.split('_')[0])
                end_date = start_date + timedelta(days=7 * weeks - 1)
            elif period_choice.endswith('_weeks'):
                weeks = int(period_choice.split('_')[0])
                end_date = start_date + timedelta(days=7 * weeks - 1)
            elif period_choice.endswith('_days'):
                days = int(period_choice.split('_')[0])
                end_date = start_date + timedelta(days=days - 1)
            cleaned_data['end_date'] = end_date
        # Validate end_date must not be before start_date
        if end_date and end_date < start_date:
            raise forms.ValidationError('End date cannot be before start date.')
        return cleaned_data