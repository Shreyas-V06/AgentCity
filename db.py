import os
import redis
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

def initialize_db():
    connection_string=os.getenv('CONNECTION_STRING')
    client=MongoClient(connection_string)
    database=client.agentcity
    return database

def initialize_redis():
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    client = redis.Redis.from_url(redis_url, decode_responses=True)
    return client

#USAGE:
# from initialize_db import initialize_db
# db=initialize_db()
# collection = db.test

# doc = {
#     "name": "Alice",
#     "email": "alice@example.com",
# }

# result = collection.insert_one(doc)
