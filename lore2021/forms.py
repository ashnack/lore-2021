from django.forms import Form, FloatField, FileField, ModelChoiceField

from .models import Game


class ImportForm(Form):
    file = FileField()


class AllocateForm(Form):
    choice = ModelChoiceField(queryset=Game.objects.filter(ready=None))
    amount = FloatField()
