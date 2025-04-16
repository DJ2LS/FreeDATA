from data_frame_factory import DataFrameFactory
import queue
from codec2 import FREEDV_MODE
import structlog
from state_manager import StateManager
from arq_data_type_handler import ARQDataTypeHandler


class TxCommand:
    """Base class for transmit commands.

    This class provides a common interface and basic functionality for all
    transmit commands, including logging, parameter handling, frame building,
    and transmission via the modem.
    """

    def __init__(self, config: dict, state_manager: StateManager, event_manager, apiParams:dict = {}, socket_interface_manager=None):
        """Initializes a new TxCommand instance.

        This method sets up the command with the given configuration, state
        manager, event manager, API parameters, and socket command handler.
        It also initializes a DataFrameFactory for building frames and an
        ARQDataTypeHandler for ARQ data handling.

        Args:
            config (dict): The configuration dictionary.
            state_manager (StateManager): The state manager object.
            event_manager: The event manager object.
            apiParams (dict, optional): API parameters for the command. Defaults to {}.
            socket_command_handler (optional): The socket command handler object. Defaults to None.
        """
        self.config = config
        self.logger = structlog.get_logger(type(self).__name__)
        self.state_manager = state_manager
        self.event_manager = event_manager
        self.set_params_from_api(apiParams)
        self.frame_factory = DataFrameFactory(config)
        self.arq_data_type_handler = ARQDataTypeHandler(event_manager, state_manager)
        self.socket_interface_manager = socket_interface_manager

    def log(self, message, isWarning = False):
        """Logs a message with the command's name.

        This method logs a message prefixed with the command's name, using
        either a warning or info log level based on the isWarning flag.

        Args:
            message (str): The message to log.
            isWarning (bool, optional): Whether to log as a warning. Defaults to False.
        """
        msg = f"[{type(self).__name__}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def set_params_from_api(self, apiParams):
        """Sets parameters from the API.

        This method is intended to be overridden by subclasses to handle
        setting specific parameters from the API request.

        Args:
            apiParams (dict): A dictionary of API parameters.
        """
        pass

    def get_name(self):
        """Returns the name of the command.

        This method returns the name of the command, which is the name of the
        class.

        Returns:
            str: The name of the command.
        """
        return type(self).__name__

    def emit_event(self, event_queue):
        """Emits an event to the event queue.

        This method is a placeholder for emitting events related to the
        command's execution. It's intended to be overridden by subclasses
        to provide specific event handling.

        Args:
            event_queue (queue.Queue): The event queue.
        """
        pass

    def log_message(self):
        """Generates a log message for the command.

        This method returns a string indicating that the command is running,
        including the command's name.

        Returns:
            str: The log message.
        """
        return f"Running {self.get_name()}"

    def build_frame(self):
        """Builds the frame for the command.

        This method is a placeholder for building the frame to be transmitted.
        It's intended to be overridden by subclasses to generate the
        appropriate frame data.
        """
        pass

    def get_tx_mode(self):
        """Returns the transmission mode for the command.

        This method returns the default transmission mode for the command,
        which is FREEDV_MODE.signalling. Subclasses can override this method
        to specify a different mode.

        Returns:
            FREEDV_MODE: The transmission mode.
        """

        if self.config['EXP'].get('enable_vhf'):
            mode = FREEDV_MODE.data_vhf_1
        else:
            mode = FREEDV_MODE.signalling

        return mode
    
    def make_modem_queue_item(self, mode, repeat, repeat_delay, frame):
        """Creates a dictionary representing a modem queue item.

        This method creates a dictionary containing the parameters for a
        modem transmission, including the mode, repeat count, repeat delay,
        and the frame data.

        Args:
            mode: The transmission mode.
            repeat (int): The number of times to repeat the transmission.
            repeat_delay (float): The delay between repetitions in seconds.
            frame (bytearray): The frame data to transmit.

        Returns:
            dict: A dictionary representing the modem queue item.
        """
        return {
            'mode': mode,
            'repeat': repeat,
            'repeat_delay': repeat_delay,
            'frame': frame,
        }

    def transmit(self, modem):
        """Transmits the command frame via the modem.

        This method builds the command frame and transmits it once using the
        modem with the configured transmission mode.

        Args:
            modem: The modem object.
        """
        frame = self.build_frame()
        modem.transmit(self.get_tx_mode(), 1, 0, frame)

    def run(self, event_queue: queue.Queue, modem):
        """Runs the command.

        This method emits an event to the event queue, logs a message
        indicating the command is running, and transmits the command frame
        via the modem.

        Args:
            event_queue (queue.Queue): The event queue.
            modem: The modem object.
        """
        self.emit_event(event_queue)
        self.logger.info(self.log_message())
        self.transmit(modem)

    def test(self, event_queue: queue.Queue):
        """Tests the command by building and returning the frame.

        This method emits an event, logs a message, and builds the frame
        that would be transmitted, but doesn't actually transmit it.
        This is useful for testing the frame building logic without
        using the modem.

        Args:
            event_queue (queue.Queue): The event queue.

        Returns:
            bytearray: The built frame.
        """
        self.emit_event(event_queue)
        self.logger.info(self.log_message())
        return self.build_frame()
