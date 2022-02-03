from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'userprofile'



urlpatterns = [
	# url(r'^register/$', views.reg_profile, name='reg-profile'),
	url(r'^subject_request/$', views.subject_request, name='subj_req'),
	url(r'^area_request/$', views.area_request, name='area_req'),
	url(r'^profile/$', views.profile, name='profile'),
	url(r'^profile/update/$', views.profileupdate, name='profileupdate'),
	url(r'^profile/photocard/$', views.photocard, name='photocard'),
	url(r'^profile/result/$', views.result, name='result'),
	url(r'^our_partner/$', views.referral, name='referral'),
	url(r'^referrer/(?P<pk>[0-9]+)/$', views.referrer_page, name='referrer'),
	url(r'^ref_profile_login/$', views.ref_profile_login, name='ref-profile-login'),
	url(r'^referral/sub/(?P<code>\w+)/$', views.sub_referral, name='sub-referral'),
	url(r'^referral/reg_profile/(?P<code>\w+)/$', views.ref_reg_profile, name='ref-reg-profile'),
	url(r'^referral/bank_reg_profile/(?P<code>\w+)/$', views.ref_bank_reg_profile, name='ref-bank-reg-profile'),
	#url(r'^reg_profile/(?P<slug>[-\w]+)-(?P<pk>[0-9]+)/$', views.reg_refer_profile, name='reg-refer-profile'),
	url(r'^make_payment/$', views.make_payment, name='make-payment'),
	url(r'^bank_payment/$', views.bank_payment, name='bank-payment'),
	url(r'^online_payment/$', views.online_payment, name='online-payment'),


]