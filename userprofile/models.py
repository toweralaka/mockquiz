# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
#to redirect upon successful submit
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta, datetime
from bank.models import Examination, Subject, Question, Topic, SubTopic
from mngr.models import AccessCode, Advert
# Create your models here.


#define active for state
class StateManager(models.Manager):
    def get_queryset(self):
        return super(StateManager, self).get_queryset().filter(active=True)


class State(models.Model):
    name = models.CharField(max_length=30, blank=False, null=False)
    active = models.BooleanField(default=True)

    objects = models.Manager()
    actv = StateManager() #active state manager

    def __str__(self):
        return self.name


#define active for area
class ExamAreaManager(models.Manager):
    def get_queryset(self):
        return super(ExamAreaManager, self).get_queryset().filter(active=True)


class ExamArea(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    exam_period = models.DateField(blank=False, null=True)
    candidates = models.IntegerField(default=0)
    auto_batch = models.BooleanField(default=True)
    active = models.BooleanField(default=True)


    objects = models.Manager()
    actv = ExamAreaManager() #active area manager

    @property
    def qty(self):
        listed = UserProfile.objects.filter(exam_area=self.id)
        count = len(listed)
        return count


    def __str__(self):
        if self.exam_period:
            return "%s, %s %s" %(self.name, self.exam_period.strftime('%b'), self.exam_period.year)
        else:
            return "%s, %s" %(self.name, self.exam_period)




# First, define the Manager subclass.
class ExamCenterManager(models.Manager):
    def get_queryset(self):
        return super(ExamCenterManager, self).get_queryset().filter(active=True)


class ExamCenter(models.Model):
    exam_area = models.ForeignKey(ExamArea, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    exam_period = models.DateField(blank=False, null=True)
    candidates = models.IntegerField(default=0)
    address = models.CharField(max_length=1000, null=True, blank=True)
    active = models.BooleanField(default=True)
    show_photocard = models.BooleanField(default=True)
    check_when = models.DateField(blank=True, null=True)
    #restrict center to a client
    cordon = models.BooleanField(default=False)

    objects = models.Manager()
    actv = ExamCenterManager() #active center specific manager

    @property
    def qty(self):
        listed = UserProfile.objects.filter(exam_center=self.id)
        count = len(listed)
        return count


    def __str__(self):
        if self.exam_period:
            return "%s - %s., %s" %(self.name, self.exam_period.strftime('%b'), self.exam_period.year)
        else:
            return "%s, %s" %(self.name, self.exam_period)



# First, define the Manager subclass.
class BatchManager(models.Manager):
    def get_queryset(self):
        return super(BatchManager, self).get_queryset().filter(active=True)


class Batch(models.Model):
    exam_center = models.ForeignKey(ExamCenter, on_delete=models.CASCADE)
    exam_period = models.DateField(blank=False, null=True)
    capacity = models.IntegerField(default=0)
    filled = models.IntegerField(default=0)
    number = models.CharField(max_length=2)
    date = models.DateField('exam date')
    time = models.TimeField('exam time')
    active = models.BooleanField(default=True)
    write_exam = models.BooleanField(default=False)
    show_result = models.BooleanField(default=False)


    objects = models.Manager()
    actv = BatchManager() #active batch specific manager

    @property
    def qty(self):
        listed = UserProfile.objects.filter(batch=self.id)
        count = len(listed)
        return count


    def __str__(self):
        return "%s(%s)" %(self.number, self.exam_center)

def get_user_scripts_receiver(sender, instance, *args, **kwargs):
    if instance.write_exam:
        for user in UserProfile.objects.filter(batch=instance):
            if user.taken_test() == "False":
                totques = 0
                for s in user.subject.all():
                    totques += s.to_do
                userques = UserScript.objects.filter(user = user)
                if userques.count() != totques:
                    #clear the userscripts
                    for i in userques:
                        i.delete()
                    user.user_scripts()
post_save.connect(get_user_scripts_receiver, sender=Batch)


class UserProfile(models.Model):
    SEX = (
        ('F', 'female'),
        ('M', 'male'),
        ('-', '-'),
    )
    PAYMENT = (
        ('online', 'online'),
        ('card', 'card'),
        ('bank', 'bank'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pin = models.CharField(max_length=10, blank=False, null=False)
    serial = models.CharField(max_length=10, blank=False, null=False)
    first_name = models.CharField(max_length=100, blank=False, null=False)
    surname = models.CharField(max_length=100, blank=False, null=False)
    sex = models.CharField(max_length=1, choices=SEX) 
    phone = models.CharField(max_length=13)
    #not null causes integrity error; so, null=True
    examination = models.ForeignKey(Examination, on_delete=models.SET_NULL, blank=False, null=True)
    course = models.CharField(max_length=100)
    exam_state = models.ForeignKey(State, on_delete=models.SET_NULL, blank=False, null=True)
    exam_area = models.ForeignKey(ExamArea, on_delete=models.SET_NULL, blank=False, null=True)
    subject = models.ManyToManyField(Subject)
    passport = models.ImageField(upload_to='passport/%Y/%m', help_text=("Maximum of 250kb.(50x50px)"))
    regnum = models.CharField(max_length=10, blank=True, null=True)
    pc = models.BooleanField(default=False)
    exam_center = models.ForeignKey(ExamCenter, on_delete=models.SET_NULL, blank=True, null=True)
    feedback = models.ForeignKey(Advert, on_delete=models.SET_NULL, blank=False, null=True, help_text=("How did you hear about this mock?"))
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, blank=True, null=True)
    seat = models.IntegerField(null=True, blank=True)
    online = models.BooleanField(default=False)
    regdate = models.DateTimeField(auto_now_add=True)
    give_sample = models.BooleanField(default=False)
    giftpin = models.CharField(max_length=10, default='', null=True, blank=True) 
    giftserial = models.CharField(max_length=10, default='', null=True, blank=True)
    payment_mode = models.CharField(max_length=8, choices=PAYMENT, default='card') 
    paid = models.BooleanField(default=False)
    referral_code = models.CharField(max_length=5, blank=True, null=True)
    mails = models.BooleanField(default=True, blank=False, verbose_name="Receive Emails?")


    def subss(self):
        sjt = []
        for i in self.subject.all():
            a = str(i.name)[0:4]
            sjt.append(a)
        return sjt

    def image_tag(self):
        return mark_safe('<img src="/media/%s" width="80" height="80" />' % (self.passport))

    image_tag.short_description = 'Image'
    
    def buyer(self):
        cd = AccessCode.objects.get(srn=self.serial, pin=self.pin)
        return cd.buyer

    def get_absolute_url(self):
        return reverse('userprofile:profile')#, kwargs={'pk': self.pk})

    def user_scripts(self):
        questions = []
        exam = self.examination
        subjects = self.subject.all()
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
                                que_set = Question.objects.filter(
                                    examination=str(exam), subject=str(subject.name), topic=str(tp), subtopic=str(i)).order_by('?')[:(int(i.to_do))]
                                bulk_script = []
                                for ques in que_set:
                                    new_script = UserScript()
                                    new_script.question = ques
                                    new_script.user = self
                                    bulk_script.append(new_script)
                                    selected_choice = '-'
                                    payload = {'question':ques, 'selected_choice':selected_choice}
                                    questions.append(payload)
                                UserScript.objects.bulk_create(bulk_script)
                                subtpunit += 1
                            else:
                                break
                    else:
                        que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name), topic=str(tp)).order_by('?')[:(int(tp.to_do))]
                        bulk_script = []
                        for ques in que_set:
                            new_script = UserScript()
                            new_script.question = ques
                            new_script.user = self
                            bulk_script.append(new_script)
                            selected_choice = '-'
                            payload = {'question':ques, 'selected_choice':selected_choice}
                            questions.append(payload)
                        UserScript.objects.bulk_create(bulk_script)
                            
            else:
                que_set = Question.objects.filter(examination=str(exam), subject=str(subject.name)).order_by('?')[:(int(subject.to_do))]
                bulk_script = []
                for ques in que_set:
                    new_script = UserScript()
                    new_script.question = ques
                    new_script.user = self
                    bulk_script.append(new_script)
                    selected_choice = '-'
                    payload = {'question':ques, 'selected_choice':selected_choice}
                    questions.append(payload)
                UserScript.objects.bulk_create(bulk_script)
    
        return questions

    def taken_test(self):
        try:
            taken = Result.objects.get(user__regnum=self.regnum)
            if taken.done:
                return "True"
            else:
                return "Started"
        except Result.DoesNotExist:
            return "False"

    def get_user_scripts(self):
        if self.taken_test() == "False":
            totques = 0
            for s in self.subject.all():
                totques += s.to_do
            userques = UserScript.objects.filter(user = self)
            if userques.count() != totques:
                #clear the userscripts
                for i in userques:
                    i.delete()
                questions = self.user_scripts()
            else:
                questions = [{'question':q.question, 'selected_choice':q.choice} for q in userques]
        else:
            questions = [
            {'question':q.question, 'selected_choice':q.choice} for q in UserScript.objects.filter(
                user = self)]
        return questions

    def result_score(self):
        if self.taken_test() == "True":
            taken = Result.objects.get(user__regnum=self.regnum)
            return taken.total
        else:
            return "Not Taken"

    def __str__(self):
        return self.user.username

# from django.db.models.signals import post_save
# from django.dispatch import receiver

# @receiver(post_save, sender=User)
# def create_profile(sender, instance, created, **kwargs):
#     if created:
#         profile, new = UserProfile.objects.get_or_create(user=instance)



class Result(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    exam_area = models.ForeignKey(ExamArea, on_delete=models.PROTECT)
    exam_center = models.ForeignKey(ExamCenter, on_delete=models.PROTECT)
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT)
    timestamp = models.DateTimeField()
    started = models.BooleanField(default = True)
    time_ended = models.DateTimeField(blank=True, null=True)
    done = models.BooleanField(default = False)
    marked = models.BooleanField(default = False)
    total = models.DecimalField(max_digits=5, decimal_places=0, default=0)
    duration = models.IntegerField(default = 0)
    timelog = models.DateTimeField(auto_now_add=True)
    scripts = models.TextField(blank=True, null=True)



    def usernm(self):
        return self.user.surname+' ('+self.user.first_name+')'


    @property
    def timespent(self):
        if self.time_ended:
            return self.time_ended - self.timestamp
        else:
            return None

    def card(self):
        sn = AccessCode.objects.get(srn=self.user.serial, pin=self.user.pin)
        return sn.buyer

    @property
    def scores(self):
        s=[]
        ss = SubjectScore.objects.filter(user=str(self.user.regnum))
        if ss.exists() == True:
            for i in ss:
                dscore = str(i.subject) + ' = ' + str(int(i.score)) #+ ' [attempted('+ str(i.attempted()) +' questions)]'
                s.append(dscore)
        return s

    @property
    def scores_attempted(self):
        s=[]
        ss = SubjectScore.objects.filter(user=str(self.user.regnum))
        if ss.exists() == True:
            for i in ss:
                dscore = str(i.subject) + ' = ' + str(int(i.score)) + ' [attempted('+ str(i.attempted()) +' questions)]'
                s.append(str(dscore))
        return s

    @property
    def totals(self):
        ss = SubjectScore.objects.filter(user=str(self.user.regnum))
        t=0
        if ss.exists() == True:
            for s in ss:
                t += int(s.score)
        return t

    # def force_markscript(self):
    #     instance = self
    #     exam = instance.user.examination
    #     time_duration = timedelta(minutes= int(exam.duration))
    #     time_to_end = instance.timelog + time_duration
    #     if timezone.localtime(timezone.now()) >= time_to_end:
    #         # if instance.force_markscript != True and instance.timelog >= timezone.make_aware(datetime.strptime("2021-05-01", "%Y-%m-%d"), timezone.get_default_timezone()) and instance.timelog <= timezone.make_aware(datetime.strptime("2021-06-01", "%Y-%m-%d"), timezone.get_default_timezone()):
    #         if not instance.marked:
    #         # if instance.timelog >= timezone.make_aware(datetime.strptime("2021-05-01", "%Y-%m-%d"), timezone.get_default_timezone()) and instance.timelog <= timezone.make_aware(datetime.strptime("2021-06-01", "%Y-%m-%d"), timezone.get_default_timezone()):
    #             oldscore = SubjectScore.objects.filter(user=str(instance.user.regnum))
    #             for j in oldscore:
    #                 j.delete()
    #             exam = instance.user.examination
    #             scripts = UserScript.objects.filter(user=instance.user)
    #             for ii in scripts:
    #                 i = ii.question.id
    #                 p = Question.objects.get(id=i)
    #                 try:
    #                     subj, new = SubjectScore.objects.get_or_create(user=str(instance.user.regnum), subject=str(p.subject)) 
    #                     dtpc = p.topic  
    #                     dsub = p.subject
    #                     dsubtop = p.subtopic
    #                     sbjct = Subject.objects.get(name=dsub, examination=exam)
    #                     try:
    #                         tpc = Topic.objects.get(name=str(dtpc), subject=sbjct)
    #                     except Topic.DoesNotExist:
    #                         wet = sbjct.weight
    #                     else:
    #                         try:
    #                             sbtp = SubTopic.objects.get(name=str(dsubtop), topic=tpc)
    #                             wet = sbtp.weight
    #                         except SubTopic.DoesNotExist:
    #                             wet = tpc.weight
                                
    #                     if ii.is_right():
    #                         subj.score = Decimal(subj.score) + Decimal(wet)
    #                         subj.save()
                            
    #                     else:
    #                         subj.score = Decimal(subj.score)
    #                         subj.save()
    #                 except Exception as e:
    #                     print(e)
    #                     pass

    #             #record scores against user
    #             total = 0
    #             scripts_total = 0
    #             for sub in SubjectScore.objects.filter(user=str(instance.user.regnum)):
    #                 total = total + sub.score
    #                 grade = Decimal(sub.remarking())
    #                 scripts_total = scripts_total + grade
    #             instance.total = total
    #             if scripts_total == instance.total:
    #                 instance.marked = True
    #                 instance.save()
    #                 return True
    #             else:
    #                 instance.total = 0
    #                 instance.marked = False
    #                 instance.save()
    #                 oldscore = SubjectScore.objects.filter(user=str(instance.user.regnum))
    #                 for j in oldscore:
    #                     j.score = 0
    #                     j.save()
    #                 return False

    def markscript(self):
        instance = self
        if instance.timestamp:
            exam = instance.user.examination
            timespent = timezone.localtime(timezone.now()) - instance.timestamp
            time_duration = timedelta(minutes= int(exam.duration))
            if instance.done or timespent > time_duration:
                if not instance.marked:
                    oldscore = SubjectScore.objects.filter(user=str(instance.user.regnum))
                    for j in oldscore:
                        j.delete()
                    exam = instance.user.examination
                    scripts = UserScript.objects.filter(user=instance.user)
                    for ii in scripts:
                        i = ii.question.id
                        p = Question.objects.get(id=i)
                        try:
                            subj, new = SubjectScore.objects.get_or_create(user=str(instance.user.regnum), subject=str(p.subject)) 
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
                    for sub in SubjectScore.objects.filter(user=str(instance.user.regnum)):
                        total = total + sub.score
                        grade = Decimal(sub.remarking())
                        scripts_total = scripts_total + grade
                    instance.total = total
                    if scripts_total == instance.total:
                        instance.marked = True
                        # return True
                    else:
                        instance.total = 0
                        instance.marked = False
                        oldscore = SubjectScore.objects.filter(user=str(instance.user.regnum))
                        for j in oldscore:
                            j.score = 0
                            j.save()
        instance.save()


    def __str__(self):
        return self.user.first_name

# def markscript_receiver(sender, instance, *args, **kwargs):
#     if instance.timestamp:
#         exam = instance.user.examination
#         timespent = timezone.localtime(timezone.now()) - instance.timestamp
#         time_duration = timedelta(minutes= int(exam.duration))
#         if instance.done or timespent > time_duration:
#             if not instance.marked:
#                 oldscore = SubjectScore.objects.filter(user=str(instance.user.regnum))
#                 for j in oldscore:
#                     j.delete()
#                 exam = instance.user.examination
#                 scripts = UserScript.objects.filter(user=instance.user)
#                 for ii in scripts:
#                     i = ii.question.id
#                     p = Question.objects.get(id=i)
#                     try:
#                         subj, new = SubjectScore.objects.get_or_create(user=str(instance.user.regnum), subject=str(p.subject)) 
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
#                 for sub in SubjectScore.objects.filter(user=str(instance.user.regnum)):
#                     total = total + sub.score
#                     grade = Decimal(sub.remarking())
#                     scripts_total = scripts_total + grade
#                 instance.total = total
#                 if scripts_total == instance.total:
#                     instance.marked = True
#                     return True
#                 else:
#                     instance.total = 0
#                     instance.marked = False
#                     oldscore = SubjectScore.objects.filter(user=str(instance.user.regnum))
#                     for j in oldscore:
#                         j.score = 0
#                         j.save()

# pre_save.connect(markscript_receiver, sender=Result)

    



class SubjectScore(models.Model):
    subject = models.CharField(max_length=50, blank=False, null=False)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    user = models.CharField(max_length=15)

    def __str__(self):
        return self.subject


    def remarking(self):
        user = UserProfile.objects.get(regnum=self.user)
        exam = user.examination
        subjt = Subject.objects.get(name=self.subject, examination=exam)
        # self.score = 0
        # self.save()
        scripts_total = 0
        scripts = UserScript.objects.filter(user=user, question__subject=subjt.name)
        for k in scripts:
            if k.is_right():
                grade = Decimal(k.weighting())
                scripts_total = scripts_total + grade
        return scripts_total

    def num_right(self):
        user = UserProfile.objects.get(regnum=self.user)
        count = 0
        for i in UserScript.objects.filter(user=user, question__subject=self.subject):
            if i.is_right():
                count += 1
        return count

    def attempted(self):
        user = UserProfile.objects.get(regnum=self.user)
        exam = user.examination
        subjt = Subject.objects.get(name=self.subject, examination=exam)
        attempts = 0
        scripts = UserScript.objects.filter(user=user, question__subject=subjt.name)
        for k in scripts:
            if k.choice:
                attempts = attempts + 1
        return attempts

# class ExamSession(models.Model):
#     user=models.ForeignKey(UserProfile)
#     question=models.CharField(max_length=10)

#     def __str__(self):
#         return str(self.user)



class SendResult(models.Model):
    user = models.CharField(max_length=15)
    result = models.ForeignKey(Result, on_delete=models.CASCADE)
    timesent = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user



class SpecialCase(models.Model):
    regnumber = models.CharField(max_length=10, default='-')
    issue = models.CharField(max_length=15)
    message = models.TextField()
    noresult = models.BooleanField(default=False)

    class Meta:
        unique_together = ('regnumber', 'issue')

    def __str__(self):
        return self.regnumber


# First, define the Manager subclass.
class WriteAccessManager(models.Manager):
    def get_queryset(self):
        return super(WriteAccessManager, self).get_queryset().filter(active=True)


class WriteAccess(models.Model):
    name = models.CharField(max_length=50)
    exam_center = models.ForeignKey(ExamCenter, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    password = models.CharField(max_length=50)
    time = models.DateTimeField()
    active = models.BooleanField(default=True)

    objects = models.Manager()
    actv = WriteAccessManager() #active write_access manager

    def __str__(self):
        return self.name


class UserScript(models.Model):
    user=models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    question=models.ForeignKey(Question, on_delete=models.CASCADE, related_name='userquestion')
    choice = models.CharField(max_length=1, blank=True, null=True)

    def __str__(self):
        return str(self.user)

    @property
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

    @property
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
# subj, new = SubjectScore.objects.get_or_create(user=str(person.user.regnum), subject=str(p.subject)) 
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
# for sub in SubjectScore.objects.filter(user=str(person.user.regnum)):
#     total += sub.score
# person.total = total
# person.save()


class Referrer(models.Model):
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=13, unique=True)
    email= models.EmailField()
    state = models.ForeignKey(State, on_delete=models.SET_NULL, blank=False, null=True)
    ref_code = models.CharField(max_length=5, unique=True)
    regdate = models.DateTimeField(auto_now_add=True)
    account_no = models.CharField(max_length=10, verbose_name="Acount Number", blank=True, null=True)
    bank = models.CharField(max_length=100, verbose_name="Bank", blank=True, null=True)
    account_name = models.CharField(max_length=100, blank=True, null=True)
    referrer_code = models.CharField(max_length=4, null=True, blank=True, verbose_name="Code Of Referrer")

    class Meta:
        unique_together = ('full_name', 'phone_number')

    def __str__(self):
        return self.full_name+"("+self.ref_code+")"





class Referral(models.Model):
    user_activated = models.ForeignKey(UserProfile, on_delete=models.PROTECT)
    referrer = models.ForeignKey(Referrer, on_delete=models.CASCADE)
    active = models.BooleanField(default=False, verbose_name="Candidate Paid?", help_text="has the referred candidate paid?")
    paid = models.BooleanField(default=False, help_text="has the referrer been paid?")
    payment_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.user_activated.regnum



class SupReferral(models.Model):
    sup_referrer = models.ForeignKey(Referrer, on_delete=models.PROTECT)
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE)
    paid = models.BooleanField(default=False, help_text="has the sup_referrer been paid?")
    payment_date = models.DateTimeField(blank=True, null=True)




@receiver(post_save, sender=Referral)
def create_profile(sender, instance, created, **kwargs):
    if created:
        try:
            sup_ref = Referrer.objects.get(ref_code=instance.referrer.referrer_code)
            profile, new = SupReferral.objects.get_or_create(sup_referrer=sup_ref, referral=instance)
        except Referrer.DoesNotExist:
            pass



class BankDirect(models.Model):
    BANK = (
        ('FCMB', 'FCMB'),
        ('ACCESS', 'ACCESS'),
        ('STANBIC', 'STANBIC'),
    )
    PAYMENT = (
        ('bank_walk_in', 'bank_walk_in'),
        ('bank_transfer', 'bank_transfer'),
    )
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    payment_date = models.DateField(help_text='yyyy-mm-dd')
    amount = models.PositiveIntegerField(help_text='In Naira')
    bank = models.CharField(max_length=8, choices=BANK)
    depositor_name = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=50, help_text='Or Teller No.')
    payment_mode = models.CharField(max_length=14, choices=PAYMENT)
    confirmed = models.BooleanField(default=False)

    def __str__(self):
        return str(self.user)

    class Meta:
        unique_together = ('transaction_id', 'bank')


class Testimonial(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    testimonial = models.TextField()


class UserBank(models.Model):
    user_file = models.FileField()
    file_name = models.CharField(max_length=200, unique=True)