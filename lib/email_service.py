# --*-- coding:utf-8 --*--
"""
@author wht
@time  2018/10/11 19:10
@desc email send
"""

import smtplib
from email.mime.text import MIMEText


from lib.config import EmailSender

receivers = ['haitao.wang@tigerobo.com']


class EmailService:

    def __init__(self, mail_host=EmailSender.mail_host, mail_user=EmailSender.mail_user,
                 mail_pass=EmailSender.mail_pass):
        self.mail_host = mail_host
        self.mail_user = mail_user
        self.mail_pass = mail_pass

    def send_email(self, content, title, content_type="plain", encode="utf-8"):
        """
        邮件的发送
        :param content: 发送的内容
        :param title: 发送的标题
        :param content_type: 希望发送的类型  plain 文本 类型  html 网页元素类型
        :param encode: 发送的文本的编码格式
        :return:  True or False  True:发送成功 False:发送失败
        """
        message = MIMEText(content, content_type, encode)  # 内容, 格式, 编码
        message['From'] = self.mail_user
        message['To'] = ",".join(receivers)
        message['Subject'] = title

        try:
            smtp_obj = smtplib.SMTP_SSL(self.mail_host, 465)  # 启用SSL发信, 端口一般是465
            smtp_obj.login(self.mail_user, self.mail_pass)  # 登录验证
            smtp_obj.sendmail(self.mail_user, receivers, message.as_string())  # 发送
        except smtplib.SMTPException as e:
            print(e)


