# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from django import forms
from ckeditor_uploader.widgets import CKEditorUploadingWidget 
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as OldGroupAdmin 
from django.contrib.auth.forms import ReadOnlyPasswordHashField
# from import_export.admin import ImportExportModelAdmin
# from import_export.admin import ImportExportActionModelAdmin
from .models import UsedCard, AccessCode, SiteView, About, Partner, Freebie, FileUploads, Receipt, Invoice, Advert, Gallery, BlogPost
from .customadmin import AccessCodeAdmin, FileUploadsAdmin, ReceiptAdmin, InvoiceAdmin

User = get_user_model()

# Register your models here.
class FreebieAdmin(admin.ModelAdmin):
    list_display = ('srn', 'pin', 'user', 'used',)
    search_fields = ('srn', 'user',)


class UsedCardAdmin(admin.ModelAdmin):
    list_display = ('serial', 'user', 'timeused',)
    search_fields = ('serial', 'user') 


class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact', 'phone', 'local_govt', 'active')
    search_fields = ('name', 'phone', 'contact')
    list_filter = ('state', 'local_govt')


class SiteViewAdmin(admin.ModelAdmin):
    list_display = ('page', 'ip', 'visit', 'time_spent', 'created',)
    search_fields = ('page', 'visit', 'ip')
    list_filter = ('page', 'created',)


class BlogAdminForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget())
    class Meta:
        model = BlogPost
        fields = ('title', 'content', 'caption_image', 'snippet', 'edited',  'views', 'shares', 'likes', 'published')

class BlogPostAdmin(admin.ModelAdmin):
    forms = BlogAdminForm
    list_display = ('title', 'views', 'shares', 'likes', 'published')
    search_fields = ('title', 'content')
    list_filter = ('published', 'created')


# class GroupCreateForm(forms.ModelForm):
# 	def __init__(self, request, *args, **kwargs):
# 		#user = kwargs.pop('user')
# 		if request.user:
# 			user = request.user
# 			super(GroupCreateForm, self).__init__(*args, **kwargs)
# 			qs = Permission.objects.filter(group__in=user.groups)
# 			self.fields['permissions'].queryset = qs 
	
# 	permissions = forms.ModelMultipleChoiceField(queryset=None,)
# 	#permissions = forms.ModelMultipleChoiceField(queryset=Permission.objects.all())#Permissions.objects.filter(gr='examiner'), to_field_name='name')
# 	class Meta:
# 		model = Group
# 		fields = ('name', 'permissions')


# 	# #used to show queryset created by loggedin user in modeladmin
# 	# def get_queryset(self, request):
# 	#     qs = super(GroupCreateForm, self).get_queryset(request)
# 	#     if request.user.is_staff:
# 	#         return qs
# 	#     return qs.filter(group=request.user.groups)

	



# class GroupAdmin(OldGroupAdmin):
# 	form = GroupCreateForm
# 	add_fieldsets = (
# 	(None, {
# 	'classes': ('wide',),
# 	'fields': ('name', 'permissions')}
# 	),
# 	)



# class UserChangeForm(forms.ModelForm):
# 	"""A form for updating users. Includes all the fields on
# 	the user, but replaces the password field with admin's
# 	password hash display field.
# 	"""
# 	password = ReadOnlyPasswordHashField()
# 	# username = forms.CharField()
# 	groups = forms.ModelMultipleChoiceField(queryset=Group.objects.exclude(name='examiner'), to_field_name='name')
# 	class Meta:
# 		model = User
# 		fields = ('email', 'password', 'username', 'is_active', 'groups')
# 		readonly_fields = ('username',)
# 		filter_horizontal = ('groups',)

# 	def clean_password(self):
# 		# Regardless of what the user provides, return the initial value.
# 		# This is done here, rather than on the field, because the
# 		# field does not have access to the initial value
# 		return self.initial["password"]

# 	def __init__(self, *args, **kwargs):
# 		super(UserChangeForm, self).__init__(*args, **kwargs)
# 		instance = getattr(self, 'instance', None)
# 		if instance and instance.id:
# 			self.fields['username'].required = False
# 			self.fields['username'].widget.attrs['disabled'] = 'disabled'

# 	def clean_username(self):
# 		# As shown in the above answer.
# 		instance = getattr(self, 'instance', None)
# 		if instance:
# 			return instance.username
# 		else:
# 			return self.cleaned_data.get('username', None)


# class UserAdmin(BaseUserAdmin):
# 	# The forms to add and change user instances
# 	form = UserChangeForm
# 	# add_form = UserCreationForm
# 	# The fields to be used in displaying the User model.
# 	# These override the definitions on the base UserAdmin
# 	# that reference specific fields on auth.User.
# 	list_display = ('username', 'email', 'is_staff')
# 	list_filter = ('is_staff',)
# 	#this displays after initial user creation for additional information
# 	fieldsets = (
# 	(None, {'fields': ('username', 'email', 'password')}),
# 	('Personal info', {'fields': ('first_name',)}),
# 	('Permissions', {'fields': ('is_staff', 'is_active', 'groups')}),
# 	#('Permissions', {'fields': ('is_staff', 'is_active')}),
# 	)
# 	# add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
# 	# overrides get_fieldsets to use this attribute when creating a user.
# 	add_fieldsets = (
# 	(None, {
# 	'classes': ('wide',),
# 	'fields': ('username', 'email', 'password1', 'password2')}
# 	),
# 	)
# 	search_fields = ('username',)
# 	ordering = ('username',)

class UserAdmin(BaseUserAdmin):
	list_display = ('username', 'email', 'is_staff')
	list_filter = ('is_staff', 'date_joined')
	search_fields = ('username',)
	ordering = ('username',)

# Now register the new UserAdmin...
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
# # ... and, since we're not using Django's built-in permissions,
# # unregister the Group model from admin.
# admin.site.unregister(Group)
# # admin.site.register(Group, GroupAdmin)
admin.site.register(AccessCode, AccessCodeAdmin)
admin.site.register(Freebie, FreebieAdmin)
admin.site.register(UsedCard, UsedCardAdmin)
admin.site.register(SiteView, SiteViewAdmin)
admin.site.register(About)
admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(Advert)
admin.site.register(FileUploads, FileUploadsAdmin)
admin.site.register(Partner, PartnerAdmin)
admin.site.register(Receipt, ReceiptAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Gallery)
