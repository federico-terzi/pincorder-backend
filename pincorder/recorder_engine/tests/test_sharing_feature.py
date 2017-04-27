import datetime
import os

from django.core.files.base import ContentFile
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import *


class SharingTest(APITestCase):
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

        # Add course, but don't authorize the testuser
        self.t4 = Teacher.objects.create(name="Domenico Verdi")
        self.course4 = Course.objects.create(name="Physics", teacher=self.t4)
        self.course4.authorized_users.add(self.currentUser2)

    def get_logged_client(self, user=None):
        if user is None:
            user = self.currentUser
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    # Recordings Sharing

    def test_share_recording_with_user(self):
        client = self.get_logged_client()

        self.assertEqual(Recording.objects.get(id=self.r1.id).privacy, 0)
        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_recordings.count(), 0)

        response = client.post('/api/recordings/' + str(self.r1.id) + '/share_recording_with_user/',
                               {'shared_user': self.currentUser2.id})

        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_recordings.count(), 1)
        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_recordings.first().id, self.r1.id)
        self.assertEqual(Recording.objects.get(id=self.r1.id).privacy, 1)

    def test_share_recording_should_fail_shared_user_doesnt_exists(self):
        client = self.get_logged_client()

        response = client.post('/api/recordings/' + str(self.r1.id) + '/share_recording_with_user/',
                               {'shared_user': '123123'})

        self.assertEqual(response.status_code, 404)

    def test_share_recording_should_fail_user_not_author_of_the_recording(self):
        client = self.get_logged_client()

        response = client.post('/api/recordings/' + str(self.r4.id) + '/share_recording_with_user/',
                               {'shared_user': self.currentUser2.id})

        self.assertEqual(response.status_code, 404)

    def test_share_recording_should_fail_recording_doesnt_exist(self):
        client = self.get_logged_client()

        response = client.post('/api/recordings/123123/share_recording_with_user/',
                               {'shared_user': self.currentUser2.id})

        self.assertEqual(response.status_code, 404)

    def test_share_recording_should_fail_shared_user_not_specified(self):
        client = self.get_logged_client()

        self.assertEqual(Recording.objects.get(id=self.r1.id).privacy, 0)
        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_recordings.count(), 0)

        response = client.post('/api/recordings/' + str(self.r1.id) + '/share_recording_with_user/',
                               {})

        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_recordings.count(), 0)
        self.assertEqual(Recording.objects.get(id=self.r1.id).privacy, 0)
        self.assertEqual(response.status_code, 500)

    def test_share_recording_should_not_change_public_privacy_status(self):
        client = self.get_logged_client()

        self.r1.privacy = 2
        self.r1.save()

        self.assertEqual(Recording.objects.get(id=self.r1.id).privacy, 2)
        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_recordings.count(), 0)

        response = client.post('/api/recordings/' + str(self.r1.id) + '/share_recording_with_user/',
                               {'shared_user': self.currentUser2.id})

        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_recordings.count(), 1)
        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_recordings.first().id, self.r1.id)
        self.assertEqual(Recording.objects.get(id=self.r1.id).privacy, 2)

    def test_share_recording_should_not_add_again_shared_recording(self):
        client = self.get_logged_client()

        self.currentUser2.profile.shared_recordings.add(self.r1)

        self.assertEqual(Recording.objects.get(id=self.r1.id).privacy, 0)
        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_recordings.count(), 1)

        response = client.post('/api/recordings/' + str(self.r1.id) + '/share_recording_with_user/',
                               {'shared_user': self.currentUser2.id})

        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_recordings.count(), 1)
        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_recordings.first().id, self.r1.id)
        self.assertEqual(Recording.objects.get(id=self.r1.id).privacy, 1)

    # Courses Sharing

    def test_share_course_with_user(self):
        client = self.get_logged_client()

        self.assertEqual(Course.objects.get(id=self.course1.id).privacy, 0)
        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_courses.count(), 0)

        response = client.post('/api/courses/' + str(self.course1.id) + '/share_course_with_user/',
                               {'shared_user': self.currentUser2.id})

        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_courses.count(), 1)
        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_courses.first().id, self.course1.id)
        self.assertEqual(Course.objects.get(id=self.course1.id).privacy, 1)

    def test_share_course_should_fail_shared_user_doesnt_exists(self):
        client = self.get_logged_client()

        response = client.post('/api/courses/' + str(self.course1.id) + '/share_course_with_user/',
                               {'shared_user': '123123'})

        self.assertEqual(response.status_code, 404)

    def test_share_course_should_fail_user_not_author_of_the_course(self):
        client = self.get_logged_client()

        response = client.post('/api/courses/' + str(self.course3.id) + '/share_course_with_user/',
                               {'shared_user': self.currentUser2.id})

        self.assertEqual(response.status_code, 404)

    def test_share_course_should_fail_course_doesnt_exist(self):
        client = self.get_logged_client()

        response = client.post('/api/courses/123123/share_course_with_user/',
                               {'shared_user': self.currentUser2.id})

        self.assertEqual(response.status_code, 404)

    def test_share_course_should_fail_shared_user_not_specified(self):
        client = self.get_logged_client()

        self.assertEqual(Course.objects.get(id=self.course1.id).privacy, 0)
        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_courses.count(), 0)

        response = client.post('/api/courses/' + str(self.course1.id) + '/share_course_with_user/',
                               {})

        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_courses.count(), 0)
        self.assertEqual(Course.objects.get(id=self.course1.id).privacy, 0)
        self.assertEqual(response.status_code, 500)

    def test_share_course_should_not_change_public_privacy_status(self):
        client = self.get_logged_client()

        self.course1.privacy = 2
        self.course1.save()

        self.assertEqual(Course.objects.get(id=self.course1.id).privacy, 2)
        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_courses.count(), 0)

        response = client.post('/api/courses/' + str(self.course1.id) + '/share_course_with_user/',
                               {'shared_user': self.currentUser2.id})

        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_courses.count(), 1)
        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_courses.first().id, self.course1.id)
        self.assertEqual(Course.objects.get(id=self.course1.id).privacy, 2)

    def test_share_course_should_not_add_again_shared_course(self):
        client = self.get_logged_client()

        self.currentUser2.profile.shared_courses.add(self.course1)

        self.assertEqual(Course.objects.get(id=self.course1.id).privacy, 0)
        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_courses.count(), 1)

        response = client.post('/api/courses/' + str(self.course1.id) + '/share_course_with_user/',
                               {'shared_user': self.currentUser2.id})

        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_courses.count(), 1)
        self.assertEqual(User.objects.get(id=self.currentUser2.id).profile.shared_courses.first().id, self.course1.id)
        self.assertEqual(Course.objects.get(id=self.course1.id).privacy, 1)

    # Userdump tests

    def test_userdump_contains_shared_courses(self):
        client = self.get_logged_client()

        self.currentUser.profile.shared_courses.add(self.course3)
        self.currentUser.save()

        self.course3.privacy = 1
        self.course3.save()

        response = client.get('/api/user_dump/')

        self.assertEqual(len(response.data['shared_courses']), 1)
        self.assertDictContainsSubset({'id': self.course3.id, 'name': self.course3.name, 'privacy': 1},
                                      response.data['shared_courses'][0])
        self.assertDictContainsSubset({'teacher': self.course3.teacher.id}, response.data['shared_courses'][0])

    def test_userdump_contains_shared_courses_that_are_public(self):
        client = self.get_logged_client()

        self.currentUser.profile.shared_courses.add(self.course3)
        self.currentUser.save()

        self.course3.privacy = 2
        self.course3.save()

        response = client.get('/api/user_dump/')

        self.assertEqual(len(response.data['shared_courses']), 1)
        self.assertDictContainsSubset({'id': self.course3.id, 'name': self.course3.name, 'privacy': 2},
                                      response.data['shared_courses'][0])
        self.assertDictContainsSubset({'teacher': self.course3.teacher.id}, response.data['shared_courses'][0])

    def test_userdump_does_not_contains_shared_courses_that_are_private(self):
        client = self.get_logged_client()

        self.currentUser.profile.shared_courses.add(self.course3)
        self.currentUser.save()

        self.course3.privacy = 0
        self.course3.save()

        response = client.get('/api/user_dump/')

        self.assertEqual(len(response.data['shared_courses']), 0)

    def test_userdump_does_not_contain_shared_courses(self):
        client = self.get_logged_client()

        self.course3.privacy = 1
        self.course3.save()

        response = client.get('/api/user_dump/')

        self.assertEqual(len(response.data['shared_courses']), 0)

    def test_userdump_contains_shared_recordings(self):
        client = self.get_logged_client()

        self.currentUser.profile.shared_recordings.add(self.r4)
        self.currentUser.save()

        self.r4.privacy = 1
        self.r4.save()

        response = client.get('/api/user_dump/')

        self.assertEqual(len(response.data['shared_recordings']), 1)
        self.assertDictContainsSubset({'id': self.r4.id, 'name': self.r4.name, 'privacy': 1},
                                      response.data['shared_recordings'][0])

    def test_userdump_contains_shared_recordings_that_are_public(self):
        client = self.get_logged_client()

        self.currentUser.profile.shared_recordings.add(self.r4)
        self.currentUser.save()

        self.r4.privacy = 2
        self.r4.save()

        response = client.get('/api/user_dump/')

        self.assertEqual(len(response.data['shared_recordings']), 1)
        self.assertDictContainsSubset({'id': self.r4.id, 'name': self.r4.name, 'privacy': 2},
                                      response.data['shared_recordings'][0])

    def test_userdump_contains_shared_recordings_that_are_private(self):
        client = self.get_logged_client()

        self.currentUser.profile.shared_recordings.add(self.r4)
        self.currentUser.save()

        self.r4.privacy = 0
        self.r4.save()

        response = client.get('/api/user_dump/')

        self.assertEqual(len(response.data['shared_recordings']), 0)

    def test_userdump_does_not_contain_shared_recordings(self):
        client = self.get_logged_client()

        self.r4.privacy = 0
        self.r4.save()

        response = client.get('/api/user_dump/')

        self.assertEqual(len(response.data['shared_recordings']), 0)