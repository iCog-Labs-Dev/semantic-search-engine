from peewee import (
    SqliteDatabase, 
    MySQLDatabase,
    PostgresqlDatabase,
    Model

)
import peewee as fields
import enum
from semantic_search_engine import constants
import sys
import typer
import rich
import os


class DatabaseEnum(enum.Enum):
    """A python enumeration used to check with the environment variable
    'SQL_DB_TYPE'.
    """
    SQLite = "sqlite"
    Postgresql = "postgres"
    MySql = "mysql"


# decides which database to connects to, sqlite by default
match constants.SQL_DB_TYPE:
    case DatabaseEnum.SQLite.value:
        # connect to/create a SQLite database.
        db = SqliteDatabase(constants.SQLITE_DB_PATH)

    case DatabaseEnum.Postgresql.value:
        # Connect to a Postgres database.
        db = PostgresqlDatabase(
            constants.POSTGRESQL_DB_NAME, 
            user = constants.POSTGRESQL_DB_USER, 
            password = constants.POSTGRESQL_DB_PASSWORD,
            host = constants.POSTGRESQL_DB_HOST, 
            port = constants.POSTGRESQL_DB_PORT
        )

    case DatabaseEnum.MySql.value:
        # Connect to a MySQL database on network.
        db = MySQLDatabase(
            constants.MYSQL_DB_NAME, 
            user = constants.MYSQL_DB_USER,
            password = constants.MYSQL_DB__PASSWORD,
            host = constants.MYSQL_DB_HOST,
            port = constants.MYSQL_DB_PORT
        )
        
    case _:
        # replace with a custom exception
        raise Exception("invalid database 'peewee' only accepts sqlite, postgresql or mysql")


# peewee ORM models
# -----------------

class BaseModel(Model):
    """A model to be inherited by all models representing a table
    """
    class Meta:
        database = db


class User(BaseModel):
    """A user table model
    """
    id = fields.CharField(max_length=15, primary_key=True, index=True)
    name = fields.CharField(max_length=50)
    deleted = fields.BooleanField()
    real_name = fields.CharField(max_length=50)
    first_name = fields.CharField(max_length=50)
    last_name = fields.CharField(max_length=50)



class Chat(BaseModel):
    """A chat table model representing a DM, channel, group or a private channel
    """
    
    id = fields.CharField(max_length=30, primary_key=True, index=True)
    name = fields.CharField(max_length=50)
    
class ChatMemberRelationship(BaseModel):
    """A relationship table model representing which user is a member which chat
    """

    member_id  = fields.ForeignKeyField(User, backref="members")
    chat_id = fields.ForeignKeyField(Chat, backref="chat")


# cli related code to manage database

# list of tables to be inserted/deleted to the database
DB_TABLES = [
    User,
    Chat,
    ChatMemberRelationship
    # insert more here
]

# initialize typer
app = typer.Typer()

# typer commands. each function represents first generation commands
@app.command()
def create_tables():
    """Creates the tables found in DB_TABLES
    """
    db.connect()

    db.create_tables(DB_TABLES)

    db.close()
    rich.print("[bold green]Done[/bold green] :thumbsup:")
    
@app.command()
def migrate():
    """Synces the schema of the database to the db.py module models. Note that
       this model does not exactly do migrations. it just deltes the tables then
       recreates the updated ones.
    """
    
    rich.print(
        "[bold red]WARNING: this will delete all existing data in the database.[/bold red]",
        end=""
    )
    answer = typer.confirm("", default = True) # double check database deletion
    if answer:
        db.connect()
        db.drop_tables(DB_TABLES)
        db.create_tables(DB_TABLES)
        db.close
        rich.print("[bold green]Done[/bold green] :thumbsup:")
    else:
        rich.print("[bold green]No chages made bye[/bold green] :waving_hand:")


if __name__ == "__main__":
    app()

    

