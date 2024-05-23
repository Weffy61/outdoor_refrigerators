from django import forms
from .models import Report, Photo


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['refrigerator', 'comment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comment'].required = False
        self.fields['comment'].label = 'Комментарий (необязательно)'


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['image']


PhotoFormSet = forms.inlineformset_factory(Report, Photo, form=PhotoForm, extra=2, can_delete=False)
