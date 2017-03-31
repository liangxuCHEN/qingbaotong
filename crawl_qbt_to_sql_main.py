# -*- coding: utf-8 -*-
import log_sys
import os
import sys
import re
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
# from selenium.webdriver.support.ui import WebDriverWait
import settings
import sql
import time


def init():
    os.environ['webdriver.gecko.driver'] = "D:\geckodriver.exe"
    profile_dir = r'C:\Users\Administrator\AppData\Roaming\Mozilla\Firefox\Profiles\70usgfgt.selenium'
    driver = webdriver.Firefox(profile_dir)
    time.sleep(2)
    return driver


def login(driver, username, password):
    driver.get("http://www.qbtchina.com/site/login")
    time.sleep(2)
    user = driver.find_element_by_id('LoginForm_username')
    user.clear()
    time.sleep(0.5)
    user.send_keys(username)
    driver.find_element_by_id('LoginForm_password').send_keys(password)
    button = driver.find_element_by_xpath('//*[@id="login-form"]/div[2]/div/span/a')
    button.click()
    time.sleep(2)


def get_table_value(driver):
    global paramets
    driver.find_element_by_id('submit-button').click()
    # get date from table, if it can not get the table
    # mostly it is the html load delay, just try again!
    time.sleep(3)
    while driver.execute_script("return document.readyState") != 'complete':
        time.sleep(2)
        # print 'wait 3  !!!'
    try:
        time.sleep(2)
        table = driver.find_element_by_id('set1')
    except NoSuchElementException:
        time.sleep(5)
        table = driver.find_element_by_id('set1')

    count = 0
    tbody = table.find_elements_by_tag_name('td')
    tmp_item = []
    tmp_data = []
    num_column = settings.MAIN_TABLE_NUM_COLUMNS

    for cell in tbody:
        tmp_item.append(cell.text)
        count += 1
        if count == num_column:
            tmp_data.append((
                paramets['category_id'].encode('utf8'),
                paramets['pos_id'],
                paramets['pos_name'],
                tmp_item[0].replace('\'', ''),
                int(tmp_item[1].replace(',', '')),
                tmp_item[2].encode('utf8'),
                tmp_item[3].encode('utf8'),
                float(tmp_item[4].replace(',', '')),
                tmp_item[5].replace(',', '').encode('utf8'),
                tmp_item[6].replace(',', '').encode('utf8'),
                (paramets['date'] + '01').encode('utf8'),
                int(paramets['record_type']),
            ))
            tmp_item = []
            count = 0

    try:
        sql.logo_item_to_sql(tmp_data)
    except:
        log.error('Error : output to SQL ')
        # print tmp_data


def chose_date(driver):
    global paramets
    time.sleep(3)
    for date_select in settings.date_chose_main[paramets['date_index']:]:
        log.error('current_url:%s;record_type:%d;date_index:%d;begin_index:%d;begin_sub_index:%d;begin_category:%d' %
                  (paramets['current_url'], paramets['record_type'], paramets['date_index'],
                   paramets['begin_index'], paramets['begin_sub_index'], paramets['begin_category']))
        try:
            res = re.findall('pos=.*', paramets['current_url'])
            paramets['pos_id'] = res[0][4::]
            driver.find_element_by_xpath("//select[@name='period_start_prop']/option[@value='" + date_select + "']").click()
        except:
            continue
            # print date_select
            # print 'have level 4 categroy !'

        paramets['date'] = date_select
        get_table_value(driver)
        paramets['date_index'] += 1
    # 恢复初始值
    paramets['date_index'] = 0


def get_data(driver, url):
    global paramets
    driver.get(url)
    time.sleep(2)
    while driver.execute_script("return document.readyState") != 'complete':
        time.sleep(2)
        # print 'wait !!!'

    driver.find_element_by_xpath("//*[@name='chart_type'][@value='3']").click()

    # 先取天猫数据，再取淘宝
    if paramets['is_first_time']:
        # print 'first time'
        if paramets['record_type'] == 1:
            driver.find_element_by_xpath("//*[@name='is_mall'][@value='" + str(paramets['record_type']) + "']").click()
            chose_date(driver)
            driver.find_element_by_xpath("//*[@name='is_mall'][@value='0']").click()
            paramets['record_type'] = 0
            chose_date(driver)
        else:
            driver.find_element_by_xpath("//*[@name='is_mall'][@value='" + str(paramets['record_type']) + "']").click()
            chose_date(driver)
        paramets['is_first_time'] = False
    else:
        # firstly, the date from tmall
        driver.find_element_by_xpath("//*[@name='is_mall'][@value='1']").click()
        paramets['record_type'] = 1
        chose_date(driver)
        # secondly, the date from taobao
        driver.find_element_by_xpath("//*[@name='is_mall'][@value='0']").click()
        paramets['record_type'] = 0
        chose_date(driver)
    # 恢复初始值
    paramets['record_type'] = 1


def get_category_urls(driver, url):
    global paramets
    driver.get(url)
    time.sleep(4)
    sub_items = driver.find_element_by_id('sidebar_category')
    sub_items = sub_items.find_elements_by_tag_name('a')
    # Need to chang when is well
    sub_urls = []
    sub_title = []
    # print 'sub item number : ', len(sub_items)
    for sub_item in sub_items[paramets['begin_index']::]:
        try:
            sub_url = sub_item.get_attribute("href")
        except:
            sub_url = ""
        if ('stat' in sub_url) and (sub_item.text != ""):
            sub_urls.append(sub_url)
            sub_title.append(sub_item.text)

    for i in range(0, len(sub_urls)):
        # print sub_title[i] + ":" + sub_urls[i]
        log.error(sub_title[i] + ":" + sub_urls[i])
        driver.get(sub_urls[i])
        time.sleep(3)
        try:
            sub_sub_items = driver.find_element_by_id('sidebar_category')
            sub_sub_items = sub_sub_items.find_elements_by_tag_name('a')
        except NoSuchElementException:
            time.sleep(3)
            sub_sub_items = driver.find_element_by_id('sidebar_category')
            sub_sub_items = sub_sub_items.find_elements_by_tag_name('a')
        # Need to chang when is well
        sub_sub_urls = []
        sub_sub_title = []
        for sub_item in sub_sub_items[paramets['begin_sub_index']::]:
            try:
                sub_url = sub_item.get_attribute("href")
            except:
                sub_url = ""
            if ('stat' in sub_url) and (sub_item.text != ""):
                sub_sub_urls.append(sub_url)
                sub_sub_title.append(sub_item.text)

        for j in range(0, len(sub_sub_urls)):
            # print sub_sub_title[j] + ":" + sub_sub_urls[j]
            log.error(sub_sub_title[j] + ":" + sub_sub_urls[j])
            paramets['current_url'] = sub_sub_urls[j]
            paramets['pos_name'] = sub_sub_title[j]
            time.sleep(1)
            get_data(driver, sub_sub_urls[j])
            paramets['begin_sub_index'] += 1

        paramets['begin_sub_index'] = 1
        paramets['begin_index'] += 1


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


def restart_program(driver, error=None):
    """Restarts the current program.
    Note: this function does not return. Any cleanup action (like
    saving data) must be done before calling this function."""
    global paramets
    file_out = open('main_process.log', 'a')
    file_out.write('current_url:%s;record_type:%d;date_index:%d;begin_index:%d;begin_sub_index:%d;begin_category:%d\n' %
                   (paramets['current_url'], paramets['record_type'], paramets['date_index'],
                    paramets['begin_index'], paramets['begin_sub_index'], paramets['begin_category']))
    file_out.close()
    driver.quit()
    log.error(error)
    python = sys.executable
    os.execl(python, python, *sys.argv)


def main_process(driver):
    global paramets
    res = re.findall('cid=[0-9].*&', paramets['current_url'])
    paramets['category_id'] = res[0][4:-1]

    for item in settings.category_urls[paramets['begin_category']:]:
        # print (item['category'])
        log.error('-------beging: ' + item['category'] + "--------")
        try:
            get_category_urls(driver, item['url'])
        except Exception, e:
            restart_program(driver, error=e)
        # new category, index should be return first one
        paramets['begin_index'] = 1
        paramets['begin_sub_index'] = 1
        paramets['begin_category'] += 1
    # print ("THE END!")

if __name__ == "__main__":
    driver = init()
    try:
        login(driver, settings.LOGIN_NAME, settings.PASSWORD)
    except Exception, e:
        time.sleep(1800)
        restart_program(driver, error=e)
    paramets = get_current_point('main_process.log')
    log = log_sys.log_init('main')
    log.error('current_url:%s;record_type:%d;date_index:%d;begin_index:%d;begin_sub_index:%d;begin_category:%d' %
              (paramets['current_url'], paramets['record_type'], paramets['date_index'],
               paramets['begin_index'], paramets['begin_sub_index'], paramets['begin_category']))
    time.sleep(2)
    paramets['is_first_time'] = True
    main_process(driver)

