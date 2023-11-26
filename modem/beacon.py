import threading
import data_frame_factory
import time

modem_config = None
modem_states = None
beacon_interval = 0
beacon_interval_timer = 0
beacon_paused = False
beacon_thread = None
frame_factory = None
event_manager = None
log = None

def init(config, states, ev_manager, logger):
    modem_config = config
    modem_states = states
    frame_factory = data_frame_factory.DataFrameFactory(modem_config)
    event_manager = ev_manager
    log = logger

def start():
    beacon_thread = threading.Thread(
        target=start, name="beacon", daemon=True
    )

    beacon_thread.start()

def run_beacon() -> None:
    """
    Controlling function for running a beacon
    Args:

        self: arq class

    Returns:

    """
    try:
        while True:
            threading.Event().wait(0.5)
            while states.is_beacon_running:
                if (
                        not states.is_arq_session
                        and not arq_file_transfer
                        and not beacon_paused
                        #and not self.states.channel_busy
                        and not states.is_modem_busy
                        and not states.is_arq_state
                ):
                    event_manager.send_custom_event(
                        freedata="modem-message",
                        beacon="transmitting",
                        dxcallsign="None",
                        interval=self.beacon_interval,
                    )
                    self.log.info(
                        "[Modem] Sending beacon!", interval=self.beacon_interval
                    )

                    beacon_frame = bytearray(self.length_sig0_frame)
                    beacon_frame[:1] = bytes([FR_TYPE.BEACON.value])
                    beacon_frame[1:7] = helpers.callsign_to_bytes(self.mycallsign)
                    beacon_frame[7:11] = helpers.encode_grid(self.mygrid)

                    if self.enable_fsk:
                        self.log.info("[Modem] ENABLE FSK", state=self.enable_fsk)
                        self.enqueue_frame_for_tx(
                            [beacon_frame],
                            c2_mode=FREEDV_MODE.fsk_ldpc_0.value,
                        )
                    else:
                        self.enqueue_frame_for_tx([beacon_frame], c2_mode=FREEDV_MODE.sig0.value, copies=1,
                                                    repeat_delay=0)
                        if self.enable_morse_identifier:
                            MODEM_TRANSMIT_QUEUE.put(["morse", 1, 0, self.mycallsign])

                self.beacon_interval_timer = time.time() + self.beacon_interval
                while (
                        time.time() < self.beacon_interval_timer
                        and self.states.is_beacon_running
                        and not self.beacon_paused
                ):
                    threading.Event().wait(0.01)

    except Exception as err:
        self.log.debug("[Modem] run_beacon: ", exception=err)
