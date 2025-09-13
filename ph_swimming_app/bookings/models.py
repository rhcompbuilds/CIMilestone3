# bookings/models.py
from django.db import models
from django.contrib.auth.models import User
from django.forms import ValidationError
from django.db.models import Sum

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
        # We need to get the total number of people for this session, excluding the current booking being validated
        # This is important for when you're editing an existing booking, not just creating a new one.
        if self.session and self.number_of_people:
            current_bookings = self.session.booking_set.exclude(pk=self.pk)
            total_booked_people = current_bookings.aggregate(total=Sum('number_of_people'))['total'] or 0
            
            total_after_booking = (total_booked_people + self.number_of_people)
            
            # Assuming your Session model's related Activity model has a max_number field
            if total_after_booking > self.session.activity.max_number:
                raise ValidationError(f"Sorry, this session does not have enough space. {self.session.activity.max_number} people for this session.")
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        # Remove the code that attempts to save booked_number on the session.
        # This is because the booked_number field does not exist.
        # It's better to calculate this value dynamically when needed.

    def __str__(self):
        return f"Booking for {self.first_name} {self.last_name} on {self.session.session_day} at {self.session.start_time}"

    class Meta:
        verbose_name_plural = "bookings"