from django import forms
from .models import Category

class SearchForm(forms.Form):

    FILTER_CHOICES = [
        ('name', 'Назва'),
        ('created_at', 'Старі'),
        ('-created_at', 'Недавні'),
        ('price', 'Ціна від меншої'),
        ('-price', 'Ціна від більшої')
    ]

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        label='Категорія',
        empty_label='Усі категорії',
        widget=forms.Select(attrs={'class' : 'form-select'})
    )

    sort_by = forms.ChoiceField(
        required=False,
        label='Сортувати за',
        choices=FILTER_CHOICES
    )