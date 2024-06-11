from PIL import Image
from django import forms
from django.contrib.auth import get_user_model

from .models import Report, Photo, Refrigerator


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['refrigerator', 'comment']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['refrigerator'].queryset = Refrigerator.objects.filter(is_assigned=user)
        self.fields['refrigerator'].label_from_instance = lambda \
            obj: f"{obj.serial_number} ({obj.model}) - {obj.organization.name}, {obj.organization.address}"
        self.fields['comment'].required = False
        self.fields['comment'].label = 'Комментарий (необязательно)'


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['image']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'accept': '*/*'}),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')

        if not image:
            raise forms.ValidationError("Это поле обязательно для заполнения.")

        try:
            img = Image.open(image)
            img.verify()
        except (IOError, SyntaxError):
            raise forms.ValidationError("Загруженный файл не является допустимым изображением.")

        return image


class ManagerReportForm(forms.Form):
    manager_review = forms.ChoiceField(
        choices=[('', '---------'), ('approve', 'Одобрено'), ('decline', 'Отклонено')],
        widget=forms.Select(attrs={'name': 'manager_review', 'class': 'custom-select', 'id': 'id_manager_review'})
    )
    comment_manager = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'cols': '40', 'rows': '10', 'id': 'id_comment_manager'})
    )


class AssignUserForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    user = forms.ModelChoiceField(queryset=get_user_model().objects.all(), label="Выберите пользователя")


PhotoFormSet = forms.inlineformset_factory(Report, Photo, form=PhotoForm, extra=2, can_delete=False)
