from rest_framework import serializers
from django.contrib.auth.models import User

class SignupSerializer(serializers.ModelSerializer):
    
    # user type 
    auth = serializers.ChoiceField(
        choices=['admin', 'user'],
        write_only=True
    )

    class Meta:
        model = User
        fields = ('auth', 'username', 'password')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        auth = validated_data.pop('auth')

        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )

        if auth == 'admin':
            user.is_staff = True
            user.is_superuser = True
            user.save()

        return user