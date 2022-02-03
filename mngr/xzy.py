def logout_exam(request):
    userprofile = Applicant.objects.get(user=request.user)
    if userprofile.online:
        userprofile.online = False
        userprofile.save()
    logout(request)

    return HttpResponseRedirect('/login_exam/')


def login_exam(request):
    if request.method == "POST":
        username = request.POST['username']
        user = authenticate(username=username)
        if user is not None:
            if user.is_active:
                if not user.is_staff:
                    login(request, user)
                    userprofile = Applicant.objects.get(user=request.user)
                    applicant = BatchedUser.objects.get(user=userprofile)
                    if not applicant.batch.active: 
                        logout(request)
                        context_instance={'error_message': 'You are not batched for this examination'}
                        return render(request, 'mngr/login.html', context_instance)

                    elif not applicant.batch.write_exam:#and date dont tally
                        logout(request)
                        context_instance={'error_message': 'You are not batched for this examination'}
                        return render(request, 'mngr/login.html', context_instance)
                    else:
                        if userprofile.online:
                            logout(request)
                            context_instance={'error_message': 'You are already logged in on another device'}
                            return render(request, 'mngr/login.html', context_instance)
                        else:
                            userprofile.online = True
                            userprofile.save()
                            return HttpResponseRedirect('/')
                else:
                    context_instance={'error_message': 'Staff Logged in'}
                    return render(request, 'mngr/login.html')
            else:
                context_instance={'error_message': 'Your account has been disabled.'}
                return render(request, 'mngr/login.html', context_instance)
        else:
            return render(request, 'mngr/login.html', {'error_message': 'Invalid Username or Password'})
    return render(request, 'mngr/login.html')



@login_required
def instructions(request):
    if not request.user.is_authenticated():
        return render(request, 'mngr/login.html')
    else:
        userprofile = Applicant.objects.get(user=request.user)
        batcheduser = BatchedUser.objects.get(user=userprofile)
        try:
            person = Result.objects.get(user = batcheduser)
        except (KeyError, Result.DoesNotExist):
            person = 'nil'

        return render(request, 'mngr/instructions.html',{'person':person,'userprofile':userprofile,})


# @login_required
# def user_choice(request):
#     if not request.user.is_authenticated():
#         return render(request, 'mngr/login.html')
#     else:
#         userprofile = Applicant.objects.get(user=request.user)
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
#             return render_to_response('mngr/test.html', {'user_choice':user_choice})

        

def check_if_correct(question_options, selected_choice):
    correct = False
    for option in question_options:
        if option.right and option == selected_choice:
            correct = True
    return correct


@login_required
def user_choice(request):
    try:
        userprofile = Applicant.objects.get(user=request.user)
        batcheduser = BatchedUser.objects.get(user=userprofile)
        if request.method == 'POST':
            choice_datum = request.POST.get('user_choice_question')
            choice_data=choice_datum.split('_')
            try:
                question_id = int(choice_data[0])
                d_question = Question.objects.get(id=question_id)
                d_choice = str(choice_data[1])
                script, new = UserScript.objects.get_or_create(user = batcheduser,question = d_question)
                script.choice = d_choice
                script.save()        
                return render_to_response('mngr/choice.html')
            except KeyError:
                pass
    except (KeyError, Applicant.DoesNotExist):
        #return HttpResponseRedirect('/login_exam/')
        pass


@login_required
def user_time(request):
    try:
        userprofile = Applicant.objects.get(user=request.user)
        batcheduser = BatchedUser.objects.get(user=userprofile)
        if request.method == 'POST':
            timespent = int(float(request.POST.get('user_time_spent')))
            if timespent > 0:
                result = Result.objects.get(user = batcheduser)
                result.duration = result.duration - timespent
                result.save()
                return render_to_response('mngr/choice.html')
            else:
                pass
    except (KeyError, Applicant.DoesNotExist):
        #return HttpResponseRedirect('/login_exam/')
        pass
    

@login_required
def exam(request):
    try:
        userprofile = Applicant.objects.get(user=request.user)
    except (KeyError, Applicant.DoesNotExist):
        return HttpResponseRedirect('/login_exam/')
    #get user result object
    batcheduser=BatchedUser.objects.get(user=userprofile)
    firm = batcheduser.batch.firm
    person, created = Result.objects.get_or_create(user = batcheduser)
    if created:
        person.duration = batcheduser.batch.duration
        person.save()
    if person.done:
        return render(request, 'mngr/instructions.html', {'person':person})
    if person.duration <= 0:
        person.done = True
        person.save()
        return render(request, 'mngr/instructions.html', {'person':person})
    else:
        subjects = batcheduser.batch.subject.all()
        totques = 0
        for s in subjects:
            if s:
                totques += s.to_do

        duration = person.duration
        questions = []
        userques = UserScript.objects.filter(user = userprofile)
        for ii in userques:
            i = ii.question.id
            q = Question.objects.get(id=i)
            selected_choice = ii.choice
            payload = {'question':q, 'selected_choice':selected_choice}
            questions.append(payload)
        if len(questions) !=totques: #not userques.exists(): #len(questions) != totques:
            questions = []
            #clear the userscripts
            userscript = UserScript.objects.filter(user=batcheduser)
            for i in userscript:
                i.delete()
            #create new userscripts and questions to do
            for subject in subjects:
                print(subject)
                if subject:
                        que_set = Question.objects.filter(subject=str(subject.name)).order_by('?')[:(int(subject.to_do))]
                        bulk_script = []
                        for ques in que_set:
                            new_script = UserScript()
                            new_script.question = ques
                            new_script.user = batcheduser
                            bulk_script.append(new_script)
                            selected_choice = 'nil'
                            payload = {'question':ques, 'selected_choice':selected_choice}
                            questions.append(payload)
                        UserScript.objects.bulk_create(bulk_script)
                        
        ##resort questions(scrambling)
        #questions = sorted(questions, key=lambda question:question.ans)
        
        if request.method == 'POST':
            person.time_ended =  timezone.now()        
            person.done = True
            person.save()
            for key, value in request.POST.items():
                try:
                    p = Question.objects.get(id=str(key))
                    try:
                        selected_choice = str(value)
                        #save user script
                        script, new = UserScript.objects.get_or_create(user = batcheduser,question = p)
                        script.choice = str(selected_choice)
                        script.save()
                    except (UnicodeEncodeError,ValueError, KeyError):
                        selected_choice = 'nil'
                except (UnicodeEncodeError,ValueError, KeyError, Question.DoesNotExist):
                    pass
            return HttpResponseRedirect('/instructions/')

        else:
            context_instance={'payload': questions,
             'userprofile':userprofile,
             'starttime':person.time_started,
             'firm':firm,
             'batcheduser':batcheduser,
              'duration':duration, 'person':person}
            return render(request, 'mngr/test.html', context_instance)



@login_required
def d_exam(request):
    try:
        userprofile = Applicant.objects.get(user=request.user)
    except (KeyError, Applicant.DoesNotExist):
        return HttpResponseRedirect('/login_exam/')
    #get user result object
    exam = userprofile.examination
    person, created = Result.objects.get_or_create(user = userprofile, 
    defaults={   
    'batch':userprofile.batch})
    if created:
        person.duration = exam.duration
        person.save()
    if person.done:
        return render(request, 'mngr/instructions.html', {'person':person})
    if person.duration <= 0:
        person.done = True
        person.save()
        return render(request, 'mngr/instructions.html', {'person':person})
    else:
        subjects = [userprofile.subject1, userprofile.subject2, userprofile.subject3, userprofile.subject4]
        totques = 0
        for s in subjects:
            if s:
                totques += s.to_do

        duration = person.duration
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
                if subject:
                    topics = subject.topic_set.all()
                    if subject.topic_set.all().exists():
                        for tp in topics:
                            subtops = tp.subtopic_set.all()
                            if tp.subtopic_set.all().exists():
                                subtpunit = 0
                                for i in subtops:
                                    if subtpunit < int(tp.unit_subtopic):
                                        que_set = Question.objects.filter(subject=str(subject.name), topic=str(tp), subtopic=str(i)).order_by('?')[:(int(i.to_do))]
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
                                que_set = Question.objects.filter(subject=str(subject.name), topic=str(tp)).order_by('?')[:(int(tp.to_do))]
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
                        que_set = Question.objects.filter(subject=str(subject.name)).order_by('?')[:(int(subject.to_do))]
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
                return render(request, 'mngr/test.html', context_instance)

            for key, value in request.POST.items():
                try:
                    p = Question.objects.get(id=str(key))
                    try:
                        selected_choice = str(value)
                        #save user script
                        script, new = UserScript.objects.get_or_create(user = userprofile,question = p)
                        script.choice = str(selected_choice)
                        script.save()
                    except (UnicodeEncodeError,ValueError, KeyError):
                        selected_choice = 'nil'
                except (UnicodeEncodeError,ValueError, KeyError, Question.DoesNotExist):
                    pass
                        
            person.done = True
            person.save()
            return HttpResponseRedirect('/instructions/')

        else:
            context_instance={'payload': questions,
             'userprofile':userprofile,
             'starttime':person.time_started,
             'exam':exam,
              'duration':duration, 'person':person}
            return render(request, 'mngr/test.html', context_instance)