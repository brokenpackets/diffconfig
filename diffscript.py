## Needs to be run from VRF with internet access.
# Grab username that made config change and store as variable.
#     if diff, then 'Configuration changed by $USER\n'+diff
import subprocess
import jsonrpclib
import os
import socket
import re
### Define transport:
notifytype = 'email' # 'email', 'slack', or 'sendgrid'

if notifytype == 'sendgrid':
    import sendgrid
    from sendgrid.helpers.mail import *

if notifytype == 'slack':
    import webhook

'''
Requirements:
  DNS Reachability to resolve webhook target (if applicable)
  HTTPS Reachability to webhook target
  diffscript.py stored under /mnt/flash/
  event-handler configured to watch syslog for 'Configured from console by'
  protocol unix-socket enabled for eAPI

---Notification Methods---
Slack Notification:
  webhook.py python module stored under /mnt/flash/
Sendgrid Notification:
  Sendgrid python module
    Install on switch with 'sudo pip install sendgrid' - may need to run
    from management VRF - sudo ip netns exec ns-{MGMTVRF} pip install sendgrid
    Sendgrid Note: Settings > Mail Settings > Plain Content (Activate) will
      allow you to send as true plaintext (keeps formatting).
Standard SMTP Email notification:
  uses EOS email client, example config:
    email
       from-user Arista-7@example.com
       server vrf MGMT smtp.sendgrid.net:587
       auth username user
       auth password pass
       tls
---------------------------
Example switch config, assumes sourcing from MGMT VRF. If not needing
to source from a VRF, use 'action bash python /mnt/flash/diffscript.py'

event-handler CONFIGCHANGE
   action bash ip netns exec ns-MGMT python /mnt/flash/diffscript.py
   delay 0
   asynchronous
   threshold 1 count 1
   !
   trigger on-logging
      regex Configured from console by

management api http-commands
  no shutdown
  protocol unix-socket
'''
## Secret Data
sg_api_key = 'sendgrid API key' # If applicable
webhook_url = 'slack incoming webhook api key' # If applicable
##

## EMAIL/Sendgrid Variables
subject = "DiffConfig"
sendgrid_from = "Arista-7@example.com"
smtp_to = "user@example.com"
##

url = "unix:/var/run/command-api.sock"
ss = jsonrpclib.Server(url)
diff = 'diff /tmp/.old_config /tmp/.new_config -U 4 -I ("Startup-config")|'
backup_diff = 'diff /mnt/flash/startup-config /tmp/.new_config -U 4 -I "Startup-config" -I "! Startup-config last"'
hostname = socket.gethostname()
username_regex = re.compile('.* Configured from console by (.*?) on.*?\(([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})')

def run_command(command):
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    return output

if os.environ.get('EVENT_LOG_MSG'):
    log_message = os.environ.get('EVENT_LOG_MSG')
    username = username_regex.match(log_message).group(1)
    ip_addr = username_regex.match(log_message).group(2)

    response = ss.runCmds( 1, [ 'copy running-config file:tmp/.new_config' ] )
    # IF exist /tmp/.old_config, use that. Else, use /mnt/flash/startup-config
    if os.path.isfile('/tmp/.old_config'):
        if os.path.getmtime('/mnt/flash/startup-config') < os.path.getmtime('/tmp/.old_config'):
            pre_output = run_command(diff)
        else:
            pre_output = run_command(backup_diff)
    else:
        pre_output = run_command(backup_diff)
    if pre_output:
        output = pre_output.split('\n',2)[2]
        if notifytype == 'sendgrid':
            sg = sendgrid.SendGridAPIClient(sg_api_key)
            from_email = Email(sendgrid_from)
            to_email = Email(smtp_to)
            content = Content("text/plain", 'Configured by *'+username+'*, at *'
                      +ip_addr+'*\n\n'+output)
            mail = Mail(from_email, subject, to_email, content)
            response = sg.client.mail.send.post(request_body=mail.get())
        if notifytype == 'slack':
            webhook.webhook(hostname, webhook_url, 'Configured by *'+username+'*, at *'+
            ip_addr+'*\n'+output)
        if notifytype == 'email':
            if os.path.exists('/tmp/.lastdiff'):
                os.remove('/tmp/.lastdiff')
            f = open('/tmp/.lastdiff','w')
            f.write('Configured by *'+username+'*, at *'+ip_addr+'*\n\n'+output)
            f.close()
            response = ss.runCmds( 1, [ 'more file:/tmp/.lastdiff | email -s '+subject+' -i '+smtp_to ], "text" )
    response = ss.runCmds( 1, [ 'copy running-config file:tmp/.old_config' ] )
