0.1.0
=====
Initial release.

0.1.2
=====
Fixed missing README.md

0.1.3
=====
Common 'mqtt' namespace for logging. This should help in log fltering.
logger module out fo the library. Logging fucntions now in the examples.
Changed subscribe() interface description

0.2.1
=====
Major internal refactoring of the publish,  subscribe and pubsubs roles over 0.1.6.
 
0.2.3
===== 
Backwards compatible with 0.2.1, with three enhancements:
    - Persistent ***per-connection state*** (Pending Publish & Subscription ACKs). Verion 0.2.1 cannot be used with two simultaneous, different MQTT broker connections.
    - Internal queue to hold PUBLISH requests beyond the window size.
    - Adaptive timeouts depending on PUBLISH PDU size and a bandwith estimate. New protocol API function `setBandwith()`. This will avoid dupicate payloads using QoS 1 and 2.

0.2.4
=====
Internal protocol constructor refactoring and document typo fixes.
Fixed bug retain flag not really set if QoS = 0

0.3.0
=====
Incompatible API version. No mor settters for callback handlers. 
Now callbacks are attributes.
Fixed missing key error bug.

0.3.1
=====
Erased unneded setPublishHandler.
Refactored connectionLost code.
Robust examples.

0.3.2
=====
Fixed reconenction bug.

0.3.3
=====
Doc fixes.
Fixed abortConnection() bug.

0.3.4
=====
Alpha => Beta status
Solved issue https://github.com/astrorafael/twisted-mqtt/issues/7


