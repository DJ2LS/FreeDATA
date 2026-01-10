import base64

from freedata_server.modem_frametypes import FRAME_TYPE as FR
from freedata_server import frame_handler
from freedata_server.message_system_db_broadcasts import DatabaseManagerBroadcasts
from freedata_server.norm.norm_transmission_irs import NormTransmissionIRS
from freedata_server.norm.norm_transmission_iss import NormTransmissionISS


class NORMFrameHandler(frame_handler.FrameHandler):
    def follow_protocol(self):
        # self.logger.debug(f"[NORM] handling burst:{self.details}")

        # origin = self.details["frame"]["origin"]
        # print(origin)
        frame = self.details["frame"]

        if frame["frame_type_int"] == FR.NORM_DATA.value:
            NormTransmissionIRS(self.ctx, frame)

        elif frame["frame_type_int"] == FR.NORM_REPAIR.value:
            NormTransmissionIRS(self.ctx, frame)

        elif frame["frame_type_int"] == FR.NORM_NACK.value:
            try:
                print(str(frame["id"]))
                print(frame["id"].decode("utf-8"))
                broadcast = DatabaseManagerBroadcasts(self.ctx).get_broadcast_per_id(frame["id"].decode("utf-8"))
                if broadcast is not None:
                    if broadcast["attempts"] >= 30:
                        print("maximum attempts reached...")
                        return
                    DatabaseManagerBroadcasts(self.ctx).increment_attempts(broadcast["id"])
                    _data = base64.b64decode(broadcast["payload_data"]["final"])
                    print(broadcast)
                    print("oring", broadcast["origin"])
                    print("domain", broadcast["domain"])
                    # print("gridsquare", broadcast["gridsquare"])
                    # print("payload_data", broadcast["payload_data"]["final"])
                    # print("priority", broadcast["priority"])
                    # print("message_type", broadcast["msg_type"])
                    # print("frame:", frame)
                    # print("missing bursts:", frame["burst_numbers"])
                    # NormTransmissionISS(self.ctx, broadcast["origin"], broadcast["domain"], broadcast["gridsquare"], data, priority=broadcast["priority"], message_type=broadcast["msg_type"], send_only_bursts=frame["burst_numbers"]).prepare_and_transmit()
                    repair_bursts = NormTransmissionISS(self.ctx).create_repair(broadcast, frame["burst_numbers"])
                    NormTransmissionISS(self.ctx).transmit_bursts(repair_bursts)
            except Exception as e:
                print(e)
        else:
            self.logger.warning("DISCARDING FRAME", frame=frame)
            return
