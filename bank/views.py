# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from decimal import Decimal
from django.utils import timezone
from django.http import HttpResponseRedirect, HttpResponse

from datetime import timedelta, datetime
import csv, StringIO #io

from django.shortcuts import render, redirect
from .models import Subject, Topic, SubTopic, Examination
from userprofile.models import Result, UserScript, SubjectScore
from center.models import Candidate, CenterCode

# Create your views here.
def get_used_codes(request):
	if request.user.is_superuser:
		for user in Candidate.objects.all():
			code = CenterCode.objects.get(srn=user.regnum)
			code.used = True
			code.save()
		return HttpResponseRedirect('/admin/center/centercode/')
	else:
		return HttpResponseRedirect('/') 



def force_markscript(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="Mock_Users.csv"'#"somefilename.csv"'
	writer = csv.writer(response)
	writer.writerow(['id', 'first_name', 'surname','regnum',
		'subj1', 'score', 'attempted', 'number_right',
		'subj2', 'score', 'attempted', 'number_right',
		'subj3', 'score', 'attempted', 'number_right',
		'subj4', 'score', 'attempted', 'number_right',
		 ])
	new_adams = Result.objects.filter(exam_center__id__exact=34)
	for i in new_adams:
		regnum = i.user.regnum
		scores = SubjectScore.objects.filter(user=regnum)
			# subject = ""
			# for j in i.subject.all():
			#     subject += (str(j.id)) + ','
			# #subjects = ','.join(subject)
		writer.writerow([i.id,i.user.first_name, i.user.surname, regnum, 
			scores[0].subject, scores[0].score, scores[0].attempted(), scores[0].num_right(),
			scores[1].subject, scores[1].score, scores[1].attempted(), scores[1].num_right(),
			scores[2].subject, scores[2].score, scores[2].attempted(), scores[2].num_right(),
			scores[3].subject, scores[3].score, scores[3].attempted(), scores[3].num_right(),
			])
	return response
	# new_adams = Result.objects.filter(
	#     timelog__gte= timezone.make_aware(
	#         datetime.strptime("2021-04-01", "%Y-%m-%d"), timezone.get_default_timezone()
	#         )
	#     )
	# new_adams = Result.objects.filter(exam_center__id__exact=34)
	# print(len(new_adams))
	# for instance in new_adams:
	#     if instance.marked == False:
	#     # instance.marked = False
	#       instance.save()
	# for instance in new_adams:
	#     exam = instance.user.examination
	#     time_duration = timedelta(minutes= int(exam.duration))
	#     time_to_end = instance.timelog + time_duration
	#     # if timezone.localtime(timezone.now()) >= time_to_end:
	#         # if instance.force_markscript != True and instance.timelog >= timezone.make_aware(datetime.strptime("2021-05-01", "%Y-%m-%d"), timezone.get_default_timezone()) and instance.timelog <= timezone.make_aware(datetime.strptime("2021-06-01", "%Y-%m-%d"), timezone.get_default_timezone()):
	#     if not instance.marked:
	#         # if instance.timelog >= timezone.make_aware(datetime.strptime("2021-05-01", "%Y-%m-%d"), timezone.get_default_timezone()) and instance.timelog <= timezone.make_aware(datetime.strptime("2021-06-01", "%Y-%m-%d"), timezone.get_default_timezone()):
	#         oldscore = SubjectScore.objects.filter(user=str(instance.user.regnum))
	#         for j in oldscore:
	#             j.delete()
	#         exam = instance.user.examination
	#         scripts = UserScript.objects.filter(user=instance.user)
	#         for ii in scripts:
	#             i = ii.question.id
	#             p = Question.objects.get(id=i)
	#             try:
	#                 subj, new = SubjectScore.objects.get_or_create(user=str(instance.user.regnum), subject=str(p.subject)) 
	#                 dtpc = p.topic  
	#                 dsub = p.subject
	#                 dsubtop = p.subtopic
	#                 sbjct = Subject.objects.get(name=dsub, examination=exam)
	#                 try:
	#                     tpc = Topic.objects.get(name=str(dtpc), subject=sbjct)
	#                 except Topic.DoesNotExist:
	#                     wet = sbjct.weight
	#                 else:
	#                     try:
	#                         sbtp = SubTopic.objects.get(name=str(dsubtop), topic=tpc)
	#                         wet = sbtp.weight
	#                     except SubTopic.DoesNotExist:
	#                         wet = tpc.weight
							
	#                 if ii.is_right():
	#                     subj.score = Decimal(subj.score) + Decimal(wet)
	#                     subj.save()
						
	#                 else:
	#                     subj.score = Decimal(subj.score)
	#                     subj.save()
	#             except Exception as e:
	#                 print(e)
	#                 pass

	#         #record scores against user
	#         total = 0
	#         scripts_total = 0
	#         for sub in SubjectScore.objects.filter(user=str(instance.user.regnum)):
	#             total = total + sub.score
	#             grade = Decimal(sub.remarking())
	#             scripts_total = scripts_total + grade
	#         instance.total = total
	#         if scripts_total == instance.total:
	#             instance.marked = True
	#             instance.save()
	#             return True
	#         else:
	#             instance.total = 0
	#             instance.marked = False
	#             instance.save()
	#             oldscore = SubjectScore.objects.filter(user=str(instance.user.regnum))
	#             for j in oldscore:
	#                 j.score = 0
	#                 j.save()
	#             return False
