from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, datetime

# Create your models here.
DAY_CHOICES = [
    ('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'),
    ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'),
    ('Sunday', 'Sunday')
]

DURATION_CHOICE = [
    ('00:30', '30 minutes'), 
    ('01:00', '1 hour'), 
    ('01:30', '1 hour 30 minutes'), 
    ('02:00', '2 hours')
]

class OpeningHour(models.Model):
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    open_time = models.TimeField()
    close_time = models.TimeField()

    def __str__(self):
        return f"{self.day}: {self.open_time.strftime('%H:%M')} - {self.close_time.strftime('%H:%M')}"

    class Meta:
        # A day can only have one set of opening hours
        unique_together = ('day', 'open_time', 'close_time')



class Activity(models.Model):
    activity_name = models.CharField(max_length=100)
    description = models.TextField()
    max_number = models.IntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    duration = models.DurationField(default=timedelta(hours=1))

    def __str__(self):
        return self.activity_name

    class Meta:
        verbose_name_plural = "activities"



class Session(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    session_day = models.CharField(max_length=10, choices=DAY_CHOICES, default='Monday')
    start_time = models.TimeField()
    booked_number = models.IntegerField(default=0)

    @property
    def end_time(self):
        # Create a temporary datetime object to perform time calculations.
        # The date part is arbitrary as we only care about the time.
        start_datetime = datetime.combine(timezone.now().date(), self.start_time)
        end_datetime = start_datetime + self.activity.duration
        return end_datetime.time()

    def __str__(self):
        return f"{self.activity} on {self.session_day} from {self.start_time.strftime('%H:%M')} to {self.end_time.strftime('%H:%M')}"