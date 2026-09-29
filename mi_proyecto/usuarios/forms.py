from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
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


class CustomerPasswordResetForm(PasswordResetForm):
    """Allow active legacy accounts with an unset password to establish one."""

    def get_users(self, email):
        user_model = get_user_model()
        email_field = user_model.get_email_field_name()
        users = user_model._default_manager.filter(
            **{f'{email_field}__iexact': email, 'is_active': True}
        )
        return (user for user in users if getattr(user, email_field, None))


class PasswordResetCodeForm(forms.Form):
    code = forms.RegexField(
        regex=r'^\d{6}$',
        error_messages={'invalid': 'Ingresa el código de 6 dígitos.'},
        widget=forms.TextInput(attrs={
            'class': 'auth-input',
            'placeholder': '000000',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'required': True,
        }),
        label='Código de recuperación',
    )


class AdminUserForm(forms.ModelForm):
    is_admin = forms.ChoiceField(
        choices=(('customer', 'Usuario'), ('admin', 'Administrador')),
        label='Rol',
        widget=forms.Select(attrs={'class': 'manage-input'}),
    )
    password1 = forms.CharField(
        label='Contraseña temporal',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'manage-input', 'autocomplete': 'new-password',
            'placeholder': 'Dejar vacío para conservar la actual',
        }),
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'manage-input', 'autocomplete': 'new-password',
            'placeholder': 'Repite la contraseña',
        }),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'manage-input', 'autocomplete': 'off'}),
            'email': forms.EmailInput(attrs={'class': 'manage-input', 'autocomplete': 'off'}),
            'first_name': forms.TextInput(attrs={'class': 'manage-input'}),
            'last_name': forms.TextInput(attrs={'class': 'manage-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'manage-checkbox'}),
        }
        labels = {
            'username': 'Usuario', 'email': 'Correo electrónico',
            'first_name': 'Nombre', 'last_name': 'Apellido', 'is_active': 'Cuenta activa',
        }

    def __init__(self, *args, allow_role_change=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.allow_role_change = allow_role_change
        if self.instance and self.instance.pk:
            self.fields['is_admin'].initial = 'admin' if (self.instance.is_staff or self.instance.is_superuser) else 'customer'
        if not self.allow_role_change:
            self.fields['is_admin'].disabled = True
            self.fields['is_active'].disabled = True
        if not self.instance or not self.instance.pk:
            self.fields['password1'].required = True
            self.fields['password2'].required = True

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        matches = User.objects.filter(username__iexact=username)
        if self.instance.pk:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise forms.ValidationError('Ya existe una cuenta con ese usuario.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        matches = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise forms.ValidationError('Ya existe una cuenta con ese correo.')
        return email

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('password1')
        password2 = cleaned.get('password2')
        if password1 or password2:
            if password1 != password2:
                self.add_error('password2', 'Las contraseñas no coinciden.')
            elif password1:
                try:
                    password_user = User(
                        username=cleaned.get('username', ''),
                        email=cleaned.get('email', ''),
                        first_name=cleaned.get('first_name', ''),
                        last_name=cleaned.get('last_name', ''),
                    )
                    validate_password(password1, password_user)
                except ValidationError as error:
                    self.add_error('password1', error)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if self.allow_role_change:
            is_admin = self.cleaned_data['is_admin'] == 'admin'
            user.is_staff = is_admin
            user.is_superuser = is_admin
        if self.cleaned_data.get('password1'):
            user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
            self.save_m2m()
        return user
