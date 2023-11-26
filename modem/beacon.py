import threading
import data_frame_factory
import time
import command_beacon

modem_config = None
states = None
beacon_interval = 0
beacon_interval_timer = 0
beacon_paused = False
beacon_thread = None
frame_factory = None
event_manager = None
log = None

def init(config, modem_states, ev_manager, logger):
    modem_config = config
    states = modem_states
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
                        #and not arq_file_transfer
                        and not beacon_paused
                        #and not states.channel_busy
                        and not states.is_modem_busy
                        and not states.is_arq_state
                ):
                    
                    cmd = command_beacon.BeaconCommand(modem_config, log)
                    cmd.run()

                beacon_interval_timer = time.time() + beacon_interval
                while (
                        time.time() < beacon_interval_timer
                        and states.is_beacon_running
                        and not beacon_paused
                ):
                    threading.Event().wait(0.01)

    except Exception as err:
        log.debug("[Modem] run_beacon: ", exception=err)
