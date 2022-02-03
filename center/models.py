from __future__ import unicode_literals
from django.conf import settings
from django.urls import reverse
from django.db import models
from django.utils.safestring import mark_safe
from ckeditor_uploader.fields import RichTextUploadingField 
from django.db.models.signals import post_save, pre_save
from django.utils import timezone
import datetime
from datetime import timedelta
from decimal import Decimal

from bank.models import Examination, Subject, Question, Topic, SubTopic
from mngr.models import Advert
from userprofile.models import State, ExamCenter


# Create your models here.

class CenterCode(models.Model):
    pin = models.CharField(max_length=6)
    srn = models.CharField(max_length=8, unique=True)
    generated = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=False)
    used = models.BooleanField(default=False)
    user = models.CharField(max_length=150, blank=True, null=True, 
        help_text="This is created when pins are issued for sale. This is the login detail")
    time_used = models.DateTimeField(blank=True, null=True)
    issued = models.BooleanField(default=False)
    buyer = models.CharField(max_length=200, blank=True, null=True, help_text="center name")#upon issue, user is created
    set_name = models.CharField(max_length=200, blank=True, null=True,
        help_text="The name of the batch to issue. This is for easy deactivation")
    alert = models.BooleanField(default=False)
    alert_by = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        unique_together = ('pin', 'srn')


    def __str__(self):
        return self.srn



class Candidate(models.Model):
    SEX = (
        ('F', 'female'),
        ('M', 'male'),
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200, blank=False, null=False)
    sex = models.CharField(max_length=1, choices=SEX) 
    phone = models.CharField(max_length=13)
    exam_center = models.ForeignKey(ExamCenter, on_delete=models.PROTECT)
    issued_by = models.CharField(max_length=200, blank=False, null=False)
    examination = models.ForeignKey(Examination, on_delete=models.PROTECT)
    subject = models.ManyToManyField(Subject)
    regnum = models.CharField(max_length=10, verbose_name="Serial")
    feedback = models.ForeignKey(Advert, on_delete=models.SET_NULL, blank=True, null=True, help_text=("How did you hear about this mock?"))
    online = models.BooleanField(default=False)
    regdate = models.DateTimeField(auto_now_add=True)


    def subss(self):
        sjt = []
        for i in self.subject.all():
            a = str(i.name)[0:4]
            sjt.append(a)
        return sjt


    def get_absolute_url(self):
        return reverse('center:index')#, kwargs={'pk': self.pk})


    def taken_test(self):
        try:
            CenterResult.objects.get(user__regnum=self.regnum)
            return "Present"
        except CenterResult.DoesNotExist:
            return "Absent"

    def user_scripts(self):
        questions = []
        exam = self.examination
        #create new userscripts and questions to do
        for subject in self.subject.all():
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
                                    new_script = CenterUserScript()
                                    new_script.question = ques
                                    new_script.user = self
                                    bulk_script.append(new_script)
                                    selected_choice = '-'
                                    payload = {'question':ques, 'selected_choice':selected_choice}
                                    questions.append(payload)
                                CenterUserScript.objects.bulk_create(bulk_script)
                                subtpunit += 1
                            else:
                                break
                    else:
                        que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name), topic=str(tp)).order_by('?')[:(int(tp.to_do))]
                        bulk_script = []
                        for ques in que_set:
                            new_script = CenterUserScript()
                            new_script.question = ques
                            new_script.user = self
                            bulk_script.append(new_script)
                            selected_choice = '-'
                            payload = {'question':ques, 'selected_choice':selected_choice}
                            questions.append(payload)
                        CenterUserScript.objects.bulk_create(bulk_script)
                            
            else:
                que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name)).order_by('?')[:(int(subject.to_do))]
                bulk_script = []
                for ques in que_set:
                    new_script = CenterUserScript()
                    new_script.question = ques
                    new_script.user = self
                    bulk_script.append(new_script)
                    selected_choice = '-'
                    payload = {'question':ques, 'selected_choice':selected_choice}
                    questions.append(payload)
                CenterUserScript.objects.bulk_create(bulk_script)
        # else:
        #     for ii in userques:
        #         i = ii.question.id
        #         q = Question.objects.get(id=i)
        #         selected_choice = ii.choice
        #         payload = {'question':q, 'selected_choice':selected_choice}
        #         questions.append(payload)
        return questions

    def get_user_scripts(self):
        if self.taken_test() == "Absent":
            totques = 0
            for s in self.subject.all():
                totques += s.to_do
            userques = CenterUserScript.objects.filter(user = self)
            if userques.count() != totques:
                #clear the userscripts
                for i in userques:
                    i.delete()
                questions = self.user_scripts()
            else:
                questions = [{'question':q.question, 'selected_choice':q.choice} for q in userques]
        else:
            questions = [
            {'question':q.question, 'selected_choice':q.choice} for q in CenterUserScript.objects.filter(
                user = self)]
        return questions

    def __str__(self):
        return self.regnum
        #return self.user.username



class CenterResult(models.Model):
    user = models.OneToOneField(Candidate, on_delete=models.CASCADE)
    exam_center = models.ForeignKey(ExamCenter, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    started = models.BooleanField(default = False)
    time_started = models.DateTimeField(blank=True, null=True)
    time_ended = models.DateTimeField(blank=True, null=True)
    done = models.BooleanField(default = False)
    marked = models.BooleanField(default = False)
    total = models.DecimalField(max_digits=5, decimal_places=0, default=0)
    duration = models.IntegerField(default = 0)
    scripts = models.TextField(blank=True, null=True)



    def full_name(self):
        return self.user.full_name

    @property
    def timespent(self):
        if self.time_ended:
            return self.time_ended - self.time_started
        else:
            return None

    def issued_to(self):
        sn = CenterCode.objects.get(user=self.user.regnum)
        return sn.buyer

    @property
    def scores(self):
        s=[]
        if self.marked:
            for i in CenterSubjectScore.objects.filter(user=str(self.user.regnum)):
                dscore = str(i.subject) + ' = ' + str(int(i.score)) 
                s.append(dscore)
        return s

    @property
    def full_scores(self):
        s=[]
        if self.marked:
            for i in CenterSubjectScore.objects.filter(user=str(self.user.regnum)):
                dscore = str(i.subject) + ' = ' + str(int(i.score)) + ' [attempted('+ str(i.attempted()) +' questions)]'
                s.append(str(dscore))
        return s

    @property
    def totals(self):
        t=0
        if self.done:
            for s in CenterSubjectScore.objects.filter(user=str(self.user.regnum)):
                t += int(s.score)
        return t

    def markscript(self):
        instance = self
        if instance.started:
            exam = instance.user.examination
            timespent = timezone.localtime(timezone.now()) - instance.time_started
            time_duration = timedelta(minutes= int(exam.duration))
            if instance.done or timespent > time_duration:
                if not instance.marked:
                    oldscore = CenterSubjectScore.objects.filter(user=str(instance.user.regnum))
                    for j in oldscore:
                        j.delete()
                    exam = instance.user.examination
                    scripts = CenterUserScript.objects.filter(user=instance.user)
                    for ii in scripts:
                        i = ii.question.id
                        p = Question.objects.get(id=i)
                        try:
                            subj, new = CenterSubjectScore.objects.get_or_create(user=str(instance.user.regnum), subject=str(p.subject)) 
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
                                    
                            if ii.is_right():
                                subj.score = Decimal(subj.score) + Decimal(wet)
                                subj.save()
                                
                            else:
                                subj.score = Decimal(subj.score)
                                subj.save()
                        except Exception:
                            pass

                    #record scores against user
                    total = 0
                    scripts_total = 0
                    for sub in CenterSubjectScore.objects.filter(user=str(instance.user.regnum)):
                        total = total + sub.score
                        grade = Decimal(sub.remarking())
                        scripts_total = scripts_total + grade
                    instance.total = total
                    if scripts_total == total:
                        instance.marked = True
                    else:
                        instance.total = 0
                        instance.marked = False
                        oldscore = CenterSubjectScore.objects.filter(user=str(instance.user.regnum))
                        for j in oldscore:
                            j.score = 0
                            j.save()
                    instance.save()

    def __str__(self):
        return self.user.full_name



# def markscript_receiver(sender, instance, *args, **kwargs):
#     if instance.started:
#         exam = instance.user.examination
#         timespent = timezone.localtime(timezone.now()) - instance.time_started
#         time_duration = timedelta(minutes= int(exam.duration))
#         if instance.done or timespent > time_duration:
#             if not instance.marked:
#                 oldscore = CenterSubjectScore.objects.filter(user=str(instance.user.regnum))
#                 for j in oldscore:
#                     j.delete()
#                 exam = instance.user.examination
#                 scripts = CenterUserScript.objects.filter(user=instance.user)
#                 for ii in scripts:
#                     i = ii.question.id
#                     p = Question.objects.get(id=i)
#                     try:
#                         subj, new = CenterSubjectScore.objects.get_or_create(user=str(instance.user.regnum), subject=str(p.subject)) 
#                         dtpc = p.topic  
#                         dsub = p.subject
#                         dsubtop = p.subtopic
#                         sbjct = Subject.objects.get(name=dsub, examination=exam)
#                         try:
#                             tpc = Topic.objects.get(name=str(dtpc), subject=sbjct)
#                         except Topic.DoesNotExist:
#                             wet = sbjct.weight
#                         else:
#                             try:
#                                 sbtp = SubTopic.objects.get(name=str(dsubtop), topic=tpc)
#                                 wet = sbtp.weight
#                             except SubTopic.DoesNotExist:
#                                 wet = tpc.weight
                                
#                         if ii.is_right():
#                             subj.score = Decimal(subj.score) + Decimal(wet)
#                             subj.save()
                            
#                         else:
#                             subj.score = Decimal(subj.score)
#                             subj.save()
#                     except Exception:
#                         pass

#                 #record scores against user
#                 total = 0
#                 scripts_total = 0
#                 for sub in CenterSubjectScore.objects.filter(user=str(instance.user.regnum)):
#                     total = total + sub.score
#                     grade = Decimal(sub.remarking())
#                     scripts_total = scripts_total + grade
#                 instance.total = total
#                 if scripts_total == total:
#                     instance.marked = True
#                 else:
#                     instance.total = 0
#                     instance.marked = False
#                     oldscore = CenterSubjectScore.objects.filter(user=str(instance.user.regnum))
#                     for j in oldscore:
#                         j.score = 0
#                         j.save()

# pre_save.connect(markscript_receiver, sender=CenterResult)




class CenterSubjectScore(models.Model):
    subject = models.CharField(max_length=50, blank=False, null=False)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    user = models.CharField(max_length=15)

    def __str__(self):
        return self.subject


    def remarking(self):
        user = Candidate.objects.get(regnum=self.user)
        exam = user.examination
        subjt = Subject.objects.get(name=self.subject, examination=exam)
        scripts_total = 0
        scripts = CenterUserScript.objects.filter(user=user, question__subject=subjt.name)
        for k in scripts:
            if k.is_right():
                scripts_total = Decimal(scripts_total) + Decimal(k.weighting())
        return scripts_total


    def attempted(self):
        user = Candidate.objects.get(regnum=self.user)
        exam = user.examination
        subjt = Subject.objects.get(name=self.subject, examination=exam)
        attempts = 0
        scripts = CenterUserScript.objects.filter(user=user, question__subject=subjt.name)
        for k in scripts:
            if k.choice:
                attempts = attempts + 1
        return attempts



class CenterSendResult(models.Model):
    user = models.CharField(max_length=15)
    result = models.ForeignKey(CenterResult, on_delete=models.CASCADE)
    timesent = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user



class CenterUserScript(models.Model):
    user=models.ForeignKey(Candidate, on_delete=models.CASCADE)
    question=models.ForeignKey(Question, on_delete=models.CASCADE, related_name='centeruserquestion')
    choice = models.CharField(max_length=1)

    def __str__(self):
        return str(self.user)

    def realans(self):
        return str(self.question.ans)

    def dchoice(self):
        if self.choice == 'a':
            return self.question.a
        elif self.choice == 'b':
            return self.question.b
        elif self.choice == 'c':
            return self.question.c
        elif self.choice == 'd':
            return self.question.d
        elif self.choice == 'e':
            return self.question.e

    def danswer(self):
        if self.question.ans == 'a':
            return self.question.a
        elif self.question.ans == 'b':
            return self.question.b
        elif self.question.ans == 'c':
            return self.question.c
        elif self.question.ans == 'd':
            return self.question.d
        elif self.question.ans == 'e':
            return self.question.e

    def dsubject(self):
        return str(self.question.subject)

    def dtopic(self):
        if self.question.topic:
            return str(self.question.topic)
        else:
            return '-'

    def weighting(self):
        exam = Examination.objects.get(name=str(self.question.examination))
        subject = Subject.objects.get(name=str(self.question.subject), examination=exam)
        try:
            tpc = Topic.objects.get(name=str(self.question.topic), subject=subject)
            try:
                sbtp = SubTopic.objects.get(name=str(self.question.topic), topic=tpc)
                return str(sbtp.weight)
            except SubTopic.DoesNotExist:
                return str(tpc.weight)
        except Topic.DoesNotExist:
            return str(subject.weight)
            
    # def subject1_total(self):
    #     subject1 = user.subject.all()[0]
    #     all_script = 



    def is_right(self):
        if str(self.question.ans).lower() == str(self.choice).lower():
            return True


#remark script
# subj, new = CenterSubjectScore.objects.get_or_create(user=str(person.user.regnum), subject=str(p.subject)) 
#             dtpc = p.topic  
#             dsub = p.subject
#             dsubtop = p.subtopic
#             sbjct = Subject.objects.get(name=dsub, examination=exam)
#             try:
#                 tpc = Topic.objects.get(name=str(dtpc), subject=sbjct)
#             except Topic.DoesNotExist:
#                 wet = sbjct.weight
#             else:
#                 try:
#                     sbtp = SubTopic.objects.get(name=str(dsubtop), topic=tpc)
#                     wet = sbtp.weight
#                 except SubTopic.DoesNotExist:
#                     wet = tpc.weight
                    
#             if is_correct:
#                 subj.score = Decimal(subj.score) + Decimal(wet)
#                 subj.save()
                
#             else:
#                 subj.score = Decimal(subj.score)
#                 subj.save()
# #record scores against user
# person.marked = True
# total = 0
# for sub in CenterSubjectScore.objects.filter(user=str(person.user.regnum)):
#     total += sub.score
# person.total = total
# person.save()




# class ExamGrading(models.Model):
# 	name = models.CharField(max_length=15)
# 	grade_floor = models.DecimalField(max_digits=5, decimal_places=2, help_text="lower score")
# 	grade_ceiling = models.DecimalField(max_digits=5, decimal_places=2, help_text="higher score")
# 	comment = models.CharField(max_length=150)
# 	message = RichTextUploadingField(blank=True, null=True)

# 	def __str__(self):
# 		return self.name


# class ExamResult(models.Model):
# 	user = models.ForeignKey(Candidate)
# 	exam_level = models.ForeignKey(StudentLevel)
# 	time_stamp = models.DateTimeField(auto_now_add=True)
# 	time_started = models.DateTimeField(blank=True, null=True)
# 	time_ended = models.DateTimeField(blank=True, null=True)
# 	user_score = models.DecimalField(default=0.00, max_digits=5, decimal_places=2)
# 	done = models.BooleanField(default=False)
# 	grade = models.ForeignKey(ExamGrading, blank=True, null=True)

# 	def result_score(self):
# 		scripts_total = 0
# 		for i in self.examscore_set.all():
# 			scripts = ExamScript.objects.filter(user=self.user, subject=i)
# 			for k in scripts:
# 				if k.is_right:
# 					scripts_total = scripts_total + Decimal(1)
# 		try:
# 			grade = ExamGrading.objects.filter(grade_floor__lte=scripts_total, grade_ceiling__gte=scripts_total)[0]
# 			self.grade = grade
# 		except:
# 			pass
# 		self.user_score = Decimal(scripts_total)
# 		self.save()
# 		return scripts_total

# 	def total_result_score(self):
# 		scripts_total = 0
# 		for i in self.examscore_set.all():
# 			scripts = ExamScript.objects.filter(user=self.user, subject=i)
# 			for k in scripts:
# 				scripts_total = scripts_total + Decimal(1)
# 		result_score = 0
# 		for i in self.examscore_set.all():
# 			scripts = ExamScript.objects.filter(user=self.user, subject=i)
# 			for k in scripts:
# 				if k.is_right:
# 					result_score = result_score + Decimal(1)
# 		try:
# 			grade = ExamGrading.objects.filter(grade_floor__lte=scripts_total, grade_ceiling__gte=scripts_total)[0]
# 			self.grade = grade
# 		except:
# 			pass
# 		self.user_score = Decimal(int(result_score))
# 		self.save()
# 		return Decimal(scripts_total)

# 	def user_guardian_phone(self):
# 		return self.user.guardian_mobile_number

# 	def __str__(self):
# 		return str(self.user)


# # class ExamScore(models.Model):
# # 	user
# # 	subject
# # 	time_stamp
# # 	score
# # 	result = models.ForeignKey(ExamResult)


# class ExamScore(models.Model):
# 	result = models.ForeignKey(ExamResult)
# 	subject = models.ForeignKey(ExamSubject)
# 	score = models.DecimalField(default=0.00, max_digits=5, decimal_places=2)
# 	time_started = models.DateTimeField(auto_now_add=True)
# 	time_ended = models.DateTimeField(blank=True, null=True)
# 	time_used = models.PositiveIntegerField(default=0)
# 	done = models.BooleanField(default=False)
# 	marked = models.BooleanField(default=False)

# 	@property
# 	def time_spent(self):
# 		return time_ended - time_started

# 	# def subject(self):
# 	# 	return str(self.examination.subject.name)

# 	def remarking(self):
# 		scripts_total = 0
# 		scripts = ExamScript.objects.filter(user=self.result.user, subject=self)
# 		for k in scripts:
# 			if k.is_right:
# 				scripts_total = scripts_total + Decimal(1)
# 		return scripts_total

# 	def __str__(self):
# 		return str(self.result.user)

# 	def total_score(self):
# 		scripts_total = 0
# 		scripts = ExamScript.objects.filter(user=self.result.user, subject=self)
# 		for k in scripts:
# 			scripts_total = scripts_total + Decimal(1)
# 		return Decimal(scripts_total)


# def markscript(sender, instance, *args, **kwargs):
# 	# allscores = Score.objects.filter(user=self.user, examination__term=self.term, 
# 	# 		examination__exam_type=self.exam_type).order_by('time_started')
# 	# 	for score in allscores:
# 	score = instance
# 	exam = score.subject
# 	if score.time_started:
# 		timespent = timezone.localtime(timezone.now()) - score.time_started
# 	else:
# 		timespent = timedelta(minutes= 0)
# 	time_duration = timedelta(minutes= int(exam.duration))
# 	if score.done or timespent > time_duration:
# 		if not score.marked:
# 			score.score = 0
# 			scripts = ExamScript.objects.filter(user=score.result.user, subject=score)
# 			for ii in scripts:
# 				wet = 1
# 				if ii.is_right:
# 					score.score = Decimal(score.score) + Decimal(wet)
# 				else:
# 					score.score = Decimal(score.score)
# 			if score.remarking() == score.score:
# 				score.marked = True
# 			else:
# 				score.marked = False

# pre_save.connect(markscript, sender=ExamScore)




# class ExamScript(models.Model):
# 	user = models.ForeignKey(Candidate)
# 	subject = models.ForeignKey(ExamScore)
# 	question = models.ForeignKey(ExamQuestion)
# 	choice = models.CharField(max_length=1)

# 	def __str__(self):
# 		return str(self.user)

# 	def answer(self):
# 		return str(self.question.ans)

# 	def ques_subject(self):
# 		return str(self.question.subject)

# 	@property
# 	def is_right(self):
# 		if str(self.question.ans).lower() == str(self.choice).lower():
# 			return True
# 		else:
# 			return False

# 	def dchoice(self):
# 	    if self.choice.lower() == 'a':
# 	        return self.question.a
# 	    elif self.choice.lower() == 'b':
# 	        return self.question.b
# 	    elif self.choice.lower() == 'c':
# 	        return self.question.c
# 	    elif self.choice.lower() == 'd':
# 	        return self.question.d
# 	    elif self.choice.lower() == 'e':
# 	        return self.question.e

# 	def danswer(self):
# 	    if self.question.ans.lower() == 'a':
# 	        return self.question.a
# 	    elif self.question.ans.lower() == 'b':
# 	        return self.question.b
# 	    elif self.question.ans.lower() == 'c':
# 	        return self.question.c
# 	    elif self.question.ans.lower() == 'd':
# 	        return self.question.d
# 	    elif self.question.ans.lower() == 'e':
# 	        return self.question.e


class CenterUserBank(models.Model):
    center = models.ForeignKey(ExamCenter, on_delete=models.CASCADE)
    user_file = models.FileField()
    file_name = models.CharField(max_length=200, unique=True)

    