from django.db import models
from django.conf import settings
from django.utils.timezone import now


class Teacher(models.Model):
    """
    Model used to represent a Teacher
    """
    # Name of the Teacher
    name = models.CharField(max_length=300)

    def __str__(self):
        return self.name


class Course(models.Model):
    """
    Model used to represent a Course
    """
    # The name of the course
    name = models.CharField(max_length=200)

    # The teacher of the course. Can be null
    teacher = models.ForeignKey('Teacher', blank=True, null=True)

    # The parent course of the current course. Can be null
    parent_course = models.ForeignKey('Course', blank=True, null=True)

    # Users that are authorized to view the course
    authorized_users = models.ManyToManyField('auth.user')

    def __str__(self):
        return self.name


class Recording(models.Model):
    """
    Model used to represent a Recording
    """

    # Name of the recording
    name = models.CharField(max_length=200)

    # Date of the recording, the default value is the submit time
    date = models.DateTimeField(default=now)

    # A string that rapresents the current status of the recording
    status = models.CharField(max_length=200, default="SUBMITTED")

    # True if the recording file is online
    is_online = models.BooleanField(default=False)

    # True if the recording file has finished conversion
    is_converted = models.BooleanField(default=False)

    # Course to which the Recording belongs to. If null, represents the root course ( or no course at all )
    course = models.ForeignKey('Course', blank=True, null=True)

    # The recording author User
    user = models.ForeignKey('auth.user')

    def __str__(self):
        return self.name


class RecordingFile(models.Model):
    """
    Model used to represent a Recording File
    """
    # Recording to which the File belongs to
    recording = models.OneToOneField(
        Recording,
        on_delete=models.CASCADE,
    )

    # Automatically set the time to the creation time
    upload_date = models.DateTimeField(auto_now=True)

    # File field that represents the actual file
    file_url = models.FileField(upload_to=settings.UPLOAD_MEDIA_URL)

    def __str__(self):
        return self.file_url.name


class Pin(models.Model):
    """
    Model used to represent a Pin
    """
    # Recording to which the Pin belongs to
    recording = models.ForeignKey('Recording', on_delete=models.CASCADE)

    # Number of milliseconds from the beginning of the file
    time = models.BigIntegerField()

    # Text of the Pin, can be null
    text = models.CharField(max_length=500, blank=True)

    # Image of the Pin, can be null
    media_url = models.FileField(upload_to=settings.UPLOAD_MEDIA_URL, blank=True)

    def __str__(self):
        return "{recording} - {time}".format(recording=str(self.recording), time=self.time)

    class Meta:
        # The couple (recording, time) must be unique: A recording can't have 2 pins at the same time
        unique_together = (('recording', 'time'),)

        # Pins will be ordered in ascending order by the time number
        ordering = ['time']
