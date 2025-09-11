from django import forms
from .models import Booking
from open_hours.models import Session

class GuestBookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            "caravan_number",
            "first_name",
            "last_name",
            "email",
            "session",
            "number_of_people",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Default queryset is all sessions (will be overridden in view)
        self.fields["session"].queryset = Session.objects.all()


class StaffBookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["caravan_number", "first_name", "last_name", "email", "session", "number_of_people", "attended"]


