from pymongo import MongoClient
from pymongo.collection import Collection


try:
    mongo_client = MongoClient()
    db = mongo_client["ml-disinformation"]
except:
    print("Could not connect to database")
    exit()


def get_collection(collection_name: str) -> Collection:
    return db[collection_name]


