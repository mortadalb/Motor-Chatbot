#!/usr/bin/python
# coding=utf-8

import sys
import os
import cx_Oracle
import json
import jwt
import time
import datetime
from os.path import basename
from functools import wraps
from flask import Flask, jsonify, request, make_response
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
from datetime import datetime, timedelta
from WEB_INSERT_DIRECT_AMAN import insert_endt_web, renew_by_pol, change_registration
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from pdfgen import generateDnPdf, generateShedPdf
from smtplib import SMTP  
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import COMMASPACE, formatdate
from shutil import copyfile
import mysql.connector

app = Flask(__name__)
app.config['SECRET_KEY'] = "XXXXXXXXX"
api = Api(app)
auth = HTTPBasicAuth()

all_keys = open('twiliokeys', 'r').read().splitlines()
account_sid = all_keys[0].split('=')[1]
auth_token  = all_keys[1].split('=')[1]

client = Client(account_sid, auth_token)

def mydb():
    mysqldb = mysql.connector.connect(
        host = "server-00616",
        port = 3305,
        user = "chatbot",
        passwd = "XXXXXXX",
        database = "quotations",
        auth_plugin='mysql_native_password')
    return mysqldb

def email(subject, destination, message):
    text_subtype = 'plain'
    content =       message
    title =         subject
    SMTPserver =    'XX.XX.XX.XX'
    sender =        'ithelpdesk@company.c0m'
    to_party =      destination
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

def send_mail(subject, text, files=None):
    To =            'motor@company.c0m'
    Cc =            'aman.admin@company.c0m'
    SMTPserver =    'XX.XX.XX.XX'
    Sender =        'ithelpdesk@company.c0m'
    msg = MIMEMultipart()
    msg['From'] = Sender
    msg['To'] =   To
    msg['Cc'] =   Cc
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(text))
    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        msg.attach(part)
    smtp = SMTP(SMTPserver)
    smtp.sendmail(Sender, [To, Cc], msg.as_string())
    smtp.close()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token') 
        if not token:
            return jsonify({'message' : 'Token is missing!'}), 403
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
        except:
            return jsonify({'message' : 'Token is invalid!'}), 403
        
        return f(*args, **kwargs)
    return decorated

@app.route('/login')  
def login():
    auth = request.authorization
    if auth and auth.username == 'admin' and auth.password == 'XXXXXXXXX':
        token = jwt.encode({'user' : auth.username, 'exp' : datetime.utcnow() + timedelta(minutes=30)}, app.config['SECRET_KEY'])
        # https://jwt.io 
        return jsonify({'token' : token.decode('UTF-8')})
    return make_response('Could not verify!', 401, {'WWW-Authenticate' : 'Basic realm="Login Required"'})

def status(branch,endt_no,endt_year,endt_type,class_of_business,office): 
    con = cx_Oracle.connect('GENCDE/XXXXXXX@XX.XX.XX.XX/amandb')
    cur = con.cursor()
    p_branch =              branch              
    p_endt_no =             endt_no             
    p_endt_year =           endt_year           
    p_endt_type =           endt_type           
    p_class_of_business =   class_of_business   
    p_office =              office              
    p_egov_flag =           cur.var(int)
    p_egov_status =         cur.var(str)    
    result = cur.callproc('WEB_INSERT_DIRECT_AMAN.get_egov_status',
        [p_branch, 
        p_office, 
        p_endt_no, 
        p_endt_year, 
        p_endt_type,
        p_class_of_business,
        p_egov_flag,
       p_egov_status])        
    return tuple(result)    
    cur.close()
    con.close()

class HelloWorld(Resource):
    def get(self):
        return {"about":"Chatbot Web Service!"}

class Test(Resource):
    @token_required
    def get(self):
        return {"test":"Chatbot Web Service!"}

class Payment_Status(Resource):
    @token_required
    def post(self):
        params = [0,0,0,0]
        parameters = request.get_json()
        json_data = json.loads(json.dumps(parameters))
        params[0] = json_data["parameters"]["policy_no"]
        params[1] = json_data["parameters"]["policy_year"]
        params[2] = json_data["parameters"]["pay_status"] 
        params[3] = json_data["parameters"]["order_id"]
        
        if 'REGISTR' in params[3]:
            mysqldb = mydb()
            mycursor1 = mysqldb.cursor()                
            sql1 = """SELECT * FROM pol_details 
                       WHERE policy_no= """ + str(params[0]) + """
                         AND policy_year= """ + str(params[1])                                     
            mycursor1.execute(sql1)            
            myresult1 = mycursor1.fetchall()
            mysqldb.close()
            
            for policy in myresult1:
                policy_type =       policy[19]
                exp_date =          policy[14]
                client_code =       policy[12]
                client_ename =      policy[11]
                client_aname =      policy[11]
                insured_ename =     policy[11]
                agent_no =          policy[17]
                agent_name =        policy[33]
                comm =              policy[18]
                comm_amount =       0
                vehicle_make =      policy[20]
                vehicle_model =     policy[21]
                type_of_body =      policy[22]
                plate_type =        policy[23]
                class_of_use =      policy[24]
                year_of_make =      policy[26]
                seating_capacity =  policy[27]
                chassis_no =        policy[28]
                change_remarks =    'Online registration no. change'
                engine_capacity =   policy[29]
                agency_repair =     policy[30]
                driver_name =       policy[11]
                pol_no =            policy[5]
                pol_year =          policy[6]
                cust_no =           policy[12]
                rsa_provider =      policy[31]
                tariff =            policy[32]
                mobile =            policy[16]

            mysqldb = mydb()
            mycursor2 = mysqldb.cursor()
            sql2 = """SELECT mobile,menu FROM chatbot WHERE mobile='whatsapp:+973""" + str(mobile) + """'"""
            mycursor2.execute(sql2)
            myresult2 = mycursor2.fetchall()
            mysqldb.close()
            
            menu = myresult2[0][1]         
            print("menu: ",menu)            
            
            mysqldb = mydb()
            mycursor3 = mysqldb.cursor()
            sql3 = """SELECT DISTINCT reg_no FROM registration 
                       WHERE pol_no= """ + str(params[0]) + """
                         AND pol_year= """ + str(params[1])
            mycursor3.execute(sql3)
            myresult3 = mycursor3.fetchall()
            mysqldb.close()
            
            for reg in myresult3:
                reg_no =       reg[0]
            
            try:
                change_registration(policy_type,
                                    exp_date,
                                    client_code,
                                    client_ename,
                                    client_aname,
                                    insured_ename,
                                    agent_no,
                                    agent_name,
                                    comm,
                                    comm_amount,
                                    vehicle_make,
                                    vehicle_model,
                                    type_of_body,
                                    plate_type,
                                    class_of_use,
                                    reg_no,
                                    year_of_make,
                                    seating_capacity,
                                    chassis_no,
                                    change_remarks,
                                    engine_capacity,
                                    agency_repair,
                                    driver_name,
                                    pol_no,
                                    pol_year,
                                    cust_no,
                                    rsa_provider,
                                    tariff)
                
                mysqldb = mydb()                   
                mycursor4 = mysqldb.cursor()    
                sql4 = """SELECT media FROM registration 
                           WHERE reg_no= """ + str(reg_no) + """
                             AND pol_no= """ + str(params[0]) + """
                             AND pol_year= """ + str(params[1])
                             
                mycursor4.execute(sql4)
                myresult4 = mycursor4.fetchall()
                mysqldb.close()
                attachments = []
                for media in myresult4:
                    if str(media[0]) != '':
                        attachments.append('./renewalBot/docs/' + str(media[0]))
                message = """Dear Motor dept.,
                
The ownership card copies are attached for your reference. Please post the concerned policy to eGov.

Regards,
Chatbot"""
                send_mail("[Chatbot Registration] Registration No. Change for Policy " + str(pol_no) + '/' + str(pol_year), message, attachments)  
                mysqldb = mydb()
                mycursor5 = mysqldb.cursor()
                sql5 = """SELECT * FROM schedule 
                           WHERE pol_no= """ + str(params[0]) + """
                             AND pol_year= """ + str(params[1]) + """
                             AND ENDT_TYPE=2 """
                         
                mycursor5.execute(sql5)
                myresult5 = mycursor5.fetchall()
                mysqldb.close()
                
                for schedule in myresult5:
                    client_name =       insured_ename
                    issue_dt =          str(schedule[15])
                    xxxxx_vat =         str(schedule[39])
                    address =           str(schedule[17])
                    voh_no =            str(schedule[33])
                    broker =            str(schedule[10])
                    cust_no =           str(schedule[37])
                    cust_vat =          str(schedule[46])
                    pol_year =          schedule[9]
                    pol_no =            schedule[8]
                    endt_no =           schedule[5]
                    endt_year =         schedule[6]
                    pol_type =          str(schedule[12])
                    eff_dt =            str(schedule[13])
                    exp_dt =            str(schedule[14])
                    registration =      schedule[20]
                    make =              str(schedule[18])
                    model =             str(schedule[19])
                    body_type =         str(schedule[38])
                    chassis_no =        str(schedule[21])
                    rsa =               str(schedule[44])
                    total_prem =        str(schedule[40])
                    vat_pct =           str(schedule[41])
                    vat_amt =           str(schedule[42])
                    final_tot =         str(schedule[43])
                    
                try:    
                    generateDnPdf('dn_add.html','prints/Tax_Invoice-'+str(params[0])+'-'+str(params[1])+'.pdf',{"name":                  client_name,
                                                                                                                "date":                  datetime.strptime(((issue_dt.__str__()).split(" "))[0], '%Y-%m-%d').strftime('%d/%m/%Y'),
                                                                                                                "xxxxx_vat":             xxxxx_vat,            
                                                                                                                "address":               address,
                                                                                                                "voucher_no":            voh_no,                 
                                                                                                                "broker":                broker,
                                                                                                                "account_no":            "10027601000000",       
                                                                                                                "customer_id":           cust_no,
                                                                                                                "customer_vat":          cust_vat,      
                                                                                                                "policy_number":         "BAH/MOT/"+str(pol_year)[-2:]+"/"+str(pol_no),
                                                                                                                "endorsement_year":      "BAH/MOT/"+str(endt_year)[-2:]+"/"+str(endt_no),
                                                                                                                "policy_type":           pol_type,
                                                                                                                "from_date":             datetime.strptime(((eff_dt.__str__()).split(" "))[0], '%Y-%m-%d').strftime('%d/%m/%Y'),
                                                                                                                "to_date":               datetime.strptime(((exp_dt.__str__()).split(" "))[0], '%Y-%m-%d').strftime('%d/%m/%Y'),
                                                                                                                "registeration_no":      registration,
                                                                                                                "vehicle_type":          body_type,
                                                                                                                "make":                  make+" - "+model,
                                                                                                                "chassis":               chassis_no,
                                                                                                                "rsa":                   rsa,    
                                                                                                                "total_before_vat":      '1',
                                                                                                                "vat_percentage":        vat_pct,
                                                                                                                "total_after_vat":       '0.050',
                                                                                                                "total_due":             '1.050',
                                                                                                                "amount_in_words":       "One Bahraini Dinar", 
                                                                                                                "printed_by":            "webadmin"})
                except:
                    print('Ok')
                
                try:
                    if int(menu) == 900:                
                        message = client.messages.create(
                                          body="""Thank you for your payment. Your vehicle registration no. under policy *""" + str(params[0]) + """/""" + str(params[1]) + """* has been successfully changed to """ + str(reg_no) + """. Your tax invoice is attached below. Please type *M* to return back to main Menu or *Q* to quit.""",
                                          from_='whatsapp:+1xxxxxxxxxxx',
                                          to='whatsapp:+973' + str(mobile))

                        invoice = client.messages.create(                                  
                                          body="Tax_Invoice-" + str(params[0]) + """-""" + str(params[1]) + ".pdf",
                                          media_url="""https://xxxxxx.ngrok.io/prints/Tax_Invoice-"""+str(params[0])+"""-"""+str(params[1])+""".pdf""",
                                          from_='whatsapp:+1xxxxxxxxxxx',
                                          to='whatsapp:+973' + str(mobile))                                     
                    else:
                        contentar = """شكراً على الدفع . لقد تمَ بنجاح تغيير رقم  لوحة المركبة إلى """ + str(reg_no) + """ ضمن الوثيقة  *""" + str(params[0]) + """/""" + str(params[1]) + """*. ستجدون مرفقاً أدناه الفاتورة الضريبية. الرجاء إدخال "ر" للعودة إلى القائمة الرئيسية أو "خ" للخروج النهائي من المحادثة."""
                        thankyou = client.messages.create(                                  
                                          body=contentar.encode("utf-8") ,
                                          from_='whatsapp:+1xxxxxxxxxxx',
                                          to='whatsapp:+973' + str(mobile))           
                except:
                    print("Exception: ",message.sid)                       
            
            except:
                if int(menu) == 900:                
                    message = client.messages.create(
                                      body="""Thank you for your payment. Your request to change the vehicle registration no. under policy *""" + str(params[0]) + """/""" + str(params[1]) + """* faced an issue. The concerned business department has been notified. You can also contact our Call Center on 17561661 to resolve your issue during business days from 8 AM to 4 PM. Please type *M* to return back to main Menu or *Q* to quit.""",
                                      from_='whatsapp:+1xxxxxxxxxxx',
                                      to='whatsapp:+973' + str(mobile))
                                
                else:
                    contentar = """شكراً على الدفع . و لكن حصل خلل خلال محاولة تغيير رقم اللوحة ضمن الوثيقة *""" + str(params[0]) + """/""" + str(params[1]) + """* كما يمكنك الإتصال على 17561661 خلال أوقات العمل من 8 صباحاً و لغاية 4 مساءً لأجل مساعدتكم. الرجاء إدخال "ر" للعودة إلى القائمة الرئيسية أو "خ" للخروج النهائي من المحادثة ."""
                    thankyou = client.messages.create(                                  
                                      body=contentar.encode("utf-8") ,
                                      from_='whatsapp:+1xxxxxxxxxxx',
                                      to='whatsapp:+973' + str(mobile))                             
                
        elif (('WHATSAPP' in params[3]) | ('SMS' in params[3])):
            try:
                mysqldb = mydb()
                mycursor = mysqldb.cursor()
                sql1 = """SELECT mobile 
                            FROM policies 
                           WHERE pol_no=""" + str(params[0]) + """
                             AND pol_year=""" + str(params[1])
                mycursor.execute(sql1)   
                result1 = mycursor.fetchall()             
                mysqldb.close()                
                for data in result1:
                    mobile = data[0]    
                print("mobile: ",mobile)           

                mysqldb = mydb()
                mycursor = mysqldb.cursor()
                sql2 = """SELECT mobile,menu FROM chatbot WHERE mobile='whatsapp:+973""" + str(mobile) + """'"""
                mycursor.execute(sql2)
                myresult2 = mycursor.fetchall()
                mysqldb.close()
                
                menu = myresult2[0][1]
                '''for menus in myresult2: 
                    mobilem = menus[0].split("whatsapp:+973")
                    if int(mobilem) == int(mobile):
                        menu = menus[1]'''            
                print("menu: ",menu)      
            
            except:
                print("Renewal by SMS 1")
            
            time_tuple = time.localtime()
            ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)            
            if params[2] == 1:
                try:
                    mysqldb = mydb()
                    mycursor = mysqldb.cursor()
                    sql3 = """INSERT INTO requests (timestamp, mobile, pol_no, pol_year, pay_status, trans_id) VALUES (%s, %s, %s, %s, %s, %s)"""
                    rec = (ts, str(mobile), int(params[0]),int(params[1]), str(params[2]), str(params[3]))
                    mycursor.execute(sql3, rec)   
                    mysqldb.commit()
                    mysqldb.close()                                      
                except:
                    print("Renewal by SMS - stage 2")
                    
                try:
                    renew_by_pol(params[0],params[1])                               
                    
                    mysqldb = mydb()
                    mycursor = mysqldb.cursor()
                    sql4 = """SELECT * FROM schedule 
                               WHERE pol_no= """ + str(params[0]) + """
                                 AND pol_year= """ + str(params[1]) + """
                                 AND ENDT_TYPE=3"""
                             
                    mycursor.execute(sql4)
                    myresult4 = mycursor.fetchall()
                    mysqldb.close()
                    
                    for schedule in myresult4:
                        client_name  =      schedule[16]
                        pol_type =          schedule[12]
                        pol_no =            str(schedule[8])
                        pol_year =          str(schedule[9])
                        eff_dt =            str(schedule[13])
                        exp_dt =            str(schedule[14])
                        registration =      str(schedule[20])
                        address =           str(schedule[17])
                        year_of_make =      str(schedule[22])
                        chassis_no =        str(schedule[21])
                        usage =             schedule[23]
                        make =              schedule[18]
                        model =             schedule[19]
                        excess =            str(schedule[27])
                        passengers =        str(schedule[24])
                        si =                str(schedule[25])
                        deductable =        str(schedule[26])
                        add_conditions =    schedule[36]
                        add_exclusions =    schedule[31]
                        accessories =       schedule[32]
                        print_dt =          str((datetime.now()).strftime("%d/%m/%Y"))
                        add_cover =         str(schedule[30])
                        issue_dt =          str(schedule[15])
                        endt_no =           schedule[5]
                        endt_year =         schedule[6]
                        voh_no =            str(schedule[33])
                        xxxxx_vat =         str(schedule[39])
                        acc_no =            str(schedule[45])
                        cust_vat =          str(schedule[46])
                        cust_no =           str(schedule[37])
                        rsa =               str(schedule[44])                           
                        body_type =         str(schedule[38])
                        broker =            str(schedule[10])
                        vat_amt =           str(schedule[42])
                        vat_pct =           str(schedule[41])
                        total_prem =        str(schedule[40])
                        final_tot =         str(schedule[43])                                                                              

                    try:
                        generateShedPdf('prints/Schedule-'+str(params[0])+'-'+str(params[1])+'.pdf',{"participant":     client_name,
                                                                                              "policy_type":            pol_type,
                                                                                              "policy_number":          "BAH/MOT/"+str(pol_year)[-2:]+"/"+str(pol_no),
                                                                                              "from_date":              datetime.strptime(((eff_dt.__str__()).split(" "))[0], '%Y-%m-%d').strftime('%d/%m/%Y'),
                                                                                              "to_date":                datetime.strptime(((exp_dt.__str__()).split(" "))[0], '%Y-%m-%d').strftime('%d/%m/%Y'),
                                                                                              "registeration_no":       registration,
                                                                                              "address":                address,
                                                                                              "make_year":              year_of_make,           
                                                                                              "chassis":                chassis_no,             
                                                                                              "usage":                  usage,                  
                                                                                              "make":                   make,                   
                                                                                              "model":                  model,                  
                                                                                              "excess":                 deductable,                 
                                                                                              "passengers":             passengers,             
                                                                                              "si":                     si,
                                                                                              "compulsory_deductible":  deductable,             
                                                                                              "additional_conditions":  add_conditions,         
                                                                                              "additional_exclusions":  add_exclusions,         
                                                                                              "accessories":            accessories,            
                                                                                              "print_date":             print_dt,
                                                                                              "additional_cover":       add_cover,              
                                                                                              "issue_date":             datetime.strptime(((issue_dt.__str__()).split(" "))[0], '%Y-%m-%d').strftime('%d/%m/%Y')})
                        copyfile('prints/Schedule-'+str(params[0])+'-'+str(params[1])+'.pdf', 'portal/storage/app/printouts')
                    except:
                        print('Next')
                    
                    try:    
                        generateDnPdf('dn_rnw.html','prints/Tax_Invoice-'+str(params[0])+'-'+str(params[1])+'.pdf',{"name":           client_name,
                                                                                               "date":                  datetime.strptime(((issue_dt.__str__()).split(" "))[0], '%Y-%m-%d').strftime('%d/%m/%Y'),
                                                                                               "xxxxx_vat":             xxxxx_vat,            
                                                                                               "address":               address,
                                                                                               "voucher_no":            voh_no,                 
                                                                                               "broker":                broker,
                                                                                               "account_no":            "10027601000000",       
                                                                                               "customer_id":           cust_no,
                                                                                               "customer_vat":          cust_vat,      
                                                                                               "policy_number":         "BAH/MOT/"+str(pol_year)[-2:]+"/"+str(pol_no),
                                                                                               "endorsement_year":      "BAH/MOT/"+str(endt_year)[-2:]+"/"+str(endt_no),
                                                                                               "policy_type":           pol_type,
                                                                                               "from_date":             datetime.strptime(((eff_dt.__str__()).split(" "))[0], '%Y-%m-%d').strftime('%d/%m/%Y'),
                                                                                               "to_date":               datetime.strptime(((exp_dt.__str__()).split(" "))[0], '%Y-%m-%d').strftime('%d/%m/%Y'),
                                                                                               "registeration_no":      registration,
                                                                                               "make":                  make+" - "+model,
                                                                                               "vehicle_type":          body_type,
                                                                                               "chassis":               chassis_no,
                                                                                               "rsa":                   rsa,    
                                                                                               "total_before_vat":      total_prem,
                                                                                               "vat_percentage":        vat_pct,
                                                                                               "total_after_vat":       vat_amt,
                                                                                               "total_due":             final_tot,
                                                                                               "amount_in_words":       "", 
                                                                                               "printed_by":            "webadmin"})
                        copyfile('prints/Tax_Invoice-'+str(params[0])+'-'+str(params[1])+'.pdf', 'portal/storage/app/printouts')
                    except:
                        print('Ok')
                    
                    try:
                        if int(menu) == 500:
                            thankyou = client.messages.create(                                  
                                              body="""Thank you for your payment. Your policy *""" + str(params[0]) + """/""" + str(params[1]) + """* has been successfully renewed. Your motor schedule and tax invoice are attached below. Please type *M* to return back to main Menu or *Q* to quit.""",
                                              from_='whatsapp:+1xxxxxxxxxxx',
                                              to='whatsapp:+973' + str(mobile))
                        else:
                            contentar = """شكراً على الدفع . لقد تمَ بنجاح تجديد وثيقة التأمين خاصتكم *""" + str(params[0]) + """/""" + str(params[1]) + """*. ستجدون مرفقاً أدناه جدول الوثيقة و الفاتورة الضريبية. الرجاء إدخال "ر" للعودة إلى القائمة الرئيسية أو "خ" للخروج النهائي من المحادثة."""
                            thankyou = client.messages.create(                                  
                                              body=contentar.encode("utf-8") ,
                                              from_='whatsapp:+1xxxxxxxxxxx',
                                              to='whatsapp:+973' + str(mobile))                
                        schedule = client.messages.create(                                  
                                          body="Schedule-" + str(params[0]) + """-""" + str(params[1]) + ".pdf",
                                          media_url="""https://xxxxxx.ngrok.io/prints/Schedule-"""+str(params[0])+"""-"""+str(params[1])+""".pdf""",
                                          from_='whatsapp:+1xxxxxxxxxxx',
                                          to='whatsapp:+973' + str(mobile))
                        
                        invoice = client.messages.create(                                  
                                          body="Tax_Invoice-" + str(params[0]) + """-""" + str(params[1]) + ".pdf",
                                          media_url="""https://xxxxxx.ngrok.io/prints/Tax_Invoice-"""+str(params[0])+"""-"""+str(params[1])+""".pdf""",
                                          from_='whatsapp:+1xxxxxxxxxxx',
                                          to='whatsapp:+973' + str(mobile))   
                    except:
                        print("Renewal by SMS - stage 3")                        
                    
                except:
                    
                    try:
                        subject = """Online Motor Policy Renewal Issue for Policy No: """ + str(params[0]) + """/""" +  str(params[1])
                        destination = 'motor@company.c0m'
                        try:
                            content = """Dear Motor Dept,

    The motor policy """ + str(params[0]) + """/""" + str(params[1]) + """ has been successfully paid online but it wasn't renewed on AMAN system. Kindly renew it on AMAN and contact the client on """ + str(mobile) + """ to share the motor documents.

    Regards,
    Chatbot"""
                            print("Sending Email with issue")
                            email(subject,destination,content)             
                        except:
                            content = """Dear Motor Dept,

    The motor policy """ + str(params[0]) + """/""" + str(params[1]) + """ has been successfully paid online but it wasn't renewed on AMAN system. Kindly renew it on AMAN and contact the client to share the motor documents.

    Regards,
    Chatbot"""
                            print("Sending Email with issue")
                            email(subject,destination,content)                   
                        print("Finished sending Email with issue")     
                                           
                        if int(menu) == 500:                
                            message = client.messages.create(
                                              from_='whatsapp:+1xxxxxxxxxxx',
                                              body="""Thank you for your payment. However, some technical difficulties occured and couldn't renew your policy *""" + str(params[0]) + """/""" + str(params[1]) + """*. Please contact our Call Center on 17561661 to resolve your policy renewal issue during business days from 8 AM to 4 PM. Please type *M* to return back to main Menu if you'd like to submit a Complaint under General inquiry sub-menu to notify the concerned parties and help you faster.""",
                                              to='whatsapp:+973' + str(mobile))
                        else:
                            contentar = """شكراً على إتمام عمليةالدفع . لقد حدتث بعض الصعاب خلال تجديد وثيقتكم *""" + str(params[0]) + """/""" + str(params[1]) + """*. الرجاء الإتصال على 1761661 خلال أوقات العمل من 8 صباحاً و لغاية 4 مساءً لأجل مساعدتكم. الرجاء إدخال "ر" للعودة إلى القائمة الرئيسية إن كنت ترغب في تقديم شكوى من أجل الإسراع في حل مشكلة التجديد."""
                            message = client.messages.create(
                                              from_='whatsapp:+1xxxxxxxxxxx',
                                              body=contentar.encode("utf-8"),
                                              to='whatsapp:+973' + str(mobile))                
                        print("Exception: ",message.sid)                          
                    except:
                        return jsonify({"status":{'result': 'Failed'}})  
            else:
                try:
                    mysqldb = mydb()
                    mycursor = mysqldb.cursor()
                    sql3 = """INSERT INTO requests (timestamp, mobile, pol_no, pol_year, pay_status, trans_id) VALUES (%s, %s, %s, %s, %s, %s)"""
                    rec = (ts, str(mobile), int(params[0]),int(params[1]), str(params[2]), str(params[3]))
                    mycursor.execute(sql3, rec)   
                    mysqldb.commit()
                    mysqldb.close()                         
                except:
                    print("Renewal by SMS - stage 4")

            return jsonify({"status":{'result': 'Ok'}})    

if __name__ == '__name__':
    app.run(debug=True)
    
api.add_resource(HelloWorld, '/')
api.add_resource(Test, '/test')
api.add_resource(Payment_Status, '/status')
