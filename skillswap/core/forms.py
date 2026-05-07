from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Skill, Review, ChatMessage


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control mb-3', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control mb-3', 'placeholder': 'Password'})
    )


class SignupForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control mb-3', 'placeholder': 'Email'})
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control mb-3', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control mb-3', 'placeholder': 'Last Name'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control mb-3', 'placeholder': 'Username'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control mb-3', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control mb-3', 'placeholder': 'Confirm Password'})


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control mb-3'})
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control mb-3'})
    )

    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_pic', 'phone']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control mb-3', 'rows': 3, 'placeholder': 'Tell others about yourself'}),
            'phone': forms.TextInput(attrs={'class': 'form-control mb-3', 'placeholder': 'Phone number'}),
            'profile_pic': forms.FileInput(attrs={'class': 'form-control mb-3'}),
        }


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['name', 'description', 'skill_wanted']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control mb-3', 'placeholder': 'Skill Name (e.g. Web Development)'}),
            'description': forms.Textarea(attrs={'class': 'form-control mb-3', 'rows': 3, 'placeholder': 'Describe your skill...'}),
            'skill_wanted': forms.TextInput(attrs={'class': 'form-control mb-3', 'placeholder': 'Skill you want in return'}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select mb-3'}),
            'comment': forms.Textarea(attrs={'class': 'form-control mb-3', 'rows': 3, 'placeholder': 'Write your review...'}),
        }


class ChatForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['message']
        widgets = {
            'message': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type message...'})
        }
