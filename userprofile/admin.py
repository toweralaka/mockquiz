# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from django.shortcuts import render
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Permission
from django.utils import timezone
# from import_export.admin import ImportExportModelAdmin
# from import_export.admin import ImportExportActionModelAdmin
from mngr.models import AccessCode
from .models import (UserProfile, ExamArea, State, UserScript, Referrer, Referral, BankDirect,
  ExamCenter, Batch, Result, SubjectScore, SendResult, WriteAccess, SpecialCase, SupReferral)
from .customadmin import (batch_users, senduserresult, BatchAdmin, UserProfileAdmin, ReferralAdmin, 
    SupReferralAdmin, activate_selected, deactivate_selected, export_results)
# from .resources import ResultResource

# Register your models here.
class BankDirectAdmin(admin.ModelAdmin):
    fields = ('confirmed',)
    list_display = ('user', 'payment_date', 'amount', 'bank', 'depositor_name', 'transaction_id', 'payment_mode', 'confirmed')
    search_fields = ('user', 'depositor_name')
    

class UserScriptAdmin(admin.ModelAdmin):
    fields = ('user', 'question', 'choice')#, 'realans')
    readonly_fields = ('realans',)
    list_display = ('user', 'dsubject', 'choice', 'realans', 'is_right', 'question')
    search_fields = ('user__regnum',)



class ReferrerAdmin(admin.ModelAdmin):
    fields = ('full_name', 'phone_number', 'state', 'bank', 'account_no', 'account_name')
    list_display = ('full_name', 'phone_number', 'ref_code', 'state', 'bank', 'regdate')
    search_fields = ('full_name', 'phone_number', 'ref_code')
    #list_filter = ('timestamp', 'exam_area', 'exam_center', 'batch')


class WriteAccessAdmin(admin.ModelAdmin):
    fields = ('name', 'exam_center', 'batch', 'password','time')
    list_display = ('name', 'exam_center', 'batch',)
    search_fields = ('name',)

    def get_actions(self, request):
        actions = super(WriteAccessAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            if 'delete_selected' in actions:
                del actions['delete_selected']
        return actions


class ExamAreaAdmin(admin.ModelAdmin):
    fields = ('name', 'exam_period', 'state', 'auto_batch', 'active',)
    list_display = ('name', 'exam_period', 'qty', 'auto_batch',)
    search_fields = ('name', 'state__name',)
    actions = ['sort_users',]

    def sort_users(self, request, queryset):
        for area in queryset:
            for userprofile in UserProfile.objects.filter(exam_area=area):
                if userprofile.paid:
                    if not userprofile.exam_center:
                        #batch to custom center
                        card = AccessCode.objects.get(srn=userprofile.serial, pin=userprofile.pin)
                        if card.custom:
                            try:
                                ucenter = ExamCenter.actv.filter(name=card.custom_center, active=True)[0]
                            except ExamCenter.DoesNotExist:
                                pass
                            else:
                                userprofile.exam_center = ucenter
                                userprofile.save()
                        else:
                            if area.auto_batch == False:
                                pass
                            else:
                                area.candidates = area.qty
                                area.save()
                                centers = ExamCenter.actv.filter(exam_area=area, cordon=False).order_by('candidates')
                                if centers.exists()== False:
                                    pass
                                else:
                                    userprofile.exam_center = centers[0]
                                    userprofile.save()             
            message_bit = str(area)+" Candidates Successfully Distributed!"
        self.message_user(request, "%s" % message_bit)                
    sort_users.short_description = 'Distribute Users To Centers'


class ExamCenterAdmin(admin.ModelAdmin):
    fields = ('exam_area', 'name', 'exam_period', 'address', 'show_photocard', 'check_when', 'active',)
    list_display = ('exam_area', '__str__', 'qty', 'show_photocard',)
    list_filter = ('active', 'show_photocard')
    search_fields = ('name', 'exam_area__name')
    actions = [batch_users, activate_selected, deactivate_selected]


class SubjectScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'score', 'remarking')
    search_fields = ('user',)


class SendResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'result' )
    search_fields = ('user',)


class ResultAdmin(admin.ModelAdmin):
    #resource_class = ResultResource
    list_display = ('user', 'card', 'usernm', 'scores', 'total', 'marked', 'timestamp')
    fields = ('user', 'marked', 'done', 'duration', 'scripts')
    # readonly_fields = ('user', 'marked', 'done')
    list_filter = ('timelog', 'marked', 'exam_center', 'batch', 'done')
    search_fields = ('user__regnum',)
    actions = ['reset_time', export_results, 'print_results', 'mark_scripts', 'remark_scripts']

    def get_actions(self, request):
        actions = super(ResultAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            if 'delete_selected' in actions:
                del actions['delete_selected']
            if 'import_results' in actions:
                del actions['import_results']
        return actions

    def remark_scripts(self, request, queryset):
        for pers in queryset:
            pers.marked = False
            pers.save()
            pers.markscript()
            if pers.marked:
                message_bit = str(pers.user.regnum)+" Scripts Successfully Marked!"
                self.message_user(request, "%s" % message_bit)
                        
    remark_scripts.short_description = 'Remark Candidate(s) Scripts'

    def mark_scripts(self, request, queryset):
        for pers in queryset:
            if not pers.marked:
                pers.markscript()
                if pers.marked:
                    message_bit = str(pers.user.regnum)+" Scripts Successfully Remarked!"
                    self.message_user(request, "%s" % message_bit)
                        
    mark_scripts.short_description = 'Mark Candidate(s) Scripts'

    def reset_time(self, request, queryset):
        for pers in queryset:
            pers.duration = 0
            pers.done = False
            pers.marked = False
            pers.timestamp = timezone.localtime(timezone.now())
            pers.save()
            message_bit = str(pers.user.regnum)+" Time Successfully Reset!"
            self.message_user(request, "%s" % message_bit)
                        
    reset_time.short_description = 'Reset Candidate(s) Time'

    def print_results(self, request, queryset):
        titled = queryset[0]
        profiles = []
        for i in queryset:
            if i.marked:
                profiles.append(i)
        context_instance={'profiles':profiles,
        'app_label': self.model._meta.app_label,
        'opts': self.model._meta,
        'has_change_permission': self.has_change_permission(request),
         'titled':titled}
        return render(request,
                          'admin/userprofile/result/results.html',
                          context_instance)
    print_results.short_description = 'Print Results'




admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(ExamArea, ExamAreaAdmin)
admin.site.register(WriteAccess, WriteAccessAdmin)
admin.site.register(UserScript, UserScriptAdmin)
admin.site.register(State)
admin.site.register(ExamCenter, ExamCenterAdmin)
admin.site.register(Batch, BatchAdmin)
admin.site.register(Result, ResultAdmin)
admin.site.register(SubjectScore, SubjectScoreAdmin)
admin.site.register(LogEntry)
admin.site.register(SendResult, SendResultAdmin)
admin.site.register(Permission)
admin.site.register(SpecialCase)
admin.site.register(BankDirect, BankDirectAdmin)
admin.site.register(Referrer, ReferrerAdmin)
admin.site.register(Referral, ReferralAdmin)
admin.site.register(SupReferral, SupReferralAdmin)