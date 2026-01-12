from typing import Annotated
from fastapi import Depends
from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv
import os

load_dotenv('backend/.env')

engine = create_engine(os.getenv('DATABASE_URL'), echo=True) #A SQLModel engine (underneath it's actually a SQLAlchemy engine) is what holds the connections to the database

"""
A Session is what stores the objects in memory and keeps track of any changes needed in the data, then it uses the engine to communicate with the database.  
Here we define a function that will create a new session for us whenever we need it.The 'with' statement ensures that the session is properly closed after we're done using it.
"""
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)] #This is a type alias that can be used in FastAPI path operations to automatically get a database session injected into them.