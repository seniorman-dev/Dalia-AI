#/backends.py

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from requests import Request
from django.core.mail import send_mail
import logging




User = get_user_model()
logger = logging.getLogger(__name__)

class EmailBackend(BaseBackend):
    def authenticate(self, request: Request, email:str=None, password:str=None, **kwargs) -> None:
        print("[DEBUG] Custom EmailBackend called")
        try:
            user = User.objects.get(email=email)
            print("[DEBUG] EmailBackend called with:", email)
        except User.DoesNotExist:
            return None
        
        if user.check_password(password):
            print("[DEBUG] EmailBackend called with:", email)
            return user
        
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


def send_email_to_user(user_id: str, content: str):
    try:
        user = User.objects.select_related().get(id=user_id,)
        send_mail(
            subject=f"Hello, {user.get_short_name()}.", 
            message=content,
            from_email="noreply@dalia.com", 
            recipient_list=[f'{user.email}']
        )
        ##logger.info(f"Sent async task email to {user.email}. Thanks to celery!")

    except User.DoesNotExist:
        pass

