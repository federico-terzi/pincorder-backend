from rest_framework import serializers
from .models import *


class RecordingFileSerializer(serializers.ModelSerializer):
    recording = serializers.HyperlinkedRelatedField(view_name='recording-detail', read_only=True)

    def get_file(self):
        return RecordingFile(**self.validated_data)

    class Meta:
        model = RecordingFile
        fields = ('id', 'recording', 'upload_date', 'file_url')


class CourseSerializer(serializers.ModelSerializer):
    teacher = serializers.PrimaryKeyRelatedField(queryset=Teacher.objects.all())

    class Meta:
        model = Course
        fields = ('id', 'name', 'teacher')


class PinSerializer(serializers.ModelSerializer):
    recording = serializers.PrimaryKeyRelatedField(queryset=Recording.objects.all(), write_only=True)

    def get_pin(self):
        return Pin(**self.validated_data)

    class Meta:
        model = Pin
        fields = ('recording', 'time', 'text', 'media_url')


class RecordingSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    def get_recording(self):
        return Recording(**self.validated_data)

    class Meta:
        model = Recording
        fields = ('id', 'name', 'date', 'course', 'status', 'is_online', 'is_converted', 'user')

class UserDumpSerializer(serializers.Serializer):
    recordings = RecordingSerializer(many=True)