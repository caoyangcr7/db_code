# -*-coding:utf8 -*-

import MySQLdb
import json
import os
from DBUtils.PooledDB import PooledDB
import sys



reload(sys)
sys.setdefaultencoding('utf-8')


class MessageToSql(object):
    """docstring for MessageToSql"""

    def __init__(self):
        pass

    def safe(self, str_s):
        return MySQLdb.escape_string(str_s)

    def dict_to_str(self, dict_data):
        '''
        change the data of dict into string like 'key=value,key=value'
        '''
        templist = []
        for k, v in dict_data.items():
            temp = "%s='%s'" % (str(k), self.safe(str(v)))
            templist.append(' ' + temp + ' ')
        return ','.join(templist)

    def dict_to_str_and(self, dict_data):
        ''''
        change the data of dict into string like 'key=value and key=value'
        '''
        templist = []
        for k, v in dict_data.items():
            temp = "%s='%s'" % (str(k), self.safe(str(v)))
            templist.append(' ' + temp + ' ')
        return 'and'.join(templist)

    def dict_to_list_for_select(self,message_dict):
        # to inquire the information for login
        message_key_list = []
        for key in message_dict.keys():
            message_key_list.append(key)
        return message_key_list

    def get_i_sql(self, data_dict, table='group_leader'):
        '''
           create the insert sql
        '''
        sql = "insert into %s set " % table
        sql += self.dict_to_str(data_dict)
        print sql
        return sql

    def get_u_sql(self, value_dict, conditions_dict, table='caoyang_data1'):
        '''
        create the update sql like 'update table set value_dict where conditions_dict'
        '''
        sql = "update %s set" % table
        sql += self.dict_to_str(value_dict)
        sql += " where %s" % self.dict_to_str_and(conditions_dict)
        print sql
        return sql

    def get_d_sql(self, conditions_dict, table='caoyang_data1'):
        '''
        create the delete sql like 'delete from table where conditons_dict'
        '''
        sql = "delete from %s" % table
        sql += " where %s" % self.dict_to_str_and(conditions)
        print sql
        return sql

    def get_s_sql(self, keys_list, conditions_dict, isdistinct=0, table='information_of_therapists'):

        if isdistinct:
            sql = "select distinct %s" % (','.join(keys_list))
        else:
            sql = "select %s" % (','.join(keys_list))
        sql += " from %s" % table
        if conditions_dict:  # if the condition_dict =={} ----->select key_list from  table
            sql += " where %s" % (self.dict_to_str_and(conditions_dict))
        print sql
        return sql

    def info_match_and_inquire(self, message_key_list, func_run_select, sql):
        # used in the login function ,return a dictionary
        # sql =
        # self.get_s_sql(self,keys_list,conditions_dict,isdistinct=0,table='caoyang_data1')
        sql_result = func_run_select(sql)
        print sql_result,'?'
        the_format_result = self.select_sql_result_format(
            sql_result, message_key_list)
        return the_format_result


    def select_sql_result_format(self, after_sql, keys_list):
        '''
        after_sql is the result after executing select sql
        key_list is the keys of chaxun(chinese)
        the aim of this method is to format the result of executing select sql
        like ((1,2),(3,4))->[{"key1":1,"key2":2},{"key1":3,"key2":4}]

        '''
        result_format_list = []
        length = len(keys_list)
        if after_sql:
            for item in after_sql:
                temp = {}
                for i in range(length):
                    temp[keys_list[i]] = str(item[i])
            result_format_list.append(temp)
        return result_format_list


class Connect_db(object):
    """ create the pool of process to connect database"""
    # create the model of single instance,but change the connection of instance 
    def __new__(cls,pool):
        if not hasattr(cls,'instance'):
            cls.instance = super(Connect_db,cls).__new__(cls)
        else:
            cls.instance._conn = pool.connection()
            print cls.instance._conn
        return cls.instance   

    def __init__(self,pool):
        '''
        get the conn and cursor
        '''
        self._conn = pool.connection()
        self._cursor  = self._conn.cursor()

    def cur(self):
        return self._cursor
    def commit(self):
        self._conn.commit()
    def execute(self,sql,fetchone=0):
        self._cursor.execute(sql)
        return self._cursor.fetchone() if fetchone else self._cursor.fetchall()
    def close(self):
        self._cursor.close()
        self._conn.close()
    def run(self,sql,fetchone=0):
        result = self.execute(sql,fetchone)
        self.commit()
        self.close()
        return result


if __name__ == '__main__':
    pass


   
