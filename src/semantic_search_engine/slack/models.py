from peewee import Model, CharField, TextField, IntegerField, ForeignKeyField, DateTimeField
from . import db

# Create a schema for 'User'
class User (Model):
   user_id=CharField( column_name='user_id', unique=True, primary_key=True )
   name=CharField( column_name='name', null=True )
   real_name=CharField( column_name='real_name', null=True )
   email=CharField( column_name='email' )
   is_bot=CharField( column_name='is_bot' )
   avatar=TextField( column_name='avatar', null=True )
   class Meta:
      database=db
      db_table='Users'

# Create a schema for 'Channel'
class Channel (Model):
   channel_id=CharField( column_name='channel_id', unique=True, primary_key=True )
   name=CharField( column_name='name' )
   access=CharField( column_name='access', default='pub' )
   purpose=TextField( column_name='purpose' )
   class Meta:
      database=db
      db_table='Channels'

# Create a schema for 'ChannelMember'
class ChannelMember (Model):
   channel_id=CharField( column_name='channel_id' )
   user_ids=TextField( column_name='user_ids' )
   no_members=IntegerField( column_name='no_members' )
   class Meta:
      database=db
      db_table='ChannelMembers'

# Create a schema for 'Channel'
class Message (Model):
   #TODO: should be unique... the gptgenerated channel has duplicate message_ids
   message_id=CharField( column_name='message_id') #, unique=True, primary_key=True ) ... TODO: this is not working
   user_id=ForeignKeyField( column_name='user_id', model=User, backref='messages' )
   channel_id=ForeignKeyField( column_name='channel_id', model=Channel, backref='messages' )
   text=TextField( column_name='text' )
   time=DateTimeField( column_name='time' )
   class Meta:
      database=db
      db_table='Messages'