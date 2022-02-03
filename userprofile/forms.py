from django.contrib.auth.models import User
from django import forms

from .models import UserProfile, Batch, ExamCenter, Referrer, BankDirect, State, UserBank
from mngr.models import AccessCode
from bank.models import Subject, Examination
# from centermock.models import MockUserBank


class DateInput(forms.DateInput):
    input_type = 'date'


class UserForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Re-type Password', widget=forms.PasswordInput)
    email = forms.EmailField()
    username = forms.CharField(error_messages = {'unique': 'A user with that Username already exists, '
        'try another'
            })

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'email']


    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The Passwords don't match")
        return password2



class UserProfileForm(forms.ModelForm):
    #INSTITUTE_CHOICES = [('', '-- select an institute --'), ] + [(t.id, t.abbr) for t in Institute.objects.filter(active=True)]
    EXAMINATION_CHOICES =[('', '-- You have not selected an institute --')]
    SUBJECT_CHOICES = [('', '-- You have not selected an examination type --')]

    #institute = forms.ModelChoiceField(queryset=Institute.objects.filter(active=True), widget=forms.Select())
    examination = forms.ModelChoiceField(queryset=Examination.objects.filter(active=True), widget=forms.Select())
    exam_state = forms.ModelChoiceField(queryset=State.objects.filter(active=True), widget=forms.Select())
    pin = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = UserProfile
        fields = ['pin', 'serial', 'examination', 'surname', 'first_name', 'sex',
         'phone', 'course', 'exam_state', 'exam_area', 'exam_center', 'feedback', 'passport', 'mails']

    def clean(self):
        cleaned_data = super(UserProfileForm, self).clean()
        # Check that card is valid
        pin = cleaned_data.get("pin")
        serial = cleaned_data.get("serial")
        exam_area = cleaned_data.get("exam_area")
        if pin and serial:
            if not AccessCode.objects.filter(pin=pin, srn=serial).exists():
                raise forms.ValidationError("Invalid PIN and Serial Number Combination")
            else:
                card = AccessCode.objects.get(pin=pin, srn=serial)
                #Check that card is used
                if card.used == True:
                    raise forms.ValidationError("Your card has already been used")
                else:
                    #Check that card is active
                    if card.active == False:
                        raise forms.ValidationError("This card is not authorised for sale. Please contact your vendor.")
                    else:
                        #Check that card is authorised for sale
                        if card.name == 'Unsold':
                            raise forms.ValidationError("This card is not authorised for sale. Please contact your vendor.")
                        else:
                            ##check that appropriate center is chosen
                            if card.custom:
                                try:
                                    center = ExamCenter.actv.get(name=card.custom_center)
                                except ExamCenter.DoesNotExist:
                                    pass
                                else:
                                    if exam_area != center.exam_area:
                                        raise forms.ValidationError("Invalid exam area for your card. Please contact your vendor for exam area.")
                

    def clean_phone(self):
        # Check that phone number is valid
        phone = self.cleaned_data.get("phone")
        if phone:
            try:
                int(phone) + 1
            except Exception as e:
                raise forms.ValidationError("Invalid Phone Number")
        return phone


    def clean_passport(self):
        # Check that passport is valid
        picture = self.cleaned_data.get("passport",None)
        if not picture:
            raise forms.ValidationError("Couldn't read uploaded image")
        if picture.size > 250*1024:
            raise forms.ValidationError("Image file too large (250kb max)")
        if picture.size < 20*1024:
            raise forms.ValidationError("Image file too small (20kb min)")
        return picture



class RefUserProfileForm(forms.ModelForm):
    EXAMINATION_CHOICES =[('', '-- You have not selected an institute --')]
    SUBJECT_CHOICES = [('', '-- You have not selected an examination type --')]
    exam_state = forms.ModelChoiceField(queryset=State.objects.filter(active=True), widget=forms.Select())
    examination = forms.ModelChoiceField(queryset=Examination.objects.filter(active=True), widget=forms.Select())

    class Meta:
        model = UserProfile
        fields = ['examination', 'surname', 'first_name', 'sex', 'referral_code',
         'phone', 'course', 'exam_state', 'exam_area', 'exam_center', 'feedback', 'passport', 'mails']
    

    def clean_phone(self):
        # Check that phone number is valid
        phone = self.cleaned_data.get("phone")
        if phone:
            try:
                int(phone) + 1
            except Exception as e:
                raise forms.ValidationError("Invalid Phone Number")
        return phone


    def clean_passport(self):
        # Check that passport is valid
        picture = self.cleaned_data.get("passport",None)
        if not picture:
            raise forms.ValidationError("Couldn't read uploaded image")
        if picture.size > 250*1024:
            raise forms.ValidationError("Image file too large (50kb max)")
        if picture.size < 20*1024:
            raise forms.ValidationError("Image file too small (20kb min)")
        return picture




class SubjectForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('subject',)

    def clean(self):
        cleaned_data = super(SubjectForm, self).clean()
        subject = cleaned_data.get("subject")
        if subject:
            s = subject[0]
            exam = s.examination
            count = 0
            for sub in subject:
                count += 1
            if count > exam.subjects:
                raise forms.ValidationError("You can't choose above the required number of subjects")



class UpdateProfileForm(forms.ModelForm):
    examination = forms.ModelChoiceField(queryset=Examination.objects.filter(active=True), widget=forms.Select())

    class Meta:
        model = UserProfile
        fields = ('examination', 'phone', 'passport', 'course')


    def clean_phone(self):
        # Check that phone number is valid
        phone = self.cleaned_data.get("phone")
        if phone:
            try:
                int(phone) + 1
            except Exception as e:
                raise forms.ValidationError("Invalid Phone Number")
        return phone


    def clean_passport(self):
        # Check that passport is valid
        picture = self.cleaned_data.get("passport",None)
        if not picture:
            raise forms.ValidationError("Couldn't read uploaded image")
        if picture.size > 250*1024:
            raise forms.ValidationError("Image file too large (250kb max)")
        if picture.size < 10*1024:
            raise forms.ValidationError("Image file too small (10kb min)")
        return picture


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ('exam_center', 'number')


class WriteForm(forms.Form):
    name = forms.CharField(label='Name')
    password = forms.CharField(label='Pass', widget=forms.PasswordInput)


class StartExamForm(forms.Form):
    CENTER_CHOICES = [('', '-- select exam center --'), ] + [(t.id, 
        "%s, %s" %(t.name, t.exam_period)) for t in ExamCenter.objects.filter(active=True)]
    BATCH_CHOICES = [('', '-- select batch --'), ] + [(t.id, 
        "%s(%s)" %(t.number, t.exam_center)) for t in Batch.objects.filter(active=True).order_by('exam_center__name')] + [('all', 'all batches'), ]
        
    exam_center = forms.ChoiceField(choices=CENTER_CHOICES, widget=forms.Select(attrs={'class':'input'})) 
    batch = forms.ChoiceField(choices=BATCH_CHOICES, widget=forms.Select(attrs={'class':'input'})) 
    password = forms.CharField(label='Pass', widget=forms.PasswordInput)


#     unit_id = request.POST.get('unit_id')

# form.fields['unit_id'].choices = [(unit_id, unit_id)]


class ReferrerForm(forms.ModelForm):
    state = forms.ModelChoiceField(queryset=State.objects.filter(active=True), widget=forms.Select())

    class Meta:
        model = Referrer
        fields = ('full_name', 'phone_number', 'email', 'state', 'referrer_code')

    def clean_phone_number(self):
        # Check that phone number is valid
        phone = self.cleaned_data.get("phone_number")
        if phone:
            try:
                int(phone) + 1
            except Exception as e:
                raise forms.ValidationError("Invalid Phone Number")
        return phone


class SubReferrerForm(forms.ModelForm):
    state = forms.ModelChoiceField(queryset=State.objects.filter(active=True), widget=forms.Select())

    class Meta:
        model = Referrer
        fields = ('full_name', 'phone_number', 'referrer_code', 'email', 'state')

    def clean_phone_number(self):
        # Check that phone number is valid
        phone = self.cleaned_data.get("phone_number")
        if phone:
            try:
                int(phone) + 1
            except Exception as e:
                raise forms.ValidationError("Invalid Phone Number")
        return phone



class BankDirectForm(forms.ModelForm):
    class Meta:
        model = BankDirect
        exclude = ('user', 'confirmed')



class ReBankDirectForm(forms.ModelForm):
    email = forms.EmailField(required=True, help_text='Email you entered during registration')
    #payment_date = fields.DateField(widget=forms.widgets.DateInput(attrs={'type': 'date'}))
    class Meta:
        model = BankDirect
        fields = ('email', 'payment_date','amount', 'bank', 'depositor_name', 'transaction_id', 'payment_mode')


    #check that user exists
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            try:
                person = UserProfile.objects.get(user__username=email)
            except Exception:
                raise forms.ValidationError("You Have Not Registered(Click On Register Above) Or You Did Not Register With This Email. ")
        return email



class ReferralLoginForm(forms.ModelForm):
    class Meta:
        model = Referrer
        fields = ('phone_number',)



class UserImportForm(forms.ModelForm):
    class Meta:
        model = UserBank
        fields = ['user_file', 'file_name']


class ResultImportForm(forms.Form):
    result_file_name = forms.CharField()
    result_file = forms.FileField()
    scores_file_name = forms.CharField()
    scores_file = forms.FileField()
    