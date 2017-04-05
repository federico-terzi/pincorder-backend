from django.contrib import admin
from .models import *

class RecordingAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'course' ,'is_online', 'is_converted','recordingfile')
    search_fields = ('name', 'course')

admin.site.register(Teacher)
admin.site.register(Course)
admin.site.register(Recording, RecordingAdmin)
admin.site.register(RecordingFile)