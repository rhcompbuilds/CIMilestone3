from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, datetime
from cloudinary.models import CloudinaryField

# Create your models here.
DAY_CHOICES = [
    ('Mon', 'Monday'), ('Tue', 'Tuesday'), ('Wed', 'Wednesday'),
    ('Thu', 'Thursday'), ('Fri', 'Friday'), ('Sat', 'Saturday'),
    ('Sun', 'Sunday')
]

DURATION_CHOICE = [
    ('00:30', '30 minutes'), 
    ('01:00', '1 hour'), 
    ('01:30', '1 hour 30 minutes'), 
    ('02:00', '2 hours')
]
 
SESSION_CHOICE = [
    ('09:00', '09:00'), ('10:00', '10:00'), ('11:00', '11:00'),
    ('12:00', '12:00'), ('13:00', '13:00'), ('14:00', '14:00'), 
    ('15:00', '15:00'), ('16:00', '16:00'),
]

class OpeningHour(models.Model):
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    open = models.CharField(max_length=5, choices=SESSION_CHOICE)
    close = models.CharField(max_length=5, choices=SESSION_CHOICE)

    def __str__(self):
        return f"{self.day}: {self.open} - {self.close}"

class Activity(models.Model):
    activity_name = models.CharField(max_length=100)
    description = models.TextField()
    max_number = models.IntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    duration = models.DurationField(default=timedelta(hours=1))
    activity_image = CloudinaryField('image', null=True, blank=True)

    def __str__(self):
        return self.activity_name

    class Meta:
        verbose_name_plural = "activities"

class Session(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, null=True, blank=True)
    session_day = models.CharField(max_length=10, choices=DAY_CHOICES, default='Monday')
    start_time = models.CharField(max_length=5, choices=SESSION_CHOICE)
    
    @property
    def people_booked(self):
       return self.booking_set.aggregate(Sum('number_of_people'))['number_of_people__sum'] or 0

    @property
    def available_places(self):
        if self.activity:
            max_capacity = self.activity.max_number
            return max_capacity - self.people_booked
        return 0
    
    @property
    def is_full(self):
        return self.available_places <= 0
        
    @property
    def end_time(self):
        if self.activity:
            start_time_obj = datetime.strptime(self.start_time, '%H:%M').time()
            start_datetime = datetime.combine(timezone.now().date(), start_time_obj)
            end_datetime = start_datetime + self.activity.duration
            return end_datetime.time()
        return None
        
    def __str__(self):
        activity_name = self.activity.activity_name if self.activity else "No Activity"
        return f"{activity_name} on {self.get_session_day_display()} starting at {self.start_time}"