from django.urls import path
from . import views

urlpatterns = [
    path("", views.booking_home, name="booking_home"),
    path("make/", views.make_booking, name="make_booking"),
    path("staff/", views.staff_view_sessions, name="staff_view_sessions"),
    path("staff/create/", views.staff_create_booking, name="staff_create_booking"),
    path("session/<int:session_id>/", views.session_bookings, name="session_bookings"),
    path("api/sessions/<int:activity_id>/", views.get_sessions, name="get_sessions"),
]
