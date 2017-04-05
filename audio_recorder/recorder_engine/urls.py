from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

router = DefaultRouter()
router.register(r'recordings', views.RecordingViewSet, base_name="recording")
router.register(r'courses', views.CourseViewSet, base_name="course")

urlpatterns = [
    url(r'^',include(router.urls))
]