import logging
from .repositories import ConversationRepository, MessageRepository
from accounts.models import User

logger = logging.getLogger(__name__)


class ConversationService:
    def __init__(self):
        self.repo = ConversationRepository()

    def get_for_user(self, user):
        return self.repo.get_for_user(user)

    def get_by_id(self, conversation_id: int):
        return self.repo.get_by_id(conversation_id)

    def create(self, **kwargs) -> dict:
        try:
            conversation = self.repo.create(**kwargs)
            return {'success': True, 'data': conversation}
        except Exception as e:
            logger.exception("Failed to create conversation")
            return {'success': False, 'error': str(e)}

    def get_or_create_direct(self, user, other_user_id: int) -> dict:
        try:
            other = User.objects.filter(id=other_user_id).first()
            if not other:
                return {'success': False, 'error': 'User not found'}
            if user == other:
                return {'success': False, 'error': 'Cannot chat with yourself'}
            conversation = self.repo.get_or_create_direct(user, other)
            return {'success': True, 'data': conversation}
        except Exception as e:
            logger.exception("Failed to get or create conversation")
            return {'success': False, 'error': str(e)}

    def start_with_participants(self, user, participant_ids: list, subject: str = '') -> dict:
        try:
            participants = list(User.objects.filter(id__in=participant_ids))
            if user not in participants:
                participants.append(user)
            if len(participants) < 2:
                return {'success': False, 'error': 'Need at least 2 participants'}
            is_group = len(participants) > 2
            conversation = self.repo.create(
                subject=subject,
                is_group=is_group,
                participants=participants,
            )
            return {'success': True, 'data': conversation}
        except Exception as e:
            logger.exception("Failed to start conversation")
            return {'success': False, 'error': str(e)}


class MessageService:
    def __init__(self):
        self.repo = MessageRepository()

    def get_by_conversation(self, conversation_id: int):
        return self.repo.get_by_conversation(conversation_id)

    def get_by_id(self, message_id: int):
        return self.repo.get_by_id(message_id)

    def send(self, conversation_id: int, sender, body: str, attachment=None) -> dict:
        try:
            message = self.repo.create(
                conversation_id=conversation_id,
                sender=sender,
                body=body,
                attachment=attachment,
            )
            conversation = message.conversation
            conversation.save(update_fields=['updated_at'])
            return {'success': True, 'data': message}
        except Exception as e:
            logger.exception("Failed to send message")
            return {'success': False, 'error': str(e)}

    def mark_as_read(self, message_id: int) -> dict:
        try:
            message = self.repo.mark_as_read(message_id)
            if message:
                return {'success': True, 'data': message}
            return {'success': False, 'error': 'Message not found'}
        except Exception as e:
            logger.exception("Failed to mark message as read")
            return {'success': False, 'error': str(e)}

    def mark_conversation_as_read(self, conversation_id: int, user) -> dict:
        try:
            count = self.repo.mark_conversation_as_read(conversation_id, user)
            return {'success': True, 'marked_count': count}
        except Exception as e:
            logger.exception("Failed to mark conversation as read")
            return {'success': False, 'error': str(e)}


class UnreadService:
    def __init__(self):
        self.repo = MessageRepository()

    def get_unread_count(self, user) -> int:
        return self.repo.get_unread_count_for_user(user)

    def get_unread_by_conversation(self, user) -> dict:
        return self.repo.get_unread_count_by_conversation(user)
