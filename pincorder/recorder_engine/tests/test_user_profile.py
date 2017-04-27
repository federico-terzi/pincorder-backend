import datetime
import os

from django.core.files.base import ContentFile
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import *


class UserProfileTest(APITestCase):
    def setUp(self):
        self.currentUser = User.objects.create(username="testuser")
        self.currentUser2 = User.objects.create(username="testuser2")

    def get_logged_client(self, user=None):
        if user is None:
            user = self.currentUser
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_user_has_profile(self):
        self.assertIsNotNone(self.currentUser.profile)