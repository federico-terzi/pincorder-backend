from django.conf.urls import url, include
from . import views


# Define the url patterns for the Desktop Version
urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^login/$', views.login, name='login')
]