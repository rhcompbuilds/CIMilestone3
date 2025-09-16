from rest_framework import serializers
from .models import Activity, Session

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ['id', 'activity_name']

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['activity', 'session_day', 'start_time']