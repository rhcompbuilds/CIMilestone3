from django.contrib import admin
from .models import OpeningHour, Activity, Session


# Register your models here.
admin.site.register(OpeningHour)
admin.site.register(Activity)
admin.site.register(Session)