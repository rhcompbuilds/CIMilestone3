from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Booking
from open_hours.models import Activity, Session
from .forms import GuestBookingForm, StaffBookingForm
from django.db.models import Sum, F
from datetime import datetime, date, time, timedelta
from django.views.decorators.csrf import csrf_exempt

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
    session = None
    if session_id:
        session = get_object_or_404(Session, pk=session_id)
        
    if request.method == "POST":
        form = GuestBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.session = session
            try:
                booking.save()
                messages.success(request, "Booking confirmed!")
                return redirect("booking_success")
            except ValidationError as e:
                messages.error(request, e.message)
    else:
        # Pre-populate the form with the selected session
        form = GuestBookingForm(initial={'session': session})

    return render(request, "bookings/make_booking.html", {
        "form": form,
        "session": session,
    })


def booking_success(request):
    return render(request, "bookings/booking_success.html")

def get_sessions(request, activity_id):
    """
    API endpoint to retrieve sessions for a given activity.
    Always returns valid JSON, even if Session fields are inconsistent.
    """
    try:
        sessions = Session.objects.filter(activity__id=activity_id).order_by('session_day', 'start_time')

        sessions_data = []
        for session in sessions:
            # Handle session_day
            day_val = getattr(session, "session_day", "")
            if hasattr(day_val, "strftime"):
                session_day_str = day_val.strftime("%Y-%m-%d")
            else:
                session_day_str = str(day_val) if day_val is not None else ""

            # Handle start_time
            time_val = getattr(session, "start_time", "")
            if hasattr(time_val, "strftime"):
                start_time_str = time_val.strftime("%H:%M")
            else:
                start_time_str = str(time_val) if time_val is not None else ""

            # Handle is_full
            is_full_val = session.is_full() if callable(session.is_full) else bool(session.is_full)

            # Handle available_places (fallback to 0 if missing)
            available_places_val = getattr(session, "available_places", 0)

            sessions_data.append({
                "pk": session.pk,
                "session_day": session_day_str,
                "start_time": start_time_str,
                "is_full": is_full_val,
                "available_places": available_places_val,
            })

        return JsonResponse({"sessions": sessions_data}, status=200)

    except Exception as e:
        print(f"An error occurred in get_sessions view: {e}")
        return JsonResponse({"error": "An internal server error occurred."}, status=500)

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
def session_bookings_list(request, session_id):
    """
    Displays a list of all bookings for a specific session.
    """
    session = get_object_or_404(Session, id=session_id)
    bookings = Booking.objects.filter(session=session)

    return render(request, "bookings/session_bookings.html", {
        "session": session,
        "bookings": bookings,
    })

@csrf_exempt
def add_session(request):
    """
    API endpoint to assign an activity to a session slot.
    """
    if request.method == 'POST':
        try:
            session_day = request.POST.get('session_day')
            start_time_str = request.POST.get('start_time')
            activity_id = request.POST.get('activity')
            
            # Convert time string to a time object
            start_time_obj = datetime.strptime(start_time_str, '%H:%M').time()
            
            # Find or create the session
            session, created = Session.objects.get_or_create(
                session_day=session_day,
                start_time=start_time_obj,
                defaults={'activity_id': activity_id}
            )
            
            if not created:
                session.activity_id = activity_id
                session.save()

            return JsonResponse({'success': True, 'message': 'Activity assigned successfully.'})
        except Exception as e:
            # Handle potential errors, such as invalid time format or missing data
            return JsonResponse({'success': False, 'message': f'An error occurred: {e}'}, status=500)
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)


@staff_member_required
def session_bookings(request, session_id):
    session = get_object_or_404(Session, id=session_id)

    # Handle POST actions (attend / release)
    if request.method == "POST":
        booking_id = request.POST.get("booking_id")
        action = request.POST.get("action")
        try:
            booking = get_object_or_404(Booking, id=booking_id)

            if action == "attend":
                booking.attended = True
                booking.save()
                # Return a JSON response instead of a redirect
                return JsonResponse({"status": "success", "message": f"Booking for {booking.first_name} marked as attended."})
            elif action == "release":
                first_name = booking.first_name
                booking.delete()
                # Return a JSON response after a successful deletion
                return JsonResponse({"status": "success", "message": f"Booking for {first_name} released."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

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
        messages.success(request, "Booking successfully cancelled.")
        return redirect("staff_all_sessions")
    
    return render(request, "bookings/cancel_booking.html", {
        "booking": booking})
