from django.db import models
from django.conf import settings


class Teacher(models.Model):
    name = models.CharField(max_length=300)

    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=200)
    teacher = models.ForeignKey('Teacher', blank=True, null=True)
    parent_course = models.ForeignKey('Course', blank=True, null=True)

    authorized_users = models.ManyToManyField('auth.user')

    def __str__(self):
        return self.name


class Recording(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateTimeField()
    status = models.CharField(max_length=200, default="SUBMITTED")
    is_online = models.BooleanField(default=False)
    is_converted = models.BooleanField(default=False)

    course = models.ForeignKey('Course')
    user = models.ForeignKey('auth.user')

    def __str__(self):
        return self.name


class RecordingFile(models.Model):
    recording = models.OneToOneField(
        Recording,
        on_delete=models.CASCADE,
    )
    upload_date = models.DateTimeField(auto_now=True)
    file_url = models.FileField(upload_to=settings.UPLOAD_MEDIA_URL)

    def __str__(self):
        return self.file_url.name


class Pin(models.Model):
    recording = models.ForeignKey('Recording', on_delete=models.CASCADE)
    time = models.IntegerField()
    text = models.CharField(max_length=500, blank=True)
    media_url = models.FileField(upload_to=settings.UPLOAD_MEDIA_URL, blank=True)

    def __str__(self):
        return "{recording} - {time}".format(recording=str(self.recording), time=self.time)

    class Meta:
        unique_together = (('recording', 'time'),)
        ordering = ['time']
