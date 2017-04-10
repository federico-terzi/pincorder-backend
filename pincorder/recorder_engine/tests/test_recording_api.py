import datetime
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

        teacher = Teacher.objects.create(name="Anna Rossi")
        course1 = Course.objects.create(name="Operative System", teacher=teacher)
        course1.authorized_users.add(self.currentUser)

        teacher2 = Teacher.objects.create(name="Carlo Verdi")
        course2 = Course.objects.create(name="Telecom", teacher=teacher2)
        course2.authorized_users.add(self.currentUser)
        course2.authorized_users.add(self.currentUser2)

        # Add course, but don't authorize the testuser
        teacher3 = Teacher.objects.create(name="Paola Gialli")
        course3 = Course.objects.create(name="Math", teacher=teacher3)
        course3.authorized_users.add(self.currentUser2)

        # Add recordings for testuser
        r1 = Recording.objects.create(name="First Registration", date=timezone.now(),
                                      course=course1, user=self.currentUser)
        r2 = Recording.objects.create(name="Second Registration",
                                      date=timezone.now()-datetime.timedelta(hours=5),
                                      course=course1, user=self.currentUser)
        r2 = Recording.objects.create(name="Third Registration",
                                      date=timezone.now() - datetime.timedelta(hours=10),
                                      course=course2, user=self.currentUser)

    def get_logged_client(self, user=None):
        if user is None:
            user = self.currentUser
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_recording_not_authorized(self):
        client = APIClient()
        response = client.get('/api/recordings/')
        self.assertEqual(response.status_code, 401)

    def test_recording_should_be_authorized(self):
        client = self.get_logged_client()
        response = client.get('/api/recordings/')
        self.assertEqual(response.status_code, 200)

    def test_recording_list(self):
        client = self.get_logged_client()
        response = client.get('/api/recordings/')

        self.assertContains(response, text="First Registration", status_code=200)
        self.assertContains(response, text="Second Registration", status_code=200)
        self.assertContains(response, text="Third Registration", status_code=200)

    def test_recording_get_details(self):
        client = self.get_logged_client()
        response = client.get('/api/recordings/1/')

        self.assertDictContainsSubset({'name': 'First Registration', 'status': 'SUBMITTED', 'is_online': 'false',
                       'is_converted': 'false', 'course': 1}, response.data)
