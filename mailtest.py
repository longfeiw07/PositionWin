#!/usr/bin/python
# -*- coding: UTF-8 -*-

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
#发件人列表
to_list=["smartgang@126.com","tong2gang@gmail.com"]
#对于大型的邮件服务器，有反垃圾邮件的功能，必须登录后才能发邮件，如126,163
mail_server="smtp.126.com"         # 126的邮件服务器
mail_login_user="smartgang@126.com"   #必须是真实存在的用户，这里我测试的时候写了自己的126邮箱
mail_passwd="39314656a"               #必须是对应上面用户的正确密码，我126邮箱对应的密码

def send_mail(to_list,sub,content):
    '''
    to_list:发给谁
    sub:主题
    content:内容
    send_mail("aaa@126.com","sub","content")
    '''
    me=mail_login_user+"<"+mail_login_user+">"
    ''''
    msg = MIMEText(content)
    msg['Subject'] = sub
    msg['From'] = me
    msg['To'] = ";".join(to_list)
    '''
    # 创建一个带附件的实例
    msg = MIMEMultipart()
    msg['From'] = me
    msg['To']=";".join(to_list)
#    msg['From'] = Header("PositionSendr", 'utf-8')
#    msg['To'] = Header("Test", 'utf-8')
    subject = 'Python SMTP 邮件测试'
    msg['Subject'] = Header(subject, 'utf-8')

    # 邮件正文内容
    msg.attach(MIMEText('邮件发送测试……', 'plain', 'utf-8'))

    # 构造附件1，传送当前目录下的 test.txt 文件
    att1 = MIMEText(open('d:\pic.jpg', 'rb').read(), 'base64', 'utf-8')
    att1["Content-Type"] = 'application/octet-stream'
    # 这里的filename可以任意写，写什么名字，邮件中显示什么名字
    att1["Content-Disposition"] = 'attachment; filename="buy.jpg"'
    msg.attach(att1)
    try:
        s = smtplib.SMTP()
        s.connect(mail_server)
        s.login(mail_login_user,mail_passwd)
        s.sendmail(me, to_list, msg.as_string())
        s.close()
        return True
    except Exception, e:
        print str(e)
        return False
if __name__ == '__main__':
    if send_mail(to_list,"subject","content"):
        print "发送成功"
    else:
        print "发送失败"