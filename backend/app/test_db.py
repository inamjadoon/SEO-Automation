from database import engine

try:
    connection = engine.connect()
    print("Database connected successfully")
    connection.close()
except Exception as e:
    print("Database connection failed:", e)


# test_main.py
# from fastapi import FastAPI

# app = FastAPI()

# @app.get("/")
# def home():
#     return {"status": "ok"}

