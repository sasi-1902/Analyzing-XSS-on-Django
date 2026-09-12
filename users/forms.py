from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254,
        help_text='Required. Enter a valid email address.',
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class EditProfileForm(forms.Form):
    username = forms.CharField(max_length=150)
    about_me = forms.CharField(widget=forms.Textarea, required=False)
    image = forms.ImageField(required=False)

    def __init__(self, *args, original_username=None, **kwargs):
        self.original_username = original_username
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username']
        if username != self.original_username and User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username
