from rest_framework import serializers

from .models import IDO, UserOutOrder, ManuallyCharge, IDOParticipant


class IDOSerializer(serializers.ModelSerializer):
    class Meta:
        model = IDO
        fields = '__all__'


class UserOutOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserOutOrder
        fields = '__all__'


class ManuallyChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManuallyCharge
        fields = '__all__'


class ParticipateIDOSerializer(serializers.Serializer):
    class Meta:
        model = IDOParticipant
        fields = ('ido', 'allocation')
