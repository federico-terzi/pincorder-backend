from rest_framework import serializers
from .models import *

class RecordingSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Recording
        fields = ('id','name','date','course','status')

class RecordingFileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = RecordingFile
        fields = ('recording', 'upload_date', 'file_url')

class CourseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Course
        fields = ('name',)