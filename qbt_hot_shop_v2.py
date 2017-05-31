# -*- coding: utf-8 -*-
import re
import os
import sys
import time
from pyquery import PyQuery as pq

import settings
import sql
import log_sys
from qbt_web_tool import init_driver, get_html

"""
content is the data
Record type = Tmall or taobao
num_col is the number of columns
"""

DB_TMP_TABLE = 'T_Data_HotShopTemp'
DB_TABLE = 'T_Data_HotShop'
DB_PROCESS = 'P_Merge_HotShop'
driver = paramets = log = headers = None
tmp_insert_data = []
engine = table_schema = None
BASE_URL = 'http://qbt.ecdataway.com'


def get_category_urls(url):
    global paramets
    response_page = get_html(url, headers)
    sub_items = pq(response_page)('#sidebar_category')
    print sub_items
    # Need to chang when is well
    sub_urls = []
    sub_title = []
    # print 'sub item number : ', len(sub_items)
    for id_sub_item in range(paramets['begin_index'], len(sub_items)):
        print id_sub_item
        sub_url = sub_items('a').eq(id_sub_item).attr('href')
        sub_text = sub_items('a').eq(id_sub_item).text()
        if ('stat' in sub_url) and (sub_text != ""):
            sub_urls.append(BASE_URL + sub_url)
            sub_title.append(sub_text)

    print sub_urls
    for i in range(0, len(sub_urls)):
        # print sub_title[i] + ":" + sub_urls[i]
        log.error(sub_title[i] + ":" + sub_urls[i])
        response_page = get_html(sub_urls[i], headers)
        sub_sub_items = pq(response_page)('#sidebar_category')
        # Need to chang when is well
        sub_sub_urls = []
        sub_sub_title = []
        print len(sub_sub_items)
        for id_sub_item in range(paramets['begin_sub_index'], len(sub_sub_items)):
            sub_url = sub_items('a').eq(id_sub_item).attr('href')
            sub_text = sub_items('a').eq(id_sub_item).text()
            if ('stat' in sub_url) and (sub_text != ""):
                sub_sub_urls.append(sub_url)
                sub_sub_title.append(sub_text)

        print sub_sub_urls
        for j in range(0, len(sub_sub_urls)):
            # print sub_sub_title[j] + ":" + sub_sub_urls[j]
            log.error(sub_sub_title[j] + ":" + sub_sub_urls[j])
            paramets['current_url'] = sub_sub_urls[j]
            paramets['pos_name'] = sub_sub_title[j]
            time.sleep(1)
            # get_data(driver, sub_sub_urls[j])
            paramets['begin_sub_index'] += 1

        paramets['begin_sub_index'] = 1
        paramets['begin_index'] += 1


def get_top_shop_table_value(post_data, record_type, date_chose=None):
    for date_select in date_chose[paramets['date_index']:]:
        log.error('current_url:%s;record_type:%d;date_index:%d;begin_index:%d;begin_category:%d' %
                  (paramets['current_url'], paramets['record_type'], paramets['date_index'],
                   paramets['begin_index'], paramets['begin_category']))
        post_data['is_small'] = record_type
        post_data['period_start2'] = post_data['period_last'] = date_select
        response_page = get_html(BASE_URL+'/stat', headers, data=post_data)
        time.sleep(3)
        tbody = pq(response_page)('table').eq(1)('tr')
        for id_cell in range(1, len(tbody)):
            a = tbody.eq(id_cell)('td').eq(1)('a')
            tmp_insert_data.append({
                'CategoryId': post_data['cid'],
                'HotRange': int(tbody.eq(id_cell)('td').eq(0).text()),
                'ShopName': a.text(),
                'ShopURL': a.attr('href').replace('\'', '').encode('utf8'),
                'SalesCnt': int(tbody.eq(id_cell)('td').eq(2).text().replace(',', '')),
                'SalesMoney': int(tbody.eq(id_cell)('td').eq(3).text().replace(',', '')),
                'city': tbody.eq(id_cell)('td').eq(4).text(),
                'RecordDate': (date_select+"01"),
                'RecordType': record_type
            })

        # output to DB
        output_data_to_db()

        paramets['date_index'] += 1

    paramets['date_index'] = 0


def get_hot_sale_data(url, data_type, date_chose=None):

    res = re.findall('&cid=[0-9].*', url)
    categoryId = res[0][5:]
    res = re.findall('rcid=[0-9].*&', url)
    rcid = res[0][5:-1]
    post_data = {
        'type': data_type,
        'rcid': rcid,
        'is_csv': '0',
        'cids': '0',
        'is_price': '1',
        'is_radio': '0',
        'cid': categoryId,
        'sort_by': 'num_total'
     }
    if paramets['is_first_time']:
        # print 'first time'
        if paramets['record_type'] == 1:
            # firstly, the date from tmall
            get_top_shop_table_value(post_data, record_type=1, date_chose=date_chose)
            # the date from taobao
            paramets['record_type'] = 0
            get_top_shop_table_value(post_data, record_type=0, date_chose=date_chose)
        else:
            # the date from taobao
            paramets['record_type'] = 0
            get_top_shop_table_value(post_data, record_type=0, date_chose=date_chose)
        paramets['is_first_time'] = False
    else:
        # firstly, the date from tmall
        paramets['record_type'] = 1
        get_top_shop_table_value(post_data, record_type=1, date_chose=date_chose)
        # secondly, the date from taobao
        paramets['record_type'] = 0
        get_top_shop_table_value(post_data, record_type=0, date_chose=date_chose)

    paramets['record_type'] = 1


def get_second_data(url):
    response_page = get_html(url, headers)
    time.sleep(2)
    sub_items = pq(response_page)('#sidebar_category')('li')
    sub_urls = []
    sub_title = []
    for id_sub_item in range(paramets['begin_index'], len(sub_items)):
        print id_sub_item
        sub_url = sub_items.eq(id_sub_item)('a').attr('href')
        sub_text = sub_items.eq(id_sub_item)('a').text()
        if ('stat' in sub_url) and (sub_text != ""):
            sub_urls.append(BASE_URL + sub_url)
            sub_title.append(sub_text)

    # begin at N, it the programme break down
    for i in range(paramets['begin_index'], len(sub_urls)):
        # print ('-item--' + sub_title[i])
        get_hot_sale_data(sub_urls[i], data_type=3, date_chose=settings.shop_date_chose)
        paramets['begin_index'] += 1

    paramets['begin_index'] = 0
    paramets['begin_category'] += 1


def output_data_to_db(is_all=False):
    global tmp_insert_data
    if len(tmp_insert_data) > 2000 or is_all:
        try:
            sql.output_data_sql(tmp_insert_data, engine, table_schema)
            log.error('Success : output to DB')
        except:
            log.error('Error : output to DB  and length of row is %d' % len(tmp_insert_data))
        finally:
            tmp_insert_data = []


def restart_program(error=None):
    """Restarts the current program.
    Note: this function does not return. Any cleanup action (like
    saving data) must be done before calling this function."""
    file_out = open('hot_shop_process.log', 'a')
    file_out.write('current_url:%s;record_type:%d;date_index:%d;begin_index:%d;begin_category:%d\n' %
                   (paramets['current_url'], paramets['record_type'], paramets['date_index'],
                    paramets['begin_index'], paramets['begin_category']))
    file_out.close()
    log.error(error)
    output_data_to_db(is_all=True)
    # sql.exec_db_merge_function(DB_PROCESS)
    driver.quit()
    python = sys.executable
    os.execl(python, python, *sys.argv)


def get_current_point(filename):
    results = None
    with open(filename) as f:
        lines = f.readlines()
        for line in lines:
            if 'current' in line:
                results = line.strip()
    if results is None:
        print 'Can not get the begin index in log'
        exit()
    else:
        begin_param = {}
        for param in results.split(';'):
            key, value = param.split(':', 1)
            if value.isdigit():
                begin_param[key] = int(value)
            else:
                begin_param[key] = value
        return begin_param


def main_process():
    time.sleep(2)
    log.error('current_url:%s;record_type:%d;date_index:%d;begin_index:%d;begin_category:%d' %
              (paramets['current_url'], paramets['record_type'], paramets['date_index'],
               paramets['begin_index'], paramets['begin_category']))
    paramets['is_first_time'] = True
    for item in settings.category_urls[paramets['begin_category']::]:
        log.error('---Step to : ' + paramets['current_url'] + '------')
        try:
            get_second_data(item['url'])
        except Exception as e:
            time.sleep(2)
            restart_program(error=e)


if __name__ == '__main__':
    table_schema, engine = sql.init_connection(DB_TMP_TABLE)
    #sql.init_temp_table(DB_TMP_TABLE, DB_TABLE)
    try:
        driver, headers = init_driver()
    except Exception as e:
        time.sleep(1800)
        restart_program(error=e)
    paramets = get_current_point('hot_shop_process.log')
    log = log_sys.log_init('hot_shop')
    main_process()
    output_data_to_db(is_all=True)
