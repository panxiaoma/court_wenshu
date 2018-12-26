# coding=utf-8
"""
initlog
1 log into db
2 log into file
2 log console
"""

from logging import FileHandler
import time
import os
import logging
from logging import StreamHandler
import sys


class DailyFileHandler(FileHandler):

    def __init__(self, filename, mode, encoding=None, delay=0):
        """
        每天的文件的处理
        :param filename:  文件的路径
        :param mode:  文件追加的类型
        :param encoding:  文件编码
        :param delay:  延迟打开文件， 0 是创建对象的时候就打开文件 1 是有日志要写入到文件的时候打开文件
        """
        FileHandler.__init__(self, filename, mode, encoding, delay)
        self.mode = mode
        self.encoding = encoding
        self.suffix = "%Y-%m-%d"
        self.suffix_time = ""

    def emit(self, record):
        """
        Emit a record.

        Always check time
        """
        try:
            if self.check_base_filename():
                self.build_base_filename()
            FileHandler.emit(self, record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def check_base_filename(self):
        """
        判断是不是有这样的文件存在
        :return:
        """
        time_tuple = time.localtime()

        if self.suffix_time != time.strftime(self.suffix, time_tuple) or not os.path.exists(
                                self.baseFilename + '.' + self.suffix_time):
            return 1
        else:
            return 0

    def build_base_filename(self):
        """
        构建文件
        """

        if self.stream:
            self.stream.close()
            self.stream = None

        # remove old suffix
        if self.suffix_time != "":
            index = self.baseFilename.find("." + self.suffix_time)
            if index == -1:
                index = self.baseFilename.rfind(".")
            self.baseFilename = self.baseFilename[:index]

        # add new suffix
        current_time_tuple = time.localtime()
        self.suffix_time = time.strftime(self.suffix, current_time_tuple)
        self.baseFilename = self.baseFilename + "." + self.suffix_time
        self.mode = 'a'
        if not self.delay:
            self.stream = self._open()


# 日志的过滤
class SingleLevelFilter(logging.Filter):

    def __init__(self, pass_level, reject):
        logging.Filter.__init__(self)
        self.pass_level = pass_level
        self.reject = reject

    def filter(self, record):
        if self.reject:
            need_filter = record.levelno != self.pass_level
        else:
            need_filter = record.levelno == self.pass_level
        return need_filter


def initlog_file(logdb=None, log_level=logging.INFO, log_name="log", filename="crawler", **kwargs):
    db_allow = False
    file_allow = False
    db_is_none = False
    logger = logging.getLogger(log_name)
    logger.setLevel(log_level)
    format = "%(asctime)s -%(module)s-[%(lineno)s]-%(thread)s-%(levelname)s - %(message)s"
    formatter = logging.Formatter(format)

    if not filename:
        filename = "." + os.path.sep + "crawler"
    # file_log

    handl_file_log = None
    try:
        handl_file_log = DailyFileHandler(filename=filename + ".log", mode="a", encoding="utf-8")
    except Exception as e:
        handl_file_log = DailyFileHandler(filename="." + os.path.sep + "crawler" + ".log", mode="a", encoding="utf-8")
    sfilter = SingleLevelFilter(logging.INFO, False)
    handl_file_log.setLevel(logging.INFO)
    handl_file_log.setFormatter(formatter)
    handl_file_log.addFilter(sfilter)

    # file_error
    handl_file_error = None
    try:
        handl_file_error = DailyFileHandler(filename=filename + ".error", mode="a", encoding="utf-8")
    except Exception as e:
        handl_file_error = DailyFileHandler(filename="." + os.path.sep + "crawler" + ".error", mode="a", encoding="utf-8")
    handl_file_error.setLevel(logging.ERROR)
    handl_file_error.setFormatter(formatter)

    # db


    # console 日志
    s = StreamHandler(sys.stdout)
    s.setLevel(logging.INFO)
    s.setFormatter(formatter)

    # 如果db 实例没有传进来
    if not logdb:db_is_none = True

    # 将处理器放在logger 里面
    if kwargs:
        print(kwargs)
        db_allow = kwargs.get("db_allow")
        print("db_allow:" + str(db_allow))
        file_allow = kwargs.get("file_allow")
        print("file_allow:" + str(file_allow))

    if db_allow and not db_is_none:
        print("<====>add db_handler:")

    else:
        print("<====>not add db_handler:")

    if file_allow:
        print("<====>add file_handler:")
        logger.addHandler(handl_file_log)
        logger.addHandler(handl_file_error)
    else:
        print("<====>not add file_handler:")
    logger.addHandler(s)




