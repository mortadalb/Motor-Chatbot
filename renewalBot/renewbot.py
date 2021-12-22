#!/usr/bin/python
# coding=utf-8

import json
import time
import os
import requests
import convert_numbers
from unidecode import unidecode
from flask import Flask, request, session
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from six.moves.urllib.parse import urlparse
from datetime import timedelta, datetime
from WEB_INSERT_DIRECT_AMAN import get_policy_details, get_policy_details_cpr, get_all_endt, get_endt_data, insert_endt_web, renew_by_pol, find_expiry, order, get_quote
from smtplib import SMTP  
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import mysql.connector
import sys  

reload(sys)  
sys.setdefaultencoding('utf8')

app = Flask(__name__)

def mydb():
    mysqldb = mysql.connector.connect(
        host = "server-00616",
        port = 3305,
        user = "chatbot",
        passwd = "XXXXXXXXXX",
        database = "quotations",
        auth_plugin='mysql_native_password')
    return mysqldb

def insert_db(mobile,level):
    phone = mobile
    menu = level
    time_tuple = time.localtime()    
    ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
    minedb = mydb()
    mycursor = minedb.cursor()
    sql = """INSERT INTO chatbot (mobile, menu, timestamp) VALUES(%s, %s, %s)"""
    rec = (mobile, menu, ts)
    mycursor.execute(sql, rec)
    minedb.commit()
    minedb.close()
    
def update_db(mobile,level):
    phone = mobile
    menu = level
    time_tuple = time.localtime()
    ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
    minedb = mydb()
    mycursor = minedb.cursor()
    sql = """UPDATE chatbot SET timestamp=(STR_TO_DATE('""" + str(ts) + """','%Y-%m-%d %H:%i:%s')), menu='""" + str(menu) + """' WHERE mobile='""" + str(mobile) + """'"""
    mycursor.execute(sql)
    minedb.commit()
    minedb.close()
    
def search_db(mobile):
    phone = mobile
    minedb = mydb()
    mycursor = minedb.cursor()
    sql = """SELECT menu FROM chatbot WHERE mobile='""" + str(mobile) + """'"""
    mycursor.execute(sql)
    myresult = mycursor.fetchall()   
    minedb.close()    
    for result in myresult:
        menu = result[0]
        return menu
    return 0 

def email(subject, message):
    text_subtype = 'plain'
    content = message
    title = subject
    SMTPserver =    'xx.xx.xx.xx'
    sender =        'ithelpdesk@company.c0m'
    destination =   'info@company.c0m'
    try:
        msg = MIMEText(content, text_subtype)
        msg['From'] = sender        
        msg['To'] = destination
        msg['Subject'] = title

        conn = SMTP(SMTPserver)
        conn.set_debuglevel(False)
        try:
            conn.sendmail(sender, destination, msg.as_string())
        finally:
            conn.quit()

    except:
        sys.exit( "mail failed; %s" % "CUSTOM_ERROR" ) 

def mail(destination, subject, message):
    text_subtype =  'plain'
    content =       message
    title =         subject
    SMTPserver =    'xx.xx.xx.xx'
    sender =        'ithelpdesk@company.c0m'
    copies =        'aman.admin@company.c0m'
    try:
        msg = MIMEText(content, text_subtype)
        msg['From'] =       sender        
        msg['To'] =         destination
        msg['Cc'] =         copies
        msg['Subject'] =    title

        conn = SMTP(SMTPserver)
        conn.set_debuglevel(False)
        try:
            conn.sendmail(sender, [destination,copies], msg.as_string())
        finally:
            conn.quit()

    except:
        sys.exit( "mail failed; %s" % "CUSTOM_ERROR" ) 

def arabic(numb):
    #mapping = [ ('0','٠'), ('1','١'), ('2','٢'), ('3','٣'), ('4','٤'), ('5','٥'), ('6','٦'), ('7','٧'), ('8','٨'), ('9','٩') ]
    #for western, eastern in mapping:
    #    numb.replace(eastern,western)
    numb = convert_numbers.english_to_hindi(numb)
    return numb

def menu_level(i):
    switcher={
            101: 210,
            102: 220,
            103: 720,
            104: 104,
            105: 105,
            106: 1000,
            202: 100,           
            211: 600,
            212: 212,
            213: 213,
            214: 214, 
            215: 215,
            221: 330,
            222: 330,
            223: 330,
            224: 330,
            225: 330,
            226: 330,
            227: 330,
            228: 330,
            229: 330,
            230: 330,
            252: 100,
            272: 100,
            282: 100,
            292: 100,
            275: 300,
            276: 301,
            331: 450,
            332: 480,
            333: 100,
            334: 330,
            335: 330,
            420: 420,
            421: 330,
            422: 330,
            423: 330,
            424: 330,
            425: 330,
            426: 330,
            427: 330,
            428: 330,
            429: 330,
            430: 330,            
            451: 500,
            452: 220,
            453: 100,
            481: 450,
            482: 100,
            497: 497,
            498: 498,
            499: 499,
            601: 601,
            602: 602,
            603: 603,
            604: 604,
            605: 605, 
            721: 830,
            722: 830,
            723: 830,
            724: 830,
            725: 830,
            726: 830,
            727: 830,
            728: 830,
            729: 830,
            730: 830, 
            831: 250,
            832: 802,
            833: 270,
            834: 280,
            835: 290,
            852: 852,
            862: 862,
            900: 900,
            1001: 2100,
            1002: 2200,
            1003: 7200,
            1004: 1004,
            1005: 1005,
            1006: 100,
            2101: 6000,
            2102: 2102,
            2103: 2103,
            2104: 2104,
            2105: 2105,
            2201: 3300,
            2202: 3300,
            2203: 3300,
            2204: 3300,
            2205: 3300,
            2206: 3300,
            2207: 3300,
            2208: 3300,
            2209: 3300,
            2210: 3300,
            2255: 3000,
            2256: 3001,
            2502: 1000,
            2702: 1000,
            2802: 1000,
            2902: 1000,
            3034: 3300,
            3035: 3300,
            3301: 4500,
            3302: 4800,
            3303: 1000,
            4200: 4200,
            4201: 3300,
            4202: 3300,
            4203: 3300,
            4204: 3300,
            4205: 3300,
            4206: 3300,
            4207: 3300,
            4208: 3300,
            4209: 3300,
            4210: 3300,
            4501: 5000,
            4502: 2200,
            4503: 1000,
            4801: 4500,
            4802: 1000,
            4970: 4970,
            4971: 4971,            
            6001: 6001,
            6002: 6002,
            6003: 6003,
            6004: 6004,
            6005: 6005,
            7201: 8300,
            7202: 8300,
            7203: 8300,
            7204: 8300,
            7205: 8300,
            7206: 8300,
            7207: 8300,
            7208: 8300,
            7209: 8300,
            7210: 8300,  
            8301: 2500,
            8302: 8002,
            8303: 2700,
            8304: 2800,
            8305: 2900,
            8502: 8502,
            8602: 8602,
            9000: 9000
            }
    return switcher.get(i,"Invalid menu item!")

def menu_00():
    level00 = """*You typed a wrong digit. Please choose the correct number from the above menu!*"""
    return level00

def menu_000():
    level000 = """*لقد أدخلت رقماً خاطئاً. الرجاء إختيار الرقم الصحيح من القائمة أعلاه!*"""
    return level000.encode("utf-8")

def menu_01():
    level01 = """*You typed a character(s) instead of a digit. You must select from the list of numbers in the above menu or type M to return to menu!*"""
    return level01

def menu_010():
    level010 = """*لقد قمت بإختيارٍ خاطئ. يجب أن تختار من الأرقام في القائمة أعلاه أو أدخل "ر" للعودة إلى القائمة الرئيسية!*"""
    return level010.encode("utf-8")

def menu_02():
    level02 = """*Company Chabot only supports Bahraini mobile numbers at the moment!*"""
    return level02

def menu_03():
    level03 = """*You typed a wrong selelection character. Please type Q or M to proceed.*"""
    return level03

def menu_030():
    level030 = """لقد قمت بإختيار خاطئ. الرجاء أدخل "خ" أو "ر" للخروج أو العودة إلى القائمة الرئيسية."""
    return level030.encode("utf-8")   
    
def menu_04():
    level04 = """*You typed a wrong selection. Please choose Q or M to continue.*"""
    return level04    

def menu_040():
    level040 = """لقد قمت بإختيار خاطئ. الرجاء أدخل "خ" أو "ر" للخروج أو العودة إلى القائمة الرئيسية."""
    return level040.encode("utf-8")   

def menu_001():
    level001 = """Thank you for using Company chatbot. Please visit us again whenever you have a new inquiry in the future!"""
    return level001

def menu_0010():
    level0010 = """شكراً لإستخدامك خدمة المتحدث الآلي. يرجى زيارتنا مرة أخرى كلما كان لديك استفسار جديد في المستقبل!"""
    return level0010.encode("utf-8")

def menu_100():
    level100 = """Welcome to Company chatbot! How can I be of your help?
    
    *1.* General inquiry
    *2.* Renew my motor insurance
    *3.* Modify my motor insurance
    *4.* Issue a new motor policy
    *5.* Register a motor claim
    *6.* للتحدث بالعربية

*** _Please select your option by typing 1 or 2 etc. to continue._
*** _You can always quit this chat by typing *Q* at any stage._"""
    return level100.encode("utf-8")

def menu_1000():
    level1000 = """أهلا بك مع المتحدث الآلي. كيف بإمكاني مساعدتك؟
    
    *١.* استعلامات عامة
    *٢.* تجديد وثيقة تأمين المركبة
    *٣.* تعديل وثيقة تأمين المركبة    
    *٤.* إصدار وثيقة جديدة لتأمين مركبة
    *٥.* تسجيل مطالبة حادث مروري
    *٦.* Chat in English

*** الرجاء إختيار ١, ٢, إلخ للمتابعة
***  كما يمكنك دائماً إدخال "خ" للخروج النهائي من المحادثة في أية مرحلة."""
    return level1000.encode("utf-8")

def menu_720(mobile):
    time_tuple = time.localtime()
    ts = time.strftime("%Y-%m-%d",time_tuple)
    mysqldb = mydb()
    mycursor1 = mysqldb.cursor()
    mycursor2 = mysqldb.cursor()
    mycursor3 = mysqldb.cursor()
    
    sql1 = """SELECT * FROM pol_details WHERE mobile= """ + str(mobile)
    sql3 = """INSERT INTO policies (mobile, pol_no, pol_year, exp_date, renewal_prem, selection, timestamp) VALUES (%s, %s, %s, STR_TO_DATE(%s,'%d/%m/%Y'), %s, %s, %s)"""
    mycursor1.execute(sql1)
    myresult1 = mycursor1.fetchall()
    
    j = 0
    level720 = """The following are your current active motor policies with Company:
    """            
    for pol in myresult1:
        if j == 10:
            break
        print(pol[5],"/",pol[6])
        sql2 = """SELECT * FROM policies WHERE pol_no=""" + str(pol[5]) + """ AND pol_year=""" + str(pol[6])
        mycursor2.execute(sql2)
        myresult2 = mycursor2.fetchall()
        if myresult2 == []:
            rec = (mobile, pol[5], pol[6], '01/01/1900', 0, j+1, ts)
            mycursor3.execute(sql3, rec)
            mysqldb.commit()
        level720 = level720 + str(j+1) + """. *""" + str(pol[5])+"/"+str(pol[6]) + """*
    """    
        j += 1    

    level720 = level720 + """    
*** _Please select your option by typing 1, 2, etc. to continue_
*** _You can type *M* to return to main menu_"""
    mysqldb.close()
    return level720 

def menu_7200(mobile):
    time_tuple = time.localtime()
    ts = time.strftime("%Y-%m-%d",time_tuple)
    mysqldb = mydb()
    mycursor1 = mysqldb.cursor()
    mycursor2 = mysqldb.cursor()
    mycursor3 = mysqldb.cursor()
    
    sql1 = """SELECT * FROM pol_details WHERE mobile= """ + str(mobile)
    sql3 = """INSERT INTO policies (mobile, pol_no, pol_year, exp_date, renewal_prem, selection, timestamp) VALUES (%s, %s, %s, STR_TO_DATE(%s,'%d/%m/%Y'), %s, %s, %s)"""
    mycursor1.execute(sql1)
    myresult1 = mycursor1.fetchall()
    
    j = 0
    level7200 = """فيما يلي تجد الوثائق الحالية الخاصة بك مع الشركة:
    """
    for pol in myresult1:
        if j == 10:
            break
        print(pol[5],"/",pol[6])
        sql2 = """SELECT * FROM policies WHERE pol_no=""" + str(pol[5]) + """ AND pol_year=""" + str(pol[6])
        mycursor2.execute(sql2)
        myresult2 = mycursor2.fetchall()
        if myresult2 == []:
            rec = (mobile, pol[5], pol[6], '01/01/1900', 0, j+1, ts)
            mycursor3.execute(sql3, rec)
            mysqldb.commit()
        level7200 = level7200 + str(arabic(j+1)) + """. *""" + str(pol[5])+"/"+str(pol[6]) + """*
    """    
        j += 1        

    level7200 = level7200 + """    
*** الرجاء إختيار ١, ٢, إلخ للمتابعة
*** أوأدخل "ر" للعودة إلى القائمة الرئيسية"""
    mysqldb.close()
    return level7200.encode("utf-8") 

def menu_830(pol_no,pol_year):
    level830 = """Please select the type of modification required for ```""" + str(pol_no) + """/""" + str(pol_year) + """```:
    
    *1.* Change ownership
    *2.* Change registration number
    *3.* Extend insurance coverage
    *4.* Change insurance coverage type
    *5.* Cancel insurance

*** _Please type 1, 2, 3, etc. to continue or *M* to return to main menu._"""
    return level830
    
def menu_8300(pol_no,pol_year):
    level8300 = """ماذا تريد أن تفعل بوثيقة التأمين """ + str(pol_no) + """/""" + str(pol_year) + """؟
     ١. تغيير الملكية
     ٢. تغيير رقم اللوحة
     ٣. تمديد مدة التأمين
     ٤. تغيير نوعية تغطية التأمين
     ٥. إلغاء التأمين     

*** الرجاء إختيار ١, ٢, ٣, إلخ للمتابعة"""
    return level8300.encode("utf-8") 

def menu_250():
    level250 = """Please confirm to send a request to change the vehicle ownership under your motor policy:
    *1.* Ok
    *2.* Cancel""" 
    return level250

def menu_2500():
    level2500 = """الرجاء التآكيد لإرسال طلب تغيير ملكية المركبة ضمن وثيقة تأمين مركبتك:
    ١. تآكيد 
    ٢. إلغاء""" 
    return level2500.encode("utf-8")

def menu_802():
    level802 = """Please insert the new *registration no.* as dispayed in your ownership card:"""
    return level802

def menu_8002():
    level8002 = """ الرجاء إدخال رقم اللوحة الجديد كما هو مدون في بطاقة الملكية:"""
    return level8002.encode("utf-8") 

def menu_270():
    level270 = """Please confirm to send a request to extend the insurance coverage under your motor policy:
    *1.* Ok
    *2.* Cancel""" 
    return level270

def menu_2700():
    level2700 = """الرجاء التآكيد لإرسال طلب تمديد تغطية التأمين ضمن وثيقة تأمين مركبتك:
    ١. تآكيد 
    ٢. إلغاء"""  
    return level2700.encode("utf-8")

def menu_280():
    level280 = """Please confirm to send a request to change the insurance coverage type under your motor policy:
    *1.* Ok
    *2.* Cancel""" 
    return level280

def menu_2800():
    level2800 = """الرجاء التآكيد لإرسال طلب تغيير نوعية تغطية التأمين ضمن وثيقة تأمين مركبتك:
    ١. تآكيد 
    ٢. إلغاء"""  
    return level2800.encode("utf-8")

def menu_290():
    level290 = """Please confirm to send a request to terminate your motor policy:
    *1.* Ok
    *2.* Cancel""" 
    return level290

def menu_2900():
    level2900 = """الرجاء التآكيد لإرسال طلب إنهاء وثيقة تأمين مركبتك:
    ١. تآكيد 
    ٢. إلغاء"""  
    return level2900.encode("utf-8")

def menu_852():
    level852 = """Please upload a copy of the *front* of your ownership card:"""
    return level852

def menu_8502():
    level8502 = """ الرجاء تحميل الصورة الأمامية لبطاقة الملكية:"""
    return level8502.encode("utf-8") 

def menu_862():
    level862 = """Please upload a copy of the *back* of your ownership card:"""
    return level862

def menu_8602():
    level8602 = """ الرجاء تحميل الصورة الخلفية لبطاقة الملكية:"""
    return level8602.encode("utf-8") 

def menu_104():
    level104 = """Please click on the following link to get a quotation and insure your car:
    
    https://xxxxxx.ngrok.io    

*** _Please contact us on 17xxxxxx for further assistance._
*** _You can type *M* if you wish to return to main menu or *Q* to quit._"""
    return level104

def menu_105():
    level105 = """Please send an email to claims@company.c0m and attach the police report of the car accident along with some photos of your car damages.

*** _Please contact us on 17xxxxxx for further assistance._
*** _You can type *M* if you wish to return to main menu or *Q* to quit._"""
    return level105

def menu_1004():
    level1004 = """الرجاء الضغط على المرفق التالي للحصول على تسعيرة لتأمين مركبتك ومن ثم تأمينها:
    
    https://xxxxxx.ngrok.io    

يرجى الاتصال بمركز الاتصال على 17xxxxxx خلال ساعات العمل لدينا للحصول على أي مساعدة إضافية.
يمكنك إدخال "ر" للعودة إلى القائمة الرئيسية أو "خ" للخروج النهائي من المحادثة."""
    return level1004.encode("utf-8")

def menu_1005():
    level1005 = """الرجاء مراسلتنا على عنوان البريد الالكتروني التالي claims@company.c0m و أرفق رسالتك بنسخة عن تقرير الشرطة و صور الأضرار في مركبتك.  

يرجى الاتصال بنا على 17xxxxxx للحصول على أي مساعدة إضافية.
يمكنك إدخال "ر" للعودة إلى القائمة الرئيسية أو "خ" للخروج النهائي من المحادثة."""
    return level1005.encode("utf-8")

def menu_210():
    level210 = """Please select your inquiry topic:
    
    *1.* Main office & outlets info
    *2.* Islamic insurance products for individuals
    *3.* Make a request
    *4.* Make a complaint
    *5.* Useful contact numbers

*** _Please type 1, 2, 3, etc. to continue or *M* to return to main menu._"""
    return level210
    
def menu_2100():
    level2100 = """الرجاء الإختيار من القائمة التالية:
    
    *١.* معلومات عن مكاتب الشركة
    *٢.* التأمين الإسلامي للأفراد
    *٣.* تقديم طلب
    *٤.* تقديم شكوى
    *٥.* أرقام تهمُك

*** الرجاء إختيار ١, ٢, إلخ للمتابعة أو أدخل "ر" للعودة إلى القائمة الرئيسية."""
    return level2100.encode("utf-8")
    
def menu_212():
    level212 = """Our insurance products offerings for individuals:
    
    *-* Motor insurance for Individuals Plan
    *-* Property All Risk Plan (incl. burglary)
    *-* Family Legacy Plan
    *-* Harvest Plan (single contribution)
    *-* Target Retirement Plan
    *-* Target Education Plan
    *-* Target Accumulation Plan
    *-* Mustaqbal Plan
    *-* Kafalah Plan (mortgage)
    *-* Tawasul Income Plan

For more info, please click on https://www.company.c0m/our-products

*** _Please contact us on 17xxxxxx for further assistance or type *P* to return to previous menu._
*** _You can type *M* if you wish to return to main menu or *Q* to quit._"""
    return level212

def menu_2102():
    level2102 = """عروضنا لمنتجات التأمين للأفراد تشمل اللآتي:
    
    *-* التأمين على المركبات
    *-* الحريق والأخطار الإضافية
    *-* برنامج الشركة تراث العائلة
    *-* برنامج الشركة الحصاد
    *-* برنامج الشركة أهداف التقاعد
    *-* برنامج الشركة أهداف التعليم
    *-* برنامج الشركة أهداف الإدخار
    *-* برنامج الشركة مستقبل
    *-* برنامج الشركة كفالة
    *-* برنامج الشركة تواصل الدخل
    
يرجى الضغط على المرفق التالي للمزيد من المعلومات http://company.c0m/ar/our-products

يرجى الاتصال بمركز الاتصال على 17xxxxxx خلال ساعات العمل لدينا للحصول على المساعدة أو أدخل "س" للعودة إلى القائمة السابقة.
كما يمكنك إدخال "ر" للعودة إلى القائمة الرئيسية أو "خ" للخروج النهائي من المحادثة."""
    return level2102.encode("utf-8")
    
def menu_213():
    level213 = """Please type your request here and hit the *Send* button.""" 
    return level213

def menu_2103():
    level2103 = """الرجاء كتابة طلبك هنا و من ثمَ الضغط على زر الإرسال.""" 
    return level2103.encode("utf-8")

def menu_214():
    level214 = """Please type your complaint here and hit the *Send* button.""" 
    return level214    

def menu_2104():
    level2104 = """يرجى كتابة شكواك هنا و من ثمَ الضغط على زر الإرسال.""" 
    return level2104.encode("utf-8")   

def menu_215():
    level215 = """*-* Invita Roadside Assistance: 1xxxxxxxx
*-* 360 Medical Support: Bahrain 800xxxxx & Outside Bahrain +973 1xxxxxxxx

*** _Please contact us on 17xxxxxx for further assistance or type *P* to return to previous menu._
*** _You can type *M* if you wish to return to main menu or *Q* to quit._"""
    return level215

def menu_2105():
    level2105 = """ـ خدمة المساعدة على الطريق من أنفيتا: 1xxxxxxxx
ـ للمساعدة الطبية من 360: 800xxxxx داخل البحرين و 973xxxxxx+ خارج البحرين

يمكنك إدخال "ر" للعودة إلى القائمة الرئيسية أو "خ" للخروج النهائي من المحادثة."""
    return level2105.encode("utf-8") 

def menu_600():
    level600 = """Please select the office or outlet of interest:
    
    *1.* Main Office
    *2.* Arad Outlet
    *3.* BDF Outlet
    *4.* East Riffa Outlet

*** _Please type 1, 2, 3, etc. to continue or type *P* to return to previous menu._
*** _You can type *M* if you wish to return to main menu or *Q* to quit._"""
    return level600

def menu_6000():
    level6000 = """الرجاء إختيار الفرع الذي تريده:     
    
    *١.* المكتب الرئيسي
    *٢.* فرع عراد
    *٣.* فرع وادي السيل
    *٤.* فرع الرفاع

الرجاء إختيار ١, ٢, إلخ للمتابعة أو أدخل "س" للعودة إلى القائمة السابقة.
يمكنك إدخال "ر" للعودة إلى القائمة الرئيسية أو "خ" للخروج النهائي من المحادثة."""
    return level6000.encode("utf-8") 

def menu_601():
    level601 = """*- Telephone:* 17xxxxxx 
    
*- Address:* xxxx Tower, Bldg xxxx, Road xxxx, Block xxx, XXXXXX District. (https://goo.gl/maps/htVvuBxg7oKByR9S9)

*- Opening Hours:* 8am through 4pm from Sunday to Thursday except for national holidays and during Ramadan

*** _Please type *P* to return to previous menu or *M* to return to main menu._"""
    return level601

def menu_6001():
    level6001 = """هاتف: 17xxxxxx
العنوان: بناية xxxxx مبنى xxxx شارع xxxx مجمع xxx ضاحية السيف (https://goo.gl/maps/htVvuBxg7oKByR9S9)
أوقات العمل من الساعة 8 صباحاً و حتى 4 مساءً ما عدا شهر رمضان و العطل الرسمية

يمكنك إدخال "س" للعودة إلى القائمة السابقة أو "ر" للعودة إلى القائمة الرئيسية."""
    return level6001.encode("utf-8")
    
def menu_602():
    level602 = """*- Telephone:* 17xxxxxx - Ext xxx 
    
*- Address:* Shop x, Building xxx, Road xx, Block xxx, XXXXX, Near Midway Super. (https://goo.gl/maps/RZzbAE9qtcdt2QPM7)

*- Opening Hours:* 9am through 5pm from Sunday to Thursday except for national holidays and during Ramadan

*** _Please type *P* to return to previous menu or *M* to return to main menu._"""
    return level602

def menu_6002():
    level6002 = """هاتف: 17xxxxxx تحويل xxx  
العنوان: محل 9 مبنى xxx شارع 44 مجمع xxx عراد بالقرب من أسواق ميدوي (https://goo.gl/maps/RZzbAE9qtcdt2QPM7)
أوقات العمل من الساعة 9 صباحاً و حتى 5 مساءً ما عدا شهر رمضان و العطل الرسمية

يمكنك إدخال "س" للعودة إلى القائمة السابقة أو "ر" للعودة إلى القائمة الرئيسية."""
    return level6002.encode("utf-8")
    
def menu_603():
    level603 = """*- Telephone:* 17xxxxxx - Ext xxx 
    
*- Address:* Bldg xxx, Road xxxx, Block xxx, XXXXXXX. (https://goo.gl/maps/Cgc6CzcdvyFEyjdf8)

*- Opening Hours:* 8am through 4pm from Sunday to Thursday except for national holidays and during Ramadan

*** _Please type *P* to return to previous menu or *M* to return to main menu._"""
    return level603

def menu_6003():
    level6003 = """هاتف: 17xxxxxx تحويل xxx  
العنوان: مبنى xxx شارع xxxx مجمع xxx وادي السيل (https://goo.gl/maps/Cgc6CzcdvyFEyjdf8)
أوقات العمل من الساعة 8 صباحاً و حتى 4 مساءً ما عدا شهر رمضان و العطل الرسمية

يمكنك إدخال "س" للعودة إلى القائمة السابقة أو "ر" للعودة إلى القائمة الرئيسية."""
    return level6003.encode("utf-8")
    
def menu_604():
    level604 = """*- Telephone:* 17xxxxxx - Ext xxx & xxx
    
*- Address:* Bldg xxx, Road xx, Block xxx, XXXXXXXXXX Ave, XXXXX. (https://goo.gl/maps/DNDXsz8pN7bCyF1u9)

*- Opening Hours:* 8am through 4pm from Sunday to Thursday except for national holidays and during Ramadan

*** _Please type *P* to return to previous menu or *M* to return to main menu._"""
    return level604

def menu_6004():
    level6004 = """هاتف: 17xxxxxx تحويل xxx  
العنوان: مبنى xxx شارع xx مجمع xxx الرفاع الشرقي (https://goo.gl/maps/DNDXsz8pN7bCyF1u9)
أوقات العمل من الساعة 8 صباحاً و حتى 4 مساءً ما عدا شهر رمضان و العطل الرسمية

يمكنك إدخال "س" للعودة إلى القائمة السابقة أو "ر" للعودة إلى القائمة الرئيسية."""
    return level6004.encode("utf-8")
    
def menu_605():
    level605 = """*- Telephone:* 17xxxxxx - Ext xxx 
    
*- Address:* Bldg xxx, Road xxxx, Block xxx, XXXXXX, XXXXXXXXX. (https://goo.gl/maps/atxAp5zdGRrweCLe9)

*- Opening Hours:* 8am through 4pm from Sunday to Thursday except for national holidays and during Ramadan

*** _Please type *P* to return to previous menu or *M* to return to main menu._"""
    return level605

def menu_6005():
    level6005 = """هاتف: 17xxxxxx تحويل xxx
العنوان: مبنى xxx شارع xxxx مجمع xxx قرب باب البحرين(https://goo.gl/maps/atxAp5zdGRrweCLe9)
أوقات العمل من الساعة 8 صباحاً و حتى 4 مساءً ما عدا شهر رمضان و العطل الرسمية

يمكنك إدخال "س" للعودة إلى القائمة السابقة أو "ر" للعودة إلى القائمة الرئيسية."""
    return level6005.encode("utf-8")

def menu_220(mobile):
    time_tuple = time.localtime()
    ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
    mysqldb = mydb()
    mycursor1 = mysqldb.cursor()
    mycursor2 = mysqldb.cursor()
    mycursor3 = mysqldb.cursor()
    
    sql1 = """SELECT * FROM pol_details WHERE mobile= """ + str(mobile)
    sql3 = """INSERT INTO policies (mobile, pol_no, pol_year, exp_date, renewal_prem, selection, timestamp) VALUES (%s, %s, %s, STR_TO_DATE(%s,'%d/%m/%Y'), %s, %s, %s)"""
    mycursor1.execute(sql1)
    myresult1 = mycursor1.fetchall()
    
    j = 0
    level220 = """The following are your current active motor policies with Company:
    """
    for pol in myresult1:
        if j == 10:
            break
        print(pol[5],"/",pol[6])
        sql2 = """SELECT * FROM policies WHERE pol_no=""" + str(pol[5]) + """ AND pol_year=""" + str(pol[6])
        mycursor2.execute(sql2)
        myresult2 = mycursor2.fetchall()
        if myresult2 == []:
            rec = (mobile, pol[5], pol[6], '01/01/1900', 0, j+1, ts)
            mycursor3.execute(sql3, rec)
            mysqldb.commit()
        level220 = level220 + str(j+1) + """. *""" + str(pol[5])+"/"+str(pol[6]) + """*
    """    
        j += 1  

    level220 = level220 + """    
*** _Please select your option by typing 1, 2, etc. to continue_
*** _You can type *56* in case your motor policy is not listed or *M* to return to main menu_"""
    mysqldb.close()
    return level220 

def menu_2200(mobile):
    time_tuple = time.localtime()
    ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
    mysqldb = mydb()
    mycursor1 = mysqldb.cursor()
    mycursor2 = mysqldb.cursor()
    mycursor3 = mysqldb.cursor()
    
    sql1 = """SELECT * FROM pol_details WHERE mobile= """ + str(mobile)
    sql3 = """INSERT INTO policies (mobile, pol_no, pol_year, exp_date, renewal_prem, selection, timestamp) VALUES (%s, %s, %s, STR_TO_DATE(%s,'%d/%m/%Y'), %s, %s, %s)"""
    mycursor1.execute(sql1)
    myresult1 = mycursor1.fetchall()
    
    j = 0
    level2200 = """فيما يلي تجد الوثائق الحالية الخاصة بك مع الشركة:
    """
    for pol in myresult1:
        if j == 10:
            break
        print(pol[5],"/",pol[6])
        sql2 = """SELECT * FROM policies WHERE pol_no=""" + str(pol[5]) + """ AND pol_year=""" + str(pol[6])
        mycursor2.execute(sql2)
        myresult2 = mycursor2.fetchall()
        if myresult2 == []:
            rec = (mobile, pol[5], pol[6], '01/01/1900', 0, j+1, ts)
            mycursor3.execute(sql3, rec)
            mysqldb.commit()
        level2200 = level2200 + str(arabic(j+1)) + """. *""" + str(pol[5])+"/"+str(pol[6]) + """*
    """
        j += 1

    level2200 = level2200 + """    
*** الرجاء إختيار ١, ٢, إلخ للمتابعة
*** كما يمكنك إختيار *٥٦* بحال عدم بيان وثيقة التأمين أو أدخل "ر" للعودة إلى القائمة الرئيسية"""
    mysqldb.close()
    return level2200.encode("utf-8") 

def menu_300():
    level300 = """Please type your motor policy details as follows:
    
*1. Year of Policy (4-digits):*"""
    return level300

def menu_3000():
    level3000 = """الرجاء إدخال تفاصيل وثيقة تأمين المركبة في الآتي:

١. سنة إصدار الوثيقة (4-أرقام):"""
    return level3000.encode("utf-8") 

def menu_301():
    level301 = """Please type your CPR/CR Number:"""
    return level301

def menu_3001():
    level3001 = """ الرجاء إدخال الرقم الشخصي (CPR/CR):"""
    return level3001.encode("utf-8") 

def menu_420(mobile):    
    time_tuple = time.localtime()
    ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
    mysqldb = mydb()
    mycursor1 = mysqldb.cursor()
    mycursor2 = mysqldb.cursor()
    mycursor3 = mysqldb.cursor()
    
    sql1 = """SELECT * FROM pol_details WHERE mobile= """ + str(mobile)
    sql3 = """INSERT INTO policies (mobile, pol_no, pol_year, exp_date, renewal_prem, selection, timestamp) VALUES (%s, %s, %s, STR_TO_DATE(%s,'%d/%m/%Y'), %s, %s, %s)"""
    mycursor1.execute(sql1)
    myresult1 = mycursor1.fetchall()
    
    j = 0
    level420 = """The following are your current active motor policies with Company:
    """
    for pol in myresult1:
        if j == 10:
            break
        print(pol[5],"/",pol[6])
        sql2 = """SELECT * FROM policies WHERE pol_no=""" + str(pol[5]) + """ AND pol_year=""" + str(pol[6])
        mycursor2.execute(sql2)
        myresult2 = mycursor2.fetchall()
        if myresult2 == []:
            rec = (mobile, pol[5], pol[6], '01/01/1900', 0, j+1, ts)
            mycursor3.execute(sql3, rec)
            mysqldb.commit()               
                                                 
        level420 = level420 + str(j+1) + """. *""" + str(pol[5])+"/"+str(pol[6]) + """*
    """
        j += 1

    level420 = level420 + """
    
*** _Please select your option by typing 1, 2, etc. to continue_
*** _Or type *M* to return to main menu_"""
    mysqldb.close()
    return level420 

def menu_4200(mobile):    
    time_tuple = time.localtime()
    ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
    mysqldb = mydb()
    mycursor1 = mysqldb.cursor()
    mycursor2 = mysqldb.cursor()
    mycursor3 = mysqldb.cursor()
    
    sql1 = """SELECT * FROM pol_details WHERE mobile= """ + str(mobile)
    sql3 = """INSERT INTO policies (mobile, pol_no, pol_year, exp_date, renewal_prem, selection, timestamp) VALUES (%s, %s, %s, STR_TO_DATE(%s,'%d/%m/%Y'), %s, %s, %s)"""
    mycursor1.execute(sql1)
    myresult1 = mycursor1.fetchall()
    
    j = 0
    level4200 = """فيما يلي تجد وثائق التأمين الحالية الخاصة بك مع الشركة:
    """
    for pol in myresult1:
        if j == 10:
            break
        print(pol[5],"/",pol[6])
        sql2 = """SELECT * FROM policies WHERE pol_no=""" + str(pol[5]) + """ AND pol_year=""" + str(pol[6])
        mycursor2.execute(sql2)
        myresult2 = mycursor2.fetchall()
        if myresult2 == []:
            rec = (mobile, pol[5], pol[6], '01/01/1900', 0, j+1, ts)
            mycursor3.execute(sql3, rec)
            mysqldb.commit()      
                                                 
        level4200 = level4200 + str(arabic(j+1)) + """. *""" + str(pol[5])+"/"+str(pol[6]) + """*
    """
        j += 1

    level4200 = level4200 + """
    
*** الرجاء إختيار ١, ٢, إلخ للمتابعة
*** يمكنك إدخال "ر" للعودة إلى القائمة الرئيسية إن كنت لا ترغب في المتابعة"""
    mysqldb.close()
    return level4200.encode("utf-8")  

def menu_330(pol_no,pol_year):
    level330 = """What do you wish to do with ```""" + str(pol_no) + """/""" + str(pol_year) + """```?
    *1.* See how much to renew it for a new term
    *2.* Check its expiry date
    *3.* Go back to main menu

*** _Please select your answer by typing 1 or 2 to continue_"""
    return level330
    
def menu_3300(pol_no,pol_year):
    level3300 = """ماذا تريد أن تفعل بوثيقة التأمين """ + str(pol_no) + """/""" + str(pol_year) + """؟
     ١. سعر تجديد الوثيقة
     ٢. التحقق من تاريخ انتهاء الصلاحية
     ٣. الرجوع إلى القائمة الرئيسية

*** الرجاء إختيار ١, ٢, إلخ للمتابعة"""
    return level3300.encode("utf-8") 

def menu_450(pol_no,pol_year):
    try:
        quotation = get_quote(pol_no,pol_year)
    except:
        return "NEXIST",0 
        
    if quotation == 0:
        return """Sorry unable to provide a quotation due to other additional endorsement(s) issued under your policy. 
Please contact our Call Center on 17xxxxxx during our working hours to get the best policy renewal quotation from our agents. 
Press *M* to return back to main menu or *Q* to quit.""",0
    elif quotation == 1:
        return """Sorry unable to provide a quotation because your policy expiry date is beyond 3 months. 
Please contact our Call Center on 17xxxxxx during our working hours for assistance. 
Press *M* to return back to main menu or *Q* to quit.""",0
    elif quotation == 2:
        return """Sorry unable to provide a quotation because your policy type is fleet. 
Please contact our Call Center on 17xxxxxx during our working hours for assistance. 
Press *M* to return back to main menu or *Q* to quit.""",0
    elif quotation == 3:
        return """Sorry unable to provide a quotation due to reaching the age limit which makes you eligible for a *discount* on your policy renewal premium. 
Please contact our Call Center on 17xxxxxx during our working hours for assistance. 
Press *M* to return back to main menu or *Q* to quit.""",0
    elif quotation == 4:
        return """Sorry unable to provide a quotation because your policy has a claim(s) and requires an agent to calculate your best policy renewal quotation. 
Please contact our Call Center on 17xxxxxx for assistance. 
Press *M* to return back to main menu or *Q* to quit.""",0
    elif quotation == 5:
        return """Sorry unable to provide a quotation because your policy is either issued by a broker or agent. Please contact your broker or agent to get the best policy renewal quotation from Company. 
Press *M* to return back to main menu or *Q* to quit.""",0
    elif quotation == 6:
        return """Sorry unable to provide a quotation because the chatbot only provides at the moment renewal quotations for regular policy types. 
Please contact our Call Center on 17xxxxxx during our working hours for assistance. 
Press *M* to return back to main menu or *Q* to quit.""",0
    elif quotation == 7:
        return """Sorry unable to provide a quotation because the chatbot encountered an issue with your policy. 
Please contact our Call Center on 17xxxxxx during our working hours for assistance. 
Press *M* to return back to main menu or *Q* to quit.""",0    
    else:
        policy_type     = quotation[0]
        vehicle_make    = quotation[1]
        vehicle_model   = quotation[2]
        registration_no = quotation[3]
        si              = quotation[4]
        rsa_prem        = quotation[5]
        vat_amt         = quotation[6]
        final_tot_amt   = quotation[9]

    if registration_no in ('TBA','Tba','tba','TBA ',' TBA',' TBA ','Tba ', 'tba '):
        time_tuple = time.localtime()
        ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
        mysqldb = mydb()
        mycursor1 = mysqldb.cursor()  
        mycursor2 = mysqldb.cursor()  
        sql1 = """SELECT * FROM tba WHERE pol_no= """ + str(pol_no) + """ AND pol_year=""" + str(pol_year)
        sql2 = """INSERT INTO tba (pol_no, pol_year, registration, timestamp) VALUES (%s, %s, %s, %s)"""
        mycursor1.execute(sql1)
        myresult1 = mycursor1.fetchall()
        if myresult1 == []:
            rec = (pol_no, pol_year, 'TBA', ts)
            mycursor2.execute(sql2, rec)
            mysqldb.commit()
        mysqldb.close()
    
    level450 = """The renewal quotation for your motor policy ```""" + str(pol_no) + """/""" + str(pol_year) + """```:
    ```Policy Type:``` *""" + str(policy_type) + """*
    ```Make & Model:``` *""" + str(vehicle_make) + """ """ + str(vehicle_model) + """*
    ```Registration:``` *""" + str(registration_no) + """*
    ```Sum Insured:``` *""" + str(si) + """*
    ```RSA Option:``` *""" + str(rsa_prem) + """ BD* 
    ```VAT Amount (5%):``` *""" + str(vat_amt) + """ BD*
    ```Renewal Premium:``` *""" + str(final_tot_amt) + """ BD*

```VAT Clause: In case of any changes in VAT rates, we shall charge you additional VAT on pro-rata basis for the period from the effective date of such changes in the VAT rate till the expiry of the policy```

Please make a selection:    
    *1.* Proceed to payment
    *2.* Check for another policy
    *3.* Go back to main menu    

*** _Please select your answer by typing 1, 2, or 3 to continue_
*** _Or type *Q* to quit_"""
    return level450,final_tot_amt

def menu_4500(pol_no,pol_year):
    try:
        quotation = get_quote(pol_no,pol_year)
    except:
        return "NEXIST",0 
        
    if quotation == 0:
        return """نأسف لعدم التمكن من تقديم عرض أسعار بسبب الإضافات الأخرى في وثيقة تأمينك.
يرجى الاتصال بمركز الاتصال الخاص بنا على 17xxxxxx خلال ساعات العمل للحصول على أفضل عرض لتجديد الوثيقة مع عملائنا. 
يمكنك إدخال "ر" للعودة إلى القائمة الرئيسية أو "خ" للخروج النهائي من المحادثة.""",0
    elif quotation == 1:
        return """نأسف لعدم التمكن من تقديم عرض أسعار حالياً. تاريخ انتهاء وثيقتك يتجاوز 3 أشهر. 
يرجى الاتصال بمركز الاتصال الخاص بنا على 17xxxxxx خلال ساعات العمل للحصول على أفضل عرض لتجديد الوثيقة مع عملائنا. 
يمكنك إدخال "ر" للعودة إلى القائمة الرئيسية أو "خ" للخروج النهائي من المحادثة.""",0
    elif quotation == 2:
        return """نأسف لعدم التمكن من تقديم عرض أسعار. نوع وثيقتك هي "أسطول".  
يرجى الاتصال بمركز الاتصال على 17xxxxxx خلال ساعات العمل لدينا للحصول على المساعدة.
يمكنك إدخال "ر" للعودة إلى القائمة الرئيسية أو "خ" للخروج النهائي من المحادثة.""",0
    elif quotation == 3:
        return """نأسف لعدم التمكن من تقديم عرض أسعار بسبب بلوغ الحد الأقصى للعمر ممَ يجعلك مؤهلاً للحصول على خصم إضافي على قسط تجديد وثيقتك.
يرجى الاتصال بمركز الاتصال على 17xxxxxx خلال ساعات العمل لدينا للحصول على المساعدة.
يمكنك إدخال "ر" للعودة إلى القائمة الرئيسية أو "خ" للخروج النهائي من المحادثة.""",0
    elif quotation == 4:
        return """نأسف لعدم التمكن من تقديم عرض أسعار. وثيقة التأمين الخاصة بك بها مطالبة (مطالبات) وتتطلب وكيلًا لإعطائك أفضل عرض أسعار من أجل تجديدها.
يرجى الاتصال بمركز الاتصال على 17xxxxxx خلال ساعات العمل لدينا للحصول على المساعدة.
يمكنك إدخال "ر" للعودة إلى القائمة الرئيسية أو "خ" للخروج النهائي من المحادثة.""",0
    elif quotation == 5:
        return """نأسف لعدم التمكن من تقديم عرض أسعار. وثيقتك صادرة عبر وسيط أو وكيل. يرجى الاتصال بالوسيط أو الوكيل للحصول على أفضل عرض أسعار لتجديد وثيقتك مع الشركة.
يمكنك إدخال "ر" للعودة إلى القائمة الرئيسية أو "خ" للخروج النهائي من المحادثة.""",0
    elif quotation == 6:
        return """نأسف لعدم التمكن من تقديم عرض أسعار. برنامج المتحدث الآلي يوفر في الوقت الحالي عروض أسعار تجديد لوثائق تأمين عادية فقط.
يرجى الاتصال بمركز الاتصال على 17xxxxxx خلال ساعات العمل لدينا للحصول على المساعدة.
يمكنك إدخال "ر" للعودة إلى القائمة الرئيسية أو "خ" للخروج النهائي من المحادثة.""",0
    elif quotation == 7:
        return """نأسف لعدم التمكن من تقديم عرض أسعار. المتحدث الآلي واجه مشكلة في تحديد بيانات وثيقة تأمينك الخاصة.
يرجى الاتصال بمركز الاتصال على 17xxxxxx خلال ساعات العمل لدينا للحصول على المساعدة.
يمكنك إدخال "ر" للعودة إلى القائمة الرئيسية أو "خ" للخروج النهائي من المحادثة.""",0 
    else:
        policy_type     = quotation[0]
        vehicle_make    = quotation[1]
        vehicle_model   = quotation[2]
        registration_no = quotation[3]
        si              = quotation[4]
        rsa_prem        = quotation[5]
        vat_amt         = quotation[6]
        final_tot_amt   = quotation[9]

    if registration_no in ('TBA','Tba','tba','TBA ',' TBA',' TBA ','Tba ', 'tba '):
        time_tuple = time.localtime()
        ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
        mysqldb = mydb()
        mycursor1 = mysqldb.cursor()  
        mycursor2 = mysqldb.cursor()  
        sql1 = """SELECT * FROM tba WHERE pol_no= """ + str(pol_no) + """ AND pol_year=""" + str(pol_year)
        sql2 = """INSERT INTO tba (pol_no, pol_year, registration, timestamp) VALUES (%s, %s, %s, %s)"""
        mycursor1.execute(sql1)
        myresult1 = mycursor1.fetchall()
        if myresult1 == []:
            rec = (pol_no, pol_year, 'TBA', ts)
            mycursor2.execute(sql2, rec)
            mysqldb.commit()
        mysqldb.close()
    
    level4500 = """عرض سعر التجديد لوثيقة تأمين سيارتك """ + str(pol_no) + """/""" + str(pol_year) + """:
    ```نوع الوثيقة:``` *""" + str(policy_type) + """*
    ```الصنع و الطراز:``` *""" + str(vehicle_make) + """ """ + str(vehicle_model) + """*
    ```رقم التسجيل:``` *""" + str(registration_no) + """*
    ```مبلغ التغطية:``` *""" + str(si) + """*
    ```خيار خدمة المساعدة على الطريق:``` *""" + str(rsa_prem) + """ د. ب.* 
    ```مبلغ ضريبة القيمة المضافة  (٥%):``` *""" + str(vat_amt) + """ د. ب.*
    ```قسط التجديد: ``` *""" + str(final_tot_amt) + """ د. ب.*

```بند ضريبة القيمة المضافة: في حال حدوث أي تغيير على معدلات ضريبة القيمة المضافة، سنقوم بخصم ضريبة القيمة المضافة الإضافية على أساس تناسبي للفترة من تاريخ سريان هذا التغيير في معدل ضريبة القيمة المضافة حتى انتهاء صلاحية الوثيقة.```

يرجى الإختيار:    
     ١. التوجه إلى عملية الدفع
     ٢. التحقق من وثيقة تأمين أخرى
     ٣. الرجوع إلى القائمة الرئيسية

*** أو أدخل "خ" للخروج النهائي من المحادثة."""
    return level4500.encode("utf-8"),final_tot_amt

def menu_480(pol_no,pol_year):
    try:
        (cur_exp,new_exp) = find_expiry(pol_no,pol_year)
    except:
        return "NEXIST"
    level480 = """Your motor policy ```""" + str(pol_no) + """/""" + str(pol_year) + """``` expiry date is *""" + str(cur_exp).split(" ")[0] + """*. What do you wish to do next?
    *1.* See how much to renew it for a new term
    *2.* Go back to main menu

*** _Please select your answer by typing 1 or 2 to continue or *Q* to quit_"""
    return level480

def menu_4800(pol_no,pol_year):
    try:
        (cur_exp,new_exp) = find_expiry(pol_no,pol_year)
    except:
        return "NEXIST"
    level4800 = """تاريخ انتهاء وثيقة التأمين الخاصة بك """ + str(pol_no) + """/""" + str(pol_year) + """ هو *""" + str(cur_exp).split(" ")[0] + """*. ماذا تريد أن تفعل؟
    
     ١.  كم السعر لتجديدها لفترة جديدة
     ٢. العودة إلى القائمة الرئيسية

*** الرجاء إختيار ١ أو ٢ للمتابعةأو أدخل "خ" للخروج النهائي من المحادثة."""
    return level4800.encode("utf-8")

def menu_497():
    level497 = """Your current vehicle registration no. is set to unknown in our data. Do you wish to provide the correct one as noted in your ownership card before you proceed?
    *1.* Yes
    *2.* No"""        
    return level497

def menu_4970():
    level4970 = """إنَ رقم تسجيل مركبتك الحالي المسجل في بياناتنا غير صحيح. أترغب في تصحيحه قبل المتابعة؟
    ١. أجل
    ٢. كلا"""        
    return level4970.encode("utf-8")

def menu_498():
    level498 = """Please insert the registration no. which is imprinted on your vehicle ownership card:"""
    return level498

def menu_4971():
    level4971 = """الرجاء إدخال رقم تسجيل مركبتك كما هو مدون في بطاقة الملكية: """
    return level4971.encode("utf-8")

def menu_499(pol_no,pol_year):
    time_tuple = time.localtime()
    ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
    mysqldb = mydb()
    mycursor = mysqldb.cursor()  
    sql = """UPDATE tba SET registration='TOZ' WHERE pol_no=""" + str(pol_no) + """ AND pol_year=""" + str(pol_year)
    mycursor.execute(sql)
    mysqldb.commit()
    mysqldb.close()    

def menu_500(final_tot_amt,pol_no,pol_year):
    order_id = order('WHATSAPP')
    params = {'order_amount': float(final_tot_amt),
              'order_description': 'Whatsapp Renewal',
              'order_id': str(order_id), 
              'policy_number': int(pol_no),
              'policy_year': int(pol_year)}  
    r = requests.post('http://xx.xx.xx.xx/api/generatePayment',headers={"Accept":"application/json"},data= params)
    json_data = json.loads(r.text)
    print json_data
    url = json_data['url'].replace("http://xx.xx.xx.xx","https://xxxxxxxxxx.ngrok.io")    
    level500 = """Please follow the link to make your payment for *""" + str(final_tot_amt) + """ BD* to renew your motor policy *""" + str(pol_no) + """/""" + str(pol_year) + """*:
""" + str(url) + """

or type *M* to return to main menu or *Q* to quit."""
    print level500
    return level500

def menu_5000(final_tot_amt,pol_no,pol_year):
    order_id = order('WHATSAPP')
    params = {'order_amount': float(final_tot_amt),
              'order_description': 'Whatsapp Renewal',
              'order_id': str(order_id), 
              'policy_number': int(pol_no),
              'policy_year': int(pol_year)}  
    r = requests.post('http://xx.xx.xx.xx/api/generatePayment',headers={"Accept":"application/json"},data= params)
    json_data = json.loads(r.text)
    print json_data
    url = json_data['url'].replace("http://xx.xx.xx.xx","https://xxxxxxxxxx.ngrok.io")    
    level5000 = """الرجاء الضغط على المرفق التالي لدفع مبلغ *""" + str(final_tot_amt) + """* دينار بحريني لتجديد وثيقة التأمين *""" + str(pol_no) + """/""" + str(pol_year) + """*:
""" + str(url) + """

أو يمكنك إدخال "ر" للعودة إلى القائمة الرئيسية أو "خ" للخروج النهائي من المحادثة."""
    return level5000.encode("utf-8")

def menu_900(pol_no,pol_year):
    order_id = order('REGISTR')
    params = {'order_amount': float(1.05),
              'order_description': 'Registration Change',
              'order_id': str(order_id), 
              'policy_number': int(pol_no),
              'policy_year': int(pol_year)}  
    r = requests.post('http://xx.xx.xx.xx/api/generatePayment',headers={"Accept":"application/json"},data= params)
    json_data = json.loads(r.text)
    print json_data
    url = json_data['url'].replace("http://xx.xx.xx.xx","https://xxxxxxxxxx.ngrok.io")    
    level900 = """Please follow the link to make your payment for *1.05 BD* to change the registration number of your vehicle under motor policy *""" + str(pol_no) + """/""" + str(pol_year) + """*:
""" + str(url) + """

or type *M* to return to main menu or *Q* to quit."""
    print level900
    return level900

def menu_9000(pol_no,pol_year):
    order_id = order('REGISTR')
    params = {'order_amount': float(1.05),
              'order_description': 'Registration Change',
              'order_id': str(order_id), 
              'policy_number': int(pol_no),
              'policy_year': int(pol_year)}  
    r = requests.post('http://xx.xx.xx.xx/api/generatePayment',headers={"Accept":"application/json"},data= params)
    json_data = json.loads(r.text)
    print json_data
    url = json_data['url'].replace("http://xx.xx.xx.xx","https://xxxxxxxxxx.ngrok.io")    
    level9000 = """الرجاء الضغط على المرفق التالي لدفع مبلغ *١.٠٥* دينار بحريني لتغير رقم لوحة مركبتك في البوليصة  *""" + str(pol_no) + """/""" + str(pol_year) + """*:
""" + str(url) + """

أو يمكنك إدخال "ر" للعودة إلى القائمة الرئيسية أو "خ" للخروج النهائي من المحادثة."""
    return level9000.encode("utf-8")

def policy(whatsappNB):
    mobile = (whatsappNB.split("whatsapp:+973"))[1]
    mysqldb = mydb()
    mycursor = mysqldb.cursor()    
    sql = """SELECT * FROM policies WHERE mobile= """ + str(mobile)
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    mysqldb.close()
    policies_no =    {}
    policies_year =  {}    
    for pol in myresult:
        policies_no.update({pol[6] : pol[1]})
        policies_year.update({pol[6] : pol[2]})
    pol_no =           policies_no[max(policies_no.keys())]
    pol_year =         policies_year[max(policies_no.keys())]   
    print(pol_no,"/",pol_year)
    return pol_no,pol_year    

def fetch_reg_no(whatsappNB):
    mobile = (whatsappNB.split("whatsapp:+973"))[1]
    mysqldb = mydb()
    mycursor = mysqldb.cursor()    
    sql = """SELECT * FROM registration WHERE mobile= """ + str(mobile)
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    mysqldb.close()
    registration =    {}
    for reg in myresult:
        registration.update({reg[5] : reg[4]})
    reg_no = registration[max(registration.keys())]
    print(reg_no)
    return reg_no    

@app.route('/renewalBot', methods=['GET', 'POST'])
def bot(): 
    whatsappNB = request.form.get('From')
    selection = request.form.get('Body')
    resp = MessagingResponse()   
    
    #Check for international numbers
    mob_no = (whatsappNB.split("whatsapp:+"))[1]
    if int(mob_no[:3]) != 973:
        menu_no = search_db(whatsappNB)
        if menu_no == 0:
            insert_db(whatsappNB, 1)
        else:
            update_db(whatsappNB, int(menu_no)+1)
        resp.message(menu_02())
        return str(resp)
    
    mobile = (whatsappNB.split("whatsapp:+973"))[1]
    menu_nb = search_db(whatsappNB)
    
    if selection in ('q','Q','quit','Quit'):
        update_db(whatsappNB, 1)
        resp.message(menu_001())
        return str(resp)

    if selection in ('خ','خروج'):
        update_db(whatsappNB, 1)
        resp.message(menu_0010())
        return str(resp)

    if selection in ('m','M','menu'):
        update_db(whatsappNB, 100)
        resp.message(menu_100())
        return str(resp)

    if selection in ('ر','رئيسة','رئيسية'):
        update_db(whatsappNB, 1000)
        resp.message(menu_1000())
        return str(resp)
        
    if selection in ('p','P'):
        if ((menu_nb > 600) & (menu_nb < 1000)):
            update_db(whatsappNB, 600)
            resp.message(menu_600())
        elif ((menu_nb == 212) | (menu_nb == 600) | (menu_nb == 215)):
            update_db(whatsappNB, 210)
            resp.message(menu_210())
        elif menu_nb == 210:
            update_db(whatsappNB, 100)
            resp.message(menu_100())             
        return str(resp)        

    if selection in ('س','سابق'):
        if menu_nb > 6000:
            update_db(whatsappNB, 6000)
            resp.message(menu_6000())
        elif ((menu_nb == 2102) | (menu_nb == 6000) | (menu_nb == 2105)):
            update_db(whatsappNB, 2100)
            resp.message(menu_2100())
        elif menu_nb == 2100:
            update_db(whatsappNB, 1000)
            resp.message(menu_1000())             
        return str(resp)        
    
    if menu_nb == 1:        
        update_db(whatsappNB, 100)
        resp.message(menu_100())
        return str(resp)
    elif menu_nb == 100:
        try:
            if int(selection) not in range(1, 7):
                resp.message(menu_00())
                return str(resp)
        except:
            resp.message(menu_01())
            return str(resp)
    elif menu_nb == 1000:
        try:
            if int(selection) not in range(1, 7):
                resp.message(menu_000())
                return str(resp)
        except:
            resp.message(menu_010())
            return str(resp)            
    elif menu_nb == 210:
        try:
            if int(selection) not in range(1, 6):
                resp.message(menu_00())
                return str(resp)            
        except:
            resp.message(menu_01())
            return str(resp)
    elif menu_nb == 2100:
        try:
            if int(selection) not in range(1, 6):
                resp.message(menu_000())
                return str(resp)            
        except:
            resp.message(menu_010())
            return str(resp)            
    elif menu_nb == 220:
        try:
            if ((int(selection) not in range(1, 11)) & (int(selection) != 55) & (int(selection) != 56)):
                print("incorrect digit")
                resp.message(menu_00())
                return str(resp)            
        except:
            resp.message(menu_01())
            return str(resp)            
    elif menu_nb == 2200:
        try:
            if ((int(selection) not in range(1, 11)) & (int(selection) != 55) & (int(selection) != 56)):
                print("incorrect digit")
                resp.message(menu_000())
                return str(resp)            
        except:
            resp.message(menu_010())
            return str(resp)                        
    elif menu_nb == 420:
        try:
            if int(selection) not in range(1, 11):
                resp.message(menu_00())
                return str(resp)            
        except:
            resp.message(menu_01())
            return str(resp)     
    elif menu_nb == 4200:
        try:
            if int(selection) not in range(1, 11):
                resp.message(menu_000())
                return str(resp)            
        except:
            resp.message(menu_010())
            return str(resp)                  
    elif menu_nb == 330:
        try:
            if int(selection) not in range(1, 4):
                resp.message(menu_00())
                return str(resp)
        except:
            resp.message(menu_01())
            return str(resp)      
    elif menu_nb == 3300:
        try:
            if int(selection) not in range(1, 4):
                resp.message(menu_000())
                return str(resp)
        except:
            resp.message(menu_010())
            return str(resp)                  
    elif menu_nb == 450:
        try:
            if int(selection) not in range(1, 4):
                resp.message(menu_00())
                return str(resp)
        except:
            resp.message(menu_01())
            return str(resp)
    elif menu_nb == 4500:
        try:
            if int(selection) not in range(1, 4):
                resp.message(menu_000())
                return str(resp)
        except:
            resp.message(menu_010())
            return str(resp)            
    elif menu_nb == 480:
        try:
            if int(selection) not in range(1, 3):
                resp.message(menu_00())
                return str(resp)
        except:
            resp.message(menu_01())
            return str(resp)
    elif menu_nb == 4800:
        try:
            if int(selection) not in range(1, 3):
                resp.message(menu_000())
                return str(resp)
        except:
            resp.message(menu_010())
            return str(resp)            
    elif menu_nb == 497:
        try:
            if int(selection) not in range(1, 3):
                resp.message(menu_00())
                return str(resp)
        except:
            resp.message(menu_01())
            return str(resp)            
    elif menu_nb == 4970:
        try:
            if int(selection) not in range(1, 3):
                resp.message(menu_000())
                return str(resp)
        except:
            resp.message(menu_010())
            return str(resp)                        
    elif menu_nb == 500:
        try:
            if str(selection) not in (q,Q,m,M):
                resp.message(menu_03())
                return str(resp)
        except:
            resp.message(menu_04())
            return str(resp)           
    elif menu_nb == 5000:
        try:
            if str(selection) not in (q,Q,m,M):
                resp.message(menu_030())
                return str(resp)
        except:
            resp.message(menu_040())
            return str(resp)                       
    elif menu_nb == 600:
        try:
            if int(selection) not in range(1, 5):
                resp.message(menu_00())
                return str(resp)
        except:
            resp.message(menu_01())
            return str(resp)          
    elif menu_nb == 6000:
        try:
            if int(selection) not in range(1, 5):
                resp.message(menu_000())
                return str(resp)
        except:
            resp.message(menu_010())
            return str(resp)         
    elif menu_nb == 830:
        try:
            if int(selection) not in range(1, 6):
                resp.message(menu_00())
                return str(resp)            
        except:
            resp.message(menu_01())
            return str(resp)
    elif menu_nb == 8300:
        try:
            if int(selection) not in range(1, 6):
                resp.message(menu_000())
                return str(resp)            
        except:
            resp.message(menu_010())
            return str(resp)   
    elif menu_nb == 250:
        try:
            if int(selection) not in range(1, 3):
                resp.message(menu_00())
            else:
                (pol_no,pol_year) = policy(whatsappNB)                
                if int(selection) == 1:
                    mail('motor@company.c0m','Change Ownership Request via Whatsapp Chatbot for motor policy ' + str(pol_no) + '/' + str(pol_year),"Please contact the client on " +  str(mobile) + " to proceed with the request to change the vehicle ownership under the mentioned policy.")                    
                    update_db(whatsappNB, 251)
                    resp.message("""Thank you for your request. You will be contacted soon within our normal working hours once a service agent has been assigned to handle your request!

    *** _Please type *M* to return to main menu._""")
                else:
                    update_db(whatsappNB, 830)
                    resp.message(menu_830(pol_no,pol_year))
        except:
            resp.message(menu_01())
        return str(resp)
    elif menu_nb == 2500:
        try:
            if int(selection) not in range(1, 3):
                resp.message(menu_000())
            else:
                (pol_no,pol_year) = policy(whatsappNB)                
                if int(selection) == 1:
                    mail('motor@company.c0m','Change Ownership Request via Whatsapp Chatbot for motor policy ' + str(pol_no) + '/' + str(pol_year),"Please contact the client on " +  str(mobile) + " to proceed with the request to change the vehicle ownership under the mentioned policy.")                
                    update_db(whatsappNB, 2501)
                    resp.message("""شكرا لطلبك. سيتم الاتصال بك قريبًا ضمن ساعات عملنا بمجرد تعيين وكيل خدمة للتعامل مع طلبك!

    *** _الرجاء إدخال "ر" للعودة إلى القائمة الرئيسية._""")
                else:
                    update_db(whatsappNB, 8300)
                    resp.message(menu_8300(pol_no,pol_year))    
        except:
            resp.message(menu_010())            
        return str(resp)        
    elif menu_nb == 270:
        try:
            if int(selection) not in range(1, 3):
                resp.message(menu_00())
            else:
                (pol_no,pol_year) = policy(whatsappNB)
                if int(selection) == 1:
                    mail('motor@company.c0m','Policy Extension Request via Whatsapp Chatbot for motor policy ' + str(pol_no) + '/' + str(pol_year),"Please contact the client on " +  str(mobile) + " to proceed with the request to extend the insurance period under the mentioned policy.")
                    update_db(whatsappNB, 271)
                    resp.message("""Thank you for your request. You will be contacted soon within our normal working hours once a service agent has been assigned to handle your request!

    *** _Please type *M* to return to main menu._""")
                else:
                    update_db(whatsappNB, 830)
                    resp.message(menu_830(pol_no,pol_year))    
        except:
            resp.message(menu_01())
        return str(resp)
    elif menu_nb == 2700:
        try:
            if int(selection) not in range(1, 3):
                resp.message(menu_000())
            else:
                (pol_no,pol_year) = policy(whatsappNB)
                if int(selection) == 1:
                    mail('motor@company.c0m','Policy Extension Request via Whatsapp Chatbot for motor policy ' + str(pol_no) + '/' + str(pol_year),"Please contact the client on " +  str(mobile) + " to proceed with the request to extend the insurance period under the mentioned policy.")
                    update_db(whatsappNB, 2701)
                    resp.message("""شكرا لطلبك. سيتم الاتصال بك قريبًا ضمن ساعات عملنا بمجرد تعيين وكيل خدمة للتعامل مع طلبك!

    *** _الرجاء إدخال "ر" للعودة إلى القائمة الرئيسية._""")
                else:
                    update_db(whatsappNB, 8300)
                    resp.message(menu_8300(pol_no,pol_year))                        
        except:
            resp.message(menu_010())            
        return str(resp)        
    elif menu_nb == 280:
        try:
            if int(selection) not in range(1, 3):
                resp.message(menu_00())
            else:
                (pol_no,pol_year) = policy(whatsappNB)
                if int(selection) == 1:
                    mail('motor@company.c0m','Change Policy Type Request via Whatsapp Chatbot for motor policy ' + str(pol_no) + '/' + str(pol_year),"Please contact the client on " +  str(mobile) + " to proceed with the request to change the policy type under the mentioned policy.")
                    update_db(whatsappNB, 281)
                    resp.message("""Thank you for your request. You will be contacted soon within our normal working hours once a service agent has been assigned to handle your request!

    *** _Please type *M* to return to main menu._""")
                else:
                    update_db(whatsappNB, 830)
                    resp.message(menu_830(pol_no,pol_year))                       
        except:
            resp.message(menu_01())
        return str(resp)
    elif menu_nb == 2800:
        try:
            if int(selection) not in range(1, 3):
                resp.message(menu_000())
            else:
                (pol_no,pol_year) = policy(whatsappNB)
                if int(selection) == 1:
                    mail('motor@company.c0m','Change Policy Type Request via Whatsapp Chatbot for motor policy ' + str(pol_no) + '/' + str(pol_year),"Please contact the client on " +  str(mobile) + " to proceed with the request to change the policy type under the mentioned policy.")
                    update_db(whatsappNB, 2801)
                    resp.message("""شكرا لطلبك. سيتم الاتصال بك قريبًا ضمن ساعات عملنا بمجرد تعيين وكيل خدمة للتعامل مع طلبك!

    *** _الرجاء إدخال "ر" للعودة إلى القائمة الرئيسية._""")
                else:
                    update_db(whatsappNB, 8300)
                    resp.message(menu_8300(pol_no,pol_year))  
        except:
            resp.message(menu_010())            
        return str(resp)        
    elif menu_nb == 290:
        try:
            if int(selection) not in range(1, 3):
                resp.message(menu_00())
            else:
                (pol_no,pol_year) = policy(whatsappNB)
                if int(selection) == 1:
                    mail('motor@company.c0m','Cancel Policy Request via Whatsapp Chatbot for motor policy ' + str(pol_no) + '/' + str(pol_year),"Please contact the client on " +  str(mobile) + " to proceed with the request to cancel the mentioned policy.")
                    update_db(whatsappNB, 291)
                    resp.message("""Thank you for your request. You will be contacted soon within our normal working hours once a service agent has been assigned to handle your request!

    *** _Please type *M* to return to main menu._""")
                else:
                    update_db(whatsappNB, 830)
                    resp.message(menu_830(pol_no,pol_year))  
        except:
            resp.message(menu_01())
        return str(resp)
    elif menu_nb == 2900:
        try:
            if int(selection) not in range(1, 3):
                resp.message(menu_000())
            else:
                (pol_no,pol_year) = policy(whatsappNB)
                if int(selection) == 1:
                    mail('motor@company.c0m','Cancel Policy Request via Whatsapp Chatbot for motor policy ' + str(pol_no) + '/' + str(pol_year),"Please contact the client on " +  str(mobile) + " to proceed with the request to cancel the mentioned policy.")
                    update_db(whatsappNB, 2901)
                    resp.message("""شكرا لطلبك. سيتم الاتصال بك قريبًا ضمن ساعات عملنا بمجرد تعيين وكيل خدمة للتعامل مع طلبك!

    *** _الرجاء إدخال "ر" للعودة إلى القائمة الرئيسية._""")
                else:
                    update_db(whatsappNB, 8300)
                    resp.message(menu_8300(pol_no,pol_year)) 
        except:
            resp.message(menu_010())            
        return str(resp)        
    elif menu_nb == 213:
        # send an email to info@company.c0m 
        try:
            if str(selection) == "":
                resp.message("""Images and other attachment types are not supported at the moment! Please retry again with a clear text message in English.""")
            else:
                email('Request via Whatsapp Chatbot from ' + str(mobile),str(selection))
                update_db(whatsappNB, 210)
                resp.message("""Thank you for your request. You will be contacted shortly once a service agent has been assigned to handle your request!

    *** _Please type *P* to return to previous menu or *M* to return to main menu._""")
        except:
            resp.message("""You might have used unsupported special characters or emojis in your message. Please retry again with a clear text message in English.""")            
        return str(resp)
    elif menu_nb == 2103:
        # send an email to info@company.c0m 
        try:
            if str(selection) == "":
                resp.message("""الصور وأنواع المرفقات الأخرى غير مدعومة في الوقت الحالي! يرجى إعادة المحاولة برسالة نصية واضحة باللغة العربية.""")
            else:
                email('Request via Whatsapp Chatbot from ' + str(mobile),str(selection))
                update_db(whatsappNB, 2100)
                resp.message("""شكرا لطلبك. سيتم الاتصال بك قريبًا بمجرد تعيين وكيل خدمة للتعامل مع طلبك!

    *** _الرجاء إدخال "س" للعودة إلى القائمة السابقة أو "ر" للعودة إلى القائمة الرئيسية._""")
        except:
            resp.message("""ربما إستعملت رمز غير مدعوم على المتحدث الآلي. يرجى إعادة المحاولة برسالة نصية واضحة باللغة العربية.""")            
        return str(resp)        
    elif menu_nb == 214:
        # send an email to info@company.c0m 
        try:
            if str(selection) == "":
                resp.message("""Images and other attachment types are not supported at the moment! Only clear text messages are supported and in English language.""")
            else:            
                email('Complaint via Whatsapp Chatbot from ' + str(mobile),str(selection))
                update_db(whatsappNB, 210)
                resp.message("""Thank you for sharing your complaint. It will be carefully reviewed and we will come back to you soon after making sure that the necessary measures have been taken or in case we require some additional info from your end to assist you further.
                
    *** _Please type *P* to return to previous menu or *M* to return to main menu._""")
        except:
            resp.message("""You might have used unsupported special characters or emojis in your message. Please retry again with a clear text message in English.""")            
        return str(resp)                
    elif menu_nb == 2104:
        # send an email to info@company.c0m 
        try:
            if str(selection) == "":
                resp.message("""الصور وأنواع المرفقات الأخرى غير مدعومة في الوقت الحالي! يرجى إعادة المحاولة برسالة نصية واضحة باللغة العربية.""")
            else:            
                email('Complaint via Whatsapp Chatbot from ' + str(mobile),str(selection))
                update_db(whatsappNB, 2100)
                resp.message("""شكرا لك على تقديم شكواك. ستتم مراجعتها بعناية وسنتواصل معك بعد التأكد من اتخاذ التدابير اللازمة أو في حال طلب بعض المعلومات الإضافية من جانبك لمساعدتك بشكل أفضل.
                
    *** _الرجاء إدخال "س" للعودة إلى القائمة السابقة أو "ر" للعودة إلى القائمة الرئيسية._""")
            #selection = 0
        except:
            resp.message("""ربما إستعملت رمز غير مدعوم على المتحدث الآلي. يرجى إعادة المحاولة برسالة نصية واضحة باللغة العربية.""")            
        return str(resp)   

    if ((menu_nb == 0) | (menu_nb == 1)):
        x = 0
    else:
        if ((menu_nb == 220) | (menu_nb == 2200)):
            if ((int(selection) != 55) & (int(selection) != 56)):
                mobile = (whatsappNB.split("whatsapp:+973"))[1]
                time_tuple = time.localtime()
                ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
                mysqldb = mydb()
                mycursor1 = mysqldb.cursor()
                mycursor2 = mysqldb.cursor()
                sql1 = """SELECT pol_no, pol_year FROM policies WHERE mobile=""" + str(mobile) + """ AND selection=""" + str(int(selection))
                mycursor1.execute(sql1)
                myresult1 = mycursor1.fetchall()
                for pol in myresult1:
                    pol_no =    pol[0]
                    pol_year =  pol[1]
                print('Selection = ',selection)
                try:
                    sql2 = """UPDATE policies SET timestamp=(STR_TO_DATE('""" + str(ts) + """','%Y-%m-%d %H:%i:%s')) WHERE pol_no=""" + str(pol_no) + """ AND pol_year=""" + str(pol_year)              
                    mycursor2.execute(sql2)
                    mysqldb.commit()
                    mysqldb.close()
                except:
                    mysqldb.close()
                    if menu_nb == 220:
                        resp.message("""*You typed a wrong digit. Please choose the correct number from the above menu!*""")       
                    else:
                        resp.message("""*لقد أدخلت رقمًا خاطئًا. الرجاء إختيار الرقم الصحيح من القائمة أعلاه!*""")
                    return str(resp)                 
        if ((menu_nb == 720) | (menu_nb == 7200)):
            mobile = (whatsappNB.split("whatsapp:+973"))[1]
            time_tuple = time.localtime()
            ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
            mysqldb = mydb()
            mycursor1 = mysqldb.cursor()
            mycursor2 = mysqldb.cursor()
            sql1 = """SELECT pol_no, pol_year FROM policies WHERE mobile=""" + str(mobile) + """ AND selection=""" + str(int(selection))
            mycursor1.execute(sql1)
            myresult1 = mycursor1.fetchall()
            for pol in myresult1:
                pol_no =    pol[0]
                pol_year =  pol[1]
            print('Selection = ',selection)
            try:
                sql2 = """UPDATE policies SET timestamp=(STR_TO_DATE('""" + str(ts) + """','%Y-%m-%d %H:%i:%s')) WHERE pol_no=""" + str(pol_no) + """ AND pol_year=""" + str(pol_year)              
                mycursor2.execute(sql2)
                mysqldb.commit()
                mysqldb.close()
            except:
                mysqldb.close()
                if menu_nb == 720:
                    resp.message("""*You typed a wrong digit. Please choose the correct number from the above menu!*""")
                else:
                    resp.message("""*لقد أدخلت رقمًا خاطئًا. الرجاء إختيار الرقم الصحيح من القائمة أعلاه!*""")
                return str(resp)                                                
        if menu_nb == 420:            
            mobile = (whatsappNB.split("whatsapp:+973"))[1]
            time_tuple = time.localtime()
            ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
            mysqldb = mydb()
            mycursor1 = mysqldb.cursor()
            mycursor2 = mysqldb.cursor()
            sql1 = """SELECT * FROM policies WHERE mobile=""" + str(mobile) + """ AND selection=""" + str(selection)            
            mycursor1.execute(sql1)
            myresult1 = mycursor1.fetchall() 
            for pol in myresult1:
                pol_no = pol[1]
                pol_year = pol[2]
            print('Selection = ',selection)
            try:
                sql2 = """UPDATE policies SET timestamp=(STR_TO_DATE('""" + str(ts) + """','%Y-%m-%d %H:%i:%s')) WHERE pol_no=""" + str(pol_no) + """ AND pol_year=""" + str(pol_year)
                mycursor2.execute(sql2)
                mysqldb.commit()
                mysqldb.close()
            except:
                resp.message("""*You typed a wrong digit. Please choose the correct number from the above menu!*""")
                mysqldb.close()
                return str(resp)                
        if menu_nb == 4200:
            mobile = (whatsappNB.split("whatsapp:+973"))[1]
            time_tuple = time.localtime()
            ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
            mysqldb = mydb()
            mycursor1 = mysqldb.cursor()
            mycursor2 = mysqldb.cursor()
            sql1 = """SELECT * FROM policies WHERE mobile=""" + str(mobile) + """ AND selection=""" + str(int(selection))
            mycursor1.execute(sql1)
            myresult1 = mycursor1.fetchall() 
            for pol in myresult1:
                pol_no = pol[1]
                pol_year = pol[2]
            print('Selection = ',selection)
            try:
                sql2 = """UPDATE policies SET timestamp=(STR_TO_DATE('""" + str(ts) + """','%Y-%m-%d %H:%i:%s')) WHERE pol_no=""" + str(pol_no) + """ AND pol_year=""" + str(pol_year)
                mycursor2.execute(sql2)
                mysqldb.commit()
                mysqldb.close()
            except:
                resp.message("""*لقد أدخلت رقمًا خاطئًا. الرجاء إختيار الرقم الصحيح من القائمة أعلاه!*""")
                mysqldb.close()
                return str(resp)                                
        if menu_nb == 300:
            with open("C://inetpub//wwwroot//renewalBot//"+mobile+"-policy.log", mode="r") as pollog:
                flag = pollog.read()
            pollog.close()

            time_tuple = time.localtime()
            ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
            mysqldb = mydb()
            mycursor = mysqldb.cursor()  
                
            if int(flag) == 0:            
                pol_year = request.form.get('Body')                
                sql = """INSERT INTO policies (mobile, pol_no, pol_year, exp_date, renewal_prem, selection, timestamp) VALUES (%s, %s, %s, STR_TO_DATE(%s,'%d/%m/%Y'), %s, %s, %s)"""
                rec = (mobile, 0, pol_year, '01/01/2100', 0, 555, ts)
                mycursor.execute(sql, rec)
                mysqldb.commit()
                mysqldb.close()
                                
                os.remove(mobile+'-policy.log')                
                pollog = open("C://inetpub//wwwroot//renewalBot//"+mobile+"-policy.log", "w+")
                pollog.write('1')
                pollog.close()                                             
                resp.message('*2. Policy No.:*')  
                return str(resp)
            else:
                pol_no = request.form.get('Body')
                sql1 = """UPDATE policies SET pol_no=""" + str(pol_no) + """, selection=55, timestamp=(STR_TO_DATE('""" + str(ts) + """','%Y-%m-%d %H:%i:%s')) WHERE mobile=""" + str(mobile) + """ AND selection=555"""     
                mycursor.execute(sql1)
                mysqldb.commit()
                mysqldb.close()
                os.remove(mobile+'-policy.log')
                mysqldb = mydb()
                mycursor2 = mysqldb.cursor() 
                sql2 = """SELECT * FROM policies WHERE mobile=""" + str(mobile) + """ AND selection=55"""
                mycursor2.execute(sql2)
                myresult2 = mycursor2.fetchall()   
                mysqldb.close()
                for pol in myresult2:
                    pol_no = pol[1]
                    pol_year = pol[2]   
                print(pol_no,"/",pol_year)                     
            selection = 34
        if menu_nb == 3000:
            with open("C://inetpub//wwwroot//renewalBot//"+mobile+"-policy.log", mode="r") as pollog:
                flag = pollog.read()
            pollog.close()

            time_tuple = time.localtime()
            ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
            mysqldb = mydb()
            mycursor = mysqldb.cursor()              
            
            if int(flag) == 0:            
                pol_year = unidecode(u''.join(request.form.get('Body')))   
                sql = """INSERT INTO policies (mobile, pol_no, pol_year, exp_date, renewal_prem, selection, timestamp) VALUES (%s, %s, %s, STR_TO_DATE(%s,'%d/%m/%Y'), %s, %s, %s)"""
                rec = (mobile, 0, pol_year, '01/01/2100', 0, 555, ts)
                mycursor.execute(sql, rec)
                mysqldb.commit()
                mysqldb.close()
                                
                os.remove(mobile+'-policy.log')                
                pollog = open("C://inetpub//wwwroot//renewalBot//"+mobile+"-policy.log", "w+")
                pollog.write('1')
                pollog.close()                                             
                resp.message('*٢. رقم الوثيقة:*')  
                return str(resp)
            else:
                pol_no = unidecode(u''.join(request.form.get('Body')))     
                sql1 = """UPDATE policies SET pol_no=""" + str(pol_no) + """, selection=55, timestamp=(STR_TO_DATE('""" + str(ts) + """','%Y-%m-%d %H:%i:%s')) WHERE mobile=""" + str(mobile) + """ AND selection=555"""     
                mycursor.execute(sql1)
                mysqldb.commit()
                mysqldb.close()  
                os.remove(mobile+'-policy.log')
                mysqldb = mydb()
                mycursor2 = mysqldb.cursor() 
                sql2 = """SELECT * FROM policies WHERE mobile=""" + str(mobile) + """ AND selection=55"""
                mycursor2.execute(sql2)
                myresult2 = mycursor2.fetchall()   
                mysqldb.close()                
                for pol in myresult2:
                    pol_no = pol[1]
                    pol_year = pol[2]   
                print(pol_no,"/",pol_year)    
            selection = 34            
        if menu_nb == 301:
            cpr_id = request.form.get('Body')            
            try:
                get_policy_details_cpr(cpr_id,mobile)  
                selection = 119
            except:
                resp.message('The provided CPR/CR number cannot be found! Please try again with another CPR/CR number or type *M* to return to main menu:')  
        if menu_nb == 3001:
            cpr_id = unidecode(u''.join(request.form.get('Body')))
            try:
                get_policy_details_cpr(cpr_id,mobile)  
                selection = 1199
            except:
                resp.message("""الرقم الشخصي المعطى غير موجود. الرجاء المعاودة بإدخال رقم شخصي آخر أو أدخل "ر" للرجوع إلى القائمة الرئيسية:""")  

        if ((menu_nb == 802) | (menu_nb == 8002)):
            if menu_nb == 802:
                reg_no = request.form.get('Body')  
            else:
                reg_no = unidecode(u''.join(request.form.get('Body')))
            if str(reg_no) == "":
                if menu_nb == 802:
                    resp.message("""Your input format is not supported! Please provide your response in clear text composed of alapha numeric format only.""")
                else:
                    resp.message("""إنَ صيغة جوابك غير مدعومة! الرجاء إدخال أحرف و أرقام فقط.""") 
            (pol_no,pol_year) = policy(whatsappNB)
            time_tuple = time.localtime()
            ts = time.strftime("%Y-%m-%d",time_tuple)
            mysqldb = mydb()
            mycursor1 = mysqldb.cursor()
            sql1 = """INSERT INTO registration (mobile, pol_no, pol_year, media, reg_no, timestamp) VALUES (%s, %s, %s, %s, %s, %s)"""        
            rec = (mobile, pol_no, pol_year, '', reg_no, ts)
            mycursor1.execute(sql1, rec)
            mysqldb.commit()
            mysqldb.close()
            if menu_nb == 802:
                selection = 50
            else:
                selection = 500          
        if ((menu_nb == 852) | (menu_nb == 8502)):
            numMedia = int(request.form.get('NumMedia'))
            if int(numMedia) != 0:   
                (pol_no,pol_year) = policy(whatsappNB) 
                reg_no = fetch_reg_no(whatsappNB)  
                time_tuple = time.localtime()
                ts = time.strftime("%Y-%m-%d",time_tuple)
                i = 0        
                for i in range(numMedia):
                    mediaUrl = request.form.get('MediaUrl' + str(i))
                    contentType = request.form.get('MediaContentType' + str(i))
                    ext = (contentType.split('/'))[1]
                    path = os.path.split(urlparse(mediaUrl).path)
                    fileName = path[1]
                    fetch = requests.get(mediaUrl, allow_redirects=True)
                    open('./docs/' + fileName + '.' + ext, 'wb').write(fetch.content)
                    mysqldb = mydb()
                    mycursor = mysqldb.cursor()
                    sql = """INSERT INTO registration (mobile, pol_no, pol_year, media, reg_no, timestamp) VALUES (%s, %s, %s, %s, %s, %s)"""
                    rec = (mobile, pol_no, pol_year, fileName + '.' + ext, reg_no, ts)
                    mycursor.execute(sql, rec)
                    mysqldb.commit()      
                    mysqldb.close()
                if menu_nb == 852:
                    selection = 10
                else:
                    selection = 100                    
            else:
                if menu_nb == 852:
                    resp.message("you haven't uploaded correctly an image for your ownership card. Please try again!")  
                else:
                    resp.message("""لم تقم بتحميل نسخة من بطاقة الملكية بالشكل الصحيح. الرجاء المحاولة من جديد!""") 
        if ((menu_nb == 862) | (menu_nb ==8602)):
            update_db(whatsappNB, menu_nb)
            numMedia = int(request.form.get('NumMedia'))
            if int(numMedia) != 0:   
                (pol_no,pol_year) = policy(whatsappNB) 
                reg_no = fetch_reg_no(whatsappNB)  
                time_tuple = time.localtime()
                ts = time.strftime("%Y-%m-%d",time_tuple)
                i = 0        
                for i in range(numMedia):
                    mediaUrl = request.form.get('MediaUrl' + str(i))
                    contentType = request.form.get('MediaContentType' + str(i))
                    ext = (contentType.split('/'))[1]
                    path = os.path.split(urlparse(mediaUrl).path)
                    fileName = path[1]
                    fetch = requests.get(mediaUrl, allow_redirects=True)
                    open('./docs/' + fileName + '.' + ext, 'wb').write(fetch.content)
                    mysqldb = mydb()
                    mycursor = mysqldb.cursor()
                    sql = """INSERT INTO registration (mobile, pol_no, pol_year, media, reg_no, timestamp) VALUES (%s, %s, %s, %s, %s, %s)"""
                    rec = (mobile, pol_no, pol_year, fileName + '.' + ext, reg_no, ts)
                    mycursor.execute(sql, rec)
                    mysqldb.commit()      
                    mysqldb.close()
                if menu_nb == 862:                              
                    selection = 38
                else:                 
                    selection = 398
            else:
                if menu_nb == 862:
                    resp.message("you haven't uploaded correctly an image for your ownership card. Please try again!")  
                else:
                    resp.message("""لم تقم بتحميل نسخة من بطاقة الملكية بالشكل الصحيح. الرجاء المحاولة من جديد!""")             
        if menu_nb == 498:
            registration = request.form.get('Body')  
            (pol_no,pol_year) = policy(whatsappNB)                        
            mysqldb = mydb()
            mycursor1 = mysqldb.cursor()     
            sql1 = """UPDATE tba SET registration=""" + str(registration) + """ WHERE pol_no=""" + str(pol_no) + """ AND pol_year=""" + str(pol_year)
            mycursor1.execute(sql1)
            mysqldb.commit()
            mysqldb.close()
            mysqldb = mydb()
            mycursor2 = mysqldb.cursor()  
            sql2 = """SELECT * FROM policies WHERE pol_no=""" + str(pol_no) + """ AND pol_year=""" + str(pol_year)
            mycursor2.execute(sql2)
            myresult2 = mycursor2.fetchall()
            mysqldb.close()
            for pol in myresult2:
                final_tot_amt = pol[4]
            resp.message(menu_500(final_tot_amt,pol_no,pol_year))            
            update_db(whatsappNB, 500)
        if menu_nb == 4971:
            registration = unidecode(u''.join(request.form.get('Body')))
            (pol_no,pol_year) = policy(whatsappNB)
            mysqldb = mydb()
            mycursor1 = mysqldb.cursor()     
            sql1 = """UPDATE tba SET registration=""" + str(registration) + """ WHERE pol_no=""" + str(pol_no) + """ AND pol_year=""" + str(pol_year)
            mycursor1.execute(sql1)
            mysqldb.commit()
            mysqldb.close()
            mysqldb = mydb()
            mycursor2 = mysqldb.cursor()  
            sql2 = """SELECT * FROM policies WHERE pol_no=""" + str(pol_no) + """ AND pol_year=""" + str(pol_year)
            mycursor2.execute(sql2)
            myresult2 = mycursor2.fetchall()
            mysqldb.close()
            for pol in myresult2:
                final_tot_amt = pol[4]
            resp.message(menu_5000(final_tot_amt,pol_no,pol_year))            
            update_db(whatsappNB, 5000)            
            
        x = menu_level(int(selection) + menu_nb)              
        
    if menu_nb == 0:  
        insert_db(whatsappNB,100)
        resp.message(menu_100())   
    elif x == 100:                  # Main Menu - English
        update_db(whatsappNB, x)
        resp.message(menu_100())
    elif x == 104:                  # New Motor Policy - English
        update_db(whatsappNB, x)
        resp.message(menu_104())        
    elif x == 105:                  # Register Claim - English
        update_db(whatsappNB, x)
        resp.message(menu_105())        
    elif x == 1000:                 # Main Menu - Arabic
        update_db(whatsappNB, x)
        resp.message(menu_1000())   
    elif x == 1004:                  # New Motor Policy - Arabic
        update_db(whatsappNB, x)
        resp.message(menu_1004())        
    elif x == 1005:                  # Register Claim - Arabic
        update_db(whatsappNB, x)
        resp.message(menu_1005())                
    elif x == 210:                  # General Inquiry - English
         update_db(whatsappNB, x)
         resp.message(menu_210()) 
    elif x == 2100:                 # General Inquiry - Arabic 
         update_db(whatsappNB, x)
         resp.message(menu_2100())          
    elif x == 212:                  # Individual Products - English
         update_db(whatsappNB, x)
         resp.message(menu_212()) 
    elif x == 2102:                  # Individual Products - Arabic
         update_db(whatsappNB, x)
         resp.message(menu_2102())          
    elif x == 213:                  # Request - English
         update_db(whatsappNB, x)
         resp.message(menu_213()) 
    elif x == 2103:                  # Request - Arabic
         update_db(whatsappNB, x)
         resp.message(menu_2103())          
    elif x == 214:                  # Complaint - English
         update_db(whatsappNB, x)
         resp.message(menu_214())   
    elif x == 2104:                  # Complaint - Arabic
         update_db(whatsappNB, x)
         resp.message(menu_2104())            
    elif x == 215:                  # Useful Contacts - English
         update_db(whatsappNB, x)
         resp.message(menu_215())        
    elif x == 2105:                  # Useful Contacts - Arabic
         update_db(whatsappNB, x)
         resp.message(menu_2105())          
    elif x == 250:                  # Useful Contacts - English
         update_db(whatsappNB, x)
         resp.message(menu_250())        
    elif x == 2500:                  # Useful Contacts - Arabic
         update_db(whatsappNB, x)
         resp.message(menu_2500())              
    elif x == 270:                  # Useful Contacts - English
         update_db(whatsappNB, x)
         resp.message(menu_270())        
    elif x == 2700:                  # Useful Contacts - Arabic
         update_db(whatsappNB, x)
         resp.message(menu_2700())   
    elif x == 280:                  # Useful Contacts - English
         update_db(whatsappNB, x)
         resp.message(menu_280())        
    elif x == 2800:                  # Useful Contacts - Arabic
         update_db(whatsappNB, x)
         resp.message(menu_2800())   
    elif x == 290:                  # Useful Contacts - English
         update_db(whatsappNB, x)
         resp.message(menu_290())        
    elif x == 2900:                  # Useful Contacts - Arabic
         update_db(whatsappNB, x)
         resp.message(menu_2900())   
    elif x == 220:
         update_db(whatsappNB, x)
         mobile = (whatsappNB.split("whatsapp:+973"))[1] 

         mysqldb = mydb()
         mycursor = mysqldb.cursor()
         sql = """SELECT * FROM pol_details WHERE mobile=""" + str(mobile)
         mycursor.execute(sql)
         check220 = mycursor.fetchall()
         mysqldb.close()
         if check220 == []:
            try:
                get_policy_details(mobile)           
            except:
                print("No active policies found")
         resp.message(menu_220(mobile))            
    elif x == 2200:
         update_db(whatsappNB, x)
         mobile = (whatsappNB.split("whatsapp:+973"))[1]
         
         mysqldb = mydb()
         mycursor = mysqldb.cursor()
         sql = """SELECT * FROM pol_details WHERE mobile=""" + str(mobile)
         mycursor.execute(sql)
         check2200 = mycursor.fetchall()
         mysqldb.close()
         if check2200 == []:
            try:
                get_policy_details(mobile)           
            except:
                print("No active policies found")
         resp.message(menu_2200(mobile))                 
    elif ((x == 720) | (x == 7200)):
         update_db(whatsappNB, x)
         mobile = (whatsappNB.split("whatsapp:+973"))[1]
         get_policy_details(mobile)           
         if x == 720:
            resp.message(menu_720(mobile)) 
         else:
            resp.message(menu_7200(mobile))   
    elif x == 852:
        update_db(whatsappNB, x)
        resp.message(menu_852()) 
    elif x == 8502:
        update_db(whatsappNB, x)
        resp.message(menu_8502())                  
    elif x == 862:
        update_db(whatsappNB, x)
        resp.message(menu_862()) 
    elif x == 8602:
        update_db(whatsappNB, x)
        resp.message(menu_8602())                    
    elif x == 300:
         update_db(whatsappNB, x)           
         resp.message(menu_300()) 
         pollog = open("C://inetpub//wwwroot//renewalBot//"+mobile+"-policy.log", "w+")
         pollog.write('0')
         pollog.close()
    elif x == 3000:
         update_db(whatsappNB, x)           
         resp.message(menu_3000()) 
         pollog = open("C://inetpub//wwwroot//renewalBot//"+mobile+"-policy.log", "w+")
         pollog.write('0')
         pollog.close()         
    elif x == 301:
         update_db(whatsappNB, x)           
         resp.message(menu_301())      
    elif x == 3001:
         update_db(whatsappNB, x)           
         resp.message(menu_3001())             
    elif x == 330:
         update_db(whatsappNB, x)
         (pol_no,pol_year) = policy(whatsappNB)
         resp.message(menu_330(pol_no,pol_year))
    elif x == 3300:
         update_db(whatsappNB, x)
         (pol_no,pol_year) = policy(whatsappNB)
         resp.message(menu_3300(pol_no,pol_year))   
    elif ((x == 802) | (x == 8002)):
         update_db(whatsappNB, x) 
         if x == 802:
            resp.message(menu_802())   
         else:
            resp.message(menu_8002())             
    elif ((x == 830) | (x == 8300)):
         update_db(whatsappNB, x)
         (pol_no,pol_year) = policy(whatsappNB)
         if x == 830:
            resp.message(menu_830(pol_no,pol_year))
         else:
            resp.message(menu_8300(pol_no,pol_year))  
    elif ((x == 900) | (x == 9000)):
         update_db(whatsappNB, x)
         (pol_no,pol_year) = policy(whatsappNB)
         if x == 900:
            resp.message(menu_900(pol_no,pol_year))
         else:
            resp.message(menu_9000(pol_no,pol_year))            
    elif x == 420:
         update_db(whatsappNB, x)             
         mobile = (whatsappNB.split("whatsapp:+973"))[1]    
         mysqldb = mydb()
         mycursor = mysqldb.cursor()
         sql = """SELECT * FROM pol_details WHERE mobile=""" + str(mobile)
         mycursor.execute(sql)
         check420 = mycursor.fetchall()
         mysqldb.close()         
         if check420 == []:
            print("No active policies found")
         resp.message(menu_420(mobile))                     
    elif x == 4200:
         update_db(whatsappNB, x)             
         mobile = (whatsappNB.split("whatsapp:+973"))[1]         
         mysqldb = mydb()
         mycursor = mysqldb.cursor()
         sql = """SELECT * FROM pol_details WHERE mobile=""" + str(mobile)
         mycursor.execute(sql)
         check4200 = mycursor.fetchall()
         mysqldb.close()
         if check4200 == []:
            print("No active policies found")
         resp.message(menu_4200(mobile))                              
    elif x == 450:
         update_db(whatsappNB, x)  
         (pol_no,pol_year) = policy(whatsappNB)
         (msgtext450,final_tot_amt) = menu_450(pol_no,pol_year)
         if msgtext450 == "NEXIST":
            update_db(whatsappNB, 300) 
            pollog = open("C://inetpub//wwwroot//renewalBot//"+mobile+"-policy.log", "w+")
            pollog.write('0')
            pollog.close()            
            msgtext450 = """One of the entered policy details is wrong. Please try again with the correct policy year and number.
Please type your motor policy details as follows:
    
*1. Year of Policy (4-digits):*"""            
         else:
             time_tuple = time.localtime()
             ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
             mysqldb = mydb()
             mycursor = mysqldb.cursor()
             sql = """UPDATE policies SET renewal_prem=""" + str(final_tot_amt) + """, timestamp=STR_TO_DATE('""" + str(ts) + """','%Y-%m-%d %H:%i:%s') WHERE pol_no=""" + str(pol_no) + """ AND pol_year=""" + str(pol_year)
             mycursor.execute(sql)
             mysqldb.commit()
             mysqldb.close()
         resp.message(msgtext450)
    elif x == 4500:
         update_db(whatsappNB, x)  
         (pol_no,pol_year) = policy(whatsappNB)
         (msgtext4500,final_tot_amt) = menu_4500(pol_no,pol_year)
         if msgtext4500 == "NEXIST":
            update_db(whatsappNB, 3000) 
            pollog = open("C://inetpub//wwwroot//renewalBot//"+mobile+"-policy.log", "w+")
            pollog.write('0')
            pollog.close()            
            msgtext4500 = """أحد التفاصيل التي تم إدخالها خاطئة. يرجى المحاولة مرة أخرى بإدخال سنة الوثيقة الصحيحة ورقمها.
يرجى كتابة تفاصيل وثيقة التأمين الخاصة بك على النحو التالي:
    
*١. سنة إصدار الوثيقة (4-أرقام):*"""            
         else:
             time_tuple = time.localtime()
             ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
             mysqldb = mydb()
             mycursor = mysqldb.cursor()
             sql = """UPDATE policies SET renewal_prem=""" + str(final_tot_amt) + """, timestamp=STR_TO_DATE('""" + str(ts) + """','%Y-%m-%d %H:%i:%s') WHERE pol_no=""" + str(pol_no) + """ AND pol_year=""" + str(pol_year)
             mycursor.execute(sql)
             mysqldb.commit()
             mysqldb.close()             
         resp.message(msgtext4500)         
    elif x == 480:
         update_db(whatsappNB, x)   
         (pol_no,pol_year) = policy(whatsappNB)
         msgtext480 = menu_480(pol_no,pol_year)
         if msgtext480 == "NEXIST":
            update_db(whatsappNB, 300) 
            pollog = open("C://inetpub//wwwroot//renewalBot//"+mobile+"-policy.log", "w+")
            pollog.write('0')
            pollog.close()            
            msgtext480 = """One of the entered policy details is wrong. Please try again with the correct policy year and number.
Please type your motor policy details as follows:
    
*1. Year of Policy (4-digits):*"""         
         resp.message(msgtext480)
    elif x == 4800:
         update_db(whatsappNB, x)   
         (pol_no,pol_year) = policy(whatsappNB)
         msgtext4800 = menu_4800(pol_no,pol_year)
         if msgtext4800 == "NEXIST":
            update_db(whatsappNB, 3000) 
            pollog = open("C://inetpub//wwwroot//renewalBot//"+mobile+"-policy.log", "w+")
            pollog.write('0')
            pollog.close()            
            msgtext4800 = """أحد التفاصيل التي تم إدخالها خاطئة. يرجى المحاولة مرة أخرى بإدخال سنة الوثيقة الصحيحة ورقمها.
يرجى كتابة تفاصيل وثيقة التأمين الخاصة بك على النحو التالي:
    
*١. سنة إصدار الوثيقة (4-أرقام):*"""         
         resp.message(msgtext4800)         
    elif x == 498:
        resp.message(menu_498())
        update_db(whatsappNB, 498)
    elif x == 4971:
        resp.message(menu_4971())
        update_db(whatsappNB, 4971)        
    elif x == 499:
        (pol_no,pol_year) = policy(whatsappNB)
        menu_499(pol_no,pol_year)          
        mysqldb = mydb()
        mycursor = mysqldb.cursor()
        sql = """SELECT * FROM policies WHERE pol_no=""" + str(pol_no) + """ AND pol_year=""" + str(pol_Year)
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        mysqldb.close()
        for pol in myresult:
            final_tot_amt = pol[4]
        resp.message(menu_500(final_tot_amt,pol_no,pol_year))            
        update_db(whatsappNB, 500)
    elif x == 4972:
        (pol_no,pol_year) = policy(whatsappNB)
        menu_499(pol_no,pol_year)  
        mysqldb = mydb()
        mycursor = mysqldb.cursor()
        sql = """SELECT * FROM policies WHERE pol_no=""" + str(pol_no) + """ AND pol_year=""" + str(pol_Year)
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        mysqldb.close()
        for pol in myresult:
            final_tot_amt = pol[4]
        resp.message(menu_5000(final_tot_amt,pol_no,pol_year))            
        update_db(whatsappNB, 5000)        
    elif x == 500:               
         (pol_no,pol_year) = policy(whatsappNB)
         mysqldb = mydb()
         mycursor1 = mysqldb.cursor()
         sql1 = """SELECT * FROM tba WHERE pol_no=""" + str(pol_no) + """ AND pol_year=""" + str(pol_year)
         mycursor1.execute(sql1)
         myresult1 = mycursor1.fetchall()            
         print("Testing for TBA")
         if myresult1 != []:
             for pol in myresult1:
                 if pol[2] == 'TBA':
                     print("TBA Found")
                     update_db(whatsappNB, 497)
                     resp.message(menu_497())   
                 else:
                     update_db(whatsappNB, x)
                     mycursor2 = mysqldb.cursor()
                     sql2 = """SELECT * FROM policies WHERE pol_no=""" + str(pol_no) + """ AND pol_year=""" + str(pol_year)
                     mycursor2.execute(sql2)
                     myresult2 = mycursor2.fetchall()   
                     mysqldb.close()
                     for pol in myresult2:
                         final_tot_amt = pol[4]
                     resp.message(menu_500(final_tot_amt,pol_no,pol_year))  
         else:
             tba = None
             print("Plate registration no. is okay")
             update_db(whatsappNB, x)
             mysqldb = mydb()
             mycursor3 = mysqldb.cursor()
             sql3 = """SELECT * FROM policies WHERE pol_no=""" + str(pol_no) + """ AND pol_year=""" + str(pol_year)
             mycursor3.execute(sql3)
             myresult3 = mycursor3.fetchall()                        
             for pol in myresult3:
                 final_tot_amt = pol[4]
             resp.message(menu_500(final_tot_amt,pol_no,pol_year))      
    elif x == 5000:               
         (pol_no,pol_year) = policy(whatsappNB)
         mysqldb = mydb()
         mycursor1 = mysqldb.cursor()
         sql1 = """SELECT * FROM tba WHERE pol_no=""" + str(pol_no) + """ AND pol_year=""" + str(pol_year)
         mycursor1.execute(sql1)
         myresult1 = mycursor1.fetchall()            
         print("Testing for TBA")
         if myresult1 != []:
             for pol in myresult1:
                 if pol[2] == 'TBA':
                     print("TBA Found")
                     update_db(whatsappNB, 4970)
                     resp.message(menu_4970())   
                 else:
                     update_db(whatsappNB, x)
                     mycursor2 = mysqldb.cursor()
                     sql2 = """SELECT * FROM policies WHERE pol_no=""" + str(pol_no) + """ AND pol_year=""" + str(pol_year)
                     mycursor2.execute(sql2)
                     myresult2 = mycursor2.fetchall()   
                     mysqldb.close()
                     for pol in myresult2:
                         final_tot_amt = pol[4]
                     resp.message(menu_5000(final_tot_amt,pol_no,pol_year))  
         else:
             tba = None
             print("Plate registration no. is okay")
             update_db(whatsappNB, x)
             mysqldb = mydb()
             mycursor3 = mysqldb.cursor()
             sql3 = """SELECT * FROM policies WHERE pol_no=""" + str(pol_no) + """ AND pol_year=""" + str(pol_year)
             mycursor3.execute(sql3)
             myresult3 = mycursor3.fetchall()                        
             for pol in myresult3:
                 final_tot_amt = pol[4]
             resp.message(menu_5000(final_tot_amt,pol_no,pol_year))               
    elif x == 600:
         update_db(whatsappNB, x)
         resp.message(menu_600())
    elif x == 6000:
         update_db(whatsappNB, x)
         resp.message(menu_6000())         
    elif x == 601:
         update_db(whatsappNB, x)
         resp.message(menu_601())
    elif x == 6001:
         update_db(whatsappNB, x)
         resp.message(menu_6001())         
    elif x == 602:
         update_db(whatsappNB, x)
         resp.message(menu_602())
    elif x == 6002:
         update_db(whatsappNB, x)
         resp.message(menu_6002())         
    elif x == 603:
         update_db(whatsappNB, x)
         resp.message(menu_603())
    elif x == 6003:
         update_db(whatsappNB, x)
         resp.message(menu_6003())         
    elif x == 604:
         update_db(whatsappNB, x)
         resp.message(menu_604())
    elif x == 6004:
         update_db(whatsappNB, x)
         resp.message(menu_6004())         
    elif x == 605:
         update_db(whatsappNB, x)
         resp.message(menu_605())     
    elif x == 6005:
         update_db(whatsappNB, x)
         resp.message(menu_6005())              
         
    return str(resp)    
    
    if x == 300:
       pol_year = request.form.get('Body')
       resp.message('*2. Policy No.:*')       
       
       pol_no = request.form.get('Body')
       mobile = (whatsappNB.split("whatsapp:+973"))[1]       
       time_tuple = time.localtime()
       ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
       mysqldb = mydb()
       mycursor = mysqldb.cursor()       
       sql = """INSERT INTO policies (mobile, pol_no, pol_year, exp_date, renewal_prem, selection, timestamp) VALUES (%s, %s, %s, STR_TO_DATE(%s,'%d/%m/%Y'), %s, %s, %s)"""
       rec = (mobile, pol_no, pol_year, '01/01/1900', 0, 555, ts)
       mycursor.execute()
       mysqldb.commit()
       mysqldb.close()
       
    if x == 3000:
       pol_year = unidecode(u''.join(request.form.get('Body')))
       resp.message('*٢. رقم الوثيقة:*')
       
       pol_no = request.form.get('Body')
       mobile = (whatsappNB.split("whatsapp:+973"))[1]
       time_tuple = time.localtime()
       ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
       mysqldb = mydb()
       mycursor = mysqldb.cursor()       
       sql = """INSERT INTO policies (mobile, pol_no, pol_year, exp_date, renewal_prem, selection, timestamp) VALUES (%s, %s, %s, STR_TO_DATE(%s,'%d/%m/%Y'), %s, %s, %s)"""
       rec = (mobile, pol_no, pol_year, '01/01/1900', 0, 555, ts)
       mycursor.execute()
       mysqldb.commit()
       mysqldb.close()                     

if __name__ == '__main__':
    app.run(debug=True)
