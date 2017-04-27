import datetime
import os

from django.core.files.base import ContentFile
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import *


class RecordingTest(APITestCase):
    def setUp(self):
        self.currentUser = User.objects.create(username="testuser")
        self.currentUser2 = User.objects.create(username="testuser2")

        self.t1 = Teacher.objects.create(name="Anna Rossi")
        self.course1 = Course.objects.create(name="Operative System", teacher=self.t1)
        self.course1.authorized_users.add(self.currentUser)

        self.t2 = Teacher.objects.create(name="Carlo Verdi")
        self.course2 = Course.objects.create(name="Telecom", teacher=self.t2)
        self.course2.authorized_users.add(self.currentUser)
        self.course2.authorized_users.add(self.currentUser2)

        # Add course, but don't authorize the testuser
        self.t3 = Teacher.objects.create(name="Paola Gialli")
        self.course3 = Course.objects.create(name="Math", teacher=self.t3)
        self.course3.authorized_users.add(self.currentUser2)

        # Add recordings for testuser
        self.r1 = Recording.objects.create(name="First Registration", date=timezone.now(),
                                      course=self.course1, user=self.currentUser)
        self.r2 = Recording.objects.create(name="Second Registration",
                                      date=timezone.now()-datetime.timedelta(hours=5),
                                      course=self.course1, user=self.currentUser)
        self.r3 = Recording.objects.create(name="Third Registration",
                                      date=timezone.now() - datetime.timedelta(hours=10),
                                      course=self.course2, user=self.currentUser)

        # Add pins to r1
        self.pin1 = Pin.objects.create(recording=self.r1, time=10, text="Explanation 1")
        self.pin2 = Pin.objects.create(recording=self.r1, time=50, media_url="url_to_img.jpg")
        self.pin3 = Pin.objects.create(recording=self.r1, time=100, text="Explanation 2")

        # Add recordings for testuser2
        self.r4 = Recording.objects.create(name="Test2 Registration", date=timezone.now(),
                                           course=self.course3, user=self.currentUser2)

    def get_logged_client(self, user=None):
        if user is None:
            user = self.currentUser
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_recording_