from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View, TemplateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.db.models import Q

from .models import SiteSetting
from .services import SiteSettingService


def is_admin(user):
    return user.is_authenticated and (user.is_admin() or user.is_superadmin)


GROUP_LABELS = dict(SiteSetting.GROUP_CHOICES)


@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class SettingsListView(TemplateView):
    template_name = 'website_settings/settings_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = SiteSettingService()
        grouped = service.get_grouped_settings()
        context['grouped_settings'] = grouped
        context['group_labels'] = GROUP_LABELS
        return context


@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class SettingsGroupPartialView(View):
    def get(self, request, group):
        service = SiteSettingService()
        settings = service.get_by_group(group)
        group_label = GROUP_LABELS.get(group, group)
        html = render_to_string('website_settings/partials/setting_group.html', {
            'group': group,
            'group_label': group_label,
            'settings': settings,
        }, request=request)
        return HttpResponse(html)


@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class SettingsBulkUpdateView(View):
    def post(self, request):
        service = SiteSettingService()
        settings_data = {}
        for key, value in request.POST.items():
            if key.startswith('setting_'):
                setting_key = key[8:]
                settings_data[setting_key] = value
        if settings_data:
            result = service.bulk_update(settings_data)
            if result['success']:
                messages.success(request, f'{result["count"]} pengaturan berhasil diperbarui.')
            else:
                messages.error(request, result.get('error', 'Gagal memperbarui pengaturan.'))
        return redirect('website_settings:settings_list')


@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class SettingCreateView(CreateView):
    model = SiteSetting
    template_name = 'website_settings/settings_form.html'
    fields = ['key', 'label', 'value', 'setting_type', 'group', 'order', 'is_public', 'description']

    def get_success_url(self):
        return reverse('website_settings:settings_list')

    def form_valid(self, form):
        result = SiteSettingService().create(**form.cleaned_data)
        if result['success']:
            messages.success(self.request, 'Pengaturan berhasil ditambahkan.')
            return redirect(self.get_success_url())
        messages.error(self.request, result['error'])
        return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = True
        return context


@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class SettingUpdateView(UpdateView):
    model = SiteSetting
    template_name = 'website_settings/settings_form.html'
    fields = ['key', 'label', 'value', 'setting_type', 'group', 'order', 'is_public', 'description']

    def get_success_url(self):
        return reverse('website_settings:settings_list')

    def form_valid(self, form):
        result = SiteSettingService().update(self.object.id, **form.cleaned_data)
        if result['success']:
            messages.success(self.request, 'Pengaturan berhasil diperbarui.')
            return redirect(self.get_success_url())
        messages.error(self.request, result['error'])
        return self.form_invalid(form)


@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class SettingDeleteView(DeleteView):
    model = SiteSetting

    def get_success_url(self):
        return reverse('website_settings:settings_list')

    def delete(self, request, *args, **kwargs):
        setting = self.get_object()
        result = SiteSettingService().delete(setting.id)
        if result['success']:
            messages.success(request, 'Pengaturan berhasil dihapus.')
        else:
            messages.error(request, result.get('error', 'Gagal menghapus pengaturan.'))
        return redirect(self.get_success_url())
