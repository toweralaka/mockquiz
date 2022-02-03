from django.conf.urls import url
from . import views

app_name = 'bank'

urlpatterns = [
	url(r'^test/$', views.detail, name='detail'),
]