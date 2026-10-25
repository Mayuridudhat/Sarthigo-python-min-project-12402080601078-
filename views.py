from datetime import date

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import DriverForm, SearchForm, SignupForm
from .models import Booking, Car


def available_cars(start, end, seats):
    """Cars with enough seats and no approved booking overlapping start..end."""
    busy = Booking.objects.filter(
        is_approved=True, start_date__lte=end, end_date__gte=start
    ).values_list("car_id", flat=True)
    return Car.objects.filter(capacity__gte=seats).exclude(id__in=busy)


def calc_total(car, start, end):
    days = (end - start).days + 1  # start and end day both count
    return car.price_per_day * days, days


def home(request):
    form = SearchForm(request.GET or None)
    if request.GET and form.is_valid():
        d = form.cleaned_data
        return redirect(
            f"/cars/?start_date={d['start_date']}&end_date={d['end_date']}&seats={d['seats']}"
        )
    return render(request, "rentals/home.html", {"form": form, "today": date.today()})


def car_list(request):
    form = SearchForm(request.GET)
    if not form.is_valid():
        # Server checks the dates again, even though JavaScript already did.
        for error in form.errors.values():
            for e in error:
                messages.error(request, e)
        return redirect("home")
    d = form.cleaned_data
    cars = available_cars(d["start_date"], d["end_date"], d["seats"])
    days = (d["end_date"] - d["start_date"]).days + 1
    rows = [{"car": c, "total": c.price_per_day * days} for c in cars]
    return render(request, "rentals/car_list.html", {"rows": rows, "days": days, **d})


@login_required
def confirm_booking(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    search = SearchForm(request.GET)
    if not search.is_valid():
        messages.error(request, "Please choose your dates again.")
        return redirect("home")
    start, end = search.cleaned_data["start_date"], search.cleaned_data["end_date"]

    if not available_cars(start, end, 1).filter(id=car.id).exists():
        messages.error(request, "Sorry, that car was just booked for those dates.")
        return redirect("home")

    total, days = calc_total(car, start, end)
    form = DriverForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        booking = Booking.objects.create(
            user=request.user, car=car, start_date=start, end_date=end,
            total_cost=total, driver_name=d["driver_name"],
            driver_dob=d["driver_dob"], driver_license=d["driver_license"],
        )
        return redirect("booking_success", booking_id=booking.id)

    return render(request, "rentals/confirm_booking.html", {
        "car": car, "form": form, "start": start, "end": end,
        "days": days, "total": total,
    })


@login_required
def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, "rentals/booking_success.html", {"booking": booking})


@login_required
def my_bookings(request):
    bookings = request.user.bookings.select_related("car")
    return render(request, "rentals/my_bookings.html", {"bookings": bookings})


def register(request):
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome to SarthiGo! Your account is ready.")
        return redirect("home")
    return render(request, "rentals/register.html", {"form": form})


def staff_only(view):
    return user_passes_test(lambda u: u.is_active and u.is_staff, login_url="login")(view)


@staff_only
def admin_dashboard(request):
    bookings = Booking.objects.select_related("car", "user")
    return render(request, "rentals/admin_dashboard.html", {"bookings": bookings})


@staff_only
@require_POST
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.is_approved = False  # history is kept
    booking.save(update_fields=["is_approved"])
    messages.success(request, f"Booking #{booking.id} was canceled.")
    return redirect("admin_dashboard")
