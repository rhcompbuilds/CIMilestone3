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
        self.locked_session = kwargs.pop('locked_session', None)
        super().__init__(*args, **kwargs)
        # Default queryset is all sessions (will be overridden in view)
        self.fields["session"].queryset = Session.objects.all()


class StaffBookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["caravan_number", "first_name", "last_name", "email", "session", "number_of_people", "attended"]

    def __init__(self, *args, **kwargs):
        locked_session = kwargs.pop('locked_session', False)
        super().__init__(*args, **kwargs)
        if locked_session:
            self.fields["session"].widget = forms.HiddenInput()