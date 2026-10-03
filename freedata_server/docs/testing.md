# Testing

The tests live in [`tests/`](../../tests) at the repository root. They need no radio and no audio
hardware: modem traffic is simulated in-process by connecting two `AppContext` instances, one for
each station.

## 1. Running the tests

```bash
python -m venv .venv
.venv/bin/pip install -e ".[test]"        # Windows: .venv\Scripts\pip
```

CI ([modem_tests.yml](../../.github/workflows/modem_tests.yml)) runs the whole suite in one process
on Ubuntu with Python 3.10–3.13:

```bash
python -m unittest discover tests
```

pytest works too (`testpaths = ["tests"]` is set in `pyproject.toml`):

```bash
python -m pytest tests
```

A full run takes about a minute. Both commands exit non-zero when a test fails.

> Before the shutdown change described in [architecture.md](architecture.md#13-appcontextstartup--shutdown),
> `AppContext.shutdown()` called `os._exit(0)`, so the first `tearDownClass` ended the run with
> exit code 0 and CI never reported failures. Don't add a hard exit back into code that tests call.

## 2. Test files

| File | What it covers | Needs a running `AppContext` |
|---|---|---|
| `test_config.py` | `CONFIG` read, write and validation on a temporary copy of the template | no |
| `test_data_frame_factory.py` | Building beacon, ping, ARQ, CQ and burst frames; payload sizes | no (config only) |
| `test_data_type_handler.py` | raw, lzma and gzip handling in `ARQDataTypeHandler` | yes |
| `test_message_database.py` | Adding, deleting and updating messages, attachments, attempt counters | yes |
| `test_message_p2p.py` | `MessageP2P` from API params, payloads with attachments | yes |
| `test_protocols.py` | PING → PING_ACK and CQ → QRV through the real frame dispatcher | yes |
| `test_arq_session.py` | A full ARQ transfer (1000 random bytes) between two stations; IRS success event | two |
| `test_message_protocol.py` | A P2P message sent over an ARQ session, checked on both stations | two |
| `test_norm_protocol.py` | Sending a NORM broadcast (smoke test, see section 5) | two |
| `test_rx_audio_callback.py` | RX audio callback/worker split and re-blocking to whole DSP blocks | yes (not started) |
| `test_api_fixes.py` | `GET /freedata/messages/{id}` (object / 404, called directly), broadcast DB helpers (read-only per-domain GET with `priority`, `mark_domain_as_read`, delete `not_found`), `Norm` priority coercion, `channel_busy` in state events, `POST /config` restarting only for non-GUI changes (fake ctx with its own config copy) | yes |
| `test_server.py` | Starts the real server as a subprocess; `/`, `GET /config`, `POST /config`, 404 for unknown message id and broadcast delete, 409 for `POST /freedata/broadcasts` with group chat disabled, `PATCH /freedata/broadcasts/{domain}/read` | separate process |
| `test_p2p_connection.py` | Disabled, see section 5 | — |

## 3. Test environment isolation

[`tests/testenv.py`](../../tests/testenv.py) creates a temporary directory per test process and:

- sets `FREEDATA_DATABASE` to a database file inside it (only if the variable isn't already set);
- provides `testenv.config_path()`, which returns a temporary copy of `config.ini.example`.

Every test module imports it **before** any `freedata_server` import and passes
`testenv.config_path()` to `AppContext` / `CONFIG`. Without it, tests would rewrite the tracked
`config.ini.example` and write messages into the user's real database in the FreeDATA app directory
(`%APPDATA%\FreeDATA` on Windows). The temporary directory is removed when the process exits.

`test_server.py` passes the same config to the server subprocess through `FREEDATA_CONFIG`, and the
subprocess inherits `FREEDATA_DATABASE`. It starts the server with `sys.executable`, so it uses the
interpreter running the tests rather than whatever `python3` is on `PATH`.

## 4. Test mode

There are two separate switches:

| Switch | Set by | Effect |
|---|---|---|
| `ctx.TESTMODE = True` (set before `ctx.startup()`) | the test | `start_modem()` skips audio devices and starts the demodulators with no stream; `modem.transmit()` puts `[mode, frames]` into `ctx.TESTMODE_TRANSMIT_QUEUE` instead of playing audio; every event is also copied into `ctx.TESTMODE_EVENTS`. |
| `frame_handler.TESTMODE = True` (module-level) | the test | `FrameHandler.transmit()` broadcasts the reply frame as an event instead of calling the modem. Only `test_protocols.py` uses it, and it resets it in `tearDownClass`, because it is global to the process. |

### Simulating the radio link

The two-station tests run two `channelWorker` threads. Each one takes frames from one station's
`TESTMODE_TRANSMIT_QUEUE`, appends 2 bytes to stand in for the CRC, optionally drops the frame
(`loss_probability`), and passes it to the other station's
`service_manager.frame_dispatcher.process_data(...)`.

### Reading events

Read events from **`ctx.TESTMODE_EVENTS`**, not from `ctx.modem_events` /
`event_manager.queues[0]`. The WebSocket manager's events worker also reads `modem_events`, so a
test reading that queue loses events to it at random.

Received frames show up as `{"type": "frame-handler", "received": "<FRAME_TYPE>", ...}`. The end of
an ARQ transfer shows up as `{"arq-transfer-outbound": {...}}` on the ISS and
`{"arq-transfer-inbound": {...}}` on the IRS, with `success` or `ABORTED` in the inner dict.

## 5. Writing tests

- Import `testenv` first and use `testenv.config_path()`.
- Set `ctx.TESTMODE = True` before `ctx.startup()` and call `ctx.shutdown()` in `tearDownClass`.
- Stop and `join()` every non-daemon thread the test starts. Register the cleanup with
  `self.addCleanup(...)` right after starting the threads, so it also runs when an assertion fails;
  otherwise the interpreter never exits.
- Wait with a timeout, and assert on the event you waited for. A wait loop that consumes the
  "session ended" event and then checks the rest of the queue can never fail.
- Avoid non-ASCII characters in `print()`. On Windows, redirected output uses cp1252 and raises
  `UnicodeEncodeError`.
- Handlers wait before replying: CQ waits a random 0–5 s before sending QRV, and messages wait for a
  free channel. Use timeouts of about 15 s for those exchanges.

## 6. Gaps

- `test_p2p_connection.py` has no runnable test. Its only test is named `DisabledtestConnect`, and
  its setup uses old constructor signatures (`CONFIG(path)`, a 5-argument `DISPATCHER`,
  `SocketInterfaceHandler(modem, config, state, event)`), so it has to be rewritten before it can
  run again.
- `test_arq_session.py` has several disabled tests (`Disabled...`): small payload with frame loss,
  ISS/IRS abort and session cleanup.
- `test_norm_protocol.py` only checks that sending a broadcast doesn't fail. It swallows exceptions
  from `Norm.run()` and NORM emits no `arq-transfer-*` events, so its success check never runs.
- No tests cover the socket interface, the radio backends or the REST endpoints beyond `/` and `/config`.
