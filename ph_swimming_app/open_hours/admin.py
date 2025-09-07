from django.contrib import admin
from .models import OpeningHour
from .models import Activity
from .models import Session

# Register your models here.
admin.site.register(OpeningHour)
admin.site.register(Activity)
admin.site.register(Session)