import datetime
import environ
import jwt
import pytz
import requests
import time
from typing import Dict, Optional

from jose import jwt as jose_jwt
from jose.utils import base64url_decode
import requests

from jwt import PyJWKClient
from api.models import CustomUser as User
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from jose.exceptions import ExpiredSignatureError, JWTError

env = environ.Env()

CLERK_API_URL = "https://api.clerk.com/v1"
CLERK_FRONTEND_API_URL = env("CLERK_FRONTEND_API_URL")
CLERK_SECRET_KEY = env("CLERK_SECRET_KEY")

# JWKS cache
_jwks_cache: Dict = {}
_jwks_cache_time: float = 0
JWKS_CACHE_TTL = 300  # 5 minutes


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
        jwks = self._get_jwks()
        header = jose_jwt.get_unverified_header(token)

        key = next((k for k in jwks["keys"] if k["kid"] == header["kid"]), None)
        if not key:
            # Force refresh JWKS and try once more
            jwks = self._get_jwks(force_refresh=True)
            key = next((k for k in jwks["keys"] if k["kid"] == header["kid"]), None)
            if not key:
                raise AuthenticationFailed(f"Public key not found for kid: {header['kid']}")

        try:
            payload = jose_jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                options={
                    "verify_aud": False
                },  # Clerk tokens don't include aud by default
            )
        except ExpiredSignatureError:
            raise AuthenticationFailed("JWT token has expired.")
        except JWTError:
            raise AuthenticationFailed("Invalid JWT token.")

        user_id = payload.get("sub")
        if user_id:
            user, _ = User.objects.get_or_create(username=user_id)
            return user

        raise AuthenticationFailed("User ID not found in token.")

    def _get_jwks(self, force_refresh: bool = False) -> Dict:
        """Get JWKS with caching and automatic refresh."""
        global _jwks_cache, _jwks_cache_time
        
        current_time = time.time()
        
        # Return cached JWKS if valid and not forcing refresh
        if not force_refresh and _jwks_cache and (current_time - _jwks_cache_time) < JWKS_CACHE_TTL:
            return _jwks_cache
        
        # Fetch fresh JWKS
        jwks_url = f"{CLERK_FRONTEND_API_URL}/.well-known/jwks.json"
        try:
            response = requests.get(jwks_url, timeout=10)
            response.raise_for_status()
            jwks = response.json()
            
            # Update cache
            _jwks_cache = jwks
            _jwks_cache_time = current_time
            
            return jwks
        except requests.RequestException as e:
            if _jwks_cache:  # Fallback to cached version if available
                return _jwks_cache
            raise AuthenticationFailed(f"Failed to fetch JWKS: {str(e)}")


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


class QueryCountMiddleware:
    """Adds X-Query-Count header in DEBUG and logs high query counts to help detect N+1 issues."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.conf import settings
        from django.db import connection

        if not getattr(settings, "DEBUG", False):
            return self.get_response(request)

        start = len(connection.queries)
        response = self.get_response(request)
        total = len(connection.queries) - start
        try:
            response["X-Query-Count"] = str(total)
        except Exception:
            # Non-standard responses may not support headers
            pass
        if total > 50:
            print(
                f"[QueryCountMiddleware] {request.method} {request.path} -> {total} queries (possible N+1)"
            )
        return response
