from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login

from .models import UserAuthKeys, UserAuthFails

import hashlib

def login_user(request, username, password, ip=None):
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        if not user.is_active:
            return {
                "result": True,
                "active": False,
                "authkey": None
            }

        authkey = UserAuthKeys.objects.create(user=user, ip=ip)
        authkey.generate()
        return {
            "result": True,
            "active": True,
            "authkey": authkey.get_as_dict()
        }
    else:
        try:
            useraccount = User.objects.get(username=username)
            UserAuthFails.objects.create(user=useraccount, ip=ip)
        except:
            # Just checking so it doesn't create an empty entry in the DB
            if(ip!=None):
                UserAuthFails.objects.create(user=None, ip=ip)
        return {
            "result": False,
            "active": False,
            "authkey": None
        }
            

def gen_auth_key(user, ip=None):
    # TODO maybe check if the user exists
    authkey = UserAuthKeys.objects.create(user=user, ip=ip)
    authkey.generate()
    return {
        "authkey": authkey.get_as_dict()
    }

def get_user_token(user):
    m = hashlib.md5()
    m.update(str(user["id"] + "_" + "todo_colocar + alguma coisa aqui").encode('utf-8'))
    print(m.hexdigest())
    return m.hexdigest()