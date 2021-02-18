from rest_framework import authentication
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from my_auth.models import MyUser
from rest_framework import exceptions


class ExampleAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        token_key = request.GET.get('token')
        if not token_key:
            return None
        try:
            user = Token.objects.get(key=token_key).user
        except Exception:
            raise exceptions.AuthenticationFailed('No such user')

        return user, None
