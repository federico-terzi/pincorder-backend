from django.conf.urls import url, include
from django.contrib import admin
from . import settings
from .views import *

# Define the url patterns for the application
urlpatterns = [
    url(r'^$', home, name='home'),
    url(r'^api/', include('recorder_engine.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^auth/', include('rest_framework_social_oauth2.urls')),
]

# Django toolbar url configuration
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns