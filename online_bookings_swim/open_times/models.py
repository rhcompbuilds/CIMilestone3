from django.db import models

# Create your models here.
class OpenTime(models.Model):
    day = models.CharField(max_length=10)
    open_time = models.TimeField()
    close_time = models.TimeField()

    def __str__(self):
        return f"{self.day}: {self.open_time} - {self.close_time}"
    def is_open(self, check_time):
        return self.open_time <= check_time <= self.close_time
    class Meta:
        ordering = ['day']