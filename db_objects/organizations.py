'''
Created on Jan 12, 2015

@author: darnold
'''
import orm2
import os, sys
top_level = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
sys.path.append(top_level)
import app_config
orm2.db = app_config.database.get('db')
orm2.host = app_config.database.get('host')
orm2.user = app_config.database.get('user')
orm2.passwd = app_config.database.get('passwd')

class Organizations(orm2.DBMapper):
    pass