from datetime import date

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

INPUT = "w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-500"


class SearchForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": INPUT}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": INPUT}))
    seats = forms.IntegerField(
        min_value=1, max_value=12, initial=4,
        widget=forms.NumberInput(attrs={"class": INPUT}),
    )

    def clean(self):
        data = super().clean()
        start, end = data.get("start_date"), data.get("end_date")
        if start and end:
            if start < date.today():
                raise forms.ValidationError("Start date cannot be in the past.")
            if end < start:
                raise forms.ValidationError("End date cannot be before the start date.")
        return data


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class DriverForm(forms.Form):
    driver_name = forms.CharField(
        max_length=100, label="Driver full name",
        widget=forms.TextInput(attrs={"class": INPUT}),
    )
    driver_dob = forms.DateField(
        label="Date of birth",
        widget=forms.DateInput(attrs={"type": "date", "class": INPUT}),
    )
    driver_license = forms.CharField(
        max_length=30, label="Driving license number",
        widget=forms.TextInput(attrs={"class": INPUT}),
    )
    agree = forms.BooleanField(
        label="I agree to the rental terms and conditions",
        error_messages={"required": "You must accept the terms to book."},
    )

    def clean_driver_dob(self):
        dob = self.cleaned_data["driver_dob"]
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise forms.ValidationError("Driver must be at least 18 years old.")
        return dob
