from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class OpeningHour(models.Model):
    day = models.CharField(max_length=10)
    open_time = models.TimeField()
    close_time = models.TimeField()
    day_id = models.IntegerField(auto_created=True, primary_key=True)

    def __str__(self):
        return f"{self.day}: {self.open_time} - {self.close_time})"


class activities(models.Model):
    activity = models.CharField(max_length=100)
    description = models.TextField()
    max_number = models.IntegerField()
    activity_id = models.IntegerField(auto_created=True, primary_key=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    duration = models.DurationField()


    def __str__(self):
        return self.activity