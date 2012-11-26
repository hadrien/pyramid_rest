# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os


def setUpPackage():
    os.environ['MONGO_URI'] = 'mongodb://localhost/prest'
    os.environ['MONGO_DB_NAME'] = 'prest'
