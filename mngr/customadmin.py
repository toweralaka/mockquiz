# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from django.contrib.admin import helpers
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth import logout
from django.conf.urls import url

from .models import UsedCard, AccessCode, SiteView, About, Partner, Freebie, FileUploads, Receipt, Invoice
from .views import rannum, ranlet, send_sms, send_email
from .forms import CodesForm, SalesForm, MailForm, CenterForm#, ReceiptForm

import requests



class FileUploadsAdmin(admin.ModelAdmin):
    actions = ['send_attach_mail',]
    

    def get_urls(self):
        urls = super(FileUploadsAdmin, self).get_urls()
        custom_urls = [
            url(
                r'^send_mail/$',
                self.admin_site.admin_view(self.sending_mail),
                name='mngr_fileuploads_sendmail',
            ),
        ]
        return custom_urls + urls


    def sending_mail(self, request):
        context = {
            'title': 'SEND EMAIL',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }
        if request.method == 'POST':
            form = MailForm(request.POST, request.FILES)
            if form.is_valid():
                to = form.cleaned_data['to']
                cc = form.cleaned_data['cc']
                subject = form.cleaned_data['subject']
                body = form.cleaned_data['body']
                filename = form.cleaned_data['filename']
                attachment = FileUploads.objects.get(name=filename)
                attach = attachment.doc
                try:
                    email=EmailMessage(str(subject), str(body), 'DiamanteMineLimited@mockexamsng.org',
                [str(to), str(cc)], ['djaafolayan@gmail.com',])
                    email.attach_file(attach.path)
                    email.send(fail_silently=False)
                except Exception as e:
                    message_bit = "Email not sent. Check Internet and Export Again"
                else:
                    message_bit = "Email Successfully Sent!"
                self.message_user(request, "%s" % message_bit)
            else:
                form = MailForm(request.POST, request.FILES)
                context['form'] = form
                context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                         self.get_prepopulated_fields(request))
                return render(request, 'admin/mngr/fileuploads/sendmail.html', context)

        form = MailForm()
        context['form'] = form
        context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                 self.get_prepopulated_fields(request))
        return render(request, 'admin/mngr/fileuploads/sendmail.html', context)

    def send_attach_mail(self, request, queryset):
        context = {
            'title': 'SEND EMAIL',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }

        form = MailForm()
        context['form'] = form
        context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                 self.get_prepopulated_fields(request))
        return render(request, 'admin/mngr/fileuploads/sendmail.html', context)
    send_attach_mail.short_description = 'Send Email With Attachment'

def activate_selected(modeladmin, request, queryset):
    for card in queryset:
        card.active = True
        card.save()
        message_bit = str(card.srn)+" Successfully Activated!"
        modeladmin.message_user(request, "%s" % message_bit)
                    
activate_selected.short_description = 'Activate Selected'

def deactivate_selected(modeladmin, request, queryset):
    for card in queryset:
        card.active = False
        card.save()
        message_bit = str(card.srn)+" Successfully Deactivated!"
        modeladmin.message_user(request, "%s" % message_bit)
                    
deactivate_selected.short_description = 'Deactivate Selected'

def remove_center(modeladmin, request, queryset):
    for card in queryset:
        card.custom = False
        card.custom_center = ''
        card.save()
        message_bit = str(card.srn)+" Center Successfully Removed!"
        modeladmin.message_user(request, "%s" % message_bit)
                    
remove_center.short_description = 'Deactivate Selected'

class AccessCodeAdmin(admin.ModelAdmin):
    list_display = ('srn', 'pin', 'name', 'buyer', 'active', 'used',)
    search_fields = ('srn', 'name', 'buyer')
    list_filter = ('buyer', 'used', 'active', 'generated')
    actions = ['activate_card', 'deactivate_card', deactivate_selected, activate_selected, remove_center]


    def get_urls(self):
        urls = super(AccessCodeAdmin, self).get_urls()
        custom_urls = [
            url(
                r'^codes/$',
                self.admin_site.admin_view(self.codes),
                name='mngr_accesscode_codes',
            ),
            url(
                r'^sales/$',
                self.admin_site.admin_view(self.sales),
                name='mngr_accesscode_sales',
            ),
            url(
                r'^deactivate/$',
                self.admin_site.admin_view(self.deactivate),
                name='mngr_accesscode_deactivate',
            ),
            url(
                r'^activate/$',
                self.admin_site.admin_view(self.activate),
                name='mngr_accesscode_activate',
            ),
            url(
                r'^setcenter/$',
                self.admin_site.admin_view(self.setcenter),
                name='mngr_accesscode_setcenter',
            ),
            # url(
            #     r'^(?P<account_id>.+)/withdraw/$',
            #     self.admin_site.admin_view(self.process_withdraw),
            #     name='account-withdraw',
            # ),
        ]
        return custom_urls + urls


    def codes(self, request):
        code_list = []
        context = {
            'title': 'GET CODES',
            'code_list' : code_list,
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }
        if request.method == 'POST':
            form = CodesForm(request.POST)
            if form.is_valid():
                number = form.cleaned_data['number']
                name = form.cleaned_data['name']
                buyer = form.cleaned_data['buyer']
                freebie = form.cleaned_data['freebie']
                custom = form.cleaned_data['custom']
                custom_center = form.cleaned_data['custom_center']
                passcode = form.cleaned_data['passcode']
                password = form.cleaned_data['password']
                if str(password) == 'eureka':
                    qty = 0
                    while qty < int(number):
                        pn = rannum(10)
                        #fetch last accesscode
                        accesses = AccessCode.objects.all()
                        counted = len(accesses)
                        if counted == 0:
                            serial = 'MCK10001'
                        else:
                            last = accesses[(counted-1)]
                            #the corresponding serial stripped of letters and incremented
                            lastsrn = str(last.srn)
                            onlynum = lastsrn[3:8]
                            lastnum = int(onlynum)
                            newnum = lastnum + 1
                            #recreate
                            serial = 'MCK' + (str(newnum))

                        newcode = AccessCode(
                        pin = pn,
                        srn = serial,
                        name = name,
                        buyer = buyer,
                        freebie = freebie,
                        custom = custom,
                        custom_center = custom_center,
                        passcode = passcode,
                        active = True,
                        used = False)
                        newcode.save()

                        code_list.append(newcode)
                        qty += 1
                    mesgbody = 'You generated '+ str(qty) + ' access codes for '+ buyer + '.'
                    smesto = '08027721770'
                    try:
                        send_sms(mesgbody, smesto)
                    except Exception:
                        pass
                    form = CodesForm()
                    context['form'] = form
                    context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                             self.get_prepopulated_fields(request))
                    return render(request, 'admin/mngr/accesscode/codes.html', context)
                else:
                    logout(request)
                    return HttpResponseRedirect('/')
            else:
                context['form'] = form
                context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                        self.get_prepopulated_fields(request))
                return render(request, 'admin/mngr/accesscode/codes.html', context)
        else:
            form = CodesForm()
            context['form'] = form
            context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                     self.get_prepopulated_fields(request))
            return render(request, 'admin/mngr/accesscode/codes.html', context)


    def sales(self, request):
        qty = 0
        nil = []
        context = {
            'title': 'SELL CARDS',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }
        if request.method == 'POST':
            form = SalesForm(request.POST)
            if form.is_valid():
                start = form.cleaned_data['start']
                finish = form.cleaned_data['finish']
                buyer = form.cleaned_data['buyer']
                passcode = form.cleaned_data['passcode']
                password = form.cleaned_data['password']
                if str(password) == 'eureka':
                    first = start[3:8]
                    prefix = start[0:3]
                    cardnum = int(first)
                    last = finish[3:8]
                    lastnum = int(last) + 1
                    while cardnum < lastnum:
                        serial = str(prefix) + (str(cardnum))
                        if not AccessCode.objects.filter(srn=serial).exists():
                            cardnum += 1
                            nil.append(serial)
                        else:
                            card = AccessCode.objects.get(srn=serial)
                            card.buyer = buyer
                            card.passcode = passcode
                            card.save()
                            cardnum += 1
                            qty += 1
                    context['buyer'] = buyer
                    context['passcode'] = passcode
                    context['qty'] = qty
                    context['nil'] = nil
                    form = SalesForm()
                    context['form'] = form
                    context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                             self.get_prepopulated_fields(request))
                    return render(request, 'admin/mngr/accesscode/sales.html', context)
                else:
                    logout(request)
                    return HttpResponseRedirect('/')
            else:
                context['form'] = form
                context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                        self.get_prepopulated_fields(request))
                return render(request, 'admin/mngr/accesscode/sales.html', context)
        else:
            form = SalesForm()
            context['form'] = form
            context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                     self.get_prepopulated_fields(request))
            return render(request, 'admin/mngr/accesscode/sales.html', context)

    def setcenter(self, request):
        qty = 0
        context = {
            'title': 'SET CENTER',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }
        if request.method == 'POST':
            form = CenterForm(request.POST)
            if form.is_valid():
                name = form.cleaned_data['name']
                center = form.cleaned_data['center']
                buyer = form.cleaned_data['buyer']
                password = form.cleaned_data['password']
                if str(password) == 'eureka':
                    for card in AccessCode.objects.filter(buyer=buyer, name=name):
                        card.custom_center = center
                        card.custom = True
                        card.save()
                        qty += 1
                    context['buyer'] = buyer
                    context['name'] = name
                    context['qty'] = qty
                    context['center'] = center
                    form = CenterForm()
                    context['form'] = form
                    context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                             self.get_prepopulated_fields(request))
                    return render(request, 'admin/mngr/accesscode/setcenter.html', context)
                else:
                    logout(request)
                    return HttpResponseRedirect('/')
            else:
                context['form'] = form
                context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                        self.get_prepopulated_fields(request))
                return render(request, 'admin/mngr/accesscode/setcenter.html', context)
        else:
            form = CenterForm()
            context['form'] = form
            context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                     self.get_prepopulated_fields(request))
            return render(request, 'admin/mngr/accesscode/setcenter.html', context)

    def deactivate(self, request):
        qty = 0
        nil = []
        context = {
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }
        if request.method == 'POST':
            form = SalesForm(request.POST)
            if form.is_valid():
                start = form.cleaned_data['start']
                finish = form.cleaned_data['finish']
                buyer = form.cleaned_data['buyer']
                password = form.cleaned_data['password']
                if str(password) == 'eureka':
                    if AccessCode.objects.filter(buyer=buyer).exists():
                        allcards = AccessCode.objects.filter(buyer=buyer)
                        for i in allcards:
                            i.active = False
                            i.save()
                            qty += 1
                        message_bit = "DEACTIVATE SUCCESSFUL!"
                    else:
                        try:
                            first = start[3:8]
                            prefix = start[0:3]
                            cardnum = int(first)
                            last = finish[3:8]
                            lastnum = int(last) + 1
                        except Exception as e:
                            message_bit = "THE CARDS ARE INVALID!"
                        else:
                            while cardnum < lastnum:
                                serial = str(prefix) + (str(cardnum))
                                if not AccessCode.objects.filter(srn=serial).exists():
                                    cardnum += 1
                                    nil.append(serial)
                                else:
                                    card = AccessCode.objects.get(srn=serial)
                                    card.active = False
                                    card.save()
                                    cardnum += 1
                                    qty += 1
                            message_bit = "DEACTIVATE SUCCESSFUL!"
                    self.message_user(request, "%s" % message_bit)
                    context['qty'] = qty
                    context['nil'] = nil
                    return render(request, 'admin/mngr/accesscode/deactivate.html', context)
                else:
                    logout(request)
                return HttpResponseRedirect('/')

            else:
                form = SalesForm(request.POST)
                context['form'] = form
                context['title'] = 'DEACTIVATE CARDS'
                context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                         self.get_prepopulated_fields(request))
                return render(request, 'admin/mngr/accesscode/deactivate.html', context)
        form = SalesForm()
        context['form'] = form
        context['title'] = 'DEACTIVATE CARDS'
        context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                 self.get_prepopulated_fields(request))
        return render(request, 'admin/mngr/accesscode/deactivate.html', context)
    
    
    def deactivate_card(self, request, queryset):
        context = {
            'title': 'DEACTIVATE CARDS',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }

        form = SalesForm()
        context['form'] = form
        context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                 self.get_prepopulated_fields(request))
        return render(request, 'admin/mngr/accesscode/deactivate.html', context)
    deactivate_card.short_description = 'Deactivate Cards'



    def activate(self, request):
        qty = 0
        nil = []
        context = {
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }
        if request.method == 'POST':
            form = SalesForm(request.POST)
            if form.is_valid():
                start = form.cleaned_data['start']
                finish = form.cleaned_data['finish']
                buyer = form.cleaned_data['buyer']
                password = form.cleaned_data['password']
                if str(password) == 'eureka':
                    if AccessCode.objects.filter(buyer=buyer).exists():
                        allcards = AccessCode.objects.filter(buyer=buyer)
                        for i in allcards:
                            i.active = False
                            i.save()
                            qty += 1
                        message_bit = "ACTIVATE SUCCESSFUL!"
                    else:
                        try:
                            first = start[3:8]
                            prefix = start[0:3]
                            cardnum = int(first)
                            last = finish[3:8]
                            lastnum = int(last) + 1
                        except Exception as e:
                            message_bit = "THE CARDS ARE INVALID!"
                        else:
                            while cardnum < lastnum:
                                serial = str(prefix) + (str(cardnum))
                                if not AccessCode.objects.filter(srn=serial).exists():
                                    cardnum += 1
                                    nil.append(serial)
                                else:
                                    card = AccessCode.objects.get(srn=serial)
                                    card.active = True
                                    card.save()
                                    cardnum += 1
                                    qty += 1
                            message_bit = "ACTIVATE SUCCESSFUL!"
                    self.message_user(request, "%s" % message_bit)
                    context['qty'] = qty
                    context['nil'] = nil
                    return render(request, 'admin/mngr/accesscode/activate.html', context)
                else:
                    logout(request)
                    return HttpResponseRedirect('/')
            else:
                form = SalesForm(request.POST)
                context['form'] = form
                context['title'] = 'ACTIVATE CARDS'
                context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                         self.get_prepopulated_fields(request))
                return render(request, 'admin/mngr/accesscode/activate.html', context)
        form = SalesForm()
        context['form'] = form
        context['title'] = 'ACTIVATE CARDS'
        context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                 self.get_prepopulated_fields(request))
        return render(request, 'admin/mngr/accesscode/activate.html', context)
    


    def activate_card(self, request, queryset):
        context = {
            'title': 'ACTIVATE CARDS',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }

        form = SalesForm()
        context['form'] = form
        context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                 self.get_prepopulated_fields(request))
        return render(request, 'admin/mngr/accesscode/activate.html', context)
    activate_card.short_description = 'Activate Cards'




class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('client', 'ref', 'transaction_date', 'amount', 'balance')
    actions = ['print_invoice',]

    def print_invoice(self, request, queryset):
        for i in queryset:
            p = Invoice.objects.get(pk=i.id)
        context = {
            'title': 'PRINT INVOICE',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }

        context['p'] = p
        return render(request, 'admin/mngr/invoice/printinv.html', context)
    print_invoice.short_description = 'Print Invoice'


class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('client', 'transaction_date', 'total')
    actions = ['print_receipt',]

    def print_receipt(self, request, queryset):
        for i in queryset:
            p = Receipt.objects.get(pk=i.id)
        context = {
            'title': 'PRINT RECEIPT',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }

        context['p'] = p
        return render(request, 'admin/mngr/receipt/printrec.html', context)
    print_receipt.short_description = 'Print Receipt'