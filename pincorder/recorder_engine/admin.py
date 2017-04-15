from django.contrib import admin
from .models import *


class RecordingAdmin(admin.ModelAdmin):
    """
    Used to display Recordings information in the Django Admin
    """
    list_display = ('name', 'date', 'course', 'is_online', 'is_converted', 'recordingfile')
    search_fields = ('name', 'course')


class CourseAdmin(admin.ModelAdmin):
    """
    Used to display Courses information in the Django Admin
    """
    list_display = ('name', 'teacher')

# Register all the Models
admin.site.register(Teacher)
admin.site.register(Course, CourseAdmin)
admin.site.register(Recording, RecordingAdmin)
admin.site.register(RecordingFile)
