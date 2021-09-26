# Std Lib Imports
from enum import Enum

# 3rd Party Imports
from tortoise import Tortoise
from tortoise.fields import *
from tortoise.models import Model

# Local Imports
pass

class version_state(Enum):
    VISIBLE = "visible"
    MODERATED = "moderated"
    DELETED = "deleted"

class resource_state(Enum):
    VISIBLE = "visible"
    MODERATED = "moderated"
    DELETED = "deleted"


class xf_resource_version(Model):
    """
        xf_resource_version
        +---------------------+---------------------------------------+------+-----+---------+----------------+
        | Field               | Type                                  | Null | Key | Default | Extra          |
        +---------------------+---------------------------------------+------+-----+---------+----------------+
        | resource_version_id | int(10) unsigned                      | NO   | PRI | <null>  | auto_increment |
        | resource_id         | int(10) unsigned                      | NO   | MUL | <null>  |                |
        | resource_update_id  | int(10) unsigned                      | NO   |     | <null>  |                |
        | version_string      | varchar(50)                           | NO   |     | <null>  |                |
        | release_date        | int(10) unsigned                      | NO   |     | <null>  |                |
        | download_url        | varchar(250)                          | NO   |     |         |                |
        | download_count      | int(10) unsigned                      | NO   |     | 0       |                |
        | rating_count        | int(10) unsigned                      | NO   |     | 0       |                |
        | rating_sum          | int(10) unsigned                      | NO   |     | 0       |                |
        | version_state       | enum('visible','moderated','deleted') | NO   |     | visible |                |
        | had_first_visible   | tinyint(3) unsigned                   | NO   |     | 0       |                |
        +---------------------+---------------------------------------+------+-----+---------+----------------+
    """
    resource_version_id = IntField(pk=True)
    resource_id = IntField()
    resource_update_id = IntField()
    version_string = CharField(max_length=50)
    release_date = IntField()
    download_url = CharField(max_length=250)
    download_count = IntField()
    rating_count = IntField(default=0)
    rating_sum = IntField(default=0)
    version_state = CharEnumField(version_state, default=version_state.VISIBLE)
    had_first_visible = IntField(default=0)

class xf_resource(Model):
    """
        xf_resource
        +------------------------+---------------------------------------+------+-----+---------+----------------+
        | Field                  | Type                                  | Null | Key | Default | Extra          |
        +------------------------+---------------------------------------+------+-----+---------+----------------+
        | resource_id            | int(10) unsigned                      | NO   | PRI | <null>  | auto_increment |
        | title                  | varchar(100)                          | NO   |     |         |                |
        | tag_line               | varchar(100)                          | NO   |     |         |                |
        | user_id                | int(10) unsigned                      | NO   | MUL | <null>  |                |
        | username               | varchar(100)                          | NO   |     |         |                |
        | resource_state         | enum('visible','moderated','deleted') | NO   |     | visible |                |
        | resource_date          | int(10) unsigned                      | NO   |     | <null>  |                |
        | resource_category_id   | int(11)                               | NO   | MUL | <null>  |                |
        | current_version_id     | int(10) unsigned                      | NO   |     | <null>  |                |
        | description_update_id  | int(10) unsigned                      | NO   |     | <null>  |                |
        | discussion_thread_id   | int(10) unsigned                      | NO   | MUL | <null>  |                |
        | external_url           | varchar(500)                          | NO   |     |         |                |
        | is_fileless            | tinyint(3) unsigned                   | NO   |     | 0       |                |
        | external_purchase_url  | varchar(500)                          | NO   |     |         |                |
        | price                  | decimal(10,2) unsigned                | NO   |     | 0.00    |                |
        | currency               | varchar(3)                            | NO   |     |         |                |
        | download_count         | int(10) unsigned                      | NO   |     | 0       |                |
        | rating_count           | int(10) unsigned                      | NO   |     | 0       |                |
        | rating_sum             | int(10) unsigned                      | NO   |     | 0       |                |
        | rating_avg             | float unsigned                        | NO   |     | 0       |                |
        | rating_weighted        | float unsigned                        | NO   | MUL | 0       |                |
        | update_count           | int(10) unsigned                      | NO   |     | 0       |                |
        | review_count           | int(10) unsigned                      | NO   |     | 0       |                |
        | last_update            | int(10) unsigned                      | NO   | MUL | <null>  |                |
        | alt_support_url        | varchar(500)                          | NO   |     |         |                |
        | had_first_visible      | tinyint(3) unsigned                   | NO   |     | 0       |                |
        | custom_resource_fields | mediumblob                            | NO   |     | <null>  |                |
        | prefix_id              | int(10) unsigned                      | NO   | MUL | 0       |                |
        | icon_date              | int(10) unsigned                      | NO   |     | 0       |                |
        | tags                   | mediumblob                            | NO   |     | <null>  |                |
        +------------------------+---------------------------------------+------+-----+---------+----------------+
    """
    resource_id = IntField(pk=True)
    title = CharField(max_length=100)
    tag_line = CharField(max_length=100)
    user_id = IntField()
    username = CharField(max_length=100)
    resource_state = CharEnumField(resource_state, default=resource_state.VISIBLE)
    resource_date = IntField()
    resource_category_id = IntField()
    current_version_id = IntField()
    description_update_id = IntField()
    discussion_thread_id = IntField()
    external_url = CharField(max_length=500)
    is_fileless = IntField(default=0)
    external_purchase_url = CharField(max_length=500)
    price = DecimalField(10,2, default=0.00)
    currency = CharField(max_length=3)
    download_count = IntField(default=0)
    rating_count = IntField(default=0)
    rating_sum = IntField(default=0)
    rating_avg = FloatField(default=0)
    rating_weighted = FloatField(default=0)
    update_count = IntField(default=0)
    review_count = IntField(default=0)
    last_update = IntField(default=0)
    alt_support_url = CharField(max_length=500)
    had_first_visible = IntField(default=0)
    custom_resource_fields = BinaryField()
    prefix_id = IntField(default=0)
    icon_date = IntField(default=0)
    tags = BinaryField()

class xf_user_field_value(Model):
    """
        xf_user_field_value
        +-------------+------------------+------+-----+---------+-------+
        | Field       | Type             | Null | Key | Default | Extra |
        +-------------+------------------+------+-----+---------+-------+
        | user_id     | int(10) unsigned | NO   | PRI | <null>  |       |
        | field_id    | varbinary(25)    | NO   | PRI | <null>  |       |
        | field_value | mediumtext       | NO   |     | <null>  |       |
        +-------------+------------------+------+-----+---------+-------+
    """
    user_id = IntField(pk=True)
    field_id = BinaryField(pk=True)
    filed_value = TextField()
