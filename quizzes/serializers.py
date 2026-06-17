from rest_framework import serializers
from .models import Quiz, QuizQuestion, QuizAnswer, QuizAttempt, QuizResponse


class QuizAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAnswer
        fields = '__all__'
        read_only_fields = ['id']


class QuizQuestionSerializer(serializers.ModelSerializer):
    answers = QuizAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = QuizQuestion
        fields = '__all__'
        read_only_fields = ['id']


class QuizQuestionCreateSerializer(serializers.ModelSerializer):
    answers = QuizAnswerSerializer(many=True, required=False)

    class Meta:
        model = QuizQuestion
        fields = ['quiz', 'question_text', 'question_type', 'points', 'order', 'answers']

    def create(self, validated_data):
        answers_data = validated_data.pop('answers', [])
        question = QuizQuestion.objects.create(**validated_data)
        for answer_data in answers_data:
            QuizAnswer.objects.create(question=question, **answer_data)
        return question


class QuizSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()
    total_points = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    attempt_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_question_count(self, obj):
        return obj.questions.count()

    def get_total_points(self, obj):
        return obj.questions.aggregate(total=serializers.model.models.Sum('points'))['total'] or 0

    def get_class_name(self, obj):
        return str(obj.class_meta) if obj.class_meta else None

    def get_created_by_name(self, obj):
        return str(obj.created_by) if obj.created_by else None

    def get_attempt_count(self, obj):
        return obj.attempts.count()


class QuizAttemptSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    quiz_title = serializers.SerializerMethodField()

    class Meta:
        model = QuizAttempt
        fields = '__all__'
        read_only_fields = ['id', 'started_at']

    def get_student_name(self, obj):
        return str(obj.student) if obj.student else None

    def get_quiz_title(self, obj):
        return obj.quiz.title if obj.quiz else None


class QuizResponseSerializer(serializers.ModelSerializer):
    question_text = serializers.SerializerMethodField()
    correct_answer_text = serializers.SerializerMethodField()

    class Meta:
        model = QuizResponse
        fields = '__all__'
        read_only_fields = ['id']

    def get_question_text(self, obj):
        return obj.question.question_text if obj.question else None

    def get_correct_answer_text(self, obj):
        if obj.question and obj.question.question_type != 'essay':
            correct = obj.question.answers.filter(is_correct=True).first()
            return correct.answer_text if correct else None
        return None


class QuizResultSerializer(serializers.ModelSerializer):
    responses = QuizResponseSerializer(many=True, read_only=True)
    quiz_title = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    correct_count = serializers.SerializerMethodField()

    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz_title', 'score', 'is_passed', 'started_at', 'completed_at',
                  'total_questions', 'correct_count', 'responses']

    def get_quiz_title(self, obj):
        return obj.quiz.title if obj.quiz else None

    def get_total_questions(self, obj):
        return obj.quiz.questions.count() if obj.quiz else 0

    def get_correct_count(self, obj):
        return obj.responses.filter(is_correct=True).count()
