from django.db.models import QuerySet
from .models import AIProvider, AIConversation, AIMessage


class AIProviderRepository:
    def get_active(self) -> AIProvider | None:
        return AIProvider.objects.filter(is_active=True).first()

    def get_by_name(self, name: str) -> AIProvider | None:
        return AIProvider.objects.filter(name=name).first()

    def get_all(self) -> QuerySet[AIProvider]:
        return AIProvider.objects.all()


class AIConversationRepository:
    def get_by_user(self, user_id: int) -> QuerySet[AIConversation]:
        return AIConversation.objects.filter(user_id=user_id).order_by('-updated_at')

    def get_by_id(self, conversation_id: int) -> AIConversation | None:
        return AIConversation.objects.filter(id=conversation_id).first()

    def create(self, user_id: int, title: str, context: str = '') -> AIConversation:
        return AIConversation.objects.create(user_id=user_id, title=title, context=context)

    def update(self, conversation_id: int, **kwargs) -> AIConversation | None:
        updated = AIConversation.objects.filter(id=conversation_id).update(**kwargs)
        if updated:
            return self.get_by_id(conversation_id)
        return None

    def delete(self, conversation_id: int) -> bool:
        return AIConversation.objects.filter(id=conversation_id).delete()[0] > 0


class AIMessageRepository:
    def get_by_conversation(self, conversation_id: int) -> QuerySet[AIMessage]:
        return AIMessage.objects.filter(conversation_id=conversation_id).order_by('created_at')

    def create(self, conversation_id: int, role: str, content: str, metadata: dict = None) -> AIMessage:
        return AIMessage.objects.create(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata or {},
        )

    def get_last_n(self, conversation_id: int, n: int = 10) -> QuerySet[AIMessage]:
        return AIMessage.objects.filter(conversation_id=conversation_id).order_by('-created_at')[:n]
