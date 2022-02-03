from import_export import resources
from .models import (UserProfile, ExamArea, State, ExamSession,
 Photocard, ExamCenter, Batch, Result, SubjectScore, SendResult, WriteAccess)



class UserProfileResource(resources.ModelResource):
    class Meta:
        model = UserProfile
        fields = ('first_name', 'surname',  'regnum', 'examination', 'seat', 'passport',)
        export_order = ('first_name', 'surname',  'regnum', 'examination', 'seat', 'passport',)


class ResultResource(resources.ModelResource):

    class Meta:
        model = Result
        fields = ('timestamp', 'marked', 'total','batch', 'exam_area', 'exam_center', 'user')
        export_order = ('timestamp', 'marked', 'total','batch', 'exam_area', 'exam_center', 'user')

    def get_instance(self, instance_loader, row):
        return False

    def save_instance(self, instance, real_dry_run):
        if not real_dry_run:
            try:
                obj = Result.objects.get(some_val=instance.some_val)
                # extra logic if object already exist
            except NFCTag.DoesNotExist:
                # create new object
                obj = Result(some_val=instance.some_val)
                obj.save()

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        if dataset.headers:
            dataset.headers = [str(header).lower().strip() for header in dataset.headers]

        if 'id' not in dataset.headers:
            dataset.headers.append('id')