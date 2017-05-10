import os, uuid

from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.http import Http404
from django.utils.timezone import now
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver


# Utility methods

def unique_name_generator(instance, filename):
    """
    Generate an unique filename
    """
    ext = filename.split('.')[-1]
    final_name = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join(settings.UPLOAD_MEDIA_URL, final_name)


# Managers

class ProfileManager(models.Manager):
    """
    Custom manager for the profile model, connected to the user
    """
    def add_course_to_users_that_have_shared_parent_course(self, course):
        """
        Add the passed course to all the users that have the parent_course shared.
        """
        # Get all the profiles with the shared parent_course
        profiles = self.get_queryset().filter(shared_courses__in=[course.parent_course])

        # Add to all the users the passed course
        for profile in profiles:
            # Add the passed course to the shared_courses of the user
            profile.shared_courses.add(course)
            # Save the changes
            profile.save()


class CourseManager(models.Manager):
    """
    Custom Manager for the Course model
    """

    def get_courses_for_user(self, user, include_shared=False):
        """
        Return the courses that the passed user is author of.
        """
        # Get the courses the user is author of
        courses = self.get_queryset().filter(authorized_users__in=[user])

        # If include_shared is true, also include courses shared with the user
        if include_shared:
            # Get the courses shared with the user
            shared_courses = self.get_shared_courses_for_user(user)

            # Merge the querysets
            courses = shared_courses | courses

        return courses

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
        result = self.get_queryset().filter(id=course_id) \
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


class TeacherManager(models.Manager):
    """
    Custom Manager for the Teacher model
    """

    def get_teachers_for_user(self, user, include_shared=True):
        """
        Return the teachers that the passed user is author of or the teachers
        belonging to courses viewed by the user.
        If include_shared=True, also include teachers of courses shared with the user
        """
        # Get the teachers the user is author of
        author_teachers = self.get_queryset().filter(authorized_users__in=[user])

        # Get the teachers belonging to the courses a user can view
        course_teachers = Teacher.objects.filter(id__in=Course.custom.get_courses_for_user(user, include_shared).values('teacher'))

        # Merge the teachers
        teachers = author_teachers | course_teachers

        # Delete duplicates
        teachers = teachers.distinct()

        return teachers

    def check_user_is_authorized_teacher_id(self, user, teacher_id, throw_404=False):
        """
        Check if the passed user is authorized to edit the teacher having the passed id.
        If throw_404=True, instead of returning False, it raise an Http404 Exception.
        """
        # True if the teacher exists and the user is the author, False otherwise
        result = self.get_queryset().filter(id=teacher_id) \
                                    .filter(authorized_users__in=[user]).exists()

        # If the result is True, return True
        if result:
            return True
        else:
            # If throw_404 is True, throw an Http404 exception. Return False otherwise.
            if throw_404:
                raise Http404("ERROR: Teacher doesn't exists or you're not authorized!")
            else:
                return False

    def search_by_name(self, name, user):
        """
        Return a list of Teachers that contain the passed 'name' parameter
        """
        # Get the teachers already used by the user
        user_teachers = self.get_teachers_for_user(user).filter(name__icontains=name)
        
        # Get the public teachers
        # Note: the distinct() is needed for the join with user_teachers
        public_teachers = self.get_queryset().filter(privacy__gte=2).filter(name__icontains=name).distinct()

        # Merge the teachers
        teachers = (user_teachers | public_teachers)

        # Order the results in descending privacy order, limiting the result number to TEACHER_SEARCH_RESULT_LIMIT
        teachers = teachers.order_by('-privacy')[:settings.TEACHER_SEARCH_RESULT_LIMIT]

        return teachers


class RecordingManager(models.Manager):
    """
    Custom manager for the Recording Model
    """

    def get_recordings_for_user(self, user, include_shared=False, prefetch_related=False):
        """
        Return a queryset of the recordings belonging to the specified user.
        If include_shared=True, also include the recordings shared with the user.
        If pin_set is accessed, specify prefetch_related=True to increase efficiency.
        """
        # Get the recordings belonging to the user
        user_recordings = self.get_queryset().filter(user=user)

        # If prefetch_related=True, avoid lazy loading of pins.
        if prefetch_related:
            # Prefetch all the pins
            user_recordings = user_recordings.prefetch_related('pin_set')

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
        shared_recordings_only = self.get_queryset().filter(
            id__in=user.profile.shared_recordings.values('id')) \
            .filter(privacy__gt=0)

        # Get the recordings belonging to a shared course
        shared_recordings_from_courses = self.get_queryset().filter(
            course__id__in=shared_courses.values('id'))

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
        result = self.get_queryset().filter(id=recording_id) \
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

    # Add the default manager
    objects = models.Manager()

    # Add the ProfileManager
    custom = ProfileManager()

    def __str__(self):
        return self.user.username


class University(models.Model):
    """
    Model used to represent a University
    """
    # Name of the university
    name = models.CharField(max_length=300)

    # Short name of the university
    short_name = models.CharField(max_length=100)

    def __str__(self):
        return self.short_name


class Teacher(models.Model):
    """
    Model used to represent a Teacher
    """
    # Name of the Teacher
    name = models.CharField(max_length=300)

    # Role of the teacher in the organization
    role = models.CharField(max_length=400, blank=True)

    # Organization of the teacher, relative to the university
    org = models.CharField(max_length=400, blank=True)

    # University of the teacher
    university = models.ForeignKey('University', blank=True, null=True)

    # Optional website of the teacher
    website = models.CharField(max_length=500, blank=True)

    # Represents the privacy level of the teacher
    # 0 is private, 1 is shared, 2 is public, 3 is featured
    privacy = models.IntegerField(default=0)

    # Users that are authorized to edit the teacher
    authorized_users = models.ManyToManyField('auth.user')

    # Add the default manager
    objects = models.Manager()

    # Add the TeacherManager
    custom = TeacherManager()

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

        # Make the teacher shared as well
        # Check if the teacher exists
        if self.teacher is not None:
            # If it exists, check compare the privacy level
            if self.teacher.privacy < self.privacy:
                # If the teacher privacy level is lower than course privacy level,
                # override teacer privacy level
                self.teacher.privacy = self.privacy
                # Save the changes
                self.teacher.save()

        # Add the course to the collection of shared courses of the shared user
        user.profile.shared_courses.add(self)

        # Then save the changes
        user.save()

        # Share all the subcourses
        for course in self.children.all():
            course.share_with_user(user)

    def save(self, *args, **kwargs):
        """
        Override default save method for the course model
        """
        # Check if a parent_course is present
        if self.parent_course is not None:
            # Get the privacy level of the parent course
            privacy = self.parent_course.privacy

            # If the parent course is not private, but this course is private,
            # make this course the same privacy level than the parent
            # NOTE: This have some consequences:
            # 1 - A course CANNOT be private if the parent is shared
            # 2 - A course CAN be public if the parent is shared or private
            if privacy > 0 and self.privacy == 0:
                # Make the privacy level the same as the parent
                self.privacy = privacy

        # Call the default save method
        super(Course, self).save(*args, **kwargs)

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

    # Add the default Manager
    objects = models.Manager()

    # Add the RecordingManager
    custom = RecordingManager()

    def is_author(self, user):
        """
        Check if the passed user is the author of the recording
        """
        return self.user.id == user.id

    def share_with_user(self, user):
        """
        Share the current recording with the passed user
        """
        # If the recording is private ( privacy = 0 ), make the recording shared ( privacy = 1 )
        # Note: if the recording is already shared, or is public, this doesn't modify it
        if self.privacy == 0:
            # Change the recording privacy to shared
            self.privacy = 1

        # Save the recording
        self.save()

        # Add the recording to the collection of shared recordings of the user
        user.profile.shared_recordings.add(self)

        # Then save the changes
        user.save()

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
def create_user_profile(sender, instance, created, raw, **kwargs):
    """
    When a new user is created, create a new profile linked to it
    """
    # Make sure to avoid this while loading data from a fixture.
    # In that case, raw = True
    if created and not raw:
        # Create a new profile
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, raw, **kwargs):
    """
    When a user is updated, save the profile
    """
    # Make sure to avoid this while loading data from a fixture.
    # In that case, raw = True
    if not raw:
        # Save the profile
        instance.profile.save()

# Signals used to manage the shared courses


@receiver(post_save, sender=Course)
def save_course_with_shared_parent_add_to_all_shared_users(sender, instance, created, raw, **kwargs):
    """
    When a course is created or updated and has a shared parent course
    it becomes shared as well.
    """
    # Check if the course has a parent_course
    # Make sure to avoid this while loading data from a fixture.
    # In that case, raw = True
    if instance.parent_course is not None and not raw:
        # Get the privacy of the parent_course
        privacy = instance.parent_course.privacy

        # Check if the parent_course is shared
        if privacy > 0:
            # Add the course to all the users that have the parent_course shared.
            Profile.custom.add_course_to_users_that_have_shared_parent_course(instance)


