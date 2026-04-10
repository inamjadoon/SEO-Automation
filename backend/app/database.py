# 
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")

if INSTANCE_CONNECTION_NAME:
    from google.cloud.sql.connector import Connector
    import pg8000

    connector = None

    def getconn():
        global connector
        if connector is None:
            connector = Connector()
        conn = connector.connect(
            INSTANCE_CONNECTION_NAME,
            "pg8000",
            user="postgres",
            password="inam4321",
            db="ai_system",
        )
        return conn

    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        pool_pre_ping=True
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()