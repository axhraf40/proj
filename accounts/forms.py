from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, VerificationDocument

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('role', 'phone_number', 'birth_date', 'profile_picture', 'bio', 'address')
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = VerificationDocument
        fields = ('document_type', 'document_file')
        widgets = {
            'document_file': forms.FileInput(attrs={'accept': '.pdf,.jpg,.jpeg,.png'})
        } 