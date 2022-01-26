---
title: Protocol
---

!!! Simple test for displaying protocol flow chart. Real protocl is much more complex...
[flow]
starttransmission=>start: Start transmission
transmissionsuccess=>end: End|success
transmissionnosuccess=>end: End|invalid

opendatachannel=>operation: Open datachannel
datachannelopened=>condition: Opened?
nretries=>condition: Retry<=5?
sendframe=>operation: Send frame
waitforack=>subroutine: Wait for ACK
ackreceived=>condition: ACK?

starttransmission->opendatachannel->datachannelopened
datachannelopened(no)->nretries(right)
nretries(yes)->opendatachannel
nretries(no, bottom)->transmissionnosuccess
datachannelopened(yes)->sendframe->waitforack->ackreceived
ackreceived(no, left)->sendframe(left)
ackreceived(yes, bottom)->transmissionsuccess(top)


[/flow]