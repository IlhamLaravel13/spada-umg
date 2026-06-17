import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, DetailView, ListView, FormView, View
from django.http import FileResponse, Http404
from django.utils import timezone

from .models import Certificate
from .services import CertificateService
from .repositories import CertificateRepository

logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class CertificateListView(ListView):
    model = Certificate
    template_name = 'certificates/certificate_list.html'
    context_object_name = 'certificates'
    paginate_by = 20

    def get_queryset(self):
        qs = Certificate.objects.filter(user=self.request.user)
        ctype = self.request.GET.get('type')
        if ctype:
            qs = qs.filter(certificate_type=ctype)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        svc = CertificateService()
        qs = Certificate.objects.filter(user=self.request.user)
        context['stats'] = {
            'total': qs.count(),
            'verified': qs.filter(is_verified=True).count(),
        }
        context['current_type'] = self.request.GET.get('type', '')
        return context


@method_decorator(login_required, name='dispatch')
class CertificateDetailView(DetailView):
    model = Certificate
    template_name = 'certificates/certificate_detail.html'
    context_object_name = 'certificate'

    def get_queryset(self):
        return Certificate.objects.filter(user=self.request.user)


@method_decorator(login_required, name='dispatch')
class CertificateDownloadView(View):
    def get(self, request, *args, **kwargs):
        certificate = get_object_or_404(
            Certificate, id=kwargs['pk'], user=request.user
        )
        if not certificate.pdf_file:
            raise Http404('File PDF tidak tersedia.')

        response = FileResponse(
            certificate.pdf_file.open('rb'),
            content_type='application/pdf',
        )
        response['Content-Disposition'] = (
            f'attachment; filename="sertifikat_{certificate.certificate_number}.pdf"'
        )
        return response


class CertificateVerifyView(FormView):
    template_name = 'certificates/certificate_verify.html'
    success_url = reverse_lazy('certificates:verify_result')

    def get_form(self, form_class=None):
        from django import forms

        class VerifyForm(forms.Form):
            certificate_number = forms.CharField(
                label='Nomor Sertifikat',
                max_length=100,
                widget=forms.TextInput(attrs={
                    'class': 'w-full rounded-xl bg-white/10 border border-white/20 text-white px-4 py-3',
                    'placeholder': 'Masukkan nomor sertifikat',
                    'autofocus': True,
                })
            )

        return VerifyForm(**self.get_form_kwargs())

    def form_valid(self, form):
        number = form.cleaned_data['certificate_number']
        return redirect(f'{self.success_url}?number={number}')

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return self.render_to_response(self.get_context_data(form=form))


class CertificateVerifyResultView(TemplateView):
    template_name = 'certificates/certificate_verify_result.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        number = self.request.GET.get('number', '')
        if number:
            svc = CertificateService()
            result = svc.verify_certificate(number)
            context['result'] = result
            context['certificate'] = result.get('certificate')
        return context


@method_decorator(login_required, name='dispatch')
class CertificateRequestView(FormView):
    template_name = 'certificates/certificate_list.html'
    success_url = reverse_lazy('certificates:list')

    def get_form(self, form_class=None):
        from django import forms

        class RequestForm(forms.Form):
            certificate_type = forms.ChoiceField(
                choices=Certificate.TYPE_CHOICES,
                label='Tipe Sertifikat',
            )
            title = forms.CharField(
                max_length=200,
                label='Judul Sertifikat',
            )
            description = forms.CharField(
                required=False,
                widget=forms.Textarea,
                label='Deskripsi',
            )

        return RequestForm(**self.get_form_kwargs())

    def form_valid(self, form):
        svc = CertificateService()
        result = svc.create_certificate(
            user=self.request.user,
            cert_type=form.cleaned_data['certificate_type'],
            title=form.cleaned_data['title'],
            description=form.cleaned_data.get('description', ''),
        )
        if result['success']:
            messages.success(self.request, 'Sertifikat berhasil dibuat.')
        else:
            messages.error(self.request, result.get('error', 'Gagal membuat sertifikat.'))
        return redirect(self.success_url)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return redirect(self.success_url)
