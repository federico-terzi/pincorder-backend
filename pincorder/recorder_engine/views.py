from django.contrib.auth.models import AnonymousUser
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
    This API is used to add, list and get information about recordings.
    
    ---
    
    **Get a Recording by ID**
    
    Return the Recording with the specified ID
    
    *USAGE*
    
    ```
    GET: .../api/recordings/{RECORDING_ID}/ 
    ```
    ---
    
    **Create a Recording**
    
    Create a Recording with the specified POST parameters
    
    *USAGE*
    
    ```
    POST: .../api/recordings/
    ```
    ---
    **Add a Batch of Pins at once**
    
    Add a Batch of Pins at once. 
    You must provide the "batch" post parameter, containing a list of pins.
    
    *USAGE*
    
    ```
    POST: .../api/recordings/{YOUR_RECORDING_ID}/add_pin_batch/
    ```
    ---
    **Get the file of a the current Recording**
    
    Return the file of the specified Recording, if it doesn't exist, it returns "NO_RECORDING_FOUND"
    
    **Note**: return a list of files
    
    *USAGE*
    
    ```
    GET: .../api/recordings/{YOUR_RECORDING_ID}/get_file/
    ```
    ---
    **Search a Recording by Name**
    
    Return the Recording with a name containing the specified string
    
    *USAGE*
    
    ```
    GET: .../api/recordings/search_by_name/?name={YOUR_SEARCH_STRING}
    ```
    
    ---
    **Get Recording Pins**
    
    Return the list of the Recording's Pins
    
    *USAGE*
    
    ```
    GET: .../api/recordings/{RECORDING_ID}/get_pins/
    ```
    
    """
    serializer_class = RecordingSerializer

    def get_queryset(self):
        # Return the recordings of the current user
        return Recording.objects.filter(user=self.request.user)

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
            serializer = RecordingFileSerializer(files, many=True, context={'request': request})

            return Response(serializer.data)

    @detail_route(methods=['get'])
    def get_status(self, request, pk=None):
        """
        Return the status of the current recording
        """

        # Get the recordings made by the user and having a name that contains the specified param
        recording = get_object_or_404(Recording.objects.filter(user=self.request.user), pk=pk)

        return Response({'status': recording.status})

    @detail_route(methods=['get'])
    def get_pins(self, request, pk=None):
        """
        Return the pins of the current recording
        """

        # Get the pins for the current recording and user
        pins = Pin.objects.filter(recording__user_id=self.request.user)\
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
                raise APIException("ERROR: "+str(serializer.errors))

    @detail_route(methods=['post'])
    def add_pin_batch(self, request, pk=None):
        """
        Add Multiple Pins at once
        """

        # Check if the user is the author of the recording, if not throw and exception
        if not Recording.objects.filter(id=pk).filter(user=self.request.user).exists():
            raise Http404("ERROR: You can't access this recording or it doesn't exists")

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

    def perform_create(self, serializer):
        # Get the posted recording
        recording = serializer.get_recording()

        # Check if the user is allowed to write in this course, if not, throw an exception
        if self.request.user not in recording.course.authorized_users.all():
            raise PermissionDenied("You're not allowed to write in this course!")

        # If the user is authorized, save the recording
        serializer.save(user=self.request.user)


class RecordingFileViewSet(viewsets.ModelViewSet):
    """
    This API is used to get and upload Recording Audios.
    
    ---
    **Get a List of Files for the current user**
    
    *USAGE*
    
    ```
    GET: .../api/recording_files/ 
    ```
    ---
    
    **Upload a Recording**
    
    Upload a recording
    
    *USAGE*
    
    ```
    POST: .../api/recording_files/
    ```
    ---
    **Get the File from the Recording ID**
    
    Note: return a list of files
    
    *USAGE*
    
    ```
    GET: .../api/recording_files/get_file_by_recording_id/?id={YOUR_RECORDING_ID}
    ```
    
    """
    serializer_class = RecordingFileSerializer

    def get_queryset(self):
        """
        Set the queryset for the current user 
        """

        # Return the Files for the current user
        return RecordingFile.objects.filter(recording__user=self.request.user)

    @list_route(methods=['get'])
    def get_file_by_recording_id(self, request):
        """
        Return the file url for the specified Recording ID
        """

        # Make sure that the user passes the 'id' parameter, if not, raise an exception
        if 'id' not in self.request.query_params:
            raise APIException("ERROR: You must specify the 'id' parameter")

        # Fetch the files for the current user and Recording id
        files = RecordingFile.objects.filter(recording__user_id=self.request.user)\
                                     .filter(recording__id=self.request.query_params['id'])

        # Check if recording has files
        if files.count() == 0:
            # If not, raise an exception
            raise APIException('NO_RECORDING_FOUND')
        else:
            # Serialize the files
            serializer = RecordingFileSerializer(files, many=True, context={'request': request})

            return Response(serializer.data)

    def perform_create(self, serializer):
        # Get the posted recording
        file = serializer.get_file()

        # Check if the user is allowed to write in this recording, if not, throw an exception
        if file.recording.user != self.request.user:
            raise PermissionDenied("You're not allowed to write in this recording!")

        # If the user is allowed, create the RecordingFile
        return super().perform_create(serializer)


class CourseViewSet(viewsets.ModelViewSet):
    """
    This API is used to create and list courses.

    ---
    **Add a Course**

    *USAGE*

    ```
    POST: .../api/courses/ 
    ```
    ---

    **Get Course info**

    *USAGE*

    ```
    GET: .../api/courses/{YOUR_COURSE_ID}/
    ```

    """
    serializer_class = CourseSerializer

    def get_queryset(self):
        """
        Set the queryset for the current user 
        """

        # Return the courses that the current user is authorized to view
        return Course.objects.filter(authorized_users__in=[self.request.user])

    def perform_create(self, serializer):
        # Get the course and add the current user to the authorized group
        course = serializer.save()
        course.authorized_users.add(self.request.user)


class PinViewSet(viewsets.ModelViewSet):
    """
    This API is used to add pins. To get pin information, check out the recordings API.

    ---
    **Add a Pin**

    *USAGE*

    ```
    POST: .../api/pins/ 
    ```

    """

    serializer_class = PinSerializer

    def get_queryset(self):
        """
        Set the queryset for the current user 
        """

        # Return the pin user is authorized to see
        return Pin.objects.filter(recording__user_id=self.request.user)

    def list(self, request, *args, **kwargs):
        # Disable the list of pins, it doesn't have a meaning in this case
        return Response("LIST_NOT_ALLOWED")

    def perform_create(self, serializer):
        # Get the current Posted Pin
        pin = serializer.get_pin()

        # If the user can't write in this recording, throw an error
        if pin.recording.user != self.request.user:
            raise PermissionDenied("You're not allowed to write in this recording!")

        # If the user is allowed, create the object
        return super().perform_create(serializer)


class UserDump(APIView):
    """
    This API is used to retrive all the profile, courses and recordings information for the current user
    """
    def get(self, request, format=None):
        # Get all the recordings for the current user
        recordings = Recording.objects.filter(user=request.user)
        # Serialize the recordings
        recording_serializer = UserDumpRecordingSerializer(recordings, many=True)

        # Serialize the user info
        user_serializer = UserDumpUserSerializer(request.user)

        # Get all the courses that user is authorized to view
        courses = Course.objects.filter(authorized_users__in=[request.user])
        # Serialize the courses information
        courses_serializer = UserDumpCourseSerializer(courses, many=True)

        # Serialize all the UserDump
        serializer = UserDumpSerializer({'recordings': recording_serializer.data, 'user': user_serializer.data,
                                         'courses': courses_serializer.data})

        return Response(serializer.data)
