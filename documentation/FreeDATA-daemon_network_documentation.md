# FreeDATA - DAEMON network documentation

## GET DAEMON STATE

#### Description:

Get the current daemon state

#### Parameters

- Type: GET
- Command: DAEMON_STATE
- Parameter: --- (str)

#### Example

```
{"type" : "GET", "command" : "DAEMON_STATE"}
```

#### Returns

```
{
	"COMMAND": "DAEMON_STATE",
	"DAEMON_STATE": [],
	"PYTHON_VERSION": str(python_version),
	"HAMLIB_VERSION": str(hamlib_version),
	"INPUT_DEVICES": [],
	"OUTPUT_DEVICES": [],
	"SERIAL_DEVICES": [],
	"CPU": "",
	"RAM": "",
	"VERSION": "0.1-prototype"
}
```

## SET CALLSIGN

#### Description:

Save your callsign to the daemon

#### Parameters

- Type: SET
- Command: MYCALLSIGN
- Parameter: callsign (str)
- timestamp: unix timestamp (str)

#### Example

```
{"type" : "SET", "command": "MYCALLSIGN" , "parameter": "<callsign>", "timestamp" : "123456789"}
```

## SET GRIDSQUARE

#### Description:

Save your gridsquare/maidenhead-locator to the daemon

#### Parameters

- Type: SET
- Command: MYGRID
- Parameter: gridsquare (str)
- timestamp: unix timestamp (str)

#### Example

```
{"type" : "SET", "command": "MYGRID" , "parameter": "<gridsquare>", "timestamp" : "123456789"}
```

## TEST HAMLIB

#### Description:

Test your hamlib settings

#### Parameters

- Type: GET
- Command: TEST_HAMLIB
- Parameter: obj
  - devicename
  - deviceport
  - pttprotocol
  - pttport
  - serialspeed
  - data_bits
  - stop_bits
  - handshake
- timestamp: unix timestamp (str)

#### Example

```
{
        "type": "GET",
        "command" : "TEST_HAMLIB",
        "parameter" : [{
            "devicename" : "<devicename>",
            "deviceport" : "<deviceport>",
            "pttprotocol" : "<pttprotocol>",
            "pttport" : "<pttport>",
            "serialspeed" : "<serialspeed>",
            "data_bits" : "<data_bits>",
            "stop_bits" : "<stop_bits>",
            "handshake" : "<handshake>"
        }]
    }
```

## START TNC

#### Description:

Start the tnc process

#### Parameters

- Type: GET
- Command: TEST_HAMLIB
- Parameter: obj
  - mycall
  - mygrid
  - rx_audio
  - tx_audio
  - devicename
  - deviceport
  - pttprotocol
  - pttport
  - serialspeed
  - data_bits
  - stop_bits
  - handshake

#### Example

```
{
        type: 'SET',
        command: 'STARTTNC',
        parameter: [{
            mycall: mycall,
            mygrid: mygrid,
            rx_audio: rx_audio,
            tx_audio: tx_audio,
            devicename: devicename,
            deviceport: deviceport,
            pttprotocol: pttprotocol,
            pttport: pttport,
            serialspeed: serialspeed,
            data_bits: data_bits,
            stop_bits: stop_bits,
            handshake: handshake

        }]
    }
```

## STOP TNC

#### Description:

Stop the tnc process

#### Parameters

- Type: SET
- Command: STOPTNC
- Parameter: ---

#### Example

```
{"type" : "SET", "command": "STOPTNC" , "parameter": "---" }
```
