# Z-Wave Repeater

Does (almost) literally nothing.

While there are a few standalone commercial Z-Wave repeaters out there, this handler was built with the [Iris Smart Plug](https://support.irisbylowes.com/link/portal/30143/30206/Article/547/Next-Gen-Iris-Smart-Plug-with-Next-Gen) in mind.
The Iris Smart Plug is a ZigBee switched outlet, but also has the interesting feature that it acts as a Z-Wave repeater, but otherwise has no other Z-Wave function.
However, when the Z-Wave side is added to SmartThings, it also shows up as a switched outlet, but does nothing when interacted with.
A side effect of this is if you have Alexa intergration, they will be exported to Alexa as usable Things, which are not desired.

## Installation

Install the device handler in the Developer API.

The device handler automatically supports the following repeaters:

  - Iris Smart Plug Z-Wave Repeater
  - Aeon Labs DSD37-ZWUS Repeater
  - Aeotec Range Extender 6
  - Vision Security Repeater ZR1202US
  - Vision Z-Wave Repeater
  - Remotec ZRP-100US / BW8140US Z-Wave Repeater

To initiate Z-Wave setup on an Iris Smart Plug, go to add a new Thing in the SmartThings app, then with the smart plug plugged in, press the power button 8 times in rapid succession.

Z-Wave repeaters will appear in the app with the primary function being Refresh, which effectively does nothing except query the device firmware version.
These repeaters should also not show up in Alexa.
