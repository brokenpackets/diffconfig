## Needs to be run from VRF with internet access.
# Grab username that made config change and store as variable.
#     if diff, then 'Configured by $USER at $IPADDR\n'+diff
import subprocess
import webhook
import jsonrpclib
import os
import socket
import re

'''
Requirements:
  DNS Reachability to resolve webhook target (if applicable)
  HTTPS Reachability to webhook target
  diffscript.py and webhook.py stored under /mnt/flash/
  event-handler configured to watch syslog for 'Configured from console by'
  
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

log_message = ''
url = "unix:/var/run/command-api.sock"
ss = jsonrpclib.Server(url)
webhook_url = 'https://hooks.slack.com/services/your/webhook/here'
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
    webhook.webhook(hostname, webhook_url, 'Configured by *'+username+'*, at *'+
    ip_addr+'*\n'+output)
response = ss.runCmds( 1, [ 'copy running-config file:tmp/.old_config' ] )
