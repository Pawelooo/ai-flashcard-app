from django import forms
from .models import Card


class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ['question', 'answer']
        widgets = {
            'question': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'answer': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
        labels = {
            'question': 'Pytanie',
            'answer': 'Odpowiedź',
        }
