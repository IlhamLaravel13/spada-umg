from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import AIConversation, AIMessage
from .serializers import (
    AIConversationSerializer, AIMessageSerializer,
    AIChatSerializer,
)


class AIConversationViewSet(viewsets.ModelViewSet):
    serializer_class = AIConversationSerializer
    search_fields = ['title']

    def get_queryset(self):
        return AIConversation.objects.filter(user=self.request.user).prefetch_related('messages')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        conversation = self.get_object()
        serializer = AIChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_msg = AIMessage.objects.create(
            conversation=conversation,
            role='user',
            content=serializer.validated_data['message'],
        )

        ai_response = self._get_ai_response(conversation, user_msg.content)
        assistant_msg = AIMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=ai_response,
        )

        return Response({
            'user_message': AIMessageSerializer(user_msg).data,
            'assistant_message': AIMessageSerializer(assistant_msg).data,
        }, status=status.HTTP_201_CREATED)

    def _get_ai_response(self, conversation, message):
        return "Maaf, asisten AI sedang dalam pengembangan. Pesan Anda telah diterima."
