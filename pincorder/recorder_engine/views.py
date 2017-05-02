from django.contrib.auth.models import AnonymousUser
from django.db.models import QuerySet
from django.http import Http404
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route, parser_classes
from rest_framework.exceptions import PermissionDenied, APIException
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView

from .serializers import *

from oauth2_provider.ext.rest_framework import TokenHasReadWriteScope, TokenHasScope, permissions


class RecordingViewSet(viewsets.ModelViewSet):
    """
    Using this API you will be able to create, edit and manage Recordings and Pins.
    
    [Check out the full documentation on GitHub](https://github.com/federico-terzi/pincorder-backend/wiki/Recording-API)
    
    """
    serializer_class = RecordingSerializer

    def get_queryset(self):
        # Return the recordings of the current user
        return Recording.custom.get_recordings_for_user(self.request.user)

    @list_route(methods=['get'])
    def search_by_name(self, request):
        """
        Search for Recordings with a name containing the specified parameter
        """

        # Make sure that the user passes the 'name' parameter, if not, raise an exception
        if 'name' not in self.request.query_params:
            raise APIException("ERROR: You must specify the 'name' parameter")

        # Get the recordings made by the user and having a name that contains the specified param
        recordings = Recording.objects.filter(user=self.request.user) \
            .filter(name__contains=request.query_params['name'])

        # Serialize the data
        serializer = RecordingSerializer(recordings, many=True, context={'request': request})

        return Response(serializer.data)

    @detail_route(methods=['get'])
    def get_file(self, request, pk=None):
        """
        Return the file for the current Recording
        """

        # Fetch the files for the current user and Recording id
        files = RecordingFile.objects.filter(recording__user_id=self.request.user) \
            .filter(recording__id=pk)

        # Check if recording has files
        if files.count() == 0:
            # If not, raise an exception
            raise APIException('NO_RECORDING_FOUND')
        else:
            # Serialize the files
            serializer = RecordingFileSerializer(files.first(), context={'request': request})

            return Response(serializer.data)

    @detail_route(methods=['get'])
    def get_status(self, request, pk=None):
        """
        Return the status of the current recording
        """

        # Get the recordings made by the user and having a name that contains the specified param
        recording = get_object_or_404(Recording.objects.filter(user=self.request.user), pk=pk)

        return Response({'status': recording.status})

    @detail_route(methods=['post'])
    @parser_classes((FormParser, MultiPartParser,))
    def upload_file(self, request, pk=None):
        """
        Upload the audio file to a recording
        """
        # Check if the user is the author of the recording, if not throw and exception
        Recording.custom.check_user_is_author_of_recording_id(user=request.user, recording_id=pk, throw_404=True)

        # Check if the file already exists
        if RecordingFile.objects.filter(recording_id=pk).exists():
            raise APIException("ERROR: The File already exists")

        # Copy the request data
        input_data = request.data.copy()

        # Add the recording reference for the foreign key
        input_data['recording'] = pk

        # Get the serializer
        serializer = RecordingFileSerializer(data=input_data)

        # Check if the serialized data is valid
        if serializer.is_valid():
            # Check that the file is an AAC audio file or MP3 audio file
            if not request.data['file_url'].name.endswith(".aac") and not request.data['file_url'].name.endswith(
                    ".mp3"):
                raise APIException("ERROR: Wrong file format!")

            # Save and get the RecordingFile
            file = serializer.save()

            # Return the response
            return Response(serializer.data)
        else:
            raise APIException("ERROR: " + str(serializer.errors))

    @detail_route(methods=['get'])
    def get_pins(self, request, pk=None):
        """
        Return the pins of the current recording
        """

        # Get the pins for the current recording and user
        pins = Pin.objects.filter(recording__user_id=self.request.user) \
            .filter(recording_id=pk).order_by('time')

        # Get the serializer
        serializer = PinSerializer(pins, many=True, context={'request': request})

        # Return the response
        return Response(serializer.data)

    @detail_route(methods=['post'])
    @parser_classes((FormParser, MultiPartParser,))
    def add_pin(self, request, pk=None):
        """
        Add or Update a Pin
        """
        # Check if the user is the author of the recording, if not throw and exception
        Recording.custom.check_user_is_author_of_recording_id(user=request.user, recording_id=pk, throw_404=True)

        # Get the pins of the current recording
        pins = Recording.objects.get(pk=pk).pin_set

        try:
            # Try to get the pin
            pin = pins.get(time=request.data['time'])

            # If the text param exists, update it
            if 'text' in request.data:
                pin.text = request.data['text']
            else:
                pin.text = ""

            # If the media_url param exists, update it
            if 'media_url' in request.data:
                # Check the media_url file format, only JPG and PNG is accepted.
                if not request.data['media_url'].name.endswith(".jpg") and not request.data['media_url'].name.endswith(
                        ".png"):
                    raise APIException("ERROR: Wrong file format!")
                # Delete the old image
                pin.media_url.delete()
                # Get the uploaded file
                upload = request.data['media_url']
                # Save the uploaded image
                pin.media_url.save(upload.name, upload)

            # Save the pin
            pin.save()

            # Return the response
            return Response(PinSerializer(pin).data)
        except Pin.DoesNotExist:
            # Copy the request data
            input_data = request.data.copy()

            # Add the recording reference for the foreign key
            input_data['recording'] = pk

            # Get the serializer
            serializer = PinSerializer(data=input_data)

            # Check if the serialized data is valid
            if serializer.is_valid():
                # Save and get the pin
                pin = serializer.save()

                # If the media_url param exists, update it
                if 'media_url' in request.data:
                    # Check the media_url file format, only JPG and PNG is accepted.
                    if not request.data['media_url'].name.endswith(".jpg") and not request.data['media_url'].name\
                            .endswith(".png"):
                        raise APIException("ERROR: Wrong file format!")
                    # Delete the old image
                    pin.media_url.delete()
                    # Get the uploaded file
                    upload = request.data['media_url']
                    # Save the uploaded image
                    pin.media_url.save(upload.name, upload)
                    # Save the pin
                    pin.save()

                # Return the response
                return Response(serializer.data)
            else:
                # If the serialized data is not valid, raise an error
                raise APIException("ERROR: " + str(serializer.errors))

    @detail_route(methods=['delete'])
    def delete_pin(self, request, pk=None):
        """
        Delete a Pin
        """
        # Check if the user is the author of the recording, if not throw and exception
        Recording.custom.check_user_is_author_of_recording_id(user=request.user, recording_id=pk, throw_404=True)

        # Check if the pin exists in the specified time
        try:
            # Get the pin at the specified time
            pin = Recording.objects.get(id=pk).pin_set.get(time=request.data['time'])

            # Delete the pin
            pin.delete()

            # Return the response
            return Response("OK")
        except Pin.DoesNotExist:
            # If no pin is found, raise an Exception
            raise Http404('ERROR: No Pin at that time!')

    @detail_route(methods=['post'])
    def add_pin_batch(self, request, pk=None):
        """
        Add Multiple Pins at once
        """
        # Check if the user is the author of the recording, if not throw and exception
        Recording.custom.check_user_is_author_of_recording_id(user=request.user, recording_id=pk, throw_404=True)

        # Make sure that the user passes the 'batch' POST parameter, if not, raise an exception
        if 'batch' not in self.request.data:
            raise APIException("ERROR: You must specify the 'batch' parameter containing the data")

        # Get the data from the batch POST parameter
        data = self.request.data['batch']

        # Get the pins of the current recording
        pins = Recording.objects.get(pk=pk).pin_set.all()

        # Initialize a list that will hold the pins
        output_data = []

        for d in data:
            # For each pin in the batch, add the current recording
            d['recording'] = pk

            try:
                # If it exists, update the text
                pin = pins.get(time=d['time'])
                if 'text' in d:
                    pin.text = d['text']
                else:
                    pin.text = ""
                pin.save()
            except Pin.DoesNotExist:
                # If the pin doesn't already exist in the database, append it to output_data
                output_data.append(d)

        # Create the serializer with the output_data
        serializer = PinSerializer(data=output_data, many=True, context={'request': request})

        # If it's valid, save the pins
        if serializer.is_valid():
            serializer.save()

        return Response(serializer.data)

    @detail_route(methods=['post'])
    def share_recording_with_user(self, request, pk=None):
        """
        Share a recording with the specified user
        """
        # Check if the user is the author of the recording, if not throw and exception
        Recording.custom.check_user_is_author_of_recording_id(user=request.user, recording_id=pk, throw_404=True)

        # Make sure that the user passes the 'shared_user' POST parameter, if not, raise an exception
        if 'shared_user' not in self.request.data:
            raise APIException("ERROR: You must specify the 'shared_user' parameter containing the data")

        # Get the shared user ID from the batch POST parameter
        shared_user_id = self.request.data['shared_user']

        # Try to get the shared user object
        try:
            # Get the user object
            shared_user = User.objects.get(id=shared_user_id)

            # Get the current recording
            recording = Recording.objects.get(pk=pk)

            # Share the recording with the user
            recording.share_with_user(shared_user)

            # Return an OK response
            return Response("OK")

        except User.DoesNotExist:
            # Raise an exception if the user doesn't exist
            raise Http404("ERROR: shared user not found!")

    def perform_create(self, serializer):
        """
        Called when a Recording object is created
        """
        # Get the posted recording
        recording = serializer.get_recording()

        # Check if a course is specified by the request
        if recording.course is not None:
            # Check if the user is allowed to write in this course, if not, throw an exception
            if self.request.user not in recording.course.authorized_users.all():
                raise PermissionDenied("You're not allowed to write in this course!")

        # If the user is authorized, save the recording
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """
        Called when a Recording object is updated
        """
        # Get the posted recording
        recording = serializer.get_recording()

        # Check if a course is specified by the request
        if recording.course is not None:
            # Check if the user is allowed to write in this course, if not, throw an exception
            if self.request.user not in recording.course.authorized_users.all():
                raise PermissionDenied("You're not allowed to write in this course!")

        # If the user is authorized, save the recording
        serializer.save()


class CourseViewSet(viewsets.ModelViewSet):
    """
    Using this API you will be able to create, edit and manage Courses.
    
    [Check out the full documentation on GitHub](https://github.com/federico-terzi/pincorder-backend/wiki/Course-API)

    """
    serializer_class = CourseSerializer

    def get_queryset(self):
        """
        Set the queryset for the current user 
        """

        # Return the courses that the current user is authorized to view
        return Course.custom.get_courses_for_user(self.request.user)

    @list_route(methods=['post'])
    def add_course_with_teacher(self, request):
        """
        Create a Course object and automatically create a Teacher object associated
        """
        # Check if the request contains the 'teacher' parameter
        if 'teacher' not in request.data:
            raise APIException("ERROR: You must specify the 'teacher' parameter! ( Teacher name )")

        # Check that the teacher parameter is not blank or null
        if not request.data['teacher']:
            raise APIException("ERROR: The teacher name can't be blank!")

        # Create a teacher object
        teacher = Teacher.objects.create(name=request.data['teacher'])

        # Copy the request data, in order to edit it later
        data = request.data.copy()

        # Update the teacher parameter, placing the correct teacher primary key
        data['teacher'] = teacher.id

        # Initialize the CourseSerializer with the edited request data
        serializer = CourseSerializer(data=data, context={'request': request})

        # Make sure that the serializer is valid
        if serializer.is_valid():
            # Save the course and get the Course instance
            course = serializer.save()

            # Add the current user to the course's authorized list
            course.authorized_users.add(self.request.user)

            # Return an OK response
            return Response('OK')
        else:
            # If serializer is not valid, raise an error
            raise APIException('ERROR: ' + str(serializer.errors))

    @detail_route(methods=['post'])
    def add_teacher(self, request, pk=None):
        """
        Create a Teacher instance and add it to the specified course.
        Can be used to modify an existing course teacher.
        """
        # Check that the user is authorized to edit the course, if not raise an exception
        Course.custom.check_user_is_author_of_course_id(request.user, pk, throw_404=True)

        # Check if the request contains the 'teacher' parameter
        if 'teacher' not in request.data:
            raise APIException("ERROR: You must specify the 'teacher' parameter! ( Teacher name )")

        # Check that the teacher parameter is not blank or null
        if not request.data['teacher']:
            raise APIException("ERROR: The teacher name can't be blank!")

        # Create a teacher object
        teacher = Teacher.objects.create(name=request.data['teacher'])

        # Get the current course
        course = Course.objects.get(id=pk)

        # Change the teacher with the newly created one
        course.teacher = teacher

        # Save the course
        course.save()

        # Return an OK response
        return Response('OK')

    @detail_route(methods=['post'])
    def share_course_with_user(self, request, pk=None):
        """
        Share a course with the specified user
        """

        # Check that the user is authorized to edit the course, if not raise an exception
        Course.custom.check_user_is_author_of_course_id(request.user, pk, throw_404=True)

        # Make sure that the user passes the 'shared_user' POST parameter, if not, raise an exception
        if 'shared_user' not in self.request.data:
            raise APIException("ERROR: You must specify the 'shared_user' parameter containing the data")

        # Get the shared user ID from the batch POST parameter
        shared_user_id = self.request.data['shared_user']

        # Try to get the shared user object
        try:
            # Get the user object
            shared_user = User.objects.get(id=shared_user_id)

            # Get the current course
            course = Course.objects.get(pk=pk)

            # Share the course with the shared_user
            course.share_with_user(shared_user)

            # Return an OK response
            return Response("OK")

        except User.DoesNotExist:
            # Raise an exception if the user doesn't exist
            raise Http404("ERROR: shared user not found!")

    def perform_create(self, serializer):
        """
        Called when a Course object is being created
        """
        # Get the course and add the current user to the authorized group
        course = serializer.get_course()

        # If a parent_course is specified, check if the user is authorized to edit it
        if course.parent_course is not None:
            # If not authorized, throw an exception
            if not Course.custom.check_user_is_author_of_course_id(self.request.user, course.parent_course.id):
                raise PermissionDenied("ERROR: You can't set a parent course that you can't edit")

        # Save the course and add the current user to the authorized group
        course = serializer.save()
        course.authorized_users.add(self.request.user)

    def perform_update(self, serializer):
        """
        Called when a Course object is being updated
        """
        # Get the course and add the current user to the authorized group
        course = serializer.get_course()

        # If a parent_course is specified, check if the user is authorized to edit it
        if course.parent_course is not None:
            # If not authorized, throw an exception
            if not Course.custom.check_user_is_author_of_course_id(self.request.user, course.parent_course.id):
                raise PermissionDenied("ERROR: You can't set a parent course that you can't edit")

        # Save the course and add the current user to the authorized group
        course = serializer.save()


class TeacherViewSet(viewsets.ModelViewSet):
    """
    Using this API you will be able to create, edit and manage Teachers.

    [Check out the full documentation on GitHub]()

    """
    serializer_class = TeacherSerializer

    def get_queryset(self):
        """
        Set the queryset for the current user 
        """

        # Return the teachers that the current user is authorized to view
        return Teacher.custom.get_teachers_for_user(self.request.user)

    def perform_create(self, serializer):
        """
        Called when a Teacher object is being created
        """
        # Get the teacher instance
        teacher = serializer.get_teacher()

        # Save the teacher and add the current user to the authorized group
        teacher = serializer.save()
        teacher.authorized_users.add(self.request.user)

    def perform_update(self, serializer):
        """
        Called when a Teacher object is being updated
        """
        # Get the teacher instance
        teacher = self.get_object()

        # If not authorized, throw an exception
        if not Teacher.custom.check_user_is_authorized_teacher_id(self.request.user, teacher.id):
            raise PermissionDenied("ERROR: You are not authorized to edit this teacher")

        # Save the teacher and add the current user to the authorized group
        teacher = serializer.save()

    def perform_destroy(self, instance):
        """
        Called when a Teacher object is being deleted
        """
        # Get the teacher instance
        teacher = instance

        # If not authorized, throw an exception
        if not Teacher.custom.check_user_is_authorized_teacher_id(self.request.user, teacher.id):
            raise PermissionDenied("ERROR: You are not authorized to delete this teacher")

        # Delete the teacher
        teacher.delete()


class UserDump(APIView):
    """
    This API is used to retrive all the profile, courses and recordings information for the current user
    """

    def get(self, request, format=None):
        # Get all the recordings for the current user
        recordings = Recording.custom.get_recordings_for_user(request.user, prefetch_related=True)

        # Calculate all the pins
        # Initialize the pin list
        pins = []

        # Cycle through all recordings
        for recording in recordings:
            # Current pin_batch contain the recording id and the batch list
            current_pin_batch = {'recording': recording,
                                 'batch': recording.pin_set.all()}

            # Add the current batch to the list
            pins.append(current_pin_batch)

        # Get all the courses that user is authorized to view
        courses = Course.custom.get_courses_for_user(user=request.user)

        # Get all the user related teachers
        teachers = Teacher.objects.filter(course__authorized_users__in=[request.user]).distinct()

        # Get all the shared courses of the user, but not the private ones
        shared_courses = Course.custom.get_shared_courses_for_user(request.user)

        # Get all the shared recordings of the user, but not the private ones
        # Note: private recordings that belong to a shared_course are included anyway
        shared_recordings = Recording.custom.get_shared_recordings(request.user, shared_courses)

        # Serialize all the UserDump
        serializer = UserDumpSerializer({'recordings': recordings, 'user': request.user,
                                         'courses': courses, 'teachers': teachers,
                                         'pins': pins, 'shared_courses': shared_courses,
                                         'shared_recordings': shared_recordings})

        return Response(serializer.data)
