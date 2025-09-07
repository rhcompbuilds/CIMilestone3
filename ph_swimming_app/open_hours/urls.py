from django.urls import path
from . import views

urlpatterns = [
    # Standard timetable view
    path("", views.timetable_view, name='timetable'),
    
    # Interactive drag-and-drop session setup view
    path("session-setup/", views.session_setup_view, name='session_setup_view'),

    # Endpoint for updating sessions
    path("update_session_activity/", views.update_session_activity, name='update_session_activity'),

    # Endpoint for fetching timetable data as JSON
    path('api/timetable-data/', views.get_timetable_data, name='timetable_data'),
]