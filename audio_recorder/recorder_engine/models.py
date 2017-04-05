from django.db import models
from django.conf import settings

class Teacher(models.Model):
    name = models.CharField(max_length=300)

    def __str__(self):
        return self.name

class Course(models.Model):
    name = models.CharField(max_length=200)
    teacher = models.ForeignKey('Teacher')
    parent_course = models.ForeignKey('Course', blank=True, null=True)

    authorized_users = models.ManyToManyField('auth.user')
    def __str__(self):
        return self.name

class Recording(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateTimeField()
    media_url = models.FileField(upload_to=settings.UPLOAD_MEDIA_URL)
    status = models.CharField(max_length=200, default="UPLOADED")
    is_online = models.BooleanField(default=False)
    is_converted = models.BooleanField(default=False)

    course = models.ForeignKey('Course')
    user = models.ForeignKey('auth.user')

    def __str__(self):
        return self.name