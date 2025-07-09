import datetime
import environ
import jwt
import pytz
import requests

from jose import jwt as jose_jwt
from jose.utils import base64url_decode
import requests

from jwt import PyJWKClient
from api.models import CustomUser as User
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

env = environ.Env()

CLERK_API_URL = "https://api.clerk.com/v1"
CLERK_FRONTEND_API_URL = env("CLERK_FRONTEND_API_URL").rstrip("/")
CLERK_SECRET_KEY = env("CLERK_SECRET_KEY")


class JWTAuthenticationMiddleware(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            raise AuthenticationFailed("Bearer token not provided.")

        user = self.decode_jwt(token)
        clerk = ClerkSDK()
        info, found = clerk.fetch_user_info(user.username)

        if not user:
            return None

        if found:
            user.email = info["email_address"]
            user.first_name = info["first_name"]
            user.last_name = info["last_name"]
            user.last_login = info["last_login"]
            user.save()

        return user, None

    def decode_jwt(self, token):
        jwks_url = f"{CLERK_FRONTEND_API_URL}/.well-known/jwks.json"
        jwks = requests.get(jwks_url).json()
        header = jose_jwt.get_unverified_header(token)

        key = next((k for k in jwks["keys"] if k["kid"] == header["kid"]), None)
        if not key:
            raise AuthenticationFailed("Public key not found.")

        payload = jose_jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        options={"verify_aud": False},
        leeway=5  # allow 5 seconds of skew
        )

        user_id = payload.get("sub")
        if user_id:
            user, _ = User.objects.get_or_create(username=user_id)
            return user
        return None


class ClerkSDK:
    def fetch_user_info(self, user_id: str):
        response = requests.get(
            f"{CLERK_API_URL}/users/{user_id}",
            headers={"Authorization": f"Bearer {CLERK_SECRET_KEY}"},
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "email_address": data["email_addresses"][0]["email_address"],
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "last_login": datetime.datetime.fromtimestamp(
                    data["last_sign_in_at"] / 1000, tz=pytz.UTC
                ),
            }, True
        else:
            return {
                "email_address": "",
                "first_name": "",
                "last_name": "",
                "last_login": None,
            }, False