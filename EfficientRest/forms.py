from django import forms
from django.core.exceptions import ObjectDoesNotExist

modelFormField = forms.IntegerField()

class modelField():
    model = None

    def __init__(self, model):
        self.model = model

    def validateModel(self, id):
        try:
            objectList = self.model.objects.get(id)
        except ObjectDoesNotExist:
            return False

        return True