# diffconfig
Watches for local configuration changes, performs a diff of new vs old config, and sends to desired notification method. Currently supports slack (webhook), sendgrid, and SMTP/Email.  

Requirements:  
  DNS Reachability to resolve email/sendgrid/webhook target  
  HTTPS Reachability to webhook target (if using Slack/sendgrid notify)  
  SMTP Reachability to email relay (if using email notify)  
  diffscript.py stored under /mnt/flash/  
  event-handler configured to watch syslog for 'Configured from console by'  
  protocol unix-socket enabled for eAPI  
  
---Notification Methods---  
Slack Notification:  
  - webhook.py python module stored under /mnt/flash/  

Sendgrid Notification:  
  - Sendgrid python module  
      - Install on switch with 'sudo pip install sendgrid' - may need to run  
        from management VRF - sudo ip netns exec ns-{MGMTVRF} pip install sendgrid  
      - Sendgrid Note: Settings > Mail Settings > Plain Content (Activate) will  
        allow you to send as true plaintext (keeps formatting).  

Standard SMTP Email notification:  
  - uses EOS email client, example config:  
```
     email
       from-user Arista-7@example.com
       server vrf MGMT smtp.sendgrid.net:587
       auth username user
       auth password pass
       tls
```
---------------------------  
Example switch config, assumes sourcing from MGMT VRF. If not needing  
to source from a VRF, use 'action bash python /mnt/flash/diffscript.py'  
```
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
```
