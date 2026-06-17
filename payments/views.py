import json
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, FormView, DetailView, ListView, View
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .models import Payment, PaymentReceipt
from .services import PaymentService, MidtransService, XenditService, InvoiceService
from .repositories import PaymentRepository

logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class PaymentListView(ListView):
    model = Payment
    template_name = 'payments/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20

    def get_queryset(self):
        qs = Payment.objects.filter(user=self.request.user)
        status = self.request.GET.get('status')
        ptype = self.request.GET.get('type')
        if status:
            qs = qs.filter(status=status)
        if ptype:
            qs = qs.filter(payment_type=ptype)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        svc = PaymentService()
        context['stats'] = svc.get_payment_stats(self.request.user.id)
        context['current_status'] = self.request.GET.get('status', '')
        context['current_type'] = self.request.GET.get('type', '')
        return context


@method_decorator(login_required, name='dispatch')
class PaymentDetailView(DetailView):
    model = Payment
    template_name = 'payments/payment_detail.html'
    context_object_name = 'payment'

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)


@method_decorator(login_required, name='dispatch')
class PaymentCreateView(FormView):
    template_name = 'payments/payment_form.html'
    success_url = reverse_lazy('payments:list')

    def get_form(self, form_class=None):
        from django import forms

        class PaymentForm(forms.Form):
            payment_type = forms.ChoiceField(
                choices=Payment.TYPE_CHOICES,
                label='Tipe Pembayaran',
                widget=forms.Select(attrs={
                    'class': 'w-full rounded-xl bg-white/10 border border-white/20 text-white px-4 py-3',
                })
            )
            amount = forms.DecimalField(
                label='Jumlah Pembayaran',
                min_value=0,
                widget=forms.NumberInput(attrs={
                    'class': 'w-full rounded-xl bg-white/10 border border-white/20 text-white px-4 py-3',
                    'placeholder': 'Rp 0',
                })
            )
            payment_method = forms.ChoiceField(
                choices=Payment.METHOD_CHOICES,
                label='Metode Pembayaran',
                widget=forms.Select(attrs={
                    'class': 'w-full rounded-xl bg-white/10 border border-white/20 text-white px-4 py-3',
                })
            )
            description = forms.CharField(
                label='Deskripsi',
                required=False,
                widget=forms.Textarea(attrs={
                    'class': 'w-full rounded-xl bg-white/10 border border-white/20 text-white px-4 py-3',
                    'rows': 3,
                    'placeholder': 'Keterangan pembayaran (opsional)',
                })
            )

        return PaymentForm(**self.get_form_kwargs())

    def form_valid(self, form):
        svc = PaymentService()
        result = svc.create_payment(
            user=self.request.user,
            payment_type=form.cleaned_data['payment_type'],
            amount=form.cleaned_data['amount'],
            description=form.cleaned_data.get('description', ''),
            payment_method=form.cleaned_data.get('payment_method', ''),
        )
        if result['success']:
            payment = result['payment']
            messages.success(self.request, 'Pembayaran berhasil dibuat.')
            if payment.payment_url:
                return redirect(payment.payment_url)
            return redirect('payments:detail', pk=payment.id)
        else:
            messages.error(self.request, result.get('error', 'Gagal membuat pembayaran.'))
            return self.form_invalid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{error}')
        return self.render_to_response(self.get_context_data(form=form))


@method_decorator(login_required, name='dispatch')
class PaymentSuccessView(TemplateView):
    template_name = 'payments/payment_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment_id = self.request.GET.get('payment_id')
        if payment_id:
            context['payment'] = get_object_or_404(
                Payment, id=payment_id, user=self.request.user
            )
        return context


@method_decorator(login_required, name='dispatch')
class PaymentFailedView(TemplateView):
    template_name = 'payments/payment_failed.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment_id = self.request.GET.get('payment_id')
        if payment_id:
            context['payment'] = get_object_or_404(
                Payment, id=payment_id, user=self.request.user
            )
        return context


@method_decorator(login_required, name='dispatch')
class PaymentRetryView(View):
    def post(self, request, *args, **kwargs):
        payment = get_object_or_404(Payment, id=kwargs['pk'], user=request.user)
        if payment.status not in ['pending', 'failed', 'expired']:
            messages.error(request, 'Pembayaran tidak dapat diulang.')
            return redirect('payments:detail', pk=payment.id)

        svc = PaymentService()
        if payment.payment_method == 'midtrans':
            midtrans = MidtransService()
            result = midtrans.create_transaction(payment)
            if result['success']:
                return redirect(result['redirect_url'])
        elif payment.payment_method == 'xendit':
            xendit = XenditService()
            result = xendit.create_invoice(payment)
            if result['success']:
                return redirect(result['invoice_url'])

        messages.error(request, 'Gagal memproses ulang pembayaran.')
        return redirect('payments:detail', pk=payment.id)


@method_decorator(login_required, name='dispatch')
class PaymentReceiptUploadView(View):
    def post(self, request, *args, **kwargs):
        payment = get_object_or_404(Payment, id=kwargs['pk'], user=request.user)
        if payment.status != 'pending':
            messages.error(request, 'Pembayaran sudah diproses.')
            return redirect('payments:detail', pk=payment.id)

        receipt_file = request.FILES.get('receipt_file')
        if not receipt_file:
            messages.error(request, 'Silakan pilih file bukti pembayaran.')
            return redirect('payments:detail', pk=payment.id)

        receipt = PaymentReceipt.objects.create(
            payment=payment,
            receipt_file=receipt_file,
            receipt_number=InvoiceService.generate_receipt_number(),
            notes=request.POST.get('notes', ''),
        )
        PaymentRepository().update_status(payment.id, 'processing')
        messages.success(request, 'Bukti pembayaran berhasil diupload.')
        return redirect('payments:detail', pk=payment.id)


@csrf_exempt
def midtrans_notification(request):
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        data = json.loads(request.body)
        svc = MidtransService()
        result = svc.handle_notification(data)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)


@csrf_exempt
def xendit_callback(request):
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        data = json.loads(request.body)
        svc = XenditService()
        result = svc.handle_callback(data)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
