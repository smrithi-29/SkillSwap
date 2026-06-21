from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.db.models import Q
from .models import Skill, SwapRequest, ChatMessage, Review, Notification, UserProfile, TeaserView
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


# PATCH /api/swaps/<id>/accept/
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def api_swap_accept(request, swap_id):
    try:
        swap = SwapRequest.objects.get(id=swap_id, to_user=request.user)
    except SwapRequest.DoesNotExist:
        return Response({'error': 'Swap not found.'}, status=404)
    swap.status = 'accepted'
    swap.save()
    return Response({'message': 'Swap accepted.'})

# PATCH /api/swaps/<id>/reject/
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def api_swap_reject(request, swap_id):
    try:
        swap = SwapRequest.objects.get(id=swap_id, to_user=request.user)
    except SwapRequest.DoesNotExist:
        return Response({'error': 'Swap not found.'}, status=404)
    swap.status = 'rejected'
    swap.save()
    return Response({'message': 'Swap rejected.'})



# GET /api/profile/
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_profile(request):
    user = request.user
    try:
        profile = user.profile
        bio = profile.bio
        phone = profile.phone
    except:
        bio = ''
        phone = ''
    skills = Skill.objects.filter(user=user, is_active=True)
    reviews = Review.objects.filter(reviewed_user=user)
    avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0
    return Response({
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'bio': bio,
        'phone': phone,
        'skill_count': skills.count(),
        'review_count': reviews.count(),
        'avg_rating': round(avg_rating, 1),
    })

# GET /api/notifications/
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_notifications(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')[:20]
    data = [{'id': n.id, 'message': n.message, 'type': n.notification_type,
             'is_read': n.is_read, 'created_at': str(n.created_at)} for n in notifs]
    return Response(data)

# POST /api/notifications/<id>/read/
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_notification_read(request, notif_id):
    try:
        notif = Notification.objects.get(id=notif_id, user=request.user)
        notif.is_read = True
        notif.save()
        return Response({'message': 'Marked as read.'})
    except Notification.DoesNotExist:
        return Response({'error': 'Not found.'}, status=404)

# GET /api/reviews/<user_id>/
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_reviews(request, user_id):
    reviews = Review.objects.filter(reviewed_user__id=user_id).order_by('-created_at')
    data = [{'id': r.id, 'reviewer': r.reviewer.username, 'rating': r.rating,
             'comment': r.comment, 'created_at': str(r.created_at)} for r in reviews]
    return Response(data)


# GET /api/skills/<skill_id>/
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_skill_detail(request, skill_id):
    skill = get_object_or_404(Skill, id=skill_id)
    has_viewed = TeaserView.objects.filter(user=request.user, skill=skill).exists()
    is_unlocked = SwapRequest.objects.filter(
        Q(from_user=request.user, to_user=skill.user) |
        Q(from_user=skill.user, to_user=request.user),
        status='accepted'
    ).exists()
    teaser_url = request.build_absolute_uri(skill.teaser_video.url) if skill.teaser_video else None
    return Response({
        'id': skill.id,
        'name': skill.name,
        'description': skill.description,
        'skill_wanted': skill.skill_wanted,
        'user_id': skill.user.id,
        'user_username': skill.user.username,
        'teaser_video': teaser_url,
        'has_viewed_teaser': has_viewed,
        'is_unlocked': is_unlocked,
    })


# POST /api/teaser-view/<skill_id>/
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_record_teaser_view(request, skill_id):
    skill = get_object_or_404(Skill, id=skill_id)
    TeaserView.objects.get_or_create(user=request.user, skill=skill)
    return Response({'status': 'recorded'})


# GET /api/matches/
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_matches(request):
    my_skills = Skill.objects.filter(user=request.user, is_active=True)
    my_offered = [s.name.lower() for s in my_skills]
    my_wanted = [s.skill_wanted.lower() for s in my_skills if s.skill_wanted]
    other_skills = Skill.objects.filter(is_active=True).exclude(user=request.user)
    matches = []
    for skill in other_skills:
        match_score = 0
        if skill.name.lower() in my_wanted:
            match_score += 2
        if skill.skill_wanted and skill.skill_wanted.lower() in my_offered:
            match_score += 2
        for offered in my_offered:
            if offered in skill.name.lower():
                match_score += 1
        if match_score > 0:
            matches.append({
                'id': skill.id,
                'name': skill.name,
                'description': skill.description,
                'skill_wanted': skill.skill_wanted,
                'user_id': skill.user.id,
                'user_username': skill.user.username,
                'match_score': match_score,
            })
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    return Response(matches[:20])


# POST /api/reviews/submit/<user_id>/
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_submit_review(request, user_id):
    try:
        reviewed_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)
    if reviewed_user == request.user:
        return Response({'error': 'Cannot review yourself.'}, status=400)
    rating = request.data.get('rating')
    comment = request.data.get('comment', '')
    if not rating or int(rating) not in range(1, 6):
        return Response({'error': 'Rating must be 1-5.'}, status=400)
    review, created = Review.objects.get_or_create(
        reviewer=request.user,
        reviewed_user=reviewed_user,
        defaults={'rating': int(rating), 'comment': comment}
    )
    if not created:
        review.rating = int(rating)
        review.comment = comment
        review.save()
    return Response({'message': 'Review submitted!'}, status=201)

    
# GET /api/user/<user_id>/
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_user_profile(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)
    try:
        bio = user.profile.bio
    except:
        bio = ''
    skills = Skill.objects.filter(user=user, is_active=True)
    reviews = Review.objects.filter(reviewed_user=user)
    avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0
    return Response({
        'user_id': user.id,
        'username': user.username,
        'bio': bio,
        'skill_count': skills.count(),
        'review_count': reviews.count(),
        'avg_rating': round(avg_rating, 1),
    })