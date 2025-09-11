# bookings/models.py
from django.db import models
from django.contrib.auth.models import User

class Booking(models.Model):
    caravan_number = models.CharField(max_length=6, unique=True)
    first_name = models.CharField(max_length=50, null=False)
    last_name = models.CharField(max_length=50, null=False)
    email = models.EmailField(null=False)
    session = models.ForeignKey('open_hours.Session', on_delete=models.CASCADE)
    number_of_people = models.PositiveIntegerField()
    booking_date = models.DateField(auto_now_add=True)
    attended = models.BooleanField(default=False)

    def __str__(self):
        return f"Booking for {self.first_name} {self.last_name} on {self.session.session_day} at {self.session.start_time}"

    class Meta:
        verbose_name_plural = "bookings"
