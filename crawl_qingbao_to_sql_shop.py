# -*- coding: utf-8 -*-
from selenium import webdriver
import re
import os
import sys
import time
import settings
import sql
import log_sys
from crawl_qbt_to_sql_main import init, login, get_current_point

"""
content is the data
Record type = Tmall or taobao
num_col is the number of columns
"""

DB_TMP_TABLE = 'T_Data_HotShopTemp'
DB_TABLE = 'T_Data_HotShop'
DB_PROCESS = 'P_Merge_HotShop'
driver = paramets = log = None
tmp_insert_data = []
engine = table_schema = None


def get_top_shop_table_value(categoryid, record_type, date_chose=None):
    time.sleep(1)
    while driver.execute_script("return document.readyState") != 'complete':
        time.sleep(2)
        # print 'wait 2  !!!'
    for date_select in date_chose[paramets['date_index']:]:
        log.error('current_url:%s;record_type:%d;date_index:%d;begin_index:%d;begin_category:%d' %
                  (paramets['current_url'], paramets['record_type'], paramets['date_index'],
                   paramets['begin_index'], paramets['begin_category']))
        try:
            driver.find_element_by_xpath("//select[@id='period']/option[@value='" + date_select + "']").click()
            driver.find_element_by_xpath("//select[@id='period_last']/option[@value='" + date_select + "']").click()
        except:
            log.error('record_type:%d;date_index:%d;begin_index:%d;begin_category:%d #### have error in chose data:%s' %
                      (paramets['record_type'], paramets['date_index'],
                       paramets['begin_index'], paramets['begin_category'], date_select))

        # get date from table, if it can not get the table
        # mostly it is the html load delay, just try again!
        driver.find_element_by_id('submit-button').click()
        if record_type == 0:
            while driver.execute_script("return document.readyState") == 'complete':
                pass
            time.sleep(4)
        else:
            time.sleep(10)

        table = driver.find_element_by_xpath("//table[contains(@class,'items')]")

        count = 0
        tbody = table.find_elements_by_tag_name('td')
        tmp_item = []
        num_column = settings.HOT_SHOP_NUM_COLUMNS
        for cell in tbody:
            # column 1,2,7 have tag a or img, so they are different way to collect
            if count % num_column == 1:
                sub_cell = cell.find_element_by_tag_name('a')
                tmp_item.append(sub_cell.get_attribute("href"))
                tmp_item.append(sub_cell.text)
            else:
                tmp_item.append(cell.text)

            count += 1
            if count == num_column:
                tmp_insert_data.append({
                    'CategoryId': categoryid,
                    'HotRange': int(tmp_item[0]),
                    'ShopName': tmp_item[2],
                    'ShopURL': tmp_item[1].replace('\'', '').encode('utf8'),
                    'SalesCnt': int(tmp_item[3].replace(',', '')),
                    'SalesMoney': int(tmp_item[4].replace(',', '')),
                    'city': tmp_item[5],
                    'RecordDate': (date_select+"01"),
                    'RecordType': record_type
                })

                tmp_item = []
                count = 0

        # output to DB
        output_data_to_db()

        paramets['date_index'] += 1

    paramets['date_index'] = 0


def get_hot_sale_data(url, type_data='item', date_chose=None):
    if type_data == 'item':
        # chose top hot sale items
        driver.get(url+'&type=4')
    elif type_data == 'shop':
        # chose top hot shop
        driver.get(url + '&type=3')
    # print url
    res = re.findall('&cid=[0-9].*', url)
    categoryId = res[0][5:]
    time.sleep(3)
    if paramets['is_first_time']:
        # print 'first time'
        if paramets['record_type'] == 1:
            # firstly, the date from tmall
            driver.find_element_by_xpath("//*[@name='is_mall'][@value='" + str(paramets['record_type']) + "']").click()
            get_top_shop_table_value(categoryId, record_type=1, date_chose=date_chose)
            # the date from taobao
            driver.find_element_by_xpath("//*[@name='is_mall'][@value='0']").click()
            paramets['record_type'] = 0
            get_top_shop_table_value(categoryId, record_type=0, date_chose=date_chose)
        else:
            # the date from taobao
            driver.find_element_by_xpath("//*[@name='is_mall'][@value='0']").click()
            paramets['record_type'] = 0
            get_top_shop_table_value(categoryId, record_type=0, date_chose=date_chose)
        paramets['is_first_time'] = False
    else:
        # firstly, the date from tmall
        driver.find_element_by_xpath("//*[@name='is_mall'][@value='1']").click()
        paramets['record_type'] = 1
        get_top_shop_table_value(categoryId, record_type=1, date_chose=date_chose)
        # secondly, the date from taobao
        driver.find_element_by_xpath("//*[@name='is_mall'][@value='0']").click()
        paramets['record_type'] = 0
        get_top_shop_table_value(categoryId, record_type=0, date_chose=date_chose)

    paramets['record_type'] = 1


def get_second_data(url):
    driver.get(url)
    time.sleep(1)
    sub_items = driver.find_element_by_id('sidebar_category')
    sub_items = sub_items.find_elements_by_tag_name('a')

    sub_urls = []
    sub_title = []
    for sub_item in sub_items[1::]:
        try:
            sub_url = sub_item.get_attribute("href")
        except:
            sub_url = ""
        if ('stat' in sub_url) and (sub_item.text != ""):
            sub_urls.append(sub_url)
            sub_title.append(sub_item.text)

    # begin at N, it the programme break down
    for i in range(paramets['begin_index'], len(sub_urls)):
        # print ('-item--' + sub_title[i])
        get_hot_sale_data(sub_urls[i], type_data='shop', date_chose=settings.shop_date_chose)
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

if __name__ == "__main__":
    table_schema, engine = sql.init_connection(DB_TMP_TABLE)
    # sql.init_temp_table(DB_TMP_TABLE, DB_TABLE)
    driver = init()
    try:
        login(driver, settings.LOGIN_NAME, settings.PASSWORD)
    except Exception as e:
        time.sleep(1800)
        restart_program(error=e)

    paramets = get_current_point('hot_shop_process.log')
    log = log_sys.log_init('hot_shop')
    main_process()
    output_data_to_db(is_all=True)

    # 把临时表数据合并到实际数据表
    # sql.exec_db_merge_function(DB_PROCESS)
