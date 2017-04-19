import datetime

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import *


class UserDumpTest(APITestCase):
    def setUp(self):
        self.currentUser = User.objects.create(username="testuser")
        self.currentUser2 = User.objects.create(username="testuser2")

        teacher = Teacher.objects.create(name="Anna Rossi")
        course1 = Course.objects.create(name="Operative System", teacher=teacher)
        course1.authorized_users.add(self.currentUser)

        self.course1 = course1

        teacher2 = Teacher.objects.create(name="Carlo Verdi")
        course2 = Course.objects.create(name="Telecom", teacher=teacher2)
        course2.authorized_users.add(self.currentUser)
        course2.authorized_users.add(self.currentUser2)

        self.course2 = course2

        # Add course, but don't authorize the testuser
        teacher3 = Teacher.objects.create(name="Paola Gialli")
        course3 = Course.objects.create(name="Math", teacher=teacher3)
        course3.authorized_users.add(self.currentUser2)

        self.course3 = course3

        # Add recordings for testuser
        r1 = Recording.objects.create(name="First Registration", date=timezone.now(),
                                      course=course1, user=self.currentUser)
        r2 = Recording.objects.create(name="Second Registration",
                                      date=timezone.now()-datetime.timedelta(hours=5),
                                      course=course1, user=self.currentUser)
        r3 = Recording.objects.create(name="Third Registration",
                                      date=timezone.now() - datetime.timedelta(hours=10),
                                      course=course2, user=self.currentUser)

        self.r1 = r1
        self.r3 = r3

        # Add pins to r1
        pin1 = Pin.objects.create(recording=r1, time=10, text="Explanation 1")
        pin2 = Pin.objects.create(recording=r1, time=50)
        pin3 = Pin.objects.create(recording=r1, time=100, text="Explanation 2")

        # Add recordings for testuser2
        r4 = Recording.objects.create(name="Test2 Registration", date=timezone.now(),
                                      course=course3, user=self.currentUser2)
        self.r4 = r4

    def get_logged_client(self, user=None):
        if user is None:
            user = self.currentUser
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_userdump_contains_user_info(self):
        client = self.get_logged_client()
        response = client.get('/api/user_dump/')

        self.assertDictContainsSubset({'id': self.currentUser.id, 'username': 'testuser',
                                       'first_name': '', 'last_name': '',
                                       'email': ''}, response.data['user'])

    def test_userdump_contains_courses(self):
        client = self.get_logged_client()
        response = client.get('/api/user_dump/')

        self.assertEqual(len(response.data['courses']), 2)
        self.assertDictContainsSubset({'id': self.course1.id, 'name': 'Operative System'}, response.data['courses'][0])
        self.assertDictContainsSubset({'id': self.course1.id, 'name': 'Anna Rossi'}, response.data['courses'][0]['teacher'])

        self.assertDictContainsSubset({'id': self.course2.id, 'name': 'Telecom'}, response.data['courses'][1])
        self.assertDictContainsSubset({'id': self.course2.id, 'name': 'Carlo Verdi'}, response.data['courses'][1]['teacher'])

    def test_userdump_should_not_contain_unauthorized_courses(self):
        client = self.get_logged_client()
        response = client.get('/api/user_dump/')

        self.assertNotContains(response, text='Paola Gialli')

    def test_userdump_contains_recordings(self):
        client = self.get_logged_client()
        response = client.get('/api/user_dump/')

        self.assertEqual(len(response.data['recordings']), 3)
        self.assertDictContainsSubset({'id': self.r1.id, 'name': 'First Registration'}, response.data['recordings'][0])
        self.assertEqual(response.data['recordings'][0]['course']['id'], self.course1.id)

        self.assertDictContainsSubset({'id': self.r3.id, 'name': 'Third Registration'}, response.data['recordings'][2])
        self.assertEqual(response.data['recordings'][2]['course']['id'], self.course2.id)

    def test_userdump_contains_pins(self):
        client = self.get_logged_client()
        response = client.get('/api/user_dump/')

        self.assertEqual(len(response.data['recordings'][0]['pin_set']), 3)
        self.assertDictContainsSubset({'time': 10,
                                       'text': 'Explanation 1'}, response.data['recordings'][0]['pin_set'][0])
        self.assertDictContainsSubset({'time': 50,
                                       }, response.data['recordings'][0]['pin_set'][1])
        self.assertDictContainsSubset({'time': 100,
                                       'text': 'Explanation 2'}, response.data['recordings'][0]['pin_set'][2])

    def test_userdump_recording_should_not_contain_pins(self):
        client = self.get_logged_client()
        response = client.get('/api/user_dump/')

        self.assertEqual(len(response.data['recordings'][1]['pin_set']), 0)