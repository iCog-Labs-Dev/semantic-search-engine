import os
from peewee import SqliteDatabase, Model, CharField, TextField, DateField
from semantic_search_engine.constants import SQLITE_PATH

os.makedirs(SQLITE_PATH, exist_ok=True)

# get or create connection with SQLite database
db = SqliteDatabase(
   SQLITE_PATH + '/auth.db' #, pragmas={'journal_mode': 'wal', 'cache_size': 10000,'foreign_keys': 1}
)
print('Path to oauth db:', db.database)

# Create a schema for 'Auth'
class Auth(Model):
   client_token=TextField( column_name='client_token', unique=True, primary_key=True )
   user_id=CharField( column_name='user_id' )
   name=CharField( column_name='name', null=True )
   username=CharField( column_name='username', null=True )
   email=CharField( column_name='email', null=True )
   role=CharField( column_name='role' )
   access_token=TextField( column_name='access_token' )
   expires_at=DateField( column_name='expires_at', null=True )
   class Meta:
      database=db
      db_table='Authenticated'

Auth.create_table()