# --*-- coding:utf-8 --*--
from lib.logger_magic import initlog_file
import logging
import json
import math
import os
import time
from wenshu.http_request import Http
from urllib import parse
from wenshu.js_utils import get_guid
from wenshu.js_utils import get_vl5x
from wenshu.js_utils import get_real_doc_id
from lib.config import mysql_db_pool, redis_pool
from dbo.dbpool import Dbpool
from dbo.redisclient import RedisClient
import traceback
from threading import Thread
import threading
import requests
initlog_file()
log = logging.getLogger()
js_lock1 = threading.Lock()
js_lock2 = threading.Lock()

def get_ip():
    for i in range(3):
        try:
            mutex = threading.Lock()
            url = 'http://10.0.2.82/proxy/next/:wenshu.court.gov.cn'
            mutex.acquire()
            r = eval(requests.get(url=url).text)
            mutex.release()
            proxy = {'http': "http://" + str(r.get("ip")) + ":" + str(r.get("port"))}
            log.info('获取到的ip:' + str(proxy))
            return proxy
            break
        except Exception:
            logger.info('获取动态代理异常')


class Wenshu():
    def __init__(self, company, mysql_pool):
        self.http = Http('中国裁判文书网')
        self.company = company.split(';')[0].strip()
        self.c_type = company.split(';')[1].strip()
        self.codes = 0
        self.mysql_pool = mysql_pool

    def spider_content(self):
        try:
            proxies = get_ip()
            indexs_url = 'http://wenshu.court.gov.cn/'
            self.http.http_request('get', indexs_url, headers=self.http.header)
            if self.http.get_status_code() is not 200:
                suc = self.http.retry('get', indexs_url, headers=self.http.header)
                if suc is not 0:
                    return
            if self.http.get_status_code() is not 200:
                return
            guid = get_guid()
            code_url = 'http://wenshu.court.gov.cn/ValiCode/GetCode'
            get_code_data = {
                'guid': guid
            }

            self.http.http_request('post', code_url, data=get_code_data, proxies=proxies, headers=self.http.header)
            if self.http.get_status_code() is not 200:
                suc = self.http.retry('post', code_url, data=get_code_data, proxies=proxies, headers=self.http.header)
                if suc is not 0:
                    return
            if self.http.get_status_code() is not 200:
                return
            self.http.parse_html()
            if not self.http.content or str(self.http.content).__len__() > 15:
                return
            log.info(self.company + '第一次获取到的number为' + self.http.content)
            number = self.http.content
            log.info('开始抓取' + self.company + ',获取到的guid:' + guid)
            index_url = 'http://wenshu.court.gov.cn/list/list/?sorttype=1&number=' + number + '&guid=' + guid \
                        +'&conditions=searchWord+QWJS+++%E5%85%A8%E6%96%87%E6%A3%80%E7%B4%A2:' + parse.quote(self.company)
            self.http.http_request('get', index_url, proxies=proxies, headers=self.http.header)
            c_v = self.http.get_cookie().get('vjkl5')
            log.info('抓取' + self.company + ',获取到的vjkl5:' + c_v)
            if not c_v:
                for k in range(3):
                    self.http.http_request('get', index_url, proxies=proxies, headers=self.http.header)
                    c_v = self.http.get_cookie().get('vjkl5')
                    if c_v:
                        break
            if c_v:
                js_lock1.acquire()
                vl5x = get_vl5x(c_v)
                js_lock1.release()
                if not vl5x:
                    log.info(self.company + '获取到的v15x有误')
                    return
                log.info(self.company + '获取到的vl5x:' + vl5x)

                tr_list_url = 'http://wenshu.court.gov.cn/List/TreeList'
                self.http.http_request('post', tr_list_url, proxies=proxies, headers=self.http.header)
                if self.http.get_status_code() is not 200:
                    suc = self.http.retry('post', tr_list_url, proxies=proxies, headers=self.http.header)
                    if suc is not 0:
                        return
                if self.http.get_status_code() is not 200:
                    log.info('抓取' + self.company + '失败')
                    self.codes = 1
                    return
                else:
                    self.http.parse_html()
                    print('htmlcontent is:', self.http.content)
                    log.info('抓取' + self.company + '列表信息.')
                    value = '全文检索:' + self.company
                    data = {
                        'Param': value,
                        'Index': '1',
                        'Page': '10',
                        'Order': '裁判日期',
                        'Direction': 'desc',
                        'vl5x': vl5x,
                        'number': number[0:4],
                        'guid': guid,
                    }
                    list_url = 'http://wenshu.court.gov.cn/List/ListContent'
                    self.http.http_request('post', list_url, proxies=proxies, data=data, headers=self.http.header)
                    if self.http.get_status_code() is not 200:
                        suc = self.http.retry('post', list_url, data=data, proxies=proxies, headers=self.http.header)
                        if suc is not 0:
                            return
                    if self.http.get_status_code() == 200:
                        self.http.parse_html()
                        if self.http.content:
                            if 'remind' in self.http.content:
                                return
                        list_json = json.loads(json.loads(self.http.content.replace(',]', ']')))
                        if not list_json:
                            self.codes = 1
                            return
                        # print(type(list_json), '获取到的json:', list_json)
                        page_total = list_json[0].get('Count')
                        if page_total == '0':
                            lst = {'案件类型': '', '裁判日期': '', '案件名称': '', '文书ID': '', '审判程序': '', '案号': '', '法院名称': '',
                                   'path': ''}
                            lst['company'] = self.company
                            self.insert_case_list(lst)
                            return
                        _str = list_json[0].get('RunEval')
                        l_count = 0
                        for value in list_json:
                            if value.get('文书ID'):
                                l_count += 1
                                try:
                                    # print(self.c_type, '------------------------------', value.get('裁判日期'))
                                    if 'ALL' not in self.c_type:
                                        if self.c_type > value.get('裁判日期'):
                                            log.info(self.company + '增量爬取结束')
                                            return
                                    js_lock2.acquire()
                                    doc_id_str = get_real_doc_id(_str, value.get('文书ID'))
                                    js_lock2.release()
                                    log.info(self.company + '抓取文书id为' + doc_id_str + '的文书')
                                    if not doc_id_str:
                                        continue
                                    content_url = 'http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx?DocID=' + doc_id_str
                                    self.http.http_request('get', content_url, data=data, proxies=proxies, headers=self.http.header)
                                    self.http.parse_html()
                                    if self.http.get_status_code() is not 200 or not self.http.content:
                                        suc = self.http.retry('get', content_url, data=data, proxies=proxies, headers=self.http.header)
                                        if suc is not 0:
                                            break
                                    if self.http.get_status_code() == 200:
                                        self.http.parse_html()
                                        # print('抓取到的content : ', self.http.content)
                                        doc_type = value.get('案件类型')
                                        if self.http.content:
                                            if '$(function()' not in self.http.content:
                                                break
                                            flag, path = self.write_text(doc_id_str, doc_type, self.http.content)
                                            if flag:
                                                value['文书ID'] = doc_id_str
                                                value['path'] = path
                                                value['company'] = self.company
                                                self.insert_case_list(value)
                                        else:
                                            m = traceback.format_exc()
                                            log.error(self.company + '状态码200返回内容为空爬取' + doc_id_str + '失败:' + m)
                                            self.err_insert(doc_id_str, value)
                                    else:
                                        m = traceback.format_exc()
                                        log.error(self.company + '状态异常无返回内容爬取' + doc_id_str + '失败:' + m)
                                        self.err_insert(doc_id_str, value)

                                except Exception:
                                    m = traceback.format_exc()
                                    log.error(self.company + '爬取' + doc_id_str + '异常:' + m)
                                    self.err_insert(doc_id_str, value)

                            else:
                                if l_count > 0:
                                    self.codes = 1
                                    log.error(self.company + "爬取时官网返回异常,此次结果失败")

                    else:
                        self.codes = 1
                        return
                    """
                       抓取翻页
                    """
                    page_sum = math.ceil(int(page_total)/10)
                    if page_sum > 20:
                        page_sum = 5
                    if page_sum > 1:
                        fflag = 0
                        for i in range(2, page_sum + 1):
                            if fflag == 1:
                                break
                            fflag = 0
                            try:
                                log.info(self.company + '开始爬取第' + str(i) + '页裁判文书')
                                data['Index'] = str(i)
                                list_url = 'http://wenshu.court.gov.cn/List/ListContent'
                                self.http.http_request('post', list_url, proxies=proxies, data=data, headers=self.http.header)
                                if self.http.get_status_code() is not 200:
                                    suc = self.http.retry('post', list_url, data=data, proxies=proxies, headers=self.http.header)
                                    if suc is not 0:
                                        fflag = 1
                                        return
                                if self.http.get_status_code() == 200:
                                    self.http.parse_html()
                                    if 'remind' in self.http.content:
                                        break
                                    list_json = json.loads(json.loads(self.http.content))
                                    _str = list_json[0].get('RunEval')
                                    l_count = 0
                                    for value in list_json:
                                        if value.get('文书ID'):
                                            l_count += 1
                                            try:
                                                if 'ALL' not in self.c_type:
                                                    if self.c_type > value.get('裁判日期'):
                                                        log.info(self.company + '增量爬取结束')
                                                        return
                                                js_lock2.acquire()
                                                doc_id_str = get_real_doc_id(_str, value.get('文书ID'))
                                                js_lock2.release()
                                                log.info(self.company + '抓取文书id为' + doc_id_str + '的文书')
                                                if not doc_id_str:
                                                    continue
                                                content_url = 'http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx?DocID=' + doc_id_str
                                                self.http.http_request('get', content_url, data=data, proxies=proxies,
                                                                       headers=self.http.header)
                                                self.http.parse_html()
                                                if self.http.get_status_code() is not 200 or not self.http.content:
                                                    suc = self.http.retry('get', content_url, data=data, proxies=proxies,
                                                                    headers=self.http.header)
                                                    if suc is not 0:
                                                        fflag = 1
                                                        break

                                                if self.http.get_status_code() == 200:
                                                    self.http.parse_html()
                                                    # print('抓取到的content : ', self.http.content)
                                                    doc_type = value.get('案件类型')
                                                    if self.http.content:
                                                        if '$(function()' not in self.http.content:
                                                            fflag = 1
                                                            break
                                                        flag, path = self.write_text(doc_id_str, doc_type,
                                                                                     self.http.content)
                                                        if flag:
                                                            value['文书ID'] = doc_id_str
                                                            value['path'] = path
                                                            value['company'] = self.company
                                                            self.insert_case_list(value)
                                                            pass
                                                    else:
                                                        m = traceback.format_exc()
                                                        log.error(self.company + '状态码200返回内容为空爬取' + doc_id_str + '失败:' + m)
                                                        self.err_insert(doc_id_str, value)
                                                else:
                                                    m = traceback.format_exc()
                                                    log.error(self.company + '状态异常无返回内容爬取' + doc_id_str + '失败:' + m)
                                                    self.err_insert(doc_id_str, value)
                                            except Exception:
                                                m = traceback.format_exc()
                                                log.error(self.company + '爬取' + doc_id_str + '失败:' + m)
                                                self.err_insert(doc_id_str, value)
                                        else:
                                            if l_count > 0:
                                                self.codes = 1
                                                log.error(self.company + "爬取时官网返回异常,此次结果失败")

                            except Exception:
                                m = traceback.format_exc()
                                log.error(self.company + '抓取第' + str(i) + '页失败:' + m)
            else:
                log.info(self.company + '多次尝试无法获取vjkl5,放弃抓取')
        except Exception:
            m = traceback.format_exc()
            log.error(self.company + '爬取失败,异常信息为:' + m)

    def err_insert(self, doc_id, lose_content):
        try:
            log.info(self.company + '开始插入数据')
            self.mysql_pool.execute_data("insert into lose_document(doc_id, company, lose_content) values(%s, %s, %s)",
                                         (str(doc_id), str(self.company), str(lose_content))).get("suc")
        except Exception :
            m = traceback.format_exc()
            log.error(self.company + '存储失败链接异常:' + doc_id + '/异常信息为:' + m)

    def insert_case_list(self, json_value):
        suc = False
        try:
            log.info(self.company + '开始插入数据')
            case_type = json_value.get('案件类型')
            judicial_time = json_value.get('裁判日期')
            case_name = json_value.get('案件名称')
            document_id = json_value.get('文书ID')
            trial_procedure = json_value.get('审判程序')
            case_no = json_value.get('案号')
            court_name = json_value.get('法院名称')
            document_way = json_value.get('path')
            company = json_value.get('company')
            suc = self.mysql_pool.execute_data("insert into judicial_documents(case_type, judicial_time, case_name, document_id, trial_procedure, case_no, court_name, document_way, company) values(%s, %s, %s,  %s, %s, %s, %s, %s, %s)",(str(case_type), str(judicial_time), str(case_name), str(document_id), str(trial_procedure), str(case_no), str(court_name), str(document_way), str(company))).get("suc")
        except Exception :
            m = traceback.format_exc()
            log.error(self.company + '存储异常:' + json_value + '/异常信息为:' + m)
        return suc

    def write_text(self, doc_id, doc_type, html):
        if not html or '$(function()' not in html:
            log.info(self.company+'错误的html,不予插入')
            return
        suc = False
        try:
            if doc_type is None:
                doc_type = '100'
            log.info(self.company + '开始存储文件号为' + doc_id + '的文书')
            # dir = "C:/data/wenshu/"
            dir = "/mnt/wenshu/gongshang-2/document/"
            today_ = time.strftime("%y%m%d", time.localtime())
            today_hours = time.strftime("%H", time.localtime())
            dir_file_path = dir + today_ + "/" + today_hours + "/" + doc_type + "/"
            if not os.path.exists(dir_file_path):
                os.makedirs(dir_file_path)
            file_path = dir_file_path + str(int(time.time())) + '-' + doc_id
            with open(file_path, "w", encoding='utf-8') as file:
                file.write(html)
            suc = True
        except Exception:
            m = traceback.format_exc()
            log.error(self.company + '文书号为/' + doc_id + "/写磁盘失败了呀" + m)
        return suc, file_path
        pass


def run(rdis_client, mysql_client):
    while True:
        try:
            suc, data = rdis_client.get_list_lpop('companyALL')
            if not suc:
                log.error("redis 链接不成功")
                time.sleep(1)
                continue
            if suc and data is None:
                log.error("redis 没有数据了 我退出了哦")
                break
            w = Wenshu(data, mysql_client)
            w.spider_content()
        except Exception:
            m = traceback.format_exc()
            log.error('抓取流程异常' + m)


if __name__ == '__main__':
    redis_client = RedisClient(**redis_pool.get("localhost"))
    mysql_client = Dbpool(**mysql_db_pool.get("localhost"))
    for i in range(5):
        Thread(target=run, args=(redis_client, mysql_client)).start()









