from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core import serializers
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Booking
from open_hours.models import Activity, Session
from .forms import GuestBookingForm
from .forms import StaffBookingForm
from django.db.models import Sum, F
from datetime import date, timedelta


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
    session = None
    if session_id:
        session = get_object_or_404(Session, pk=session_id)
        
    if request.method == "POST":
        form = GuestBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.session = session

            if session.booked_number + booking.number_of_people > session.activity.max_number:
                messages.error(request, "Sorry, this session is fully booked.")
            else:
                booking.save()
                # update the session booked_number
                session.booked_number += booking.number_of_people
                session.save()
                messages.success(request, "Booking confirmed!")
                return redirect("booking_success")
            booking.save()
            return redirect("booking_success")
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
    """
    Staff view to list all bookings for a specific session.
    Also handles marking bookings as attended.
    """
    session = get_object_or_404(Session, pk=session_id)
    bookings = session.booking_set.all().order_by('first_name')

    if request.method == "POST":
        booking_id = request.POST.get("booking_id")
        action = request.POST.get("action")
        booking = get_object_or_404(Booking, pk=booking_id)

        if action == "attend":
            booking.attended = True
            booking.save()
        elif action == "release":
            # You can add logic here to un-attend or delete
            booking.attended = False
            booking.save()
        return redirect('session_bookings', session_id=session.id)
    
    return render(request, "bookings/session_bookings.html", {
        "session": session,
        "bookings": bookings
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