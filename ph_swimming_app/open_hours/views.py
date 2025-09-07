from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import generic
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Session, Activity, OpeningHour, TimetableSession, TimetableActivity, DAY_CHOICES
from collections import defaultdict
import datetime
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

 
class OpenHours(generic.ListView):
    queryset = OpeningHour.objects.all().order_by('day', 'open_time')
    template_name = 'timetable.html'
    paginate_by = 7


def show_timetable(request):
    """
    Renders the main timetable page.
    """
    activities = Activity.objects.all()
    day_choices = DAY_CHOICES
    
    context = {
        'activities': activities,
        'day_choices': day_choices,
    }
    return render(request, 'timetable.html', context)

@require_POST
@login_required
@csrf_exempt
def add_session(request):
    """
    Handles the form submission for adding a new timetable session via AJAX.
    Returns a JSON response to the JavaScript.
    """
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'You do not have permission to perform this action.'}, status=403)
    
    try:
        session_day = request.POST.get('session_day')
        start_time_str = request.POST.get('start_time')
        activity_id = request.POST.get('activity')
        
        if not all([session_day, start_time_str, activity_id]):
            return JsonResponse({'success': False, 'message': 'All fields are required.'}, status=400)
            
        # --- START VALIDATION LOGIC from your existing code ---
        valid_time_slot = False
        opening_hours_for_day = OpeningHour.objects.filter(day=session_day)
        submitted_time = datetime.datetime.strptime(start_time_str, '%H:%M').time()
        
        for oh in opening_hours_for_day:
            if oh.open_time <= submitted_time < oh.close_time:
                valid_time_slot = True
                break
        
        if not valid_time_slot:
            return JsonResponse({'success': False, 'message': "Error: The selected time is outside of the valid opening hours for this day."}, status=400)
        # --- END VALIDATION LOGIC ---
        
        selected_activity = Activity.objects.get(pk=activity_id)
        
        # Create and save the new session using your models
        Session.objects.create(
            activity=selected_activity,
            session_day=session_day,
            start_time=submitted_time,
            booked_number=0 # Assuming this field is required
        )
        
        return JsonResponse({'success': True, 'message': 'Session added successfully!'})
    
    except Activity.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid activity selected.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {e}'}, status=500)

def get_timetable_data(request):
    """
    Retrieves all timetable sessions and returns them as a JSON response.
    This is called by the JavaScript to dynamically update the timetable.
    """
    sessions = Session.objects.select_related('activity').all().order_by('session_day', 'start_time')
    
    # This line will help you debug. Check your Django console for the count.
    print(f"Number of sessions retrieved: {len(sessions)}")
    
    timetable_data = defaultdict(dict)
    
    # Use your DAY_CHOICES for consistency
    day_map = dict(DAY_CHOICES)
    
    for session in sessions:
        day_display = day_map.get(session.session_day, 'Unknown Day')
        time_slot = session.start_time.strftime('%H:%M')
        
        # Ensure the activity field exists before trying to access it
        activity_name = session.activity.activity_name if session.activity else 'N/A'
        
        timetable_data[day_display][time_slot] = {
            'activity_name': activity_name
        }
    
    return JsonResponse(timetable_data)
