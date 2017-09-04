from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .utilities import get_new_big_token, fix_date, get_new_token


# TODO: make it work with other user models
# User = settings.AUTH_USER_MODEL


class UserAuthKeys(models.Model):
    #####
    # Saves the Authentication Keys for Users, to use on remote environments like Mobile and FrontEnd
    #####
    user = models.ForeignKey(User)
    key = models.TextField(max_length=128, unique=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    last_use = models.DateTimeField(auto_now_add=False, auto_now=True)
    expire_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)

    def generate(self):
        self.key = get_new_token()
        self.expire_at = timezone.now() + timedelta(days=14)
        self.save()

    def valid(self):
        if self.expire_at > timezone.now():
            return True
        else:
            return False

    def get_as_dict(self):
        return {
            "key": self.key,
            "ip": self.ip,
            "last_use": str(self.last_use),
            "expire_at": str(self.expire_at),
            "created_at": str(self.created_at)
        }

    class Meta:
        app_label = 'EfficientRest'


class UserAuthFails(models.Model):
    #####
    # Saves the Authentication fails for ips
    #####
    ip = models.GenericIPAddressField(null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)

    def get_as_dict(self):
        return {
            "ip": self.ip,
            "created_at": remove_microseconds(self.created_at)
        }

    class Meta:
        app_label = 'EfficientRest'
