from django.urls import path
from . import views

urlpatterns = [
    path("", views.booking_home, name="booking_home"),
    path("make/", views.make_booking, name="make_booking"),
    path("sessions/all/", views.staff_all_sessions, name="staff_all_sessions"),
    path("sessions/today/", views.staff_today_sessions, name="staff_today_sessions"),
    path("session/<int:session_id>/", views.session_bookings, name="session_bookings"),
    path("success/", views.booking_success, name="booking_success"),
    path("api/sessions/<int:activity_id>/", views.get_sessions, name="get_sessions"),
]
