from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, View, TemplateView
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q

from .models import Conversation, Message
from .services import ConversationService, MessageService, UnreadService
from accounts.models import User


@method_decorator([login_required], name='dispatch')
class InboxView(TemplateView):
    template_name = 'messaging/inbox.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conv_service = ConversationService()
        unread_service = UnreadService()
        conversations = conv_service.get_for_user(self.request.user)
        context['conversations'] = conversations
        context['unread_counts'] = unread_service.get_unread_by_conversation(self.request.user)
        return context


@method_decorator([login_required], name='dispatch')
class ConversationListView(ListView):
    model = Conversation
    template_name = 'messaging/conversation_list.html'
    context_object_name = 'conversations'

    def get_queryset(self):
        service = ConversationService()
        qs = service.get_for_user(self.request.user)
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(
                Q(subject__icontains=query) |
                Q(participants__username__icontains=query) |
                Q(participants__email__icontains=query) |
                Q(participants__first_name__icontains=query) |
                Q(participants__last_name__icontains=query)
            ).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_id'] = self.request.GET.get('current')
        context['unread_counts'] = UnreadService().get_unread_by_conversation(self.request.user)
        return context


@method_decorator([login_required], name='dispatch')
class ConversationDetailView(DetailView):
    model = Conversation
    template_name = 'messaging/conversation_detail.html'
    context_object_name = 'conversation'

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = self.object
        msg_service = MessageService()
        conv_service = ConversationService()
        unread_service = UnreadService()

        msg_service.mark_conversation_as_read(conversation.id, self.request.user)
        context['messages'] = msg_service.get_by_conversation(conversation.id)
        context['other_participants'] = conversation.participants.exclude(id=self.request.user.id)
        context['unread_counts'] = unread_service.get_unread_by_conversation(self.request.user)
        context['conversations'] = conv_service.get_for_user(self.request.user)
        return context


@method_decorator([login_required], name='dispatch')
class StartConversationView(View):
    def get(self, request):
        conv_service = ConversationService()
        users = User.objects.exclude(id=request.user.id)
        if request.user.is_mahasiswa():
            users = users.filter(
                Q(role='dosen') |
                Q(role='admin') |
                Q(study_program=request.user.study_program)
            ).distinct()
        conversations = conv_service.get_for_user(request.user)
        context = {
            'users': users,
            'conversations': conversations,
        }
        return render(request, 'messaging/new_message.html', context)

    def post(self, request):
        participant_ids = request.POST.getlist('participants')
        subject = request.POST.get('subject', '')
        recipient_id = request.POST.get('recipient')

        if recipient_id:
            participant_ids = [recipient_id]

        if not participant_ids:
            messages.error(request, 'Pilih setidaknya satu penerima.')
            return redirect('messaging:start_conversation')

        service = ConversationService()
        if len(participant_ids) == 1:
            result = service.get_or_create_direct(request.user, int(participant_ids[0]))
        else:
            result = service.start_with_participants(request.user, [int(pid) for pid in participant_ids], subject)

        if result['success']:
            return redirect('messaging:conversation_detail', pk=result['data'].id)
        messages.error(request, result.get('error', 'Gagal memulai percakapan.'))
        return redirect('messaging:start_conversation')


@method_decorator([login_required], name='dispatch')
class SendMessageView(View):
    def post(self, request, pk):
        conversation = get_object_or_404(Conversation, id=pk, participants=request.user)
        body = request.POST.get('body', '').strip()
        attachment = request.FILES.get('attachment')

        if not body and not attachment:
            messages.error(request, 'Pesan tidak boleh kosong.')
            return redirect('messaging:conversation_detail', pk=pk)

        service = MessageService()
        result = service.send(conversation.id, request.user, body, attachment)

        if request.headers.get('HX-Request'):
            if result['success']:
                msg_list_html = render_to_string('messaging/partials/message_list.html', {
                    'messages': service.get_by_conversation(conversation.id),
                    'user': request.user,
                }, request=request)
                return HttpResponse(msg_list_html)
            return HttpResponse(status=400)

        if result['success']:
            messages.success(request, 'Pesan terkirim.')
        else:
            messages.error(request, result.get('error', 'Gagal mengirim pesan.'))
        return redirect('messaging:conversation_detail', pk=pk)


@method_decorator([login_required], name='dispatch')
class MarkAsReadView(View):
    def post(self, request, pk):
        service = MessageService()
        message = service.get_by_id(pk)
        if not message:
            return JsonResponse({'success': False, 'error': 'Message not found'})
        if request.user not in message.conversation.participants.all():
            return JsonResponse({'success': False, 'error': 'Not a participant'})
        result = service.mark_as_read(pk)
        if request.headers.get('HX-Request'):
            return HttpResponse(status=200, headers={'HX-Trigger': 'messageRead'})
        return JsonResponse(result)


@method_decorator([login_required], name='dispatch')
class UnreadCountView(View):
    def get(self, request):
        service = UnreadService()
        count = service.get_unread_count(request.user)
        if request.headers.get('HX-Request'):
            return render(request, 'messaging/partials/unread_badge.html', {'unread_count': count})
        return JsonResponse({'unread_count': count})
