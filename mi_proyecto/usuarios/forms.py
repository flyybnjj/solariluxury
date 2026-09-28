from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm


class RegistroForm(forms.ModelForm):
    """
    [DEPRECADO / CÓDIGO MUERTO]
    Formulario legado de registro con contraseña. El sistema opera actualmente
    bajo autenticación Passwordless OTP vía solicitar_acceso_view.
    Se conserva únicamente por compatibilidad hacia atrás.
    """
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Contraseña (mínimo 6 caracteres)',
            'required': True,
        }),
        label="Contraseña"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Confirmar contraseña',
            'required': True,
        }),
        label="Confirmar Contraseña"
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'auth-input',
                'placeholder': 'Nombre de usuario',
                'required': True,
                'autocomplete': 'username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'auth-input',
                'placeholder': 'Correo electrónico',
                'required': True,
                'autocomplete': 'email'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este correo ya se encuentra registrado.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('password_confirm')
        if p1 and p2 and p1 != p2:
            self.add_error('password_confirm', "Las contraseñas no coinciden.")
        if p1 and len(p1) < 6:
            self.add_error('password', "La contraseña debe tener al menos 6 caracteres.")
        return cleaned_data


class LoginForm(AuthenticationForm):
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
