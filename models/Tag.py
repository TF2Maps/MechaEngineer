# Std Lib Imports
from datetime import datetime, timedelta

# 3rd Party Imports
import databases
import orm
import sqlalchemy

# Local Imports
from utils import load_config

config = load_config()


class Tag(orm.Model):
    __tablename__ = "tags"
    __metadata__ = sqlalchemy.MetaData()
    __database__ =  databases.Database(config.databases.tags)

    id = orm.Integer(primary_key=True)
    key = orm.String(max_length=100, unique=True)
    value = orm.String(max_length=1024)
    author = orm.String(max_length=100)
    date = orm.DateTime(default=datetime.now())

engine = sqlalchemy.create_engine(str(Tag.__database__.url))
Tag.__metadata__.create_all(engine)
