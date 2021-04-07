# Std Lib Imports
from datetime import datetime
import asyncio

# 3rd Party Imports
import databases
import orm
import sqlalchemy

# Local Imports
from utils import load_config

config = load_config()


class Maps(orm.Model):
    __tablename__ = "maps"
    __metadata__ = sqlalchemy.MetaData()
    __database__ =  databases.Database(config.databases.tf2maps_bot)

    id = orm.Integer(primary_key=True)
    discord_user_handle = orm.String(max_length=50)
    discord_user_id = orm.Integer()
    map = orm.String(max_length=50)
    url = orm.String(max_length=255)
    notes = orm.Text(allow_null=True)
    status = orm.String(max_length=50)
    added = orm.DateTime(default=datetime.now())
    played = orm.DateTime(allow_null=True)


# This should be done using normal SQLAlchemy semantics;
# The box this is on has a broken dep chain which prevents using create_engine
# engine = sqlalchemy.create_engine(str(Maps.__database__.url))
# Maps.__metadata__.create_all(engine)
