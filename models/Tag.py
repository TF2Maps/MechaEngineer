# Std Lib Imports
pass

# 3rd Party Imports
from tortoise import Tortoise, fields
from tortoise.models import Model

# Local Imports
pass

class Tag(Model):
    id = fields.IntField(pk=True)
    key = fields.TextField()
    value = fields.CharField(max_length=1024)
    author = fields.CharField(max_length=128)
    date = fields.DatetimeField(null=True)

    def __str__(self):
        return self.key