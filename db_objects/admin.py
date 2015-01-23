'''
Created on Jan 12, 2015

@author: darnold
'''
import orm2
import os, sys
import redis
top_level = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
sys.path.append(top_level)
import app_config
import random
import string

orm2.db = app_config.database.get('db')
orm2.host = app_config.database.get('host')
orm2.user = app_config.database.get('user')
orm2.passwd = app_config.database.get('passwd')

class Config(orm2.DBMapper):
    pass
