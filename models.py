from django.contrib.auth.models import User
from django.db import models


class Car(models.Model):
    name = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField(help_text="Number of seats")
    price_per_day = models.DecimalField(max_digits=8, decimal_places=2)
    image_url = models.URLField(blank=True)

    class Meta:
        ordering = ["price_per_day"]

    def __str__(self):
        return f"{self.name} ({self.capacity} seats)"


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="bookings")
    start_date = models.DateField()
    end_date = models.DateField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    # Cancelling sets this to False, so booking history is kept.
    is_approved = models.BooleanField(default=True)
    driver_name = models.CharField(max_length=100)
    driver_dob = models.DateField()
    driver_license = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.car.name} | {self.start_date} to {self.end_date} | {self.user.username}"

    @property
    def days(self):
        # Start and end day both count.
        return (self.end_date - self.start_date).days + 1

    @property
    def status(self):
        return "Approved" if self.is_approved else "Canceled"
