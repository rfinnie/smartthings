# Z-Wave Repeater

Does (almost) literally nothing.

While there are a few standalone commercial Z-Wave repeaters out there, this handler was built with the Iris Smart Plug in mind.
The Iris Smart Plug is a ZigBee switched outlet, but also has the interesting feature that it acts as a Z-Wave repeater, but otherwise has no other Z-Wave function.
However, when the Z-Wave side is added to SmartThings, it also shows up as a switched outlet, but does nothing when interacted with.
A side effect of this is if you have Alexa intergration, they will be exported to Alexa as usable Things, which are not desired.

## Installation

Install the device handler in the Developer API.

If you have an Iris Smart Plug, the device handler will detect the Z-Wave setup automatically.
To initiate Z-Wave setup, go to add a new Thing in the SmartThings app, then with the smart plug plugged in, press the power button 8 times in rapid succession.

[Other Z-Wave repeaters](http://products.z-wavealliance.org/regions/2/categories/15/products) should work with this device handler, but will require manual setup.
Add the device through the SmartThings app, then edit the Thing in the Developer API and change Type to "Z-Wave Repeater".
(If this works for you, please consider filing an Issue to get your device added, specifying the Raw Description of the device.)

Z-Wave repeaters will appear in the app with the primary function being Refresh, which effectively does nothing except query the device firmware version.
These repeaters should also not show up in Alexa.
