---
title: 'App design'
---

!!! Basic design how FreeDATA works

[sequence]
Client->Daemon:TCP/IP Command
Client->TNC:TCP/IP Command
Daemon-->Client:TCP/IP Stream
TNC-->Client:TCP/IP Stream
Daemon->TNC:start/stop
TNC->codec2:data
codec2->TNC:raw modulation
TNC->Audio device: protocol+modulation
Audio device->Radio:direct/interface
TNC->Radio:Control via Hamlib
[/sequence]