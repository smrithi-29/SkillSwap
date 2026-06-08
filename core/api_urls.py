from django.urls import path
from . import api_views

urlpatterns = [
    path('auth/login/', api_views.api_login, name='api_login'),
    path('auth/signup/', api_views.api_signup, name='api_signup'),
    path('skills/', api_views.api_skills_list, name='api_skills_list'),
    path('skills/create/', api_views.api_skills_create, name='api_skills_create'),
    path('swaps/', api_views.api_swaps_list, name='api_swaps_list'),
    path('swaps/create/', api_views.api_swaps_create, name='api_swaps_create'),
    path('chat/<int:user_id>/', api_views.api_chat, name='api_chat'),
    path('chat/<int:user_id>/send/', api_views.api_chat_send, name='api_chat_send'),
]