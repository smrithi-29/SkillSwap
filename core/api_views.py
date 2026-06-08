from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.db.models import Q
from .models import Skill, SwapRequest, ChatMessage
from .serializers import (
    SignupSerializer, SkillSerializer,
    SwapRequestSerializer, ChatMessageSerializer
)

# POST /api/auth/login/
@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    if not username or not password:
        return Response({'error': 'Username and password required.'}, status=400)
    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid credentials.'}, status=401)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'is_staff': user.is_staff,
    })

# POST /api/auth/signup/
@api_view(['POST'])
@permission_classes([AllowAny])
def api_signup(request):
    serializer = SignupSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user_id': user.id, 'username': user.username}, status=201)
    return Response(serializer.errors, status=400)

# GET /api/skills/
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_skills_list(request):
    skills = Skill.objects.filter(is_active=True).exclude(user=request.user)
    q = request.query_params.get('q', '')
    if q:
        skills = skills.filter(Q(name__icontains=q) | Q(description__icontains=q))
    serializer = SkillSerializer(skills, many=True, context={'request': request})
    return Response(serializer.data)

# POST /api/skills/
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_skills_create(request):
    serializer = SkillSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

# GET /api/swaps/
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_swaps_list(request):
    swaps = SwapRequest.objects.filter(
        Q(from_user=request.user) | Q(to_user=request.user)
    ).order_by('-created_at')
    serializer = SwapRequestSerializer(swaps, many=True)
    return Response(serializer.data)

# POST /api/swaps/
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_swaps_create(request):
    to_user_id = request.data.get('to_user_id')
    skill_offered_id = request.data.get('skill_offered_id')
    skill_wanted_text = request.data.get('skill_wanted_text', '')
    if not to_user_id or not skill_offered_id:
        return Response({'error': 'to_user_id and skill_offered_id are required.'}, status=400)
    try:
        to_user = User.objects.get(id=to_user_id)
        skill_offered = Skill.objects.get(id=skill_offered_id, user=request.user)
    except (User.DoesNotExist, Skill.DoesNotExist):
        return Response({'error': 'Invalid user or skill.'}, status=404)
    swap = SwapRequest.objects.create(
        from_user=request.user,
        to_user=to_user,
        skill_offered=skill_offered,
        skill_wanted_text=skill_wanted_text,
        status='pending'
    )
    serializer = SwapRequestSerializer(swap)
    return Response(serializer.data, status=201)

# GET /api/chat/<user_id>/
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_chat(request, user_id):
    try:
        other_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)
    messages_qs = ChatMessage.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by('timestamp')
    serializer = ChatMessageSerializer(messages_qs, many=True, context={'request': request})
    return Response(serializer.data)

# POST /api/chat/<user_id>/
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_chat_send(request, user_id):
    try:
        other_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)
    msg_text = request.data.get('message', '')
    if not msg_text:
        return Response({'error': 'Message cannot be empty.'}, status=400)
    msg = ChatMessage.objects.create(
        sender=request.user,
        receiver=other_user,
        message=msg_text
    )
    serializer = ChatMessageSerializer(msg, context={'request': request})
    return Response(serializer.data, status=201)