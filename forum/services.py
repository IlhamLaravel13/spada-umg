import logging
from .repositories import ForumRepository, ForumTopicRepository, ForumReplyRepository

logger = logging.getLogger(__name__)


class ForumService:
    def __init__(self):
        self.repo = ForumRepository()
        self.topic_repo = ForumTopicRepository()
        self.reply_repo = ForumReplyRepository()

    def get_all(self):
        return self.repo.get_all()

    def get_active(self):
        return self.repo.get_active()

    def get_by_id(self, forum_id: int):
        return self.repo.get_by_id(forum_id)

    def get_by_class(self, class_id: int):
        return self.repo.get_by_class(class_id)

    def get_for_user(self, user):
        return self.repo.get_for_user(user)

    def create(self, **kwargs) -> dict:
        try:
            forum = self.repo.create(**kwargs)
            return {'success': True, 'data': forum}
        except Exception as e:
            logger.exception("Failed to create forum")
            return {'success': False, 'error': str(e)}

    def update(self, forum_id: int, **kwargs) -> dict:
        try:
            forum = self.repo.update(forum_id, **kwargs)
            if forum:
                return {'success': True, 'data': forum}
            return {'success': False, 'error': 'Forum not found'}
        except Exception as e:
            logger.exception("Failed to update forum")
            return {'success': False, 'error': str(e)}

    def delete(self, forum_id: int) -> dict:
        try:
            if self.repo.delete(forum_id):
                return {'success': True, 'message': 'Forum deleted successfully'}
            return {'success': False, 'error': 'Forum not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_topics(self, forum_id: int):
        return self.topic_repo.get_by_forum(forum_id)

    def get_topic_by_id(self, topic_id: int):
        return self.topic_repo.get_by_id(topic_id)

    def create_topic(self, **kwargs) -> dict:
        try:
            topic = self.topic_repo.create(**kwargs)
            return {'success': True, 'data': topic}
        except Exception as e:
            logger.exception("Failed to create topic")
            return {'success': False, 'error': str(e)}

    def update_topic(self, topic_id: int, **kwargs) -> dict:
        try:
            topic = self.topic_repo.update(topic_id, **kwargs)
            if topic:
                return {'success': True, 'data': topic}
            return {'success': False, 'error': 'Topic not found'}
        except Exception as e:
            logger.exception("Failed to update topic")
            return {'success': False, 'error': str(e)}

    def delete_topic(self, topic_id: int) -> dict:
        try:
            if self.topic_repo.delete(topic_id):
                return {'success': True, 'message': 'Topic deleted successfully'}
            return {'success': False, 'error': 'Topic not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def increment_views(self, topic_id: int):
        try:
            self.topic_repo.increment_views(topic_id)
        except Exception:
            pass

    def get_replies(self, topic_id: int):
        return self.reply_repo.get_by_topic(topic_id)

    def get_reply_by_id(self, reply_id: int):
        return self.reply_repo.get_by_id(reply_id)

    def create_reply(self, **kwargs) -> dict:
        try:
            reply = self.reply_repo.create(**kwargs)
            return {'success': True, 'data': reply}
        except Exception as e:
            logger.exception("Failed to create reply")
            return {'success': False, 'error': str(e)}

    def update_reply(self, reply_id: int, **kwargs) -> dict:
        try:
            reply = self.reply_repo.update(reply_id, **kwargs)
            if reply:
                return {'success': True, 'data': reply}
            return {'success': False, 'error': 'Reply not found'}
        except Exception as e:
            logger.exception("Failed to update reply")
            return {'success': False, 'error': str(e)}

    def delete_reply(self, reply_id: int) -> dict:
        try:
            if self.reply_repo.delete(reply_id):
                return {'success': True, 'message': 'Reply deleted successfully'}
            return {'success': False, 'error': 'Reply not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def toggle_like(self, reply_id: int, user) -> dict:
        return self.reply_repo.toggle_like(reply_id, user)

    def mark_as_solution(self, reply_id: int, topic_id: int) -> dict:
        return self.reply_repo.mark_as_solution(reply_id, topic_id)

    def toggle_topic_pin(self, topic_id: int) -> dict:
        topic = self.topic_repo.get_by_id(topic_id)
        if not topic:
            return {'success': False, 'error': 'Topic not found'}
        return self.update_topic(topic_id, is_pinned=not topic.is_pinned)

    def toggle_topic_close(self, topic_id: int) -> dict:
        topic = self.topic_repo.get_by_id(topic_id)
        if not topic:
            return {'success': False, 'error': 'Topic not found'}
        return self.update_topic(topic_id, is_closed=not topic.is_closed)
