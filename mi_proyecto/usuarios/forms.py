from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class RegistroForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'auth-input', 'placeholder': 'Contraseña', 'required': True,
        'autocomplete': 'new-password',
    }), label='Contraseña')
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'auth-input', 'placeholder': 'Repite la contraseña', 'required': True,
        'autocomplete': 'new-password',
    }), label='Confirmar contraseña')

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'Nombre de usuario', 'required': True, 'autocomplete': 'username'}),
            'email': forms.EmailInput(attrs={'class': 'auth-input', 'placeholder': 'Correo electrónico', 'required': True, 'autocomplete': 'email'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este correo ya tiene una cuenta. Inicia sesión o recupera tu contraseña.')
        return email

    def clean(self):
        cleaned = super().clean()
        password1, password2 = cleaned.get('password1'), cleaned.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Las contraseñas no coinciden.')
        if password1:
            try:
                validate_password(password1, self.instance)
            except ValidationError as error:
                self.add_error('password1', error)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].strip()
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        data = kwargs.get('data')
        if data is not None:
            username_field = User.USERNAME_FIELD
            candidate = data.get(username_field, '').strip()
        else:
            candidate = ''
        if '@' in candidate:
            account = User.objects.filter(email__iexact=candidate).only('username').first()
            if account:
                data = data.copy()
                data[username_field] = account.get_username()
                kwargs['data'] = data
        super().__init__(*args, **kwargs)

    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'auth-input',
        'placeholder': 'Usuario o correo electrónico',
        'required': True,
        'autocomplete': 'username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'auth-input',
        'placeholder': 'Tu contraseña',
        'required': True,
        'autocomplete': 'current-password'
    }))
