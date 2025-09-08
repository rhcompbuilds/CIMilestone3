from collections import defaultdict
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Session, Activity, DAY_CHOICES, SESSION_CHOICE

def show_timetable(request):
    """
    Renders the timetable with all slots prepopulated.
    """
    timetable_slots = defaultdict(lambda: defaultdict(lambda: {'activity': None}))

    # Prepopulate all slots
    for day_code, day_name in DAY_CHOICES:
        for time_str, _ in SESSION_CHOICE:
            timetable_slots[day_name][time_str] = {'activity': None}

    # Fill with existing sessions
    existing_sessions = Session.objects.select_related('activity').all()
    for session in existing_sessions:
        day_display = session.get_session_day_display()
        if day_display in timetable_slots and session.start_time in timetable_slots[day_display]:
            timetable_slots[day_display][session.start_time] = {
                'activity': session.activity,
                'session_id': session.id
            }

    context = {
        'timetable_slots': timetable_slots,
        'activities': Activity.objects.all(),
        'day_choices': DAY_CHOICES,
        'session_choices': SESSION_CHOICE,
    }
    return render(request, 'timetable.html', context)


@require_POST
@login_required
@csrf_exempt
def add_session(request):
    """
    Adds or updates a session with a selected activity
    """
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'You do not have permission.'}, status=403)

    try:
        session_day = request.POST.get('session_day')
        start_time = request.POST.get('start_time')
        activity_id = request.POST.get('activity')

        if not all([session_day, start_time, activity_id]):
            return JsonResponse({'success': False, 'message': 'All fields are required.'}, status=400)

        activity = Activity.objects.get(pk=activity_id)

        # Determine how many 1-hour slots are needed
        total_minutes = activity.duration.total_seconds() / 60
        slots_needed = int(total_minutes / 60)
        if total_minutes % 60 != 0:
            slots_needed += 1

        # Consecutive slots
        session_times = [time for time, _ in SESSION_CHOICE]
        start_index = session_times.index(start_time)
        if start_index + slots_needed > len(session_times):
            return JsonResponse({'success': False, 'message': 'Activity does not fit in remaining slots.'}, status=400)

        # Check conflicts
        for i in range(slots_needed):
            current_time = session_times[start_index + i]
            try:
                session = Session.objects.get(session_day=session_day, start_time=current_time)
                if session.activity:
                    return JsonResponse({'success': False, 'message': f'Session at {current_time} already booked.'}, status=400)
            except Session.DoesNotExist:
                return JsonResponse({'success': False, 'message': f'Session slot at {current_time} does not exist.'}, status=400)

        # Assign activity
        for i in range(slots_needed):
            current_time = session_times[start_index + i]
            session = Session.objects.get(session_day=session_day, start_time=current_time)
            session.activity = activity
            session.save()

        return JsonResponse({'success': True, 'message': 'Activity assigned successfully!'})

    except Activity.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Selected activity does not exist.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {e}'}, status=500)


def get_timetable_data(request):
    """
    Returns timetable as JSON for live updates.
    """
    from collections import defaultdict
    sessions = Session.objects.select_related('activity').all()
    timetable_data = defaultdict(dict)
    day_map = dict(DAY_CHOICES)

    for session in sessions:
        day_display = day_map.get(session.session_day, 'Unknown Day')
        timetable_data[day_display][session.start_time] = {
            'activity_name': session.activity.activity_name if session.activity else 'Free'
        }

    return JsonResponse(timetable_data)
