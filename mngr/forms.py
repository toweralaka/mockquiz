from django import forms

from .models import InBox

class InBoxForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput)

    class Meta:
        model = InBox
        exclude = ['time_in']



class CodesForm(forms.Form):
    name = forms.CharField(label='Name')
    number = forms.CharField(label='Number')
    buyer = forms.CharField(label='Buyer')
    freebie = forms.BooleanField(label='Grant Freebie?', required=False)
    custom = forms.BooleanField(label='Restrict To Center?', required=False)
    custom_center = forms.CharField(label='Center Name', required=False)
    passcode = forms.CharField(label='Pass Code', required=False)
    password = forms.CharField(label='', widget=forms.PasswordInput)


class CenterForm(forms.Form):
    name = forms.CharField(label='Card Set Name')
    buyer = forms.CharField(label='Buyer')
    center = forms.CharField(label='Center')
    password = forms.CharField(label='', widget=forms.PasswordInput)

# centers = []
# for i in ExamCenter.objects.filter(active=True):
#     if not i in centers:
#         centers.append(i)

    

# class CodesForm(forms.Form):
#     name = forms.CharField(label='Name')
#     number = forms.CharField(label='Number')
#     buyer = forms.CharField(label='Buyer')
#     freebie = forms.BooleanField(label='Grant Freebie?', required=False)
#     custom = forms.BooleanField(label='Restrict To Center?', required=False)
#     custom_center = forms.ChoiceField(
#         choices=[
#         (center.pk, center) for center in centers],
#         widget = forms.Select(attrs={'class':'input'}),
#         label = "Select Examination Center",
#         required=False
#         )
#     passcode = forms.CharField(label='Pass Code', required=False)
#     password = forms.CharField(label='', widget=forms.PasswordInput)


# class CenterForm(forms.Form):
#     name = forms.CharField(label='Card Set Name')
#     buyer = forms.CharField(label='Buyer')
#     center = forms.ChoiceField(
#         choices=[
#         (center.pk, center) for center in centers],
#         widget = forms.Select(attrs={'class':'input'}),
#         label = "Select Examination Center",
#         required=True
#         )
#     password = forms.CharField(label='', widget=forms.PasswordInput)


class SalesForm(forms.Form):
    start = forms.CharField(label='Start Serial')
    finish = forms.CharField(label='End Serial')
    buyer = forms.CharField(label='Buyer', required=False)
    passcode = forms.CharField(label='Pass Code', required=False)
    password = forms.CharField(label='', widget=forms.PasswordInput)


    def clean_start(self):
        # Check that card is valid
        start = self.cleaned_data.get("start")
        if start:
            if len(start) < 8:
                raise forms.ValidationError("Invalid Card Number")
        return start

    def clean_finish(self):
        # Check that card is valid
        finish = self.cleaned_data.get("finish")
        if finish:
            if len(finish) < 8:
                raise forms.ValidationError("Invalid Card Number")
        return finish

class MailForm(forms.Form):
    to = forms.EmailField(label='Send To')
    cc = forms.EmailField(label='Copy')
    subject = forms.CharField(label='Subject of Message')
    body = forms.CharField(label='Message Content', widget=forms.Textarea)
    filename = forms.CharField(label='File To Attach', required=False)


# class ReceiptForm(forms.Form):
#     client = 
#     address = 
#     particulars = 
#     quantity = 
#     amount = 
#     cash = 
#     cheque = 
#     bank = 
#     cheque_no = 

#     def clean_finish(self):
#         # Check that card is valid
#         finish = self.cleaned_data.get("finish")
#         if finish:
#             if len(finish) < 8:
#                 raise forms.ValidationError("Invalid Card Number")
#         return finish