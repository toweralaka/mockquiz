    import csv
from django.http import HttpResponse
def some_view(request):
# Create the HttpResponse object with the appropriate CSV header.
response = HttpResponse(content_type='text/csv')
response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'
writer = csv.writer(response)
writer.writerow(['First row', 'Foo', 'Bar', 'Baz'])
writer.writerow(['Second row', 'A', 'B', 'C', '"Testing"', "Here's a quote"])
return response

    def export_batch_user(self, request, queryset):

        import csv, StringIO
        for btch in queryset:
            email = EmailMessage(str(btch.exam_center)+'(Batch'+str(btch.number)+')' +'Result', ' ', ' ',
                ['djaafolayan@gmail.com', 'olaidealaka12@gmail.com'], ['blindcopy@gmail.com',])

            #attach results
            attachment_csv_file = StringIO.StringIO()

            writer = csv.writer(attachment_csv_file)

            writer.writerow(['user_id', 'username', 'password_hash','profile_id','pin', 'serial', 'first_name', 
                'surname', 'sex', 'phone', 'course', 'passport', 'regnum', 'pc', 'seat', 'online', 'regdate', 
                'give_sample', 'giftpin', 'giftserial', 'batch_id', 'exam_area_id', 'exam_center_id', 'exam_state_id', 
                'examination_id', 'user_id', 'feedback_id', 'paid', 'payment_mode', 'referral_code', 'mails', 'subject'])
            allprofiles = UserProfile.objects.filter(batch=btch)
            #profile_data = allprofiles.values_list('timestamp', 'marked', 'total','batch', 'exam_area', 'exam_center', 'user')
            for i in allprofiles:
                d_user = i.user
                # profl = Result.objects.get(user=pers)
                # data = (profl.user, profl.exam_area, profl.exam_center, profl.batch, profl.timestamp, 
                #profl.marked, profl.total,)
                #writer.writerow(i)
                writer.writerow([d_user.id,d_user.username,d_user.password,i.id,i.pin, i.serial, i.first_name, 
                    i.surname, i.sex, i.phone, i.course, i.passport, i.regnum, i.pc, i.seat, i.online, i.regdate, 
                    i.give_sample, i.giftpin, i.giftserial, i.batch_id, i.exam_area_id, i.exam_center_id, 
                    i.exam_state_id, i.examination_id, i.user_id, i.feedback_id, i.paid, i.payment_mode, 
                    i.referral_code, i.mails, i.subject.all])

            email.attach('attachment_result.csv', attachment_csv_file.getvalue(),
            'text/csv')

            #attach subject scores
            attachment_csv_file = StringIO.StringIO()

            writer = csv.writer(attachment_csv_file)

            writer.writerow(['subject', 'score', 'user'])
            profiles = UserProfile.objects.filter(batch=btch)
            for pf in profiles:
                uscores = SubjectScore.objects.filter(user=str(pf.regnum))
                scores = uscores.values_list('subject', 'score', 'user')
                for i in scores:
                    writer.writerow(i)

            email.attach('attachment_score.csv', attachment_csv_file.getvalue(),
            'text/csv')

            #attach special cases
            attachment_csv_file = StringIO.StringIO()

            writer = csv.writer(attachment_csv_file)

            writer.writerow(['regnumber', 'issue', 'message', 'noresult'])
            profiles = UserProfile.objects.filter(batch=btch)
            for pf in profiles:
                case = SpecialCase.objects.filter(regnumber=str(pf.regnum))
                cases = case.values_list('regnumber', 'issue', 'message', 'noresult')
                for i in cases:
                    writer.writerow(i)

            email.attach('attachment_special_cases.csv', attachment_csv_file.getvalue(),
            'text/csv')
            try:
                email.send(fail_silently=False)
            except Exception as e:
                message_bit = "Export Not Successful for Batch Number "+str(btch.number)+". Check Internet and Export Again"
            else:
                message_bit = "Export Successful for Batch Number "+str(btch.number)+"!"
            self.message_user(request, "%s" % message_bit)
        
    export_results.short_description = 'Export Batch Users'


    def export_center_user(self, request, queryset):

        import csv, StringIO
        for btch in queryset:
            email = EmailMessage(str(btch.exam_center)+'(Batch'+str(btch.number)+')' +'Result', ' ', ' ',
                ['djaafolayan@gmail.com', 'olaidealaka12@gmail.com'], ['blindcopy@gmail.com',])

            #attach results
            attachment_csv_file = StringIO.StringIO()

            writer = csv.writer(attachment_csv_file)

            writer.writerow(['timestamp', 'marked', 'total','batch', 'exam_area', 'exam_center', 'user'])
            reslt = Result.objects.filter(batch=btch)
            users = reslt.values_list('timestamp', 'marked', 'total','batch', 'exam_area', 'exam_center', 'user')
            for i in users:
                # pers = i.user.user
                # profl = Result.objects.get(user=pers)
                # data = (profl.user, profl.exam_area, profl.exam_center, profl.batch, profl.timestamp, profl.marked, profl.total,)
                writer.writerow(i)

            email.attach('attachment_result.csv', attachment_csv_file.getvalue(),
            'text/csv')

            #attach subject scores
            attachment_csv_file = StringIO.StringIO()

            writer = csv.writer(attachment_csv_file)

            writer.writerow(['subject', 'score', 'user'])
            profiles = UserProfile.objects.filter(batch=btch)
            for pf in profiles:
                uscores = SubjectScore.objects.filter(user=str(pf.regnum))
                scores = uscores.values_list('subject', 'score', 'user')
                for i in scores:
                    writer.writerow(i)

            email.attach('attachment_score.csv', attachment_csv_file.getvalue(),
            'text/csv')

            #attach special cases
            attachment_csv_file = StringIO.StringIO()

            writer = csv.writer(attachment_csv_file)

            writer.writerow(['regnumber', 'issue', 'message', 'noresult'])
            profiles = UserProfile.objects.filter(batch=btch)
            for pf in profiles:
                case = SpecialCase.objects.filter(regnumber=str(pf.regnum))
                cases = case.values_list('regnumber', 'issue', 'message', 'noresult')
                for i in cases:
                    writer.writerow(i)

            email.attach('attachment_special_cases.csv', attachment_csv_file.getvalue(),
            'text/csv')
            try:
                email.send(fail_silently=False)
            except Exception as e:
                message_bit = "Export Not Successful for Batch Number "+str(btch.number)+". Check Internet and Export Again"
            else:
                message_bit = "Export Successful for Batch Number "+str(btch.number)+"!"
            self.message_user(request, "%s" % message_bit)
        
    export_results.short_description = 'Export Center Users'


    def export_area_user(self, request, queryset):

        import csv, StringIO
        for btch in queryset:
            email = EmailMessage(str(btch.exam_center)+'(Batch'+str(btch.number)+')' +'Result', ' ', ' ',
                ['djaafolayan@gmail.com', 'olaidealaka12@gmail.com'], ['blindcopy@gmail.com',])

            #attach results
            attachment_csv_file = StringIO.StringIO()

            writer = csv.writer(attachment_csv_file)

            writer.writerow(['timestamp', 'marked', 'total','batch', 'exam_area', 'exam_center', 'user'])
            reslt = Result.objects.filter(batch=btch)
            users = reslt.values_list('timestamp', 'marked', 'total','batch', 'exam_area', 'exam_center', 'user')
            for i in users:
                # pers = i.user.user
                # profl = Result.objects.get(user=pers)
                # data = (profl.user, profl.exam_area, profl.exam_center, profl.batch, profl.timestamp, profl.marked, profl.total,)
                writer.writerow(i)

            email.attach('attachment_result.csv', attachment_csv_file.getvalue(),
            'text/csv')

            #attach subject scores
            attachment_csv_file = StringIO.StringIO()

            writer = csv.writer(attachment_csv_file)

            writer.writerow(['subject', 'score', 'user'])
            profiles = UserProfile.objects.filter(batch=btch)
            for pf in profiles:
                uscores = SubjectScore.objects.filter(user=str(pf.regnum))
                scores = uscores.values_list('subject', 'score', 'user')
                for i in scores:
                    writer.writerow(i)

            email.attach('attachment_score.csv', attachment_csv_file.getvalue(),
            'text/csv')

            #attach special cases
            attachment_csv_file = StringIO.StringIO()

            writer = csv.writer(attachment_csv_file)

            writer.writerow(['regnumber', 'issue', 'message', 'noresult'])
            profiles = UserProfile.objects.filter(batch=btch)
            for pf in profiles:
                case = SpecialCase.objects.filter(regnumber=str(pf.regnum))
                cases = case.values_list('regnumber', 'issue', 'message', 'noresult')
                for i in cases:
                    writer.writerow(i)

            email.attach('attachment_special_cases.csv', attachment_csv_file.getvalue(),
            'text/csv')
            try:
                email.send(fail_silently=False)
            except Exception as e:
                message_bit = "Export Not Successful for Batch Number "+str(btch.number)+". Check Internet and Export Again"
            else:
                message_bit = "Export Successful for Batch Number "+str(btch.number)+"!"
            self.message_user(request, "%s" % message_bit)
        
    export_results.short_description = 'Export Area Users'


    def export_state_user(self, request, queryset):

        import csv, StringIO
        for btch in queryset:
            email = EmailMessage(str(btch.exam_center)+'(Batch'+str(btch.number)+')' +'Result', ' ', ' ',
                ['djaafolayan@gmail.com', 'olaidealaka12@gmail.com'], ['blindcopy@gmail.com',])

            #attach results
            attachment_csv_file = StringIO.StringIO()

            writer = csv.writer(attachment_csv_file)

            writer.writerow(['timestamp', 'marked', 'total','batch', 'exam_area', 'exam_center', 'user'])
            reslt = Result.objects.filter(batch=btch)
            users = reslt.values_list('timestamp', 'marked', 'total','batch', 'exam_area', 'exam_center', 'user')
            for i in users:
                # pers = i.user.user
                # profl = Result.objects.get(user=pers)
                # data = (profl.user, profl.exam_area, profl.exam_center, profl.batch, profl.timestamp, profl.marked, profl.total,)
                writer.writerow(i)

            email.attach('attachment_result.csv', attachment_csv_file.getvalue(),
            'text/csv')

            #attach subject scores
            attachment_csv_file = StringIO.StringIO()

            writer = csv.writer(attachment_csv_file)

            writer.writerow(['subject', 'score', 'user'])
            profiles = UserProfile.objects.filter(batch=btch)
            for pf in profiles:
                uscores = SubjectScore.objects.filter(user=str(pf.regnum))
                scores = uscores.values_list('subject', 'score', 'user')
                for i in scores:
                    writer.writerow(i)

            email.attach('attachment_score.csv', attachment_csv_file.getvalue(),
            'text/csv')

            #attach special cases
            attachment_csv_file = StringIO.StringIO()

            writer = csv.writer(attachment_csv_file)

            writer.writerow(['regnumber', 'issue', 'message', 'noresult'])
            profiles = UserProfile.objects.filter(batch=btch)
            for pf in profiles:
                case = SpecialCase.objects.filter(regnumber=str(pf.regnum))
                cases = case.values_list('regnumber', 'issue', 'message', 'noresult')
                for i in cases:
                    writer.writerow(i)

            email.attach('attachment_special_cases.csv', attachment_csv_file.getvalue(),
            'text/csv')
            try:
                email.send(fail_silently=False)
            except Exception as e:
                message_bit = "Export Not Successful for Batch Number "+str(btch.number)+". Check Internet and Export Again"
            else:
                message_bit = "Export Successful for Batch Number "+str(btch.number)+"!"
            self.message_user(request, "%s" % message_bit)
        
    export_results.short_description = 'Export State Users'






    'pin', 'serial', 'first_name', 'surname', 'sex', 'phone', 'course', 'passport', 'regnum', 'pc', 'seat', 'online', 'regdate', 'give_sample', 'giftpin', 'giftserial', 'batch_id', 'exam_area_id', 'exam_center_id', 'exam_state_id', 'examination_id', 'user_id', 'feedback_id', 'paid', 'payment_mode', 'referral_code', 'mails', 'subject'
i.pin, i.serial, i.first_name, i.surname, i.sex, i.phone, i.course, i.passport, i.regnum, i.pc, i.seat, i.online, i.regdate, i.give_sample, i.giftpin, i.giftserial, i.batch_id, i.exam_area_id, i.exam_center_id, i.exam_state_id, i.examination_id, i.user_id, i.feedback_id, i.paid, i.payment_mode, i.referral_code, i.mails
id  pin serial  first_name  surname sex phone   course  passport    regnum  pc  seat    online  regdate give_sample giftpin giftserial  batch_id    exam_area_id    exam_center_id  exam_state_id   examination_id  user_id feedback_id paid    payment_mode    referral_code   mails
