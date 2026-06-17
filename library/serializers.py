from rest_framework import serializers
from .models import LibraryItem, LibraryCategory


class LibraryCategorySerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = LibraryCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'is_active', 'item_count']

    def get_item_count(self, obj):
        if hasattr(obj, 'item_count'):
            return obj.item_count
        return obj.libraryitem_set.filter(is_published=True).count()


class LibraryItemSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    faculty_name = serializers.SerializerMethodField()
    study_program_name = serializers.SerializerMethodField()
    uploaded_by_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()
    type_label = serializers.SerializerMethodField()

    class Meta:
        model = LibraryItem
        fields = [
            'id', 'title', 'author', 'description', 'item_type', 'type_label',
            'category', 'category_name', 'faculty', 'faculty_name',
            'study_program', 'study_program_name', 'file', 'file_url',
            'cover_image', 'cover_url', 'publisher', 'publication_year',
            'isbn', 'pages', 'language', 'tags', 'download_count', 'view_count',
            'is_published', 'uploaded_by', 'uploaded_by_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'download_count', 'view_count', 'created_at', 'updated_at']

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_faculty_name(self, obj):
        return obj.faculty.name if obj.faculty else None

    def get_study_program_name(self, obj):
        return obj.study_program.name if obj.study_program else None

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
        return None

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None

    def get_cover_url(self, obj):
        if obj.cover_image:
            return obj.cover_image.url
        return None

    def get_type_label(self, obj):
        return dict(LibraryItem.TYPE_CHOICES).get(obj.item_type, obj.item_type)


class LibraryItemUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibraryItem
        fields = [
            'title', 'author', 'description', 'item_type', 'category',
            'faculty', 'study_program', 'file', 'cover_image', 'publisher',
            'publication_year', 'isbn', 'pages', 'language', 'tags',
        ]

    def validate_file(self, value):
        max_size = 100 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError('Ukuran file maksimal 100MB')
        return value
