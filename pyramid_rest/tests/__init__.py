import os


def setUpPackage():
    os.environ['MONGO_URI'] = 'mongodb://localhost/prest_test'
    os.environ['MONGO_DB_NAME'] = 'prest_test'
