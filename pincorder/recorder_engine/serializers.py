from rest_framework import serializers
from .models import *


class RecordingSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Recording
        fields = ('id', 'name', 'date', 'course', 'status', 'user')


class RecordingFileSerializer(serializers.HyperlinkedModelSerializer):
    recording = serializers.HyperlinkedRelatedField(view_name='recording-detail', read_only=True)

    class Meta:
        model = RecordingFile
        fields = ('id', 'recording', 'upload_date', 'file_url')


class CourseSerializer(serializers.HyperlinkedModelSerializer):
    teacher = serializers.PrimaryKeyRelatedField(queryset=Teacher.objects.all())

    class Meta:
        model = Course
        fields = ('id', 'name', 'teacher')