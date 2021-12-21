import pdfkit
from bs4 import BeautifulSoup
import re
import io
import sys  

reload(sys)  
sys.setdefaultencoding('utf8')

def generateDnPdf(template, file_name, data):
    # Soup and PDf Configs
    path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    bs = lambda x: BeautifulSoup(x, 'html.parser')

    soup = BeautifulSoup(io.open(template), 'html.parser')
    target = soup.find(name='div',attrs={'class': lambda c: c and 'Participant' in c})
    replacement = str(data["name"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Date' in c})
    replacement = str(data["date"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Tazur-vat' in c})
    replacement = str(data["tazur_vat"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Address' in c})
    replacement = str(data["address"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Voucher-no' in c})
    replacement = str(data["voucher_no"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Broker' in c})
    replacement = str(data["broker"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Account-no' in c})
    replacement = str(data["account_no"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Customer-id' in c})
    replacement = str(data["customer_id"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Customer-vat' in c})
    replacement = str(data["customer_vat"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Policy-number' in c})
    replacement = str(data["policy_number"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Endorsement-number' in c})
    replacement = str(data["endorsement_year"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Policy-type' in c})
    replacement = str(data["policy_type"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'From-date' in c})
    replacement = str(data["from_date"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'To-date' in c})
    replacement = str(data["to_date"])
    soup = bs(str(soup).replace(str(target), replacement))
    
    target = soup.find(name='div',attrs={'class': lambda c: c and 'Make' in c})
    replacement = str(data["make"])
    soup = bs(str(soup).replace(str(target), replacement))    

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Registration-No' in c})
    replacement = str(data["registeration_no"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Vehicle-type' in c})
    replacement = str(data["vehicle_type"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Chassis' in c})
    replacement = str(data["chassis"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'RSA' in c})
    replacement = str(data["rsa"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Total-before-vat' in c})
    replacement = str(data["total_before_vat"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Vat-percentage' in c})
    replacement = str(data["vat_percentage"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Total-after-vat' in c})
    replacement = str(data["total_after_vat"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Total-due' in c})
    replacement = str(data["total_due"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Amount-in-words' in c})
    replacement = str(data["amount_in_words"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Printed-by' in c})
    replacement = str(data["printed_by"])
    soup = bs(str(soup).replace(str(target), replacement))

    pdfkit.from_string(str(soup), file_name ,configuration=config)


def generateShedPdf(file_name, data):
    options = {
            'quiet':'',
            'page-size':'A4',
            'dpi':600,
            'disable-smart-shrinking':'',
        }
    # Soup and PDf Configs
    path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    bs = lambda x: BeautifulSoup(x, 'html.parser')

    #with io.open('schedule.html', 'r', encoding='utf8') as sched:
    #    soup = BeautifulSoup(sched, 'html.parser')
        
    soup = BeautifulSoup(io.open('schedule.html', encoding='utf8'), 'html.parser')
    #soup = BeautifulSoup(open("schedule.html"), "html.parser", from_encoding = 'utf-8')

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Participant' in c})
    replacement = str(data["participant"])
    soup = bs(str(soup).replace(str(target), replacement))
    
    target = soup.find(name='div',attrs={'class': lambda c: c and 'Participant' in c})
    replacement = str(data["participant"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Policy-type' in c})
    replacement = str(data["policy_type"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Policy-number' in c})
    replacement = str(data["policy_number"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'From-date' in c})
    replacement = str(data["from_date"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'To-date' in c})
    replacement = str(data["to_date"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Registration-number' in c})
    replacement = str(data["registeration_no"])
    soup = bs(str(soup).replace(str(target), replacement))
    
    target = soup.find(name='div',attrs={'class': lambda c: c and 'Address' in c})
    replacement = str(data["address"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Make-year' in c})
    replacement = str(data["make_year"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Chassis' in c})
    replacement = str(data["chassis"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Usage' in c})
    replacement = str(data["usage"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Make' in c})
    replacement = str(data["make"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Model' in c})
    replacement = str(data["model"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Excess' in c})
    replacement = str(data["excess"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Passengers' in c})
    replacement = str(data["passengers"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'SI' in c})
    replacement = str(data["si"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Compulsory-deductible' in c})
    replacement = str(data["compulsory_deductible"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Additional-conditions' in c})
    replacement = str(data["additional_conditions"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Additional-exclusions' in c})
    replacement = str(data["additional_exclusions"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Accessories' in c})
    replacement = str(data["accessories"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Print-date' in c})
    replacement = str(data["print_date"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Additional-cover' in c})
    replacement = str(data["additional_cover"])
    soup = bs(str(soup).replace(str(target), replacement))

    target = soup.find(name='div',attrs={'class': lambda c: c and 'Issue-date' in c})
    replacement = str(data["issue_date"])
    soup = bs(str(soup).replace(str(target), replacement))   


    pdfkit.from_string(str(soup), file_name ,configuration=config,options=options)
