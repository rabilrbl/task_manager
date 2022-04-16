# serializers.py in the users Django app
from django.db import transaction
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
from django.contrib.auth  import get_user_model

User = get_user_model()


class CustomRegisterSerializer(RegisterSerializer):
    name = serializers.CharField(max_length=255, required=False)

    # Define transaction.atomic to rollback the save operation in case of error
    @transaction.atomic
    def save(self, request):
        user = super().save(request)
        user.name = self.data.get('name')
        user.save()
        return user

class CustomUserDetailsSerializer(UserDetailsSerializer):

    class Meta:
        extra_fields = []
        if hasattr(User, 'USERNAME_FIELD'):
            extra_fields.append(User.USERNAME_FIELD)
        if hasattr(User, 'EMAIL_FIELD'):
            extra_fields.append(User.EMAIL_FIELD)
        if hasattr(User, 'name'):
            extra_fields.append('name')
        model = User
        fields = ('pk', *extra_fields)
        read_only_fields = ('email',)