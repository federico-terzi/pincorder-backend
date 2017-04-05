from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import PermissionDenied, APIException
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from .models import *
from .serializers import *

# class RecordingViewSet(viewsets.ViewSet):
#
#     def list(self, request):
#         if isinstance(request.user, AnonymousUser):
#             raise PermissionDenied()
#         queryset = Recording.objects.filter(user = request.user)
#         serializer = RecordingSerializer(queryset, many=True, context={'request':request})
#         return Response(serializer.data)
#
#     def retrieve(self, request, pk=None):
#         queryset = Recording.objects.all()
#         recording = get_object_or_404(queryset, pk=pk)
#         serializer = RecordingSerializer(recording)
#         return Response(serializer.data)


class RecordingViewSet(viewsets.ModelViewSet):

    serializer_class = RecordingSerializer

    def get_queryset(self):
        if isinstance(self.request.user, AnonymousUser):
            raise PermissionDenied()
        return Recording.objects.filter(user=self.request.user)

    @list_route(methods=['get'])
    def search_by_name(self, request):
        if isinstance(self.request.user, AnonymousUser):
            raise PermissionDenied()
        if not 'name' in self.request.query_params:
            raise APIException("ERROR: You must specify the 'name' parameter")
        recordings = Recording.objects.filter(user=self.request.user)\
                                      .filter(name__contains=request.query_params['name'])
        serializer = RecordingSerializer(data=recordings, many=True, context={'request': request})
        serializer.is_valid()
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class RecordingFileViewSet(viewsets.ModelViewSet):

    serializer_class = RecordingFileSerializer

    def get_queryset(self):
        if isinstance(self.request.user, AnonymousUser):
            raise PermissionDenied()
        return RecordingFile.objects.filter(recording__user=self.request.user)

class CourseViewSet(viewsets.ViewSet):

    def list(self, request):
        queryset = Course.objects.all()
        serializer = CourseSerializer(queryset, many=True, context={'request':request})
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Course.objects.all()
        course = get_object_or_404(queryset, pk=pk)
        serializer = CourseSerializer(course)
        return Response(serializer.data)