from django.contrib import admin
from .models import *


class RecordingFileInline(admin.TabularInline):
    """
    Used to display Recording File inline in the recording admin page
    """
    model = RecordingFile


class RecordingAdmin(admin.ModelAdmin):
    """
    Used to display Recordings information in the Django Admin
    """
    list_display = ('name', 'date', 'course', 'is_online', 'is_converted', 'recordingfile')
    search_fields = ('name', 'course')
    fieldsets = (
        (None, {
            'fields': ('name', 'date', 'course', 'privacy', 'user')
        }),
        ('Status Fields', {
            'fields': ('status', 'is_online', 'is_converted')
        }),
    )
    inlines = (RecordingFileInline,)

    def get_form(self, request, obj=None, **kwargs):
        """
        Override default method to automatically include current user
        """
        # Get the form
        form = super(RecordingAdmin, self).get_form(request, obj, **kwargs)

        # If obj is None, the recording is being created, so change the default user
        if obj is None:
            # Set the user that made the request as the initial user
            form.base_fields['user'].initial = request.user

        # Return the form
        return form


class CourseAdmin(admin.ModelAdmin):
    """
    Used to display Courses information in the Django Admin
    """
    list_display = ('name', 'teacher')


class ProfileAdmin(admin.ModelAdmin):
    """
    Used to display Profile information in the Django Admin
    """
    list_display = ('user',)
    filter_horizontal = ('shared_recordings', 'shared_courses')

# Register all the Models
admin.site.register(Teacher)
admin.site.register(Course, CourseAdmin)
admin.site.register(Recording, RecordingAdmin)
admin.site.register(RecordingFile)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(University)
