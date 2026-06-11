from django import forms
from .models import Card


class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ['topic', 'question', 'answer']
        widgets = {
            'topic': forms.Select(attrs={'class': 'form-select'}),
            'question': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'answer': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
        labels = {
            'topic': 'Temat',
            'question': 'Pytanie',
            'answer': 'Odpowiedź',
        }
