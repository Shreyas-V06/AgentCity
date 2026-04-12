import os
import redis
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

_redis_client = None

def initialize_db():
    connection_string=os.getenv('CONNECTION_STRING')
    client=MongoClient(connection_string)
    database=client.agentcity
    return database

def initialize_redis():
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        _redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
    return _redis_client

#USAGE:
# from initialize_db import initialize_db
# db=initialize_db()
# collection = db.test

# doc = {
#     "name": "Alice",
#     "email": "alice@example.com",
# }

# result = collection.insert_one(doc)
