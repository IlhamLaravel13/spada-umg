from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UserSession


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    role_display = serializers.SerializerMethodField()
    faculty_name = serializers.SerializerMethodField()
    study_program_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'role', 'role_display',
            'full_name', 'first_name', 'last_name', 'nim', 'nidn', 'nip',
            'phone', 'avatar', 'bio', 'faculty', 'faculty_name',
            'study_program', 'study_program_name', 'enrollment_year',
            'is_verified', 'is_active', 'theme_preference',
            'email_notifications', 'last_activity', 'date_joined',
        ]
        read_only_fields = ['id', 'is_verified', 'last_activity', 'date_joined']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_role_display(self, obj):
        return obj.get_role_display()

    def get_faculty_name(self, obj):
        return obj.faculty.name if obj.faculty else None

    def get_study_program_name(self, obj):
        return obj.study_program.name if obj.study_program else None


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=['mahasiswa', 'dosen'])
    nim = serializers.CharField(max_length=20, required=False, allow_null=True)
    nidn = serializers.CharField(max_length=20, required=False, allow_null=True)
    nip = serializers.CharField(max_length=20, required=False, allow_null=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username sudah digunakan.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email sudah terdaftar.')
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password2': 'Password tidak cocok.'})
        if data['role'] == 'mahasiswa' and not data.get('nim'):
            raise serializers.ValidationError({'nim': 'NIM wajib diisi untuk mahasiswa.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        role = validated_data.pop('role')
        password = validated_data.pop('password')
        user = User(**validated_data, role=role)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(label='NIM/NIDN/NIP/Email/Username')
    password = serializers.CharField(write_only=True)
    remember_me = serializers.BooleanField(required=False, default=False)

    def validate(self, data):
        identifier = data.get('identifier')
        password = data.get('password')

        if not identifier or not password:
            raise serializers.ValidationError('Silakan isi semua field.')

        user = None
        try:
            if '@' in identifier and '.' in identifier:
                user = User.objects.get(email=identifier)
            else:
                user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(nim=identifier)
            except User.DoesNotExist:
                try:
                    user = User.objects.get(nidn=identifier)
                except User.DoesNotExist:
                    try:
                        user = User.objects.get(nip=identifier)
                    except User.DoesNotExist:
                        pass

        if user is None:
            raise serializers.ValidationError('User tidak ditemukan.')

        auth_user = authenticate(username=user.username, password=password)
        if auth_user is None:
            raise serializers.ValidationError('Password salah.')

        if not auth_user.is_active:
            raise serializers.ValidationError('Akun tidak aktif.')

        data['user'] = auth_user
        return data


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'bio', 'avatar',
            'faculty', 'study_program', 'enrollment_year',
            'theme_preference', 'email_notifications',
        ]

    def validate_phone(self, value):
        if value and not value.isdigit() and not value.startswith('+'):
            raise serializers.ValidationError('Nomor telepon tidak valid.')
        return value


class UserSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSession
        fields = ['id', 'ip_address', 'user_agent', 'is_active', 'last_activity', 'created_at']
        read_only_fields = ['id', 'ip_address', 'user_agent', 'last_activity', 'created_at']
