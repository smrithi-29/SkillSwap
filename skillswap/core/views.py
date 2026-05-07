from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from .models import UserProfile, Skill, SwapRequest, ChatMessage, Review, Notification
from .forms import LoginForm, SignupForm, ProfileForm, SkillForm, ReviewForm, ChatForm


def create_profile_if_missing(user):
    UserProfile.objects.get_or_create(user=user)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                create_profile_if_missing(user)
                if user.is_staff:
                    return redirect('admin_dashboard')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html', {'form': form})


def signup_view(request):
    form = SignupForm()
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
    return render(request, 'signup.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    create_profile_if_missing(request.user)
    my_skills = Skill.objects.filter(user=request.user, is_active=True)
    pending_requests = SwapRequest.objects.filter(to_user=request.user, status='pending').count()
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    recent_activity = SwapRequest.objects.filter(
        Q(from_user=request.user) | Q(to_user=request.user)
    ).order_by('-created_at')[:5]
    return render(request, 'dashboard.html', {
        'my_skills': my_skills,
        'pending_requests': pending_requests,
        'unread_notifications': unread_notifications,
        'recent_activity': recent_activity,
    })


@login_required
def marketplace_view(request):
    query = request.GET.get('q', '')
    skills = Skill.objects.filter(is_active=True).exclude(user=request.user)
    if query:
        skills = skills.filter(Q(name__icontains=query) | Q(description__icontains=query))
    return render(request, 'marketplace.html', {'skills': skills, 'query': query})


@login_required
def profile_view(request):
    create_profile_if_missing(request.user)
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            request.user.first_name = form.cleaned_data.get('first_name', '')
            request.user.last_name = form.cleaned_data.get('last_name', '')
            request.user.save()
            profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        })
    my_skills = Skill.objects.filter(user=request.user, is_active=True)
    reviews = Review.objects.filter(reviewed_user=request.user)
    return render(request, 'profile.html', {'form': form, 'my_skills': my_skills, 'reviews': reviews})


@login_required
def view_profile(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    create_profile_if_missing(other_user)
    skills = Skill.objects.filter(user=other_user, is_active=True)
    reviews = Review.objects.filter(reviewed_user=other_user)
    return render(request, 'view_profile.html', {'other_user': other_user, 'skills': skills, 'reviews': reviews})


@login_required
def post_skill_view(request):
    form = SkillForm()
    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.user = request.user
            skill.save()
            messages.success(request, 'Skill posted successfully!')
            return redirect('marketplace')
    return render(request, 'post_skill.html', {'form': form})


@login_required
def matches_view(request):
    my_skills = Skill.objects.filter(user=request.user, is_active=True)
    my_wanted = [s.skill_wanted.lower() for s in my_skills if s.skill_wanted]
    my_offered = [s.name.lower() for s in my_skills]
    matches = []
    if my_wanted or my_offered:
        other_skills = Skill.objects.filter(is_active=True).exclude(user=request.user)
        for skill in other_skills:
            offered_match = any(w in skill.name.lower() for w in my_wanted)
            wanted_match = any(o in (skill.skill_wanted or '').lower() for o in my_offered)
            if offered_match or wanted_match:
                matches.append(skill)
    return render(request, 'matches.html', {'matches': matches})


@login_required
def chat_list_view(request):
    sent = ChatMessage.objects.filter(sender=request.user).values_list('receiver', flat=True)
    received = ChatMessage.objects.filter(receiver=request.user).values_list('sender', flat=True)
    user_ids = set(list(sent) + list(received))
    chat_users = User.objects.filter(id__in=user_ids)
    return render(request, 'chat_list.html', {'chat_users': chat_users})


@login_required
def chat_view(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    messages_qs = ChatMessage.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).order_by('timestamp')
    form = ChatForm()
    if request.method == 'POST':
        form = ChatForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.receiver = other_user
            msg.save()
            Notification.objects.create(
                user=other_user,
                message=f"New message from {request.user.username}",
                notification_type='new_message'
            )
            return redirect('chat', user_id=user_id)
    return render(request, 'chat.html', {
        'other_user': other_user,
        'messages': messages_qs,
        'form': form,
    })


@login_required
def swap_requests_view(request):
    received = SwapRequest.objects.filter(to_user=request.user).order_by('-created_at')
    sent = SwapRequest.objects.filter(from_user=request.user).order_by('-created_at')
    return render(request, 'swap_requests.html', {'received': received, 'sent': sent})


@login_required
def request_swap(request, skill_id):
    skill = get_object_or_404(Skill, id=skill_id)
    if skill.user == request.user:
        messages.error(request, "You can't request a swap with your own skill.")
        return redirect('marketplace')
    existing = SwapRequest.objects.filter(from_user=request.user, skill_offered__user=request.user, to_user=skill.user, status='pending')
    if existing.exists():
        messages.warning(request, 'You already have a pending request for this user.')
        return redirect('marketplace')
    my_skills = Skill.objects.filter(user=request.user, is_active=True)
    if not my_skills.exists():
        messages.error(request, 'You need to post a skill first before requesting a swap.')
        return redirect('post_skill')
    SwapRequest.objects.create(
        from_user=request.user,
        to_user=skill.user,
        skill_offered=my_skills.first(),
        skill_wanted_text=skill.name,
        status='pending'
    )
    Notification.objects.create(
        user=skill.user,
        message=f"{request.user.username} wants to swap skills with you!",
        notification_type='new_request'
    )
    messages.success(request, f'Swap request sent to {skill.user.username}!')
    return redirect('swap_requests')


@login_required
def accept_swap(request, request_id):
    swap = get_object_or_404(SwapRequest, id=request_id, to_user=request.user)
    swap.status = 'accepted'
    swap.save()
    Notification.objects.create(
        user=swap.from_user,
        message=f"{request.user.username} accepted your swap request!",
        notification_type='swap_accepted'
    )
    messages.success(request, 'Swap request accepted!')
    return redirect('swap_requests')


@login_required
def reject_swap(request, request_id):
    swap = get_object_or_404(SwapRequest, id=request_id, to_user=request.user)
    swap.status = 'rejected'
    swap.save()
    Notification.objects.create(
        user=swap.from_user,
        message=f"{request.user.username} rejected your swap request.",
        notification_type='swap_rejected'
    )
    messages.warning(request, 'Swap request rejected.')
    return redirect('swap_requests')


@login_required
def reviews_view(request):
    received_reviews = Review.objects.filter(reviewed_user=request.user)
    given_reviews = Review.objects.filter(reviewer=request.user)
    accepted_swaps = SwapRequest.objects.filter(
        (Q(from_user=request.user) | Q(to_user=request.user)),
        status='accepted'
    )
    reviewable_users = []
    for swap in accepted_swaps:
        other = swap.to_user if swap.from_user == request.user else swap.from_user
        already_reviewed = Review.objects.filter(reviewer=request.user, reviewed_user=other).exists()
        if not already_reviewed and other not in reviewable_users:
            reviewable_users.append(other)
    return render(request, 'reviews.html', {
        'received_reviews': received_reviews,
        'given_reviews': given_reviews,
        'reviewable_users': reviewable_users,
    })


@login_required
def submit_review(request, user_id):
    reviewed_user = get_object_or_404(User, id=user_id)
    if reviewed_user == request.user:
        messages.error(request, "You can't review yourself.")
        return redirect('reviews')
    existing = Review.objects.filter(reviewer=request.user, reviewed_user=reviewed_user)
    if existing.exists():
        messages.warning(request, 'You have already reviewed this user.')
        return redirect('reviews')
    form = ReviewForm()
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = request.user
            review.reviewed_user = reviewed_user
            review.save()
            Notification.objects.create(
                user=reviewed_user,
                message=f"{request.user.username} left you a {review.rating}-star review!",
                notification_type='new_review'
            )
            messages.success(request, 'Review submitted!')
            return redirect('reviews')
    return render(request, 'submit_review.html', {'form': form, 'reviewed_user': reviewed_user})


@login_required
def notifications_view(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications.html', {'notifications': notifs})


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def admin_dashboard(request):
    total_users = User.objects.count()
    total_skills = Skill.objects.count()
    active_swaps = SwapRequest.objects.filter(status='accepted').count()
    pending_requests = SwapRequest.objects.filter(status='pending').count()
    return render(request, 'admin_panel/dashboard.html', {
        'total_users': total_users,
        'total_skills': total_skills,
        'active_swaps': active_swaps,
        'pending_requests': pending_requests,
    })


@admin_required
def admin_users(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin_panel/users.html', {'users': users})


@admin_required
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if not user.is_superuser:
        user.delete()
        messages.success(request, 'User deleted.')
    else:
        messages.error(request, 'Cannot delete superuser.')
    return redirect('admin_users')


@admin_required
def admin_skills(request):
    skills = Skill.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/skills.html', {'skills': skills})


@admin_required
def admin_delete_skill(request, skill_id):
    skill = get_object_or_404(Skill, id=skill_id)
    skill.delete()
    messages.success(request, 'Skill removed.')
    return redirect('admin_skills')


@admin_required
def admin_requests(request):
    swap_requests = SwapRequest.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/requests.html', {'swap_requests': swap_requests})


@admin_required
def admin_approve_request(request, request_id):
    swap = get_object_or_404(SwapRequest, id=request_id)
    swap.status = 'accepted'
    swap.save()
    messages.success(request, 'Request approved.')
    return redirect('admin_requests')


@admin_required
def admin_reject_request(request, request_id):
    swap = get_object_or_404(SwapRequest, id=request_id)
    swap.status = 'rejected'
    swap.save()
    messages.warning(request, 'Request rejected.')
    return redirect('admin_requests')


@admin_required
def admin_reports(request):
    flagged_skills = Skill.objects.filter(is_active=False)
    recent_swaps = SwapRequest.objects.order_by('-created_at')[:10]
    return render(request, 'admin_panel/reports.html', {
        'flagged_skills': flagged_skills,
        'recent_swaps': recent_swaps,
    })
