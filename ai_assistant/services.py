import json
import logging
from abc import ABC, abstractmethod
from django.conf import settings

from .repositories import AIProviderRepository, AIConversationRepository, AIMessageRepository

logger = logging.getLogger(__name__)


class BaseAIService(ABC):
    @abstractmethod
    def chat(self, messages: list, **kwargs) -> str:
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        pass


class OpenAIService(BaseAIService):
    def __init__(self, api_key: str = None, model: str = 'gpt-4'):
        self.api_key = api_key
        self.model = model

    def chat(self, messages: list, **kwargs) -> str:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 2000),
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.exception("OpenAI API error")
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    def get_model_name(self) -> str:
        return self.model


class GeminiService(BaseAIService):
    def __init__(self, api_key: str = None, model: str = 'gemini-pro'):
        self.api_key = api_key
        self.model = model

    def chat(self, messages: list, **kwargs) -> str:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)

            system_msg = ''
            chat_messages = []
            for msg in messages:
                if msg['role'] == 'system':
                    system_msg = msg['content']
                elif msg['role'] == 'user':
                    chat_messages.append({'role': 'user', 'parts': [msg['content']]})
                elif msg['role'] == 'assistant':
                    chat_messages.append({'role': 'model', 'parts': [msg['content']]})

            if system_msg:
                chat_messages.insert(0, {'role': 'user', 'parts': [f"System: {system_msg}"]})

            response = model.generate_content(
                chat_messages,
                generation_config=genai.types.GenerationConfig(
                    temperature=kwargs.get('temperature', 0.7),
                    max_output_tokens=kwargs.get('max_tokens', 2000),
                )
            )
            return response.text
        except Exception as e:
            logger.exception("Gemini API error")
            raise RuntimeError(f"Gemini API error: {str(e)}")

    def get_model_name(self) -> str:
        return self.model


class AIService:
    def __init__(self):
        self.provider_repo = AIProviderRepository()
        self.conv_repo = AIConversationRepository()
        self.msg_repo = AIMessageRepository()
        self._provider_instance = None

    def _get_provider(self) -> BaseAIService:
        if self._provider_instance:
            return self._provider_instance

        provider = self.provider_repo.get_active()
        if not provider:
            raise RuntimeError('Tidak ada provider AI yang aktif')

        if provider.name == 'openai':
            self._provider_instance = OpenAIService(
                api_key=provider.api_key, model=provider.model
            )
        elif provider.name == 'gemini':
            self._provider_instance = GeminiService(
                api_key=provider.api_key, model=provider.model
            )
        else:
            raise RuntimeError(f'Provider AI tidak dikenal: {provider.name}')

        return self._provider_instance

    def _build_messages(self, conversation_id: int, user_message: str, system_context: str = '') -> list:
        messages = []
        if system_context:
            messages.append({'role': 'system', 'content': system_context})

        recent = self.msg_repo.get_last_n(conversation_id, 10)
        for msg in reversed(recent):
            messages.append({'role': msg.role, 'content': msg.content})

        messages.append({'role': 'user', 'content': user_message})
        return messages

    def send_message(self, conversation_id: int, user_id: int, message: str) -> dict:
        try:
            conversation = self.conv_repo.get_by_id(conversation_id)
            if not conversation:
                return {'success': False, 'error': 'Percakapan tidak ditemukan'}
            if conversation.user_id != user_id:
                return {'success': False, 'error': 'Anda tidak memiliki akses ke percakapan ini'}

            self.msg_repo.create(conversation_id, 'user', message)

            system_context = conversation.context
            messages = self._build_messages(conversation_id, message, system_context)

            provider = self._get_provider()
            response_text = provider.chat(messages)

            ai_msg = self.msg_repo.create(
                conversation_id, 'assistant', response_text,
                {'model': provider.get_model_name()}
            )

            self.conv_repo.update(conversation_id)

            return {
                'success': True,
                'message': {
                    'id': ai_msg.id,
                    'role': ai_msg.role,
                    'content': ai_msg.content,
                    'metadata': ai_msg.metadata,
                    'created_at': ai_msg.created_at.isoformat(),
                }
            }
        except RuntimeError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.exception("AI Service error")
            return {'success': False, 'error': 'Terjadi kesalahan saat memproses pesan'}

    def create_conversation(self, user_id: int, title: str, context: str = '') -> dict:
        try:
            conv = self.conv_repo.create(user_id, title, context)
            return {'success': True, 'conversation': conv}
        except Exception as e:
            logger.exception("Failed to create conversation")
            return {'success': False, 'error': str(e)}

    def get_conversation_history(self, conversation_id: int, user_id: int) -> dict:
        conv = self.conv_repo.get_by_id(conversation_id)
        if not conv or conv.user_id != user_id:
            return {'success': False, 'error': 'Percakapan tidak ditemukan'}
        messages = self.msg_repo.get_by_conversation(conversation_id)
        return {'success': True, 'conversation': conv, 'messages': messages}

    def get_user_conversations(self, user_id: int):
        return self.conv_repo.get_by_user(user_id)

    def delete_conversation(self, conversation_id: int, user_id: int) -> dict:
        conv = self.conv_repo.get_by_id(conversation_id)
        if not conv:
            return {'success': False, 'error': 'Percakapan tidak ditemukan'}
        if conv.user_id != user_id:
            return {'success': False, 'error': 'Anda tidak memiliki akses'}
        self.conv_repo.delete(conversation_id)
        return {'success': True}

    def summarize_material(self, text: str) -> dict:
        try:
            provider = self._get_provider()
            messages = [
                {'role': 'system', 'content': 'Buatlah ringkasan dari teks berikut dalam bahasa Indonesia. '
                                              'Sertakan poin-poin penting. Gunakan format yang rapi.'},
                {'role': 'user', 'content': text},
            ]
            summary = provider.chat(messages, max_tokens=1000, temperature=0.3)
            return {'success': True, 'summary': summary}
        except Exception as e:
            logger.exception("Summarization error")
            return {'success': False, 'error': str(e)}

    def get_learning_recommendations(self, user_id: int, interests: str = '') -> dict:
        try:
            provider = self._get_provider()
            messages = [
                {'role': 'system', 'content': 'Kamu adalah asisten akademik yang membantu mahasiswa memilih materi '
                                              'pembelajaran. Berikan rekomendasi belajar berdasarkan minat mereka '
                                              'dalam bahasa Indonesia.'},
                {'role': 'user', 'content': f'Beri saya rekomendasi materi pembelajaran untuk topik: {interests}'},
            ]
            recommendations = provider.chat(messages, max_tokens=1500)
            return {'success': True, 'recommendations': recommendations}
        except Exception as e:
            logger.exception("Recommendation error")
            return {'success': False, 'error': str(e)}

    def ask_question(self, question: str, context: str = '') -> dict:
        try:
            provider = self._get_provider()
            system_msg = 'Kamu adalah asisten akademik yang membantu menjawab pertanyaan seputar perkuliahan.'
            if context:
                system_msg += f'\n\nKonteks:\n{context}'
            messages = [
                {'role': 'system', 'content': system_msg},
                {'role': 'user', 'content': question},
            ]
            answer = provider.chat(messages)
            return {'success': True, 'answer': answer}
        except Exception as e:
            logger.exception("Q&A error")
            return {'success': False, 'error': str(e)}
