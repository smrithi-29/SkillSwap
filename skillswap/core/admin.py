from django.contrib import admin
from .models import UserProfile, Skill, SwapRequest, ChatMessage, Review, Notification

admin.site.register(UserProfile)
admin.site.register(Skill)
admin.site.register(SwapRequest)
admin.site.register(ChatMessage)
admin.site.register(Review)
admin.site.register(Notification)
