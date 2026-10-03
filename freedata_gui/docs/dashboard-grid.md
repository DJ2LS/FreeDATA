# Dashboard grid, waterfall and RX audio

This page documents the main dashboard of the FreeDATA GUI: the gridstack
layout in [dynamic_components.vue](../src/components/dynamic_components.vue),
the widgets in [src/components/grid/](../src/components/grid/), the waterfall
([waterfallHandler.js](../src/js/waterfallHandler.js),
[spectrum.js](../src/assets/waterfall/spectrum.js)) and RX audio playback
([grid_audio.vue](../src/components/grid/grid_audio.vue),
[audioStore.js](../src/store/audioStore.js),
[audioStreamHandler.js](../src/js/audioStreamHandler.js)).

`dynamic_components.vue` is mounted by
[main_screen.vue](../src/components/main_screen.vue).

## 1. Gridstack setup

The grid is created in `onMounted` with
`GridStack.init(...)` (gridstack `^12.3.3`):

| Option | Value | Effect |
|---|---|---|
| `column` | 24 | 24 columns; width CSS for `.gs-24` is hand-written in the component's `<style>` block |
| `cellHeight` | `"5px"` | One row unit is 5 px, which is why widget heights are large numbers (8 to 92) |
| `margin` | 5 | |
| `minRow` | 50 | |
| `float` | true | Widgets stay where they are dropped (no gravity) |
| `draggable` | `{ scroll: true }` | |
| `resizable` | `{ handles: "se,sw" }` | Resize from the bottom corners only |

The `grid` instance is a plain `let`, not a `ref`, on purpose (a comment
links gridstack issue #2115: Vue proxies break gridstack's object comparison).

Rendering is Vue-driven: `items` (a `ref([])`) holds one node per placed
widget, `{x, y, w, h, id: "w_<n>", component2, autoPlace}`. The template
renders one `.grid-stack-item` per node with `gs-x/gs-y/gs-w/gs-h/gs-id` and
`gs-auto-position`, and `<component :is="w.component2">` inside. After Vue
renders the DOM, `nextTick(() => grid.makeWidget(node.id))` hands it to
gridstack.

## 2. Widget registry

`gridWidgets` is an array of `gridWidget` objects:
`new gridWidget(component, size, text, quickFill, autoPlace, category, id, quickFillSM, sizeSM)`.

- `id` is persisted in saved layouts. The source comment says never to change
  it. IDs in use: 0 to 22 and 24 (23 is unused).
- `size` is used for the normal "Fill grid" and for picker adds. `sizeSM` is
  used by "Fill grid (small screen)".
- `autoPlace` is `true` for every widget. Fill and restore set it to `false`
  for a moment so the stored position is used.
- `category` picks the picker accordion section (`<category>Body` DOM id).

Size columns are `x,y,w,h` in grid units (w out of 24, h in 5 px rows).
"QF" and "QF-SM" mark whether the widget is included by Fill grid and
Fill grid (small screen).

| ID | Picker text | Component | Size (QF) | Size (SM) | Category | QF | QF-SM | Shows | Store fields / API |
|---|---|---|---|---|---|---|---|---|---|
| 0 | Heard stations list (detailed) | [grid_active_heard_stations.vue](../src/components/grid/grid_active_heard_stations.vue) | 0,13,16,40 | 0,53,6,55 | Activity | yes | no | Table: time, frequency, callsign, grid, distance, activity icon, SNR, AFK | `state.heard_stations`; `settings.remote.STATION.mygrid`, `settings.remote.GUI.distance_unit`; ping button calls `sendModemPing` (POST `/modem/ping_ping`); chat button sets `chat.newChatCallsign` / `newChatMessage` and opens `#newChatModal`; row click dispatches `stationSelected` |
| 1 | Stats (waterfall, etc) | [grid_active_stats.vue](../src/components/grid/grid_active_stats.vue) | 16,16,8,87 | 12,0,12,56 | Stats | yes | yes | Tabs: waterfall canvas, constellation scatter, speed/SNR chart; footer with busy-slot S1 to S5 and "data" indicators | `initWaterfall()`; `state.scatter`, `state.arq_speed_list_*`, `state.channel_busy_slot`, `state.is_codec2_traffic` |
| 2 | Audio main | [grid_active_audio.vue](../src/components/grid/grid_active_audio.vue) | 16,0,8,20 | 0,114,6,20 | Audio | no | no | S-meter and dBFS bars side by side | `state.s_meter_strength_percent/raw`, `state.dbfs_level_percent`, `state.dbfs_level` |
| 3 | Rig control main | [grid_active_rig_control.vue](../src/components/grid/grid_active_rig_control.vue) | 0,108,6,25 | 0,114,6,25 | Rig | yes | no | Frequency (opens frequency offcanvas), mode, RF power, tuner switch | `state.frequency`, `state.mode`, `state.rf_level`, `state.tuner`, `state.hamlib_status`; POST `/radio` |
| 4 | Broadcasts main (horizontal) | [grid_active_broadcasts.vue](../src/components/grid/grid_active_broadcasts.vue) | 6,70,6,25 | 6,70,6,25 | Broadcasts | no | no | DX call input, Ping, CQ, beacon toggle | `state.beacon_state`; `sendModemPing`, `sendModemCQ`, `setModemBeacon` |
| 5 | Heard stations list (small) | [grid_active_heard_stations_mini.vue](../src/components/grid/grid_active_heard_stations_mini.vue) | 1,1,6,54 | 0,42,12,42 | Activity | no | yes | Time and callsign only | `state.heard_stations`; row click dispatches `stationSelected` |
| 6 | S-Meter widget | [grid_s-meter.vue](../src/components/grid/grid_s-meter.vue) | 16,0,4,8 | 16,0,4,8 | Rig | yes | no | S-meter bar | `state.s_meter_strength_percent`, `state.s_meter_strength_raw` |
| 7 | Dbfs meter | [grid_dbfs.vue](../src/components/grid/grid_dbfs.vue) | 20,0,4,8 | 20,0,4,8 | Audio | yes | no | RX dBFS bar | `state.dbfs_level_percent`, `state.dbfs_level` |
| 8 | Activities list | [grid_activities.vue](../src/components/grid/grid_activities.vue) | 0,53,6,55 | 0,53,6,55 | Activity | yes | no | Activity log: origin, time, type, direction | `state.activities` (array of `[key, {origin, timestamp, activity_type, direction}]`) |
| 9 | Broadcasts main (vertical) | [grid_active_broadcasts_vert.vue](../src/components/grid/grid_active_broadcasts_vert.vue) | 16,103,8,42 | 16,103,8,42 | Broadcasts | yes | no | DX call + Ping, big CQ button, beacon and AFK switches | `state.beacon_state`, `state.away_from_key`; `sendModemPing`, `sendModemCQ`, `setModemBeacon(enabled, away_from_key)` |
| 10 | Tx/PTT indicator | [grid_ptt.vue](../src/components/grid/grid_ptt.vue) | 2,0,5,13 | 5,0,7,14 | Rig | yes | yes | "ON AIR" tile, yellow while transmitting | `state.ptt_state` |
| 11 | My callsign widget | [grid_mycall.vue](../src/components/grid/grid_mycall.vue) | 7,0,9,13 | 7,0,9,13 | Other | yes | no | `MYCALL-SSID` heading | `settingsStore.remote.STATION.mycall/myssid` |
| 12 | CQ button | [grid_CQ.vue](../src/components/grid/grid_CQ.vue) | 3,27,2,8 | 0,28,12,14 | Broadcasts | no | yes | CQ button, 3 s cooldown | `sendModemCQ` |
| 13 | Ping widget | [grid_ping.vue](../src/components/grid/grid_ping.vue) | 3,27,4,9 | 0,84,12,9 | Broadcasts | no | yes | DX call input + Ping | `sendModemPing`; listens to `stationSelected` |
| 14 | Frequency widget | [grid_frequency.vue](../src/components/grid/grid_frequency.vue) | 20,8,4,8 | 0,114,6,30 | Rig | yes | no | Current frequency in kHz; click opens `#offcanvasFrequency` | `state.frequency` |
| 15 | Stop widget | [grid_stop.vue](../src/components/grid/grid_stop.vue) | 0,0,2,13 | 0,0,5,14 | Other | yes | yes | Stop sign button | `stopTransmission` (POST `/modem/stop_transmission`) |
| 16 | Beacon button | [grid_beacon.vue](../src/components/grid/grid_beacon.vue) | 3,27,3,8 | 0,14,12,14 | Broadcasts | no | yes | Beacon toggle with spinner while active | `state.beacon_state`; `setModemBeacon(bool)` |
| 17 | My callsign widget (small) | [grid_mycall small.vue](../src/components/grid/grid_mycall%20small.vue) | 8,40,4,10 | 8,40,4,8 | Other | no | no | Read-only call / SSID inputs | `settingsStore.remote.STATION.mycall/myssid` |
| 18 | Tune widget | [grid_tune.vue](../src/components/grid/grid_tune.vue) | 16,8,2,8 | 16,8,2,8 | Audio | no | no | Button that opens `#audioModal` | none directly (see section 7) |
| 19 | Scatter graph | [grid_scatter.vue](../src/components/grid/grid_scatter.vue) | 0,114,6,30 | 0,53,6,55 | Stats | no | no | Constellation scatter | `state.scatter` |
| 20 | Speed/SNR graph | [grid_stats_chart.vue](../src/components/grid/grid_stats_chart.vue) | 0,114,6,30 | 0,114,6,30 | Stats | no | no | ARQ speed (bar) and SNR (line) | `state.arq_speed_list_timestamp/bpm/snr` |
| 21 | SWR widget | [grid_swr_meter.vue](../src/components/grid/grid_swr_meter.vue) | 16,8,4,8 | 16,8,4,8 | Rig | yes | no | SWR bar and `SWR 1:x` | `state.swr_percent`, `state.swr_raw` |
| 22 | Station Map | [grid_stations_map.vue](../src/components/grid/grid_stations_map.vue) | 6,53,10,92 | 12,56,12,92 | Other | yes | yes | d3 world map with own and heard stations | `state.heard_stations`, `settings.remote.STATION.mygrid` |
| 24 | Audio Stream | [grid_audio.vue](../src/components/grid/grid_audio.vue) | 16,8,4,24 | 16,8,4,24 | Audio | no | no | Start/Stop button for RX audio monitoring | `useAudioStore().getNextBlock()` |

[grid_button.vue](../src/components/grid/grid_button.vue) is not a widget. It is
the picker button (see section 3).

### Adding a widget

1. Create `src/components/grid/grid_<name>.vue`.
2. Import it in `dynamic_components.vue` and add a `new gridWidget(...)` entry
   with a new unique `id`. The end-of-array comment says "Next new widget ID
   should be 25", which is correct (24 is Audio Stream).
3. `category` must be one of `Activity`, `Audio`, `Broadcasts`, `Rig`,
   `Stats`, `Other`. These map to the DOM ids `activityBody`, `audioBody`,
   `broadcastsBody`, `rigBody`, `statsBody`, `otherBody`. Any other value means
   no picker button is created.
4. Widget root elements usually use `h-100`/`w-100` so they fill the cell.
   Button-like widgets use `width: calc(100% - 24px)` to leave room for the
   close button.

## 3. Widget picker, edit mode, add and remove

- A fixed "Grid edit" tab on the right edge opens the Bootstrap offcanvas
  `#offcanvasGridItems`.
- On mount, the code loops over `gridWidgets` and, for each one, inserts
  `<div id="gridbtn-<index>">` into the matching accordion body. It then
  renders a `grid_button` into that div with Vue's low-level
  `render(h(grid_button, {btnText, btnID: index}), el)`. `btnID` is the
  **array index**, not the widget `id`.
- Clicking the button dispatches `window` event `add-widget` with
  `detail = index`. `dynamic_components.vue` handles it in `onAddWidget`
  with `addNewWidget2(gridWidgets[index], true)` (unknown indexes are
  ignored). The widget is auto-placed (`gs-auto-position`) and the layout is
  saved. The listener is registered in `onMounted` before the layout is
  restored and removed in `onBeforeUnmount`.
- Lock/unlock button: `toggleGridEdit()` flips
  `settingsStore.local.grid_enabled` and calls `grid.enable()` or
  `grid.disable()`. The close (X) button on each widget is only visible while
  unlocked.
- `remove(w)` splices the node from `items`, calls
  `grid.removeWidget('#id', false)`, and saves.
- "Clear grid" (`clearAllItems`) calls `grid.removeAll(false)`, empties
  `items`, and saves an empty layout. The `w_<n>` counter is deliberately not
  reset, so a new widget never reuses the id/key of a removed one.
- "Fill grid" / "Fill grid (small screen)" (`quickfill` / `quickfillSM`)
  first clear the grid, then add every widget flagged `quickFill` /
  `quickFillSM` at its `size` / `sizeSM`. Pressing them twice no longer
  duplicates widgets.

## 4. Layout persistence and presets

All layout state is client side. It lives in `settingsStore.local`
([settingsStore.js](../src/store/settingsStore.js)), which is stored in
browser `localStorage` under the key `localConfig`. Nothing is sent to the
server.

| Key | Default | Meaning |
|---|---|---|
| `grid_layout` | `"[]"` | JSON **string** of the current layout |
| `grid_preset` | `"[]"` | JSON string of the user's saved preset |
| `grid_enabled` | `true` | Edit mode unlocked |

Layout format: `[[x, y, w, h, widgetId], ...]`.

- **Save**: `saveGridLayout()` runs on every gridstack `change` event
  (`onChange`), on add, on remove and on clear. It maps each node back to its
  registry entry by `component2.__name`, writes `grid_layout`, and calls
  `saveLocalSettingsToConfig()`. A deep `watch` in settingsStore also persists
  any change to `local`.
- **Validation** (`parseLayout(text, strict)`): parses the JSON (a layout
  that was JSON-encoded twice, as in some older configs, is unwrapped), and
  keeps only entries that are 5-element arrays of finite numbers whose last
  element is a known widget id. It returns `null` if the text is not valid
  JSON or not an array. In strict mode (uploaded files) it also returns
  `null` if any entry is invalid or the layout is empty.
- **Restore**: `restoreGridLayoutFromConfig()` only runs when `items` is
  empty. It reads `grid_layout` with `parseLayout(..., false)`, so invalid
  entries and unknown ids are dropped; an unusable layout is logged and
  nothing is restored. For each tuple it looks up the widget by `id`,
  temporarily sets `autoPlace=false` and `size={x,y,w,h}`, and adds it. In
  `onMounted` the call is wrapped in `try/catch`; on an exception the grid is
  emptied.
- **First run / bad layout**: if nothing was restored, `quickfill()` builds
  the default layout.
- **Save preset**: copies `grid_layout` into `grid_preset`.
- **Restore preset** (`loadPreset`): validates `grid_preset` first. If it is
  unusable or empty, a toast "No valid saved grid preset. Current layout was
  kept." is shown and nothing changes. Otherwise it clears the grid, copies
  `grid_preset` into `grid_layout`, and restores.
- **Download preset**: saves `grid_layout` (with any surrounding quotes
  removed) as `FreeDATA_GUI_preset.freedata`.
- **Upload preset**: reads a `.freedata` file and validates it with
  `parseLayout(content, true)`. An invalid file shows a toast "Invalid preset
  file. Current layout and preset were kept." and changes nothing. A valid
  file is stored (re-serialised) in `grid_preset`, **replacing the saved
  preset**, and then `loadPreset()` runs.

## 5. Frequency offcanvas

`dynamic_components.vue` also contains `#offcanvasFrequency`. It is opened by
the Frequency widget and by the QRG button in Rig control. It has a free-text
frequency input bound to `state.new_frequency` and a list of band presets
(50.616, 50.308, 28.093, 27.265, 27.245, 24.908, 21.093, 18.106, 14.093,
7.053 MHz). Both the input and the presets call
`setRadioParametersFrequency()`, which sends POST `/radio`
`{radio_frequency}`.

## 6. Waterfall

### Data flow

```
server /fft websocket (text frames, JSON array of numbers)
  -> event_sock.js connect("fft", addDataToWaterfall)
  -> waterfallHandler.addDataToWaterfall(data): JSON.parse, ignore non-arrays
  -> for every registered Spectrum: spectrum.addData(bins)
  -> Spectrum draws a new row on an offscreen canvas and copies it, scaled, to the widget's <canvas>
```

- [event_sock.js](../src/js/event_sock.js) opens `ws(s)://host:port/fft`. If
  the page runs on port 8080 (the dev server), port 5000 is used instead. The
  socket reconnects 1 s after it closes. Only the `/states` socket runs
  `loadAllData()` on open, and errors on `/fft` do not mark the server as
  disconnected.
- [grid_active_stats.vue](../src/components/grid/grid_active_stats.vue)
  renders `<canvas :id="gridwfid-<random>">`, calls `initWaterfall(id)` in
  `onMounted` and keeps the returned instance; `onBeforeUnmount` passes it to
  `removeWaterfall()`.
- `initWaterfall(id)` in [waterfallHandler.js](../src/js/waterfallHandler.js)
  runs `new Spectrum(id, {spectrumPercent: 0, wf_rows: 1024, wf_size: 1024})`,
  applies `settings.local.wf_theme`, pushes the instance onto the
  module-level `spectrums` array and returns it. Every instance in that array
  gets every FFT frame. `removeWaterfall(spectrum)` takes an instance out of
  the array, so a removed Stats widget stops receiving data.
- `setColormap()` re-applies `wf_theme` to all instances. It is called from
  [settings_gui.vue](../src/components/settings_gui.vue) when the theme
  select changes.

### spectrum.js API used

[spectrum.js](../src/assets/waterfall/spectrum.js) is a vendored copy of Jeppe
Ledet-Pedersen's MIT "HTML Canvas/WebSockets Waterfall" with DJ2LS changes.
It is converted to an ES module (`export function Spectrum`) and has the
colormaps pasted at the end of the file.

| Member | Used by GUI | Notes |
|---|---|---|
| `new Spectrum(canvasId, options)` | yes | Options: `centerHz` (1500), `spanHz` (0), `wf_size`, `wf_rows` (512), `spectrumPercent`, `spectrumPercentStep`, `averaging`, `maxHold`. dB range is fixed at `min_db=0`, `max_db=70` |
| `addData(bins)` | yes | If `bins.length` changes, resizes the offscreen canvas. Then calls `drawSpectrum()`, `addWaterfallRow(bins)` and `resize()`. Does nothing while paused |
| `setColorMap(index)` | yes | `this.colormap = colormaps[index]` |
| `drawSpectrum()` | internal | Draws fixed bandwidth marker lines on the waterfall canvas (x = 28.1/65/121.6/178.4/235/271.9 in bin units), fills the main canvas white, then returns early. The FFT line plot, averaging and max-hold code is commented out |
| `addWaterfallRow(bins)` | internal | Scrolls the offscreen canvas down 1 px, maps each bin to a colormap index with `squeeze()` (0 to 70 dB onto 0 to 255), and draws it scaled to the visible canvas |
| `resize()` | internal | Sizes the canvas to its parent. Falls back to 500x250 if the parent has zero size |
| `setRange`, `setPaused`, `toggleColor`, `setMaxHold`, `toggleFullscreen`, `onKeypress`, ... | no | Present, but nothing in the GUI calls them and no key listener is attached |

Because `spectrumPercent` is 0, only the waterfall is drawn (no spectrum
trace or axes).

### Colormaps

`colormaps = [turbo, fosphor, viridis, inferno, magma, jet, binary, plasma, rainbow, ocean]`,
each a 256-entry RGB table. The `wf_theme` setting is the index into this
array. Its default is `2` (viridis, shown as "Default" in settings).

`spectrum.js` is based on Jeppe Ledet-Pedersen's MIT-licensed waterfall; its
[LICENSE](../src/assets/waterfall/LICENSE) and README are kept next to it.

## 7. RX audio playback

### Data flow

```
server /audio_rx websocket (binary frames, int16 PCM mono)
  -> event_sock.js connect("audio_rx", addDataToAudio)   binaryType = "arraybuffer"
  -> audioStreamHandler.addDataToAudio(buf): whole int16 samples copied
  -> audioStore.addBlock(int16)                            ring buffer, 1024 blocks
  -> grid_audio.vue loop(): drain getNextBlock() -> Float32 -> AudioBuffer -> schedule
```

- `binaryType = "arraybuffer"` is set for any endpoint whose name contains
  `audio`.
- [audioStreamHandler.js](../src/js/audioStreamHandler.js) ignores anything
  that is not an `ArrayBuffer`, drops a trailing odd byte, ignores frames
  with no complete sample, and copies the samples with
  `new Int16Array(data.slice(...))` (little-endian, platform byte order)
  before calling `audio.addBlock(copy)`. Any number of samples is accepted.
- [audioStore.js](../src/store/audioStore.js) has a fixed ring buffer of
  `BUFFER_SIZE = 1024` blocks with `writePtr`/`readPtr`/`readyBlocks`. When
  it is full, the oldest block is overwritten. `getNextBlock()` returns
  `null` when the buffer is empty. The buffer fills whether or not anyone is
  listening; `resetBuffer()` empties it.
- [grid_audio.vue](../src/components/grid/grid_audio.vue):
  - **Start** calls `audio.resetBuffer()` (drops audio buffered while nobody
    listened), creates `new AudioContext({sampleRate: 8000})`, resumes it if
    it is suspended (stopping again if that fails), and starts `loop(ctx)`.
  - Every 20 ms (`POLL_MS`) the loop drains **all** buffered blocks. Each
    block is converted with `s / 32768` to Float32, put in a 1-channel
    8000 Hz `AudioBuffer` and scheduled with `source.start(nextStartTime)`;
    `nextStartTime` then advances by the buffer duration, so blocks play
    back-to-back on the audio clock.
  - After an underrun (or for the first block) playback restarts 100 ms in
    the future (`START_DELAY_S`) to absorb network jitter. If more than 1 s
    of audio is already scheduled (`MAX_QUEUED_S`), new blocks are dropped
    to keep latency bounded. A block that fails to schedule is skipped with a
    warning instead of ending the loop.
  - The loop ends when `isPlaying` is false or a newer context replaced the
    one it was started with.
  - **Stop** sets `isPlaying=false`, clears the loop timer and closes the
    context. `onBeforeUnmount` calls Stop, so removing the widget while it
    plays stops playback.

### Chunk length (800 vs 2400 samples)

The GUI takes the buffer length from each block (`float32.length`), so any
non-zero number of samples plays, including the server's 800-sample
(100 ms at 8 kHz) chunks. Odd byte lengths and empty frames are handled in
`addDataToAudio` (see above).

## 8. Charts and meters

All Chart.js charts use `vue-chartjs` (`chart.js ^4.5.1`). Each component
registers the scales and elements it needs; the two speed/SNR charts mix a
bar dataset into a `Line` chart, so they also register `BarController` and
`BarElement`.

| Widget | Type | Data |
|---|---|---|
| [grid_scatter.vue](../src/components/grid/grid_scatter.vue) | `Scatter` | `state.scatter` (set in [eventHandler.js](../src/js/eventHandler.js) from `JSON.parse(data.scatter)`). Axes hidden, zero lines 3 px, no legend or tooltip |
| [grid_stats_chart.vue](../src/components/grid/grid_stats_chart.vue) | `Line` with a line (SNR, right axis `SNR`) and a bar (speed in bytes per minute, left axis `SPEED`) dataset | `computed` chart data: labels `state.arq_speed_list_timestamp`, data `state.arq_speed_list_snr` / `state.arq_speed_list_bpm` |
| [grid_active_stats.vue](../src/components/grid/grid_active_stats.vue) | Same scatter and speed charts, as tabs next to the waterfall | Same plain arrays in a `computed` (the event handler replaces the arrays, so the charts update) |
| [grid_s-meter.vue](../src/components/grid/grid_s-meter.vue) | Bootstrap progress bar | width = `s_meter_strength_percent`%, label `s_meter_strength_raw`; scale bar segments 1/64/14/21 % (sum 100) |
| [grid_dbfs.vue](../src/components/grid/grid_dbfs.vue) | progress bar | width and `aria-valuenow` = `dbfs_level_percent`, label `dbfs_level` dBFS; same 1/64/14/21 % scale |
| [grid_swr_meter.vue](../src/components/grid/grid_swr_meter.vue) | progress bar | width and bound `:aria-valuenow` = `swr_percent` (`aria-valuemax` 100), label `SWR 1:swr_raw`; static 25/50/25 green/yellow/red scale |
| [grid_active_audio.vue](../src/components/grid/grid_active_audio.vue) | two progress bars | S-meter and dBFS together, same scales |

None of the meters set element ids any more, so several meter widgets can be
on the grid at the same time without duplicate DOM ids.

### Stations map

[grid_stations_map.vue](../src/components/grid/grid_stations_map.vue) uses
`d3` (`^7.9.0`), `topojson-client` and `qth-locator`:

- On mount, and on every window `resize`, `drawMap()` rebuilds an SVG with a
  `d3.geoMercator()` projection scaled to the container width.
- It lazily imports `@/assets/countries-50m.json` and converts it with
  `feature(world, world.objects.countries)`.
- It draws the countries (paths with class `country-path`, so the zoom
  handler can rescale their stroke) and two label layers: all country names,
  shown when zoom k >= 3, and the 10 largest by `d3.geoArea`, shown when
  k < 3.
- `updatePinsAndLines()` draws:
  - a blue pin for `settings.remote.STATION.mygrid`;
  - a red pin for every `state.heard_stations` entry with a usable
    `gridsquare` (not empty and not `------`);
  - blue lines from your own station to each heard station.

  Hovering a pin puts its text in the header input. For heard stations the
  distance is given in `settings.remote.GUI.distance_unit` (`km`, `mi` or
  `nm`, converted from km).
- A deep `watch` on `state.heard_stations` re-runs `updatePinsAndLines()`
  once the map group exists, so pins follow new stations without a resize.
- `d3.zoom` allows a scale of 1 to 8. The zoom handler rescales pins, line
  widths, country strokes and labels. The header buttons are zoom in (x1.2),
  home (`centerMap()`: redraws pins and pans to mygrid) and zoom out (x0.8).
- `centerMap()` also runs once, 1.5 s after setup. It returns early if the
  map is not drawn yet, and the timer is cleared on unmount together with
  the window `resize` listener.

## 9. Control widgets and their API calls

All calls go through [api.js](../src/js/api.js). They are all POSTs, so a
failure (for example 503 "Modem not running") shows an error toast with the
server's message (see [architecture.md](architecture.md#71-transport-helpers)).

| Widget(s) | Action | API call |
|---|---|---|
| Stop | `stopTransmission()` | POST `/modem/stop_transmission` |
| CQ button, Broadcasts (both) | `sendModemCQ()`; the button is disabled or shows a "sending" label for 3 s | POST `/modem/cqcqcq` |
| Ping widget, Broadcasts (both), Heard stations (detailed) | `sendModemPing(call)`: upper-cases the call and appends `-0` when there is no SSID; does nothing if the call is still invalid | POST `/modem/ping_ping` `{dxcall}` |
| Beacon button, Broadcasts (horizontal) | `setModemBeacon(!state.beacon_state)` | POST `/modem/beacon` `{enabled, away_from_key:false}` |
| Broadcasts (vertical) | beacon switch / AFK switch | POST `/modem/beacon` `{enabled, away_from_key: state.away_from_key}` |
| Rig control | mode select / power select / tuner switch | POST `/radio` `{radio_mode}` / `{radio_rf_level}` / `{radio_tuner}` |
| Frequency widget, Rig control QRG | open `#offcanvasFrequency` (section 5) | POST `/radio` `{radio_frequency}` |
| Tune | opens `#audioModal` in [main_modals.vue](../src/components/main_modals.vue). That modal has the tune buttons (`sendSineTone(true/false)` = POST `/radio/tune` `{enable_tuning}`) and the test frame button (POST `/modem/send_test_frame`) | none in the widget itself |
| Tx/PTT indicator | display only | `state.ptt_state` |

`stationSelected` (window `CustomEvent`, `detail` = callsign) is dispatched by
both heard-station lists. It is consumed by the Ping widget and both
Broadcasts widgets to pre-fill the DX call input. They add the window
listener in `onMounted` and remove it in `onBeforeUnmount`. The Ping/CQ
buttons in the two Broadcasts widgets have their own ids
(`broadcastsSendPing`/`broadcastsSendCQ` and
`broadcastsVertSendPing`/`broadcastsVertSendCQ`); the Ping widget keeps
`sendPing`.

## 10. Known issues

Grid / layout:

- Uploading a valid preset silently overwrites the user's saved
  `grid_preset` (by design of `uploadPreset`, but there is no confirmation).
- The picker accordion's ids and labels do not match (for example,
  `headingAudioControl` is the "statistics" section). This is cosmetic.

Waterfall:

- The bandwidth marker lines are hard-coded positions in bin units, so they
  are only correct for the bin spacing assumed in the source comment. The
  comment itself says "Math not correct".

RX audio:

- The ring buffer still fills (up to 1024 blocks, about 102 s at 800
  samples) while nobody listens. Start discards it, so it only costs memory.
- `audioStore.rxStream` is a legacy array that nothing uses.

Heard stations / map:

- In the detailed heard list, the station-info button is permanently
  `disabled`.
- In the map:
  - The `.popup` div is never shown (`popupStyle` is never set); hover text
    goes to the header input instead.
  - The map height is fixed at 400 px no matter how big the widget is.
