from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm, PasswordChangeForm as BasePasswordChangeForm,
    PasswordResetForm as BasePasswordResetForm,
    SetPasswordForm as BaseSetPasswordForm
)
from django.utils.translation import gettext_lazy as _
from .models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label=_('NIM / NIDN / NIP / Email / Username'),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Masukkan NIM, NIDN, NIP, Email, atau Username',
            'autocomplete': 'username',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Masukkan password',
            'autocomplete': 'current-password',
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox',
        })
    )

    error_messages = {
        'invalid_login': _(
            'Silakan masukkan NIM/NIDN/NIP/Email/Username dan password yang benar. '
            'Perhatikan besar kecilnya huruf.'
        ),
        'inactive': _('Akun ini tidak aktif.'),
    }


class MahasiswaRegistrationForm(forms.ModelForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Masukkan username',
            'autocomplete': 'username',
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'contoh@student.umg.ac.id',
            'autocomplete': 'email',
        })
    )
    nim = forms.CharField(
        label='NIM',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Masukkan NIM',
        })
    )
    first_name = forms.CharField(
        label='Nama Depan', required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nama depan',
        })
    )
    last_name = forms.CharField(
        label='Nama Belakang', required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nama belakang',
        })
    )
    phone = forms.CharField(
        label='No. Telepon', required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '08xxxxxxxxxx',
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Minimal 8 karakter',
            'autocomplete': 'new-password',
        })
    )
    password2 = forms.CharField(
        label='Konfirmasi Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Ulangi password',
            'autocomplete': 'new-password',
        })
    )
    agree_terms = forms.BooleanField(
        label='Saya menyetujui syarat dan ketentuan',
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'nim', 'first_name', 'last_name',
            'phone', 'password1', 'password2'
        ]

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username sudah digunakan.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email sudah terdaftar.')
        return email

    def clean_nim(self):
        nim = self.cleaned_data['nim']
        if User.objects.filter(nim=nim).exists():
            raise forms.ValidationError('NIM sudah terdaftar.')
        return nim

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Password tidak cocok.')
        if password1 and len(password1) < 8:
            raise forms.ValidationError('Password minimal 8 karakter.')
        return password2

    def clean_agree_terms(self):
        if not self.cleaned_data.get('agree_terms'):
            raise forms.ValidationError('Anda harus menyetujui syarat dan ketentuan.')
        return True

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.role = 'mahasiswa'
        if commit:
            user.save()
        return user


class DosenRegistrationForm(forms.ModelForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Masukkan username',
            'autocomplete': 'username',
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'contoh@umg.ac.id',
            'autocomplete': 'email',
        })
    )
    nidn = forms.CharField(
        label='NIDN', required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Masukkan NIDN',
        })
    )
    nip = forms.CharField(
        label='NIP', required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Masukkan NIP',
        })
    )
    first_name = forms.CharField(
        label='Nama Depan', required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nama depan',
        })
    )
    last_name = forms.CharField(
        label='Nama Belakang', required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nama belakang',
        })
    )
    phone = forms.CharField(
        label='No. Telepon', required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '08xxxxxxxxxx',
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Minimal 8 karakter',
            'autocomplete': 'new-password',
        })
    )
    password2 = forms.CharField(
        label='Konfirmasi Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Ulangi password',
            'autocomplete': 'new-password',
        })
    )
    agree_terms = forms.BooleanField(
        label='Saya menyetujui syarat dan ketentuan',
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'nidn', 'nip', 'first_name',
            'last_name', 'phone', 'password1', 'password2'
        ]

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username sudah digunakan.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email sudah terdaftar.')
        return email

    def clean_nidn(self):
        nidn = self.cleaned_data.get('nidn')
        if nidn and User.objects.filter(nidn=nidn).exists():
            raise forms.ValidationError('NIDN sudah terdaftar.')
        return nidn

    def clean_nip(self):
        nip = self.cleaned_data.get('nip')
        if nip and User.objects.filter(nip=nip).exists():
            raise forms.ValidationError('NIP sudah terdaftar.')
        return nip

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Password tidak cocok.')
        if password1 and len(password1) < 8:
            raise forms.ValidationError('Password minimal 8 karakter.')
        return password2

    def clean_agree_terms(self):
        if not self.cleaned_data.get('agree_terms'):
            raise forms.ValidationError('Anda harus menyetujui syarat dan ketentuan.')
        return True

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.role = 'dosen'
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'bio', 'avatar',
            'faculty', 'study_program', 'theme_preference',
            'email_notifications'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nama depan',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nama belakang',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '08xxxxxxxxxx',
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Ceritakan tentang diri Anda...',
                'rows': 4,
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-file',
                'accept': 'image/*',
            }),
            'faculty': forms.Select(attrs={
                'class': 'form-select',
            }),
            'study_program': forms.Select(attrs={
                'class': 'form-select',
            }),
            'theme_preference': forms.Select(attrs={
                'class': 'form-select',
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        if phone and not phone.isdigit() and not phone.startswith('+'):
            raise forms.ValidationError('Nomor telepon tidak valid.')
        return phone


class PasswordChangeForm(BasePasswordChangeForm):
    old_password = forms.CharField(
        label='Password Saat Ini',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Masukkan password saat ini',
            'autocomplete': 'current-password',
        })
    )
    new_password1 = forms.CharField(
        label='Password Baru',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Minimal 8 karakter',
            'autocomplete': 'new-password',
        })
    )
    new_password2 = forms.CharField(
        label='Konfirmasi Password Baru',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Ulangi password baru',
            'autocomplete': 'new-password',
        })
    )


class PasswordResetForm(BasePasswordResetForm):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Masukkan email terdaftar',
            'autocomplete': 'email',
        })
    )


class SetPasswordForm(BaseSetPasswordForm):
    new_password1 = forms.CharField(
        label='Password Baru',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Minimal 8 karakter',
            'autocomplete': 'new-password',
        })
    )
    new_password2 = forms.CharField(
        label='Konfirmasi Password Baru',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Ulangi password baru',
            'autocomplete': 'new-password',
        })
    )
