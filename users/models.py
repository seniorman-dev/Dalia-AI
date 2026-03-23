
# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid





class User(AbstractUser):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True
    )
    account_type = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email'),
            ('google', 'Google'),
        ],
        default='email'
    )
    is_onboarded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Tells Django to use email as the login field
    USERNAME_FIELD = 'email'
    # Remove email from REQUIRED_FIELDS since it's the username
    # fields required when creating a superuser interactively (other than email and password)
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return self.email

    @property
    def display_name(self):
        return self.full_name or self.email.split('@')[0]