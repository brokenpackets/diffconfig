# diffconfig
Watches for local configuration changes, performs a diff of new vs old config, and sends to slack.

Requirements:
  DNS Reachability to resolve webhook target (if applicable)   
  HTTPS Reachability to webhook target   
  diffscript.py and webhook.py stored under /mnt/flash/   
  event-handler configured to watch syslog for 'Configured from console by'   
  protocol unix-socket enabled for eAPI   
   
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
