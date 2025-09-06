from django.contrib import admin
from .models import OpeningHour
from .models import activities

# Register your models here.
admin.site.register(OpeningHour)
admin.site.register(activities)