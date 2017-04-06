from django.contrib.auth.models import AnonymousUser
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.exceptions import PermissionDenied, APIException
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .serializers import *


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
    
    """
    serializer_class = RecordingSerializer

    def get_queryset(self):
        # If the user is not authenticated, raise an exception
        if isinstance(self.request.user, AnonymousUser):
            raise PermissionDenied()

        # Return the recordings of the current user
        return Recording.objects.filter(user=self.request.user)

    @list_route(methods=['get'])
    def search_by_name(self, request):
        """
        Search for Recordings with a name containing the specified parameter
        """
        # If the user is not authenticated, raise an exception
        if isinstance(self.request.user, AnonymousUser):
            raise PermissionDenied()

        # Make sure that the user passes the 'name' parameter, if not, raise an exception
        if 'name' not in self.request.query_params:
            raise APIException("ERROR: You must specify the 'name' parameter")

        # Get the recordings made by the user and having a name that contains the specified param
        recordings = Recording.objects.filter(user=self.request.user) \
                                      .filter(name__contains=request.query_params['name'])

        # Serialize the data
        serializer = RecordingSerializer(data=recordings, many=True, context={'request': request})
        serializer.is_valid()  # Needed to make the request work

        return Response(serializer.data)

    @detail_route(methods=['get'])
    def get_file(self, request, pk=None):
        """
        Return the file for the current Recording
        """
        # If the user is not authenticated, raise an exception
        if isinstance(self.request.user, AnonymousUser):
            raise PermissionDenied()

        # Fetch the files for the current user and Recording id
        files = RecordingFile.objects.filter(recording__user_id=self.request.user) \
                                     .filter(recording__id=pk)

        # Check if recording has files
        if files.count() == 0:
            # If not, raise an exception
            raise APIException('NO_RECORDING_FOUND')
        else:
            # Serialize the files
            serializer = RecordingFileSerializer(data=files, many=True, context={'request': request})
            serializer.is_valid()

            return Response(serializer.data)

    @detail_route(methods=['get'])
    def get_status(self, request, pk=None):
        """
        Return the status of the current recording
        """
        # If the user is not authenticated, raise an exception
        if isinstance(self.request.user, AnonymousUser):
            raise PermissionDenied()

        # Get the recordings made by the user and having a name that contains the specified param
        recording = get_object_or_404(Recording.objects.filter(user=self.request.user), pk=pk)

        return Response({'status': recording.status})

    def perform_create(self, serializer):
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
        # If the user is not authenticated, raise an exception
        if isinstance(self.request.user, AnonymousUser):
            raise PermissionDenied()

        # Return the Files for the current user
        return RecordingFile.objects.filter(recording__user=self.request.user)

    @list_route(methods=['get'])
    def get_file_by_recording_id(self, request):
        """
        Return the file url for the specified Recording ID
        """
        # If the user is not authenticated, raise an exception
        if isinstance(self.request.user, AnonymousUser):
            raise PermissionDenied()

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
            serializer = RecordingFileSerializer(data=files, many=True, context={'request': request})
            serializer.is_valid()

            return Response(serializer.data)


class CourseViewSet(viewsets.ModelViewSet):

    serializer_class = CourseSerializer

    def get_queryset(self):
        """
        Set the queryset for the current user 
        """
        # If the user is not authenticated, raise an exception
        if isinstance(self.request.user, AnonymousUser):
            raise PermissionDenied()

        # Return the courses that the current user is authorized to view
        return Course.objects.filter(authorized_users__in=[self.request.user])
