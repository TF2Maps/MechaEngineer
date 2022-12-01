# Std Lib Imports
from datetime import datetime

# 3rd Party Imports
from tortoise import fields
from tortoise.models import Model

# Local Imports
pass

"""
+-----------+--------------+-------------------+--------------+-------------------+---------------------+---------------------+
| verify_id | verifier_uid | verifier_username | verified_uid | verified_username | verified_steam_link | verified_steam_id64 |
+-----------+--------------+-------------------+--------------+-------------------+---------------------+---------------------+
    PK INT          INT             varchar255      int             varchar255          varchar255              varchar255
+-----------+--------------+-------------------+--------------+-------------------+---------------------+---------------------+

create table verification (
  verify_id int AUTO_INCREMENT PRIMARY KEY,
  verifier_uid bigint,
  verifier_username VARCHAR(255),
  verified_uid bigint,
  verified_username VARCHAR(255),
  verified_steam_link VARCHAR(255),
  verified_steam_id64 VARCHAR(255),
  time_verified datetime,
  overridden bool
);
"""

class VerificationDB(Model):
    verify_id = fields.IntField(pk=True)
    verifier_uid = fields.IntField()
    verifier_username = fields.CharField(max_length=255)
    verified_uid = fields.IntField()
    verified_username = fields.CharField(max_length=255)
    verified_steam_link = fields.CharField(max_length=255)
    verified_steam_id64 = fields.CharField(max_length=255)
    time_verified = fields.DatetimeField(default=datetime.now())
    overridden = fields.BooleanField()