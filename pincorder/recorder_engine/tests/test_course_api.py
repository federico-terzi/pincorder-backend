import datetime

from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import *
from django.utils import timezone

class CourseTest(APITestCase):
    def setUp(self):
        self.currentUser = User.objects.create(username="testuser")
        self.currentUser2 = User.objects.create(username="testuser2")

        teacher = Teacher.objects.create(name="Anna Rossi")
        self.t1 = teacher
        course = Course.objects.create(name="Operative System", teacher=teacher)
        course.authorized_users.add(self.currentUser)

        teacher2 = Teacher.objects.create(name="Carlo Verdi")
        self.t2 = teacher2
        course2 = Course.objects.create(name="Telecom", teacher=teacher2)
        course2.authorized_users.add(self.currentUser)
        course2.authorized_users.add(self.currentUser2)

        # Add course, but don't authorize the testuser
        teacher3 = Teacher.objects.create(name="Paola Gialli")
        self.t3 = teacher3
        course3 = Course.objects.create(name="Math", teacher=teacher3)
        course3.authorized_users.add(self.currentUser2)

        course4 = Course.objects.create(name="Laboratory", teacher=teacher, parent_course=course)
        course4.authorized_users.add(self.currentUser)
        self.course4 = course4

        self.course1 = course
        self.course2 = course2
        self.course3 = course3

        # Add recordings for testuser
        r1 = Recording.objects.create(name="First Registration", date=timezone.now(),
                                      course=course, user=self.currentUser)
        r2 = Recording.objects.create(name="Second Registration",
                                      date=timezone.now() - datetime.timedelta(hours=5),
                                      course=course, user=self.currentUser)
        r3 = Recording.objects.create(name="Third Registration",
                                      date=timezone.now() - datetime.timedelta(hours=10),
                                      course=course2, user=self.currentUser)

        self.r1 = r1

        # Add pins to r1
        pin1 = Pin.objects.create(recording=r1, time=10, text="Explanation 1")
        pin2 = Pin.objects.create(recording=r1, time=50, media_url="url_to_img.jpg")
        pin3 = Pin.objects.create(recording=r1, time=100, text="Explanation 2")


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

    def test_course_has_privacy(self):
        client = self.get_logged_client()
        response = client.get('/api/courses/'+str(self.course1.id)+"/")

        self.assertEqual(response.data['privacy'], 0)

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

    def test_add_course_with_parent(self):
        client = self.get_logged_client()
        response = client.post('/api/courses/', {'name': 'Course 1', 'teacher': self.t1.id,
                                                 'parent_course': self.course2.id})

        self.assertTrue(Course.objects.filter(name='Course 1').exists())
        self.assertEqual(Course.objects.get(name='Course 1').teacher.name, "Anna Rossi")
        self.assertEqual(Course.objects.get(name='Course 1').parent_course.id, self.course2.id)

        # Check if user is added to authorized users
        self.assertIn(self.currentUser, Course.objects.get(name='Course 1').authorized_users.all())

    def test_add_course_if_not_staff_privacy_cant_be_higher_than_featured(self):
        client = self.get_logged_client()

        response = client.post('/api/courses/',
                                {'name': 'New Course', 'privacy': settings.FEATURED_PRIVACY_LEVEL})

        self.assertEqual(Course.objects.get(id=response.data['id']).privacy, settings.PUBLIC_PRIVACY_LEVEL)

    def test_add_course_if_staff_privacy_can_be_featured(self):
        client = self.get_logged_client()

        self.currentUser.is_staff = True
        self.currentUser.save()

        response = client.post('/api/courses/',
                               {'name': 'New Course', 'privacy': settings.FEATURED_PRIVACY_LEVEL})

        self.assertEqual(Course.objects.get(id=response.data['id']).privacy, settings.FEATURED_PRIVACY_LEVEL)

    def test_add_course_should_fail_unauthorized_parent(self):
        client = self.get_logged_client()
        response = client.post('/api/courses/', {'name': 'Course 1', 'teacher': self.t1.id,
                                                 'parent_course': self.course3.id})

        self.assertFalse(Course.objects.filter(name='Course 1').exists())

    def test_add_course_without_teacher(self):
        client = self.get_logged_client()
        response = client.post('/api/courses/', {'name': 'Course 1'})

        self.assertTrue(Course.objects.filter(name='Course 1').exists())

        # Check if user is added to authorized users
        self.assertIn(self.currentUser, Course.objects.get(name='Course 1').authorized_users.all())

    def test_add_course_without_name_should_fail(self):
        client = self.get_logged_client()
        response = client.post('/api/courses/', {})

        self.assertFalse(Course.objects.filter(name='Course 1').exists())

    def test_add_course_should_fail_teacher_doesnt_exist(self):
        client = self.get_logged_client()
        response = client.post('/api/courses/', {'name': 'Course 1', 'teacher': 1000})  # Teacher doesn't exists

        self.assertFalse(Course.objects.filter(name='Course 1').exists())

    def test_add_course_with_teacher(self):
        client = self.get_logged_client()
        response = client.post('/api/courses/add_course_with_teacher/', {'name': 'Course 1', 'teacher': 'Cristina'})

        self.assertTrue(Course.objects.filter(name='Course 1').exists())
        self.assertEqual(Course.objects.get(name='Course 1').teacher.name, "Cristina")

        # Check if user is added to authorized users
        self.assertIn(self.currentUser, Course.objects.get(name='Course 1').authorized_users.all())

    def test_add_course_with_teacher_should_fail_without_teacher(self):
        client = self.get_logged_client()
        response = client.post('/api/courses/add_course_with_teacher/', {'name': 'Course 1'})

        self.assertFalse(Course.objects.filter(name='Course 1').exists())

        self.assertEqual(response.status_code, 500)

    def test_add_course_with_teacher_should_fail_with_blank_teacher(self):
        client = self.get_logged_client()
        response = client.post('/api/courses/add_course_with_teacher/', {'name': 'Course 1', 'teacher': ''})

        self.assertFalse(Course.objects.filter(name='Course 1').exists())

        self.assertEqual(response.status_code, 500)

    def test_add_course_with_teacher_should_fail_without_name(self):
        client = self.get_logged_client()
        response = client.post('/api/courses/add_course_with_teacher/', {'teacher': ''})

        self.assertFalse(Course.objects.filter(name='Course 1').exists())

        self.assertEqual(response.status_code, 500)

    def test_edit_course_name(self):
        client = self.get_logged_client()

        self.assertEqual(Course.objects.get(id=self.course1.id).name, 'Operative System')

        response = client.patch('/api/courses/{id}/'.format(id=self.course1.id), {'name': 'Course 1'})

        self.assertEqual(Course.objects.get(id=self.course1.id).name, 'Course 1')

        # Check if user is added to authorized users
        self.assertIn(self.currentUser, Course.objects.get(name='Course 1').authorized_users.all())

    def test_edit_course_teacher(self):
        client = self.get_logged_client()

        self.assertEqual(Course.objects.get(id=self.course1.id).teacher, self.t1)

        response = client.patch('/api/courses/{id}/'.format(id=self.course1.id),
                                {'name': 'Course 1', 'teacher': self.t2.id})

        self.assertEqual(Course.objects.get(id=self.course1.id).teacher, self.t2)

    def test_edit_course_if_not_staff_privacy_cant_be_higher_than_featured(self):
        client = self.get_logged_client()

        self.assertEqual(Course.objects.get(id=self.course1.id).privacy, 0)

        response = client.patch('/api/courses/' + str(self.course1.id) + '/',
                                {'privacy': settings.FEATURED_PRIVACY_LEVEL})

        self.assertEqual(Course.objects.get(id=self.course1.id).privacy, settings.PUBLIC_PRIVACY_LEVEL)

    def test_edit_course_if_staff_privacy_can_be_featured(self):
        client = self.get_logged_client()

        self.currentUser.is_staff = True
        self.currentUser.save()

        self.assertEqual(Course.objects.get(id=self.course1.id).privacy, 0)

        response = client.patch('/api/courses/' + str(self.course1.id) + '/',
                                {'privacy': settings.FEATURED_PRIVACY_LEVEL})

        self.assertEqual(Course.objects.get(id=self.course1.id).privacy, settings.FEATURED_PRIVACY_LEVEL)

    def test_make_course_shared(self):
        client = self.get_logged_client()

        self.assertEqual(Course.objects.get(id=self.course1.id).privacy, 0)

        response = client.patch('/api/courses/{id}/'.format(id=self.course1.id), {'privacy': 1})

        self.assertEqual(Course.objects.get(id=self.course1.id).privacy, 1)

    def test_make_course_public(self):
        client = self.get_logged_client()

        self.assertEqual(Course.objects.get(id=self.course1.id).privacy, 0)

        response = client.patch('/api/courses/{id}/'.format(id=self.course1.id), {'privacy': 2})

        self.assertEqual(Course.objects.get(id=self.course1.id).privacy, 2)

    def test_edit_course_parent_course(self):
        client = self.get_logged_client()

        self.assertEqual(Course.objects.get(id=self.course1.id).parent_course, None)

        response = client.patch('/api/courses/{id}/'.format(id=self.course1.id), {'parent_course': self.course2.id})

        self.assertEqual(Course.objects.get(id=self.course1.id).parent_course.id, self.course2.id)

    def test_edit_course_should_fail_user_not_authorized(self):
        client = self.get_logged_client(self.currentUser2)

        self.assertEqual(Course.objects.get(id=self.course1.id).name, 'Operative System')

        response = client.patch('/api/courses/{id}/'.format(id=self.course1.id), {'name': 'Course 1'})

        self.assertEqual(Course.objects.get(id=self.course1.id).name, 'Operative System')

        # Check if user is added to authorized users
        self.assertNotIn(self.currentUser2, Course.objects.get(id=self.course1.id).authorized_users.all())

    def test_edit_course_should_fail_unauthorized_parent_course(self):
        client = self.get_logged_client(self.currentUser2)

        self.assertEqual(Course.objects.get(id=self.course2.id).parent_course, None)

        response = client.patch('/api/courses/{id}/'.format(id=self.course2.id), {'parent_course': self.course1.id})

        self.assertEqual(Course.objects.get(id=self.course2.id).parent_course, None)

    def test_edit_course_should_fail_course_doesnt_exist(self):
        client = self.get_logged_client(self.currentUser2)

        response = client.patch('/api/courses/{id}/'.format(id=123123), {'name': 'Course 1'})

        self.assertEqual(response.status_code, 404)

    def test_edit_course_should_fail_teacher_doesnt_exists(self):
        client = self.get_logged_client(self.currentUser2)

        response = client.patch('/api/courses/{id}/'.format(id=self.course1.id),
                                {'name': 'Course 1', 'teacher': 1231231})

        self.assertEqual(response.status_code, 404)

    def test_delete_course(self):
        client = self.get_logged_client()

        self.assertTrue(Course.objects.filter(id=self.course1.id).exists())

        response = client.delete('/api/courses/{id}/'.format(id=self.course1.id))

        self.assertFalse(Course.objects.filter(id=self.course1.id).exists())

    def test_delete_course_check_recordings_are_deleted(self):
        client = self.get_logged_client()

        self.assertTrue(Course.objects.filter(id=self.course1.id).exists())
        self.assertEqual(Recording.objects.filter(course__id=self.course1.id).count(), 2)

        response = client.delete('/api/courses/{id}/'.format(id=self.course1.id))

        self.assertEqual(Recording.objects.filter(course__id=self.course1.id).count(), 0)
        self.assertFalse(Course.objects.filter(id=self.course1.id).exists())

    def test_delete_course_check_pins_are_deleted(self):
        client = self.get_logged_client()

        self.assertTrue(Course.objects.filter(id=self.course1.id).exists())

        initialCount = Pin.objects.filter(recording__course__id=self.course1.id).count()
        initialTot = Pin.objects.count()
        self.assertGreater(initialCount, 0)

        response = client.delete('/api/courses/{id}/'.format(id=self.course1.id))

        self.assertEqual(Pin.objects.count(), initialTot-initialCount)
        self.assertFalse(Course.objects.filter(id=self.course1.id).exists())

    def test_delete_course_check_child_courses_are_deleted(self):
        client = self.get_logged_client()

        self.assertTrue(Course.objects.filter(parent_course_id=self.course1.id).exists())
        childCourse = Course.objects.filter(parent_course_id=self.course1.id).first()

        response = client.delete('/api/courses/{id}/'.format(id=self.course1.id))

        self.assertFalse(Course.objects.filter(id=childCourse.id).exists())
        self.assertFalse(Course.objects.filter(id=self.course1.id).exists())

    def test_delete_course_check_teachers_are_not_deleted(self):
        client = self.get_logged_client()

        teacher = self.course2.teacher
        self.assertTrue(Teacher.objects.filter(id=teacher.id).exists())

        response = client.delete('/api/courses/{id}/'.format(id=self.course2.id))

        self.assertTrue(Teacher.objects.filter(id=teacher.id).exists())

    def test_delete_course_should_fail_user_not_authorized(self):
        client = self.get_logged_client(self.currentUser2)

        self.assertTrue(Course.objects.filter(id=self.course1.id).exists())

        response = client.delete('/api/courses/{id}/'.format(id=self.course1.id))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Course.objects.filter(id=self.course1.id).exists())

    def test_delete_course_should_fail_user_not_authorized_but_shared(self):
        client = self.get_logged_client(self.currentUser2)

        self.course1.share_with_user(self.currentUser2)

        self.assertTrue(Course.objects.filter(id=self.course1.id).exists())

        response = client.delete('/api/courses/{id}/'.format(id=self.course1.id))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Course.objects.filter(id=self.course1.id).exists())

    def test_delete_course_should_fail_course_doesnt_exist(self):
        client = self.get_logged_client(self.currentUser2)

        self.assertTrue(Course.objects.filter(id=self.course1.id).exists())

        response = client.delete('/api/courses/{id}/'.format(id=123123))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Course.objects.filter(id=self.course1.id).exists())

    def test_course_add_teacher_edit(self):
        client = self.get_logged_client()

        self.assertEqual(Course.objects.get(id=self.course1.id).teacher, self.t1)

        response = client.post('/api/courses/{id}/add_teacher/'.format(id=self.course1.id),
                                {'teacher': 'Mary'})

        self.assertEqual(Course.objects.get(id=self.course1.id).teacher.name, 'Mary')

    def test_course_add_teacher(self):
        client = self.get_logged_client()

        # Reset the course teacher
        course = Course.objects.get(id=self.course1.id)
        course.teacher = None
        course.save()
        self.assertEqual(Course.objects.get(id=self.course1.id).teacher, None)

        response = client.post('/api/courses/{id}/add_teacher/'.format(id=self.course1.id),
                                {'teacher': 'Mary'})

        self.assertEqual(Course.objects.get(id=self.course1.id).teacher.name, 'Mary')

    def test_course_add_teacher_should_fail_user_not_authorized(self):
        client = self.get_logged_client(self.currentUser2)

        # Reset the course teacher
        course = Course.objects.get(id=self.course1.id)
        course.teacher = None
        course.save()
        self.assertEqual(Course.objects.get(id=self.course1.id).teacher, None)

        response = client.post('/api/courses/{id}/add_teacher/'.format(id=self.course1.id),
                                {'teacher': 'Mary'})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Course.objects.get(id=self.course1.id).teacher, None)

    def test_course_edit_teacher_should_fail_user_not_authorized(self):
        client = self.get_logged_client(self.currentUser2)

        self.assertEqual(Course.objects.get(id=self.course1.id).teacher, self.t1)

        response = client.post('/api/courses/{id}/add_teacher/'.format(id=self.course1.id),
                                {'teacher': 'Mary'})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Course.objects.get(id=self.course1.id).teacher, self.t1)