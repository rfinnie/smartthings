# TP-LINK Smart Plug HS100 (LAN web proxy)

The [TP-LINK HS100](http://www.tp-link.com/us/products/details/HS100.html) (and related family) is a WiFi smart plug.
By default, it connects outbound to the Kasa service where it is managed remotely.
However, it has an undocumented local interface on port 9999, which is XOR-obfuscated JSON, but is otherwise completely open.

SmartThings does not allow for local LAN direct TCP communication, but does allow for local LAN HTTP communication, so we will use an HTTP proxy to talk to it.
This local LAN proxy allows for POSTing JSON to the service, and receiving JSON replies, which the device handler can work with.

Be warned: this handler and proxy rely on an undocumented and obfuscated protocol of the TP-LINK HS100, which could change at any time.
It has been tested as of the following firmwares:
* HS100: 1.2.2 Build 170907 Rel.164228
* HS105: 1.2.9 Build 170808 Rel.145916

## Device setup

You may want to give your device a static DHCP-assigned IP on your LAN for convenience and stability ahead of time.
The MAC address is located on a label on the back of the device.

Go through the initial setup through Kasa.
Once it is set up, make sure you can connect to the IP on port 9999.

```
$ nc -vz 10.128.67.72 9999
Connection to 10.128.67.72 9999 port [tcp/*] succeeded!
```

## Proxy setup

Run hs100_proxy.py on a stable LAN host as a daemon, pointing to the HS100 IP.
(How you daemonize the service is beyond the scope of these instructions: systemd, screen, etc.)

```
$ hs100_proxy.py 10.128.67.72
```

By default, the proxy will listen on port 8362 and connect to the HS100 IP on port 9999, but these can be customized.
Pass `--help` for a full list of options.

Once the proxy is running, test it (`json_pp` is optional but formats the output more readably):

```
# Status
$ curl -s --data-binary '{"system":{"get_sysinfo":{"state":null}}}}' -H "Content-type: application/json" http://10.128.67.5:8362/command | json_pp
{
   "system" : {
      "get_sysinfo" : {
         "err_code" : 0,
         "rssi" : -55,
         "dev_name" : "Wi-Fi Smart Plug",
         "on_time" : 0,
         "active_mode" : "none",
         "deviceId" : "800609D208EA6F1A3CE2876B35AA215A17BA1683",
         "relay_state" : 0,
         "alias" : "hs100",
         "icon_hash" : "",
         "feature" : "TIM",
         "fwId" : "59542398207847F07D67AB57530532B8",
         "hw_ver" : "1.0",
         "sw_ver" : "1.1.1 Build 160725 Rel.163650",
         "oemId" : "37589AA1F5CACDC53E2914B7760127E5",
         "model" : "HS100(US)",
         "longitude" : 0,
         "type" : "IOT.SMARTPLUGSWITCH",
         "latitude" : 0,
         "hwId" : "5EACBE93FB9E32ECBE1F1C2ADE6DDE11",
         "mac" : "50:C7:BF:0F:E4:16",
         "updating" : 0,
         "led_off" : 0
      }
   }
}

# Turn on outlet
$ curl -s --data-binary '{"system":{"set_relay_state":{"state":1}}}}' -H 'Content-type: application/json' http://10.128.67.5:8362/command | json_pp
{
   "system" : {
      "set_relay_state" : {
         "err_code" : 0
      }
   }
}

# Turn off outlet
$ curl -s --data-binary '{"system":{"set_relay_state":{"state":0}}}}' -H 'Content-type: application/json' http://10.128.67.5:8362/command | json_pp
{
   "system" : {
      "set_relay_state" : {
         "err_code" : 0
      }
   }
}
```

## SmartThings setup

Install the device handler in the Developer API.

Add a New Device, with the following options (values in *italics* may be changed):

  - Name: *Outlet*
  - Label: *HS100 Outlet*
  - Zigbee Id:
  - Device Network Id: *0A804305:20AA*
  - Type: TP-LINK Smart Plug HS100 (LAN web proxy)
  - Version: Published
  - Location: *Home*
  - Hub: *Home Hub*
  - Group:

The most important configuration is the Device Network Id.
This is the hex representation of the proxy IP and port.
So in our example, while 10.128.67.72:9999 is the device itself, 10.128.67.5:8362 is the proxy and becomes 0A804305:20AA (0A = 10, 80 = 128, 43 = 67, 05 = 05, 20AA = 8362).
The Device Network Id appears to be case sensitive, and must be uppercase.
If it's not uppercase, commands will work, but the status replies from the proxy will not be received by the hub.

This Device Network Id restriction effectively limits you to one proxy per HS100 device, so if you have multiple devices, you will need to run multiple proxies on different ports.
