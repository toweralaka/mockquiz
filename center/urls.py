from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from .views import (index, login_exam, logout_exam, signup, get_subjects, instructions, exam, 
		update_elapse_time, user_choice
)

app_name = 'center'



urlpatterns = [
	url(r'^$', index, name='index'),
	url(r'^login_exam/$', login_exam, name='login_exam'),
	url(r'^register/$', signup, name='register'),
	url(r'^getsubjects/$', get_subjects, name='get-subjects'),
	url(r'^instructions/$', instructions, name='instructions'),
	url(r'^exam/$', exam, name='exam'),
	url(r'^update_elapse_time/$', update_elapse_time, name='update_elapse_time'),
	url(r'^user_choice/$', user_choice, name='user_choice'),
    url(r'^logout_exam/$', logout_exam, name='logout_exam'),
]