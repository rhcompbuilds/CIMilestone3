from django.urls import path
from . import views

urlpatterns = [
    # Standard timetable view
    path("", views.show_timetable, name='timetable'),
    
    # Interactive drag-and-drop session setup view
    path("add_session/", views.add_session, name='add_session'),

    # Endpoint for updating sessions
    path("update_session_activity/", views.show_timetable, name='update_session_activity'),

    # Endpoint for fetching timetable data as JSON
    path('api/timetable-data/', views.show_timetable, name='timetable_data'),
]