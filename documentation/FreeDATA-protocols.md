# FreeDATA - Protocols

## ARQ Sessions

An ARQ Session represents a reliable data transmission session from a sending station (A) to a receiving station (B). It uses automatic repeat request on top of different codec2 modes according to the transmission channel conditions.

So lets say A wants to send some data to B. A typical scenario would be like this:

```
ISS->(1)IRS:<datac13> OPEN_REQ(session id, origin, dest)
IRS->(1)ISS:<datac13> OPEN_ACK (session id, proto version, speed level, frames, snr)

ISS->(1)IRS:<datac13> INFO(id, total_bytes, total_crc)
IRS->(1)ISS:<datac13> INFO_ACK(id, total_crc)

ISS->(1)IRS:BURST (ID, offset, payload),(ID, offset, payload),(ID, offset, payload)
IRS->(1)ISS:BURST_ACK (ID, next_offset, speed level, frames, snr)

ISS-->(1)IRS:Lost BURST (total or part)
IRS->(1)ISS:BURST_NACK (ID, next_offset, speed level, frames, snr)

ISS->(1)IRS:BURST (ID, offset, payload),(ID, offset, payload),(ID, offset, payload)
IRS->(1)ISS:DATA ACK NACK (ID, next_offset, speed level, frames, snr)
```

### Frame details

#### SESSION_OPEN_REQ

ISS sends this first

DATAC13 Mode (12 bytes)

| field           | bytes |
| --------------- | ----- |
| session id      | 1     |
| origin          | 6     |
| destination_crc | 3     |

#### SESSION_OPEN_ACK

Sent by the IRS in response to a SESSION_OPEN_REQ

DATAC13 Mode (12 bytes)

| field            | bytes |
| ---------------- | ----- |
| session id       | 1     |
| origin           | 6     |
| destination_crc  | 3     |
| protocol version | 1     |
| snr              | 1     |

#### SESSION_INFO

ISS sends this in response to a SESSION_OPEN_ACK

DATAC13 Mode (12 bytes)

| field       | bytes |
| ----------- | ----- |
| session id  | 1     |
| total bytes | 4     |
| total crc   | 4     |
| snr         | 1     |

#### SESSION_INFO_ACK

IRS sends this in response to a SESSION_INFO

DATAC13 Mode (12 bytes)

| field            | bytes |
| ---------------- | ----- |
| session id       | 1     |
| total crc        | 4     |
| snr              | 1     |
| speed level      | 1     |
| frames per burst | 1     |

#### Data Burst

ISS sends this to send data to IRS

Mode according to handshake speed level

Frames per burst according to handshake

##### Modulation

Each burst is composed of frames_per_burst frames:

|preamble|f1|f2|f3|...|postamble|

##### Each data frame

| field      | bytes                          |
| ---------- | ------------------------------ |
| session id | 1                              |
| offset     | 4                              |
| payload    | (the remaining payload length) |

#### DATA_BURST_ACK

Sent by the IRS following successful decoding of burst.

| field                 | bytes |
| --------------------- | ----- |
| session id            | 1     |
| next offset           | 4     |
| next speed level      | 1     |
| next frames per burst | 1     |
| snr                   | 1     |

#### DATA_BURST_NACK

Sent by the IRS following unsuccessful decoding of burst or timeout.

| field                 | bytes |
| --------------------- | ----- |
| session id            | 1     |
| next offset           | 4     |
| next speed level      | 1     |
| next frames per burst | 1     |
| snr                   | 1     |

#### DATA ACK NACK

Sent by the IRS after receiving data with a state information.

| field      | bytes |
| ---------- | ----- |
| session id | 1     |
| state      | 1     |
| snr        | 1     |
