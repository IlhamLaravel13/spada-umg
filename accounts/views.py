from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    PasswordResetView as BasePasswordResetView,
    PasswordResetConfirmView as BasePasswordResetConfirmView,
    PasswordResetCompleteView as BasePasswordResetCompleteView,
    PasswordResetDoneView as BasePasswordResetDoneView,
)
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import FormView, TemplateView, UpdateView, View
from django.http import JsonResponse, Http404
from django.conf import settings
from django.utils import timezone

from .forms import (
    LoginForm, MahasiswaRegistrationForm, DosenRegistrationForm,
    UserProfileForm, PasswordChangeForm,
)
from .models import User, UserSession, LoginAttempt
from .services import AuthService, UserService, SessionService
from .repositories import SessionRepository


class LoginView(FormView):
    template_name = 'accounts/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('dashboard:redirect')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        auth_service = AuthService()
        identifier = form.cleaned_data['username']
        password = form.cleaned_data['password']
        remember_me = form.cleaned_data.get('remember_me', True)

        ip_address = self._get_client_ip()
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')

        result = auth_service.authenticate_user(
            identifier, password, ip_address, user_agent, self.request
        )

        if result['success']:
            if not remember_me:
                self.request.session.set_expiry(0)
            messages.success(
                self.request,
                f'Selamat datang kembali, {result["user"].get_full_name() or result["user"].username}!'
            )
            redirect_to = self.request.GET.get('next', self.success_url)
            return redirect(redirect_to)
        else:
            messages.error(self.request, result['error'])
            return self.form_invalid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return self.render_to_response(self.get_context_data(form=form))

    def _get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return self.request.META.get('REMOTE_ADDR', '')


class RegisterView(TemplateView):
    template_name = 'accounts/register.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:redirect')
        return super().dispatch(request, *args, **kwargs)


class RegisterMahasiswaView(FormView):
    template_name = 'accounts/register_mahasiswa.html'
    form_class = MahasiswaRegistrationForm
    success_url = reverse_lazy('accounts:login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:redirect')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        auth_service = AuthService()
        result = auth_service.register_mahasiswa(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password1'],
            nim=form.cleaned_data['nim'],
            first_name=form.cleaned_data.get('first_name', ''),
            last_name=form.cleaned_data.get('last_name', ''),
            phone=form.cleaned_data.get('phone', ''),
        )

        if result['success']:
            messages.success(
                self.request,
                'Pendaftaran berhasil! Silakan login dengan akun Anda.'
            )
            return redirect(self.success_url)
        else:
            messages.error(self.request, result['error'])
            return self.form_invalid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return self.render_to_response(self.get_context_data(form=form))


class RegisterDosenView(FormView):
    template_name = 'accounts/register_dosen.html'
    form_class = DosenRegistrationForm
    success_url = reverse_lazy('accounts:login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:redirect')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        auth_service = AuthService()
        result = auth_service.register_dosen(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password1'],
            nidn=form.cleaned_data.get('nidn', ''),
            nip=form.cleaned_data.get('nip', ''),
            first_name=form.cleaned_data.get('first_name', ''),
            last_name=form.cleaned_data.get('last_name', ''),
            phone=form.cleaned_data.get('phone', ''),
        )

        if result['success']:
            messages.success(
                self.request,
                'Pendaftaran berhasil! Silakan login dengan akun Anda.'
            )
            return redirect(self.success_url)
        else:
            messages.error(self.request, result['error'])
            return self.form_invalid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return self.render_to_response(self.get_context_data(form=form))


class LogoutView(View):
    def get(self, request, *args, **kwargs):
        auth_service = AuthService()
        auth_service.logout_user(request)
        messages.info(request, 'Anda telah berhasil logout.')
        return redirect('accounts:login')


@method_decorator(login_required, name='dispatch')
class ProfileView(TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user
        context['sessions'] = UserSession.objects.filter(
            user=user, is_active=True
        ).order_by('-last_activity')[:5]
        context['active_tab'] = self.request.GET.get('tab', 'profile')

        total_sessions = UserSession.objects.filter(user=user).count()
        failed_attempts = LoginAttempt.objects.filter(
            username=user.username, was_successful=False
        ).count()

        context['stats'] = {
            'total_sessions': total_sessions,
            'active_sessions': context['sessions'].count(),
            'failed_attempts': failed_attempts,
            'member_since': user.date_joined,
        }
        return context


@method_decorator(login_required, name='dispatch')
class ProfileUpdateView(UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from academics.models import Faculty
            context['faculties'] = Faculty.objects.filter(is_active=True)
        except (ImportError, RuntimeError):
            context['faculties'] = []
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Profil berhasil diperbarui!')
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return self.render_to_response(self.get_context_data(form=form))


@method_decorator(login_required, name='dispatch')
class PasswordChangeView(FormView):
    template_name = 'accounts/password_change.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('accounts:password_change')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
        messages.success(self.request, 'Password berhasil diubah!')
        return redirect(self.success_url)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return self.render_to_response(self.get_context_data(form=form))


class PasswordResetView(BasePasswordResetView):
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/emails/password_reset_email.html'
    subject_template_name = 'accounts/emails/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')

    def form_valid(self, form):
        messages.success(
            self.request,
            'Email reset password telah dikirim. Silakan cek inbox email Anda.'
        )
        return super().form_valid(form)


class PasswordResetDoneView(BasePasswordResetDoneView):
    template_name = 'accounts/password_reset.html'


class PasswordResetConfirmView(BasePasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')

    def form_valid(self, form):
        messages.success(
            self.request,
            'Password berhasil direset! Silakan login dengan password baru Anda.'
        )
        return super().form_valid(form)


class PasswordResetCompleteView(BasePasswordResetCompleteView):
    template_name = 'accounts/password_reset.html'


@method_decorator(login_required, name='dispatch')
class EmailVerificationView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_verified:
            messages.info(request, 'Email Anda sudah terverifikasi.')
            return redirect('accounts:profile')

        auth_service = AuthService()
        result = auth_service.verify_email_token(request.user.id)

        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['error'])

        return redirect('accounts:profile')


@method_decorator(login_required, name='dispatch')
class SessionManagementView(View):
    def post(self, request, *args, **kwargs):
        session_id = kwargs.get('session_id')
        action = request.POST.get('action', 'terminate')

        session_service = SessionService()

        if action == 'terminate_all':
            session_key = request.session.session_key
            result = session_service.terminate_all_sessions(
                request.user.id, session_key
            )
        elif session_id:
            result = session_service.terminate_session(session_id, request.user.id)
        else:
            messages.error(request, 'Sesi tidak valid.')
            return redirect('accounts:profile')

        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['error'])

        return redirect('accounts:profile')

    def get(self, request, *args, **kwargs):
        return redirect('accounts:profile')
