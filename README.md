# Ryan Finnie's Smart SmartThings Things

*Not guaranteed to be smart.*

## Device Handlers

### Z-Wave Repeater

Does (almost) literally nothing.

While there are a few standalone commercial Z-Wave repeaters out there, this handler was built with the Iris Smart Plug in mind.
The Iris Smart Plug is a ZigBee switched outlet, but also has the interesting feature that it acts as a Z-Wave repeater, but otherwise has no other Z-Wave function.
However, when the Z-Wave side is added to SmartThings, it also shows up as a switched outlet, but does nothing when interacted with.
A side effect of this is if you have Alexa intergration, they will be exported to Alexa as usable Things, which are not desired.

To install, add to the Developer API, then edit your existing Z-Wave Thing and change Type to "Z-Wave Repeater".
It will appear in the app with the primary function being Refresh, which effectively does nothing except query the device firmware version.
These repeaters should also not show up in Alexa.
