import datetime

from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import *
from django.utils import timezone


class UniversityTest(APITestCase):
    def setUp(self):
        self.currentUser = User.objects.create(username="testuser")
        self.currentUser2 = User.objects.create(username="testuser2")
        self.currentUser3 = User.objects.create(username="testuser3")

        self.uni1 = University.objects.create(name="Università di Bologna", short_name="UNIBO")
        self.uni2 = University.objects.create(name="Università di Firenze", short_name="UNIFI")
        self.uni3 = University.objects.create(name="Università di Napoli", short_name="UNINA")

        self.t1 = Teacher.objects.create(name="Anna Rossi")
        self.course1 = Course.objects.create(name="Operative System", teacher=self.t1)
        self.course1.authorized_users.add(self.currentUser)

        self.t2 = Teacher.objects.create(name="Carlo Verdi")
        self.course2 = Course.objects.create(name="Telecom", teacher=self.t2)
        self.course2.authorized_users.add(self.currentUser)
        self.course2.authorized_users.add(self.currentUser2)

    def get_logged_client(self, user=None):
        if user is None:
            user = self.currentUser
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_list_all_universities(self):
        client = self.get_logged_client()

        response = client.get("/api/uni/")

        self.assertContains(response, status_code=200, text=self.uni1.name)
        self.assertContains(response, status_code=200, text=self.uni1.short_name)
        self.assertContains(response, status_code=200, text=self.uni1.id)

        self.assertContains(response, status_code=200, text=self.uni2.name)
        self.assertContains(response, status_code=200, text=self.uni2.short_name)
        self.assertContains(response, status_code=200, text=self.uni2.id)

        self.assertContains(response, status_code=200, text=self.uni3.name)
        self.assertContains(response, status_code=200, text=self.uni3.short_name)
        self.assertContains(response, status_code=200, text=self.uni3.id)

    def test_get_university(self):
        client = self.get_logged_client()

        response = client.get("/api/uni/"+str(self.uni1.id)+"/")

        self.assertContains(response, status_code=200, text=self.uni1.name)
        self.assertContains(response, status_code=200, text=self.uni1.short_name)
        self.assertContains(response, status_code=200, text=self.uni1.id)

    def test_create_university_should_fail(self):
        client = self.get_logged_client()

        response = client.post("/api/uni/", {'name': 'Bad University'})

        self.assertEqual(response.status_code, 405)

    def test_edit_university_should_fail(self):
        client = self.get_logged_client()

        response = client.patch("/api/uni/"+str(self.uni1.id)+"/", {'name': 'Bad University'})

        self.assertEqual(response.status_code, 405)

    def test_delete_university_should_fail(self):
        client = self.get_logged_client()

        response = client.delete("/api/uni/"+str(self.uni1.id)+"/")

        self.assertEqual(response.status_code, 405)

    def test_search_university_short_name(self):
        client = self.get_logged_client()

        response = client.get("/api/uni/search/?name="+str(self.uni1.short_name))

        self.assertContains(response, status_code=200, text=self.uni1.name)
        self.assertContains(response, status_code=200, text=self.uni1.short_name)
        self.assertContains(response, status_code=200, text=self.uni1.id)

    def test_search_university_name(self):
        client = self.get_logged_client()

        response = client.get("/api/uni/search/?name="+str(self.uni1.name))

        self.assertContains(response, status_code=200, text=self.uni1.name)
        self.assertContains(response, status_code=200, text=self.uni1.short_name)
        self.assertContains(response, status_code=200, text=self.uni1.id)

    def test_search_universities(self):
        client = self.get_logged_client()

        response = client.get("/api/uni/search/?name=UNI")

        self.assertEqual(len(response.data), 3)

    def test_search_universities_case_insensitive(self):
        client = self.get_logged_client()

        response = client.get("/api/uni/search/?name=uNi")

        self.assertEqual(len(response.data), 3)

    def test_search_universities_result_limit(self):
        client = self.get_logged_client()

        # Create 100 new universities
        for i in range(100):
            University.objects.create(name="University "+str(i), short_name="UNI"+str(i))

        response = client.get("/api/uni/search/?name=uNi")

        self.assertEqual(len(response.data), settings.UNIVERSITIES_SEARCH_RESULT_LIMIT)

    def test_search_university_should_fail_name_not_provided(self):
        client = self.get_logged_client()

        response = client.get("/api/uni/search/")

        self.assertEqual(response.status_code, 500)