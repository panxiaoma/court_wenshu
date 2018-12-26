# --*-- coding:utf-8 --*--
"""
@author wht
@time  2018/10/12 09:22
@desc 日志类型
"""

from logging import FileHandler
import time
import os
import logging
from logging import StreamHandler
import sys

from lib.config import LoggerConfig


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
        写入日志
        :param record:   log_record 对象
        :return:
        """
        try:
            if self.check_base_filename():
                self.build_base_filename()
            FileHandler.emit(self, record)
        except SystemExit:
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


class SingleLevelFilter(logging.Filter):
    """
    日志过滤
    """
    def __init__(self, pass_level, reject):
        logging.Filter.__init__(self)
        self.pass_level = pass_level
        self.reject = reject

    def filter(self, record):
        """
        返回 true 写入  返回 false 过滤
        :param record:
        :return:
        """
        if self.reject:
            need_filter = record.levelno != self.pass_level
        else:
            need_filter = record.levelno == self.pass_level
        return need_filter


def initlog_file(log_level=logging.INFO, filename=LoggerConfig.file_name, file_allow=True):
    logger = logging.getLogger()
    logger.setLevel(log_level)
    format_str = LoggerConfig.format_str
    formatter = logging.Formatter(format_str)

    if file_allow and not filename:
        raise Exception("允许写文件的时候, 需要传入文件名")

    if filename and file_allow:
        try:
            handl_file_log = DailyFileHandler(filename=filename + ".log", mode="a", encoding="utf-8")
        except FileNotFoundError:
            handl_file_log = DailyFileHandler(filename="." + os.path.sep + "crawler" + ".log", mode="a",
                                              encoding="utf-8")
        sfilter = SingleLevelFilter(logging.INFO, False)
        handl_file_log.setLevel(logging.INFO)
        handl_file_log.setFormatter(formatter)
        handl_file_log.addFilter(sfilter)

        try:
            handl_file_error = DailyFileHandler(filename=filename + ".error", mode="a", encoding="utf-8")
        except FileNotFoundError:
            handl_file_error = DailyFileHandler(filename="." + os.path.sep + "crawler" + ".error", mode="a",
                                                encoding="utf-8")
        handl_file_error.setLevel(logging.ERROR)
        handl_file_error.setFormatter(formatter)
        logger.addHandler(handl_file_log)
        logger.addHandler(handl_file_error)

    s = StreamHandler(sys.stdout)
    s.setLevel(log_level)
    s.setFormatter(formatter)

    logger.addHandler(s)

