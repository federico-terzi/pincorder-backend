from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'recordings', views.RecordingViewSet, base_name="recording")
router.register(r'courses', views.CourseViewSet, base_name="course")
router.register(r'recording_files', views.RecordingFileViewSet, base_name="recording_files")

urlpatterns = [
    url(r'^', include(router.urls))
]