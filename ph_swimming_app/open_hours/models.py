from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class OpeningHour(models.Model):
    day = models.CharField(max_length=10)
    open_time = models.TimeField()
    close_time = models.TimeField()

    def __str__(self):
        return f"{self.day}: {self.open_time} - {self.close_time})"