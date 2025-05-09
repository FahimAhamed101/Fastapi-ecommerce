from models import *
from sqlmodel import SQLModel, create_engine, Session

from fastapi import  UploadFile

DATABASE_URL="postgresql://neondb_owner:npg_VEg9bZp7snaW@ep-lucky-shape-a4votp4d-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"


engine = create_engine(DATABASE_URL, echo=True)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session