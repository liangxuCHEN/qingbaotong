# -*- coding: utf-8 -*-
import re
import log_sys
import settings
import crawl_qbt_to_sql_main as tool
import time
from urllib import unquote as decode_ch
import sql
import os
import sys

"""
本脚步爬取情报通的关注店铺所有宝贝的价格数据， 现在已有商铺33个，如果有变化，请在setting.follow_shop_urls更改。
并且开启 sql.is_exist_item_struct(item_struct) 这个函数，
follow_shop_log 记录爬虫的进度
"""
DB_TMP_TABLE = 'T_Data_AnalyseItemTemp'
DB_TABLE = 'T_Data_AnalyseItem'
DB_PROCESS_ITEM = 'P_Merge_AnalyseItem'
DB_PROCESS_ITEMSTRUCT = 'P_Merge_ItemStruct'
driver = paramets = log = None


def get_items_value(data_dic, data_list):
    for item_id in data_list:
        url, item_url, item_name, category = data_dic[item_id]
        paramets['current_url'] = url
        log.error('current_url:%s;index_item:%d;index_shop:%d' %
                  (paramets['current_url'], paramets['index_item'], paramets['index_shop']))
        item_struct = (
            paramets['sid'],
            paramets['shop_name'].replace('\'', ''),
            item_id,
            item_url,
            item_name.replace('\'', ''),
            category.replace('\'', ''),
        )
        # output item struct to sql
        sql.add_item_struct(item_struct)

        driver.get(url)
        time.sleep(2)
        # print settings.follow_shop_start_date
        driver.execute_script("document.getElementById('start_date').value = '" + settings.follow_shop_start_date + "'")
        driver.execute_script("document.getElementById('end_date').value = '" + settings.follow_shop_end_date + "'")
        driver.find_element_by_xpath("//*[@name='is_chart'][@value='1']").click()
        driver.find_element_by_name("submit").click()

        time.sleep(8)
        while driver.execute_script("return document.readyState") != 'complete':
            time.sleep(3)
        table = driver.find_element_by_tag_name('tbody')
        td_data = table.find_elements_by_tag_name('td')

        tmp_item = []
        tmp_data = []
        i = 0
        for cell in td_data:
            tmp_item.append(cell.text)
            i += 1
            if i == settings.follow_shop_num:
                tmp_data.append((
                    paramets['sid'].encode('utf8'),
                    item_id.encode('utf8'),
                    float(tmp_item[3].replace(',', '')) if tmp_item[3] != '' else 0,
                    float(tmp_item[1].replace(',', '')) if tmp_item[1] != '' else 0,
                    float(tmp_item[2].replace(',', '')) if tmp_item[2] != '' else 0,
                    tmp_item[0].encode('utf8')
                ))
                i = 0
                tmp_item = []
        # the last one is the sum result
        sql.analyse_item_to_sql(tmp_data[:-1], DB_TMP_TABLE)

        # 完成一个宝贝，加一
        paramets['index_item'] += 1


def get_items_urls_value():
    table = driver.find_element_by_class_name('text-center')
    while driver.execute_script("return document.readyState") != 'complete':
        time.sleep(3)
        # print 'wait load'
    all_items = table.find_elements_by_tag_name('a')

    items_data_dic = {}
    items_list = []
    # 记录宝贝所在的商店，还有它的名字，网址
    for cell in all_items:
        item_url = cell.get_attribute("href")
        if 'avgPriceTrend' in item_url:
            match_group = re.match(r".*tb_item_id=(.*)&.*", item_url)
            if match_group is not None:
                items_list.append(match_group.group(1))
                items_data_dic[match_group.group(1)] = []
                items_data_dic[match_group.group(1)].append(item_url)
            else:
                log.error('Step 1 the item : ' + item_url + 'has not enough information')
                # print('Step 1 the item : ' + item_url + 'has not enough information')

    item_details = driver.find_elements_by_class_name('text-left')
    i = 0
    item_id = ''
    for data_item in item_details:
        # item information
        if i % 2 == 0:
            # get item_id
            item_url = data_item.find_element_by_tag_name('a').get_attribute("href")
            match_group = re.match(r".*id=(.*)", item_url)
            if match_group is not None:
                item_id = match_group.group(1)
                items_data_dic[item_id].append(item_url)
                items_data_dic[item_id].append(data_item.text)
            else:
                log.error('Step 2 the item : ' + item_url + 'has not enough information')
                # print('Step 2 the item : ' + item_url + 'has not enough information')
        # item category information
        else:
            items_data_dic[item_id].append(data_item.text)

        i += 1

    return {'dic': items_data_dic, 'list': items_list}


def get_shop_value(url):
    driver.get(url)
    time.sleep(2)
    current_url = driver.current_url

    match_group = re.match(r".*sid=(.*)&amp;nick=(.*)", current_url)
    if match_group is not None:
        paramets['sid'] = match_group.group(1)
        paramets['shop_name'] = decode_ch(str(match_group.group(2))).decode('utf8')
    else:
        log.error('Step 0 the item : ' + current_url + 'has not enough information')
        # ('Step 0 the item : ' + current_url + 'has not enough information')

    res_dic = {}
    res_list = []
    # 多页内容
    pages = driver.find_elements_by_class_name('page')
    if pages is not None:
        res = get_items_urls_value()
        res_dic.update(res['dic'])
        res_list += res['list']
        for i_page in range(1, len(pages)):
            # 进入下一页
            scrpit_text = "document.getElementsByClassName('page')[" + str(i_page) + \
                          "].getElementsByTagName('a')[0].click()"
            driver.execute_script(scrpit_text)
            time.sleep(2)
            res = get_items_urls_value()
            res_dic.update(res['dic'])
            res_list += res['list']
    else:
        return get_items_urls_value()

    return {'dic': res_dic, 'list': res_list}


def restart_program(error):
    """Restarts the current program.
    Note: this function does not return. Any cleanup action (like
    saving data) must be done before calling this function."""
    file_out = open('follow_shop_process.log', 'a')
    file_out.write('current_url:%s;index_item:%d;index_shop:%d \n' %
                   (paramets['current_url'], paramets['index_item'], paramets['index_shop']))
    file_out.close()
    log.error(error)
    driver.quit()
    sql.exec_db_merge_function(DB_PROCESS_ITEM)
    python = sys.executable
    os.execl(python, python, *sys.argv)

if __name__ == '__main__':
    driver = tool.init()
    try:
        tool.login(driver, settings.LOGIN_NAME, settings.PASSWORD)
        sql.init_temp_table(DB_TMP_TABLE, DB_TABLE)
    except Exception, e:
        time.sleep(1800)
        restart_program(e)

    paramets = tool.get_current_point('follow_shop_process.log')
    log = log_sys.log_init('follow_shop')
    time.sleep(2)
    log.error('current_url:%s;index_item:%d;index_shop:%d' %
              (paramets['current_url'], paramets['index_item'], paramets['index_shop']))

    for shop_url in settings.follow_shop_urls[paramets['index_shop']:]:
        log.error('---Step to : ' + paramets['current_url'] + '------')
        try:
            res = get_shop_value('http://www.qbtchina.com' + shop_url)
            time.sleep(3)
            get_items_value(res['dic'], res['list'][paramets['index_item']:])
        except Exception, e:
            restart_program(e)
        # new category, index should be return first one
        paramets['index_item'] = 0
        paramets['index_shop'] += 1

    # 把临时表数据合并到实际数据表
    sql.exec_db_merge_function(DB_PROCESS_ITEM)
    sql.exec_db_merge_function(DB_PROCESS_ITEMSTRUCT)
