from command import TxCommand
import api_validations
from protocol_arq_iss import ISS
from protocol_arq import ARQ

class ARQRawCommand(TxCommand):

    def __int__(self, state_manager):
        # open a new arq instance here
        self.initialize_arq_instance()

    def set_params_from_api(self, apiParams):
        self.dxcall = apiParams['dxcall']
        if not api_validations.validate_freedata_callsign(self.dxcall):
            self.dxcall = f"{self.dxcall}-0"
        return super().set_params_from_api(apiParams)

    def initialize_arq_transmission_iss(self, data):
        if id := self.get_id_from_frame(data):
            instance = self.initialize_arq_instance()
            self.states.register_arq_instance_by_id(id, instance)
            instance['arq_irs'].arq_received_data_channel_opener()


    def initialize_arq_instance(self):
        self.arq = ARQ(self.config, self.event_queue, self.state_manager)
        self.arq_iss = ISS(self.config, self.event_queue, self.state_manager)

        return {
            'arq': self.arq,
            'arq_irs': self.arq_irs,
            'arq_iss': self.arq_iss,
            'arq_session': self.arq_session
        }
    def build_frame(self):
        return self.frame_factory.build_arq_connect(destination=self.dxcall, session_id=b'', isWideband=True)
