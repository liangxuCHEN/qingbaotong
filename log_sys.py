# -*- coding: utf-8 -*-
import logging
import re
import time


def log_init(file_name, level=None):
    """
    logging.debug('This is debug message')
    logging.info('This is info message')
    logging.warning('This is warning message')
    """
    file_name = file_name + str(int(time.time())) + '.log'
    file_out = open(file_name, 'w')
    file_out.write('---------------------begin log------------------')
    file_out.close()
    if level == 'DEBUG':
        level = logging.DEBUG
    else:
        level = logging.ERROR
    logging.basicConfig(level=level,
                        format='%(asctime)s [line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        filename=file_name,
                        filemode='w')
    return logging

if __name__ == "__main__":
    with open('E:\qingbaotong\myapp.log') as f:
        lines = f.readlines()
        for line in lines:
            if 'Current' in line:
                res = re.findall('http.*', line)
                res = res[0].split(';')
                print res
