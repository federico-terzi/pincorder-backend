from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from . import views


# Define urls for the APIs
router = DefaultRouter()
router.register(r'recordings', views.RecordingViewSet, base_name="recording")
router.register(r'courses', views.CourseViewSet, base_name="course")
router.register(r'recording_files', views.RecordingFileViewSet, base_name="recording_files")
router.register(r'pins', views.PinViewSet, base_name="pins")

# Define the url patterns for the API
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^user_dump/$', views.UserDump.as_view(), name='user-dump')  # User Dump URL
]