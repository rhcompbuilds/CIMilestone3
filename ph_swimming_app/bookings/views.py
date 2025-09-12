from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core import serializers
from django.core.exceptions import ValidationError
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Booking
from open_hours.models import Activity, Session
from .forms import GuestBookingForm
from .forms import StaffBookingForm
from django.db.models import Sum, F
from datetime import date, timedelta

""" Guest Views """
def booking_home(request):
    """
    Displays a grid of available activities for a guest to select.
    """
    activities = Activity.objects.exclude(activity_name='Lunch')
    return render(request, "bookings/booking_home.html", {
        "activities": activities,
    })


def make_booking(request):
    session_id = request.GET.get("session")
    
    if not session_id:
        messages.error(request, "A valid session must be selected.")
        return redirect('booking_home')

    session = get_object_or_404(Session, pk=session_id)

    # Check if the session is full before showing the form
    if session.is_full:
        messages.warning(request, "This session is fully booked.")
        return render(request, "bookings/make_booking.html", {
            "session": session,
        })

    if request.method == "POST":
        form = GuestBookingForm(request.POST)
        if form.is_valid():
            number_of_people = form.cleaned_data['number_of_people']
            
            # Re-check capacity before saving to prevent overbooking
            if session.spaces_remaining >= number_of_people:
                booking = form.save(commit=False)
                booking.session = session
                booking.save()
                messages.success(request, "Your booking has been confirmed!")
                return redirect("booking_home")
            else:
                messages.error(request, "Not enough spaces remaining. Please choose a smaller number of people.")
    else:
        form = GuestBookingForm(initial={'session': session})

    return render(request, "bookings/make_booking.html", {
        "form": form,
        "session": session,
    })


def booking_success(request):
    return render(request, "bookings/booking_success.html")

def get_sessions(request, activity_id):
    """
    Returns a JSON object of all sessions for a given activity.
    """
    sessions = Session.objects.filter(activity__id=activity_id).order_by('session_day', 'start_time')
    
    sessions_data = serializers.serialize("json", sessions)
    
    return JsonResponse({"sessions": sessions_data}, safe=False)

def get_sessions_api(request, activity_id):
    """API endpoint to get sessions for a given activity."""
    activity = get_object_or_404(Activity, pk=activity_id)
    sessions = Session.objects.filter(activity=activity).order_by('session_day', 'start_time')

    session_data = []
    for session in sessions:
        session_data.append({
            'pk': session.pk,
            'session_day': session.session_day,
            'start_time': session.start_time,
            'available_places': session.available_places,
            'is_full': session.is_full
        })
    
    return JsonResponse({'sessions': session_data})

""" Staff Views """

@staff_member_required
def staff_today_sessions(request):
    """
    Staff view to display a grid of today's sessions with booking counts.
    """
    today_code = date.today().strftime('%a')
    
    # Filter for sessions happening today and exclude 'Lunch' activity
    today_sessions = Session.objects.filter(
        session_day=today_code, 
        activity__activity_name__isnull=False
    ).exclude(
        activity__activity_name='Lunch'
    ).annotate(
        total_booked=Sum('booking__number_of_people')
    ).order_by('start_time')

    # Ensure total_booked is 0 for sessions with no bookings
    for session in today_sessions:
        if session.total_booked is None:
            session.total_booked = 0

    return render(request, "bookings/staff_sessions_grid.html", {
        "today_sessions": today_sessions
    })

@staff_member_required
def session_bookings(request, session_id):
    session = get_object_or_404(Session, id=session_id)

    # Handle POST actions (attend / release)
    if request.method == "POST":
        booking_id = request.POST.get("booking_id")
        action = request.POST.get("action")
        booking = get_object_or_404(Booking, id=booking_id)

        if action == "attend":
            booking.attended = True
            booking.save()
            messages.success(request, f"Booking for {booking.first_name} marked as attended.")
        elif action == "release":
            booking.delete()
            session.booked_number = (
                session.booking_set.aggregate(total=Sum("number_of_people"))["total"] or 0
            )
            session.save()
            messages.success(request, f"Booking for {booking.first_name} released.")

        return redirect("session_bookings", session_id=session.id)

    bookings = session.booking_set.all()

    return render(request, "bookings/session_bookings.html", {
        "session": session,
        "bookings": bookings,
    })

@staff_member_required
def staff_all_sessions(request):
    """
    Staff view to display ALL sessions with booking counts and filtering.
    """
    day_filter = request.GET.get("day")
    activity_filter = request.GET.get("activity")

    sessions = Session.objects.exclude(
        activity__activity_name='Lunch'
    ).annotate(
        total_booked=Sum('booking__number_of_people')
    ).order_by('session_day', 'start_time')

    # Ensure total_booked is 0 if no bookings exist
    for session in sessions:
        if session.total_booked is None:
            session.total_booked = 0

    # Apply filters
    if day_filter:
        sessions = sessions.filter(session_day=day_filter)
    if activity_filter:
        sessions = sessions.filter(activity_id=activity_filter)

    activities = Activity.objects.exclude(activity_name="Lunch")

    return render(request, "bookings/staff_all_sessions.html", {
        "sessions": sessions,
        "activities": activities,
        "selected_day": day_filter,
        "selected_activity": activity_filter,
    })


@staff_member_required
def staff_make_booking(request, session_id=None):
    """
    Allow staff to create a booking for a guest.
    If session_id is passed, preselect the session.
    Superusers can override capacity checks.
    """
    initial_data = {}
    locked_session = False

    if session_id:
        session = get_object_or_404(Session, id=session_id)
        initial_data["session"] = session
        locked_session = True

    if request.method == "POST":
        form = StaffBookingForm(request.POST, initial=initial_data, locked_session=locked_session)
        if form.is_valid():
            booking = form.save(commit=False)
            try:
                if request.user.is_superuser:
                    booking.full_clean(exclude=None)
                    booking.save()
                    messages.success(request, "Booking confirmed (override).")
                else:
                    booking.save()
                    messages.success(request, "Booking confirmed.")
                return redirect("staff_all_sessions")
            except ValidationError as e:
                messages.error(request, e.message)
    else:
        form = StaffBookingForm(initial=initial_data, locked_session=locked_session)

    return render(request, "bookings/staff_booking.html", {
        "form": form,
        "locked_session": session if locked_session else None
    })

# Cancel a booking
@staff_member_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    session = booking.session

    if request.method == "POST":
        booking.delete()
        session.booked_number = (
        session.booking_set.aggregate(total=Sum('number_of_people'))['total'] or 0
        )
        session.save()
        messages.success(request, "Booking successfully cancelled.")
        return redirect("staff_all_sessions")
    
    return render(request, "bookings/cancel_booking.html", {
        "booking": booking})