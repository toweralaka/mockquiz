# # -*- coding: utf-8 -*-
# from __future__ import unicode_literals
# from django import forms
# from django.contrib import admin
# #from ckeditor_uploader.widgets import CKEditorUploadingWidget 
# from .models import Examination, Subject, Topic, Question, SubTopic


# class SubjectAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name', 'examination', 'weight')
#     ordering = ('examination', 'name')


# class TopicAdmin(admin.ModelAdmin):
#     list_display = ('name', 'subject', 'to_do', 'unit_subtopic')


# class SubTopicAdmin(admin.ModelAdmin):
#     list_display = ('name', 'topic', 'to_do', 'weight')



# # class QuestionAdminForm(forms.ModelForm):
# #     question_text = forms.CharField(widget=CKEditorUploadingWidget())
# #     a = forms.CharField(widget=CKEditorUploadingWidget())
# #     b = forms.CharField(widget=CKEditorUploadingWidget())
# #     c = forms.CharField(widget=CKEditorUploadingWidget())
# #     d = forms.CharField(widget=CKEditorUploadingWidget())
# #     e = forms.CharField(widget=CKEditorUploadingWidget())
# #     class Meta:
# #         model = Question
# #         fields = ('examination', 'subject', 'topic', 'question_text', 'image', 'a', 'b', 'c', 'd', 'e', 'ans')


# class QuestionAdmin(admin.ModelAdmin):
#     #forms = QuestionAdminForm
#     list_display = ('question', 'option_a', 'option_b', 'option_c', 'option_d', 'option_e', 'ans', 'examination', 'topic', 'subtopic')# 'a', 'b', 'c', 'd', 'e', 'ans',)
#     list_filter = ('examination', 'topic', 'subject', 'batch')
#     fields = ('examination', 'batch', 'subject', 'topic', 'question_text', 'group_name', 'image', 'a', 'b', 'c', 'd', 'e', 'ans')
#     search_fields = ('question_text', 'batch', 'group_name')
#     ordering = ('group_name',)
#     save_as = True



# #register admin apps
# admin.site.register(Question, QuestionAdmin)
# admin.site.register(Subject, SubjectAdmin)
# admin.site.register(Examination)
# admin.site.register(Topic, TopicAdmin)
# admin.site.register(SubTopic, SubTopicAdmin)
