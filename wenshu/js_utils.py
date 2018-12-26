# --*-- coding:utf-8 --*--

import execjs
import os
import re
import logging
log = logging.getLogger()
log.info('执行的js引擎为:' + execjs.get().name)
print('执行的js引擎为:' + execjs.get().name)


def create_guid():
    js_comp = "var createGuid = function () { return (((1 + Math.random()) * 0x10000) | 0).toString(16).substring(1); }"
    guid = execjs.compile(js_comp).call("createGuid")
    return guid


def get_guid():
    return create_guid() + create_guid() + "-" + create_guid() + "-" + create_guid() + create_guid() + "-" +\
           create_guid() + create_guid() + create_guid()


def get_vl5x(js_value):
    """
    post  请求的ID 解密
    :param js_value:
    :return:
    """
    if js_value:
        try:
            s ="function getCookie(a){ return '" + str(js_value) + "' }"
            beautiful_js_str = s
            file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "lib/rs.js")
            with open(file_path, "r") as file:
                files = file.readlines()
                for data in files:
                    beautiful_js_str += data
            js_com = execjs.compile(beautiful_js_str)
            code = js_com.call("getKey")
            return code
        except Exception as e:
            log.error('v15x加密错误')
            return None
    else:
        log.error('v15x传入的值有误:' + str(js_value))


def un_zip_key(js_data):
    """
    解密数据的 一步
    :param js_data:
    :return:
    """
    beautiful_js_str = ""
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "lib/get_real_doc_id.js"), encoding="utf-8") \
            as file:
        files = file.readlines()
        for data in files:
            beautiful_js_str += data
    js_com = execjs.compile(beautiful_js_str)
    code = js_com.call("unzip", js_data)
    return code


def get_com_str_key(eval_str):
    """
    获取com_str_key
    :param eval_str:
    :return:
    """
    code = un_zip_key(eval_str)
    codes = str(code).split(";")
    bianlian_name = codes[0].split("=")[0]
    function_code = codes[0].split("=")[1]
    function_info = "function getValue(){ return " + function_code + " }"
    code_value = execjs.compile(function_info).call("getValue")
    index = codes[3].find('(')
    rindex = codes[3].rfind(")(")
    function_code = codes[3][index + 1:rindex]
    code_value = code_value.replace("\"", "\\\"")
    function_info_two = "function getComKey(){\n var " + bianlian_name + " = \"" + code_value + "\" \nvar " \
                        "data= " + function_code + " \nreturn data }"
    data = execjs.compile(function_info_two).call("getComKey")
    find_data = re.search("com\.str\._KEY=\"(.*?)\";", data)
    com_str_key = find_data.group(1)
    return com_str_key


def get_doc_js_function(com_str_key):
    """
    最终的 解密js
    :param com_str_key:
    :return:
    :param com_str_key:
    :return:
    """
    beautiful_js_str = ""
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "lib/get_real_doc_id.js"), "r", encoding="utf-8") as file:
        files = file.readlines()
        for data in files:
            beautiful_js_str += data
    beautiful_js_str += "\ncom.str._KEY=\""+com_str_key+"\""
    js_com = execjs.compile(beautiful_js_str)
    return js_com


def get_real_doc_id(eval_str, doc_id):
    """
    获取最终的doc_id
    :param eval_str:
    :param doc_id_list:
    :return:
    """
    try:
        com_str_key = get_com_str_key(eval_str)
        if not com_str_key:
            return
        js_com = get_doc_js_function(com_str_key)
        real_doc_id = js_com.call("get_doc_id", doc_id)
        return real_doc_id
    except Exception as e:
        log.error('获取get_doc_id异常.')



