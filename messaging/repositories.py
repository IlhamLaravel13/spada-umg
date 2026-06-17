from django.db.models import QuerySet, Q, Count, Prefetch
from django.utils import timezone
from .models import Conversation, Message


class ConversationRepository:
    def get_all(self) -> QuerySet[Conversation]:
        return Conversation.objects.prefetch_related('participants').all()

    def get_by_id(self, conversation_id: int) -> Conversation | None:
        return Conversation.objects.filter(id=conversation_id).prefetch_related('participants').first()

    def get_for_user(self, user) -> QuerySet[Conversation]:
        return Conversation.objects.filter(participants=user).prefetch_related(
            'participants',
            Prefetch('messages', queryset=Message.objects.order_by('-created_at')[:1], to_attr='last_message')
        ).annotate(
            unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=user))
        ).order_by('-updated_at')

    def get_or_create_direct(self, user1, user2) -> Conversation:
        qs = Conversation.objects.filter(is_group=False, participants=user1).filter(participants=user2).distinct()
        conversation = qs.first()
        if conversation:
            return conversation
        conversation = Conversation.objects.create(is_group=False)
        conversation.participants.add(user1, user2)
        return conversation

    def create(self, **kwargs) -> Conversation:
        participants = kwargs.pop('participants', [])
        conversation = Conversation.objects.create(**kwargs)
        for user in participants:
            conversation.participants.add(user)
        return conversation

    def update(self, conversation_id: int, **kwargs) -> Conversation | None:
        updated = Conversation.objects.filter(id=conversation_id).update(**kwargs)
        if updated:
            return self.get_by_id(conversation_id)
        return None

    def delete(self, conversation_id: int) -> bool:
        return Conversation.objects.filter(id=conversation_id).delete()[0] > 0


class MessageRepository:
    def get_all(self) -> QuerySet[Message]:
        return Message.objects.select_related('sender', 'conversation').all()

    def get_by_id(self, message_id: int) -> Message | None:
        return Message.objects.filter(id=message_id).select_related('sender', 'conversation').first()

    def get_by_conversation(self, conversation_id: int) -> QuerySet[Message]:
        return Message.objects.filter(conversation_id=conversation_id).select_related('sender').order_by('created_at')

    def get_unread_for_user(self, user) -> QuerySet[Message]:
        return Message.objects.filter(
            ~Q(sender=user),
            conversation__participants=user,
            is_read=False
        ).select_related('sender', 'conversation')

    def get_unread_count_for_user(self, user) -> int:
        return Message.objects.filter(
            ~Q(sender=user),
            conversation__participants=user,
            is_read=False
        ).count()

    def get_unread_count_by_conversation(self, user) -> dict:
        qs = Message.objects.filter(
            ~Q(sender=user),
            conversation__participants=user,
            is_read=False
        ).values('conversation_id').annotate(count=Count('id'))
        return {item['conversation_id']: item['count'] for item in qs}

    def create(self, **kwargs) -> Message:
        return Message.objects.create(**kwargs)

    def mark_as_read(self, message_id: int) -> Message | None:
        updated = Message.objects.filter(id=message_id, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        if updated:
            return self.get_by_id(message_id)
        return None

    def mark_conversation_as_read(self, conversation_id: int, user) -> int:
        return Message.objects.filter(
            conversation_id=conversation_id,
            is_read=False
        ).exclude(sender=user).update(is_read=True, read_at=timezone.now())

    def delete(self, message_id: int) -> bool:
        return Message.objects.filter(id=message_id).delete()[0] > 0
