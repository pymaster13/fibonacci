from audioop import add
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from rest_framework import serializers

from .models import News


User = get_user_model()


class NewsDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = '__all__'
