from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import News


User = get_user_model()


class NewsDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = '__all__'
