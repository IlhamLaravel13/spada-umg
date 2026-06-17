import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, DeleteView, View, TemplateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string

from .models import AIConversation, AIMessage
from .services import AIService


@method_decorator(login_required, name='dispatch')
class AIChatView(TemplateView):
    template_name = 'ai_assistant/ai_chat.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = AIService()
        context['conversations'] = service.get_user_conversations(self.request.user.id)

        conversation_id = self.request.GET.get('conversation')
        if conversation_id:
            result = service.get_conversation_history(
                int(conversation_id), self.request.user.id
            )
            if result['success']:
                context['active_conversation'] = result['conversation']
                context['messages'] = result['messages']
        return context


@method_decorator(login_required, name='dispatch')
class AISendMessageView(View):
    def post(self, request, *args, **kwargs):
        service = AIService()
        message = request.POST.get('message', '').strip()
        conversation_id = request.POST.get('conversation_id')

        if not message:
            return JsonResponse({'success': False, 'error': 'Pesan tidak boleh kosong'})

        if not conversation_id:
            title = message[:50] + '...' if len(message) > 50 else message
            result = service.create_conversation(request.user.id, title)
            if not result['success']:
                return JsonResponse(result)
            conversation_id = result['conversation'].id
        else:
            conversation_id = int(conversation_id)

        result = service.send_message(conversation_id, request.user.id, message)
        if result['success']:
            result['conversation_id'] = conversation_id
            if request.headers.get('HX-Request'):
                html = render_to_string(
                    'ai_assistant/_message_partial.html',
                    {'msg': result['message'], 'is_user': False},
                    request=request,
                )
                response = HttpResponse(html)
                response['HX-Trigger'] = json.dumps({
                    'conversationUpdated': {'id': conversation_id},
                    'clearInput': '',
                })
                return response
        return JsonResponse(result)


@method_decorator(login_required, name='dispatch')
class AICreateConversationView(View):
    def post(self, request, *args, **kwargs):
        service = AIService()
        title = request.POST.get('title', 'Percakapan Baru')
        result = service.create_conversation(request.user.id, title)
        if result['success']:
            return redirect('ai_assistant:chat') + f'?conversation={result["conversation"].id}'
        messages.error(request, result['error'])
        return redirect('ai_assistant:chat')


@method_decorator(login_required, name='dispatch')
class AIDeleteConversationView(View):
    def post(self, request, pk):
        service = AIService()
        result = service.delete_conversation(pk, request.user.id)
        if result['success']:
            messages.success(request, 'Percakapan dihapus')
        else:
            messages.error(request, result['error'])
        return redirect('ai_assistant:chat')


@method_decorator(login_required, name='dispatch')
class AIHistoryView(ListView):
    template_name = 'ai_assistant/ai_history.html'
    context_object_name = 'conversations'

    def get_queryset(self):
        service = AIService()
        return service.get_user_conversations(self.request.user.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for conv in context['conversations']:
            conv.msg_count = conv.messages.count()
        context['total_conversations'] = context['conversations'].count()
        return context


@method_decorator(login_required, name='dispatch')
class AISidebarView(TemplateView):
    template_name = 'ai_assistant/ai_sidebar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = AIService()
        context['conversations'] = service.get_user_conversations(self.request.user.id)[:5]
        return context


@method_decorator(login_required, name='dispatch')
class AISummarizeView(View):
    def post(self, request):
        text = request.POST.get('text', '')
        if not text:
            return JsonResponse({'success': False, 'error': 'Teks tidak boleh kosong'})
        service = AIService()
        result = service.summarize_material(text)
        return JsonResponse(result)


@method_decorator(login_required, name='dispatch')
class AIRecommendationsView(View):
    def post(self, request):
        interests = request.POST.get('interests', '')
        service = AIService()
        result = service.get_learning_recommendations(request.user.id, interests)
        return JsonResponse(result)


@method_decorator(login_required, name='dispatch')
class AIAskQuestionView(View):
    def post(self, request):
        question = request.POST.get('question', '')
        context = request.POST.get('context', '')
        if not question:
            return JsonResponse({'success': False, 'error': 'Pertanyaan tidak boleh kosong'})
        service = AIService()
        result = service.ask_question(question, context)
        return JsonResponse(result)
