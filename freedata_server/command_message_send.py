from command import TxCommand
import api_validations
import base64
from queue import Queue
from arq_session_iss import ARQSessionISS
from message_p2p import MessageP2P
from arq_data_type_handler import ARQ_SESSION_TYPES
from message_system_db_manager import DatabaseManager
from message_system_db_messages import DatabaseManagerMessages
import threading
import numpy as np
import time


class SendMessageCommand(TxCommand):
    """Command to send a P2P message using an ARQ transfer session"""

    def set_params_from_api(self, apiParams):
        """Sets parameters from the API request.

        This method creates a MessageP2P object from the API parameters,
        and adds the message to the database with the status 'queued'.

        Args:
            apiParams (dict): A dictionary containing the API parameters.
        """
        origin = f"{self.ctx.config_manager.config['STATION']['mycall']}-{self.ctx.config_manager.config['STATION']['myssid']}"
        self.message = MessageP2P.from_api_params(origin, apiParams)
        DatabaseManagerMessages(self.ctx).add_message(
            self.message.to_dict(),
            statistics={},
            direction="transmit",
            status="queued",
            frequency=self.ctx.state_manager.radio_frequency,
        )

    def transmit(self):
        """Transmits the first queued message using ARQ.

        This method retrieves the first queued message from the database,
        prepares the data using the ARQ data type handler, creates an
        ARQSessionISS, and starts the transmission. It includes error
        handling and logging.

        Args:
            modem: The modem object.
        """
        if self.ctx.state_manager.getARQ():
            self.log("Modem busy, waiting until ready...")
            return

        if not self.ctx.rf_modem:
            self.log("Modem not running...", isWarning=True)
            return

        first_queued_message = DatabaseManagerMessages(self.ctx).get_first_queued_message()
        if not first_queued_message:
            self.log("No queued message in database.")
            return
        try:
            self.log(f"Queued message found: {first_queued_message['id']}")
            # DatabaseManagerMessages(self.ctx.event_manager).update_message(first_queued_message["id"], update_data={'status': 'transmitting'}, frequency=self.ctx.state_manager.radio_frequency)
            message_dict = DatabaseManagerMessages(self.ctx).get_message_by_id(
                first_queued_message["id"]
            )
            message = MessageP2P.from_api_params(message_dict["origin"], message_dict)

            # wait some random time and wait if we have an ongoing codec2 transmission
            # on our channel. This should prevent some packet collision
            random_delay = np.random.randint(0, 10)
            threading.Event().wait(random_delay)
            while self.ctx.state_manager.is_receiving_codec2_signal():
                threading.Event().wait(0.1)

            # we are going to wait and check if we received any other codec2 signal within 10s.
            # if so, we are returning, message stays queued.
            # this helps to avoid packet collisions.
            time_to_wait = 10
            time_waiting_for_free_channel = time.time() + time_to_wait
            self.log(f"Checking channel if free for {time_to_wait}s", isWarning=False)
            while time.time() < time_waiting_for_free_channel:
                threading.Event().wait(0.1)
                if self.ctx.state_manager.is_receiving_codec2_signal():
                    self.log(
                        f"Codec2 signal found, skipping  message until next cycle", isWarning=True
                    )
                    return

            # If we came until here, we are setting status to transmitting, otherwise it stays in queued
            DatabaseManagerMessages(self.ctx).update_message(
                first_queued_message["id"],
                update_data={"status": "transmitting"},
                frequency=self.ctx.state_manager.radio_frequency,
            )

            # Convert JSON string to bytes (using UTF-8 encoding)
            payload = message.to_payload().encode("utf-8")
            json_bytearray = bytearray(payload)
            data, data_type = self.arq_data_type_handler.prepare(
                json_bytearray, ARQ_SESSION_TYPES.p2pmsg_zlib
            )
            iss = ARQSessionISS(self.ctx, self.message.destination, data, data_type)
            self.ctx.state_manager.register_arq_iss_session(iss)
            iss.start()
        except Exception as e:
            self.log(f"Error starting ARQ session: {e}", isWarning=True)
