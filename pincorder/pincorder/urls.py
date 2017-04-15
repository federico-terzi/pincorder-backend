from django.conf.urls import url, include
from django.contrib import admin


# Define the url patterns for the application
urlpatterns = [
    url(r'^api/', include('recorder_engine.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]
