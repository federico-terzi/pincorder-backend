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

        teacher = Teacher.objects.create(name="Anna Rossi")
        course1 = Course.objects.create(name="Operative System", teacher=teacher)
        course1.authorized_users.add(self.currentUser)

        self.course1 = course1

        teacher2 = Teacher.objects.create(name="Carlo Verdi")
        course2 = Course.objects.create(name="Telecom", teacher=teacher2)
        course2.authorized_users.add(self.currentUser)
        course2.authorized_users.add(self.currentUser2)

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

        # Add pins to r1
        pin1 = Pin.objects.create(recording=r1, time=10, text="Explanation 1")
        pin2 = Pin.objects.create(recording=r1, time=50, media_url="url_to_img.jpg")
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

        self.assertDictContainsSubset({'name': 'First Registration', 'status': 'SUBMITTED', 'is_online': False,
                                       'is_converted': False, 'course': self.course1.id}, response.data)

    def test_recording_should_not_exist(self):
        client = self.get_logged_client()
        response = client.get('/api/recordings/1000/')

        self.assertEqual(response.status_code, 404)

    def test_recording_should_not_be_visible_from_another_user(self):
        client = self.get_logged_client(self.currentUser2)
        response = client.get('/api/recordings/1/')

        self.assertEqual(response.status_code, 404)

    def test_add_recording_to_course(self):
        client = self.get_logged_client()
        response = client.post('/api/recordings/', {'name': 'Test Recording', 'date': timezone.now(),
                                                    'course': self.course1.id})

        self.assertEqual(self.course1.recording_set.count(), 3)

        lastRecording = Recording.objects.last()

        self.assertEqual(lastRecording.name, 'Test Recording')
        self.assertEqual(lastRecording.user, self.currentUser)
        self.assertEqual(lastRecording.course, self.course1)

    def test_add_recording_to_unauthorized_course_should_fail(self):
        client = self.get_logged_client()
        response = client.post('/api/recordings/', {'name': 'Test Recording', 'date': timezone.now(),
                                                    'course': self.course3.id})

        self.assertEqual(self.course3.recording_set.count(), 1)

    def test_edit_recording(self):
        client = self.get_logged_client()
        response = client.patch('/api/recordings/1/', {'name': 'New Name'})

        recording = Recording.objects.first()

        self.assertEqual(recording.name, 'New Name')

    def test_edit_unauthorized_recording_should_fail(self):
        client = self.get_logged_client(self.currentUser2)
        response = client.patch('/api/recordings/1/', {'name': 'New Name'})

        recording = Recording.objects.first()

        self.assertNotEqual(recording.name, 'New Name')

    def test_delete_recording(self):
        client = self.get_logged_client()
        initialCount = Recording.objects.count()
        response = client.delete('/api/recordings/1/')

        self.assertEqual(initialCount, Recording.objects.count()+1)

    def test_delete_recording_check_if_file_is_deleted(self):
        client = self.get_logged_client()
        initialCount = Recording.objects.count()
        response = client.post('/api/recordings/1/upload_file/',
                               {'file_url': open('recorder_engine/tests/test.mp3', 'rb')},
                               format='multipart')
        print(response.content)
        filename = response.data['file_url']
        response = client.delete('/api/recordings/1/')

        self.assertFalse(os.path.isfile(os.path.join(settings.MEDIA_ROOT, filename)))
        self.assertEqual(initialCount, Recording.objects.count()+1)

    def test_delete_unauthorized_recording_should_fail(self):
        client = self.get_logged_client(self.currentUser2)
        initialCount = Recording.objects.count()
        response = client.delete('/api/recordings/1/')

        self.assertEqual(initialCount, Recording.objects.count())

    def test_recording_list_pins(self):
        client = self.get_logged_client()
        response = client.get('/api/recordings/1/get_pins/')

        self.assertDictContainsSubset({'time': 10, 'text': 'Explanation 1', 'media_url': None}, response.data[0])
        self.assertDictContainsSubset({'time': 50, 'text': '',
                                       'media_url': 'http://testserver/media/url_to_img.jpg'},
                                      response.data[1])
        self.assertDictContainsSubset({'time': 100, 'text': 'Explanation 2', 'media_url': None}, response.data[2])

    def test_add_pin_to_recording(self):
        client = self.get_logged_client()
        response = client.post('/api/recordings/{id}/add_pin/'.format(id=self.r1.id),
                               {'time': 200, 'text': 'Test Pin',
                                'media_url': open('recorder_engine/tests/wrong.png', 'rb')},
                                format = 'multipart')

        self.assertEqual(self.r1.pin_set.count(), 4)

        lastPin = Pin.objects.last()

        self.assertEqual(lastPin.text, 'Test Pin')
        self.assertTrue(lastPin.media_url is not None)
        self.assertEqual(lastPin.recording, self.r1)
        self.assertEqual(lastPin.time, 200)

        filename = '/'.join(response.data['media_url'].split('/')[-2:])

        # Deleting file
        os.remove(os.path.join(settings.MEDIA_ROOT, filename))

    def test_add_pin_to_recording_with_only_text(self):
        client = self.get_logged_client()
        response = client.post('/api/recordings/{id}/add_pin/'.format(id=self.r1.id), {'time': 200, 'text': 'Test Pin'})

        self.assertEqual(self.r1.pin_set.count(), 4)

        lastPin = Pin.objects.last()

        self.assertEqual(lastPin.text, 'Test Pin')
        self.assertEqual(lastPin.recording, self.r1)
        self.assertEqual(lastPin.time, 200)

    def test_add_pin_to_recording_with_only_media(self):
        client = self.get_logged_client()
        response = client.post('/api/recordings/{id}/add_pin/'.format(id=self.r1.id),
                               {'time': 200, 'media_url': open('recorder_engine/tests/wrong.png', 'rb')},
                               format='multipart')

        self.assertEqual(self.r1.pin_set.count(), 4)

        lastPin = Pin.objects.last()

        self.assertTrue(lastPin.media_url is not None)
        self.assertEqual(lastPin.recording, self.r1)
        self.assertEqual(lastPin.time, 200)

        filename = '/'.join(response.data['media_url'].split('/')[-2:])

        # Deleting file
        os.remove(os.path.join(settings.MEDIA_ROOT, filename))

    def test_add_pin_to_unauthorized_recording_should_fail(self):
        client = self.get_logged_client()
        response = client.post('/api/recordings/{id}/add_pin/'.format(id=self.r4.id), {'time': 200, 'text': 'Test Pin'})

        self.assertEqual(self.r4.pin_set.count(), 0)

    def test_edit_pin(self):
        client = self.get_logged_client()
        response = client.post('/api/recordings/{id}/add_pin/'.format(id=self.r1.id), {'time': 10, 'text': 'New Name'})

        pin = Pin.objects.first()

        self.assertEqual(pin.text, 'New Name')

    def test_edit_unauthorized_pin_should_fail(self):
        client = self.get_logged_client(self.currentUser2)
        response = client.post('/api/recordings/{id}/add_pin/'.format(id=self.r1.id), {'time': 10, 'text': 'New Name'})

        pin = Pin.objects.first()

        self.assertNotEqual(pin.text, 'New Name')

    def test_delete_pin(self):
        client = self.get_logged_client()
        initialCount = Pin.objects.count()
        response = client.delete('/api/recordings/{id}/delete_pin/'.format(id=self.r1.id), {'time': 10})

        self.assertEqual(initialCount, Pin.objects.count()+1)

    def test_delete_pin_check_if_image_is_deleted(self):
        client = self.get_logged_client()

        response = client.post('/api/recordings/{id}/add_pin/'.format(id=self.r1.id),
                               {'time': 200, 'media_url': open('recorder_engine/tests/wrong.png', 'rb')},
                               format='multipart')

        filename = response.data['media_url']
        initialCount = Pin.objects.count()
        response = client.delete('/api/recordings/{id}/delete_pin/'.format(id=self.r1.id), {'time': 200})

        self.assertFalse(os.path.isfile(os.path.join(settings.MEDIA_ROOT, filename)))
        self.assertEqual(initialCount, Pin.objects.count()+1)

    def test_delete_pin_at_non_existing_time_should_fail(self):
        client = self.get_logged_client()
        initialCount = Pin.objects.count()
        response = client.delete('/api/recordings/{id}/delete_pin/'.format(id=self.r1.id), {'time': 1023})

        self.assertEqual(initialCount, Pin.objects.count())

    def test_delete_unauthorized_pin_should_fail(self):
        client = self.get_logged_client(self.currentUser2)
        initialCount = Pin.objects.count()
        response = client.delete('/api/recordings/{id}/delete_pin/'.format(id=self.r1.id), {'time': 10})

        self.assertEqual(initialCount, Pin.objects.count())

    def test_add_pin_to_same_time_should_fail(self):
        client = self.get_logged_client()
        response = client.post('/api/recordings/{id}/add_pin/'.format(id=self.r1.id), {'time': 100, 'text': 'Test Pin'})

        self.assertEqual(self.r1.pin_set.count(), 3)

    def test_add_multiple_pins_to_recording(self):
        client = self.get_logged_client()
        response = client.post('/api/recordings/1/add_pin_batch/',
                               {'batch': [{'time': 200, 'text': 'Test Pin'}, {'time': 250, 'text': 'Test Pin 2'}]})

        self.assertEqual(self.r1.pin_set.count(), 5)

        pin = Pin.objects.get(id=4)

        self.assertEqual(pin.text, 'Test Pin')
        self.assertEqual(pin.recording, self.r1)
        self.assertEqual(pin.time, 200)

        pin = Pin.objects.get(id=5)

        self.assertEqual(pin.text, 'Test Pin 2')
        self.assertEqual(pin.recording, self.r1)
        self.assertEqual(pin.time, 250)

    def test_add_multiple_pins_to_recording_with_update(self):
        client = self.get_logged_client()
        response = client.post('/api/recordings/1/add_pin_batch/',
                               {'batch': [{'time': 10, 'text': 'Test Pin'}, {'time': 250, 'text': 'Test Pin 2'}]})

        self.assertEqual(self.r1.pin_set.count(), 4)

        pin = Pin.objects.get(id=1)

        self.assertEqual(pin.text, 'Test Pin')
        self.assertEqual(pin.recording, self.r1)
        self.assertEqual(pin.time, 10)

        pin = Pin.objects.get(id=4)

        self.assertEqual(pin.text, 'Test Pin 2')
        self.assertEqual(pin.recording, self.r1)
        self.assertEqual(pin.time, 250)

    def test_add_multiple_pins_should_fail_for_not_id(self):
        client = self.get_logged_client()
        response = client.post('/api/recordings//add_pin_batch/',
                               {'batch': [{'time': 200, 'text': 'Test Pin'}, {'time': 250, 'text': 'Test Pin 2'}]})
        self.assertEqual(self.r1.pin_set.count(), 3)

    def test_add_multiple_pins_should_fail_for_not_batch(self):
        client = self.get_logged_client()
        response = client.post('/api/recordings/1/add_pin_batch/',
                               {})

        self.assertEqual(self.r1.pin_set.count(), 3)

    def test_add_multiple_pins_should_fail_for_unauthorized_recording(self):
        client = self.get_logged_client()
        response = client.post('/api/recordings/4/add_pin_batch/',
                               {'batch': [{'time': 200, 'text': 'Test Pin'}, {'time': 250, 'text': 'Test Pin 2'}]})

        self.assertEqual(self.r4.pin_set.count(), 0)

    def test_add_multiple_pins_should_fail_for_not_existing_recording(self):
        client = self.get_logged_client()
        response = client.post('/api/recordings/400/add_pin_batch/',
                               {'batch': [{'time': 200, 'text': 'Test Pin'}, {'time': 250, 'text': 'Test Pin 2'}]})

        self.assertEqual(response.status_code, 404)

    def test_upload_file(self):
        client = self.get_logged_client()
        response = client.post('/api/recordings/1/upload_file/',
                               {'file_url': open('recorder_engine/tests/test.mp3', 'rb')},
                                format='multipart')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.r1.recordingfile.file_url.url, response.data['file_url'])

        filename = '/'.join(response.data['file_url'].split('/')[-2:])
        self.assertTrue(os.path.isfile(os.path.join(settings.MEDIA_ROOT, filename)))

        # Deleting file
        os.remove(os.path.join(settings.MEDIA_ROOT, filename))

    def test_upload_file_already_exist_should_fail(self):
        client = self.get_logged_client()
        response = client.post('/api/recordings/1/upload_file/',
                               {'file_url': open('recorder_engine/tests/test.mp3', 'rb')},
                                format='multipart')

        filename = '/'.join(response.data['file_url'].split('/')[-2:])

        # Deleting file
        os.remove(os.path.join(settings.MEDIA_ROOT, filename))

        # Send the request again
        response = client.post('/api/recordings/1/upload_file/',
                               {'file_url': open('recorder_engine/tests/test.mp3', 'rb')},
                               format='multipart')

        self.assertEqual(response.status_code, 500)

    def test_upload_file_wrong_format_should_fail(self):
        client = self.get_logged_client()
        response = client.post('/api/recordings/1/upload_file/',
                               {'file_url': open('recorder_engine/tests/wrong.png', 'rb')},
                                format='multipart')

        self.assertEqual(response.status_code, 500)

    def test_upload_file_to_nonexisting_recording_should_fail(self):
        client = self.get_logged_client()
        response = client.post('/api/recordings/1234/upload_file/',
                               {'file_url': open('recorder_engine/tests/test.mp3', 'rb')},
                                format='multipart')

        self.assertEqual(response.status_code, 404)

    def test_upload_file_without_params_should_fail(self):
        client = self.get_logged_client()
        response = client.post('/api/recordings/1/upload_file/',
                               {'file_url': ''},
                                format='multipart')

        self.assertEqual(response.status_code, 500)