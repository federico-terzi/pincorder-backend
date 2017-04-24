from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.fields import CurrentUserDefault
from .models import *


class RecordingFileSerializer(serializers.ModelSerializer):
    """
    Serializer used to manage recording files
    """
    recording = serializers.PrimaryKeyRelatedField(queryset=Recording.objects.all())

    def get_file(self):
        """
        Return a RecordingFile object with the data, without saving it
        """
        return RecordingFile(**self.validated_data)

    class Meta:
        model = RecordingFile
        fields = ('id', 'recording', 'upload_date', 'file_url')


class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer used to manage courses
    """
    teacher = serializers.PrimaryKeyRelatedField(queryset=Teacher.objects.all(), required=False)

    class Meta:
        model = Course
        fields = ('id', 'name', 'teacher', 'parent_course')


class PinSerializer(serializers.ModelSerializer):
    """
    Serializer used to manage pins
    """
    recording = serializers.PrimaryKeyRelatedField(queryset=Recording.objects.all(), write_only=True)

    def get_pin(self):
        """
        Return a Pin object with the validated data, without saving it
        """
        return Pin(**self.validated_data)

    class Meta:
        model = Pin
        fields = ('recording', 'time', 'text', 'media_url')
        read_only_fields = ('media_url',)


class RecordingSerializer(serializers.ModelSerializer):
    """
    Serializer used to manage recordings
    """
    user = serializers.StringRelatedField()

    def get_recording(self):
        """
        Return a Recording object with the validated data, without saving it
        """
        return Recording(**self.validated_data)

    class Meta:
        model = Recording
        fields = ('id', 'name', 'date', 'course', 'status', 'is_online', 'is_converted', 'user')
        read_only_fields = ('id', 'status', 'is_online', 'is_converted', 'user')

"""
The UserDump* classes are used in the UserDumpAPI, where all the information
about the current user is returned
"""


class UserDumpUserSerializer(serializers.ModelSerializer):
    """
    Serializer used to display User data in the UserDump
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')


class UserDumpTeacherSerializer(serializers.ModelSerializer):
    """
    Serializer used to display Teacher data in the UserDump
    """
    class Meta:
        model = Teacher
        fields = ('id', 'name')


class UserDumpCourseSerializer(serializers.ModelSerializer):
    """
    Serializer used to display Course data in the UserDump
    """
    teacher = UserDumpTeacherSerializer()

    class Meta:
        model = Course
        fields = ('id', 'name', 'teacher', 'parent_course')


class UserDumpCourseOnlyIdSerializer(serializers.ModelSerializer):
    """
    Serializer used to display the Course id in the UserDump
    """
    class Meta:
        model = Course
        fields = ('id',)


class UserDumpPinSerializer(serializers.ModelSerializer):
    """
    Serializer used to display Pin data in the UserDump
    """
    class Meta:
        model = Pin
        fields = ('time', 'text', 'media_url')


class UserDumpRecordingSerializer(serializers.ModelSerializer):
    """
    Serializer used to display Recording data in the UserDump
    """

    # Uncomment if you want full information of the course in the recording
    pin_set = UserDumpPinSerializer(many=True)

    class Meta:
        model = Recording
        fields = ('id', 'name', 'date', 'course', 'status', 'is_online', 'is_converted', 'pin_set')


class UserDumpSerializer(serializers.Serializer):
    """
    Serializer used to display the UserDump
    """

    user = UserDumpUserSerializer()
    courses = UserDumpCourseSerializer(many=True)
    recordings = UserDumpRecordingSerializer(many=True)

    # The UserDump is read only, so no creation is allowed
    def create(self, validated_data):
        pass

    # The UserDump is read only, so no update is allowed
    def update(self, instance, validated_data):
        pass
