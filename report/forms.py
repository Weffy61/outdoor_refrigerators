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


# class ManagerReportForm(forms.ModelForm):
#     class Meta:
#         model = Report
#         fields = ['manager_review', 'comment_manager']
#         widgets = {
#             'manager_review': forms.Select(choices=Report.MANAGER_REVIEW_CHOICES, attrs={'class': 'form-control'}),
#             'comment_manager': forms.Textarea(attrs={'class': 'form-control'}),
#         }
class ManagerReportForm(forms.Form):
    manager_review = forms.ChoiceField(
        choices=[('', '---------'), ('approve', 'Одобрено'), ('decline', 'Отклонено')],
        widget=forms.Select(attrs={'name': 'manager_review', 'class': 'custom-select', 'id': 'id_manager_review'})
    )
    comment_manager = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'cols': '40', 'rows': '10', 'id': 'id_comment_manager'})
    )


PhotoFormSet = forms.inlineformset_factory(Report, Photo, form=PhotoForm, extra=2, can_delete=False)
