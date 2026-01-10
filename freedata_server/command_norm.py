from freedata_server.command import TxCommand
from freedata_server import api_validations
import base64
import threading
from freedata_server.norm.norm_transmission_iss import NormTransmissionISS


class Norm(TxCommand):
    def set_params_from_api(self, apiParams):
        self.origin = apiParams["origin"]
        if not api_validations.validate_freedata_callsign(self.origin):
            self.origin = f"{self.origin}-0"

        self.domain = apiParams["domain"]
        if not api_validations.validate_freedata_callsign(self.domain):
            self.domain = f"{self.domain}-0"

        # strip data to maximum payload
        self.data = base64.b64decode(apiParams["data"])
        self.data = self.data[: 15 * 26]

        if "priority" not in apiParams:
            self.priority = 1
        else:
            self.priority = apiParams["priority"]

        self.msgtype = apiParams["type"]
        self.gridsquare = apiParams["gridsquare"]

    def run(self):
        try:
            if not self.ctx.config_manager.config["EXP"]["enable_groupchat"]:
                return False

            self.emit_event()
            self.logger.info(self.log_message())

            # NormTransmissionISS(self.ctx).prepare_and_transmit_data(self.origin, self.domain, self.gridsquare, self.data, self.priority, self.msgtype)

            tx_thread = threading.Thread(
                target=NormTransmissionISS(self.ctx).prepare_and_transmit_data,
                args=(self.origin, self.domain, self.gridsquare, self.data, self.priority, self.msgtype),
            )
            tx_thread.start()

        except Exception as e:
            self.log(f"Error starting NORM transmission: {e}", isWarning=True)

        return False
