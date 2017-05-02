import datetime

from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import *
from django.utils import timezone


class TeacherTest(APITestCase):
    def setUp(self):
        self.currentUser = User.objects.create(username="testuser")
        self.currentUser2 = User.objects.create(username="testuser2")
        self.currentUser3 = User.objects.create(username="testuser3")

        self.university = University.objects.create(name="University of Bologna", short_name="unibo")

        self.t1 = Teacher.objects.create(name="Anna Rossi", role="Professor", org="Physics Department",
                                         university=self.university, website="example.com", privacy=0)
        self.t1.authorized_users.add(self.currentUser)

        self.course1 = Course.objects.create(name="Operative System", teacher=self.t1)
        self.course1.authorized_users.add(self.currentUser)

        self.t2 = Teacher.objects.create(name="Carlo Verdi", role="Professor", org="Math Department",
                                         university=self.university, website="example2.com", privacy=0)
        self.t2.authorized_users.add(self.currentUser2)
        self.course2 = Course.objects.create(name="Telecom", teacher=self.t2)
        self.course2.authorized_users.add(self.currentUser)
        self.course2.authorized_users.add(self.currentUser2)

        # Add course, but don't authorize the testuser
        self.t3 = Teacher.objects.create(name="Paola Gialli")
        self.t3.authorized_users.add(self.currentUser2)
        self.course3 = Course.objects.create(name="Math", teacher=self.t3)
        self.course3.authorized_users.add(self.currentUser2)

    def get_logged_client(self, user=None):
        if user is None:
            user = self.currentUser
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_user_is_authorized_to_view_if_author_of_teacher(self):
        client = self.get_logged_client()

        self.assertTrue(Teacher.custom.get_teachers_for_user(self.currentUser).filter(id=self.t1.id).exists())

    def test_user_is_authorized_to_view_if_author_of_course(self):
        client = self.get_logged_client()

        self.assertTrue(Teacher.custom.get_teachers_for_user(self.currentUser).filter(id=self.t2.id).exists())

    def test_user_is_not_authorized_to_view_if_not_author_of_course_or_author_of_teacher(self):
        client = self.get_logged_client()

        self.assertFalse(Teacher.custom.get_teachers_for_user(self.currentUser).filter(id=self.t3.id).exists())

    def test_user_is_authorized_to_edit_teacher_if_author(self):
        client = self.get_logged_client()

        self.assertTrue(Teacher.custom.check_user_is_authorized_teacher_id(self.currentUser, self.t1.id))

    def test_user_is_not_authorized_to_edit_teacher_if_author_of_course(self):
        client = self.get_logged_client()

        self.assertFalse(Teacher.custom.check_user_is_authorized_teacher_id(self.currentUser, self.t2.id))

    def test_user_is_not_authorized_to_edit_teacher(self):
        client = self.get_logged_client()

        self.assertFalse(Teacher.custom.check_user_is_authorized_teacher_id(self.currentUser, self.t3.id))

    # API endpoint

    def test_get_teacher(self):
        client = self.get_logged_client()

        client.get('/api/teachers/'+str(self.t1.id)+'/')

        self.assertEqual(Teacher.objects.get(name="Anna Rossi").role, 'Professor')
        self.assertEqual(Teacher.objects.get(name="Anna Rossi").org, 'Physics Department')
        self.assertEqual(Teacher.objects.get(name="Anna Rossi").university, self.university)
        self.assertEqual(Teacher.objects.get(name="Anna Rossi").website, 'example.com')

        self.assertIn(self.currentUser, Teacher.objects.get(name="Anna Rossi").authorized_users.all())

    def test_create_teacher_endpoint_just_name(self):
        client = self.get_logged_client()

        initialCount = Teacher.objects.count()
        self.assertFalse(Teacher.objects.filter(name="New Teacher").exists())

        client.post('/api/teachers/', {'name': 'New Teacher'})

        self.assertEqual(Teacher.objects.count(), initialCount+1)
        self.assertIn(self.currentUser, Teacher.objects.get(name="New Teacher").authorized_users.all())

    def test_create_teacher_endpoint_all_data(self):
        client = self.get_logged_client()

        initialCount = Teacher.objects.count()
        self.assertFalse(Teacher.objects.filter(name="New Teacher").exists())

        client.post('/api/teachers/', {'name': 'New Teacher', 'role': 'Professor', 'org': 'Physics Department',
                                         'university': self.university.id, 'website': 'example.com'})

        self.assertEqual(Teacher.objects.count(), initialCount+1)
        self.assertEqual(Teacher.objects.get(name="New Teacher").role, 'Professor')
        self.assertEqual(Teacher.objects.get(name="New Teacher").org, 'Physics Department')
        self.assertEqual(Teacher.objects.get(name="New Teacher").university, self.university)
        self.assertEqual(Teacher.objects.get(name="New Teacher").website, 'example.com')

        self.assertIn(self.currentUser, Teacher.objects.get(name="New Teacher").authorized_users.all())

    def test_edit_teacher(self):
        client = self.get_logged_client()

        self.assertEqual(Teacher.objects.get(id=self.t1.id).name, 'Anna Rossi')

        response = client.patch('/api/teachers/'+str(self.t1.id)+'/', {'name': 'New Teacher'})

        self.assertEqual(Teacher.objects.get(id=self.t1.id).name, 'New Teacher')

    def test_edit_teacher_should_fail_not_teacher_author(self):
        client = self.get_logged_client()

        self.assertEqual(Teacher.objects.get(id=self.t2.id).name, 'Carlo Verdi')

        response = client.patch('/api/teachers/'+str(self.t2.id)+'/', {'name': 'New Teacher'})

        self.assertEqual(Teacher.objects.get(id=self.t2.id).name, 'Carlo Verdi')

    def test_delete_teacher(self):
        client = self.get_logged_client()

        self.assertTrue(Teacher.objects.filter(id=self.t1.id).exists())

        response = client.delete('/api/teachers/'+str(self.t1.id)+'/')

        self.assertFalse(Teacher.objects.filter(id=self.t1.id).exists())

    def test_delete_teacher_should_fail_not_author_of_teacher(self):
        client = self.get_logged_client()

        self.assertTrue(Teacher.objects.filter(id=self.t2.id).exists())

        response = client.delete('/api/teachers/'+str(self.t2.id)+'/')

        self.assertTrue(Teacher.objects.filter(id=self.t2.id).exists())