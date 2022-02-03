# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404, render, redirect,render_to_response
from django.contrib import messages # to add context to HttpResponseRedirect
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse#to serialise the ajax response

# from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
# #from django.views import generic
# #from django.views.generic import View
from django.utils import timezone
# from django.shortcuts import render, render_to_response
# from django.template import RequestContext
# from django.contrib.auth.models import User
# #from django.views.generic.edit import UpdateView
# import datetime
from datetime import timedelta

# # Create your views here.
from .models import (Candidate, CenterCode, CenterResult, CenterSubjectScore, 
    CenterUserScript) 
from mngr.models import About
#, CenterUserScript, Score, ExamSchedule
from bank.models import Topic, Subject, Question, SubTopic, Examination
# from decimal import Decimal
from .forms import SignUpForm
# from django.contrib.auth import get_user_model

# User = get_user_model()

#today = timezone.localtime(timezone.now())


def login_exam(request):
    try:
        about = About.objects.all()[0]
    except Exception:
        about = None
    today = timezone.localtime(timezone.now()).today()
    CURRENTYEAR = today.year
    if request.method == "POST":
        username = request.POST['username']
        try:
            user = authenticate(username=username)
        except Exception:
            user = None
        if user is not None:
            if user.is_active:
                if not user.is_staff:
                    login(request, user)
                    try:
                        code = CenterCode.objects.get(user=str(request.user))
                        if code.alert:
                            logout(request)
                            context_instance={'error_message': 'Invalid! Please Return Code To Issuer', 
                            'about': about}
                            return render(request, 'center/login.html', context_instance)
                        if not code.active:
                            logout(request)
                            context_instance={'error_message': 'Invalid Login', 
                            'about': about}
                            return render(request, 'center/login.html', context_instance)
                        else:
                            try:
                                student = Candidate.objects.get(user=request.user)
                            except Candidate.DoesNotExist:
                                return HttpResponseRedirect('/mocktest/register/') 
                            # if student.online:
                            #     logout(request)
                            #     context_instance={'error_message': 'You are already logged in on another device', 
                            #     'about': about}
                            #     return render(request, 'center/login.html', context_instance)
                            # else:
                            student.online = True
                            student.save()
                            return HttpResponseRedirect('/mocktest/')
                    except CenterCode.DoesNotExist:
                        try:
                            UserProfile.objects.get(user=user)
                            return redirect('/')
                        except UserProfile.DoesNotExist:
                            user.delete()
                            context_instance={'error_message': 'Please See Center Admin For Login Credentials', 
                                'about': about}
                            return render(request, 'center/login.html', context_instance)
                else:
                    context_instance={'error_message': 'Staff Logged in'}
                    return render(request, 'center/login.html', context_instance)
            else:
                context_instance={'about': about, 
                'error_message': 'Your account has been disabled. Please contact invigilator.'}
                return render(request, 'center/login.html', context_instance)
        else:
            return render(request, 'center/login.html', {'error_message': 'Invalid User ID', 'about': about})
    context_instance={'about': about}
    return render(request, 'center/login.html', context_instance)


def get_subjects(request):
    if request.is_ajax():
        exam_id = request.GET.get("exam")
        exam = Examination.objects.get(id=exam_id)
        subjects = Subject.objects.filter(examination=exam).order_by('-compulsory', 'name')
        units = exam.subjects
        return render(request, "center/subjects.html", {'subjects':subjects, 'units':units})
    else:
        raise Http404


@login_required
def signup(request):
    if request.user.is_staff:
        logout(request)
        return redirect("center:login_exam")
    try:
        Candidate.objects.get(user=request.user)
        return redirect("center:index")
    except Exception:
        pass
    try:
        code = CenterCode.objects.get(user=str(request.user))
        if code.alert:
            logout(request)
            context_instance={'error_message': 'Invalid! Please Return Code To Issuer', 
            'about': about}
            return render(request, 'center/login.html', context_instance)
    except CenterCode.DoesNotExist:
        logout(request)
        context_instance={'error_message': 'Please See Center Admin For Login Credentials', 
        'about': about}
        return render(request, 'center/login.html', context_instance)
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = request.user
            student = form.save(commit=False)
            try:
                code = CenterCode.objects.get(user=user.username, used=False)
            except CenterCode.DoesNotExist:
                context_instance={'about': about, 
                'error_message': 'Invalid Access Code. Please contact invigilator.'}
                return render(request, 'center/login.html', context_instance)
            dsubjects = form.cleaned_data.get('subject')
            student.regnum = str(code.srn)
            student.user = user
            student.issued_by = code.buyer
            student.save()
            for sub in dsubjects:
                student.subject.add(sub)
            student.save()
            code.used = True
            # code.user = str(user.username)
            code.time_used = timezone.localtime(timezone.now())
            code.save()
            student.user_scripts()
            return redirect("center:index")
        else:
            return render(request, "center/registration.html", {'form':form,})
    form = SignUpForm()
    return render(request, "center/registration.html", {'form':form,})



def logout_exam(request):
    try:
        candidate = Candidate.objects.get(user=request.user)
        if candidate.online:
            candidate.online = False
            candidate.save()
    except Candidate.DoesNotExist:
        pass
    try:
        logout(request)
    except Exception:
        pass
    return HttpResponseRedirect('/mocktest/login_exam/')


def update_elapse_time(request):
    try:
        candidate = Candidate.objects.get(user=request.user)
        if request.method == 'POST':
            minutes = request.POST.get('incByMinutes')
            try:
                person = CenterResult.objects.get(user=candidate)
                person.duration += 2
                person.save()        
                return render_to_response('center/choice.html')
            except (KeyError, CenterResult.DoesNotExist):
                pass
    except (KeyError, Candidate.DoesNotExist):
        #return HttpResponseRedirect('/mocktest/login_exam/')
        pass


def rdrct(request):
    return HttpResponseRedirect('/')


def centermockrdrct(request):
    return HttpResponseRedirect('/centermock/')


#@login_required #never for index page
def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/mocktest/login_exam/')
    else:
        if request.user.is_staff:
            messages.add_message(request, messages.INFO, "Staff logged In")
            return HttpResponseRedirect('/mocktest/login_exam/')
        else:
            try:
                candidate = Candidate.objects.get(user=request.user)
                return render(request, 'center/index.html', {'candidate':candidate})
            except Candidate.DoesNotExist:
                try:
                    UserProfile.objects.get(user=request.user)
                    return redirect('/')
                except UserProfile.DoesNotExist:
                    logout(request)
                    messages.add_message(request, messages.INFO, "This is not your examination batch. Contact invigilator")
                    return HttpResponseRedirect('/mocktest/login_exam/')        
            


@login_required
def instructions(request):
    if not request.user.is_authenticated:
        return render(request, 'center/login.html')
    else:
        try:
            candidate = Candidate.objects.get(user=request.user)
            try:
                person = CenterResult.objects.get(user = candidate)
            except (KeyError, CenterResult.DoesNotExist):
                person = 'nil'
        except Candidate.DoesNotExist:
            logout(request)
            return HttpResponseRedirect('/mocktest/login_exam/')

        return render(request, 'center/instructions.html',{'person':person,})




        

def user_choice(request):
    if request.is_ajax():
        saved_script = False
        flash_message = ""
        try:
            candidate = Candidate.objects.get(user=request.user)
            choice_datum = request.POST.get('user_choice_question')
            choice_data=choice_datum.split('_')
            try:
                question_id = int(choice_data[0])
                d_question = Question.objects.get(id=question_id)
                d_choice = str(choice_data[1])
                script = CenterUserScript.objects.get(user = candidate, question = d_question)
                script.choice = d_choice
                script.save()        
                # feedback = 'Selection Saved'
                flash_message = ""
                saved_script = True
            except Exception:
                flash_message = 'Please Select Option'
        except (KeyError, Candidate.DoesNotExist):
            flash_message = 'You Are Not Signed Up. Please Contact Invigilator'
        data = {
            # 'feedback' : feedback
            "feed_back" : flash_message,
            "saved_script": saved_script
        }
        return JsonResponse(data)
    else:
        return Http404

# def user_choice(request):
#     if request.is_ajax():
#         try:
#             userprofile = UserProfile.objects.get(user=request.user)
#             choice_datum = request.POST.get('user_choice_question')
#             choice_data=choice_datum.split('_')
#             try:
#                 question_id = int(choice_data[0])
#                 d_question = Question.objects.get(id=question_id)
#                 d_choice = str(choice_data[1])
#                 script = UserScript.objects.get(user = userprofile, question = d_question)
#                 script.choice = d_choice
#                 script.save()        
#                 flash_message = "Script Saved!"
#             except KeyError:
#                 flash_message = "Invalid Selection"
#         except (KeyError, UserProfile.DoesNotExist):
#             flash_message = "You Are Not Logged In"
#         data = {
#             "flash_message" : flash_message,
#         }
        
#         return JsonResponse(data)
#     else:
#         raise Http404


@login_required
def user_time(request):
    try:
        userprofile = UserProfile.objects.get(user=request.user)
        if request.method == 'POST':
            timespent = int(float(request.POST.get('user_time_spent')))
            if timespent > 0:
                result = Result.objects.get(user = userprofile, 
                        exam_area=userprofile.exam_area,
                        exam_center=userprofile.exam_center)
                result.duration = result.duration - timespent
                result.save()
                return render_to_response('center/choice.html')
            else:
                pass
    except (KeyError, UserProfile.DoesNotExist):
        #return HttpResponseRedirect('/mocktest/login_exam/')
        pass
    
@login_required
def exam(request):
    try:
        candidate = Candidate.objects.get(user=request.user)
    except (KeyError, Candidate.DoesNotExist):
        logout(request)
        return HttpResponseRedirect('/mocktest/login_exam/')
    #get user result object
    exam = candidate.examination
    person, created = CenterResult.objects.get_or_create(user = candidate, 
        exam_center=candidate.exam_center)
    if person.done:
        return render(request, 'center/instructions.html', {'person':person})
    if not person.started:
        person.started = True
        person.time_started = timezone.localtime(timezone.now())
        person.save()
    duration = exam.duration
    time_elapsed = person.duration # remove
    timespent = timezone.localtime(timezone.now()) - person.time_started
    time_duration = timedelta(minutes= int(duration))
    if timespent >= time_duration:
        person.done = True
        person.save()
        return render(request, 'center/instructions.html', {'person':person})
    else:      
        if request.method == 'POST':
            #check for number of questions answered
            count = len(request.POST.items()) - 1
            if count < exam.limit:
                timespent = timezone.localtime(timezone.now()) - person.time_started
                time_duration = timedelta(minutes= int(duration))
                if timespent < time_duration:
                    starttime = person.time_started.strftime('%a %b %d %Y %H:%M:%S %z')
                    context_instance={'payload': candidate.get_user_scripts(),
                     'candidate':candidate,
                     'starttime': starttime,
                     'time_elapsed': time_elapsed,
                     'error_message': "You have to answer a minimum of " +str(exam.limit)+ " questions before you can submit",
                      'duration':duration, 'person':person}
                    return render(request, 'center/test.html', context_instance)

            scrpts = {key:value for (key, value) in request.POST.items()}
            person.scripts = "%s -ADD- %s" %(person.scripts, scrpts)
            person.done = True
            person.save()
            return HttpResponseRedirect('/mocktest/instructions/')

        else:
            starttime = person.time_started.strftime('%a %b %d %Y %H:%M:%S %z')
            context_instance={'payload': candidate.get_user_scripts(),
             'candidate':candidate,
             'time_elapsed': time_elapsed,
             'starttime':starttime,
              'duration':duration, 'person':person}
            return render(request, 'center/test.html', context_instance)

# @login_required
# def exam(request):
#     try:
#         candidate = Candidate.objects.get(user=request.user)
#     except (KeyError, Candidate.DoesNotExist):
#         logout(request)
#         return HttpResponseRedirect('/mocktest/login_exam/')
#     #get user result object
#     exam = candidate.examination
#     person, created = CenterResult.objects.get_or_create(user = candidate, 
#         exam_center=candidate.exam_center)
#     if person.done:
#         return render(request, 'center/instructions.html', {'person':person})
#     if not person.started:
#         person.started = True
#         person.time_started = timezone.localtime(timezone.now())
#         person.save()
#     duration = exam.duration
#     time_elapsed = person.duration # remove
#     timespent = timezone.localtime(timezone.now()) - person.time_started
#     time_duration = timedelta(minutes= int(duration))
#     if timespent > time_duration:
#         person.done = True
#         person.save()
#         return render(request, 'center/instructions.html', {'person':person})
#     else:
#         subjects = candidate.subject.all()
#         totques = 0
#         for s in subjects:
#             totques += s.to_do
#         questions = []
#         userques = CenterUserScript.objects.filter(user = candidate)
#         if userques.count() != totques:
#             #clear the userscripts
#             for i in userques:
#                 i.delete()
#             #create new userscripts and questions to do
#             for subject in subjects:
#                 topics = subject.topic_set.all()
#                 if subject.topic_set.all().exists():
#                     for tp in topics:
#                         subtops = tp.subtopic_set.all()
#                         if tp.subtopic_set.all().exists():
#                             subtpunit = 0
#                             for i in subtops:
#                                 if subtpunit < int(tp.unit_subtopic):
#                                     que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name), topic=str(tp), subtopic=str(i)).order_by('?')[:(int(i.to_do))]
#                                     bulk_script = []
#                                     for ques in que_set:
#                                         new_script = CenterUserScript()
#                                         new_script.question = ques
#                                         new_script.user = candidate
#                                         bulk_script.append(new_script)
#                                         selected_choice = 'nil'
#                                         payload = {'question':ques, 'selected_choice':selected_choice}
#                                         questions.append(payload)
#                                     CenterUserScript.objects.bulk_create(bulk_script)
#                                     subtpunit += 1
#                                 else:
#                                     pass
#                         else:
#                             que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name), topic=str(tp)).order_by('?')[:(int(tp.to_do))]
#                             bulk_script = []
#                             for ques in que_set:
#                                 new_script = CenterUserScript()
#                                 new_script.question = ques
#                                 new_script.user = candidate
#                                 bulk_script.append(new_script)
#                                 selected_choice = 'nil'
#                                 payload = {'question':ques, 'selected_choice':selected_choice}
#                                 questions.append(payload)
#                             CenterUserScript.objects.bulk_create(bulk_script)
                                
#                 else:
#                     que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name)).order_by('?')[:(int(subject.to_do))]
#                     bulk_script = []
#                     for ques in que_set:
#                         new_script = CenterUserScript()
#                         new_script.question = ques
#                         new_script.user = candidate
#                         bulk_script.append(new_script)
#                         selected_choice = 'nil'
#                         payload = {'question':ques, 'selected_choice':selected_choice}
#                         questions.append(payload)
#                     CenterUserScript.objects.bulk_create(bulk_script)
#         else:
#             for ii in userques:
#                 i = ii.question.id
#                 q = Question.objects.get(id=i)
#                 selected_choice = ii.choice
#                 payload = {'question':q, 'selected_choice':selected_choice}
#                 questions.append(payload)
        
#         if request.method == 'POST':
#             #check for number of questions answered
#             count = 0
#             for key, value in request.POST.items():
#                 if str(value) == 'a' or str(value) == 'b' or str(value) == 'c' or str(value) == 'd' or str(value) == 'e':
#                     count += 1
#             if count < exam.limit:
#                 timespent = timezone.localtime(timezone.now()) - person.time_started
#                 time_duration = timedelta(minutes= int(duration))
#                 if timespent < time_duration:
#                     starttime = person.time_started.strftime('%a %b %d %Y %H:%M:%S %z')
#                     context_instance={'payload': questions,
#                      'candidate':candidate,
#                      'starttime': starttime,
#                      'time_elapsed': time_elapsed,
#                      'error_message': "You have to answer a minimum of " +str(exam.limit)+ " questions before you can submit",
#                       'duration':duration, 'person':person}
#                     return render(request, 'center/test.html', context_instance)

#             # for key, value in request.POST.items():
#             #     try:
#             #         p = Question.objects.get(id=str(key))
#             #     except (UnicodeEncodeError,ValueError, KeyError, Question.DoesNotExist):
#             #         pass
#             #     else:
#             #         try:
#             #             selected_choice = str(value)
#             #             if p.ans == selected_choice:
#             #                 is_correct = True 
#             #             else:
#             #                 is_correct = False
#             #         except (UnicodeEncodeError,ValueError, KeyError):
#             #             selected_choice = 'nil'
#             #             is_correct = False
#             #             pass
#             #         #save user script
#             #         try:
#             #             script = CenterUserScript.objects.get(user = candidate, question = p)
#             #             script.choice = str(selected_choice)
#             #             script.save()
#             #         except CenterUserScript.DoesNotExist:
#             #             pass
#             scrpts = {key:value for (key, value) in request.POST.items()}
#             person.scripts = "%s -ADD- %s" %(person.scripts, scrpts)
#             person.done = True
#             person.save()
#             return HttpResponseRedirect('/mocktest/instructions/')

#         else:
#             starttime = person.time_started.strftime('%a %b %d %Y %H:%M:%S %z')
#             context_instance={'payload': questions,
#              'candidate':candidate,
#              'time_elapsed': time_elapsed,
#              'starttime':starttime,
#               'duration':duration, 'person':person}
#             return render(request, 'center/test.html', context_instance)
            
# #@login_required never for index page
# def index(request):
# 	try:
# 		about = About.objects.all()[0]
# 	except Exception:
# 		about = None
# 	# today = timezone.localtime(timezone.now()).date()
# 	# right_now = timezone.localtime(timezone.now()) + timedelta(minutes= int('60'))
# 	#print(examsc.start_time<=right_now)
# 	if not request.user.is_authenticated:
# 		return HttpResponseRedirect('/mocktest/login_exam/')
# 	else:
# 		if request.user.is_staff:
# 			logout(request)
# 			return HttpResponseRedirect('/mocktest/login_exam/')
# 		else:
# 			try:
# 				student = Candidate.objects.get(user=request.user)
# 				exam_level = student.previous_class.level
# 				try:
# 					examinee = CenterResult.objects.filter(user=student).order_by('-time_stamp')[0]
# 					try:
# 						allscores = CenterSubjectScore.objects.filter(result=examinee)[0]
# 					except IndexError:
# 						for sub in exam_level.examsubject_set.all():
# 							score = CenterSubjectScore.objects.create(result=examinee, subject=sub)
# 					#check if User Exams Are All Done
# 					try:
# 						undone = CenterSubjectScore.objects.filter(result=examinee, done=False)[0]
# 					except IndexError:
# 						examinee.done=True
# 						examinee.save()
# 				except IndexError:
# 					examinee = CenterResult.objects.create(user=student, exam_level=exam_level)
# 					for sub in exam_level.examsubject_set.all():
# 						score = CenterSubjectScore.objects.create(result=examinee, subject=sub)

# 			except Candidate.DoesNotExist:
# 				return HttpResponseRedirect('/mocktest/register/')        
# 			return render(request, 'center/index.html', {'student':student, 'examinee':examinee})
# 			#, 'exam':exam, 'about': about})



# @login_required
# def exam_instruction(request, pk):
# 	try:
# 		about = About.objects.all()[0]
# 	except Exception:
# 		about = None
# 	if not request.user.is_authenticated:
# 		return HttpResponseRedirect('/mocktest/login_exam/')
# 	else:
# 		if request.user.is_staff:
# 			logout(request)
# 			return HttpResponseRedirect('/mocktest/login_exam/')
# 		else:
# 			try:
# 				student = Candidate.objects.get(user=request.user)
# 				subject = CenterSubjectScore.objects.get(pk=pk)
# 			except Candidate.DoesNotExist:
# 				logout(request)
# 				return HttpResponseRedirect('/mocktest/login_exam/')  
# 			context_instance = {'student':student, 'subject':subject, 'about': about}
# 			return render(request, 'center/instructions.html', context_instance)
        

# def update_elapse_time(request):
# 	if request.is_ajax():
# 		flash_message = ''
# 		try:
# 			student = Candidate.objects.get(user=request.user)
# 			if request.method == 'POST':
# 				minutes = request.POST.get('incByMinutes')
# 				subject = request.POST.get('cur_subj')
# 				try:
# 					person = CenterSubjectScore.objects.get(subject=subject)
# 					person.time_used += 2
# 					person.save()        
# 					return render_to_response('center/choice.html')
# 				except (KeyError, CenterSubjectScore.DoesNotExist):
# 					pass
# 		except (KeyError, Candidate.DoesNotExist):
# 			#return HttpResponseRedirect('/mocktest/login_exam/')
# 			pass
# 		return JsonResponse({"flash_message":flash_message,})
# 	else:
# 		raise Http404

# @login_required
# def user_choice(request):
# 	if request.is_ajax():
# 		flash_message = ''
# 		try:
# 			student = Candidate.objects.get(user=request.user)
# 			if request.method == 'POST':
# 				choice_datum = request.POST.get('user_choice_question')
# 				choice_data=choice_datum.split('_')
# 				dsubject = request.POST.get('cur_subj')
# 				try:
# 					subject = CenterSubjectScore.objects.get(pk=dsubject)
# 					try:
# 						question_id = int(choice_data[0])
# 						d_question = ExamQuestion.objects.get(id=question_id)
# 						d_choice = str(choice_data[1])
# 						try:
# 							script = CenterUserScript.objects.get(user = student, subject=subject, question = d_question)
# 							script.choice = d_choice
# 							script.save()   
# 						except CenterUserScript.DoesNotExist:
# 							"Invalid Examination Script! Contact Invigilator To Logout & Login Again"     
# 						return render_to_response('center/choice.html')
# 					except KeyError:
# 						flash_message = "Invalid Option!"
# 				except CenterSubjectScore.DoesNotExist:
# 					flash_message = "Invalid Examination Subject! Contact Invigilator To Logout & Login Again"
# 		except (KeyError, Candidate.DoesNotExist):
# 			flash_message = "You Are Not Logged In"
# 		return JsonResponse({"flash_message":flash_message,})
# 	else:
# 		raise Http404

    

# @login_required
# def start_exam(request, pk):
# 	try:
# 		about = About.objects.all()[0]
# 	except Exception:
# 		about = None
# 	if request.user.is_staff:
# 		logout(request)
# 		return HttpResponseRedirect('/mocktest/login_exam/')
# 	try:
# 		student = Candidate.objects.get(user=request.user)
# 	except Candidate.DoesNotExist:
# 		logout(request)
# 		return HttpResponseRedirect('/mocktest/login_exam/')
# 	cur_subj = CenterSubjectScore.objects.get(pk=pk)
# 	if cur_subj.result.user != student:
# 		return HttpResponseRedirect('/mocktest/')
# 	subject = cur_subj.subject
# 	if cur_subj.done:
# 		return HttpResponseRedirect('/mocktest/')
# 	duration = subject.duration
# 	timespent = timezone.localtime(timezone.now()) - cur_subj.time_started
# 	time_duration = timedelta(minutes= int(duration))
# 	if cur_subj.time_used >= duration:
# 		cur_subj.done = True
# 		cur_subj.save()
# 		return HttpResponseRedirect('/mocktest/')
# 	else:
# 		time_elapsed = cur_subj.time_used
# 		questions = []
# 		if subject.randomise:
# 			userques = CenterUserScript.objects.filter(user=student, subject=cur_subj).order_by('?')
# 		else:
# 			userques = CenterUserScript.objects.filter(user=student, subject=cur_subj).order_by('question')
# 		for ii in userques:
# 			i = ii.question.id
# 			q = ExamQuestion.objects.get(id=i)
# 			selected_choice = ii.choice
# 			payload = {'question':q, 'selected_choice':selected_choice}
# 			questions.append(payload)
# 		if len(questions) != subject.questions_to_do:
# 			#delete scipt
# 			userques.delete()
# 			questions = []
# 			if subject.randomise:
# 				que_set = ExamQuestion.objects.filter(
# 					subject=subject, 
# 					level=student.previous_class.level).order_by('?')[:int(subject.questions_to_do)]
# 			else:
# 				que_set = ExamQuestion.objects.filter(
# 					subject=subject, 
# 					level=student.previous_class.level).order_by('id')[:int(subject.questions_to_do)]
# 			bulk_script = []
# 			for ques in que_set:
# 				new_script = CenterUserScript()
# 				new_script.question = ques
# 				new_script.subject = cur_subj
# 				new_script.user = student
# 				bulk_script.append(new_script)
# 				selected_choice = 'nil'
# 				payload = {'question':ques, 'selected_choice':selected_choice}
# 				questions.append(payload)
# 			CenterUserScript.objects.bulk_create(bulk_script)

# 		if request.method == 'POST':
# 			cur_subj.time_ended = timezone.localtime(timezone.now())
# 			cur_subj.save()
# 			#check for number of questions answered
# 			count = 0
# 			duration_check = duration - 2
# 			for key, value in request.POST.items():
# 				if str(value) == 'a' or str(value) == 'b' or str(value) == 'c' or str(value) == 'd' or str(value) == 'e':
# 					count += 1
# 			if count < subject.minimum_to_do:
# 				if int(cur_subj.time_used) < int(duration_check):
# 					starttime = cur_subj.time_started.strftime('%a %b %d %Y %H:%M:%S %z')
# 					context_instance={'payload': questions,
# 					 'student':student,
# 					 'starttime': starttime,
# 					 'time_elapsed': time_elapsed,
# 					 'about': about,
# 					 'subject': subject,
# 					 'error_message': ("You have to answer a minimum of " +str(subject.minimum_to_do)+ 
# 					 " questions before you can submit"),
# 					  'duration':duration, 'cur_subj':cur_subj}
# 					return render(request, 'center/test.html', context_instance)

# 			for key, value in request.POST.items():
# 				try:
# 					p = ExamQuestion.objects.get(id=str(key))
# 				except (UnicodeEncodeError,ValueError, KeyError, ExamQuestion.DoesNotExist):
# 					pass
# 				else:
# 					try:
# 						selected_choice = str(value)
# 					except (UnicodeEncodeError,ValueError, KeyError):
# 						selected_choice = 'nil'
# 					else:
# 						#save user script
# 						try:
# 							script = CenterUserScript.objects.get(user=student, subject=cur_subj, question = p)
# 							script.choice = str(selected_choice)
# 							script.save()
# 						except Exception:
# 							pass

# 			if cur_subj.remarking() == cur_subj.score:
# 				cur_subj.marked = True
# 				cur_subj.done = True
# 				cur_subj.save()
# 			else:
# 				cur_subj.marked = False
# 				cur_subj.done = True
# 				cur_subj.save()			
# 			return HttpResponseRedirect('/mocktest/')

# 		else:
# 			starttime = cur_subj.time_started.strftime('%a %b %d %Y %H:%M:%S %z')
# 			context_instance={'payload': questions,
# 			 'student':student,
# 			 'starttime':starttime,
# 			 'time_elapsed': time_elapsed,
# 			 'about': about,
# 			 'subject': subject,
# 			  'duration':duration, 'cur_subj':cur_subj}
# 			return render(request, 'center/test.html', context_instance)



# @login_required
# def correction(request, pk):
# 	try:
# 		about = About.objects.all()[0]
# 	except Exception:
# 		about = None
# 	if request.user.is_staff:
# 		logout(request)
# 		return HttpResponseRedirect('/mocktest/login_exam/')
# 	try:
# 		student = Candidate.objects.get(user=request.user)
# 	except Candidate.DoesNotExist:
# 		logout(request)
# 		return HttpResponseRedirect('/mocktest/login_exam/')
# 	cur_subj = CenterSubjectScore.objects.get(pk=pk)
# 	if cur_subj.result.user != student:
# 		return HttpResponseRedirect('/mocktest/')
# 	subject = cur_subj.subject
# 	questions = []
# 	userques = CenterUserScript.objects.filter(user=student, subject=cur_subj).order_by('question')
# 	for ii in userques:
# 		i = ii.question.id
# 		q = ExamQuestion.objects.get(id=i)
# 		selected_choice = ii.choice
# 		answer = q.ans
# 		if ii.is_right:
# 			correct = True
# 		else:
# 			correct = False
# 		payload = {'question':q, 'selected_choice':selected_choice, 'answer':answer, 'correct':correct}
# 		questions.append(payload)

# 	context_instance={'payload': questions,
# 	 'student':student,
# 	 'about': about,
# 	 'subject': subject,
# 	  'cur_subj':cur_subj}
# 	return render(request, 'center/correction.html', context_instance)


