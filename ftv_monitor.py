#!/usr/bin/python3
import requests
import re
import pprint
import os
import subprocess
# sudo apt install swaks python3-requests
# Add a crontab:
# */10 * *  *  *   python3 /home/pi/ftv_monitor.py &> /home/pi/ftv_monitor.log

# <config>
banned_workers = []
banned_offices = ["Åkersberga (Åkersberga)",
                  "Nynäshamn (Nynäshamn)",
                  "Kungsängen (Kungsängen)",
                  "Hallunda (Norsborg)",
                  "Huddinge (Huddinge)",
                  "Skogås (Skogås)",
                  "Medicinsk tandvård Stora Sköndal (Sköndal)",
                  "Fruängen (Hägersten)",
                  "Mörby (Danderyd)",
                  "Brommaplan (Bromma)",
                  "Högdalen (Bandhagen)",
                  "Skärholmen (Skärholmen)",
                  "Skanstull (Stockholm)",
                  "Rotebro (Sollentuna)",
                  "Handen (Handen)",
                  "Vallentuna (Vallentuna)",
                  "Sigtuna (Sigtuna)",
                  "Västertorp (Hägersten)",
                  "Solna (Solna)",
                  "Sundbyberg (Sundbyberg)",
                  "Spånga (Spånga)",
                  "Västerhaninge (Tungelsta)",
                  ]

history_file = os.path.expanduser("~/.ftv_monitor_history.log")
url = "https://www.folktandvardenstockholm.se/api/booking/lastminutenotcached"
mail_server="XXXX"
mail_port="XXXX"
mail_to="XXXX"
mail_from="XXXX"
mail_subject="Lediga tider folktandvården"
mail_user=mail_from
mail_password="XXXX"
# </config>

def mail_swaks(smtpserver,smtpport,user,password,mail_to,mail_from,subject,body):
    # Warning! I don't take responsibility if SWAKS fails to handle
    # arguments correctly!
    subprocess.run([
        "swaks",
        "--add-header","Content-Type: text/plain;charset=utf-8",
        "-s",smtpserver,
        "-p",smtpport,
        "-t",mail_to,
        "-f",mail_from,
        "--header","Subject: %s"%subject,
        "-S","--protocol","ESMTP","-a",
        "-au",user,
        "-ap",password,
        "--body",body])


def sanitize_input(text,t="text"):
    filters = {
        "text": r'[^A-Z0-9a-zÅÄÖåäöéíì .:,-]',
        "hex": r'[^A-F0-9a-f]',
        "number": r'[^0-9]'
    }
    return re.sub(filters[t],"",str(text),re.MULTILINE)

r = requests.get(url=url)
body_parts = []
for avail_time in r.json():
    #pprint.pprint(avail_time)
    
    notes = []
    lines = []
    agetype = sanitize_input(avail_time['timeType']['ageType'])
    description = sanitize_input(avail_time['timeType']['description'])
    start = sanitize_input(avail_time['startTime'])
    end = sanitize_input(avail_time['endTime'])
    place =  "%s (%s)"%(sanitize_input(avail_time['clinicName']),sanitize_input(avail_time['city']))
    price = sanitize_input(avail_time['price'])
    worker = sanitize_input(avail_time['resourceName'])
    time_id = sanitize_input(avail_time['id'].lower(),'hex')

    if worker in banned_workers:
        continue
    if place in banned_offices:
        continue
   
    if os.path.isfile(history_file):
        with open(history_file,'r') as f:
            lines = f.read().splitlines()
    #pprint.pprint(lines)
   
    if time_id in lines:
        continue
    
    with open(history_file,'a+') as f:
        f.write("%s\n"%time_id)
        
    summary = "\n".join(["Type: %s"%description,
           "Location: %s"%place,
           "Time: %s - %s"%(start,end),
           "Price: %s"%price,
           "For: %s"%agetype,
           "Resource: %s"%worker,
           "Notes:"] + notes)
    body_parts.append(summary)

if len(body_parts) != 0:
    mail_swaks(mail_server, mail_port, mail_user, mail_password, mail_to, mail_from, mail_subject, "\n\n".join(body_parts))
