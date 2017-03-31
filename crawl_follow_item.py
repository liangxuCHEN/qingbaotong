# -*- coding: utf-8 -*-
import re
import log_sys
import settings
import crawl_qbt_to_sql_main as tool
import time
from bs4 import BeautifulSoup
import sql
import os
import sys


def get_items_value(driver, data_dic, data_list):
    global paramets
    for item_id in data_list:
        url, item_url, item_name, category, shop_name = data_dic[item_id]
        paramets['current_url'] = url
        log.error('current_url:%s;index_item:%d;index_group:%d' %
                  (paramets['current_url'], paramets['index_item'], paramets['index_group']))
        match_group = re.match(r".*sid=(.*)&tb_item_id.*", url)
        if match_group is not None:
            sid = match_group.group(1)
        else:
            log.error('Step 0 the item : ' + url + 'has not enough information')

        item_struct = (
            sid,
            shop_name.replace('\'', ''),
            item_id,
            item_url,
            item_name.replace('\'', ''),
            category.replace('\'', ''),
        )
        # output item struct to sql

        res = sql.is_exist_item_value(item_struct, settings.follow_item_start_date)

        if res:
            log.error('item %s is exist !' % item_id)
            # print('item %s is exist !' % item_id)
        else:
            # 在关注商店里面没有重复的宝贝，继续添加
            driver.get(url)
            time.sleep(2)
            driver.execute_script("document.getElementById('start_date').value = '" + settings.follow_item_start_date + "'")
            driver.execute_script("document.getElementById('end_date').value = '" + settings.follow_item_end_date + "'")
            driver.find_element_by_xpath("//*[@name='is_chart'][@value='1']").click()
            driver.find_element_by_name("submit").click()

            time.sleep(10)
            try:
                table = driver.find_element_by_tag_name('tbody')
            except:
                time.sleep(8)
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
                        sid.encode('utf8'),
                        item_id.encode('utf8'),
                        float(tmp_item[3].replace(',', '')) if tmp_item[3] != '' else 0,
                        float(tmp_item[1].replace(',', '')) if tmp_item[1] != '' else 0,
                        float(tmp_item[2].replace(',', '')) if tmp_item[2] != '' else 0,
                        tmp_item[0].encode('utf8')
                    ))
                    i = 0
                    tmp_item = []
            # the last one is the sum result
            sql.analyse_item_to_sql(tmp_data[:-1])

        # 完成一个宝贝，加一
        paramets['index_item'] += 1


def get_items_urls_value(driver):
    global paramets
    while driver.execute_script("return document.readyState") != 'complete':
        time.sleep(3)
        # print 'wait load'
    table = driver.find_element_by_id('all_goods')

    all_items = table.find_elements_by_tag_name('a')

    items_data_dic = {}
    items_list = []
    # 记录宝贝所在的商店，还有它的名字，网址
    for cell in all_items:
        item_url = cell.get_attribute("href")
        if 'avgPriceTrend' in item_url:
            match_group = re.match(r".*tb_item_id=(.*)&is_mall.*", item_url)
            if match_group is not None:
                items_list.append(match_group.group(1))
                items_data_dic[match_group.group(1)] = []
                items_data_dic[match_group.group(1)].append(item_url)
            else:
                log.error('Step 1 the item : ' + item_url + 'has not enough information')
                # print('Step 1 the item : ' + item_url + 'has not enough information')

    soup = BeautifulSoup(driver.page_source, "html.parser")
    item_details = soup.find_all('td', attrs={'align': 'left'})
    i = 0
    item_id = ''
    for data_item in item_details:
        # 找到宝贝的名字
        if data_item.get('width') == "350":
            # get item_id
            item_url = data_item.a.attrs['href']
            match_group = re.match(r".*id=(.*)", item_url)
            if match_group is not None:
                item_id = match_group.group(1)
                items_data_dic[item_id].append(item_url)
                items_data_dic[item_id].append(data_item.a.string)
            else:
                log.error('Step 2 the item : ' + item_url + 'has not enough information')
                # print('Step 2 the item : ' + item_url + 'has not enough information')
        # item category information
        elif data_item.a.string == u'住宅家具':
            sub_a = data_item.find_all('a')
            category = ''
            for text in sub_a:
                category += text.string + '>'
            items_data_dic[item_id].append(category[:-1])
        else:
            items_data_dic[item_id].append(data_item.a.string)

        i += 1

    return {'dic': items_data_dic, 'list': items_list}


def get_group_value(driver, url):
    # 取得一组宝贝里面的所有宝贝链接
    global paramets
    driver.get(url)
    time.sleep(2)
    res_dic = {}
    res_list = []
    # 多页内容
    pages = driver.find_elements_by_class_name('page')
    if pages is not None:
        res = get_items_urls_value(driver)
        res_dic.update(res['dic'])
        res_list += res['list']
        for i_page in range(1, len(pages)):
            # 进入下一页
            scrpit_text = "document.getElementsByClassName('page')[" + str(i_page) + \
                          "].getElementsByTagName('a')[0].click()"
            driver.execute_script(scrpit_text)
            time.sleep(2)
            res = get_items_urls_value(driver)
            res_dic.update(res['dic'])
            res_list += res['list']
    else:
        return get_items_urls_value(driver)

    return {'dic': res_dic, 'list': res_list}


def restart_program(error):
    """Restarts the current program.
    Note: this function does not return. Any cleanup action (like
    saving data) must be done before calling this function."""
    global paramets
    file_out = open('follow_item_process.log', 'a')
    file_out.write('current_url:%s;index_item:%d;index_shop:%d\n' %
                   (paramets['current_url'], paramets['index_item'], paramets['index_shop']))
    file_out.close()
    log.error(error)
    driver.quit()
    python = sys.executable
    os.execl(python, python, *sys.argv)


def get_urls_value(driver):
    global paramets
    while driver.execute_script("return document.readyState") != 'complete':
        time.sleep(3)
    table = driver.find_element_by_class_name('search_result_table')
    all_items = table.find_elements_by_tag_name('a')

    items_list = []
    for cell in all_items:
        try:
            item_url = cell.get_attribute("href")
            if 'itemlist' in item_url:
                    items_list.append(item_url)
        except:
            pass

    return items_list


def get_all_urls(driver):
    # 取得所有宝贝分组
    driver.get('http://www.qbtchina.com/item')
    time.sleep(2)
    res_list = []
    # 多页内容
    pages = driver.find_elements_by_class_name('page')
    if pages is not None:
        res_list += get_urls_value(driver)
        for i_page in range(1, len(pages)):
            # 进入下一页
            scrpit_text = "document.getElementsByClassName('page')[" + str(i_page) + \
                          "].getElementsByTagName('a')[0].click()"
            driver.execute_script(scrpit_text)
            time.sleep(2)
            res_list += get_urls_value(driver)
    else:
        return get_urls_value(driver)

    return res_list


if __name__ == '__main__':

    driver = tool.init()
    try:
        tool.login(driver, settings.LOGIN_NAME, settings.PASSWORD)
    except Exception, e:
        time.sleep(20)
        restart_program(e)

    paramets = tool.get_current_point('follow_item_process.log')
    log = log_sys.log_init('follow_item')
    time.sleep(2)
    log.error('current_url:%s;index_item:%d;index_group:%d' %
              (paramets['current_url'], paramets['index_item'], paramets['index_group']))

    # 获取全部分组url
    all_urls = get_all_urls(driver)

    for url in all_urls[paramets['index_group']:]:
        log.error('---Step to : ' + paramets['current_url'] + '------')
        try:
            res = get_group_value(driver, url)
            time.sleep(3)
            get_items_value(driver, res['dic'], res['list'][paramets['index_item']:])
        except Exception, e:
            restart_program(e)
        # new category, index should be return first one
        paramets['index_item'] = 0
        paramets['index_group'] += 1

    # print('Well done, it is the END !')
