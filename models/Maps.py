# Std Lib Imports
from datetime import datetime

# 3rd Party Imports
from tortoise import fields
from tortoise.models import Model

# Local Imports
pass


class Maps(Model):
    id = fields.IntField(pk=True)
    discord_user_handle = fields.CharField(max_length=50)
    discord_user_id = fields.IntField()
    map = fields.CharField(max_length=50)
    url = fields.CharField(max_length=255)
    notes = fields.TextField(null=True)
    status = fields.CharField(max_length=50)
    added = fields.DatetimeField(default=datetime.now())
    played = fields.DatetimeField(null=True)
