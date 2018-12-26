# --*-- coding:utf-8 --*--
"""
@author wht
@time  2018/9/17 上午10:51
"""

from datetime import date
from datetime import timedelta
import logging
import re
from requests.sessions import Session
import os
import time

logger = logging.getLogger()


def date_add_day(day=0, format_str="%Y-%m-%d"):
    """
    日期的加减
    :param day:
    :param format_str:
    :return:
    """
    try:
        dated = date.today()+timedelta(days=day)
        n_day = dated.strftime(format=format_str)
    except Exception as e:
        raise e
    return n_day


zh_pattern = re.compile('^[\u4e00-\u9fa5]+$')


def all_line_is_zh(word):
    """
    判断传入字符串是否包含中文
    :param word: 待判断字符串
    :return: True:包含中文  False:不包含中文
    :param word:
    :return:
    """
    global zh_pattern
    match = zh_pattern.search(word)
    return match


def http_session_update_cookies(session, cookies):
    """
    更新session的 cookie
    :param session:
    :param cookies:
    :return:
    """

    if not isinstance(session, Session) or not isinstance(cookies, dict):
        raise Exception("不是http_session 或者 不是字典的cookies")
    session.cookies.update(cookies)


def http_session_get_cookie_dict(session):
    """
    从session 里获取字典cookie
    :param session:
    :return:
    """
    if not isinstance(session, Session):
        raise Exception("session 不是 http session")

    cookies = session.cookies
    cookie_dict = dict()
    for cookie in cookies:
        name = cookie.name
        value = cookie.value
        cookie_dict[name] = value


def write_gongshan_data_into_span_array(data, today_date, file_name):
    """

    :param data:  数据
    :param today_date:  日期为路径
    :param file_name:  文件名
    :return:
    """

    suc = False
    try:
        dir = "/mnt/gongshang/"
        # dir = "C:/data/demodate/"
        area_code = chioce_city_code(file_name)
        dir_file_path = dir + today_date + "/" + area_code + "/"
        if not os.path.exists(dir_file_path):
            os.makedirs(dir_file_path)
        file_path = dir_file_path + file_name
        # file_path = 'C:/data/demodate/' + file_name
        with open(file_path, "w") as file:
            file.write(data)
        suc = True
    except Exception as e:
        logger.exception(str(e))
        logger.error(file_name+":写磁盘失败了呀")
    return suc


def chioce_city_code(file_name):
    """
    传入的是注册号的话
    :param file_name:  注册号或者统一社会编码
    :return:
    """
    file_name = file_name.strip() if isinstance(file_name, str) else str(file_name).strip()
    if len(file_name) <= 15:
        return file_name[:6]
    elif len(file_name) == 18:
        return file_name[2:8]
    return file_name


nbsp_flag = " "
emsp_flag = " "
thinsp_flag = " "


def re_sub_replace_html_special_code(data):
    """
    替换话
    :param data:
    :return:
    """
    re_comp = re.compile(nbsp_flag + "|" + emsp_flag + "|" + thinsp_flag)
    data = re.sub(re_comp, "", data)
    return data


def js_time(fun):
    """

    :param fun:
    :return:
    """
    def warpper(*args, **kwargs):
        start = time.time()
        ret = fun(*args, **kwargs)
        end = time.time()
        logger.info(fun.__name__ + ":花费时间:"+str(end-start))
        return ret
    return warpper

