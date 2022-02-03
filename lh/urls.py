from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'lh'



urlpatterns = [
	url(r'^$', views.index, name='index'),
	#cdl normal mock
	#url(r'^cbt/$', views.rdrct, name='rdrct'),
	#cdl center mock
	url(r'^cbt/$', views.centerrdrct, name='rdrct'),
	url(r'^login_exam/$', views.login_exam, name='login_exam'),
	url(r'^instructions/$', views.instructions, name='instructions'),
	url(r'^exam/$', views.exam, name='exam'),
	url(r'^user_choice/$', views.user_choice, name='user_choice'),
	url(r'^update_elapse_time/$', views.update_elapse_time, name='update_elapse_time'),
	url(r'^user_time/$', views.user_time, name='user_time'),
    url(r'^logout_exam/$', views.logout_exam, name='logout_exam'),
]