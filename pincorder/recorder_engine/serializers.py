from rest_framework import serializers
from django.contrib.auth.models import User
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

# User dumps


class UserDumpUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')


class UserDumpTeacherSerializer(serializers.ModelSerializer):

    class Meta:
        model = Teacher
        fields = ('id', 'name')


class UserDumpCourseSerializer(serializers.ModelSerializer):
    teacher = UserDumpTeacherSerializer()

    class Meta:
        model = Course
        fields = ('id', 'name', 'teacher')


class UserDumpCourseOnlyIdSerializer(serializers.ModelSerializer):

    class Meta:
        model = Course
        fields = ('id')


class UserDumpPinSerializer(serializers.ModelSerializer):

    class Meta:
        model = Pin
        fields = ('time', 'text', 'media_url')


class UserDumpRecordingSerializer(serializers.ModelSerializer):
    # Uncomment if you want full information of the course in the recording
    course = UserDumpCourseSerializer()
    #course = UserDumpCourseOnlyIdSerializer()
    pin_set = UserDumpPinSerializer(many=True)

    class Meta:
        model = Recording
        fields = ('id', 'name', 'date', 'course', 'status', 'is_online', 'is_converted', 'pin_set')


class UserDumpSerializer(serializers.Serializer):
    user = UserDumpUserSerializer()
    recordings = UserDumpRecordingSerializer(many=True)
    courses = UserDumpCourseSerializer(many=True)
