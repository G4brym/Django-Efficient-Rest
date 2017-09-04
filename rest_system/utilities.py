import uuid
import datetime as dt
from django.utils.dateparse import parse_datetime

def get_new_token():
    return str(str(uuid.uuid4()) + str(uuid.uuid4())).replace("-", "")[:64]

def get_new_big_token():
    return str(str(uuid.uuid4()) + str(uuid.uuid4()) + str(uuid.uuid4()) + str(uuid.uuid4())).replace("-", "")[:128]

def fix_date(datetime):
    return dt.datetime.strptime((str(datetime)), "%Y-%m-%d %H:%M:%S.%f")