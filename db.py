import os
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

def initialize_db():
    connection_string=os.getenv('CONNECTION_STRING')
    client=MongoClient(connection_string)
    database=client.klh
    return database

#USAGE:
# from initialize_db import initialize_db
# db=initialize_db()
# collection = db.test

# doc = {
#     "name": "Alice",
#     "email": "alice@example.com",
# }

# result = collection.insert_one(doc)
