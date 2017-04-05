from rest_framework import serializers
from .models import *

class RecordingSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Recording
        fields = ('name','date','course','status', 'media_url')

class CourseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Course
        fields = ('name',)