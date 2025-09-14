from django.urls import path
from . import views

urlpatterns = [
    # Standard timetable view
    path("", views.show_timetable, name='home'),
    
    # Interactive drag-and-drop session setup view
    path("add_session/", views.add_session, name='add_session'),

    # Endpoint for updating sessions
    path("update_session_activity/", views.show_timetable, name='update_session_activity'),

    # Endpoint for fetching timetable data as JSON
    path('api/timetable-data/', views.show_timetable, name='timetable_data'),
    
    # The main URL for the drag-and-drop scheduler page.
    path('', views.scheduler_view, name='scheduler'),

    # API endpoint to fetch the list of activities
    path('api/activities/', views.ActivityListAPIView.as_view(), name='api-activity-list'),

    # when a user drops an activity onto the timetable.
    path('api/schedule/create/', views.ScheduleCreateAPIView.as_view(), name='api-schedule-create'),
]