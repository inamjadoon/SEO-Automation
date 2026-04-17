# # 
# import os
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base
# from dotenv import load_dotenv

# load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL")
# INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")

# if INSTANCE_CONNECTION_NAME:
#     from google.cloud.sql.connector import Connector
#     import pg8000

#     connector = None

#     def getconn():
#         global connector
#         if connector is None:
#             connector = Connector()
#         conn = connector.connect(
#             INSTANCE_CONNECTION_NAME,
#             "pg8000",
#             user="postgres",
#             password="inam4321",
#             db="ai_system",
#         )
#         return conn

#     engine = create_engine(
#         "postgresql+pg8000://",
#         creator=getconn,
#         pool_pre_ping=True
#     )
# else:
#     engine = create_engine(
#         DATABASE_URL,
#         pool_pre_ping=True
#     )

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from google.cloud.sql.connector import Connector
import pg8000

INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")

if not INSTANCE_CONNECTION_NAME:
    raise RuntimeError("INSTANCE_CONNECTION_NAME is required")

connector = Connector()

def getconn():
    return connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pg8000",
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME", "ai_system"),
    )

engine = create_engine(
    "postgresql+pg8000://",
    creator=getconn,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=2,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()