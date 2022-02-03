# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404, render, redirect,render_to_response
from django.http import Http404, HttpResponseRedirect, HttpResponse
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

# Create your views here.
from userprofile.models import (UserProfile, Result, UserScript,
    Photocard, ExamSession, SubjectScore, Batch)
from bank.models import Topic, Examination, Subject, Question, SubTopic
from decimal import Decimal



def logout_exam(request):
    userprofile = UserProfile.objects.get(user=request.user)
    if userprofile.online:
        userprofile.online = False
        userprofile.save()
    logout(request)

    return HttpResponseRedirect('/login_exam/')


def login_exam(request):
    if request.method == "POST":
        username = request.POST['username']
        #password = request.POST['password']
        user = authenticate(username=username)#, password=password)
        if user is not None:
            if user.is_active:
                if not user.is_staff:
                    login(request, user)
                    userprofile = UserProfile.objects.get(user=request.user)
                    if not userprofile.batch:
                        logout(request)
                        context_instance={'error_message': 'You are not batched for this examination'}
                        return render(request, 'lh/login.html', context_instance)
                    else:
                        btch = userprofile.batch
                        if not btch.write_exam:
                            logout(request)
                            context_instance={'error_message': 'This is not your examination batch'}
                            return render(request, 'lh/login.html', context_instance)
                        else:
                            if userprofile.online:
                                logout(request)
                                context_instance={'error_message': 'You are already logged in on another device'}
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



def index(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login_exam/')
    else:
        if request.user.is_staff:
            return HttpResponseRedirect('/login_exam/')
        else:
            userprofile = UserProfile.objects.get(user=request.user)
        
            return render(request, 'lh/index.html', {'userprofile':userprofile})


@login_required
def instructions(request):
    if not request.user.is_authenticated():
        return render(request, 'lh/login.html')
    else:
        userprofile = UserProfile.objects.get(user=request.user)
        try:
            person = Result.objects.get(user = userprofile)
        except (KeyError, Result.DoesNotExist):
            person = 'nil'

        return render(request, 'lh/instructions.html',{'person':person,})


# @login_required
# def user_choice(request):
#     if not request.user.is_authenticated():
#         return render(request, 'lh/login.html')
#     else:
#         userprofile = UserProfile.objects.get(user=request.user)
#         if request.method== 'POST':
#             d_choice = request.POST.get('user_choice')
#             d_question = request.POST.get('user_choice_question')
#             csrf = request.POST.get('csrfmiddlewaretoken')
#             for key, value in request.POST.items():
#                 print(key, value)
#             print(d_question)
#             print('against')
#             print('d_choice')
#             print('against')
#             print(csrf)
            
#             # print(str(d_choice))
#             # print(str(d_question))
#             # user_choice, i = UserScript.objects.get_or_create(user=userprofile, question=d_question)
#             # user_choice.choice = str(d_choice)
#             #print(str(user_choice.question))
#             #print(user_choice.choice)
#             return render_to_response('lh/test.html', {'user_choice':user_choice})

        

def check_if_correct(question_options, selected_choice):
    correct = False
    for option in question_options:
        if option.right and option == selected_choice:
            correct = True
    return correct


@login_required
def user_choice(request):
    try:
        userprofile = UserProfile.objects.get(user=request.user)
        if request.method == 'POST':
            choice_datum = request.POST.get('user_choice_question')
            choice_data=choice_datum.split('_')
            print (choice_data)
            try:
                question_id = int(choice_data[0])
                d_question = Question.objects.get(id=question_id)
                d_choice = str(choice_data[1])
                script, new = UserScript.objects.get_or_create(user = userprofile,question = d_question)
                script.choice = d_choice
                script.save()        
                return render_to_response('lh/choice.html')
            except KeyError:
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

    person, created = Result.objects.get_or_create(user = userprofile, 
    exam_area=userprofile.exam_area,
    exam_center=userprofile.exam_center,
    defaults={   
    'batch':userprofile.batch})
    if person.marked:
        return render(request, 'lh/instructions.html', {'person':person})
    else:
        subjects = userprofile.subject.all()
        totques = 0
        for s in subjects:
            totques += s.to_do

        exam = userprofile.examination
        duration = exam.duration
        questions = []
        userques = UserScript.objects.filter(user = userprofile)
        for ii in userques:
            i = ii.question.id
            q = Question.objects.get(id=i)
            selected_choice = ii.choice
            payload = {'question':q, 'selected_choice':selected_choice}
            questions.append(payload)
        if len(questions) != totques:
            questions = []
            #clear the userscripts
            userscript = UserScript.objects.filter(user=userprofile)
            for i in userscript:
                i.delete()
            #create new userscripts and questions to do
            for subject in subjects:
                topics = subject.topic_set.all()
                if subject.topic_set.all().exists():
                    for tp in topics:
                        subtops = tp.subtopic_set.all()
                        if tp.subtopic_set.all().exists():
                            subtpunit = 0
                            for i in subtops:
                                if subtpunit < int(tp.unit_subtopic):
                                    que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name), topic=str(tp), subtopic=str(i)).order_by('?')[:(int(i.to_do))]
                                    bulk_script = []
                                    for ques in que_set:
                                        new_script = UserScript()
                                        new_script.question = ques
                                        new_script.user = userprofile
                                        bulk_script.append(new_script)
                                        selected_choice = 'nil'
                                        payload = {'question':ques, 'selected_choice':selected_choice}
                                        questions.append(payload)
                                    UserScript.objects.bulk_create(bulk_script)
                                    subtpunit += 1
                                else:
                                    pass
                        else:
                            que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name), topic=str(tp)).order_by('?')[:(int(tp.to_do))]
                            bulk_script = []
                            for ques in que_set:
                                new_script = UserScript()
                                new_script.question = ques
                                new_script.user = userprofile
                                bulk_script.append(new_script)
                                selected_choice = 'nil'
                                payload = {'question':ques, 'selected_choice':selected_choice}
                                questions.append(payload)
                            UserScript.objects.bulk_create(bulk_script)
                                
                else:
                    que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name)).order_by('?')[:(int(subject.to_do))]
                    bulk_script = []
                    for ques in que_set:
                        new_script = UserScript()
                        new_script.question = ques
                        new_script.user = userprofile
                        bulk_script.append(new_script)
                        selected_choice = 'nil'
                        payload = {'question':ques, 'selected_choice':selected_choice}
                        questions.append(payload)
                    UserScript.objects.bulk_create(bulk_script)
                        
        ##resort questions(scrambling)
        #questions = sorted(questions, key=lambda question:question.ans)
        
        if request.method == 'POST':
            #if page is refreshed, make recorded score zero
            for subD in SubjectScore.objects.filter(user=str(person.user.regnum)):
                subD.score = 0
                subD.save()
            #clear userscript
            # for i in UserScript.objects.filter(user=person.user):
            #     i.delete()
                #print(str(i))
               # subD.save()
            #check for number of questions answered
            count = 0
            for key, value in request.POST.items():
                if str(value) == 'a' or str(value) == 'b' or str(value) == 'c' or str(value) == 'd' or str(value) == 'e':
                    count += 1
            if count < exam.limit:
                context_instance={'payload': questions,
                 'userprofile':userprofile,
                 'error_message': "You have to answer a minimum of " +str(exam.limit)+ " questions before you can submit",
                  'duration':duration, 'person':person}
                return render(request, 'lh/test.html', context_instance)
            # if count > totques:
            #     for subD in SubjectScore.objects.filter(user=str(person.user.regnum)):
            #     subD.score = 0
            #     subD.save()
            # #check for number of questions answered
            # count = 0
            # for key, value in request.POST.items():
            #     if str(value) == 'a' or str(value) == 'b' or str(value) == 'c' or str(value) == 'd' or str(value) == 'e':
            #         count += 1

            for key, value in request.POST.items():
                try:
                    p = Question.objects.get(id=str(key))
                except (UnicodeEncodeError,ValueError, KeyError, Question.DoesNotExist):
                    pass
                else:
                    try:
                        selected_choice = str(value)
                        if p.ans == selected_choice:
                            is_correct = True
                        else:
                            is_correct = False
                    except (UnicodeEncodeError,ValueError, KeyError):
                        selected_choice = 'nil'
                        is_correct = False
                        pass

                    else:
                        #save user script
                        script, new = UserScript.objects.get_or_create(user = userprofile,question = p)
                        script.choice = str(selected_choice)
                        script.save()
                        subj, new = SubjectScore.objects.get_or_create(user=str(person.user.regnum), subject=str(p.subject)) 
                        dtpc = p.topic  
                        dsub = p.subject
                        dsubtop = p.subtopic
                        sbjct = Subject.objects.get(name=dsub, examination=exam)
                        try:
                            tpc = Topic.objects.get(name=str(dtpc), subject=sbjct)
                        except Topic.DoesNotExist:
                            wet = sbjct.weight
                        else:
                            try:
                                sbtp = SubTopic.objects.get(name=str(dsubtop), topic=tpc)
                                wet = sbtp.weight
                            except SubTopic.DoesNotExist:
                                wet = tpc.weight
                                
                        if is_correct:
                            subj.score = Decimal(subj.score) + Decimal(wet)
                            subj.save()
                            
                        else:
                            subj.score = Decimal(subj.score)
                            subj.save()
            #record scores against user
            person.marked = True
            total = 0
            for sub in SubjectScore.objects.filter(user=str(person.user.regnum)):
                total += sub.score
            person.total = total
            person.save()
            return HttpResponseRedirect('/instructions/')

        else:
            context_instance={'payload': questions,
             'userprofile':userprofile,
             'starttime':person.timestamp,
              'duration':duration, 'person':person}
            return render(request, 'lh/test.html', context_instance)