from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Skill, SwapRequest, ChatMessage

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )

class SkillSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    teaser_video_url = serializers.SerializerMethodField()

    class Meta:
        model = Skill
        fields = ['id', 'user', 'name', 'description', 'skill_wanted', 'is_active', 'teaser_video_url', 'created_at']

    def get_teaser_video_url(self, obj):
        request = self.context.get('request')
        if obj.teaser_video and request:
            return request.build_absolute_uri(obj.teaser_video.url)
        return None

class SwapRequestSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    to_user_id = serializers.IntegerField(write_only=True)
    skill_offered_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = SwapRequest
        fields = ['id', 'from_user', 'to_user', 'to_user_id', 'skill_offered', 'skill_offered_id', 'skill_wanted_text', 'status', 'created_at']
        read_only_fields = ['status', 'skill_offered', 'from_user', 'to_user']

class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'message', 'image_url', 'timestamp']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if hasattr(obj, 'image') and obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None