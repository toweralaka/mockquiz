# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404, render, redirect,render_to_response
from django.http import Http404, HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib import messages # add context to HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.views.generic import View
from django.utils import timezone
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from django.views.generic.edit import UpdateView
import datetime
from datetime import timedelta

# Create your views here.
from userprofile.models import (UserProfile, Result, UserScript, SubjectScore, Batch)
from bank.models import Topic, Examination, Subject, Question, SubTopic
from decimal import Decimal



def logout_exam(request):
    try:
        userprofile = UserProfile.objects.get(user=request.user)
        if userprofile.online:
            userprofile.online = False
            userprofile.save()
    except UserProfile.DoesNotExist:
        pass
    try:
        logout(request)
    except Exception:
        pass
    return HttpResponseRedirect('/login_exam/')


def update_elapse_time(request):
    try:
        userprofile = UserProfile.objects.get(user=request.user)
        if request.method == 'POST':
            minutes = request.POST.get('incByMinutes')
            try:
                person = Result.objects.get(user=userprofile)
                person.duration += 2
                person.save()        
                return render_to_response('lh/choice.html')
            except (KeyError, Result.DoesNotExist):
                pass
    except (KeyError, UserProfile.DoesNotExist):
        #return HttpResponseRedirect('/login_exam/')
        pass


def rdrct(request):
    return HttpResponseRedirect('/')

def centerrdrct(request):
    return HttpResponseRedirect('/mocktest/')

def centermockrdrct(request):
    return HttpResponseRedirect('/centermock/')


def login_exam(request):
    if request.method == "POST":
        username = request.POST['username']
        #password = request.POST['password']
        user = authenticate(username=username)#, password=password)
        if user is not None:
            if user.is_active:
                if not user.is_staff:
                    login(request, user)
                    try:
                        userprofile = UserProfile.objects.get(user=request.user)
                    except UserProfile.DoesNotExist:
                        logout(request)
                        messages.add_message(request, messages.INFO, "You Are Not Registered For This Examination. Contact invigilator")
                        return HttpResponseRedirect('/login_exam/') 
                    if not userprofile.batch:
                        a_batch = Batch.objects.filter(active=True, write_exam=True)[0]
                        if userprofile.exam_center != a_batch.exam_center:
                            logout(request)
                            context_instance={'error_message': 'This is Not Your Examination Center.'}
                            return render(request, 'lh/login.html', context_instance)
                        else:
                            userprofile.batch = a_batch
                            userprofile.save()
                    else:
                        btch = userprofile.batch
                        if not btch.write_exam:
                            logout(request)
                            context_instance={'error_message': 'Your examination batch is not writing at this time'}
                            return render(request, 'lh/login.html', context_instance)
                    # if userprofile.online:
                    #     logout(request)
                    #     context_instance={'error_message': 'You are already logged in on another device'}
                    #     return render(request, 'lh/login.html', context_instance)
                    if not userprofile.paid:
                        logout(request)
                        context_instance={'error_message': 'Your Payment For This Examination Has Not Been Confirmed'}
                        return render(request, 'lh/login.html', context_instance)
                    else:
                        userprofile.online = True
                        userprofile.save()
                        return HttpResponseRedirect('/')
                else:
                    context_instance={'error_message': 'Staff Logged in'}
                    return render(request, 'lh/login.html')
            else:
                context_instance={'error_message': 'Your account has been disabled. Please contact your vendor.'}
                return render(request, 'lh/login.html', context_instance)
        else:
            return render(request, 'lh/login.html', {'error_message': 'Invalid Username or Password'})
    return render(request, 'lh/login.html')


#@login_required #never for index page
def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login_exam/')
    else:
        if request.user.is_staff:
            return HttpResponseRedirect('/login_exam/')
        else:
            try:
                userprofile = UserProfile.objects.get(user=request.user)
            except UserProfile.DoesNotExist:
                logout(request)
                messages.add_message(request, messages.INFO, "This is not your examination batch. Contact invigilator")
                return HttpResponseRedirect('/login_exam/')        
            return render(request, 'lh/index.html', {'userprofile':userprofile})


@login_required
def instructions(request):
    if not request.user.is_authenticated:
        return render(request, 'lh/login.html')
    else:
        userprofile = UserProfile.objects.get(user=request.user)
        try:
            person = Result.objects.get(user = userprofile)
        except (KeyError, Result.DoesNotExist):
            person = 'nil'

        return render(request, 'lh/instructions.html',{'person':person,})



        

def check_if_correct(question_options, selected_choice):
    correct = False
    for option in question_options:
        if option.right and option == selected_choice:
            correct = True
    return correct


def user_choice(request):
    if request.is_ajax():
        saved_script = False
        try:
            userprofile = UserProfile.objects.get(user=request.user)
            try:
                choice_datum = request.POST.get('user_choice_question')
                choice_data=choice_datum.split('_')
                question_id = int(choice_data[0])
                d_question = Question.objects.get(id=question_id)
                d_choice = str(choice_data[1])
                script = UserScript.objects.filter(user = userprofile, question = d_question)[0]
                script.choice = d_choice
                script.save()        
                # flash_message = "Script Saved!"
                flash_message = ""
                saved_script = True
            except:
                flash_message = "Please Select An Option"
        except UserProfile.DoesNotExist:
            flash_message = "You Are Not Logged In"
        data = {
            "feed_back" : flash_message,
            "saved_script": saved_script
        }
        
        return JsonResponse(data)
    else:
        raise Http404


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
                return render_to_response('lh/choice.html')
            else:
                pass
    except (KeyError, UserProfile.DoesNotExist):
        #return HttpResponseRedirect('/login_exam/')
        pass
    

@login_required
def exam(request):
    try:
        userprofile = UserProfile.objects.get(user=request.user)
    except (KeyError, UserProfile.DoesNotExist):
        return HttpResponseRedirect('/login_exam/')
    #get user result object
    exam = userprofile.examination
    person, created = Result.objects.get_or_create(user = userprofile, 
    exam_area=userprofile.exam_area,
    exam_center=userprofile.exam_center,
    defaults={   
        'timestamp':timezone.localtime(timezone.now()),
        'batch':userprofile.batch})
    duration = exam.duration
    if person.done:
        return render(request, 'lh/instructions.html', {'person':person})
    time_elapsed = person.duration
    timespent = timezone.localtime(timezone.now()) - person.timestamp
    time_duration = timedelta(minutes= int(duration))
    if timespent > time_duration:
        person.done = True
        person.save()
        return render(request, 'lh/instructions.html', {'person':person})
    else:
        if request.method == 'POST':
            #check for number of questions answered
            count = len(request.POST.items()) - 1
            if count < exam.limit:
                timespent = timezone.localtime(timezone.now()) - person.timestamp
                time_duration = timedelta(minutes= int(duration))
                if timespent < time_duration:
                    starttime = person.timestamp.strftime('%a %b %d %Y %H:%M:%S %z')
                    context_instance={'payload': userprofile.get_user_scripts(),
                     'userprofile':userprofile,
                     'starttime': starttime,
                     'time_elapsed': time_elapsed,
                     'error_message': "You have to answer a minimum of " +str(exam.limit)+ " questions before you can submit",
                      'duration':duration, 'person':person}
                    return render(request, 'lh/test.html', context_instance)

            scrpts = {key:value for (key, value) in request.POST.items()}
            person.scripts = "%s -ADD- %s" %(person.scripts, scrpts)
            person.done = True
            person.save()
            return HttpResponseRedirect('/instructions/')

        else:
            starttime = person.timestamp.strftime('%a %b %d %Y %H:%M:%S %z')
            context_instance={'payload': userprofile.get_user_scripts(),
             'userprofile':userprofile,
             'time_elapsed': time_elapsed,
             'starttime':starttime,
              'duration':duration, 'person':person}
            return render(request, 'lh/test.html', context_instance)


# @login_required
# def exam(request):
#     try:
#         userprofile = UserProfile.objects.get(user=request.user)
#     except (KeyError, UserProfile.DoesNotExist):
#         return HttpResponseRedirect('/login_exam/')
#     #get user result object
#     exam = userprofile.examination
#     person, created = Result.objects.get_or_create(user = userprofile, 
#     exam_area=userprofile.exam_area,
#     exam_center=userprofile.exam_center,
#     defaults={   
#         'timestamp':timezone.localtime(timezone.now()),
#         'batch':userprofile.batch})
#     duration = exam.duration
#     if person.done:
#         return render(request, 'lh/instructions.html', {'person':person})
#     time_elapsed = person.duration
#     timespent = timezone.localtime(timezone.now()) - person.timestamp
#     time_duration = timedelta(minutes= int(duration))
#     if timespent > time_duration:
#         person.done = True
#         person.save()
#         return render(request, 'lh/instructions.html', {'person':person})
#     else:
#         subjects = userprofile.subject.all()
#         totques = 0
#         for s in subjects:
#             totques += s.to_do
#         questions = []
#         userques = UserScript.objects.filter(user = userprofile)
#         if userques.count() != totques:
#             #clear the userscripts
#             userscript = UserScript.objects.filter(user=userprofile)
#             for i in userscript:
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
#                                         new_script = UserScript()
#                                         new_script.question = ques
#                                         new_script.user = userprofile
#                                         bulk_script.append(new_script)
#                                         selected_choice = 'nil'
#                                         payload = {'question':ques, 'selected_choice':selected_choice}
#                                         questions.append(payload)
#                                     UserScript.objects.bulk_create(bulk_script)
#                                     subtpunit += 1
#                                 else:
#                                     pass
#                         else:
#                             que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name), topic=str(tp)).order_by('?')[:(int(tp.to_do))]
#                             bulk_script = []
#                             for ques in que_set:
#                                 new_script = UserScript()
#                                 new_script.question = ques
#                                 new_script.user = userprofile
#                                 bulk_script.append(new_script)
#                                 selected_choice = 'nil'
#                                 payload = {'question':ques, 'selected_choice':selected_choice}
#                                 questions.append(payload)
#                             UserScript.objects.bulk_create(bulk_script)
                                
#                 else:
#                     que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name)).order_by('?')[:(int(subject.to_do))]
#                     bulk_script = []
#                     for ques in que_set:
#                         new_script = UserScript()
#                         new_script.question = ques
#                         new_script.user = userprofile
#                         bulk_script.append(new_script)
#                         selected_choice = 'nil'
#                         payload = {'question':ques, 'selected_choice':selected_choice}
#                         questions.append(payload)
#                     UserScript.objects.bulk_create(bulk_script)
#         else:
#             for ii in userques:
#                 i = ii.question.id
#                 q = Question.objects.get(id=i)
#                 selected_choice = ii.choice
#                 payload = {'question':q, 'selected_choice':selected_choice}
#                 questions.append(payload)
                
#         ##resort questions(scrambling)
#         #questions = sorted(questions, key=lambda question:question.ans)
        
#         if request.method == 'POST':
#             #check for number of questions answered
#             count = 0
#             for key, value in request.POST.items():
#                 if str(value) == 'a' or str(value) == 'b' or str(value) == 'c' or str(value) == 'd' or str(value) == 'e':
#                     count += 1
#             if count < exam.limit:
#                 timespent = timezone.localtime(timezone.now()) - person.timestamp
#                 time_duration = timedelta(minutes= int(duration))
#                 if timespent < time_duration:
#                     starttime = person.timestamp.strftime('%a %b %d %Y %H:%M:%S %z')
#                     context_instance={'payload': questions,
#                      'userprofile':userprofile,
#                      'starttime': starttime,
#                      'time_elapsed': time_elapsed,
#                      'error_message': "You have to answer a minimum of " +str(exam.limit)+ " questions before you can submit",
#                       'duration':duration, 'person':person}
#                     return render(request, 'lh/test.html', context_instance)

#             scrpts = {key:value for (key, value) in request.POST.items()}
#             person.scripts = "%s -ADD- %s" %(person.scripts, scrpts)
#             # for key, value in request.POST.items():
#             #     try:
#             #         p = Question.objects.get(id=str(key))
#             #     except (UnicodeEncodeError,ValueError, KeyError, Question.DoesNotExist):
#             #         pass
#             #     else:
#             #         # try:
#             #         #     selected_choice = str(value)
#             #         #     if p.ans == selected_choice:
#             #         #         is_correct = True 
#             #         #     else:
#             #         #         is_correct = False
#             #         # except (UnicodeEncodeError,ValueError, KeyError):
#             #         #     selected_choice = 'nil'
#             #         #     is_correct = False
#             #         #     pass

#             #         # else:
#             #         #save user script
#             #         try:
#             #             script = UserScript.objects.filter(user = userprofile,question = p)[0]
#             #             selected_choice = str(value)
#             #             script.choice = str(selected_choice)
#             #             script.save()
#             #         except:
#             #             pass

#             person.done = True
#             person.save()
#             return HttpResponseRedirect('/instructions/')

#         else:
#             starttime = person.timestamp.strftime('%a %b %d %Y %H:%M:%S %z')
#             context_instance={'payload': questions,
#              'userprofile':userprofile,
#              'time_elapsed': time_elapsed,
#              'starttime':starttime,
#               'duration':duration, 'person':person}
#             return render(request, 'lh/test.html', context_instance)

