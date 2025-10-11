from django.urls import path
from . import views

urlpatterns = [
    # 1. INDEX/HOME PATH: Public Timetable (timetable.html)
    path("", views.show_timetable, name='index'), 
    
    # 2. ADMIN/STAFF DASHBOARD PATHS
    path("admin_schedule/", views.scheduler_view, name='admin_schedule'),
    path("reset_bookings/", views.reset_bookings_view, name='reset_bookings'),

    # 3. API ENDPOINTS
    
    # Activity List (Read-only)
    path('api/activities/', views.ActivityListAPIView.as_view(), name='api_activities'), 
    
    # Session List (Initial Timetable Load)
    path('api/schedule/list/', views.SessionListAPIView.as_view(), name='api_schedule_list'), 
    
    # Session Creation (POST: Drag-and-Drop Assignment)
    path('api/schedule/create/', views.SessionCreateAPIView.as_view(), name='api_schedule_create'), 
    path('api/schedule/<int:pk>/', views.SessionManageAPIView.as_view(), name='api_schedule_manage'),
]