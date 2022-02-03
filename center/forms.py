from django import forms
from .models import Candidate, CenterUserBank
from userprofile.models import State, ExamCenter
from bank.models import Examination, Subject, Question
from mngr.models import Advert


class CodesForm(forms.Form):
    number = forms.CharField(label='Number')
    password = forms.CharField(label='', widget=forms.PasswordInput)
    

    class Meta:
        fields = ['number', 'password']



SEX = (
        ('Sex', 'Sex'),
        ('F', 'female'),
        ('M', 'male'),
    )

class SignUpForm(forms.ModelForm):
    full_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder':'Full Name', 'class':'input'}))
    phone = forms.CharField(
    	max_length=13, widget=forms.TextInput(attrs={'placeholder':'Enter Active Phone Number To Get Result', 'class':'input'}))
    sex = forms.ChoiceField(choices=SEX, widget=forms.Select(attrs={'class':'input'})) 
    exam_center = forms.ModelChoiceField(
        queryset = ExamCenter.objects.filter(active=True),
        widget = forms.Select(attrs={'class':'input'}),
        empty_label = "Select Examination Center",
        required=True
        )
    examination = forms.ModelChoiceField(
        queryset = Examination.objects.filter(active=True),
        widget = forms.Select(attrs={'class':'input'}),
        empty_label = "Select Examination Type",
        required=True
        )
    subject = forms.ModelMultipleChoiceField(
        queryset = Subject.objects.all(),
        widget = forms.SelectMultiple(attrs={'class':'input'}),
        required=True
        )
    # feedback = forms.ModelChoiceField(
    #     queryset = Advert.objects.all(),
    #     widget = forms.Select(attrs={'class':'input'}),
    #     empty_label = "How Did You Hear About Us",
    #     required=False
    #     )
    class Meta:
        model = Candidate
        fields = ('full_name', 'sex', 'phone', 'exam_center', 'examination', 'subject')
        
    
    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone:
            try:
                int(phone) + 1
            except Exception:
                raise forms.ValidationError("Invalid Phone Number")
        return phone

    def clean(self):
        cleaned_data = super(SignUpForm, self).clean()
        exam = cleaned_data.get("examination")
        subject = cleaned_data.get("subject")
        if exam and subject:
            units = len(subject)
            if units > exam.subjects:
                raise forms.ValidationError(
                    "Too Many Subjects Selected"
                )
            compsry = Subject.objects.filter(examination=exam, compulsory=True)
            if len(compsry) == units:
                raise forms.ValidationError(
                    "Please Select Subjects"
                )

        

class SalesForm(forms.Form):
    start = forms.CharField(label='Start Serial')
    finish = forms.CharField(label='End Serial')
    buyer = forms.CharField(label='Buyer', required=True)
    set_name = forms.CharField(label='Name This Set Of Codes', required=True)
    password = forms.CharField(label='', widget=forms.PasswordInput)


    def clean_start(self):
        # Check that card is valid
        start = self.cleaned_data.get("start")
        if start:
            if len(start) < 7:
                raise forms.ValidationError("Invalid Card Number")
        return start

    def clean_finish(self):
        # Check that card is valid
        finish = self.cleaned_data.get("finish")
        if finish:
            if len(finish) < 7:
                raise forms.ValidationError("Invalid Card Number")
        return finish


class DeactivateForm(forms.Form):
    regnum = forms.CharField(label='Reg Number', required=False)
    buyer = forms.CharField(label='Issued To', required=False)
    set_name = forms.CharField(label='Set Name', required=False)

    def clean(self):
        cleaned_data = super(DeactivateForm, self).clean()
        buyer = cleaned_data.get("buyer")
        set_name = cleaned_data.get("set_name")
        if buyer:
            if not set_name:
                raise forms.ValidationError(
                    "Please Enter Set Name"
                )
        if set_name:
            if not buyer:
                raise forms.ValidationError(
                    "Please Enter Issued To"
                )


class UserImportForm(forms.ModelForm):
    class Meta:
        model = CenterUserBank
        fields = ['user_file', 'file_name', 'center']


class UserDataForm(forms.Form):
    file_name = forms.CharField()
    candidate = forms.FileField()
    result = forms.FileField()
    scores = forms.FileField()
    # files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    # class Meta:
    #     model = CenterUserBank
    #     fields = ['user_file', 'file_name', 'center']
