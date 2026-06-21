from django.urls import path
from .api_views import (
    api_login, api_signup,
    api_skills_list, api_skills_create, api_skill_detail,
    api_swaps_list, api_swaps_create, api_swap_accept, api_swap_reject,
    api_chat, api_chat_send,
    api_profile, api_user_profile,
    api_notifications, api_notification_read,
    api_reviews, api_submit_review,
    api_record_teaser_view, api_matches,
)

urlpatterns = [
    path('auth/login/', api_login, name='api_login'),
    path('auth/signup/', api_signup, name='api_signup'),
    path('skills/', api_skills_list, name='api_skills_list'),
    path('skills/create/', api_skills_create, name='api_skills_create'),
    path('skills/<int:skill_id>/', api_skill_detail, name='api_skill_detail'),
    path('swaps/', api_swaps_list, name='api_swaps_list'),
    path('swaps/create/', api_swaps_create, name='api_swaps_create'),
    path('swaps/<int:swap_id>/accept/', api_swap_accept, name='api_swap_accept'),
    path('swaps/<int:swap_id>/reject/', api_swap_reject, name='api_swap_reject'),
    path('chat/<int:user_id>/', api_chat, name='api_chat'),
    path('chat/<int:user_id>/send/', api_chat_send, name='api_chat_send'),
    path('profile/', api_profile, name='api_profile'),
    path('user/<int:user_id>/', api_user_profile, name='api_user_profile'),
    path('notifications/', api_notifications, name='api_notifications'),
    path('notifications/<int:notif_id>/read/', api_notification_read, name='api_notification_read'),
    path('reviews/<int:user_id>/', api_reviews, name='api_reviews'),
    path('reviews/submit/<int:user_id>/', api_submit_review, name='api_submit_review'),
    path('teaser-view/<int:skill_id>/', api_record_teaser_view, name='api_record_teaser_view'),
    path('matches/', api_matches, name='api_matches'),
]