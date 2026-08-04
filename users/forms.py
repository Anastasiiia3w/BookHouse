from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, UserProfile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label='Email',
        widget=forms.TextInput(attrs={
            'placeholder' : 'example@gmail.com',
            'autocomplete' : 'email',
        })
    )

    username = forms.CharField(
        label="Ім'я користувача",
        widget=forms.TextInput(attrs={
            'placeholder' : 'Ваше ім\'я',
            'autocomplete' : 'username',
        })
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('phone', 'city', 'avatar')

        widgets = {
            'city': forms.TextInput(
                attrs={
                    'placeholder': 'Київ',
                    'class': 'form-control'
                }
            ),
            'phone': forms.TextInput(
                attrs={
                    'placeholder': '+380...',
                    'class': 'form-control'
                }
            ),
            'avatar': forms.FileInput(
                attrs={
                    'class': 'form-control'
                }
            ),
        }