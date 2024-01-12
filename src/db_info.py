from pymongo import MongoClient
from config import HOSTNAME, PORT, DATABASE, KEYBOARD_COLLECTION, MOUSE_COLLECTION, APPLICATION_COLLECTION


def connected():
    try:
        client = MongoClient(HOSTNAME, PORT, serverSelectionTimeoutMS=500)
        client.server_info()
        db = client[DATABASE]
        db.command("serverStatus")
        return True
    except Exception as e:
        print(e)
        return False


def get_db_size():
    client = MongoClient(HOSTNAME, PORT)
    db = client[DATABASE]
    size = db.command("dbStats")["dataSize"] / 1000000
    size = round(size, 2)
    return size


def get_collection_names():
    client = MongoClient(HOSTNAME, PORT)
    db = client[DATABASE]
    return db.list_collection_names()


def get_collection_stats(coll):
    client = MongoClient(HOSTNAME, PORT)
    db = client[DATABASE]
    pipeline = [{"$collStats": {"storageStats": {}}}]
    stats = next(db[coll].aggregate(pipeline), None)
    count = 0
    size = 0
    if stats and "storageStats" in stats:
        if "count" in stats["storageStats"]:
            count = stats["storageStats"]["count"]
        if "timeseries" in stats["storageStats"]:
            count = db.get_collection(coll).count_documents({})
        size = stats["storageStats"]["size"] / 1000000
        size = "{0} (MB)".format(round(size, 2))
    return {"count": count, "size": size}
