from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from . import views


# Define urls for the APIs
router = DefaultRouter()
router.register(r'recordings', views.RecordingViewSet, base_name="recording")
router.register(r'courses', views.CourseViewSet, base_name="course")

# Define the url patterns for the API
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^user_dump/$', views.UserDump.as_view(), name='user-dump')  # User Dump URL
]