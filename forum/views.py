from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.db.models import Q

from .models import Forum, ForumTopic, ForumReply
from .services import ForumService


def is_admin_or_dosen(user):
    return user.is_authenticated and (user.is_dosen() or user.is_admin())


class ForumListView(ListView):
    model = Forum
    template_name = 'forum/forum_list.html'
    context_object_name = 'forums'
    paginate_by = 20

    def get_queryset(self):
        service = ForumService()
        qs = service.get_for_user(self.request.user) if self.request.user.is_authenticated else service.get_active()
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))
        return qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_class_view'] = False
        return context


class ClassForumListView(ListView):
    model = Forum
    template_name = 'forum/forum_list.html'
    context_object_name = 'forums'
    paginate_by = 20

    def get_queryset(self):
        class_id = self.kwargs.get('class_id')
        service = ForumService()
        return service.get_by_class(class_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_class_view'] = True
        context['class_id'] = self.kwargs.get('class_id')
        return context


class ForumDetailView(DetailView):
    model = Forum
    template_name = 'forum/forum_detail.html'
    context_object_name = 'forum'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = ForumService()
        topics = service.get_topics(self.object.id)
        query = self.request.GET.get('q')
        if query:
            topics = topics.filter(Q(title__icontains=query) | Q(content__icontains=query))
        context['topics'] = topics
        return context


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class ForumCreateView(CreateView):
    model = Forum
    template_name = 'forum/forum_form.html'
    fields = ['class_meta', 'title', 'description', 'is_active']

    def get_success_url(self):
        return reverse('forum:forum_detail', args=[self.object.id])

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        result = ForumService().create(**form.cleaned_data, created_by=self.request.user)
        if result['success']:
            messages.success(self.request, 'Forum berhasil dibuat.')
            return redirect(self.get_success_url())
        messages.error(self.request, result['error'])
        return self.form_invalid(form)


class TopicDetailView(DetailView):
    model = ForumTopic
    template_name = 'forum/topic_detail.html'
    context_object_name = 'topic'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if request.user.is_authenticated:
            ForumService().increment_views(self.object.id)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = ForumService()
        context['replies'] = service.get_replies(self.object.id)
        return context


@method_decorator([login_required], name='dispatch')
class TopicCreateView(CreateView):
    model = ForumTopic
    template_name = 'forum/topic_form.html'
    fields = ['title', 'content']

    def dispatch(self, request, *args, **kwargs):
        self.forum = get_object_or_404(Forum, id=self.kwargs.get('forum_id'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['forum'] = self.forum
        return context

    def form_valid(self, form):
        service = ForumService()
        result = service.create_topic(
            forum=self.forum,
            title=form.cleaned_data['title'],
            content=form.cleaned_data['content'],
            author=self.request.user,
        )
        if result['success']:
            messages.success(self.request, 'Topik berhasil dibuat.')
            return redirect('forum:topic_detail', pk=result['data'].id)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)


@method_decorator([login_required], name='dispatch')
class TopicUpdateView(UpdateView):
    model = ForumTopic
    template_name = 'forum/topic_form.html'
    fields = ['title', 'content']

    def get_success_url(self):
        return reverse('forum:topic_detail', args=[self.object.id])

    def get_queryset(self):
        return ForumTopic.objects.filter(author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        context['forum'] = self.object.forum
        return context

    def form_valid(self, form):
        result = ForumService().update_topic(self.object.id, **form.cleaned_data)
        if result['success']:
            messages.success(self.request, 'Topik berhasil diperbarui.')
            return redirect(self.get_success_url())
        messages.error(self.request, result['error'])
        return self.form_invalid(form)


@method_decorator([login_required], name='dispatch')
class TopicDeleteView(DeleteView):
    model = ForumTopic

    def get_success_url(self):
        return reverse('forum:forum_detail', args=[self.object.forum_id])

    def get_queryset(self):
        return ForumTopic.objects.filter(author=self.request.user)

    def delete(self, request, *args, **kwargs):
        topic = self.get_object()
        forum_id = topic.forum_id
        result = ForumService().delete_topic(topic.id)
        if result['success']:
            messages.success(request, 'Topik berhasil dihapus.')
        else:
            messages.error(request, result['error'])
        return redirect('forum:forum_detail', pk=forum_id)


@method_decorator([login_required], name='dispatch')
class ReplyCreateView(View):
    def post(self, request, topic_id):
        service = ForumService()
        topic = service.get_topic_by_id(topic_id)
        if not topic:
            messages.error(request, 'Topik tidak ditemukan.')
            return redirect('forum:forum_list')
        if topic.is_closed:
            messages.error(request, 'Topik ini sudah ditutup.')
            return redirect('forum:topic_detail', pk=topic_id)

        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')
        if not content:
            messages.error(request, 'Konten balasan tidak boleh kosong.')
            return redirect('forum:topic_detail', pk=topic_id)

        kwargs = {
            'topic': topic,
            'content': content,
            'author': request.user,
        }
        if parent_id:
            kwargs['parent_id'] = parent_id

        result = service.create_reply(**kwargs)
        if result['success']:
            if request.headers.get('HX-Request'):
                html = render_to_string('forum/reply_partial.html', {'reply': result['data']}, request=request)
                return HttpResponse(html, status=201)
            messages.success(request, 'Balasan berhasil ditambahkan.')
        else:
            messages.error(request, result['error'])
        return redirect('forum:topic_detail', pk=topic_id)


@method_decorator([login_required], name='dispatch')
class ReplyUpdateView(View):
    def post(self, request, pk):
        service = ForumService()
        reply = service.get_reply_by_id(pk)
        if not reply or reply.author != request.user:
            messages.error(request, 'Anda tidak memiliki izin.')
            return redirect('forum:topic_detail', pk=reply.topic_id if reply else 0)

        content = request.POST.get('content')
        if not content:
            messages.error(request, 'Konten tidak boleh kosong.')
            return redirect('forum:topic_detail', pk=reply.topic_id)

        result = service.update_reply(pk, content=content)
        if result['success']:
            messages.success(request, 'Balasan diperbarui.')
        return redirect('forum:topic_detail', pk=reply.topic_id)


@method_decorator([login_required], name='dispatch')
class ReplyDeleteView(View):
    def post(self, request, pk):
        service = ForumService()
        reply = service.get_reply_by_id(pk)
        if not reply:
            messages.error(request, 'Balasan tidak ditemukan.')
            return redirect('forum:forum_list')
        if reply.author != request.user and not request.user.is_admin():
            messages.error(request, 'Anda tidak memiliki izin.')
            return redirect('forum:topic_detail', pk=reply.topic_id)
        topic_id = reply.topic_id
        result = service.delete_reply(pk)
        if result['success']:
            messages.success(request, 'Balasan dihapus.')
        return redirect('forum:topic_detail', pk=topic_id)


@method_decorator([login_required], name='dispatch')
class ReplyToggleLikeView(View):
    def post(self, request, pk):
        service = ForumService()
        result = service.toggle_like(pk, request.user)
        if request.headers.get('HX-Request'):
            return HttpResponse(status=200, headers={'HX-Trigger': 'replyLiked'})
        return JsonResponse(result)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class ReplyMarkSolutionView(View):
    def post(self, request, pk, topic_id):
        service = ForumService()
        result = service.mark_as_solution(pk, topic_id)
        if result['success']:
            messages.success(request, 'Solusi ditandai.')
        else:
            messages.error(request, result.get('error', 'Gagal menandai solusi.'))
        return redirect('forum:topic_detail', pk=topic_id)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class ToggleTopicPinView(View):
    def post(self, request, pk):
        service = ForumService()
        topic = service.get_topic_by_id(pk)
        if not topic:
            messages.error(request, 'Topik tidak ditemukan.')
            return redirect('forum:forum_list')
        service.toggle_topic_pin(pk)
        return redirect('forum:topic_detail', pk=pk)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class ToggleTopicCloseView(View):
    def post(self, request, pk):
        service = ForumService()
        topic = service.get_topic_by_id(pk)
        if not topic:
            messages.error(request, 'Topik tidak ditemukan.')
            return redirect('forum:forum_list')
        result = service.toggle_topic_close(pk)
        if result['success']:
            messages.success(request, 'Status topik diperbarui.')
        return redirect('forum:topic_detail', pk=pk)
