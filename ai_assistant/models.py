from django.db import models


class AIProvider(models.Model):
    PROVIDER_CHOICES = (
        ('openai', 'OpenAI'),
        ('gemini', 'Google Gemini'),
    )
    name = models.CharField(max_length=50, choices=PROVIDER_CHOICES, unique=True)
    api_key = models.CharField(max_length=500)
    is_active = models.BooleanField(default=False)
    model = models.CharField(max_length=100, default='gpt-4')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_name_display()} - {self.model}"


class AIConversation(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='ai_conversations')
    title = models.CharField(max_length=200)
    context = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class AIMessage(models.Model):
    ROLE_CHOICES = (('user', 'User'), ('assistant', 'Assistant'), ('system', 'System'))
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:50]}"
