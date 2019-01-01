import logging
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import multiprocessing


# logging = logging.getLogger(__name__)


def send_msg_by_name(esp_clients, msg, name):
    for c in esp_clients:
        try:
            if c.name == name:
                c.send_msg(msg)
        except Exception as e:
            logging.error(e)


def send_mail(reciver, title, content):
    p = multiprocessing.Process(target=_send_email, args=(reciver, title, content))
    p.daemon = True
    p.start()


def _send_email(reciver, title, content):

    msg_from = 'alonebo.zhou@qq.com'  # 发送方邮箱
    passwd = 'timyoawmsoisbfge'  # 填入发送方邮箱的授权码
    msg_to = reciver  # 收件人邮箱

    subject = title  # 主题
    content = content  # 正文
    msg = MIMEText(content)
    msg['Subject'] = subject
    msg['From'] = msg_from
    msg['To'] = msg_to
    try:
        s = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 邮件服务器及端口号
        s.login(msg_from, passwd)
        s.sendmail(msg_from, msg_to, msg.as_string())
        logging.info('send email to {}success'.format(reciver))
    except Exception as e:
        logging.error(e)
    finally:
        s.quit()
