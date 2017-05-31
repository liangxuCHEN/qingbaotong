# -*- coding: utf-8 -*-
from pyquery import PyQuery as pq
import urllib
import sys
import urllib2
import cookielib
import os
import zlib
from selenium import webdriver
from crawl_qbt_to_sql_main import login
import settings

def demo1():
    # 获取Cookiejar对象（存在本机的cookie消息）
    cookie = cookielib.CookieJar()
    # 自定义opener,并将opener跟CookieJar对象绑定
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    # 安装opener,此后调用urlopen()时都会使用安装过的opener对象
    urllib2.install_opener(opener)

    url = "http://www.baidu.com"
    urllib2.urlopen(url)


def demo2(url, headers):
    # profile_dir = r'C:\Users\Administrator\AppData\Roaming\Mozilla\Firefox\Profiles\l8rzesb2.selenium'
    # ckjar = cookielib.MozillaCookieJar(
    #     os.path.join(profile_dir, 'cookies.txt'))



    # req = urllib2.Request(url, postdata, header)
    req = urllib2.Request(url, headers=headers)
    # req.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')

    # opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(ckjar))
    urllib_opener = urllib2.build_opener()

    f = urllib_opener.open(req)
    htm = f.read()
    htm = zlib.decompress(htm, 16+zlib.MAX_WBITS)
    f.close()
    return htm


def demo3():
    # os.environ['webdriver.gecko.driver'] = r"D:\geckodriver.exe"
    profile_dir = r'C:\Users\Administrator\AppData\Roaming\Mozilla\Firefox\Profiles\l8rzesb2.selenium'
    driver = webdriver.Firefox(profile_dir, executable_path=r'D:\geckodriver\geckodriver.exe')
    login(driver, settings.LOGIN_NAME, settings.PASSWORD)

    return driver.get_cookies()


if __name__ == '__main__':
    # doc = pq('https://segmentfault.com/a/1190000005182997')
    # print doc.html()
    # lis = doc('li')
    # for li in lis.items():
    #     print li.html()
    # print li.text()    # 遍历所有
    # h = doc('h2')
    # hs = h.attr('id', 'articleHeader0')
    # for i in hs:
    #     print i.text

    # p = pq('<p id="hello" class="hello"></p>')('p')
    # print p.addClass('beauty')
    # print p.removeClass('hello')
    # print p.css('font-size', '16px')
    # print p.css({'background-color': 'yellow'})

    # print pq('192.168.3.187/single_user_rate', {'foo': 'bar'}, method='post', verify=True)
    headers = {
        'Host': 'qbt.ecdataway.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Referer': 'http://qbt.ecdataway.com/stat?cid=50008164',
        'Cookie': 'UM_distinctid=15c52a5798ec5-00160e9c636d288-44504130-13c680-15c52a5798f276; CNZZDATA1258713365=79147817-1496034613-http%253A%252F%252Fwww.ecdataway.com%252F%7C1496197923; Hm_lvt_d614fba9d6d7554f5977bd1d74235343=1496138486,1496193793; PHPSESSID=e9j9obkg2nqgm4lt936pm6q0q6; Hm_lpvt_d614fba9d6d7554f5977bd1d74235343=1496199221',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }



    qbt_cookie = demo3()
    # qbt_cookie = [{u'domain': u'.ecdataway.com', u'secure': False, u'value': u'15c52a5798ec5-00160e9c636d288-44504130-13c680-15c52a5798f276', u'expiry': None, u'path': u'/', u'httpOnly': False, u'name': u'UM_distinctid'}, {u'domain': u'qbt.ecdataway.com', u'secure': False, u'value': u'79147817-1496034613-http%253A%252F%252Fwww.ecdataway.com%252F%7C1496196990', u'expiry': None, u'path': u'/', u'httpOnly': False, u'name': u'CNZZDATA1258713365'}, {u'domain': u'.qbt.ecdataway.com', u'secure': False, u'value': u'1496138486,1496193793,1496201203', u'expiry': None, u'path': u'/', u'httpOnly': False, u'name': u'Hm_lvt_d614fba9d6d7554f5977bd1d74235343'}, {u'domain': u'.qbt.ecdataway.com', u'secure': False, u'value': u'1496201203', u'expiry': None, u'path': u'/', u'httpOnly': False, u'name': u'Hm_lpvt_d614fba9d6d7554f5977bd1d74235343'}, {u'domain': u'qbt.ecdataway.com', u'secure': False, u'value': u'ashnggb1535e99lk6ga5850ls7', u'expiry': None, u'path': u'/', u'httpOnly': False, u'name': u'PHPSESSID'}]
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
        'Referer': 'http://qbt.ecdataway.com/stat?rcid=2011010116&cid=50008164',
        'Cookie': cookie_text[:-1],
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    url = 'http://qbt.ecdataway.com/stat?rcid=2011010116&cid=50015886'
    r = demo2(url, headers)
    print pq(r).html()
    sub_items = pq(r)('#sidebar_category')
    print len(sub_items)
    sub_urls = []
    sub_title = []
    for id_sub_item in range(0, len(sub_items)):
        print id_sub_item
        sub_url = sub_items('li').eq(id_sub_item).attr('href')
        sub_text = sub_items('a').eq(id_sub_item).text()
        if ('stat' in sub_url) and (sub_text != ""):
            sub_urls.append(sub_url)
            sub_title.append(sub_text)
    print sub_urls
