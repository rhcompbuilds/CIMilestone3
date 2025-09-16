from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from open_hours.models import Session, Booking, HistoricalSession, HistoricalBooking

class Command(BaseCommand):
    help = 'Resets bookings for past sessions and archives them.'

    def handle(self, *args, **options):
        # Calculate the date and time from which to reset sessions
        yesterday = timezone.now().date() - timedelta(days=1)
        
        # Find all sessions that are for yesterday or earlier
        sessions_to_reset = Session.objects.filter(session_day__lt=yesterday) # Assuming a date field or similar
        
        # This is where your logic will need to be adapted based on how you handle session dates.
        # If your Session model has a full DateTimeField, you can do this:
        # sessions_to_reset = Session.objects.filter(start_time__lt=timezone.now() - timedelta(hours=1))

        # We will use the `session_day` and `start_time` fields to determine
        # if a session has passed. This requires some careful date math.
        
        self.stdout.write(self.style.SUCCESS(f'Starting booking reset for {yesterday}...'))

        for session in sessions_to_reset:
            # 1. Archive the session and its bookings
            historical_session = HistoricalSession.objects.create(
                activity=session.activity,
                session_day=session.session_day,
                start_time=session.start_time,
                total_booked=session.people_booked  # Use the property from your model
            )

            for booking in session.booking_set.all():
                HistoricalBooking.objects.create(
                    user=booking.user,
                    historical_session=historical_session,
                    number_of_people=booking.number_of_people,
                    booking_date=booking.booking_date
                )
            
            session.booking_set.all().delete()
            
        self.stdout.write(self.style.SUCCESS('Successfully reset and archived past bookings.'))