from collections import defaultdict
import datetime
from django.db import transaction

# Core Django imports
from django.shortcuts import render, redirect
from django.http import JsonResponse
# NOTE: Removed unnecessary csrf_exempt and require_POST as DRF views handle these.

# Authentication and Authorization imports
from django.contrib.auth.mixins import UserPassesTestMixin 
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages 

# Command Execution
from django.core.management import call_command

# DRF Imports
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

# Local Imports
# Assuming SessionSerializer and ActivitySerializer exist in .serializers
# Assuming Session, Activity, DAY_CHOICES, SESSION_CHOICE exist in .models
from .serializers import ActivitySerializer, SessionSerializer 
from .models import Session, Activity, DAY_CHOICES, SESSION_CHOICE 

# ----------------------------------------------------------------------
# SYSTEM CONFIGURATION
# ----------------------------------------------------------------------
# 🚨 IMPORTANT: Define this here or ideally in your settings.py and import it.
# LUNCH_ACTIVITY_ID = 5 is used as per your input.
LUNCH_ACTIVITY_ID = 5 

DAY_MAPPING = {
    "Mon": 1, "mon": 1, "Tue": 2, "tue": 2, "Wed": 3, "wed": 3,
    "Thu": 4, "thu": 4, "Fri": 5, "fri": 5, "Sat": 6, "sat": 6,
    "Sun": 7, "sun": 7,
}
DAY_CODE_TO_DISPLAY = dict(DAY_CHOICES)
SESSION_TIMES = [t for t, _ in SESSION_CHOICE]

# ----------------------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------------------

def calculate_slots_needed(duration):
    """Calculates the number of 1-hour slots required for an activity duration."""
    if not duration:
        return 1
    total_seconds = duration.total_seconds()
    slots_needed = int(total_seconds / 3600)
    # Add an extra slot if there's a remainder (e.g., 1.5 hours needs 2 slots)
    if total_seconds % 3600 != 0:
        slots_needed += 1
    return max(1, slots_needed) # Ensure at least 1 slot is used

def get_spanned_session_slots(start_session):
    """
    Finds all subsequent Session slots spanned by a multi-hour activity.
    It fetches slots that share the same day and fall within the activity's duration.
    """
    if not start_session.activity or not start_session.activity.duration:
        return [start_session]

    slots_needed = calculate_slots_needed(start_session.activity.duration)
    
    try:
        start_index = SESSION_TIMES.index(start_session.start_time)
    except ValueError:
        # Should not occur if data is clean, but safe fallback
        return [start_session] 

    end_index = start_index + slots_needed
    # Get the time strings for all affected slots
    spanned_times = SESSION_TIMES[start_index:end_index]
    
    # Efficiently fetch all session objects for the same day/times
    return list(Session.objects.filter(
        session_day=start_session.session_day,
        start_time__in=spanned_times
    ).order_by('start_time'))

# ----------------------------------------------------------------------
# PUBLIC TIMETABLE VIEW
# ----------------------------------------------------------------------

def show_timetable(request):
    """
    Renders the public timetable page, calculating multi-hour spans.
    """
    timetable_slots = defaultdict(lambda: defaultdict(lambda: {'activity': None, 'hidden': False}))

    # 1. Prepopulate all slots
    for day_code, day_name in DAY_CHOICES:
        for time_str, _ in SESSION_CHOICE:
            timetable_slots[day_name][time_str] = {'activity': None, 'hidden': False}

    # 2. Fill with existing sessions
    existing_sessions = Session.objects.select_related('activity').order_by('session_day', 'start_time')
    
    for session in existing_sessions:
        day_display = session.get_session_day_display()
        if session.activity and session.start_time in timetable_slots[day_display]:
            
            # Assign current slot (the starting slot)
            timetable_slots[day_display][session.start_time]['activity'] = session.activity

            # Hide following slots (continuation slots)
            slots_needed = calculate_slots_needed(session.activity.duration)

            try:
                start_index = SESSION_TIMES.index(session.start_time)
            except ValueError:
                continue 

            for i in range(1, slots_needed):
                if start_index + i < len(SESSION_TIMES):
                    next_time = SESSION_TIMES[start_index + i]
                    # Mark the subsequent slots as hidden/occupied by the span
                    timetable_slots[day_display][next_time]['hidden'] = True

    context = {
        'timetable_slots': timetable_slots,
        'activities': Activity.objects.all(),
        'day_choices': DAY_CHOICES,
        'session_choices': SESSION_CHOICE,
    }
    return render(request, 'timetable.html', context)

# ----------------------------------------------------------------------
# ADMIN SCHEDULER VIEWS
# ----------------------------------------------------------------------

# 1. Permission Class for Staff/Superusers
class IsStaffOrSuperuser(UserPassesTestMixin, permissions.BasePermission):
    """
    Custom permission to only allow staff and superusers to edit/create/delete.
    """
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True # Allow read access (GET) for everyone
        return request.user.is_staff or request.user.is_superuser 

# 2. Template View (The admin dashboard)
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def scheduler_view(request):
    """
    Renders the drag-and-drop scheduler page.
    """
    return render(request, 'open_hours/scheduler.html', {})


# 3. API Views (List/Create/Update/Delete)

class ActivityListAPIView(generics.ListAPIView):
    """GET /api/activities/ - Populates the activity sidebar."""
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [permissions.AllowAny]


class SessionListAPIView(generics.ListAPIView):
    """GET /api/schedule/list/ - Fetches the initial schedule data."""
    queryset = Session.objects.all().select_related('activity')
    serializer_class = SessionSerializer
    permission_classes = [permissions.AllowAny]


class SessionManageAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Handles Update (Move) and Delete (Unschedule) of single Session slots.
    Implements LUNCH protection and safe unscheduling.
    """
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [IsStaffOrSuperuser] 

    def get_session_and_check_lunch(self, session):
        """Raises PermissionDenied if staff attempts to modify the LUNCH session."""
        if session.activity and session.activity.id == LUNCH_ACTIVITY_ID:
            if not self.request.user.is_superuser:
                raise PermissionDenied("Only superusers can modify the system-mandated LUNCH session.")
    
    @transaction.atomic
    def perform_destroy(self, instance):
        """Clears activity from all spanned slots (unschedule) and enforces Lunch protection."""
        self.get_session_and_check_lunch(instance) # Check user permissions

        # 🟢 FIX: Find all associated slots and clear the activity field
        spanned_slots = get_spanned_session_slots(instance)
        
        for slot in spanned_slots:
            slot.activity = None
            slot.save()
            
        # Return HTTP 200 OK with a success message for client-side feedback
        return Response({'message': 'Session unscheduled successfully.'}, status=status.HTTP_200_OK)


    def perform_update(self, serializer):
        """Enforces Lunch protection before allowing a session to be moved/updated."""
        session = self.get_object()
        self.get_session_and_check_lunch(session)
        serializer.save()


class SessionCreateAPIView(generics.CreateAPIView):
    """
    POST /api/schedule/create/ - Handles drag-and-drop assignment (single/multi-hour).
    Uses database transactions for integrity.
    """
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [IsStaffOrSuperuser]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = request.data
        session_day_abbr = data.get('session_day')
        start_time_raw = data.get('start_time')
        activity_id = data.get('activity')
        
        # --- Validation and Standardization ---
        session_day = DAY_MAPPING.get(session_day_abbr)
        if not session_day:
             raise ValidationError({'session_day': 'Invalid session day abbreviation.'})

        start_time = f"{start_time_raw}:00" if isinstance(start_time_raw, str) and len(start_time_raw) == 5 else start_time_raw

        if not all([session_day, start_time, activity_id]):
            raise ValidationError({'message': 'All required fields are missing.'})

        try:
            activity = Activity.objects.get(pk=activity_id)
        except Activity.DoesNotExist:
            raise ValidationError({'activity': 'Activity not found.'})

        # --- DURATION & CONFLICT CHECK ---
        slots_needed = calculate_slots_needed(activity.duration)
        
        try:
            start_index = SESSION_TIMES.index(start_time)
        except ValueError:
            raise ValidationError({'start_time': 'Invalid start time format or value.'})

        if start_index + slots_needed > len(SESSION_TIMES):
            raise ValidationError({'message': 'Activity does not fit in remaining slots.'})

        # Check for conflicts and find the starting slot ID using select_for_update for concurrency control
        slots_to_update = []
        for i in range(slots_needed):
            current_time = SESSION_TIMES[start_index + i]
            try:
                # 🟢 ROBUSTNESS FIX: select_for_update locks the rows during the transaction
                session_slot = Session.objects.select_for_update().get(session_day=session_day, start_time=current_time)
                
                if session_slot.activity is not None:
                    raise ValidationError({'message': f'Slot at {current_time} is already occupied by {session_slot.activity.activity_name}.'})

                slots_to_update.append(session_slot)
            except Session.DoesNotExist:
                raise ValidationError({'message': f'Session slot at {current_time} does not exist (pre-population failed).'})

        # Assign activity to all required slots
        for session_slot in slots_to_update:
            session_slot.activity = activity
            session_slot.save()
            
        # Return the serialized data for the starting session slot to the frontend
        serializer = self.get_serializer(slots_to_update[0])

        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
#--------------------------
# RESET BOOKINGS FUNCTION
#--------------------------
def is_superuser(user):
    return user.is_superuser

@user_passes_test(is_superuser)
@login_required
def reset_bookings_view(request):
    """
    Executes the 'reset_bookings' management command. Only accessible by superusers.
    """
    if request.method == 'POST':
        try:
            call_command('reset_bookings', interactive=False)
            messages.success(request, "SUCCESS: All bookings have been reset and open slots recreated.")
        except Exception as e:
            messages.error(request, f"ERROR resetting bookings: {e}")
            
        return redirect('admin_schedule')

    messages.error(request, "Error: This action requires a POST request.")
    return redirect('admin_schedule')
