from django.contrib import admin
from .models import (CenterCode, Candidate, CenterResult, CenterSendResult, CenterSubjectScore,
	CenterUserBank, CenterUserScript)
from .customadmin import CenterCodeAdmin, CandidateAdmin, CenterSubjectScoreAdmin, CenterResultAdmin
# Register your models here.



class CenterUserScriptAdmin(admin.ModelAdmin):
	list_display = ('__str__', 'dsubject', 'choice', 'realans', 'is_right', 'question')
	fields = ('user', 'choice', 'question',)
	read_only_fields = ('user', 'choice', 'question')
	search_fields = ('user__user__username', 'user__full_name')
	# list_filter = ('done', 'marked')




admin.site.register(CenterCode, CenterCodeAdmin)
admin.site.register(Candidate, CandidateAdmin)
admin.site.register(CenterUserScript, CenterUserScriptAdmin)
admin.site.register(CenterResult, CenterResultAdmin)
admin.site.register(CenterSubjectScore, CenterSubjectScoreAdmin)
# admin.site.register()
# admin.site.register()
# admin.site.register()
