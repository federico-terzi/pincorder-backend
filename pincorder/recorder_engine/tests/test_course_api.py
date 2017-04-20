from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import *


class CourseTest(APITestCase):
    def setUp(self):
        self.currentUser = User.objects.create(username="testuser")
        self.currentUser2 = User.objects.create(username="testuser2")

        teacher = Teacher.objects.create(name="Anna Rossi")
        self.t1 = teacher
        course = Course.objects.create(name="Operative System", teacher=teacher)
        course.authorized_users.add(self.currentUser)

        teacher2 = Teacher.objects.create(name="Carlo Verdi")
        course2 = Course.objects.create(name="Telecom", teacher=teacher2)
        course2.authorized_users.add(self.currentUser)
        course2.authorized_users.add(self.currentUser2)

        # Add course, but don't authorize the testuser
        teacher3 = Teacher.objects.create(name="Paola Gialli")
        course3 = Course.objects.create(name="Math", teacher=teacher3)
        course3.authorized_users.add(self.currentUser2)

        self.course1 = course
        self.course2 = course2
        self.course3 = course3

    def get_logged_client(self, user=None):
        if user is None:
            user = self.currentUser
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_course_not_authorized(self):
        client = APIClient()
        response = client.get('/api/courses/')
        self.assertEqual(response.status_code, 401)

    def test_user_cant_see_courses_where_he_is_not_authorized(self):
        client = self.get_logged_client()
        response = client.get('/api/courses/{id}/'.format(id=self.course3.id))
        self.assertEqual(response.status_code, 404)

    def test_course_should_be_authorized(self):
        client = self.get_logged_client()
        response = client.get('/api/courses/')
        self.assertEqual(response.status_code, 200)

    def test_show_course_list_for_testuser(self):
        client = self.get_logged_client()
        response = client.get('/api/courses/')

        self.assertContains(response, text="Operative System", status_code=200)
        self.assertContains(response, text="Telecom", status_code=200)
        self.assertNotContains(response, text="Math", status_code=200)

    def test_show_course_list_for_testuser2(self):
        client = self.get_logged_client(self.currentUser2)
        response = client.get('/api/courses/')

        self.assertNotContains(response, text="Operative System", status_code=200)
        self.assertContains(response, text="Telecom", status_code=200)
        self.assertContains(response, text="Math", status_code=200)

    def test_add_course(self):
        client = self.get_logged_client()
        response = client.post('/api/courses/', {'name': 'Course 1', 'teacher': self.t1.id})

        self.assertTrue(Course.objects.filter(name='Course 1').exists())
        self.assertEqual(Course.objects.get(name='Course 1').teacher.name, "Anna Rossi")

        # Check if user is added to authorized users
        self.assertIn(self.currentUser, Course.objects.get(name='Course 1').authorized_users.all())
    
    def test_add_course_should_fail_teacher_doesnt_exist(self):
        client = self.get_logged_client()
        response = client.post('/api/courses/', {'name': 'Course 1', 'teacher': 100})  # Teacher doesn't exists

        self.assertFalse(Course.objects.filter(name='Course 1').exists())