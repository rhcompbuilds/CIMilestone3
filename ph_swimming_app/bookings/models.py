# bookings/models.py
from django.db import models
from django.contrib.auth.models import User
from django.forms import ValidationError

class Booking(models.Model):
    caravan_number = models.CharField(max_length=6, unique=True)
    first_name = models.CharField(max_length=50, null=False)
    last_name = models.CharField(max_length=50, null=False)
    email = models.EmailField(null=False)
    session = models.ForeignKey('open_hours.Session', on_delete=models.CASCADE)
    number_of_people = models.PositiveIntegerField()
    booking_date = models.DateField(auto_now_add=True)
    attended = models.BooleanField(default=False)
        
    def clean(self):
        if self.session and self.number_of_people:
            total_after_booking = (self.session.booked_number + self.number_of_people)
            if total_after_booking > self.session.activity.max_number:
                raise ValidationError(f"Sorry, this session does not have enough space. {self.session.activity.max_number} people for this session.")
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        # Update the booked number in the session
        self.session.booked_number = (
            self.session.booking_set.aggregate(total=models.Sum('number_of_people'))['total'] or 0
        )
        self.session.save()

    def __str__(self):
        return f"Booking for {self.first_name} {self.last_name} on {self.session.session_day} at {self.session.start_time}"

    class Meta:
        verbose_name_plural = "bookings"
