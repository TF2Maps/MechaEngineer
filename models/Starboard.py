# Std Lib Imports
from datetime import datetime

# 3rd Party Imports
from tortoise import fields
from tortoise.models import Model

# Local Imports
pass


class Starboard(Model):
    id = fields.IntField(pk=True)

    message_id = fields.IntField()
    message_author_id = fields.IntField()
    reaction_author_id = fields.IntField()
    reaction_emoji = fields.CharField(max_length=256)
