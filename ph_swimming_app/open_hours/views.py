from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Session, Activity, DAY_CHOICES, OpeningHour
from collections import defaultdict
from django.utils import timezone
import datetime
from django.http import JsonResponse
from .models import TimetableSession, TimetableActivity
from collections import defaultdict
import json

 
def timetable_view(request):
    """
    Displays a timetable of all sessions.
    Allows authenticated admin users to add new sessions.
    """
    timetable_slots = get_timetable_slots()

    # Populate the timetable slots with existing sessions
    existing_sessions = Session.objects.all().select_related('activity')
    for session in existing_sessions:
        day_display = session.get_session_day_display()
        start_time_str = session.start_time.strftime('%H:%M')
        if day_display in timetable_slots and start_time_str in timetable_slots[day_display]:
            timetable_slots[day_display][start_time_str] = session

    activities = Activity.objects.all()
    
    if request.method == 'POST' and request.user.is_superuser:
        try:
            session_day = request.POST.get('session_day')
            start_time_str = request.POST.get('start_time')
            activity_id = request.POST.get('activity')
            
            # --- START VALIDATION LOGIC ---
            valid_time_slot = False
            opening_hours_for_day = OpeningHour.objects.filter(day=session_day)
            submitted_time = datetime.datetime.strptime(start_time_str, '%H:%M').time()
            
            for oh in opening_hours_for_day:
                if oh.open_time <= submitted_time < oh.close_time:
                    valid_time_slot = True
                    break
            
            if not valid_time_slot:
                messages.error(request, f"Error: The selected time is outside of the valid opening hours for this day.")
                return redirect('timetable_view')
            # --- END VALIDATION LOGIC ---
            
            selected_activity = Activity.objects.get(pk=activity_id)
            
            new_session = Session.objects.create(
                activity=selected_activity,
                session_day=session_day,
                start_time=submitted_time,
                booked_number=0
            )
            
            messages.success(request, f"Successfully added session for {selected_activity.activity_name} on {new_session.get_session_day_display()}.")
            return redirect('timetable_view')

        except (Activity.DoesNotExist, ValueError) as e:
            messages.error(request, f"Error creating session: {e}")

    context = {
        'timetable_slots': timetable_slots,
        'activities': activities,
        'day_choices': DAY_CHOICES,
    }
    return render(request, 'open_hours\\timetable.html', context)

def get_timetable_slots():
    """Generates a structured dictionary of hourly time slots for the timetable."""
    time_slots = defaultdict(dict)
    
    opening_hours = OpeningHour.objects.all()
    
    for oh in opening_hours:
        current_time = datetime.datetime.combine(datetime.date.min, oh.open_time)
        close_time = datetime.datetime.combine(datetime.date.min, oh.close_time)
        
        while current_time < close_time:
            time_slot = current_time.time()
            time_slots[oh.get_day_display()][time_slot.strftime('%H:%M')] = None
            current_time += datetime.timedelta(hours=1)
            
    return time_slots

def get_timetable_data(request):
    """
    Retrieves all timetable sessions and returns them as a JSON response.
    """
    sessions = TimetableSession.objects.select_related('activity').all().order_by('day', 'start_time')
    
    timetable_data = defaultdict(dict)
    
    # Django's TimetableSession model has a 'day' field, e.g., 'mon'
    # We need to map this to a display name.
    day_map = {
        'mon': 'Monday',
        'tue': 'Tuesday',
        'wed': 'Wednesday',
        'thu': 'Thursday',
        'fri': 'Friday',
        'sat': 'Saturday',
        'sun': 'Sunday',
    }
    
    for session in sessions:
        day_display = day_map.get(session.day, 'Unknown Day')
        time_slot = session.start_time.strftime('%I:%M %p') # Format time, e.g., 09:00 AM
        
        timetable_data[day_display][time_slot] = {
            'activity_name': session.activity.activity_name
        }
    
    return JsonResponse(timetable_data)

@login_required
def session_setup_view(request):
    """
    Displays the interactive timetable for session setup.
    Generates hourly slots and shows existing sessions.
    """
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('timetable_view')

    timetable_slots = get_timetable_slots()
    
    existing_sessions = Session.objects.all().select_related('activity')
    for session in existing_sessions:
        day_display = session.get_session_day_display()
        start_time_str = session.start_time.strftime('%H:%M')
        if start_time_str in timetable_slots[day_display]:
            timetable_slots[day_display][start_time_str] = session

    context = {
        'day_choices': DAY_CHOICES,
        'activities': Activity.objects.all(),
        'timetable_slots': timetable_slots,
    }
    return render(request, 'session_setup.html', context)

@csrf_exempt
@login_required
def update_session_activity(request):
    """
    Handles POST requests to update a session with a new activity.
    """
    if request.method == 'POST' and request.user.is_superuser:
        session_id = request.POST.get('session_id')
        activity_id = request.POST.get('activity_id')
        
        try:
            session = Session.objects.get(pk=session_id)
            if activity_id and activity_id != 'null':
                activity = Activity.objects.get(pk=activity_id)
                session.activity = activity
            else:
                session.activity = None

            session.save()
            return JsonResponse({'status': 'success', 'message': 'Session updated successfully.'})

        except (Session.DoesNotExist, Activity.DoesNotExist) as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=405)