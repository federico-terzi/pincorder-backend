import os, uuid

from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.http import Http404
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
    shared_recordings = models.ManyToManyField('Recording', blank=True)

    # Shared courses with the user
    shared_courses = models.ManyToManyField('Course', blank=True)


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


class CourseManager(models.Manager):
    """
    Custom Manager for the Course model
    """
    def get_courses_for_user(self, user):
        """
        Return the courses that the passed user is author of.
        """
        return self.get_queryset().filter(authorized_users__in=[user])

    def get_shared_courses_for_user(self, user):
        """
        Return a queryset that include all the shared courses of the user, 
        but not the private ones.
        
        Note: the check of the privacy status is necessary because if a user shares
              a course and then makes it private again, the shared user
              shouldn't be able to view it. 
        """
        # Get all the shared courses of the user, but not the private ones
        # Note: the check of the privacy status is necessary because if a user shares
        #       a course and then makes it private again, the shared user
        #       shouldn't be able to view it.
        shared_courses = self.get_queryset().filter(id__in=user.profile.shared_courses.values('id')) \
                                            .filter(privacy__gt=0)

        return shared_courses

    def check_user_is_author_of_course_id(self, user, course_id, throw_404=False):
        """
        Check if the passed user is the author of the course having the passed id.
        If throw_404=True, instead of returning False, it raise an Http404 Exception.
        """
        # True if the course exists and the user is the author, False otherwise
        result = self.get_queryset().filter(id=course_id)\
                                    .filter(authorized_users__in=[user]).exists()

        # If the result is True, return True
        if result:
            return True
        else:
            # If throw_404 is True, throw an Http404 exception. Return False otherwise.
            if throw_404:
                raise Http404("ERROR: Course doesn't exists or you're not authorized!")
            else:
                return False


class Course(models.Model):
    """
    Model used to represent a Course
    """
    # The name of the course
    name = models.CharField(max_length=200)

    # The teacher of the course. Can be null
    teacher = models.ForeignKey('Teacher', blank=True, null=True)

    # The parent course of the current course. Can be null.
    # To get all the children of a course use Course.children.all()
    parent_course = models.ForeignKey('self', blank=True, null=True, related_name='children')

    # Users that are authorized to view the course
    authorized_users = models.ManyToManyField('auth.user')

    # Represents the privacy level of the course
    # 0 is private, 1 is shared and 2 is public
    privacy = models.IntegerField(default=0)

    # Add the default manager
    objects = models.Manager()

    # Add the CourseManager
    custom = CourseManager()

    def __str__(self):
        return self.name

    def share_with_user(self, user):
        """
        Share the current course with the passed user
        """
        # If the course is private ( privacy = 0 ), make the course shared ( privacy = 1 )
        # Note: if the course is already shared, or is public, this doesn't modify it
        if self.privacy == 0:
            # Change the course privacy to shared
            self.privacy = 1

        # Save the course
        self.save()

        # If the course wasn't already shared with the shared user
        if self not in user.profile.shared_courses.all():
            # Add the course to the collection of shared courses of the shared user
            user.profile.shared_courses.add(self)

            # Then save the changes
            user.save()

        # Share all the subcourses
        for course in self.children.all():
            course.share_with_user(user)

    class Meta:
        # Courses will be ordered in ascending order by the ID
        ordering = ['id']


class RecordingManager(models.Manager):
    """
    Custom manager for the Recording Model
    """
    def get_recordings_for_user(self, user, include_shared=False):
        """
        Return a queryset of the recordings belonging to the specified user
        If include_shared=True, also include the recordings shared with the user 
        """
        # Get the recordings belonging to the user
        user_recordings = self.get_queryset().filter(user=user)

        # Check if shared recording should be included
        if include_shared:
            # Get the shared recordings for the user
            shared_recordings = self.get_shared_recordings(user)

            # Union of the user_recordings and shared_recordings
            recordings = user_recordings | shared_recordings

            # Return the Recordings queryset
            return recordings
        else:
            # Return the Recordings queryset
            return user_recordings

    def get_shared_recordings(self, user, shared_courses=None):
        """
        Return a queryset containing the recordings shared with the specified user.
        If shared_courses is passed, instead of making a new query, it uses the
        passed queryset ( Used for efficiency purposes ).
        """
        # For efficiency purposes, if you already calculated the shared_courses queryset,
        # you can pass it, in this way the query isn't repeated.
        # If the shared course queryset is not passed, make the query
        if shared_courses is None:
            # Get all the shared courses of the user
            shared_courses = Course.custom.get_shared_courses_for_user(user)

        # Get all the shared recordings of the user, but not the private ones
        # Shared recordings are the union of recordings that are directly shared
        # or recordings belonging to a shared course
        # Note: the check of the privacy status is necessary because if a user shares
        #       a recording and then makes it private again, the shared user
        #       shouldn't be able to view it.

        # Get the recordings shared directly with the user
        shared_recordings_only = self.get_queryset().filter(id__in=user.profile.shared_recordings.values('id')) \
                                                    .filter(privacy__gt=0)

        # Get the recordings belonging to a shared course
        shared_recordings_from_courses = self.get_queryset().filter(course__id__in=shared_courses.values('id'))

        # Union of the two sources of recordings
        shared_recordings = (shared_recordings_only | shared_recordings_from_courses)

        # Return the shared recordings
        return shared_recordings

    def check_user_is_author_of_recording_id(self, user, recording_id, throw_404=False):
        """
        Check if the passed user is the author of the recording having the passed id.
        If throw_404=True, instead of returning False, it raise an Http404 Exception.
        """
        # True if the recording exists and the user is the author, False otherwise
        result = self.get_queryset().filter(id=recording_id)\
                                    .filter(user=user).exists()

        # If the result is True, return True
        if result:
            return True
        else:
            # If throw_404 is True, throw an Http404 exception. Return False otherwise.
            if throw_404:
                raise Http404("ERROR: You can't access this recording or it doesn't exists")
            else:
                return False


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

    # Add the default Manager
    objects = models.Manager()

    # Add the RecordingManager
    custom = RecordingManager()

    def is_author(self, user):
        """
        Check if the passed user is the author of the recording
        """
        return self.user.id == user.id

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
