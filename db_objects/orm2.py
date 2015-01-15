#!/usr/bin/python
import re

class orm(object): pass
class db_table(orm, object):
    def __init__(self, orm=None, **kwargs):
        self.db_params = {}
        for k, v in orm.__dict__.items():
            setattr(self, k, v)

class DbIterable:
    def __init__(self, orm, fields, results):
        for k, v in orm.__dict__.items():
            setattr(self, k, v)
        self.results = []
        self.fields = fields
        for result in results:
            self.results.append(result)

    def __iter__(self):
        return self

    def next(self):
        try:
            db_obj = db_table(self)
            item = self.results.pop()
            for i in range(0, len(self.fields)):
                db_obj.set(self.fields[i][0], item[i])
            return db_obj
        except:
            raise StopIteration
         
        
class orm:
        space_regex = re.compile('\s')
        varchar_regex = re.compile('varchar\((\d*)\)')
        enum_regex = re.compile('enum(\(.*\))')

        def __varchar(size):
            pass

        def __get_loaded(self, tpl):
            loaded_objects = []
            query = "select "
            for i in range(0, len(self.fields) - 1):
                query += "%s, " %self.fields[i][0]
            query += "%s " %self.fields[i+1][0]
            query += "from %s where " % self.table_name

            def load_from_dict(self, load_dict={}):
                for k, v in load_dict.items():
                    if k not in self.get_fields():
                        raise AttributeError('illegal key in load_dict')
                    tpl.set(k, v)

            def load(self, **kwargs):
                params = []
                for arg in kwargs.keys():
                    params.append("%s='%s'" % (arg, kwargs[arg]))
                real_query = query +" and ".join(params)
                self.cursor.execute(real_query)
                results = self.cursor.fetchone()
                try:
                    for i in range(0, len(self.fields)):
                        tpl.set(self.fields[i][0], results[i])
                except:
                    pass
                
            def loadall(self, **kwargs):
                params = []
                for arg in kwargs.keys():
                    params.append("%s='%s'" % (arg, kwargs[arg]))
                real_query = query +" and ".join(params)
                self.cursor.execute(real_query)
                for result in self.cursor.fetchall():
                    yield dict(zip([x[0] for x in self.fields], [x for x in result]))

            return load, loadall, load_from_dict
            
        def __get_saved(self, tpl):
            table_name = self.table_name
            def update(self):
                query = "update %s set " %table_name
                db_fields = []
                params = []
                for field in self.fields:
                    if not tpl.db_params.get(field[0], None): continue
                    if not(re.search('PRI', str(field[3])) or re.search('MUL', str(field[3]))): 
                        params.append("%s='%s'" % (field[0], tpl.db_params[field[0]]))
                param_list = ", ".join(params)
                query += param_list
                query += " where id='%s'"%self.get_id()
                self.cursor.execute(query)
                self.db.commit()

            def upsert(self):
                if 'id' in self.dump().keys():
                    self.update()
                else:
                    self.insert()

            def is_auto(self, field):
                if 'auto_increment' in field[-1]:
                    return True
                return False

            def delete(self):
                query = "delete from %s where id=%s" % (table_name, self.get_id())
                self.cursor.execute(query)
                self.db.commit()

            def insert(self):
                params = []
                values = []
                for field in self.fields:
                    #if tpl.is_auto(field): continue #skip if it's auto_incremented
                    if not tpl.db_params.get(field[0], None): continue
                    params.append(field[0])
                    values.append("'%s'" % tpl.db_params[field[0]])
                query = "insert into  %s (%s) values (%s)" %(table_name, ", ".join(params), ", ".join(values))
                self.cursor.execute(query)
                self.db.commit()
            return (update, insert, delete, upsert)

        def __get_fields(self):
            self.fields = []
            self.cursor.execute('desc %s' % self.table_name)
            res = self.cursor.fetchall()
            for result in res:
                self.fields.append(result)


        def __init__(self, *args, **kwargs):
            self.created_classes = {}
            req_args = ['db', 'user','passwd','host']
            for arg in req_args:
                if arg not in kwargs.keys():
                    raise Exception(
                        "Required Arguments: 'db','user','passwd','host'")
            try:
                import MySQLdb
            except ImportError:
                raise Exception("MySQLdb is not installed on this system, or is not in PYTHONPATH")
            setattr(self, 'db', MySQLdb.connect(**kwargs))
            setattr(self, 'cursor', self.db.cursor())
        
	def get_row(self, **kwargs):
	    '''
	    required kwargs: table, row
	    returns all records in row from table
	    '''
	    row = kwargs.get('row')
	    table = kwargs.get('table')
	    items = []
	    self.cursor.execute('select %s from %s' %(row,table))
	    data = self.cursor.fetchall()
	    for item in data:
		items.append(item[0])
	    return items

	def get_row_like(self, **kwargs):
	    '''
	    required kwargs: table, row, where, like
	    returns all records in a row of a table like variable
	    '''
            row = kwargs.get('row')
            table = kwargs.get('table')
	    like = kwargs.get('like')
	    where = kwargs.get('where')
	    items = []
	    self.cursor.execute("select %s from %s where %s like '%s'" %(row,table,where,like))
	    data = self.cursor.fetchall()
	    for item in data:
		items.append(item[0])
	    return items

        def get_tables(self):
            self.cursor.execute('show tables')
            tables = []
            for table in self.cursor.fetchall():
                tables.append(table[0])
            return tables

        def __dump(self):
            for key in db_table.db_params.keys():
                print key, db_table.db_params[key]

        def __factory(self, tpl, field, field_type):

            def getter(self):
                return getattr(tpl, field, None)

            def get(self, var):
                try:
                    return tpl.db_params[var]
                except KeyError:
                    return False

            def get_fields(self):
                try:
                    fields = []
                    for field in self.fields:
                        fields.append(field[0])
                    return fields
                except:
                    return []

            def set(self, var, val):
                fields = []
                for field in self.fields:
                    fields.append(field[0])
                if var not in fields:
                    raise Exception("setting invalid variable name, %s not listed in field list" % var)
                try:
                    tpl.db_params[var] = val
                    setattr(tpl, var, val)
                except:
                    return False

            def dump(self):
                try:
                    return tpl.db_params
                except:
                    return False

            def setter(self, value):
                tpl.db_params[field] = value
                setattr(tpl, field, value)

            if re.search(self.__class__.varchar_regex, field_type):
                size = int(re.search(self.__class__.varchar_regex, field_type).group(1))

                def setter(self, value):
                    if len(value) <= size:
                        tpl.db_params[field] = value
                        setattr(tpl, field, value)
                        return
                    raise Exception("String Length Greater than Field Length")

            if re.search(self.__class__.enum_regex, field_type):
                allowed_values = eval(
                    re.search(self.__class__.enum_regex, field_type).group(1))

                def setter(self, value):
                    if value in allowed_values:
                        tpl.db_params[field] = value
                        setattr(tpl, field, value)
                        return
                    raise Exception("Value not allowed, possible values: %s" %
                                    ",".join(allowed_values))

            setattr(tpl, 'db', self.db)
            setattr(tpl, 'cursor', self.cursor)
            (update, insert, delete, upsert) = self.__get_saved(tpl)
            load,loadall,load_from_dict  = self.__get_loaded(tpl)
            return (getter, setter, get, set, dump, update, insert, delete, upsert, load, loadall, load_from_dict, get_fields)

        def create(self, table_name):
            import re
            #tpl = db_table(self)
            #if table_name in self.created_classes.keys():
            #    return self.created_classes.get(table_name)
            tpl = type(table_name, (object, ), {'db_params': {}})()
            self.table_name = table_name
            if re.search(self.__class__.space_regex, table_name):
                raise Exception("table name invalid, spaces are not allowed!")
            self.__get_fields()
            for field in self.fields:
                (getter, setter,get,set,dump,update,insert,delete, upsert, load,loadall,load_from_dict,get_fields) = self.__factory(tpl,field[0],field[1])
                #(update, insert)=self.__get_saved(tpl)
                setattr(tpl.__class__, 'get_%s' % field[0],getter)
                if not field[-1]:
                    setattr(tpl.__class__, 'set_%s' % field[0],setter)
                del getter
                del setter
            setattr(tpl, 'fields', self.fields)
            setattr(tpl.__class__, 'get_fields', get_fields)
            setattr(tpl.__class__, 'get', get)
            setattr(tpl.__class__, 'set', set)
            setattr(tpl.__class__, 'load', load)
            setattr(tpl.__class__, 'loadall', loadall)
            setattr(tpl.__class__, 'load_from_dict', load_from_dict)
            setattr(tpl.__class__, 'update', update)
            setattr(tpl.__class__, 'insert', insert)
            setattr(tpl.__class__, 'delete', delete)
            setattr(tpl.__class__, 'save', upsert)
            setattr(tpl.__class__, 'dump', dump)
            #self.created_classes[table_name] = tpl 
            return tpl



user = None
db = None
passwd = None
host= None

class DBMapper:
    
    def __init__(self, **kwargs):
        orm_db = orm(user=user, db=db, passwd=passwd, host=host)
        org = orm_db.create(self.__class__.__name__.lower())
        for k, v in org.__dict__.items():
            setattr(self, k, v)
        try:
            for k, v in org.__class__.__dict__.items():
                if k.startswith('__'): continue
                setattr(self.__class__, k, v)
        except:
            pass
        if kwargs:
            self.load(**kwargs)
