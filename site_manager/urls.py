from django.conf.urls import url

from . import views
from userprofile import views as rviews

app_name = 'mngr'



urlpatterns = [
    url(r'^$', views.index, name='home'),
    #url(r'^iptime/$', views.get_ip_time, name='ip'),
    #url(r'^login_user/$', views.login_user, name='login_user'),
    #url(r'^logout_user/$', views.logout_user, name='logout_user'),
    url(r'^sales_point/$', views.partner, name='partner'),
    url(r'^guidelines/$', views.guidelines, name='guidelines'),
    url(r'^contact/$', views.contact, name='contact'),
    url(r'^register/$', rviews.reg_profile, name='reg-profile'),
    #url(r'^post-utme/$', views.index, name='home'),
    url(r'^gallery/$', views.gallery, name='gallery'),
    url(r'^blogs/$', views.blogs, name='blogs'),
    url(r'^blog/(?P<pk>[0-9]+)/$', views.blog, name='blog'),
    url(r'^share/(?P<pk>[0-9]+)/$', views.share, name='share'),
]  
