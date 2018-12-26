# --*-- coding:utf-8 --*--
"""
@author pxm
@time  2018/12/6 11:23
@desc
"""
from lib.logger_magic import initlog_file
import logging
from lib.config import mysql_db_pool, redis_pool
from dbo.dbpool import Dbpool
from concurrent.futures import ThreadPoolExecutor
import traceback
from threading import Thread
from wenshu.http_request import Http
import json
import time
import os
initlog_file()
log = logging.getLogger()


class DocumentIdSpider():
    def __init__(self, serialno, doc_id, company, mysql_pool):
        self.company = company
        self.doc_id = doc_id
        self.http = Http('中国裁判文书网')
        self.serialno = serialno
        self.mysql_pool = mysql_pool

    def spider(self, content):
        if self.doc_id:
            if content.get('文书ID'):
                try:
                    doc_id_str = self.doc_id
                    log.info(self.company + '抓取文书id为' + doc_id_str + '的文书')
                    content_url = 'http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx?DocID=' + doc_id_str
                    self.http.http_request('get', content_url, headers=self.http.header)
                    self.http.parse_html()
                    if self.http.get_status_code() is not 200 or not self.http.content:
                        self.http.retry('get', content_url, headers=self.http.header)
                    if self.http.get_status_code() == 200:
                        self.http.parse_html()
                        doc_type = content.get('案件类型')
                        if self.http.content:
                            flag, path = self.write_text(doc_id_str, doc_type, self.http.content)
                            if flag:
                                content['文书ID'] = doc_id_str
                                content['path'] = path
                                content['company'] = self.company
                                success = self.insert_case_list(content)
                                if success:
                                    self.del_doc_id(serialno=self.serialno)

                        else:
                            m = traceback.format_exc()
                            log.error(self.company + '状态码200返回内容为空爬取' + doc_id_str + '失败:' + m)
                    else:
                        m = traceback.format_exc()
                        log.error(self.company + '状态异常无返回内容爬取' + doc_id_str + '失败:' + m)
                except Exception:
                    m = traceback.format_exc()
                    log.error(self.company + '爬取' + doc_id_str + '异常:' + m)

    def del_doc_id(self, serialno):
        log.info(self.company + '删除serialno=' + str(serialno) + '的数据')
        sql = 'delete from lose_document where serialno = ' + str(serialno)
        self.mysql_pool.delete_execute(sql)

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
        except Exception as e:
            m = traceback.format_exc()
            log.error(self.company + '存储异常:' + json_value + '/异常信息为:' + m)
        return suc

    def write_text(self, doc_id, doc_type, html):
        suc = False
        try:
            if doc_type is None:
                doc_type = '100'
            log.info(self.company + '开始存储文件号为' + doc_id + '的文书')
            print('------------------->', html)
            dir = "C:/data/wenshu/"
            # dir = "/mnt/wenshu/gongshang-2/document/"
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


def run(document):
    if document:
        try:
            serialno = document[0]
            doc_id = document[1]
            company = document[2]
            content = document[4]
            json_content = eval(content)
            D = DocumentIdSpider(serialno, doc_id, company, mysql_client)
            D.spider(json_content)
        except Exception as e:
            print(e)
            pass


if __name__ == '__main__':
    mysql_client = Dbpool(**mysql_db_pool.get("localhost"))
    while True:
        pool = ThreadPoolExecutor(1)
        suc, data = mysql_client.select_execute('select * from lose_document ')
        if not data:
            log.info('补录裁判文书---队列中无数据等待中')
            time.sleep(60)
            continue
        pool.map(run, data)
        pool.shutdown()
        # futures = pool.map(run, data)
        # future_list = [future for future in futures]
        # while future_list:
        #     future = future_list.pop()
        #     if not future.done():
        #         future_list.append(future)
        #         continue
        #     try:
        #         future.result()
        #     finally:
        #         future.cancel()

        # for value in data:
        #     try:
        #         pool.submit(run, value)
        #     except Exception as e:
        #         log.info('补录裁判文书失败')
        # Thread.join()
        # for i in range(3):
        #     Thread(target=run, args=(data,)).start()

