from django.contrib import admin
from .models import *


class RecordingAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'course', 'is_online', 'is_converted', 'recordingfile')
    search_fields = ('name', 'course')


class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher')

admin.site.register(Teacher)
admin.site.register(Course, CourseAdmin)
admin.site.register(Recording, RecordingAdmin)
admin.site.register(RecordingFile)
