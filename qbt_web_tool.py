import urllib2
from urllib import urlencode
import time
import zlib
from selenium import webdriver
import settings


def login(driver, username, password):
    driver.get("http://qbt.ecdataway.com/site/login")
    time.sleep(20)
    user = driver.find_element_by_id('LoginForm_username')
    user.clear()
    time.sleep(0.5)
    user.send_keys(username)
    driver.find_element_by_id('LoginForm_password').send_keys(password)
    button = driver.find_element_by_xpath('//*[@id="login-form"]/div[2]/div/span/a')
    button.click()
    time.sleep(2)


def init_driver():
    profile_dir = r'C:\Users\Administrator\AppData\Roaming\Mozilla\Firefox\Profiles\l8rzesb2.selenium'
    driver = webdriver.Firefox(profile_dir, executable_path=r'D:\geckodriver\geckodriver.exe')
    login(driver, settings.LOGIN_NAME, settings.PASSWORD)
    time.sleep(1)
    # driver.get('http://qbt.ecdataway.com/stat?rcid=2011010116&cid=50001705')
    qbt_cookie = driver.get_cookies()
    cookie_text = ""
    for c in qbt_cookie:
        cookie_text += u'='.join([c[u'name'], c[u'value']]) + u';'
    print cookie_text
    headers = {
        'Host': 'qbt.ecdataway.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Referer': '',
        'Cookie': cookie_text[:-1],
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    return driver, headers


def get_html(url, headers, data=None):
    headers['Referer'] = url
    if data:
        data = urlencode(data)
        req = urllib2.Request(url, data, headers=headers)
    else:
        req = urllib2.Request(url, headers=headers)

    urllib_opener = urllib2.build_opener()
    f = urllib_opener.open(req)
    htm = f.read()
    htm = zlib.decompress(htm, 16+zlib.MAX_WBITS)
    f.close()
    return htm