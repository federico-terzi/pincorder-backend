import os, uuid

from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


# Utility methods

def unique_name_generator(instance, filename):
    """
    Generate an unique filename
    """
    ext = filename.split('.')[-1]
    final_name = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join(settings.UPLOAD_MEDIA_URL, final_name)


# Models

class Profile(models.Model):
    """
    Model connected to a user and represents the user profile data
    """
    # User to which the Profile belongs to
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )

    # Shared Recordings with the user
    shared_recordings = models.ManyToManyField('Recording')

    # Shared courses with the user
    shared_courses = models.ManyToManyField('Course')


class Teacher(models.Model):
    """
    Model used to represent a Teacher
    """
    # Name of the Teacher
    name = models.CharField(max_length=300)

    def __str__(self):
        return self.name

    class Meta:
        # Teachers will be ordered in ascending order by the name
        ordering = ['name']


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

    # Represents the privacy level of the course
    # 0 is private, 1 is shared and 2 is public
    privacy = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        # Courses will be ordered in ascending order by the ID
        ordering = ['id']


class Recording(models.Model):
    """
    Model used to represent a Recording
    """

    # Name of the recording
    name = models.CharField(max_length=200)

    # Date of the recording
    date = models.DateTimeField()

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

    # Represents the privacy level of the recording
    # 0 is private, 1 is shared and 2 is public
    privacy = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        # Recordings will be ordered in ascending order by the ID
        ordering = ['id']


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

    # File field that represents the actual file ( a unique name is given to each file )
    file_url = models.FileField(upload_to=unique_name_generator)

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

    # Image of the Pin, can be null ( a unique name is given to each image )
    media_url = models.FileField(upload_to=unique_name_generator, blank=True)

    def __str__(self):
        return "{recording} - {time}".format(recording=str(self.recording), time=self.time)

    class Meta:
        # The couple (recording, time) must be unique: A recording can't have 2 pins at the same time
        unique_together = (('recording', 'time'),)

        # Pins will be ordered in ascending order by the time number
        ordering = ['time']


# Post Delete Handlers, used to delete media files after instances are deleted

@receiver(post_delete, sender=Pin)
def pin_post_delete_handler(sender, **kwargs):
    """
    Delete the Pin Image after the object is deleted
    """
    photo = kwargs['instance']
    if photo.media_url:
        storage, path = photo.media_url.storage, photo.media_url.path
        storage.delete(path)


@receiver(post_delete, sender=RecordingFile)
def recording_file_post_delete_handler(sender, **kwargs):
    """
    Delete the Recording file after the object is deleted
    """
    recording_file = kwargs['instance']
    if recording_file.file_url:
        storage, path = recording_file.file_url.storage, recording_file.file_url.path
        storage.delete(path)


# Signals used to keep the profile in sync with the user

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    When a new user is created, create a new profile linked to it
    """
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    When a user is updated, save the profile
    """
    instance.profile.save()
