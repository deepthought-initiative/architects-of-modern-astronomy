import os

def store(storename, key):
    """adds *key* to the store"""
    return os.mkdir(os.path.join(storename, key))

def is_stored(storename, key):
    """checks whether *key* is present in the store"""
    return os.path.exists(os.path.join(storename, key))
