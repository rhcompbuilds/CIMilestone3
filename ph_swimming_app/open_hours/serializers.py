from rest_framework import serializers
from .models import Activity, Session

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ['id', 'activity_name', 'duration'] 
        

class SessionSerializer(serializers.ModelSerializer):
    
    
    activity_name = serializers.CharField(
        source='activity.activity_name', 
        read_only=True, 
        allow_null=True 
    )
    
    activity_duration = serializers.DurationField(
        source='activity.duration', 
        read_only=True, 
        allow_null=True
    )
    
    activity = serializers.PrimaryKeyRelatedField(
        queryset=Activity.objects.all(), 
        allow_null=True
    )

    class Meta:
        model = Session
        fields = ['id', 'session_day', 'start_time', 'activity', 'activity_name', 'activity_duration']