from django.db.models import QuerySet, Q, Count
from .models import Forum, ForumTopic, ForumReply


class ForumRepository:
    def get_all(self) -> QuerySet[Forum]:
        return Forum.objects.select_related('class_meta', 'created_by').all()

    def get_active(self) -> QuerySet[Forum]:
        return self.get_all().filter(is_active=True)

    def get_by_id(self, forum_id: int) -> Forum | None:
        return Forum.objects.filter(id=forum_id).select_related('class_meta', 'created_by').first()

    def get_by_class(self, class_id: int) -> QuerySet[Forum]:
        return self.get_active().filter(class_meta_id=class_id)

    def get_for_user(self, user) -> QuerySet[Forum]:
        qs = self.get_active().select_related('class_meta', 'created_by')
        if user.is_mahasiswa():
            return qs.filter(class_meta__enrollments__student=user).distinct()
        elif user.is_dosen():
            return qs.filter(Q(class_meta__lecturer=user) | Q(created_by=user)).distinct()
        return qs

    def search(self, query: str) -> QuerySet[Forum]:
        return Forum.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    def create(self, **kwargs) -> Forum:
        return Forum.objects.create(**kwargs)

    def update(self, forum_id: int, **kwargs) -> Forum | None:
        updated = Forum.objects.filter(id=forum_id).update(**kwargs)
        if updated:
            return self.get_by_id(forum_id)
        return None

    def delete(self, forum_id: int) -> bool:
        return Forum.objects.filter(id=forum_id).delete()[0] > 0


class ForumTopicRepository:
    def get_all(self) -> QuerySet[ForumTopic]:
        return ForumTopic.objects.select_related('forum', 'author').all()

    def get_by_id(self, topic_id: int) -> ForumTopic | None:
        return ForumTopic.objects.filter(id=topic_id).select_related('forum', 'author', 'forum__class_meta').first()

    def get_by_forum(self, forum_id: int) -> QuerySet[ForumTopic]:
        return self.get_all().filter(forum_id=forum_id)

    def search(self, query: str) -> QuerySet[ForumTopic]:
        return ForumTopic.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )

    def increment_views(self, topic_id: int):
        ForumTopic.objects.filter(id=topic_id).update(views=Count('views') + 1)

    def create(self, **kwargs) -> ForumTopic:
        return ForumTopic.objects.create(**kwargs)

    def update(self, topic_id: int, **kwargs) -> ForumTopic | None:
        updated = ForumTopic.objects.filter(id=topic_id).update(**kwargs)
        if updated:
            return self.get_by_id(topic_id)
        return None

    def delete(self, topic_id: int) -> bool:
        return ForumTopic.objects.filter(id=topic_id).delete()[0] > 0


class ForumReplyRepository:
    def get_all(self) -> QuerySet[ForumReply]:
        return ForumReply.objects.select_related('topic', 'author', 'parent').prefetch_related('likes').all()

    def get_by_id(self, reply_id: int) -> ForumReply | None:
        return ForumReply.objects.filter(id=reply_id).select_related('topic', 'author', 'parent').first()

    def get_by_topic(self, topic_id: int) -> QuerySet[ForumReply]:
        return self.get_all().filter(topic_id=topic_id)

    def create(self, **kwargs) -> ForumReply:
        return ForumReply.objects.create(**kwargs)

    def update(self, reply_id: int, **kwargs) -> ForumReply | None:
        updated = ForumReply.objects.filter(id=reply_id).update(**kwargs)
        if updated:
            return self.get_by_id(reply_id)
        return None

    def delete(self, reply_id: int) -> bool:
        return ForumReply.objects.filter(id=reply_id).delete()[0] > 0

    def toggle_like(self, reply_id: int, user) -> dict:
        reply = self.get_by_id(reply_id)
        if not reply:
            return {'success': False, 'error': 'Reply not found'}
        if reply.likes.filter(id=user.id).exists():
            reply.likes.remove(user)
            return {'success': True, 'liked': False}
        reply.likes.add(user)
        return {'success': True, 'liked': True}

    def mark_as_solution(self, reply_id: int, topic_id: int) -> dict:
        ForumReply.objects.filter(topic_id=topic_id).update(is_solution=False)
        updated = ForumReply.objects.filter(id=reply_id).update(is_solution=True)
        if updated:
            return {'success': True}
        return {'success': False, 'error': 'Reply not found'}
