import sys
import os
import cx_Oracle
import json
import jwt
import time
import datetime
from functools import wraps
from flask import Flask, jsonify, request, make_response
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
from datetime import datetime, timedelta
from tinydb import TinyDB, Query
import mysql.connector

app = Flask(__name__)
app.config['SECRET_KEY'] = "XXXXXXXXXX"
api = Api(app)
auth = HTTPBasicAuth()

def mydb():
    mysqldb = mysql.connector.connect(
        host = "server-00616",
        port = 3305,
        user = "chatbot",
        passwd = "XXXXXXXXXX",
        database = "quotations",
        auth_plugin='mysql_native_password')
    return mysqldb

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
    if auth and auth.username == 'admin' and auth.password == 'XXXXXXXXXX':
        token = jwt.encode({'user' : auth.username, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
        # https://jwt.io 
        return jsonify({'token' : token.decode('UTF-8')})
    return make_response('Could not verify!', 401, {'WWW-Authenticate' : 'Basic realm="Login Required"'})

def get_egov_status(branch,endt_no,endt_year,endt_type,class_of_business,office): 
    con = cx_Oracle.connect('GENCDE/XXXXXXXXXX@xx.xx.xx.xx/amandb')
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

def get_policy_details_cpr(cpr,mobile):
    con = cx_Oracle.connect('GENCDE/xxxxxxxx@xx.xx.xx.xx/amandb')
    cur1 = con.cursor()
    cur3 = con.cursor()
    p_cpr = cpr
    cust_no = None
  
    cur1.execute("""SELECT distinct ecar_cust_no 
                      FROM carcde.car_ins_endt
                     WHERE ecar_cust_no IN (SELECT cust_no 
                                              FROM gencde.customers   
                                             WHERE cust_CPR_CR = """ + "'" + p_cpr + "'" +""")                  
                       AND ecar_status + 0 != 2
                       AND TO_DATE(SYSDATE,'dd/mm/rrrr') - TO_DATE(ecar_ins_ed_dt,'dd/mm/rrrr') < 1""")
    result1 = cur1.fetchall()
    g = 0
    entities =()
    for entity1 in result1:
        cust_no = int(result1[g][0])
        entities = entities + (cust_no,0)
        g = g+1
    cur1.close()
        
    if cust_no != ():
        cur3.execute("""SELECT Decode (vcar_pol_office, 2, 'Qatar', 'Bahrain') office_desc, 
                            NVL (GENCDE.get_sys_desc_web (55,(SELECT cust_sub_class  
                                                                FROM gencde.customers    
                                                               WHERE  vcar_office = cust_office   
                                                                 AND  vcar_agent_no = cust_no),2),'Direct')    source,   
                            GENCDE.get_sys_desc_web (16, vcar_class_of_business, 2)  class_desc,    
                            GENCDE.get_sys_desc_web (29, vcar_policy_type, 2)        pol_type_desc, 
                            vcar_pol_no      policy_no,      
                            vcar_pol_year    policy_year, 
                            vcar_endt_no endt_no, 
                            vcar_year endt_year,  
                            (Select Replace (cust_lname, Chr (9))    
                                From   gencde.customers 
                                Where  vcar_agent_no = cust_no  
                                And    vcar_branch = cust_branch   
                                And    vcar_office = cust_office)   intermediary,   
                            Replace (vcar_client_name, Chr (9))  client,    
                            Replace (vcar_cust_name, Chr (9))    insured,    
                            vcar_cust_no cust_no,    
                            vcar_ins_st_dt       eff_dt,     
                            vcar_ins_ed_dt       exp_dt,     
                            vcar_ins_ed_dt + 1   ren_dt,
                            """ + "'" + mobile + "'" + """ mobile,
                            (SELECT MAX (EVCL_POLICY_TYPE)  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no = evcl_endt_no  
                                    AND vcar_year = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type)  Pol_Type,                              
                            (SELECT MAX (vvcl_vehicle_make)  
                                FROM carcde.vcar_vehicle_endt  
                                WHERE     vcar_office = vvcl_office  
                                    AND vcar_endt_no = vvcl_endt_no  
                                    AND vcar_year = vvcl_year  
                                    AND vcar_endt_type = vvcl_endt_type) Make,  
                            (SELECT MAX (vvcl_vehicle_model)  
                                FROM carcde.vcar_vehicle_endt  
                                WHERE     vcar_office = vvcl_office  
                                    AND vcar_endt_no = vvcl_endt_no  
                                    AND vcar_year = vvcl_year  
                                    AND vcar_endt_type = vvcl_endt_type) Model,  
                            (SELECT MAX (NVL (evcl_type_of_body,ovcl_type_of_body))  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no = evcl_endt_no  
                                    AND vcar_year = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type)  Body_Type,                 
                            (SELECT MAX (NVL (EVCL_PLATE_TYPE,OVCL_PLATE_TYPE))  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no = evcl_endt_no  
                                    AND vcar_year = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type)  Plate_Type,   
                            (SELECT MAX (NVL (EVCL_CLASS_OF_USE,OVCL_CLASS_OF_USE))  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no = evcl_endt_no  
                                    AND vcar_year = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type)  Class_Of_Use,  
                            (SELECT MAX (NVL (EVCL_REGISTRATION_NO,OVCL_REGISTRATION_NO))  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no = evcl_endt_no  
                                    AND vcar_year = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type)  Registration_No,    
                            (SELECT MAX (DECODE (evcl_year_of_make,  
                                                NULL, ovcl_year_of_make,  
                                                evcl_year_of_make))  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no = evcl_endt_no  
                                    AND vcar_year = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type) Make_Year, 
                            (SELECT MAX (NVL (EVCL_SEAT_CAPACITY,OVCL_SEAT_CAPACITY))  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no = evcl_endt_no  
                                    AND vcar_year = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type)  Seats,       
                            (SELECT MAX (NVL (EVCL_CHASSIS_NO,OVCL_CHASSIS_NO))  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no = evcl_endt_no  
                                    AND vcar_year = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type)  Chassis,                                          
                            (SELECT max(decode(EVCL_ENGINE_CAPACITY,null,OVCL_ENGINE_CAPACITY,EVCL_ENGINE_CAPACITY))  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no   = evcl_endt_no  
                                    AND vcar_year      = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type) Engine_CC,  
                            (SELECT MAX (NVL(EVCL_AGENCY_FLAG,2))  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no = evcl_endt_no  
                                    AND vcar_year = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type)  Agency_Repair,            
                            (SELECT MAX (ECAR_RSA_PROVIDER)  
                                FROM carcde.car_ins_endt  
                                WHERE     vcar_office = ecar_office  
                                    AND vcar_endt_no = ecar_endt_no  
                                    AND vcar_year = ecar_year  
                                    AND vcar_endt_type = ecar_endt_type)  RSA_Provider,                                               
                            (SELECT MAX (NVL (EVCL_TP_TARIFF,OVCL_TP_TARIFF))  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no = evcl_endt_no  
                                    AND vcar_year = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type)  Tariff,
                            VCAR_AGENT_NO Agent_No,
                            NVL(VCAR_AGENT_COMM,0) Agent_Comm,
                            (SELECT NVL(cust_aname,cust_lname) 
                                FROM gencde.customers 
                                WHERE cust_no = VCAR_AGENT_NO) Agent_Name                             
                        FROM carcde.vcar_max_ins_endt a       
                    WHERE vcar_status + 0 != 2 
                      AND TO_DATE(SYSDATE,'dd/mm/rrrr') - TO_DATE(vcar_ins_ed_dt,'dd/mm/rrrr') < 1
                        AND VCAR_CUST_NO IN """ + str(entities))               
        result3 = cur3.fetchall()

        mysqldb = mydb()
        mycursor1 = mysqldb.cursor()
        mycursor2 = mysqldb.cursor()

        i = 0
        for row3 in result3:
            sql1 = """SELECT * FROM pol_details WHERE policy_no=""" + str(result3[i][4]) + """ AND policy_year=""" + str(result3[i][5])
            mycursor1.execute(sql1)
            check4 = mycursor1.fetchall()
            if check4 == []:   
                time_tuple = time.localtime()
                ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
                
                sql2 = """INSERT INTO pol_details (timestamp, 
                                                   office_desc,
                                                   source,
                                                   class_desc,
                                                   pol_type_desc,
                                                   policy_no,
                                                   policy_year,
                                                   endt_no,
                                                   endt_year,
                                                   intermediary,
                                                   client,
                                                   insured,
                                                   cust_no,
                                                   eff_dt,
                                                   exp_dt,
                                                   ren_dt,
                                                   mobile,
                                                   agent_no,
                                                   agent_comm,
                                                   pol_type,
                                                   veh_make,
                                                   veh_model,
                                                   body_type,
                                                   plate_type,
                                                   class_of_use,
                                                   reg_no,
                                                   year_of_make,
                                                   seats,
                                                   chassis,
                                                   engine_cc,
                                                   agency_repair,
                                                   rsa_provider,
                                                   tariff,
                                                   agent_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                                                                        %s, %s, %s, %s)"""

                rec = (ts,
                       result3[i][0],
                       result3[i][1],
                       result3[i][2],
                       result3[i][3],
                       result3[i][4], 
                       result3[i][5],
                       result3[i][6], 
                       result3[i][7], 
                       result3[i][8], 
                       result3[i][9], 
                       result3[i][10],
                       result3[i][11],
                       (((result3[i][12]).__str__()).split(" "))[0], 
                       (((result3[i][13]).__str__()).split(" "))[0],
                       (((result3[i][14]).__str__()).split(" "))[0],
                       result3[i][15],
                       result3[i][30],
                       result3[i][31],
                       result3[i][16],
                       result3[i][17],
                       result3[i][18],
                       result3[i][19],
                       result3[i][20],
                       result3[i][21],
                       result3[i][22],
                       result3[i][23],
                       result3[i][24],
                       result3[i][25],
                       result3[i][26],
                       result3[i][27],
                       result3[i][28],
                       result3[i][29],
                       result3[i][32])
                
                try:
                    mycursor2.execute(sql2, rec)
                    mysqldb.commit()
                except:
                    print("Some errors during records insert in pol_details table!")

            i = i+1
    mysqldb.close()
    cur3.close()
    con.close()

def get_policy_details(mobile):
    con = cx_Oracle.connect('GENCDE/xxxxxxxx@xx.xx.xx.xx/amandb')
    cur1 = con.cursor()
    cur2 = con.cursor()
    cur3 = con.cursor()
    p_mobile = mobile
    cust_no = None

    cur1.execute("""SELECT distinct ecar_cust_no 
                      FROM carcde.car_ins_endt
                     WHERE ecar_cust_no IN (SELECT ca_cust_no  
                                              FROM gencde.cust_address    
                                             WHERE ca_t_mobile = """ + "'" + p_mobile + "'" +""")                  
                       AND ecar_status + 0 != 2
                       AND TO_DATE(SYSDATE,'dd/mm/rrrr') - TO_DATE(ecar_ins_ed_dt,'dd/mm/rrrr') < 1""")
    result1 = cur1.fetchall()
    g = 0

    entities =()
    for entity1 in result1:
        cust_no = int(result1[g][0])
        entities = entities + (cust_no,0)
        g = g+1
    cur1.close()

    if entities == ():
        cur2.execute("""SELECT distinct ecar_cust_no 
                          FROM carcde.car_ins_endt
                          WHERE ecar_cust_no IN (SELECT cust_no 
                                                   FROM gencde.customers   
                                                  WHERE cust_mobile = """ + "'" + p_mobile + "'" +""")                  
                            AND ecar_status + 0 != 2
                            AND TO_DATE(SYSDATE,'dd/mm/rrrr') - TO_DATE(ecar_ins_ed_dt,'dd/mm/rrrr') < 1""")   
        result2 = cur2.fetchall()
        h = 0

        for entity2 in result2:
            cust_no = int(result2[h][0])
            entities = entities + (cust_no,0)
            h = h+1
        cur2.close()
        
    if cust_no != ():
        cur3.execute("""SELECT Decode (vcar_pol_office, 2, 'Qatar', 'Bahrain') office_desc, 
                                NVL (GENCDE.get_sys_desc_web (55,(SELECT cust_sub_class  
                                                                    FROM gencde.customers    
                                                                    WHERE  vcar_office = cust_office   
                                                                        AND  vcar_agent_no = cust_no),2),'Direct')    source,   
                                GENCDE.get_sys_desc_web (16, vcar_class_of_business, 2)  class_desc,    
                                GENCDE.get_sys_desc_web (29, vcar_policy_type, 2)        pol_type_desc, 
                                vcar_pol_no      policy_no,      
                                vcar_pol_year    policy_year, 
                                vcar_endt_no endt_no, 
                                vcar_year endt_year,  
                                (Select Replace (cust_lname, Chr (9))    
                                    From   gencde.customers 
                                    Where  vcar_agent_no = cust_no  
                                    And    vcar_branch = cust_branch   
                                    And    vcar_office = cust_office)   intermediary,   
                                Replace (vcar_client_name, Chr (9))  client,    
                                Replace (vcar_cust_name, Chr (9))    insured,    
                                vcar_cust_no cust_no,    
                                vcar_ins_st_dt       eff_dt,     
                                vcar_ins_ed_dt       exp_dt,     
                                vcar_ins_ed_dt + 1   ren_dt,
                                """ + "'" + p_mobile + "'" + """ mobile,
                            (SELECT MAX (EVCL_POLICY_TYPE)  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no = evcl_endt_no  
                                    AND vcar_year = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type)  Pol_Type,                              
                            (SELECT MAX (vvcl_vehicle_make)  
                                FROM carcde.vcar_vehicle_endt  
                                WHERE     vcar_office = vvcl_office  
                                    AND vcar_endt_no = vvcl_endt_no  
                                    AND vcar_year = vvcl_year  
                                    AND vcar_endt_type = vvcl_endt_type) Make,  
                            (SELECT MAX (vvcl_vehicle_model)  
                                FROM carcde.vcar_vehicle_endt  
                                WHERE     vcar_office = vvcl_office  
                                    AND vcar_endt_no = vvcl_endt_no  
                                    AND vcar_year = vvcl_year  
                                    AND vcar_endt_type = vvcl_endt_type) Model,  
                            (SELECT MAX (NVL (evcl_type_of_body,ovcl_type_of_body))  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no = evcl_endt_no  
                                    AND vcar_year = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type)  Body_Type,                 
                            (SELECT MAX (NVL (EVCL_PLATE_TYPE,OVCL_PLATE_TYPE))  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no = evcl_endt_no  
                                    AND vcar_year = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type)  Plate_Type,   
                            (SELECT MAX (NVL (EVCL_CLASS_OF_USE,OVCL_CLASS_OF_USE))  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no = evcl_endt_no  
                                    AND vcar_year = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type)  Class_Of_Use,  
                            (SELECT MAX (NVL (EVCL_REGISTRATION_NO,OVCL_REGISTRATION_NO))  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no = evcl_endt_no  
                                    AND vcar_year = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type)  Registration_No,    
                            (SELECT MAX (DECODE (evcl_year_of_make,  
                                                NULL, ovcl_year_of_make,  
                                                evcl_year_of_make))  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no = evcl_endt_no  
                                    AND vcar_year = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type) Make_Year, 
                            (SELECT MAX (NVL (EVCL_SEAT_CAPACITY,OVCL_SEAT_CAPACITY))  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no = evcl_endt_no  
                                    AND vcar_year = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type)  Seats,       
                            (SELECT MAX (NVL (EVCL_CHASSIS_NO,OVCL_CHASSIS_NO))  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no = evcl_endt_no  
                                    AND vcar_year = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type)  Chassis,                                          
                            (SELECT max(decode(EVCL_ENGINE_CAPACITY,null,OVCL_ENGINE_CAPACITY,EVCL_ENGINE_CAPACITY))  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no   = evcl_endt_no  
                                    AND vcar_year      = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type) Engine_CC,  
                            (SELECT MAX (NVL(EVCL_AGENCY_FLAG,2))  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no = evcl_endt_no  
                                    AND vcar_year = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type)  Agency_Repair,            
                            (SELECT MAX (ECAR_RSA_PROVIDER)  
                                FROM carcde.car_ins_endt  
                                WHERE     vcar_office = ecar_office  
                                    AND vcar_endt_no = ecar_endt_no  
                                    AND vcar_year = ecar_year  
                                    AND vcar_endt_type = ecar_endt_type)  RSA_Provider,                                               
                            (SELECT MAX (NVL (EVCL_TP_TARIFF,OVCL_TP_TARIFF))  
                                FROM carcde.car_vehicle_endt  
                                WHERE     vcar_office = evcl_office  
                                    AND vcar_endt_no = evcl_endt_no  
                                    AND vcar_year = evcl_year  
                                    AND vcar_endt_type = evcl_endt_type)  Tariff,
                            VCAR_AGENT_No Agent_No,
                            NVL(VCAR_AGENT_COMM,0) Agent_Comm,
                            (SELECT NVL(cust_aname,cust_lname) 
                               FROM gencde.customers 
                              WHERE cust_no = VCAR_AGENT_NO) Agent_Name                                   
                     FROM carcde.vcar_max_ins_endt a       
                    WHERE vcar_status + 0 != 2 
                      AND TO_DATE(SYSDATE,'dd/mm/rrrr') - TO_DATE(vcar_ins_ed_dt,'dd/mm/rrrr') < 1
                      AND VCAR_CUST_NO IN """ + str(entities))               
        result3 = cur3.fetchall()
        
        mysqldb = mydb()
        mysqlcur = mysqldb.cursor()
        mycursor4 = mysqldb.cursor()
        i = 0
        for row3 in result3:
            sql4 = """SELECT * FROM pol_details 
                       WHERE mobile= """ + str(result3[i][15]) + """
                         AND policy_no= """ + str(result3[i][4],) + """
                         AND policy_year= """ + str(result3[i][5],)
                         
            mycursor4.execute(sql4)
            myresult4 = mycursor4.fetchall()            
            if myresult4 == []:   
                time_tuple = time.localtime()
                ts = time.strftime("%Y-%m-%d",time_tuple)
                sqlFormula = """INSERT INTO pol_details (timestamp, 
                                                         office_desc,
                                                         source,
                                                         class_desc,
                                                         pol_type_desc,
                                                         policy_no,
                                                         policy_year,
                                                         endt_no,
                                                         endt_year,
                                                         intermediary,
                                                         client,
                                                         insured,
                                                         cust_no,
                                                         eff_dt,
                                                         exp_dt,
                                                         ren_dt,
                                                         mobile,
                                                         agent_no,
                                                         agent_comm,
                                                         pol_type,
                                                         veh_make,
                                                         veh_model,
                                                         body_type,
                                                         plate_type,
                                                         class_of_use,
                                                         reg_no,
                                                         year_of_make,
                                                         seats,
                                                         chassis,
                                                         engine_cc,
                                                         agency_repair,
                                                         rsa_provider,
                                                         tariff,
                                                         agent_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                                             %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                                             %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                                                                             %s, %s, %s, %s)"""
                rec = (ts,
                       result3[i][0],
                       result3[i][1],
                       result3[i][2],
                       result3[i][3],
                       result3[i][4], 
                       result3[i][5],
                       result3[i][6], 
                       result3[i][7], 
                       result3[i][8], 
                       result3[i][9], 
                       result3[i][10],
                       result3[i][11],
                       (((result3[i][12]).__str__()).split(" "))[0], 
                       (((result3[i][13]).__str__()).split(" "))[0],
                       (((result3[i][14]).__str__()).split(" "))[0],
                       result3[i][15],
                       result3[i][30],
                       result3[i][31],
                       result3[i][16],
                       result3[i][17],
                       result3[i][18],
                       result3[i][19],
                       result3[i][20],
                       result3[i][21],
                       result3[i][22],
                       result3[i][23],
                       result3[i][24],
                       result3[i][25],
                       result3[i][26],
                       result3[i][27],
                       result3[i][28],
                       result3[i][29],
                       result3[i][32])
                try:
                    mysqlcur.execute(sqlFormula, rec)
                    mysqldb.commit()
                except:
                    print("Some errors during records insert in pol_details table!")                
            i = i+1
        
        mysqldb.close()
        cur3.close()
        con.close()

def change_registration(policy_type,
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
                        registration_no,
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
                        tariff): 
    con = cx_Oracle.connect('GENCDE/xxxxxxxx@xx.xx.xx.xx/amandb')
    cur = con.cursor()
    cur.execute("""ALTER SESSION SET NLS_DATE_FORMAT = 'DD/MM/YYYY'""")
    
    P_BRANCH                     = 1
    P_OFFICE                     = 1
    P_CLASS_OF_BUSINESS          = 1
    P_POLICY_TYPE                = policy_type
    P_ENDT_TYPE                  = 2                                    
    P_TRN_TYPE                   = 10
    P_ISSUE_DATE                 = (datetime.now()).strftime("%d/%m/%Y")        
    P_PAYMENT_MODE               = 1
    P_HIJRI_EFF_DATE             = None             
    P_HIJRI_EXP_DATE             = None
    P_EFF_DATE                   = (datetime.now()).strftime("%d/%m/%Y") 
    P_EXP_DATE                   = exp_date 
    P_CLIENT_CODE                = client_code
    P_CLIENT_ENAME               = client_ename
    P_CLIENT_ANAME               = client_aname
    P_INSURED_ENAME              = insured_ename
    P_INSURED_ANAME              = None                 
    P_BROKER                     = agent_no                                
    P_BROKER_COMM_PCNT           = comm                                    
    P_BROKER_COMM_AMT            = comm_amount                             
    P_ID_NO                      = None
    P_OCCUPATION                 = None
    P_NATIONALITY                = None
    P_CITY                       = None
    P_HOME_TEL                   = None
    P_OFFICE_TEL                 = None
    P_MOBILE                     = None
    P_DOB                        = None
    P_AGE                        = None
    P_VEHICLE_MAKE               = vehicle_make
    P_VEHICLE_MODEL              = vehicle_model
    P_TYPE_OF_BODY               = type_of_body
    P_PLATE_TYPE                 = plate_type
    P_EVCL_CUSTOM_ID             = None
    P_CLASS_OF_USE               = class_of_use
    P_PLATE_NO                   = registration_no
    P_ENGINE_NO                  = None
    P_NO_OF_CYLINDERS            = None
    P_YEAR_OF_MAKE               = year_of_make
    P_SEATING_CAPACITY           = seating_capacity
    P_SI                         = 0
    P_RATE                       = None
    P_BASIC_PREM                 = 0
    P_TOTAL_PREM                 = 1
    P_NET_PREM                   = 0
    P_ADD_PREM                   = 0
    P_DISCOUNT                   = 0
    P_DEPRECIATION               = None
    P_CHASSIS_NO                 = chassis_no
    P_REMARKS                    = change_remarks
    P_ADDRESS                    = None
    P_BUS_LOCATION               = 1
    P_VEHICLE_COLOR              = None
    P_DEDUCTABLE                 = None
    P_ENGINE_CAPACITY            = engine_capacity
    P_PER_ACC_DRV                = 0
    P_PAD_COVER_PCNT             = 0
    P_PAD_COVER_AMT              = 0
    P_PER_ACC_DRV_PASS           = 0
    P_PADP_COVER_PCNT            = 0
    P_PADP_COVER_AMT             = 0
    P_AGENCY_REPAIR              = agency_repair                
    P_ER_COVER_PCNT              = 0
    P_ER_COVER_AMT               = 0
    P_CON_NAT                    = 0
    P_CN_COVER_PCNT              = 0
    P_CN_COVER_AMT               = 0
    P_BETWEEB_AGE                = 0
    P_BA_COVER_PCNT              = 0
    P_BA_COVER_AMT               = 0
    P_LESSTHAN_AGE               = 0
    P_LA_COVER_PCNT              = 0
    P_LA_COVER_AMT               = 0
    P_ADJUST_FLAG                = 0
    P_CUST_ZIP_CODE              = None
    P_CUST_PO_BOX                = None
    P_DRIVER_NAME                = driver_name
    P_AGENCY_FLAG                = 2
    P_USER_ID                    = 'WebAdmin'
    P_POL_NO                     = pol_no
    P_POL_YEAR                   = pol_year
    P_ENDT_NO                    = cur.var(int)
    P_YEAR                       = cur.var(int)
    P_DRIVER_BIRTH_DT            = None
    P_DRIVER_IQAMA_NO            = None
    P_DRIVER_LICENSE_TYPE        = None
    P_REF_NO                     = None
    P_BROKER_NO                  = 0
    P_SOURCE                     = 1
    P_POST_FLAG                  = cur.var(int)
    P_ENDT_DT                    = cur.var(datetime)
    P_CLIENT_VOH_TYPE            = cur.var(int)
    P_CLIENT_VOH_YEAR            = cur.var(int)
    P_CLIENT_VOH_NO              = cur.var(int)
    P_AGENT_VOH_TYPE             = cur.var(int)
    P_AGENT_VOH_YEAR             = cur.var(int)
    P_AGENT_VOH_NO               = cur.var(int)
    P_CUST_NO                    = cust_no
    P_AGENT_NO                   = agent_no
    P_AGENT_NAME                 = agent_name
    P_AGENT_COMM_AMT             = comm_amount
    P_SERVICE_CHARGE             = 0
    P_ADD_TAX                    = 0
    P_ISSUE_FEE                  = 1
    P_STAMP_FEE                  = 0
    P_ICF_FEE                    = 0
    P_GATR_PREM                  = 0
    P_REI_FLAG                   = cur.var(int)
    P_ERR_FLAG                   = cur.var(int)
    P_SEQUENCE_NO                = None
    p_rsa_provider               = rsa_provider
    p_beneficiary_no             = None
    p_cust_class                 = None
    p_disc_code                  = 0
    p_disc_pcnt                  = 0
    p_ncb_flag                   = 0
    p_ncb_amt                    = 0
    p_loading_code               = 0
    p_loading_pcnt               = 0
    p_loading                    = 0
    p_load_amt                   = 0                                                        
    p_tariff_pkg                 = tariff
    p_endo_serial                = cur.var(int)
    p_vat_pcnt                   = 5
    p_vat_amt                    = 0.05
    p_final_tot_amt              = 1.05
    p_vat_comm_pcnt              = 0                                                        
    p_vat_comm_amt               = 0                                                        
    P_ecar_vehicle_serial        = cur.var(int)
    p_file_no                    = None
    print("Pre-insert")
    result = cur.callproc('WEB_INSERT_DIRECT_AMAN.insert_endt_web',
        [P_BRANCH               ,
        P_OFFICE                ,
        P_CLASS_OF_BUSINESS     ,
        P_POLICY_TYPE           ,
        P_ENDT_TYPE             ,
        P_TRN_TYPE              ,
        P_ISSUE_DATE            ,
        P_PAYMENT_MODE          ,
        P_HIJRI_EFF_DATE        ,
        P_HIJRI_EXP_DATE        ,
        P_EFF_DATE              ,
        P_EXP_DATE              ,
        P_CLIENT_CODE           ,
        P_CLIENT_ENAME          ,
        P_CLIENT_ANAME          ,
        P_INSURED_ENAME         ,
        P_INSURED_ANAME         ,
        P_BROKER                ,
        P_BROKER_COMM_PCNT      ,
        P_BROKER_COMM_AMT       ,
        P_ID_NO                 ,
        P_OCCUPATION            ,
        P_NATIONALITY           ,
        P_CITY                  ,
        P_HOME_TEL              ,
        P_OFFICE_TEL            ,
        P_MOBILE                ,
        P_DOB                   ,
        P_AGE                   ,
        P_VEHICLE_MAKE          ,
        P_VEHICLE_MODEL         ,
        P_TYPE_OF_BODY          ,
        P_PLATE_TYPE            ,
        P_EVCL_CUSTOM_ID        ,
        P_CLASS_OF_USE          ,
        P_PLATE_NO              ,
        P_ENGINE_NO             ,
        P_NO_OF_CYLINDERS       ,
        P_YEAR_OF_MAKE          ,
        P_SEATING_CAPACITY      ,
        P_SI                    ,
        P_RATE                  ,
        P_BASIC_PREM            ,
        P_TOTAL_PREM            ,
        P_NET_PREM              ,
        P_ADD_PREM              ,
        P_DISCOUNT              ,
        P_DEPRECIATION          ,
        P_CHASSIS_NO            ,
        P_REMARKS               ,
        P_ADDRESS               ,
        P_BUS_LOCATION          ,
        P_VEHICLE_COLOR         ,
        P_DEDUCTABLE            ,
        P_ENGINE_CAPACITY       ,
        P_PER_ACC_DRV           ,
        P_PAD_COVER_PCNT        ,
        P_PAD_COVER_AMT         ,
        P_PER_ACC_DRV_PASS      ,
        P_PADP_COVER_PCNT       ,
        P_PADP_COVER_AMT        ,
        P_AGENCY_REPAIR         ,
        P_ER_COVER_PCNT         ,
        P_ER_COVER_AMT          ,
        P_CON_NAT               ,
        P_CN_COVER_PCNT         ,
        P_CN_COVER_AMT          ,
        P_BETWEEB_AGE           ,
        P_BA_COVER_PCNT         ,
        P_BA_COVER_AMT          ,
        P_LESSTHAN_AGE          ,
        P_LA_COVER_PCNT         ,
        P_LA_COVER_AMT          ,
        P_ADJUST_FLAG           ,
        P_CUST_ZIP_CODE         ,
        P_CUST_PO_BOX           ,
        P_DRIVER_NAME           ,
        P_AGENCY_FLAG           ,
        P_USER_ID               ,
        P_POL_NO                ,
        P_POL_YEAR              ,
        P_ENDT_NO               ,
        P_YEAR                  ,
        P_DRIVER_BIRTH_DT       ,
        P_DRIVER_IQAMA_NO       ,
        P_DRIVER_LICENSE_TYPE   ,
        P_REF_NO                ,
        P_BROKER_NO             ,
        P_SOURCE                ,
        P_POST_FLAG             ,
        P_ENDT_DT               ,
        P_CLIENT_VOH_TYPE       ,
        P_CLIENT_VOH_YEAR       ,
        P_CLIENT_VOH_NO         ,
        P_AGENT_VOH_TYPE        ,
        P_AGENT_VOH_YEAR        ,
        P_AGENT_VOH_NO          ,
        P_CUST_NO               ,
        P_AGENT_NO              ,
        P_AGENT_NAME            ,
        P_AGENT_COMM_AMT        ,
        P_SERVICE_CHARGE        ,
        P_ADD_TAX               ,
        P_ISSUE_FEE             ,
        P_STAMP_FEE             ,
        P_ICF_FEE               ,
        P_GATR_PREM             ,
        P_REI_FLAG              ,
        P_ERR_FLAG              ,
        P_SEQUENCE_NO           ,
        p_rsa_provider          ,
        p_beneficiary_no        ,
        p_cust_class            ,
        p_disc_code             ,
        p_disc_pcnt             ,
        p_ncb_flag              ,
        p_ncb_amt               ,
        p_loading_code          ,
        p_loading_pcnt          ,
        p_loading               ,
        p_load_amt              ,
        p_tariff_pkg            ,
        p_endo_serial           , 
        p_vat_pcnt              ,
        p_vat_amt               ,
        p_final_tot_amt         ,
        p_vat_comm_pcnt         ,
        p_vat_comm_amt          ,
        P_ecar_vehicle_serial   ,
        p_file_no])        
    print("result: ",tuple(result))
    time_tuple = time.localtime()
    ts = time.strftime("%Y-%m-%d",time_tuple)
    mysqldb = mydb()
    mysqlcur = mysqldb.cursor()
    sqlFormula = """INSERT INTO renewals (timestamp                 ,                  
                                          BRANCH                   ,
                                          OFFICE                   ,
                                          CLASS_OF_BUSINESS        ,
                                          POLICY_TYPE              ,
                                          ENDT_TYPE                ,
                                          TRN_TYPE                 ,
                                          ISSUE_DATE               ,
                                          PAYMENT_MODE             ,
                                          HIJRI_EFF_DATE           ,
                                          HIJRI_EXP_DATE           ,
                                          EFF_DATE                 ,
                                          EXP_DATE                 ,
                                          CLIENT_CODE              ,
                                          CLIENT_ENAME             ,
                                          CLIENT_ANAME             ,
                                          INSURED_ENAME            ,
                                          INSURED_ANAME            ,
                                          BROKER                   ,
                                          BROKER_COMM_PCNT         ,
                                          BROKER_COMM_AMT          ,
                                          ID_NO                    ,
                                          OCCUPATION               ,
                                          NATIONALITY              ,
                                          CITY                     ,
                                          HOME_TEL                 ,
                                          OFFICE_TEL               ,
                                          MOBILE                   ,
                                          DOB                      ,
                                          AGE                      ,
                                          VEHICLE_MAKE             ,
                                          VEHICLE_MODEL            ,
                                          TYPE_OF_BODY             ,
                                          PLATE_TYPE               ,
                                          EVCL_CUSTOM_ID           ,
                                          CLASS_OF_USE             ,
                                          PLATE_NO                 ,
                                          ENGINE_NO                ,
                                          NO_OF_CYLINDERS          ,
                                          YEAR_OF_MAKE             ,
                                          SEATING_CAPACITY         ,
                                          SI                       ,
                                          RATE                     ,
                                          BASIC_PREM               ,
                                          TOTAL_PREM               ,
                                          NET_PREM                 ,
                                          ADD_PREM                 ,
                                          DISCOUNT                 ,
                                          DEPRECIATION             ,
                                          CHASSIS_NO               ,
                                          REMARKS                  ,
                                          ADDRESS                  ,
                                          BUS_LOCATION             ,
                                          VEHICLE_COLOR            ,
                                          DEDUCTABLE               ,
                                          ENGINE_CAPACITY          ,
                                          PER_ACC_DRV              ,
                                          PAD_COVER_PCNT           ,
                                          PAD_COVER_AMT            ,
                                          PER_ACC_DRV_PASS         ,
                                          PADP_COVER_PCNT          ,
                                          PADP_COVER_AMT           ,
                                          AGENCY_REPAIR            ,
                                          ER_COVER_PCNT            ,
                                          ER_COVER_AMT             ,
                                          CON_NAT                  ,
                                          CN_COVER_PCNT            ,
                                          CN_COVER_AMT             ,
                                          BETWEEB_AGE              ,
                                          BA_COVER_PCNT            ,
                                          BA_COVER_AMT             ,
                                          LESSTHAN_AGE             ,
                                          LA_COVER_PCNT            ,
                                          LA_COVER_AMT             ,
                                          ADJUST_FLAG              ,
                                          CUST_ZIP_CODE            ,
                                          CUST_PO_BOX              ,
                                          DRIVER_NAME              ,
                                          AGENCY_FLAG              ,
                                          USER_ID                  ,
                                          POL_NO                   ,
                                          POL_YEAR                 ,
                                          ENDT_NO                  ,
                                          ENDT_YEAR                ,
                                          DRIVER_BIRTH_DT          ,
                                          DRIVER_IQAMA_NO          ,
                                          DRIVER_LICENSE_TYPE      ,
                                          REF_NO                   ,
                                          BROKER_NO                ,
                                          SOURCE                   ,
                                          POST_FLAG                ,
                                          ENDT_DT                  ,
                                          CLIENT_VOH_TYPE          ,
                                          CLIENT_VOH_YEAR          , 
                                          CLIENT_VOH_NO            ,
                                          AGENT_VOH_TYPE           ,
                                          AGENT_VOH_YEAR           ,
                                          AGENT_VOH_NO             ,
                                          CUST_NO                  ,
                                          AGENT_NO                 ,
                                          AGENT_NAME               ,
                                          AGENT_COMM_AMT           ,
                                          SERVICE_CHARGE           ,
                                          ADD_TAX                  ,
                                          ISSUE_FEE                ,
                                          STAMP_FEE                ,
                                          ICF_FEE                  ,
                                          GATR_PREM                ,
                                          REI_FLAG                 ,
                                          ERR_FLAG                 ,
                                          SEQUENCE_NO              ,
                                          RSA_PROVIDER             ,
                                          BENEFICIARY_NO           ,
                                          CUST_CLASS               ,
                                          DISC_CODE                ,
                                          DISC_PCNT                ,
                                          NCB_FLAG                 ,
                                          NCB_AMT                  ,
                                          LOADING_CODE             ,
                                          LOADING_PCNT             ,
                                          LOADING                  ,
                                          LOAD_AMT                 ,
                                          TARIFF_PKG               ,
                                          ENDO_SERIAL              ,   
                                          VAT_PCNT                 ,
                                          VAT_AMT                  ,
                                          FINAL_TOT_AMT            ,
                                          VAT_COMM_PCNT            ,
                                          VAT_COMM_AMT             ,
                                          VEHICLE_SERIAL           ,
                                          FILE_NO) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    rec = (ts,                  
           result[0],
           result[1],
           result[2],
           result[3],
           result[4],
           result[5],
           ts,
           result[7],
           result[8],
           result[9],
           ts,
           datetime.strptime((((result[11]).__str__()).split(" "))[0], '%Y-%m-%d').strftime('%Y-%m-%d'),
           result[12],
           result[13],
           result[14],
           result[15],
           result[16],
           result[17],
           result[18],
           result[19],
           result[20],
           result[21],
           result[22],
           result[23],
           result[24],
           result[25],
           result[26],
           result[27],
           result[28],
           result[29],
           result[30],
           result[31],
           result[32],
           result[33],
           result[34],
           result[35],
           result[36],
           result[37],
           result[38],
           result[39],
           result[40],
           result[41],
           result[42],
           result[43],
           result[44],
           result[45],
           result[46],
           result[47],
           result[48],
           result[49],
           result[50],
           result[51],
           result[52],
           result[53],
           result[54],
           result[55],
           result[56],
           result[57],
           result[58],
           result[59],
           result[60],
           result[61],
           result[62],
           result[63],
           result[64],
           result[65],
           result[66],
           result[67],
           result[68],
           result[69],
           result[70],
           result[71],
           result[72],
           result[73],
           result[74],
           result[75],
           result[76],
           result[77],
           result[78],
           result[79],
           result[80],
           result[81],
           result[82],
           result[83],
           result[84],
           result[85],
           result[86],
           result[87],
           result[88],
           result[89],
           result[90],
           result[91],
           result[92], 
           result[93],
           result[94],
           result[95],
           result[96],
           result[97],
           result[98],
           result[99],
           result[100],
           result[101],
           result[102],
           result[103],
           result[104],
           result[105],
           result[106],
           result[107],
           result[108],
           result[109],
           result[110],
           result[111],
           result[112],
           result[113],
           result[114],
           result[115],
           result[116],
           result[117],
           result[118],
           result[119],
           result[120],
           result[121],
           result[122],   
           result[123],
           result[124],
           result[125],
           result[126],
           result[127],
           result[128],
           result[129])

    mysqlcur.execute(sqlFormula, rec)
    mysqldb.commit()
    mysqldb.close()

    print("Finished processing insert.")    
    cur.close()
    con.close()

    get_schedule_data(pol_no,pol_year,2,10)

def get_pol_type(pol_type):
    con = cx_Oracle.connect('GENCDE/xxxxxxxx@xx.xx.xx.xx/amandb')
    cur = con.cursor()
    cur.execute("""SELECT GENCDE.get_sys_desc_web (29,""" + "'" + str(pol_type) + "'" + """, 2) from DUAL""")               
    result = cur.fetchall()
    cur.close()
    con.close()
    return result[0][0]

def get_body_type(body_type):
    con = cx_Oracle.connect('GENCDE/xxxxxxxx@xx.xx.xx.xx/amandb')
    cur = con.cursor()
    cur.execute("""SELECT GENCDE.get_sys_desc_web (103,""" + "'" + str(body_type) + "'" + """, 2) from DUAL""")           
    result = cur.fetchall()
    cur.close()
    con.close()
    return result[0][0]

def get_veh_make(make):
    con = cx_Oracle.connect('GENCDE/xxxxxxxx@xx.xx.xx.xx/amandb')
    cur = con.cursor()
    cur.execute("""SELECT GENCDE.get_sys_desc_web (101,""" + "'" + str(make) + "'" + """, 1) from DUAL""")               
    result = cur.fetchall()
    cur.close()
    con.close()    
    return result[0][0]

def get_veh_model(model):
    con = cx_Oracle.connect('GENCDE/xxxxxxxx@xx.xx.xx.xx/amandb')
    cur = con.cursor()
    cur.execute("""SELECT GENCDE.get_sys_desc_web (110,""" + "'" + str(model) + "'" + """, 1) from DUAL""")               
    result = cur.fetchall()
    cur.close()
    con.close()    
    return result[0][0]

def check_for_claims(pol_no,pol_year,pol_type,uw_year,cust_no): 
    con = cx_Oracle.connect('GENCDE/xxxxxxxx@xx.xx.xx.xx/amandb')
    cur = con.cursor()
    
    mg_ecar_branch                        = 1                          
    mg_ecar_office                        = 1                     
    mg_ecar_pol_no                        = pol_no             
    mg_ecar_pol_year                      = pol_year           
    mg_ecar_class_of_business             = 1                                           
    mg_ecar_policy_type                   = pol_type
    mg_uw_year                            = uw_year
    mg_cust_no                            = cust_no
    mg_ecar_client                        = cur.var(int)    
    mg_no_of_clm                          = cur.var(int)
    mg_tot_incurred                       = cur.var(int)
    mg_tot_loss_flag                      = cur.var(int)
    
    result = cur.callproc('WEB_INSERT_DIRECT_AMAN.chk_no_of_claims',
        [mg_ecar_branch, 
        mg_ecar_office,
        mg_ecar_pol_no,
        mg_ecar_pol_year,
        mg_ecar_class_of_business,
        mg_ecar_policy_type,
        mg_uw_year,
        mg_cust_no,
        mg_ecar_client,
        mg_no_of_clm,
        mg_tot_incurred,
        mg_tot_loss_flag])  
    cur.close()
    con.close()          
    print(tuple(result))

def get_all_endt(pol_no,pol_year):
    con = cx_Oracle.connect('GENCDE/xxxxxxxx@xx.xx.xx.xx/amandb')
    cur = con.cursor()
    cur.execute("""SELECT ECAR_ENDT_NO,
                          ECAR_YEAR,
                          ECAR_ENDT_TYPE,
                          ECAR_TRN_TYPE,
                          ECAR_POL_NO,
                          ECAR_POL_YEAR,
                          GENCDE.get_sys_desc_web (29, ECAR_POLICY_TYPE, 2), 
                          ECAR_SOURCE,
                          ECAR_ENDT_DT,
                          ECAR_INS_ST_DT,
                          ECAR_INS_ED_DT,
                          ECAR_UW_YEAR,
                          ECAR_CLIENT,
                          ECAR_CLIENT_NAME,
                          ECAR_CUST_NO,
                          ECAR_CUST_NAME,
                          ECAR_NET_PREM,
                          ECAR_DISCOUNTS,
                          ECAR_LOADINGS,
                          ECAR_GATR_PREM RSA,
                          ECAR_ISSUE_FEE,
                          ECAR_TOTAL_PREM,
                          nvl(ECAR_VAT_AMT,0) VAT_Amount,
                          nvl (ECAR_FINAL_TOTAL,ECAR_TOTAL_PREM) Final_Total,
                          nvl(decode(nvl(ecar_si,ocar_si),0,ocar_si,ecar_si),0) si
                     FROM carcde.car_ins_endt
                    WHERE ECAR_POL_NO= """ + "'" + str(pol_no) + "'" + """
                      AND ECAR_POL_YEAR = """ + "'" + str(pol_year) + "'" + """
                      AND ECAR_POST_FLAG > 0
                    ORDER BY ECAR_ENDT_DT DESC """)               
    result = cur.fetchall()
    i = 0
    mysqldb = mydb()
    for row in result:        
        time_tuple = time.localtime()
        ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)        
        mycursor = mysqldb.cursor()
        sql0 = """SELECT * FROM all_endts WHERE endt_no=""" + str(result[i][0]) + """ AND endt_year=""" + str(result[i][1])
        mycursor.execute(sql0)
        check0 = mycursor.fetchall()
        if check0 == []:
            sql = """INSERT INTO all_endts (timestamp      ,     
                                            endt_no        ,               
                                            endt_year      ,  
                                            endt_type      ,
                                            endt_trans     ,
                                            pol_no         ,               
                                            pol_year       ,  
                                            pol_type       , 
                                            source         ,
                                            endt_dt        ,
                                            ins_st         ,
                                            ins_ed         ,
                                            uw_year        ,
                                            client_no      ,
                                            client_name    ,
                                            cust_no        ,
                                            cust_name      ,
                                            net_prem       ,
                                            discounts      ,
                                            loadings       ,
                                            rsa_prem       ,
                                            issue_fee      ,
                                            total_prem     ,
                                            vat_amount     ,
                                            final_total    ,
                                            si) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                    %s, %s, %s, %s, %s, %s)"""        
            rec = (ts, 
                result[i][0], 
                result[i][1], 
                result[i][2],
                result[i][3],
                result[i][4],
                result[i][5],                      
                result[i][6], 
                result[i][7], 
                datetime.strptime((((result[i][8]).__str__()).split(" "))[0], '%Y-%m-%d').strftime('%Y-%m-%d'),
                datetime.strptime((((result[i][9]).__str__()).split(" "))[0], '%Y-%m-%d').strftime('%Y-%m-%d'),
                datetime.strptime((((result[i][10]).__str__()).split(" "))[0], '%Y-%m-%d').strftime('%Y-%m-%d'),
                result[i][11], 
                result[i][12], 
                result[i][13].rstrip(), 
                result[i][14],
                result[i][15], 
                result[i][16],
                result[i][17],
                result[i][18],
                result[i][19],
                result[i][20],
                result[i][21],
                result[i][22],
                result[i][23],
                result[i][24])

            try:
                mycursor.execute(sql, rec)
                mysqldb.commit()
            except:
                print("Some errors during records insert in pol_details table under get_all_endt()!")

        i = i+1
    mysqldb.close()
    cur.close()
    con.close()    

def get_endt_data(endt_no,endt_year,endt_type):                 
    mysqldb = mydb()
    mycursor = mysqldb.cursor()   
    sql =  """SELECT * FROM endt_details 
                WHERE endt_no=""" + str(endt_no) + """
                  AND endt_year=""" + str(endt_year)
    mycursor.execute(sql)
    check = mycursor.fetchall()
    mysqldb.close()   

    if check == []:
        con = cx_Oracle.connect('GENCDE/xxxxxxxx@xx.xx.xx.xx/amandb')
        cur = con.cursor()
        
        user_id                               = 'WebAdmin'
        mg_ecar_endt_no                       = endt_no             
        mg_ecar_year                          = endt_year           
        mg_ecar_class_of_business             = 1           
        mg_ecar_endt_type                     = endt_type                   
        mg_ecar_office                        = 1                     
        mg_ecar_branch                        = 1                                   
        mg_ecar_policy_type                   = cur.var(int)
        mg_ecar_endt_dt                       = cur.var(datetime)
        mg_ecar_client                        = cur.var(int)
        mg_ecar_client_name                   = cur.var(str)
        mg_ecar_cust_name                     = cur.var(str)
        mg_ecar_cust_tel_no                   = cur.var(str)
        mg_ecar_cust_address                  = cur.var(str)
        mg_ecar_agent_no                      = cur.var(int)
        mg_ecar_agent_comm                    = cur.var(int)
        mg_ecar_agent_comm_amt                = cur.var(int)
        mg_ecar_ins_st_dt                     = cur.var(datetime) 
        mg_ecar_ins_ed_dt                     = cur.var(datetime) 
        mg_ecar_endt_st_dt                    = cur.var(datetime) 
        mg_ecar_si                            = cur.var(int)
        mg_ecar_rate                          = cur.var(int)
        mg_ecar_gross_prem                    = cur.var(int)
        mg_ecar_discounts                     = cur.var(int)
        mg_ecar_add_prem                      = cur.var(int)
        mg_ecar_remarks                       = cur.var(str)
        mg_ecar_total_prem                    = cur.var(int)
        mg_ecar_cust_job                      = cur.var(int)
        mg_ecar_client_aname                  = cur.var(str)
        mg_ecar_cust_aname                    = cur.var(str)
        mg_ecar_cust_birth_dt                 = cur.var(datetime) 
        mg_ecar_hijri_st_dt                   = cur.var(str)
        mg_ecar_hijri_ed_dt                   = cur.var(str)
        mg_ecar_pol_hijri_st_dt               = cur.var(str)
        mg_ecar_bus_location                  = cur.var(int)
        mg_ecar_cust_id_no                    = cur.var(str)
        mg_ecar_cust_nationality              = cur.var(int)
        mg_ecar_cust_city                     = cur.var(int)
        mg_ecar_cust_tel                      = cur.var(str)
        mg_ecar_cust_mobile                   = cur.var(str)
        mg_ecar_cust_zimg_code                = cur.var(str)
        mg_ecar_cust_po_box                   = cur.var(str)
        mg_evcl_vehicle_make                  = cur.var(int)
        mg_evcl_vehicle_model                 = cur.var(int)
        mg_evcl_type_of_body                  = cur.var(int)
        mg_evcl_plate_type                    = cur.var(int)
        mg_evcl_class_of_use                  = cur.var(int)
        mg_evcl_vehicle_color                 = cur.var(int)
        mg_evcl_chassis_no                    = cur.var(str)
        mg_evcl_year_of_make                  = cur.var(int)
        mg_evcl_no_of_cylender                = cur.var(int)
        mg_evcl_registration_no               = cur.var(str)
        mg_evcl_seat_capacity                 = cur.var(int)
        mg_evcl_depreciation                  = cur.var(int)
        mg_evcl_deductable                    = cur.var(int)
        mg_evcl_engine_capacity               = cur.var(int)
        mg_evcl_engine_no                     = cur.var(str)
        mg_ecar_adjust_flag                   = cur.var(int)
        mg_ecar_payment_term                  = cur.var(int)
        mg_evcl_sequence_no                   = cur.var(int)
        mg_evcl_ref_no                        = cur.var(str)
        mg_ecar_issue_fee                     = cur.var(int)
        mg_ecar_service_charge                = cur.var(int)
        mg_evcl_add_driver_name               = cur.var(str)
        mg_evcl_add_driver_license_type       = cur.var(int)
        mg_evcl_add_driver_birth_dt           = cur.var(datetime) 
        mg_evcl_custom_id                     = cur.var(int)
        mg_evcl_add_driver_iqama_no           = cur.var(str)
        mg_ecar_status                        = cur.var(int)
        mg_rsa_provider                       = cur.var(int)
        mg_beneficiary_no                     = cur.var(int)
        mg_cust_class                         = cur.var(int)
        mg_client_voh_no                      = cur.var(int)
        mg_client_voh_year                    = cur.var(int)
        mg_client_voh_type                    = cur.var(int)
        mg_agent_voh_no                       = cur.var(int)
        mg_agent_voh_year                     = cur.var(int)
        mg_agent_voh_type                     = cur.var(int)
        mg_gatr_prem                          = cur.var(int)
        mg_loading                            = cur.var(int)
        mg_no_of_clm                          = cur.var(int)
        mg_tot_incurred                       = cur.var(int)
        mg_tariff_pkg                         = cur.var(int)
        mg_user_name                          = cur.var(str)
        mg_endo_serial                        = cur.var(int)
        mg_vat_pcnt                           = cur.var(int)
        mg_vat_amt                            = cur.var(int)
        mg_final_tot_amt                      = cur.var(int)
        mg_vat_comm_pcnt                      = cur.var(int)
        mg_vat_comm_amt                       = cur.var(int)
        mg_file_no                            = cur.var(str)    
        
        result = cur.callproc('WEB_INSERT_DIRECT_AMAN.get_endt_data',
            [user_id, 
            mg_ecar_endt_no,
            mg_ecar_year,
            mg_ecar_class_of_business,
            mg_ecar_endt_type,
            mg_ecar_office,
            mg_ecar_branch,
            mg_ecar_policy_type,
            mg_ecar_endt_dt,
            mg_ecar_client,
            mg_ecar_client_name,
            mg_ecar_cust_name,
            mg_ecar_cust_tel_no,
            mg_ecar_cust_address,
            mg_ecar_agent_no,
            mg_ecar_agent_comm,
            mg_ecar_agent_comm_amt,
            mg_ecar_ins_st_dt,
            mg_ecar_ins_ed_dt,
            mg_ecar_endt_st_dt,
            mg_ecar_si,
            mg_ecar_rate,
            mg_ecar_gross_prem,
            mg_ecar_discounts,
            mg_ecar_add_prem,
            mg_ecar_remarks,
            mg_ecar_total_prem,
            mg_ecar_cust_job,
            mg_ecar_client_aname,
            mg_ecar_cust_aname,
            mg_ecar_cust_birth_dt,
            mg_ecar_hijri_st_dt,
            mg_ecar_hijri_ed_dt,
            mg_ecar_pol_hijri_st_dt,
            mg_ecar_bus_location,
            mg_ecar_cust_id_no,
            mg_ecar_cust_nationality,
            mg_ecar_cust_city,
            mg_ecar_cust_tel,
            mg_ecar_cust_mobile,
            mg_ecar_cust_zimg_code,
            mg_ecar_cust_po_box,
            mg_evcl_vehicle_make,
            mg_evcl_vehicle_model,
            mg_evcl_type_of_body,
            mg_evcl_plate_type,
            mg_evcl_class_of_use,
            mg_evcl_vehicle_color,
            mg_evcl_chassis_no,
            mg_evcl_year_of_make,
            mg_evcl_no_of_cylender,
            mg_evcl_registration_no,
            mg_evcl_seat_capacity,
            mg_evcl_depreciation,
            mg_evcl_deductable,
            mg_evcl_engine_capacity,
            mg_evcl_engine_no,
            mg_ecar_adjust_flag,
            mg_ecar_payment_term,
            mg_evcl_sequence_no,
            mg_evcl_ref_no,
            mg_ecar_issue_fee,
            mg_ecar_service_charge,
            mg_evcl_add_driver_name,
            mg_evcl_add_driver_license_type,
            mg_evcl_add_driver_birth_dt,
            mg_evcl_custom_id,
            mg_evcl_add_driver_iqama_no,
            mg_ecar_status,
            mg_rsa_provider,
            mg_beneficiary_no,
            mg_cust_class,
            mg_client_voh_no,
            mg_client_voh_year,
            mg_client_voh_type,
            mg_agent_voh_no,
            mg_agent_voh_year,
            mg_agent_voh_type,
            mg_gatr_prem,
            mg_loading,
            mg_no_of_clm,
            mg_tot_incurred,
            mg_tariff_pkg,
            mg_user_name,
            mg_endo_serial,
            mg_vat_pcnt,
            mg_vat_amt,
            mg_final_tot_amt,
            mg_vat_comm_pcnt,
            mg_vat_comm_amt,
            mg_file_no])        
			
        try:
            if result[65] != None:
                driver_age = datetime.strptime((((result[65]).__str__()).split(" "))[0], '%Y-%m-%d').strftime('%Y-%m-%d'),
            else:
                driver_age = None
        except:
            driver_age = None

        time_tuple = time.localtime()
        ts = time.strftime("%Y-%m-%d %H:%M:%S",time_tuple)
        mysqldb = mydb()
        mycursor = mysqldb.cursor()
        sql = """INSERT INTO endt_details (timestamp,
                                        endt_no,
                                        endt_year,
                                        class_of_business,
                                        endt_type,
                                        office,
                                        branch,
                                        pol_type,
                                        endt_dt,
                                        client_no,
                                        client_name,
                                        cust_name,
                                        cust_tel_no,
                                        cust_address,
                                        agent_no,
                                        comm,
                                        comm_amt,
                                        ins_st,
                                        ins_ed,
                                        endt_st_dt,
                                        si,
                                        rate,
                                        gross_prem,
                                        discounts,
                                        add_prem,
                                        remarks,
                                        total_prem,
                                        cust_job,
                                        client_aname,
                                        cust_aname,
                                        cust_birth_dt,
                                        hijri_st_dt,
                                        hijri_ed_dt,
                                        pol_hijri_st_dt,
                                        bus_location,
                                        cust_id_no,
                                        cust_nationality,
                                        cust_city,
                                        cust_tel,
                                        cust_mobile,
                                        cust_zimg_code,
                                        cust_po_box,
                                        vehicle_make,
                                        vehicle_model,
                                        type_of_body,
                                        plate_type,
                                        class_of_use,
                                        vehicle_color,
                                        chassis_no,
                                        year_of_make,
                                        no_of_cylender,
                                        registration_no,
                                        seat_capacity,
                                        depreciation,
                                        deductable,
                                        engine_capacity,
                                        engine_no,
                                        adjust_flag,
                                        payment_term,
                                        sequence_no,
                                        ref_no,
                                        issue_fee,
                                        service_charge,
                                        add_driver_name,
                                        add_driver_license_type,
                                        add_driver_birth_dt,
                                        custom_id,
                                        add_driver_iqama_no,
                                        status,
                                        rsa_provider,
                                        beneficiary_no,
                                        cust_class,
                                        client_voh_no,
                                        client_voh_year,
                                        client_voh_type,
                                        agent_voh_no,
                                        agent_voh_year,
                                        agent_voh_type,
                                        rsa_prem,
                                        loading,
                                        no_of_clm,
                                        tot_incurred,
                                        tariff_pkg,
                                        user_name,
                                        endo_serial,
                                        vat_pcnt,
                                        vat_amt,
                                        final_tot_amt,
                                        vat_comm_pcnt,
                                        vat_comm_amt,
                                        file_no) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        rec = (ts,
            result[1],
            result[2],
            result[3],
            result[4],
            result[5],
            result[6],
            result[7],
            datetime.strptime((((result[8]).__str__()).split(" "))[0], '%Y-%m-%d').strftime('%Y-%m-%d'),
            result[9],
            result[10].rstrip(),
            result[11],
            result[12],
            result[13],
            result[14],
            result[15],
            result[16],
            datetime.strptime((((result[17]).__str__()).split(" "))[0], '%Y-%m-%d').strftime('%Y-%m-%d'),
            datetime.strptime((((result[18]).__str__()).split(" "))[0], '%Y-%m-%d').strftime('%Y-%m-%d'),
            datetime.strptime((((result[19]).__str__()).split(" "))[0], '%Y-%m-%d').strftime('%Y-%m-%d'),
            result[20],
            result[21],
            result[22],
            result[23],
            result[24],
            result[25],
            result[26],
            result[27],
            result[28].rstrip(),
            result[29],
            datetime.strptime((((result[30]).__str__()).split(" "))[0], '%Y-%m-%d').strftime('%Y-%m-%d'),
            None,
            None,
            None,
            result[34],
            result[35],
            result[36],
            result[37],
            result[38],
            result[39],
            result[40],
            result[41],
            result[42],
            result[43],
            result[44],
            result[45],
            result[46],
            result[47],
            result[48],
            result[49],
            result[50],
            result[51],
            result[52],
            result[53],
            result[54],
            result[55],
            result[56],
            result[57],
            result[58],
            result[59],
            result[60],
            result[61],
            result[62],
            result[63],
            result[64],
            driver_age,
            result[66],
            result[67],
            result[68],
            result[69],
            result[70],
            result[71],
            result[72],
            result[73],
            result[74],
            result[75],
            result[76],
            result[77],
            result[78],
            result[79],
            result[80],
            result[81],
            result[82],
            result[83],
            result[84],
            result[85],
            result[86],
            result[87],
            result[88],
            result[89],
            result[90])

        try:
            mycursor.execute(sql, rec)
            mysqldb.commit()
        except:
            print("Some errors during records insert in endt_details table!")

        mysqldb.close()

        cur.close()
        con.close()

def get_input_data(policy_no,policy_year):                      
    con = cx_Oracle.connect('GENCDE/xxxxxxxx@xx.xx.xx.xx/amandb')
    cur = con.cursor()
    p_policy_no = policy_no
    p_policy_year = policy_year
    cur.execute("""SELECT VUW_OFFICE,VUW_CLASS_DESC,VUW_POL_TYPE_DESC,3 endt_type,3 trans_type,trunc(sysdate),1,NULL,NULL,VUW_REN_DT,VUW_EXP_DT,
                          VUW_VCAR_CUST_NO,VUW_CLIENT,VUW_CLIENT,VUW_INSURED,
                          Null,
                          Null,
                          0,
                          0,
                          Null,   
                          Null,
                          Null,
                          Null,
                          Null,
                          Null,
                          Null,
                          Null,
                          Null,
                          VUW_VEHICLE_MAKE,
                          VUW_VEHICLE_MODEL,
                          VUW_VEHICLE_TYPE,
                          1,        -- plate type
                          Null,
                          1,        -- class of use
                          VUW_REGISTRATION_NO,
                          Null,
                          Null,
                          VUW_VEHICLE_YEAR,
                          VUW_NO_OF_PASSENGERS,
                          VUW_REN_SI,
                          2.0, --rate
                          VUW_REN_NET_PREM,
                          VUW_REN_TOT_PREM,
                          VUW_REN_NET_PREM,
                          0,        
                          0,
                          Null,     --  depreciation
                          VUW_CHASSIS_NO,
                          'Renewal Remarks',      -- remarks
                          Null,
                          1,        -- business location
                          Null,   
                          VUW_DEDUCTIBLE,
                          VUW_ENGINE_CC,
                          0,
                          0,
                          0,
                          0,
                          0,
                          0,
                          2,      --  agency repair
                          0,
                          0,
                          0,
                          0,
                          0,
                          0,
                          0,
                          0,
                          0,
                          0,
                          0,
                          0,
                          Null,
                          Null,
                          VUW_INSURED,
                          2,    --  agency flag
                          'WebAdmin',    -- user id
                          VUW_POLICY_NO,
                          VUW_POLICY_YEAR,
                          Null,
                          Null,
                          Null,
                          Null,
                          0,      -- broker no.
                          1,      -- source
                          VUW_VCAR_CUST_NO,
                          0,      -- agent no.
                          Null,   -- agnet name
                          0,    
                          0,
                          0,
                          0,
                          0,
                          0,
                          VUW_RSA_AMT,
                          Null,
                          VUW_RSA_PROVIDER,
                          VUW_JOINT_NAME,   -- mortgage
                          Null,
                          0,
                          0,
                          1,    -- NCB years
                          0,
                          0,
                          0,
                          0,
                          0,
                          VUW_VEHICLE_TARIFF       
                     FROM GENCDE.VPLN_UW_VIEW_SMS
                    WHERE VUW_POLICY_NO = """ + "'" + p_policy_no + "'" + """
                      And VUW_POLICY_YEAR = """ + "'" + p_policy_year + "'")               
    result = cur.fetchall()
    print(tuple(result))
    cur.close()
    con.close()

def insert_endt_web(policy_type,
                    eff_date,
                    exp_date,
                    client_code,
                    client_ename,
                    client_aname,
                    insured_ename,
                    agent_no,
                    comm,
                    comm_amount,
                    vehicle_make,
                    vehicle_model,
                    type_of_body,
                    plate_type,
                    class_of_use,
                    registration_no,
                    year_of_make,
                    seating_capacity,
                    SI,
                    rate,
                    basic_prem,
                    total_prem,
                    net_prem,
                    chassis_no,
                    renewal_remarks,
                    deductable,
                    engine_capacity,
                    driver_name,
                    pol_no,
                    pol_year,
                    cust_no,
                    rsa_prem,
                    rsa_provider,
                    tariff,
                    vat_pcnt,
                    vat_amt,
                    final_tot_amt,
                    cpr,
                    address): 
    con = cx_Oracle.connect('GENCDE/xxxxxxxx@xx.xx.xx.xx/amandb')
    cur = con.cursor()
    cur.execute("""ALTER SESSION SET NLS_DATE_FORMAT = 'DD/MM/YYYY'""")
    
    P_BRANCH                     = 1
    P_OFFICE                     = 1
    P_CLASS_OF_BUSINESS          = 1
    P_POLICY_TYPE                = policy_type
    P_ENDT_TYPE                  = 3                                    
    P_TRN_TYPE                   = 3
    P_ISSUE_DATE                 = (datetime.now()).strftime("%d/%m/%Y")        
    P_PAYMENT_MODE               = 1
    P_HIJRI_EFF_DATE             = None             
    P_HIJRI_EXP_DATE             = None
    P_EFF_DATE                   = eff_date 
    P_EXP_DATE                   = exp_date 
    P_CLIENT_CODE                = client_code
    P_CLIENT_ENAME               = client_ename
    P_CLIENT_ANAME               = client_aname
    P_INSURED_ENAME              = insured_ename
    P_INSURED_ANAME              = None                 
    P_BROKER                     = agent_no                                
    P_BROKER_COMM_PCNT           = comm                                    
    P_BROKER_COMM_AMT            = comm_amount                             
    P_ID_NO                      = cpr
    P_OCCUPATION                 = None
    P_NATIONALITY                = None
    P_CITY                       = None
    P_HOME_TEL                   = None
    P_OFFICE_TEL                 = None
    P_MOBILE                     = None
    P_DOB                        = None
    P_AGE                        = None
    P_VEHICLE_MAKE               = vehicle_make
    P_VEHICLE_MODEL              = vehicle_model
    P_TYPE_OF_BODY               = type_of_body
    P_PLATE_TYPE                 = plate_type
    P_EVCL_CUSTOM_ID             = None
    P_CLASS_OF_USE               = class_of_use
    P_PLATE_NO                   = registration_no
    P_ENGINE_NO                  = None
    P_NO_OF_CYLINDERS            = None
    P_YEAR_OF_MAKE               = year_of_make
    P_SEATING_CAPACITY           = seating_capacity
    P_SI                         = SI
    P_RATE                       = rate
    P_BASIC_PREM                 = basic_prem
    P_TOTAL_PREM                 = total_prem
    P_NET_PREM                   = net_prem
    P_ADD_PREM                   = 0
    P_DISCOUNT                   = 0
    P_DEPRECIATION               = None
    P_CHASSIS_NO                 = chassis_no
    P_REMARKS                    = renewal_remarks
    P_ADDRESS                    = address
    P_BUS_LOCATION               = 1
    P_VEHICLE_COLOR              = None
    P_DEDUCTABLE                 = deductable
    P_ENGINE_CAPACITY            = engine_capacity
    P_PER_ACC_DRV                = 0
    P_PAD_COVER_PCNT             = 0
    P_PAD_COVER_AMT              = 0
    P_PER_ACC_DRV_PASS           = 0
    P_PADP_COVER_PCNT            = 0
    P_PADP_COVER_AMT             = 0
    P_AGENCY_REPAIR              = 2                
    P_ER_COVER_PCNT              = 0
    P_ER_COVER_AMT               = 0
    P_CON_NAT                    = 0
    P_CN_COVER_PCNT              = 0
    P_CN_COVER_AMT               = 0
    P_BETWEEB_AGE                = 0
    P_BA_COVER_PCNT              = 0
    P_BA_COVER_AMT               = 0
    P_LESSTHAN_AGE               = 0
    P_LA_COVER_PCNT              = 0
    P_LA_COVER_AMT               = 0
    P_ADJUST_FLAG                = 0
    P_CUST_ZIP_CODE              = None
    P_CUST_PO_BOX                = None
    P_DRIVER_NAME                = driver_name
    P_AGENCY_FLAG                = 2
    P_USER_ID                    = 'WebAdmin'
    P_POL_NO                     = pol_no
    P_POL_YEAR                   = pol_year
    P_ENDT_NO                    = cur.var(int)
    P_YEAR                       = cur.var(int)
    P_DRIVER_BIRTH_DT            = None
    P_DRIVER_IQAMA_NO            = None
    P_DRIVER_LICENSE_TYPE        = None
    P_REF_NO                     = None
    P_BROKER_NO                  = 0
    P_SOURCE                     = 1
    P_POST_FLAG                  = cur.var(int)
    P_ENDT_DT                    = cur.var(datetime) 
    P_CLIENT_VOH_TYPE            = cur.var(int)
    P_CLIENT_VOH_YEAR            = cur.var(int)
    P_CLIENT_VOH_NO              = cur.var(int)
    P_AGENT_VOH_TYPE             = cur.var(int)
    P_AGENT_VOH_YEAR             = cur.var(int)
    P_AGENT_VOH_NO               = cur.var(int)
    P_CUST_NO                    = client_code 
    P_AGENT_NO                   = 0
    P_AGENT_NAME                 = None
    P_AGENT_COMM_AMT             = 0
    P_SERVICE_CHARGE             = 0
    P_ADD_TAX                    = 0
    P_ISSUE_FEE                  = 0
    P_STAMP_FEE                  = 0
    P_ICF_FEE                    = 0
    P_GATR_PREM                  = rsa_prem
    P_REI_FLAG                   = cur.var(int)
    P_ERR_FLAG                   = cur.var(int)
    P_SEQUENCE_NO                = None
    p_rsa_provider               = rsa_provider
    p_beneficiary_no             = None
    p_cust_class                 = None
    p_disc_code                  = 0
    p_disc_pcnt                  = 0
    p_ncb_flag                   = 1
    p_ncb_amt                    = 0
    p_loading_code               = 0
    p_loading_pcnt               = 0
    p_loading                    = 0
    p_load_amt                   = 0                                                        
    p_tariff_pkg                 = tariff
    p_endo_serial                = cur.var(int)
    p_vat_pcnt                   = vat_pcnt
    p_vat_amt                    = vat_amt
    p_final_tot_amt              = final_tot_amt
    p_vat_comm_pcnt              = 0                                                        
    p_vat_comm_amt               = 0                                                        
    P_ecar_vehicle_serial        = cur.var(int)
    p_file_no                    = None
    print("Pre-insert")
    result = cur.callproc('WEB_INSERT_DIRECT_AMAN.insert_endt_web',
        [P_BRANCH,
        P_OFFICE                ,
        P_CLASS_OF_BUSINESS     ,
        P_POLICY_TYPE           ,
        P_ENDT_TYPE             ,
        P_TRN_TYPE              ,
        P_ISSUE_DATE            ,
        P_PAYMENT_MODE          ,
        P_HIJRI_EFF_DATE        ,
        P_HIJRI_EXP_DATE        ,
        P_EFF_DATE              ,
        P_EXP_DATE              ,
        P_CLIENT_CODE           ,
        P_CLIENT_ENAME          ,
        P_CLIENT_ANAME          ,
        P_INSURED_ENAME         ,
        P_INSURED_ANAME         ,
        P_BROKER                ,
        P_BROKER_COMM_PCNT      ,
        P_BROKER_COMM_AMT       ,
        P_ID_NO                 ,
        P_OCCUPATION            ,
        P_NATIONALITY           ,
        P_CITY                  ,
        P_HOME_TEL              ,
        P_OFFICE_TEL            ,
        P_MOBILE                ,
        P_DOB                   ,
        P_AGE                   ,
        P_VEHICLE_MAKE          ,
        P_VEHICLE_MODEL         ,
        P_TYPE_OF_BODY          ,
        P_PLATE_TYPE            ,
        P_EVCL_CUSTOM_ID        ,
        P_CLASS_OF_USE          ,
        P_PLATE_NO              ,
        P_ENGINE_NO             ,
        P_NO_OF_CYLINDERS       ,
        P_YEAR_OF_MAKE          ,
        P_SEATING_CAPACITY      ,
        P_SI                    ,
        P_RATE                  ,
        P_BASIC_PREM            ,
        P_TOTAL_PREM            ,
        P_NET_PREM              ,
        P_ADD_PREM              ,
        P_DISCOUNT              ,
        P_DEPRECIATION          ,
        P_CHASSIS_NO            ,
        P_REMARKS               ,
        P_ADDRESS               ,
        P_BUS_LOCATION          ,
        P_VEHICLE_COLOR         ,
        P_DEDUCTABLE            ,
        P_ENGINE_CAPACITY       ,
        P_PER_ACC_DRV           ,
        P_PAD_COVER_PCNT        ,
        P_PAD_COVER_AMT         ,
        P_PER_ACC_DRV_PASS      ,
        P_PADP_COVER_PCNT       ,
        P_PADP_COVER_AMT        ,
        P_AGENCY_REPAIR         ,
        P_ER_COVER_PCNT         ,
        P_ER_COVER_AMT          ,
        P_CON_NAT               ,
        P_CN_COVER_PCNT         ,
        P_CN_COVER_AMT          ,
        P_BETWEEB_AGE           ,
        P_BA_COVER_PCNT         ,
        P_BA_COVER_AMT          ,
        P_LESSTHAN_AGE          ,
        P_LA_COVER_PCNT         ,
        P_LA_COVER_AMT          ,
        P_ADJUST_FLAG           ,
        P_CUST_ZIP_CODE         ,
        P_CUST_PO_BOX           ,
        P_DRIVER_NAME           ,
        P_AGENCY_FLAG           ,
        P_USER_ID               ,
        P_POL_NO                ,
        P_POL_YEAR              ,
        P_ENDT_NO               ,
        P_YEAR                  ,
        P_DRIVER_BIRTH_DT       ,
        P_DRIVER_IQAMA_NO       ,
        P_DRIVER_LICENSE_TYPE   ,
        P_REF_NO                ,
        P_BROKER_NO             ,
        P_SOURCE                ,
        P_POST_FLAG             ,
        P_ENDT_DT               ,
        P_CLIENT_VOH_TYPE       ,
        P_CLIENT_VOH_YEAR       ,
        P_CLIENT_VOH_NO         ,
        P_AGENT_VOH_TYPE        ,
        P_AGENT_VOH_YEAR        ,
        P_AGENT_VOH_NO          ,
        P_CUST_NO               ,
        P_AGENT_NO              ,
        P_AGENT_NAME            ,
        P_AGENT_COMM_AMT        ,
        P_SERVICE_CHARGE        ,
        P_ADD_TAX               ,
        P_ISSUE_FEE             ,
        P_STAMP_FEE             ,
        P_ICF_FEE               ,
        P_GATR_PREM             ,
        P_REI_FLAG              ,
        P_ERR_FLAG              ,
        P_SEQUENCE_NO           ,
        p_rsa_provider          ,
        p_beneficiary_no        ,
        p_cust_class            ,
        p_disc_code             ,
        p_disc_pcnt             ,
        p_ncb_flag              ,
        p_ncb_amt               ,
        p_loading_code          ,
        p_loading_pcnt          ,
        p_loading               ,
        p_load_amt              ,
        p_tariff_pkg            ,
        p_endo_serial           , 
        p_vat_pcnt              ,
        p_vat_amt               ,
        p_final_tot_amt         ,
        p_vat_comm_pcnt         ,
        p_vat_comm_amt          ,
        P_ecar_vehicle_serial   ,
        p_file_no])        
    print("result: ",tuple(result))

    if result[50] != None:
        addr = result[50].rstrip()
    else:
        addr = result[50]

    time_tuple = time.localtime()
    ts = time.strftime("%Y-%m-%d",time_tuple)
    mysqldb = mydb()
    mysqlcur = mysqldb.cursor()
    sqlFormula = """INSERT INTO renewals (timestamp                 ,                  
                                          BRANCH                   ,
                                          OFFICE                   ,
                                          CLASS_OF_BUSINESS        ,
                                          POLICY_TYPE              ,
                                          ENDT_TYPE                ,
                                          TRN_TYPE                 ,
                                          ISSUE_DATE               ,
                                          PAYMENT_MODE             ,
                                          HIJRI_EFF_DATE           ,
                                          HIJRI_EXP_DATE           ,
                                          EFF_DATE                 ,
                                          EXP_DATE                 ,
                                          CLIENT_CODE              ,
                                          CLIENT_ENAME             ,
                                          CLIENT_ANAME             ,
                                          INSURED_ENAME            ,
                                          INSURED_ANAME            ,
                                          BROKER                   ,
                                          BROKER_COMM_PCNT         ,
                                          BROKER_COMM_AMT          ,
                                          ID_NO                    ,
                                          OCCUPATION               ,
                                          NATIONALITY              ,
                                          CITY                     ,
                                          HOME_TEL                 ,
                                          OFFICE_TEL               ,
                                          MOBILE                   ,
                                          DOB                      ,
                                          AGE                      ,
                                          VEHICLE_MAKE             ,
                                          VEHICLE_MODEL            ,
                                          TYPE_OF_BODY             ,
                                          PLATE_TYPE               ,
                                          EVCL_CUSTOM_ID           ,
                                          CLASS_OF_USE             ,
                                          PLATE_NO                 ,
                                          ENGINE_NO                ,
                                          NO_OF_CYLINDERS          ,
                                          YEAR_OF_MAKE             ,
                                          SEATING_CAPACITY         ,
                                          SI                       ,
                                          RATE                     ,
                                          BASIC_PREM               ,
                                          TOTAL_PREM               ,
                                          NET_PREM                 ,
                                          ADD_PREM                 ,
                                          DISCOUNT                 ,
                                          DEPRECIATION             ,
                                          CHASSIS_NO               ,
                                          REMARKS                  ,
                                          ADDRESS                  ,
                                          BUS_LOCATION             ,
                                          VEHICLE_COLOR            ,
                                          DEDUCTABLE               ,
                                          ENGINE_CAPACITY          ,
                                          PER_ACC_DRV              ,
                                          PAD_COVER_PCNT           ,
                                          PAD_COVER_AMT            ,
                                          PER_ACC_DRV_PASS         ,
                                          PADP_COVER_PCNT          ,
                                          PADP_COVER_AMT           ,
                                          AGENCY_REPAIR            ,
                                          ER_COVER_PCNT            ,
                                          ER_COVER_AMT             ,
                                          CON_NAT                  ,
                                          CN_COVER_PCNT            ,
                                          CN_COVER_AMT             ,
                                          BETWEEB_AGE              ,
                                          BA_COVER_PCNT            ,
                                          BA_COVER_AMT             ,
                                          LESSTHAN_AGE             ,
                                          LA_COVER_PCNT            ,
                                          LA_COVER_AMT             ,
                                          ADJUST_FLAG              ,
                                          CUST_ZIP_CODE            ,
                                          CUST_PO_BOX              ,
                                          DRIVER_NAME              ,
                                          AGENCY_FLAG              ,
                                          USER_ID                  ,
                                          POL_NO                   ,
                                          POL_YEAR                 ,
                                          ENDT_NO                  ,
                                          ENDT_YEAR                ,
                                          DRIVER_BIRTH_DT          ,
                                          DRIVER_IQAMA_NO          ,
                                          DRIVER_LICENSE_TYPE      ,
                                          REF_NO                   ,
                                          BROKER_NO                ,
                                          SOURCE                   ,
                                          POST_FLAG                ,
                                          ENDT_DT                  ,
                                          CLIENT_VOH_TYPE          ,
                                          CLIENT_VOH_YEAR          , 
                                          CLIENT_VOH_NO            ,
                                          AGENT_VOH_TYPE           ,
                                          AGENT_VOH_YEAR           ,
                                          AGENT_VOH_NO             ,
                                          CUST_NO                  ,
                                          AGENT_NO                 ,
                                          AGENT_NAME               ,
                                          AGENT_COMM_AMT           ,
                                          SERVICE_CHARGE           ,
                                          ADD_TAX                  ,
                                          ISSUE_FEE                ,
                                          STAMP_FEE                ,
                                          ICF_FEE                  ,
                                          GATR_PREM                ,
                                          REI_FLAG                 ,
                                          ERR_FLAG                 ,
                                          SEQUENCE_NO              ,
                                          RSA_PROVIDER             ,
                                          BENEFICIARY_NO           ,
                                          CUST_CLASS               ,
                                          DISC_CODE                ,
                                          DISC_PCNT                ,
                                          NCB_FLAG                 ,
                                          NCB_AMT                  ,
                                          LOADING_CODE             ,
                                          LOADING_PCNT             ,
                                          LOADING                  ,
                                          LOAD_AMT                 ,
                                          TARIFF_PKG               ,
                                          ENDO_SERIAL              ,   
                                          VAT_PCNT                 ,
                                          VAT_AMT                  ,
                                          FINAL_TOT_AMT            ,
                                          VAT_COMM_PCNT            ,
                                          VAT_COMM_AMT             ,
                                          VEHICLE_SERIAL           ,
                                          FILE_NO) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                           %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                           %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                           %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                           %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                           %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                           %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                           %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                           %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                           %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                           %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                           %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                                                           %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

    rec = (ts,
           result[0],
           result[1],
           result[2],
           result[3],
           result[4],
           result[5],
           datetime.strptime((((result[6]).__str__()).split(" "))[0], '%d/%m/%Y').strftime('%Y-%m-%d'),
           result[7],
           result[8],
           result[9],
           datetime.strptime((((result[10]).__str__()).split(" "))[0], '%Y-%m-%d').strftime('%Y-%m-%d'),
           datetime.strptime((((result[11]).__str__()).split(" "))[0], '%Y-%m-%d').strftime('%Y-%m-%d'),
           result[12],
           result[13],
           result[14],
           result[15],
           result[16],
           result[17],
           result[18],
           result[19],
           result[20],
           result[21],
           result[22],
           result[23],
           result[24],
           result[25],
           result[26],
           result[27],
           result[28],
           result[29],
           result[30],
           result[31],
           result[32],
           result[33],
           result[34],
           result[35],
           result[36],
           result[37],
           result[38],
           result[39],
           result[40],
           result[41],
           result[42],
           result[43],
           result[44],
           result[45],
           result[46],
           result[47],
           result[48],
           result[49],
           addr,
           result[51],
           result[52],
           result[53],
           result[54],
           result[55],
           result[56],
           result[57],
           result[58],
           result[59],
           result[60],
           result[61],
           result[62],
           result[63],
           result[64],
           result[65],
           result[66],
           result[67],
           result[68],
           result[69],
           result[70],
           result[71],
           result[72],
           result[73],
           result[74],
           result[75],
           result[76],
           result[77],
           result[78],
           result[79],
           result[80],
           result[81],
           result[82],
           result[83],
           result[84],
           result[85],
           result[86],
           result[87],
           result[88],
           result[89],
           result[90],
           result[91],
           result[92],
           result[93],
           result[94],
           result[95],
           result[96],
           result[97],
           result[98],
           result[99],
           result[100],
           result[101],
           result[102],
           result[103],
           result[104],
           result[105],
           result[106],
           result[107],
           result[108],
           result[109],
           result[110],
           result[111],
           result[112],
           result[113],
           result[114],
           result[115],
           result[116],
           result[117],
           result[118],
           result[119],
           result[120],
           result[121],
           result[122],
           result[123],
           result[124],
           result[125],
           result[126],
           result[127],
           result[128],
           result[129])

    mysqlcur.execute(sqlFormula, rec)
    mysqldb.commit()
    mysqldb.close()
                      
    print("Finished processing insert. Now going to collect Schedule data.")    
    cur.close()
    con.close()
    get_schedule_data(pol_no,pol_year,3,3)

def get_quote(pol_no,pol_year):
    con = cx_Oracle.connect('GENCDE/xxxxxxxx@xx.xx.xx.xx/amandb')   
    get_all_endt(pol_no,pol_year)

    mysqldb = mydb()
    mycursor1 = mysqldb.cursor()   
    sql1 =  """SELECT * FROM all_endts 
                WHERE pol_no=""" + str(pol_no) + """ 
                  AND pol_year=""" + str(pol_year) + """
                  AND endt_trans in (0,3,7,9)"""
    mycursor1.execute(sql1)
    results = mycursor1.fetchall()
    mysqldb.close()

    j = 0
    endt_dates =    {}
    trans =         {}
    expiry_dates =  {}
    endorsements =  {}
    premiums =      {}
    types =         {}
    customer =      {}
    sum_insured =   {}
    polcy_type =    {}
    for record in results:
        if results[j][4] in (0,3,7,9):
            print(results[j][1],results[j][3],results[j][4],results[j][22],results[j][11])                 
            endt_dates.update({datetime.strptime(results[j][9].__str__().split(" ")[0], '%Y-%m-%d').date() : results[j][1]})
            expiry_dates.update({datetime.strptime(results[j][11].__str__().split(" ")[0], '%Y-%m-%d').date() : results[j][1]})
            endorsements.update({results[j][1] : results[j][2]})
            premiums.update({results[j][1] : results[j][17]})
            sum_insured.update({results[j][1] : results[j][25]})
            polcy_type.update({results[j][1] : results[j][7]})
            types.update({results[j][1] : results[j][3]})
            trans.update({results[j][1] : results[j][4]})
            customer.update({results[j][1] : results[j][15]})  
        j = j+1
   
    try:
        endt_type =     (types[endt_dates[max(endt_dates.keys())]])
        endt_trans =    (trans[endt_dates[max(endt_dates.keys())]])
        policy_type =   (polcy_type[endt_dates[max(endt_dates.keys())]])
        print('Endt_Trans: ',endt_trans)
    except:
        print('Exited because polciy might have wrong posting flag value or other issues')
        return 7

    if endt_trans == 7:
        endt_date =         max(endt_dates.keys())
        cur_eff =           max(expiry_dates.keys()) - timedelta(days=365)
        cur_exp =           max(expiry_dates.keys())
        last_prem =         (premiums[endt_dates[max(endt_dates.keys())]])
        si =                (sum_insured[endt_dates[max(endt_dates.keys())]])
        endt_no =           endt_dates[max(endt_dates.keys())]
        endt_year =         endorsements[endt_dates[max(endt_dates.keys())]]           
        expiry_dates.pop(cur_exp)
        prev_exp =          max(expiry_dates.keys())
        days =              cur_exp - prev_exp
        print("Days: ", days)
        new_eff =           max(expiry_dates.keys()) + timedelta(days=1)
        new_exp =           max(expiry_dates.keys()) + timedelta(days=365)        
        if policy_type == 'Motor Third Party Liability Takaful':
            gross_prem =        (last_prem/int(str(cur_exp - prev_exp).split(" ")[0]))*365*0.95
        else:
            gross_prem =        (last_prem/int(str(cur_exp - prev_exp).split(" ")[0]))*365*0.85
        cust_no =           (customer[endt_dates[max(endt_dates.keys())]])
    elif endt_trans == 9:   
        print ("Exited because Transaction Type is 9")
        return 0
    else:
        endt_date =         max(endt_dates.keys())
        cur_eff =           max(expiry_dates.keys()) - timedelta(days=365)
        cur_exp =           max(expiry_dates.keys())
        new_eff =           max(expiry_dates.keys()) + timedelta(days=1)
        new_exp =           max(expiry_dates.keys()) + timedelta(days=365)
        print(new_exp)
        endt_no =           endt_dates[max(endt_dates.keys())]
        endt_year =         endorsements[endt_dates[max(endt_dates.keys())]]    
        cust_no =           (customer[endt_dates[max(endt_dates.keys())]])
        si =                (sum_insured[endt_dates[max(endt_dates.keys())]])
        if policy_type == 'Motor Third Party Liability Takaful':
            gross_prem = (premiums[endt_dates[max(endt_dates.keys())]])*0.95
        else:
            gross_prem = (premiums[endt_dates[max(endt_dates.keys())]])*0.85  

    cur_time = datetime.strptime((datetime.now() - timedelta(days=1)).__str__().split(" ")[0], '%Y-%m-%d').date()
    days_diff = cur_exp - cur_time
    print("Days before expiry: ", str(days_diff).split(" ")[0])

    if (days_diff > timedelta(days=92)) | (days_diff < timedelta(days=0)):
        print ("Exited because policy expiry date is beyond accepatble range")
        return 1

    old_date  = str(endt_date).split("-")[0]
    print("old_date: ",old_date)

    #START: modification for SI
    mysqldb = mydb()
    mycursor2 = mysqldb.cursor()   
    sql2 =  """SELECT * FROM all_endts 
                WHERE pol_no=""" + str(pol_no) + """ 
                  AND pol_year=""" + str(pol_year) + """
                  AND endt_trans in (0,3,9,14)"""
    mycursor2.execute(sql2)
    results3 = mycursor2.fetchall()
    mysqldb.close()

    h = 0
    endt_dates3 =    {}
    trans3 =         {}
    sum_insured3 =   {}
    premiums3 =      {}
    endorsements3 =  {}
    types3 =         {}
    for record3 in results3:
        if results3[h][4] in (0,3,9,14):
            endt_dates3.update({datetime.strptime(results3[h][9].__str__().split(" ")[0], '%Y-%m-%d').date() : results3[h][1]})            
            sum_insured3.update({results3[h][1] : results3[h][25]})
            trans3.update({results3[h][1] : results3[h][4]})
            premiums3.update({results3[h][1] : results3[h][17]})
            endorsements3.update({results3[h][1] : results3[h][2]})
            types3.update({results3[h][1] : results3[h][3]})
        h = h+1  

    endt_type3 =  (types3[endt_dates3[max(endt_dates3.keys())]])
    endt_trans3 = (trans3[endt_dates3[max(endt_dates3.keys())]])
    endt_no3 =    endt_dates3[max(endt_dates3.keys())]
    endt_year3 =  endorsements3[endt_dates3[max(endt_dates3.keys())]]

    if endt_trans3 == 14:
        print('Change of Vehicle SI endt found')
        get_endt_data(endt_no3,endt_year3,endt_type3)

        mysqldb = mydb()
        mycursor3 = mysqldb.cursor()   
        sql3 =  """SELECT * FROM endt_details 
                    WHERE endt_no=""" + str(endt_no3) + """
                      AND endt_year=""" + str(endt_year3)
        mycursor3.execute(sql3)
        result3 = mycursor3.fetchall()
        mysqldb.close()        

        for endorsement3 in result3:
            si_add = round(int(endorsement3[20]),0) 
        print("si_add = ", si_add)
        prem_add = (premiums3[endt_dates3[max(endt_dates3.keys())]])*0.85     
        print("prem_add = ", prem_add)

    cur12 = con.cursor()
    cur12.execute("""select to_number(""" + str(old_date) + """) - (select decode (substr(CUST_CPR_CR,1,1), 
                            0,
                            to_number(20||substr(CUST_CPR_CR,1,2)), 
                            to_number(19||substr(CUST_CPR_CR,1,2))) 
                       from gencde.customers
                      where CUST_NO= """ + "'" + str(cust_no) + "'" + """) driver_age
                       from dual""")               
    old_driver = cur12.fetchall()
    old_age = old_driver[0][0]
    cur12.close()    

    mysqldb = mydb()
    mycursor4 = mysqldb.cursor()   
    sql4 =  """SELECT * FROM all_endts 
                WHERE pol_no=""" + str(pol_no) + """
                  AND pol_year=""" + str(pol_year) + """
                  AND endt_trans=8"""
    mycursor4.execute(sql4)
    results0 = mycursor4.fetchall()
    mysqldb.close()        

    j = 0
    transfer_dates =    {}
    endt_dates1 =       {}
    endorsements1 =     {}
    types1 =            {}
    customer1 =         {}
    loading1 =          {}
    
    for record in results0:
        if results0[j][4] == 8:
            print("Policy Transfer endt found")
            print(results0[j][1],results0[j][3],results0[j][4],results0[j][22],results0[j][11])        
            transfer_dates.update({datetime.strptime(results0[j][9].__str__().split(" ")[0], '%Y-%m-%d').date() : results0[j][1]}) 
            endt_dates1.update({datetime.strptime(results0[j][9].__str__().split(" ")[0], '%Y-%m-%d').date() : results0[j][1]})
            types1.update({results0[j][1] : results0[j][3]})
            endorsements1.update({results0[j][1] : results0[j][2]})
            customer1.update({results0[j][1] : results0[j][15]})
            loading1.update({results0[j][1] : results0[j][19]})
        j = j+1
    
    base_rate = 0
    under_age_loading = 0
    try:
        transfer_date = max(transfer_dates.keys())
        print("Transfer Date: ",transfer_date)
        print("Endt Date: ",endt_date)
        if ((transfer_date >= endt_date) & (policy_type == 'Motor Third Party Liability Takaful')):
            base_rate = 1
            cust_no = (customer1[endt_dates1[max(endt_dates1.keys())]])
            try:
                under_age_loading = (loading1[endt_dates1[max(endt_dates1.keys())]])
            except:
                under_age_loading = 0
            print("Base Rate: ",base_rate)
            print("under_age_loading: ",under_age_loading)
        elif ((transfer_date > endt_date) & (policy_type == 'Motor Comprehensive Takaful')):
            cust_no = (customer1[endt_dates1[max(endt_dates1.keys())]])
            try:
                under_age_loading = (loading1[endt_dates1[max(endt_dates1.keys())]])
            except:
                under_age_loading = 0
            print("under_age_loading: ",under_age_loading)
    except:
        base_rate = 0

    cur1 = con.cursor()
    cur1.execute("""select ECAR_FLEET_FLAG
                      from CARCDE.CAR_INS_ENDT
                     where ECAR_POL_NO=""" + "'" + str(pol_no) + "'" + """
                       and ECAR_POL_YEAR = """ + "'" + str(pol_year) + "'" + """
                       and ECAR_ENDO_SERIAL= (select max(ECAR_ENDO_SERIAL) 
                                                from CARCDE.CAR_INS_ENDT 
                                               where ECAR_POL_NO = """ + "'" + str(pol_no) + "'" + """ 
                                                 and ECAR_POL_YEAR = """ + "'" + str(pol_year) + "'" + """)""")  
    fleet_flag = cur1.fetchall()
    cur1.close()   
    
    if fleet_flag != []:
        if int(fleet_flag[0][0]) == 1:
            print ("Exited because it is a fleet policy")
            return 2

    cur2 = con.cursor()
    cur2.execute("""select to_number(to_CHAR(trunc(sysdate),'RRRR')) - (select decode (substr(CUST_CPR_CR,1,1), 
                           0,
                           to_number(20||substr(CUST_CPR_CR,1,2)), 
                           to_number(19||substr(CUST_CPR_CR,1,2))) 
                      from gencde.customers
                     where CUST_NO= """ + "'" + str(cust_no) + "'" + """) driver_age
                      from dual""")               
    driver = cur2.fetchall()
    driver_age = driver[0][0]
    cur2.close()    

    mysqldb = mydb()
    mycursor5 = mysqldb.cursor()   
    sql5 =  """SELECT * FROM endt_details 
                WHERE endt_no=""" + str(endt_no) + """
                  AND endt_year=""" + str(endt_year)
    mycursor5.execute(sql5)
    check2 = mycursor5.fetchall()
    mysqldb.close()   

    if check2 == []:
        get_endt_data(endt_no,endt_year,endt_type)
    
    mysqldb = mydb()
    mycursor6 = mysqldb.cursor()   
    sql6 =  """SELECT * FROM endt_details 
                WHERE endt_no=""" + str(endt_no) + """
                  AND endt_year=""" + str(endt_year)
    mycursor6.execute(sql6)
    result = mycursor6.fetchall()    
    mysqldb.close() 

    for endorsement in result:
        policy_type =       endorsement[7]
        vehicle_make =      endorsement[42]
        vehicle_model =     endorsement[43]
        type_of_body =      endorsement[44]
        plate_type =        endorsement[45]
        class_of_use =      endorsement[46] 
        registration_no =   endorsement[51] 
        year_of_make =      endorsement[49]
        seat_capacity =     endorsement[52]
        if endt_trans == 7:
            si =            round(int(si)*0.85,0)
        else:
            si =            round(int(endorsement[20])*0.85,0) 
        chassis_no =        endorsement[48]
        deductable =        endorsement[54]
        engine_capacity =   endorsement[55]
        rsa_prem =          endorsement[78]
        rsa_provider =      endorsement[69]
        loading =           endorsement[79]
        agent_no =          endorsement[14]          

    cur3 = con.cursor()
    cur3.execute("""ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD'""")               
    cur3.execute("""SELECT COUNT(CC_CLM_NO||'/'||CC_YEAR ) Claim_No,                                                                
                           SUM((NVL (cc_est_own,0) + NVL (cc_est_tp,0)) -
                           (NVL (cc_rec_est_own,0) + NVL (cc_rec_est_tp,0))) Incurred
                      FROM CARCDE.CAR_CLAIMS
                     WHERE CC_AT_FAULT_FLAG = 1
                       AND CC_POL_NO= """ + "'" + str(pol_no) + "'" + """
                       AND CC_POL_YEAR= """ + "'" + str(pol_year) + "'" + """
                       AND CC_INFORM_DT > to_date('""" + str(cur_eff).split(" ")[0] + """','yyyy-mm-dd') 
                     GROUP BY CC_POL_NO||'/'||CC_POL_YEAR""")
    
    result3 = cur3.fetchall()
    cur3.close()   
    if result3 == []:
        nb_claims = 0
        incurred = 0
    else:
        nb_claims = result3[0][0]
        incurred = result3[0][1]
        print("Claims Nb: ", nb_claims)
        print("Total Incurred: ", incurred)

    if (nb_claims > 0):
        print ("Exited because number of claims is not zero")
        return 4

    #   Check minimum premium for TPL based on type_of_body, engine_capacity, and seat_capacity (Buses only)
    if get_pol_type(policy_type) == 'Motor Third Party Liability Takaful':
        if ((get_body_type(type_of_body) == 'Bus') | (get_body_type(type_of_body) == 'Mini Bus')):
            seat_prem = int(seat_capacity)*3
            gross_prem = (gross_prem/0.95 - seat_prem)*0.95
            if engine_capacity < 1401:
                min_prem = 54
                base_prem = 67
            elif engine_capacity < 2201:
                min_prem = 60
                base_prem = 75
            elif engine_capacity < 3651:
                min_prem = 71
                base_prem = 89
            elif engine_capacity > 3650:
                min_prem = 90
                base_prem = 112
        elif ((get_body_type(type_of_body) == 'Saloon') | (get_body_type(type_of_body) == 'Sedan') | (get_body_type(type_of_body) == 'Jeep') | (get_body_type(type_of_body) == 'Coupe')):
            gross_prem = (gross_prem/0.95 - loading)*0.95
            if engine_capacity < 1401:
                min_prem = 42
                base_prem = 53
            elif engine_capacity < 2201:
                min_prem = 47
                base_prem = 59
            elif engine_capacity < 3651:
                min_prem = 57
                base_prem = 71
            elif engine_capacity > 3650:
                min_prem = 66
                base_prem = 83
        elif get_body_type(type_of_body) == 'Motor Cycle':
            gross_prem = (gross_prem/0.95 - loading)*0.95
            if engine_capacity < 251:
                min_prem = 44
                base_prem = 55
            elif engine_capacity < 401:
                min_prem = 56
                base_prem = 70
            elif engine_capacity < 751:
                min_prem = 76
                base_prem = 95
            elif engine_capacity > 750:
                min_prem = 120
                base_prem = 150
        elif get_body_type(type_of_body) == 'Sports':
            gross_prem = (gross_prem/0.95 - loading)*0.95
            if engine_capacity < 1401:
                min_prem = 69
                base_prem = 80
                gross_prem = gross_prem + 27
            elif engine_capacity < 2201:
                min_prem = 77
                base_prem = 89
                gross_prem = gross_prem + 30
            elif engine_capacity < 3651:
                min_prem = 92
                base_prem = 107
                gross_prem = gross_prem + 35
            elif engine_capacity > 3650:
                min_prem = 108
                base_prem = 125
                gross_prem = gross_prem + 42
        else:
            gross_prem = (gross_prem/0.95 - loading)*0.95
            if engine_capacity < 1401:
                min_prem = 61
                base_prem = 76
            elif engine_capacity < 2201:
                min_prem = 68
                base_prem = 85
            elif engine_capacity < 3651:
                min_prem = 74
                base_prem = 93
            elif engine_capacity > 3650:
                min_prem = 100
                base_prem = 125
    #   Check minumim premium for Comprehensive based on type_of_body 
    elif get_pol_type(policy_type) == 'Motor Comprehensive Takaful':
        try:
            prem_add = prem_add
        except:
            prem_add = 0
        if ((get_body_type(type_of_body) == 'Bus') | (get_body_type(type_of_body) == 'Mini Bus')):
            seat_prem = int(seat_capacity)*3
            gross_prem = ((gross_prem + prem_add)/0.85 - seat_prem)*0.85
            min_prem = 160
        elif ((get_body_type(type_of_body) == 'Sports') | (get_body_type(type_of_body) == 'Coupe')):
            gross_prem = ((gross_prem + prem_add)/0.85 - loading)*0.85
            min_prem = 200
        elif ((get_body_type(type_of_body) == 'Sedan') | (get_body_type(type_of_body) == 'Saloon') | (get_body_type(type_of_body) == 'Jeep')):
            gross_prem = ((gross_prem + prem_add)/0.85 - loading)*0.85
            min_prem = 130
        elif get_body_type(type_of_body) == 'Ambulance':
            gross_prem = ((gross_prem + prem_add)/0.85 - loading)*0.85
            min_prem = 250
        else:
            gross_prem = ((gross_prem + prem_add)/0.85 - loading)*0.85
            min_prem = 160

    if gross_prem < min_prem:
        gross_prem = min_prem

    if base_rate == 1:
        gross_prem = base_prem

    print(driver_age)
    if ((get_pol_type(policy_type) == 'Motor Comprehensive Takaful') & (driver_age < 23)):
        if get_body_type(type_of_body) == 'Sports':
            if old_age < 23:
                loading = int(loading) 
            else:
                loading = int(loading) + int(under_age_loading)
        else:
            if old_age < 23:
                loading = int(loading)
            else:
                loading = int(under_age_loading)   
        print("UA loading 1")
        gross_prem = gross_prem + loading
    elif ((get_pol_type(policy_type) == 'Motor Comprehensive Takaful') & (driver_age == 23)):
        if get_body_type(type_of_body) == 'Sports':
            if old_age < 23:
                loading = int(loading) 
            else:
                loading = int(loading) + int(under_age_loading)
        else:
            if old_age < 25:
                loading = int(loading)
            else:
                loading = int(under_age_loading)
        loading = loading - (gross_prem*0.037)
        if loading < 0:
            loading = 0
        print("UA loading 2")
        gross_prem = gross_prem + loading
    elif ((get_pol_type(policy_type) == 'Motor Third Party Liability Takaful') & (driver_age < 25)):
        if get_body_type(type_of_body) == 'Sports':
            if old_age < 25:
                loading = int(loading) 
            else:
                loading = int(loading) + int(under_age_loading)
        else:
            if old_age < 25:
                loading = int(loading)
            else:
                loading = int(under_age_loading)           
        print("UA loading 3")
        gross_prem = gross_prem + loading
    elif ((get_pol_type(policy_type) == 'Motor Third Party Liability Takaful') & (driver_age == 25)):  
        if get_body_type(type_of_body) == 'Sports':
            if old_age < 25:
                loading = int(loading) 
            else:
                loading = int(loading) + int(under_age_loading)
        else:
            if old_age < 25:
                loading = int(loading)
            else:
                loading = int(under_age_loading)
        loading = int(loading) - (base_prem*0.25)
        if loading < 0:
            loading = 0
        gross_prem = gross_prem + loading
        print("UA loading 4")

    try:
        cur6 = con.cursor()
        cur6.execute("""SELECT DISTINCT(CRR_RI_RATE)
                        FROM carcde.car_rsa_rating
                        WHERE crr_code = """ + "'" + str(rsa_provider) + "'" + """""")  
        rsa_rate = cur6.fetchall()
        cur6.close()   
    except:
        rsa_provider = None

    if endt_trans == 7:
        print(rsa_provider)
        if rsa_provider != None:
            rsa_prem = int(rsa_rate[0][0])            

    if ((get_body_type(type_of_body) == 'Bus') | (get_body_type(type_of_body) == 'Mini Bus')):
        total_prem =        round(gross_prem + seat_prem + rsa_prem,2)
    else:
        total_prem =        round(gross_prem + rsa_prem,2)
    
    if ((get_pol_type(policy_type) == 'Motor Comprehensive Takaful') & (driver_age < 23)):
        if total_prem < 220:
            total_prem = 220

    vat_amt =           round(total_prem * 0.05,2)
    final_tot_amt =     round(total_prem + vat_amt,2)   
    gross_prem = round(gross_prem,2) 

    # Direct Business
    if ((agent_no != None)):                               
        # Agents
        if agent_no not in (2064,2051,15609,9258,1708,13273,1106,1097,1708,27153,33123,32855,42465,44786,44787,45195,45198,45200,45201,45202,
                            45204,45206,45208,45210,52445,52833,52853,53168,52863,53949,55520,58543,58737,57945,62763,80778,80780,80783,80785,
                            80788,80790,85041,73266,35762,52066,34625,55336,14528,29734,32287,15416,15418,3950,29599,82576,53471):                                           
            # Showrooms
            if agent_no not in (71121,92572,76143,77100,54349,29605,33187,38914,76457):    
                # Brokers
                if agent_no not in (1081,1273,1396,4649,12225,46002,29398,1715,1134,32476,4507,1302,1865,1173,7618,103570,34013,1248,1227,23927,
                                    1367,1336,1094,31210,1335,3021,98046,92909):          
                    print ("Exited because policy is under a non whitelisted Broker or Agent")
                    return 5


    cur5 = con.cursor()
    cur5.execute("""SELECT GENCDE.get_sys_desc_web(857,nvl(EVCL_TP_TARIFF,OVCL_TP_TARIFF),2)
                      FROM carcde.car_vehicle_endt 
                     WHERE EVCL_pol_no = """ + "'" + str(pol_no) + "'" + """
                       AND EVCL_pol_year= """ + "'" + str(pol_year) + "'" + """
                       AND EVCL_REC_ID= (select max(EVCL_REC_ID) 
                                           from carcde.car_vehicle_endt 
                                          where EVCL_pol_no = """ + "'" + str(pol_no) + "'" + """ 
                                            and EVCL_pol_year=""" + "'" + str(pol_year) + "'" + """)""")  
    tariff = cur5.fetchall()
    cur5.close()   

    con.close()

    #Check if the plate type & number has been recently changed after the last renewal or policy issuance
    mysqldb = mydb()
    mycursor7 = mysqldb.cursor()   
    sql7 =  """SELECT * FROM all_endts 
                WHERE pol_no=""" + str(pol_no)  + """
                  AND pol_year=""" + str(pol_year) + """
                  AND endt_trans in (0,3,10)"""
    mycursor7.execute(sql7)
    results2 = mycursor7.fetchall()    
    mysqldb.close()     

    g = 0
    z2 = 0
    endt_dates2 =    {}
    endorsements2 =  {}
    types2 =         {}
    trans2 =         {}
    for record2 in results2:
        if results2[g][4] in (0,3):
            endt_dates2.update({datetime.strptime(results2[g][9].__str__().split(" ")[0], '%Y-%m-%d').date() : results2[g][1]})
            endorsements2.update({results2[g][1] : results2[g][2]})
            types2.update({results2[g][1] : results2[g][3]})
            trans2.update({results2[g][1] : results2[g][4]})
        g = g+1
   
    endt_no2 =           endt_dates2[max(endt_dates2.keys())]
    endt_year2 =         endorsements2[endt_dates2[max(endt_dates2.keys())]]
    endt_type2 =         (types2[endt_dates2[max(endt_dates2.keys())]])
    endt_trans2 =         (trans2[endt_dates2[max(endt_dates2.keys())]]) 

    if endt_trans2 == 3:
        endt_dt2 = max(endt_dates2.keys())
        z2 = 1
        mysqldb = mydb()
        mycursor8 = mysqldb.cursor()   
        sql8 =  """SELECT * FROM endt_details 
                    WHERE endt_no=""" + str(endt_no2) + """
                        AND endt_year=""" + str(endt_year2)
        mycursor8.execute(sql8)
        result2 = mycursor8.fetchall()    
        mysqldb.close()  
        for endorsement2 in result2:
            plate_type2 =        endorsement2[45]
            registration_no2 =   endorsement2[51]           

    g = 0
    z3 = 0
    endt_dates3 =    {}
    endorsements3 =  {}
    types3 =         {}
    trans3 =         {}        
    for record3 in results2:
        if results2[g][4] == 10:
            endt_dates3.update({datetime.strptime(results2[g][9].__str__().split(" ")[0], '%Y-%m-%d').date() : results2[g][1]})
            endorsements3.update({results2[g][1] : results2[g][2]})
            types3.update({results2[g][1] : results2[g][3]})
            trans3.update({results2[g][1] : results2[g][4]})
        g = g+1

    if endt_trans3 == 10:
        endt_no3 =           endt_dates3[max(endt_dates3.keys())]
        endt_year3 =         endorsements3[endt_dates3[max(endt_dates3.keys())]]
        endt_type3 =         (types3[endt_dates3[max(endt_dates3.keys())]])
        endt_trans3 =         (trans3[endt_dates3[max(endt_dates3.keys())]])       

        endt_dt3 = max(endt_dates3.keys())   
        z3 = 1
        mysqldb = mydb()
        mycursor8 = mysqldb.cursor()   
        sql8 =  """SELECT * FROM endt_details 
                    WHERE endt_no=""" + str(endt_no3) + """
                        AND endt_year=""" + str(endt_year3)
        mycursor8.execute(sql8)
        result2 = mycursor8.fetchall()    
        mysqldb.close()  
        for endorsement2 in result2:
            plate_type3 =        endorsement2[45]
            registration_no3 =   endorsement2[51]    

    if z2 == 1:
        try:
            if z3 == 1:            
                if endt_dt2 > endt_dt3:
                    plate_type =        plate_type2
                    registration_no =   registration_no2
                else:
                    plate_type =        plate_type3
                    registration_no =   registration_no3
        except:
            plate_type =        plate_type2
            registration_no =   registration_no2                  

    try:
        print("SI prior 14 = ", si)
        si = si + round(float(si_add)*0.85,0)
    except:
        print("No additional SI found")

    if ((str(tariff[0][0]) == 'Motor Comprehensive Takaful') | (str(tariff[0][0]) == 'Motor Third Party Liability Takaful')):
        print(get_pol_type(policy_type),get_veh_make(vehicle_make),get_veh_model(vehicle_model),registration_no,si,rsa_prem,vat_amt,gross_prem,total_prem,final_tot_amt)
        return get_pol_type(policy_type),get_veh_make(vehicle_make),get_veh_model(vehicle_model),registration_no,si,rsa_prem,vat_amt,gross_prem,total_prem,final_tot_amt,plate_type
    else:
        print ("Exited because policy type is neither Comprehensive nor TPL")
        return 6

def renew_by_pol(pol_no,pol_year):
    get_all_endt(pol_no,pol_year)

    mysqldb = mydb()
    mycursor1 = mysqldb.cursor()
    sql1 = """SELECT * FROM all_endts 
               WHERE pol_no=""" + str(pol_no) + """
                 AND pol_year=""" + str(pol_year) + """
                 AND endt_trans in (0,3,7,9)"""
    mycursor1.execute(sql1)   
    results = mycursor1.fetchall()             
    mysqldb.close()

    j = 0
    endt_dates =    {}
    expiry_dates =  {}
    endorsements =  {}
    premiums =      {}
    types =         {}
    customer =      {}
    for record in results:
        if results[j][4] in (0,3,7,9):
            print(results[j][1],results[j][3],results[j][4],results[j][22],results[j][11])
            endt_dates.update({datetime.strptime(results[j][9].__str__().split(" ")[0], '%Y-%m-%d').date() : results[j][1]})
            expiry_dates.update({datetime.strptime(results[j][11].__str__().split(" ")[0], '%Y-%m-%d').date() : results[j][1]})
            endorsements.update({results[j][1] : results[j][2]})
            premiums.update({results[j][1] : results[j][17]})
            types.update({results[j][1] : results[j][3]})
            customer.update({results[j][1] : results[j][15]})
        j = j+1
   
    new_eff =           max(expiry_dates.keys()) + timedelta(days=1)
    new_exp =           max(expiry_dates.keys()) + timedelta(days=365)
    print(new_exp)
    endt_no =           endt_dates[max(endt_dates.keys())]
    endt_year =         endorsements[endt_dates[max(endt_dates.keys())]]
    endt_type =         (types[endt_dates[max(endt_dates.keys())]])
    cust_no =           (customer[endt_dates[max(endt_dates.keys())]])
    gross_prem =        (premiums[endt_dates[max(endt_dates.keys())]]) * 0.85
    endt_dat =          max(endt_dates.keys())
    print(endt_no,"/",endt_year)
    get_endt_data(endt_no,endt_year,endt_type)

    mysqldb = mydb()
    mycursor2 = mysqldb.cursor()
    sql2 = """SELECT * FROM endt_details
               WHERE endt_no=""" + str(endt_no) + """
                 AND endt_year=""" + str(endt_year)
    mycursor2.execute(sql2)   
    result = mycursor2.fetchall()             
    mysqldb.close()

    for endorsement in result:
        pol_type =          endorsement[7]
        client_no =         cust_no
        client_name =       endorsement[11]
        client_aname =      endorsement[11]
        cust_name =         endorsement[11]
        agent_no =          endorsement[14]
        comm =              endorsement[15]
        vehicle_make =      endorsement[42]
        vehicle_model =     endorsement[43]
        type_of_body =      endorsement[44]
        plate_type =        endorsement[45]
        class_of_use =      endorsement[46] 
        registration_no =   endorsement[51] 
        year_of_make =      endorsement[49]
        seat_capacity =     endorsement[52]
        cpr =               endorsement[35]
        address =           endorsement[13]
        try:
            si =                round(endorsement[20]*0.85,0)
        except:
            si = 0
        rate =              endorsement[21]
        chassis_no =        endorsement[48]
        deductable =        endorsement[54]
        engine_capacity =   endorsement[55]
        cust_aname =        endorsement[29]
        rsa_prem =          endorsement[78]
        rsa_provider =      endorsement[69]
        tariff_pkg =        endorsement[82]
        vat_pcnt =          endorsement[85]
    print('CPR: ', cpr)
    renewal_remarks =   'Renewed online'

    if agent_no in (71121,92572,76143,77100,54349,29605,33187,38914,76457): # Showrooms business becomes direct on renewal        
        agent_no = None
        comm = 0
    else:
        print('agent_no is ',agent_no)

    (pol_type_,vehicle_make_,vehicle_model_,registration_no,si,rsa_prem,vat_amt,gross_prem,total_prem,final_tot_amt,plate_type) = get_quote(pol_no,pol_year)
    try:
        comm_amount = total_prem * (comm/100)
    except:
        comm_amount = 0

    mysqldb = mydb()
    mycursor3 = mysqldb.cursor()
    sql3 = """SELECT * FROM all_endts
               WHERE pol_no=""" + str(pol_no) + """
                 AND pol_year=""" + str(pol_year) + """
                 AND endt_trans=8"""
    mycursor3.execute(sql3)   
    results1 = mycursor3.fetchall()             
    mysqldb.close()    
    
    jj = 0
    endt_dates1 =    {}
    endorsements1 =  {}
    types1 =         {}
    customer1 =      {}
    try:
        for record1 in results1:
            if results1[jj][4] == 8:
                print(results1[jj][1],results1[jj][3],results1[jj][4],results1[jj][22],results1[jj][11])
                endt_dates1.update({datetime.strptime(results1[jj][9].__str__().split(" ")[0], '%Y-%m-%d').date() : results1[jj][1]})
                types1.update({results1[jj][1] : results1[jj][3]})
                endorsements1.update({results1[jj][1] : results1[jj][2]})
                customer1.update({results1[jj][1] : results1[jj][15]})
            jj = jj+1
    
        endt_no1 =           endt_dates1[max(endt_dates1.keys())]
        endt_year1 =         endorsements1[endt_dates1[max(endt_dates1.keys())]]
        endt_type1 =         (types1[endt_dates1[max(endt_dates1.keys())]])
        cust_no =            (customer1[endt_dates1[max(endt_dates1.keys())]])
        endt_dat1 =          max(endt_dates1.keys())

        if endt_dat1 > endt_dat:
            print(endt_no1,"/",endt_year1)
            get_endt_data(endt_no1,endt_year1,endt_type1)
        
            mysqldb = mydb()
            mycursor4 = mysqldb.cursor()
            sql4 = """SELECT * FROM endt_details
                    WHERE endt_no=""" + str(endt_no1) + """
                        AND endt_year=""" + str(endt_year1) 
            mycursor4.execute(sql4)
            result1 = mycursor4.fetchall()             
            mysqldb.close()            

            for endorsement1 in result1:
                client_no =         cust_no
                client_name =       endorsement1[11]
                client_aname =      endorsement1[29]
                cust_name =         endorsement1[11]
                cust_aname =        endorsement1[29]
    except:
        print("There is no endt type 8!")
  
    mysqldb = mydb()
    mycursor5 = mysqldb.cursor()
    sql5 = """SELECT * FROM tba
            WHERE pol_no=""" + str(pol_no) + """
                AND pol_year=""" + str(pol_year) 
    mycursor5.execute(sql5)                    
    check5 = mycursor5.fetchall()             
    mysqldb.close()                

    if check5 != []:
        if str(check5[0][2]) != 'TOZ':
            registration_no = str(check5[0][2])

    print(pol_type,
            new_eff,new_exp,
            client_no,client_name,client_aname,
            cust_name,
            agent_no,comm,comm_amount,
            vehicle_make,vehicle_model,
            type_of_body,plate_type,
            class_of_use,
            registration_no,
            year_of_make,
            seat_capacity,
            si,rate,
            gross_prem,total_prem,gross_prem,
            chassis_no,
            renewal_remarks,
            deductable,
            engine_capacity,
            cust_aname,
            pol_no,pol_year,
            cust_no,
            rsa_prem,rsa_provider,
            tariff_pkg,
            vat_pcnt,vat_amt,
            final_tot_amt,
            cpr,address)
    print("Calling insert_endt_web function")
    insert_endt_web(pol_type,
                    new_eff,new_exp,
                    client_no,client_name,client_aname,
                    cust_name,
                    agent_no,comm,comm_amount,
                    vehicle_make,vehicle_model,
                    type_of_body,plate_type,
                    class_of_use,
                    registration_no,
                    year_of_make,
                    seat_capacity,
                    si,rate,
                    gross_prem,total_prem,gross_prem,
                    chassis_no,
                    renewal_remarks,
                    deductable,
                    engine_capacity,
                    cust_aname,
                    pol_no,pol_year,
                    cust_no,
                    rsa_prem,rsa_provider,
                    tariff_pkg,
                    vat_pcnt,vat_amt,
                    final_tot_amt,
                    cpr,address)

def find_expiry(pol_no,pol_year):
    get_all_endt(pol_no,pol_year)

    mysqldb = mydb()
    mycursor = mysqldb.cursor()
    sql = """SELECT * FROM all_endts
            WHERE pol_no=""" + str(pol_no) + """
                AND pol_year=""" + str(pol_year)  + """
                AND endt_trans in (0,3,7,9)"""
    mycursor.execute(sql)                    
    results = mycursor.fetchall()             
    mysqldb.close()   

    j = 0
    expiry_dates =  {}
    for record in results:
        if results[j][4] in (0,3,7,9):
            expiry_dates.update({datetime.strptime(results[j][11].__str__().split(" ")[0], '%Y-%m-%d').date() : results[j][1]})
            j = j+1
    cur_exp =           max(expiry_dates.keys())
    new_exp =           max(expiry_dates.keys()) + timedelta(days=365)    
    return cur_exp,new_exp

def order(type):
    order = str(type) + '-' + str((datetime.now()).strftime("%Y%m%d")) + '-'
    with open("C://inetpub//wwwroot//renewalBot//order.log", "r") as orders1:
        order_no1 = orders1.read()
        orders1.close()
    os.remove('order.log')
    order_no2 = int(order_no1) + 1
    with open("C://inetpub//wwwroot//renewalBot//order.log", "w+") as orders2:
        orders2.write(str(order_no2))
        orders2.close()
    order_id = order + str(order_no1)
    return order_id

def get_latest_endt(pol_no,pol_year,trns_type):
    con = cx_Oracle.connect('GENCDE/xxxxxxxx@xx.xx.xx.xx/amandb')
    cur = con.cursor()
    cur.execute("""SELECT DISTINCT ECAR_ENDT_NO,
                          ECAR_YEAR,
                          ECAR_ENDT_TYPE,
                          ECAR_TRN_TYPE,
                          ECAR_POL_NO,
                          ECAR_POL_YEAR,
                          GENCDE.get_sys_desc_web (29, ECAR_POLICY_TYPE, 2), 
                          ECAR_SOURCE,
                          ECAR_ENDT_DT,
                          ECAR_INS_ST_DT,
                          ECAR_INS_ED_DT,
                          ECAR_UW_YEAR,
                          ECAR_CLIENT,
                          ECAR_CLIENT_NAME,
                          ECAR_CUST_NO,
                          ECAR_CUST_NAME,
                          ECAR_NET_PREM,
                          ECAR_DISCOUNTS,
                          ECAR_LOADINGS,
                          ECAR_GATR_PREM RSA,
                          ECAR_ISSUE_FEE,
                          ECAR_TOTAL_PREM,
                          nvl(ECAR_VAT_AMT,0) VAT_Amount,
                          nvl (ECAR_FINAL_TOTAL,ECAR_TOTAL_PREM) Final_Total
                     FROM carcde.car_ins_endt
                    WHERE ECAR_POL_NO= """ + "'" + str(pol_no) + "'" + """
                      AND ECAR_POL_YEAR = """ + "'" + str(pol_year) + "'" + """
                      AND ECAR_POST_FLAG > 0
                      AND ECAR_YEAR = EXTRACT(YEAR FROM SYSDATE)
                      AND ECAR_TRN_TYPE = """ + "'" + str(trns_type) + "'" + """
                    ORDER BY ECAR_ENDT_DT DESC,ECAR_ENDT_NO DESC """)               
    result = cur.fetchall()
    cur.close()
    con.close() 
    print(result[0][0]) 
    return result[0][0],result[0][1]   

def get_schedule_data(pol_no,
                            pol_year,
                            endt_type,
                            trns_type): 
    (endt_no,endt_year) = get_latest_endt(pol_no,pol_year,trns_type)
    print(endt_no,endt_year)
    
    con = cx_Oracle.connect('GENCDE/xxxxxxxx@xx.xx.xx.xx/amandb')
    cur1 = con.cursor()

    p_lang                      =   1
    p_branch                    =   1              
    p_office                    =   1   
    p_ecar_class_of_business    =   1
    p_ecar_endt_no              =   endt_no            
    p_ecar_year                 =   endt_year           
    p_ecar_endt_type            =   endt_type           
    p_pol_no                    =   pol_no
    p_pol_year                  =   pol_year
    p_broker_value              =   None
    p_policy_no                 =   cur1.var(str)
    p_policy_type               =   cur1.var(str)
    p_eff                       =   cur1.var(str)
    p_exp                       =   cur1.var(str)
    p_issue                     =   cur1.var(str)
    p_insured                   =   cur1.var(str)
    p_address                   =   cur1.var(str)
    p_vehicle_make              =   cur1.var(str)
    p_vehicle_model             =   cur1.var(str)
    p_registration_no           =   cur1.var(str)
    p_chassis_no                =   cur1.var(str)
    p_year_of_make              =   cur1.var(int)
    p_class_of_use              =   cur1.var(str)
    p_seat_capacity             =   cur1.var(int)
    p_value                     =   cur1.var(str)
    p_deductible                =   cur1.var(str)
    p_vol_excess                =   cur1.var(str)
    p_bus_loc                   =   cur1.var(str)
    p_ecar_bus_location         =   cur1.var(int)
    p_cover_desc                =   cur1.var(str)
    p_excluding_desc            =   cur1.var(str)
    p_evcl_accessories          =   cur1.var(str)
 
    result1 = cur1.callproc('WEB_INSERT_DIRECT_AMAN.get_schedule_data',
        [p_lang,
         p_branch,
         p_office,
         p_ecar_class_of_business,
         p_ecar_endt_no,
         p_ecar_year,
         p_ecar_endt_type,
         p_pol_no,
         p_pol_year,
         p_broker_value,
         p_policy_no,
         p_policy_type,
         p_eff,
         p_exp,
         p_issue,
         p_insured,
         p_address,
         p_vehicle_make,
         p_vehicle_model,
         p_registration_no,
         p_chassis_no,
         p_year_of_make,
         p_class_of_use,
         p_seat_capacity,
         p_value,
         p_deductible,
         p_vol_excess,
         p_bus_loc,
         p_ecar_bus_location,
         p_cover_desc,
         p_excluding_desc,
         p_evcl_accessories])  

    cur1.close()
    
    cur2 = con.cursor()
    cur2.execute("""select VUW_CLIENT_VOH_NO,       
                           VUW_ACC_CLIENT_VOH_YEAR, 
                           CLASS_OF_USE_DESC usage, 
                           DEDUCTABLE,              
                           RSA_PROVIDER,           
                           (select CRR_ENAME 
                               from CARCDE.CAR_RSA_RATING
                               where CRR_CODE=RSA_PROVIDER
                               and CRR_POL_TYPE=VUW_POL_TYPE) RSA,         
                           (select nvl(CUST_ACCOUNT_NO,'10027601000000') 
                               from gencde.customers
                               where cust_no=VUW_CLIENT_NO) account_no,     
                           (select CUST_VAT_FILE 
                               from gencde.customers
                               where cust_no=VUW_CLIENT_NO) customer_vat,  
                           (select GENCDE.get_sys_desc_web (101,nvl(EVCL_VEHICLE_MAKE,OVCL_VEHICLE_MAKE),2) 
                               from carcde.car_vehicle_endt
                               where EVCL_ENDT_NO = VUW_ENDT_NO
                               and EVCL_YEAR=VUW_ENDT_YEAR
                               and EVCL_VEHICLE_SERIAL=1
                               and EVCL_ENDT_TYPE=""" + "'" + str(endt_type) + "'" + """) Make,                  
                           (select GENCDE.get_sys_desc_web (110,nvl(EVCL_VEHICLE_MODEL,OVCL_VEHICLE_MODEL),2) 
                               from carcde.car_vehicle_endt
                               where EVCL_ENDT_NO = VUW_ENDT_NO
                               and EVCL_YEAR=VUW_ENDT_YEAR
                               and EVCL_VEHICLE_SERIAL=1
                               and EVCL_ENDT_TYPE=""" + "'" + str(endt_type) + "'" + """) Model,                
                           (select nvl(vvcl_accessories,'Nil')  
                               from carcde.vcar_vehicle_endt  
                               where vvcl_branch = 1
                               and vvcl_office = 1
                               and vvcl_endt_no = VUW_ENDT_NO
                               and vvcl_year = VUW_ENDT_YEAR
                               and vvcl_endt_type = """ + "'" + str(endt_type) + "'" + """
                               and VVCL_VEHICLE_SERIAL=1) Accessories,      
                           decode ((select sys_lsdesc 
                                      from gencde.systemf
                                     where sys_major = 106
                                       and sys_minor= (SELECT  VCOV_CODE 
                                                         FROM CARCDE.vCAR_COVER_ENDT
                                                        WHERE  vCOV_branch = 1
                                                          AND vCOV_office = 1
                                                          AND vCOV_endt_no = VUW_ENDT_NO
                                                          AND vCOV_year = VUW_ENDT_YEAR
                                                          AND vCOV_endt_type = """ + "'" + str(endt_type) + "'" + """)) || ' ' ||
                                    (select CRR_ENAME 
                                       from CARCDE.CAR_RSA_RATING
                                      where CRR_CODE=RSA_PROVIDER
                                        and CRR_POL_TYPE=VUW_POL_TYPE),' ','Nil',
                                    (select sys_lsdesc 
                                       from gencde.systemf
                                      where sys_major = 106
                                        and sys_minor= (SELECT VCOV_CODE 
                                                          FROM CARCDE.vCAR_COVER_ENDT
                                                         WHERE vCOV_branch = 1
                                                           AND vCOV_office = 1
                                                           AND vCOV_endt_no = VUW_ENDT_NO
                                                           AND vCOV_year = VUW_ENDT_YEAR
                                                           AND vCOV_endt_type = """ + "'" + str(endt_type) + "'" + """)) || ' ' ||
                                    (select CRR_ENAME 
                                       from CARCDE.CAR_RSA_RATING
                                      where CRR_CODE=RSA_PROVIDER
                                        and CRR_POL_TYPE=VUW_POL_TYPE)) additional_cover,
                           decode ((SELECT GENCDE.get_sys_desc_web (106,VCOV_CODE,2) 
                                      FROM CARCDE.vCAR_COVER_ENDT
                                     WHERE vCOV_branch = 1
                                       AND vCOV_office = 1
                                       AND vCOV_endt_no = VUW_ENDT_NO
                                       AND vCOV_year = VUW_ENDT_YEAR
                                       AND vCOV_endt_type = """ + "'" + str(endt_type) + "'" + """) || ' ' ||
                                   (select CRR_ENAME 
                                      from CARCDE.CAR_RSA_RATING
                                     where CRR_CODE=RSA_PROVIDER
                                       and CRR_POL_TYPE=VUW_POL_TYPE),' ','Nil',
                                   (SELECT GENCDE.get_sys_desc_web (106,VCOV_CODE,2) 
                                      FROM CARCDE.vCAR_COVER_ENDT
                                     WHERE vCOV_branch = 1
                                       AND vCOV_office = 1
                                       AND vCOV_endt_no = VUW_ENDT_NO
                                       AND vCOV_year = VUW_ENDT_YEAR
                                       AND vCOV_endt_type = """ + "'" + str(endt_type) + "'" + """) || ' ' ||
                                   (select CRR_ENAME 
                                      from CARCDE.CAR_RSA_RATING
                                     where CRR_CODE=RSA_PROVIDER
                                       and CRR_POL_TYPE=VUW_POL_TYPE)) additional_conditions,
                           VUW_CLIENT_NO,                                                                                                                 
                           BODY_TYPE_DESC,                                      
                           '200000513800002' tazur_vat,
                           VUW_TOTAL_PREM,                                                                                                                    
                           VUW_VAT_PCNT,
                           VUW_VAT_AMT,
                           VUW_TOTAL_PREM + VUW_VAT_AMT Final_Total,
                           (SELECT CUST_ANAME 
                              from gencde.customers 
                             where CUST_NO = VUW_AGENT_NO
                               and CUST_OFFICE=1) broker,
                           (SELECT ca_full_address 
                              FROM gencde.cust_address
                             WHERE ca_cust_no = VUW_CLIENT_NO) address                             
                       from PLNCDE.VPLN_UW_VIEW_MACAW
                       where VUW_ENDT_NO  = """ + "'" + str(endt_no) + "'" + """
                       and VUW_ENDT_YEAR = """ + "'" + str(endt_year) + "'" + """
                       and VUW_DEPT_NO=1
                       and VUW_ENDT_TYPE=""" + "'" + str(endt_type) + "'" )               
    result2 = cur2.fetchall()
    print(tuple(result2))
    
    time_tuple = time.localtime()
    ts = time.strftime("%Y-%m-%d",time_tuple)
        
    mysqldb = mydb()
    mysqlcur = mysqldb.cursor()            
    
    sqlFormula = """INSERT INTO schedule (timestamp,                  
                                          LANG,
                                          BRANCH,
                                          OFFICE,
                                          CLASS_OF_BUSINESS,
                                          ENDT_NO,
                                          ENDT_YEAR,
                                          ENDT_TYPE,
                                          POL_NO,
                                          POL_YEAR,
                                          BROKER,
                                          POLICY_NO,
                                          POLICY_TYPE,
                                          EFF_DATE,
                                          EXP_DATE,
                                          ISSUE_DATE,
                                          INSURED,
                                          ADDRESS,
                                          VEHICLE_MAKE,
                                          VEHICLE_MODEL,
                                          REGISTRATION_NO,
                                          CHASSIS_NO,
                                          YEAR_OF_MAKE,
                                          CLASS_OF_USE,
                                          SEATING_CAPACITY,
                                          VALUE,
                                          DEDUCTIBLE,
                                          EXCESS,
                                          BUS_LOC,
                                          BUS_LOCATION,
                                          COVERS,
                                          EXCLUSIONS,
                                          ACCESSORIES,
                                          VOH_NO,
                                          VOH_YEAR,
                                          ADDITIONAL_COVER,
                                          ADDITIONAL_CONDITIONS,
                                          CUST_NO,  
                                          BODY_TYPE,
                                          TAZUR_VAT,
                                          TOTAL_PREM,
                                          VAT_PCNT,
                                          VAT_AMT,
                                          TOTAL_FINAL,
                                          RSA,
                                          CUST_ACC,
                                          CUST_VAT) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                                                            %s, %s, %s, %s, %s, %s, %s)"""
    rec = (ts,                  
            result1[0],
            result1[1],
            result1[2],
            result1[3],
            result1[4],
            result1[5],
            result1[6],
            result1[7],
            result1[8],
            result2[0][20],
            result1[10],
            result1[11],
            datetime.strptime(result1[12][0:10], '%d/%m/%Y').strftime('%Y-%m-%d'),
            datetime.strptime(result1[13][0:10], '%d/%m/%Y').strftime('%Y-%m-%d'),
            datetime.strptime(result1[14][0:10], '%d-%b-%y').strftime('%Y-%m-%d'),
            result1[15],
            result2[0][21],
            result2[0][8],
            result2[0][9],
            result1[19],
            result1[20],
            result1[21],
            result2[0][2],
            result1[23],
            result1[24],
            result2[0][3],
            result1[26],
            result1[27],
            result1[28],
            result1[29],
            result1[30],
            result2[0][10],
            result2[0][0],
            result2[0][1],
            result2[0][11],
            result2[0][12],
            result2[0][13],  
            result2[0][14],
            result2[0][15],
            result2[0][16],
            result2[0][17],
            result2[0][18],
            result2[0][19],
            result2[0][5],
            result2[0][6],
            result2[0][7])
    try:
        mysqlcur.execute(sqlFormula, rec)
        mysqldb.commit()
    except:
        print("Some errors during records insert in schedule table!")                
    
    mysqldb.close()    
    
    cur2.close()
    con.close()

class HelloWorld(Resource):
    def get(self):
        return {"about":"t'azur Chatbot Web Service!"}

class Test(Resource):
    @token_required
    def get(self):
        return {"test":"t'azur Chatbot Web Service!"}

class Get_Egov_Status(Resource):
    @token_required
    def post(self):
        params = [0,0,0,0,0,0]
        parameters = request.get_json()
        json_data = json.loads(json.dumps(parameters))
        params[0] = json_data["parameters"]["p_branch"]
        params[1] = json_data["parameters"]["p_endt_no"]
        params[2] = json_data["parameters"]["p_endt_year"]
        params[3] = json_data["parameters"]["p_endt_type"]
        params[4] = json_data["parameters"]["p_class_of_business"]
        params[5] = json_data["parameters"]["p_office"]            
        query_response = get_egov_status(params[0],params[1],params[2],params[3],params[4],params[5])
        return jsonify({"get_egov_status":{'p_egov_flag': query_response[6],'p_egov_status': query_response[7]}})

if __name__ == '__name__':
    app.run(debug=True)
    
api.add_resource(HelloWorld, '/')
api.add_resource(Test, '/test')
api.add_resource(Get_Egov_Status, '/get_egov_status')
