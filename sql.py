# -*- coding: utf-8 -*-
import pymssql
import settings
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def init_connection(table_name):
    engine = create_engine('mssql+pymssql://%s:%s@%s/%s' % (
        settings.HOST_253_USER,
        settings.HOST_PASSWORD,
        settings.HOST_253,
        settings.DB
    ))
    # connection = engine.connect()
    metadata = sqlalchemy.schema.MetaData(bind=engine, reflect=True)
    table_schema = sqlalchemy.Table(table_name, metadata, autoload=True)

    return table_schema, engine


def output_data_sql(list_write, engine, table_schema):

    connection = engine.connect()
    # Open the session
    Session = sessionmaker(bind=engine)
    session = Session()

    # Inser the dataframe into the database in one bulk
    # print(table_schema.insert())
    try:
        connection.execute(table_schema.insert(), list_write)
        session.commit()
    except Exception as e:
        print e
    finally:
        session.close()
        connection.close()


"""
use pymssql connect to the sql server
"""


class Mssql:
    def __init__(self):
        self.host = settings.HOST
        self.user = settings.HOST_USER
        self.pwd = settings.HOST_PASSWORD
        self.db = settings.DB

    def __get_connect(self):
        if not self.db:
            raise (NameError, "do not have db information")
        self.conn = pymssql.connect(
            host=self.host,
            user=self.user,
            password=self.pwd,
            database=self.db,
            charset="utf8"
        )
        cur = self.conn.cursor()
        if not cur:
            raise (NameError, "Have some Error")
        else:
            return cur

    def exec_query(self, sql):
        """
         the query will return the list, example;
                ms = MSSQL(host="localhost",user="sa",pwd="123456",db="PythonWeiboStatistics")
                resList = ms.ExecQuery("SELECT id,NickName FROM WeiBoUser")
                for (id,NickName) in resList:
                    print str(id),NickName
        """
        cur = self.__get_connect()
        #print 'get conn'
        cur.execute(sql)
        res_list = cur.fetchall()

        # the db object must be closed
        self.conn.close()
        return res_list

    def exec_non_query(self, sql):
        """
        execute the query without return list, example：
            cur = self.__GetConnect()
            cur.execute(sql)
            self.conn.commit()
            self.conn.close()
        """
        cur = self.__get_connect()
        cur.execute(sql)
        self.conn.commit()
        self.conn.close()

    def exec_many_query(self, sql, param):
        """
        execute the query without return list, example：
            cur = self.__GetConnect()
            cur.execute(sql)
            self.conn.commit()
            self.conn.close()
        """
        cur = self.__get_connect()
        try:
            cur.executemany(sql, param)
            self.conn.commit()
        except Exception as e:
            print e
            self.conn.rollback()

        self.conn.close()


def hot_sale_item_to_sql(data, table_name):
    conn = Mssql()
    insert_sql = "insert into " + table_name + " values (%s,%s,%s,%s,%d,%d,%d,%d,%s,%s,%s,%s,%d,%d)"
    conn.exec_many_query(insert_sql, data)


def hot_shop_to_sql(data, table_name):
    conn = Mssql()
    insert_sql = "insert into " + table_name + " values (%s,%d,%s,%s,%d,%d,%s,%d,%s)"
    conn.exec_many_query(insert_sql, data)


def make_hot_shop_plan(data):
    conn = Mssql()
    insert_sql = "insert into T_Plan_HotShop(" \
                "CategoryId, CategoryName, CategoryURL, RecordDate,RecoredType)values('%s','%s','%s','%s','%d')" % \
                (data['CategoryId'].encode('utf8'),
                 data['CategoryName'].encode('utf8'),
                 data['CategoryURL'].encode('utf8'),
                 data['RecordDate'],
                 data['RecordType'])
    conn.exec_non_query(insert_sql)


def update_hot_shop_plan(data):
    conn = Mssql()
    update_sql = "update T_Plan_Hotshop set Iscolled=1 where CategoryId='%s' and RecordDate='%s' and RecoredType='%d'" %\
                (data['CategoryId'],
                 data['RecordDate'],
                 data['RecordType']
                 )
    conn.exec_non_query(update_sql)


def logo_item_to_sql(data, table_name):
    conn = Mssql()
    insert_sql = "insert into " + table_name + " values (%s,%s,%s,%s,%d,%s,%s,%d,%s,%s,%s,%d)"
    conn.exec_many_query(insert_sql, data)


def analyse_item_to_sql(data, table_name):
    conn = Mssql()
    sql_text = "insert into " + table_name + " values (%s,%s,%d,%d,%d,%s)"
    conn.exec_many_query(sql_text, data)


def add_item_struct(data):
    conn = Mssql()
    sql_text = "insert into T_Data_ItemStructTemp values ('%s','%s','%s','%s','%s','%s')" % \
               (data[0].encode('utf8'),
                data[1].encode('utf8'),
                data[2].encode('utf8'),
                data[3].encode('utf8'),
                data[4].encode('utf8'),
                data[5].encode('utf8'))
    conn.exec_non_query(sql_text)


def is_exist_item_value(data, date_begin):
    conn = Mssql()
    sql_text = "select itemID from T_Data_AnalyseItem where itemId='%s' and recordDate='%s'" % \
               (data[2].encode('utf8'), date_begin.encode('utf8'))
    res = conn.exec_query(sql_text)
    if len(res) > 0:
        return True
    else:
        add_item_struct(data)
        return False


def init_temp_table(table_name, org_table):
    conn = Mssql()
    script = """IF EXISTS (select * from sysobjects where name='{0}')drop TABLE {0}
    SELECT * INTO {0} FROM {1} WHERE 1<>1
    """.format(table_name, org_table)
    conn.exec_non_query(script)


def exec_db_merge_function(func_name):
    conn = Mssql()
    script = "exec %s" % func_name
    conn.exec_non_query(script)


if __name__ == "__main__":
    print 'begin'
    #data = {'RecordType': 1, 'CategoryURL': u'http://item.taobao.com/item.htm?id=538834474818', 'CategoryId': '1121', 'CategoryName': u'\u987e\u5bb6\u5bb6\u5c45\u65d7\u8230\u5e97', 'RecordDate': "20170101"}
    #make_hot_sale_plan(data)
    #data = (u'20724159', u'\u7687\u5bb6\u5320\u4eba\u5bb6\u5177\u65d7\u8230\u5e97', u'18803430577', u'http://item.taobao.com/item.htm?id=18803430577', u'\u7687\u5bb6\u5320\u4eba\u63d0\u524d\u8d2d/\u7269\u6d41\u8fd0\u8d39\u8865\u5dee/\u6709\u507f\u5165\u6237\u8d39\u7528/\u5b9a\u91d1\u652f\u4ed8\u4e13\u7528\u94fe\u63a5', u'\u5176\u4ed6 \xbb \u5b9a\u91d1')
    # data = [('50001412', '88', '\xe6\x98\xaf\xe5\x90\xa6\xe7\xbb\x84\xe8\xa3\x85', '\xe7\xbb\x84\xe8\xa3\x85', 313281, '90.52%', '90.45%', 28426155.0, '95.36%', '95.3%', '20160101',1), ('50001412', '88', '\xe6\x98\xaf\xe5\x90\xa6\xe7\xbb\x84\xe8\xa3\x85', '\xe6\x95\xb4\xe8\xa3\x85', 32818, '9.48%', '9.48%', 1382185.0, '4.64%', '4.63%', '20160101',1)]
    data = [('50015888', 'http://gd3.alicdn.com/bao/uploaded/i3/TB12Vb3KVXXXXa.XFXXXXXXXXXX_!!0-item_pic.jpg_60x60q70.jpg', '51e0', 'http://item.taobao.com/item.htm?id=525229635892', 1578.0, 484.0, 330, 159630, '177', 'http://item.taobao.com/item.htm?id=525229635892', '4eac', '20170301', 0, 1)]
    hot_sale_item_to_sql(data, 'T_Data_HotItemTemp')
    print 'END'
