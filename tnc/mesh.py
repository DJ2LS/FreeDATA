# -*- coding: UTF-8 -*-
"""

@author: DJ2LS

HF mesh networking prototype and testing module

        import time
        MeshParam.routing_table = [['AA1AA', 'direct', 0, 1.0, 25, time.time(), ], ['AA1AA', 'AA2BB', 1, 3.1, 10, time.time(), ],
                  ['AA3CC', 'AA2BB', 5, -4.5, -3, time.time(), ]]

        print(MeshParam.routing_table)
        print("---------------------------------")




TODO: SIGNALLING FOR ACK/NACK:
- mesh-signalling burst is datac13
- mesh-signalling frame contains [message id, status, hops, score, payload]
- frame type is 1 byte
- message id is 32bit crc --> 4bytes
- status can be ACK, NACK, PING, PINGACK --> 1byte
- payload = 14bytes - 8 bytes  = 6bytes
- create a list for signalling frames, contains [message id, message-status, attempts, state, timestamp]
- on "IRS", send ACK/NACK 10 times on receiving beacon?
- on "ROUTER", receive ACK/NACK, and store it in table, also send it 10 times
- if sent 10 times, set ACK/NACK state to "done"
- if done already in list, don't reset retry counter
- delete ACK/NACK if "done" and timestamp older than 1day

TODO: SCORE CALCULATION:
SNR: negative --> * 2

"""
# pylint: disable=invalid-name, line-too-long, c-extension-no-member
# pylint: disable=import-outside-toplevel, attribute-defined-outside-init

from static import TNC, MeshParam, FRAME_TYPE, Station, ModemParam, ARQ
from codec2 import FREEDV_MODE
import numpy as np
import time
import threading
import modem
import helpers
import structlog

from queues import MESH_RECEIVED_QUEUE

class MeshRouter():
    def __init__(self):

        self.log = structlog.get_logger("RF")


        self.mesh_broadcasting_thread = threading.Thread(
            target=self.broadcast_routing_table, name="worker thread receive", daemon=True
        )
        self.mesh_broadcasting_thread.start()

        self.mesh_rx_dispatcher_thread = threading.Thread(
            target=self.mesh_rx_dispatcher, name="worker thread receive", daemon=True
        )
        self.mesh_rx_dispatcher_thread.start()


    def get_from_heard_stations(self):
        """
        get data from heard stations
        heard stations format:
        [dxcallsign,dxgrid,int(time.time()),datatype,snr,offset,frequency]

        TNC.heard_stations.append(
                    [
                        dxcallsign,
                        dxgrid,
                        int(time.time()),
                        datatype,
                        snr,
                        offset,
                        frequency,
                    ]
                )
        """
        dxcallsign_position = 0
        dxgrid_position = 1
        timestamp_position = 2
        type_position = 3
        snr_position = 4
        offset_position = 5
        frequency_position = 6

        try:
            for item in TNC.heard_stations:
                print("-----------")
                print(item)
                print(item[snr_position])
                try:
                    print(item[snr_position])
                    snr = bytes(item[snr_position], "utf-8").split(b"/")
                    snr = int(float(snr[0]))
                except Exception as err:
                    snr = int(float(item[snr_position]))

                new_router = [helpers.get_crc_24(item[dxcallsign_position]), helpers.get_crc_24(b'direct'), 0, snr, self.calculate_score_by_snr(snr), item[timestamp_position]]
                self.add_router_to_routing_table(new_router)
        except Exception as e:
            self.log.warning("[MESH] error fetching data from heard station list", e=e)

    def add_router_to_routing_table(self, new_router):
        try:
            # destination callsign # router callsign # hops # rx snr # route quality # timestamp
            for _, item in enumerate(MeshParam.routing_table):
                # update routing entry if exists
                if new_router[0] in item[0] and new_router[1] in item[1]:
                    print(f"UPDATE {MeshParam.routing_table[_]} >>> {new_router}")
                    MeshParam.routing_table[_] = new_router

            # add new routing entry if not exists
            if new_router not in MeshParam.routing_table:
                print(f"INSERT {new_router} >>> ROUTING TABLE")
                MeshParam.routing_table.append(new_router)
        except Exception as e:
            self.log.warning("[MESH] error adding data to routing table", e=e, router=new_router)

    def broadcast_routing_table(self, interval=180):

        while True:
            # always enable receiving for datac4 if broadcasting
            modem.RECEIVE_DATAC4 = True


            threading.Event().wait(1)
            if MeshParam.enable_protocol and not ARQ.arq_state and not ModemParam.channel_busy:
                try:

                    # wait some time until sending routing table
                    threading.Event().wait(interval)

                    # before we are transmitting, let us update our routing table
                    self.get_from_heard_stations()

                    #[b'DJ2LS-0', 'direct', 0, 9.6, 9.6, 1684912305]
                    mesh_broadcast_frame_header = bytearray(4)
                    mesh_broadcast_frame_header[:1] = bytes([FRAME_TYPE.MESH_BROADCAST.value])
                    mesh_broadcast_frame_header[1:4] = helpers.get_crc_24(Station.mycallsign)

                    # callsign(6), router(6), hops(1), path_score(1) == 14 ==> 14 28 42 ==> 3 mesh routing entries
                    # callsign_crc(3), router_crc(3), hops(1), path_score(1) == 8 --> 6
                    # callsign_crc(3), hops(1), path_score(1) == 5 --> 10

                    # Create a new bytearray with a fixed length of 50
                    result = bytearray(50)

                    # Iterate over the route subarrays and add the selected entries to the result bytearray
                    index = 0
                    for route_id, route in enumerate(MeshParam.routing_table):
                        # the value 5 is the length of crc24 + hops + score

                        dxcall = MeshParam.routing_table[route_id][0]
                        # router = MeshParam.routing_table[i][1]
                        hops = MeshParam.routing_table[route_id][2]
                        # snr = MeshParam.routing_table[i][3]
                        route_score = np.clip(MeshParam.routing_table[route_id][4], 0, 254)
                        # timestamp = MeshParam.routing_table[i][5]
                        result[index:index + 5] = dxcall + bytes([hops]) + bytes([route_score])
                        index += 5

                    # Split the result bytearray into a list of fixed-length bytearrays
                    split_result = [result[i:i + 50] for i in range(0, len(result), 50)]
                    frame_list = []
                    for _ in split_result:
                        # make sure payload is always 50
                        _[len(_):] = bytes(50 - len(_))
                        #print(len(_))
                        frame_list.append(mesh_broadcast_frame_header + _)

                    TNC.transmitting = True
                    c2_mode = FREEDV_MODE.datac4.value
                    self.log.info("[MESH] broadcasting routing table", frame_list=frame_list, frames=len(split_result))
                    modem.MODEM_TRANSMIT_QUEUE.put([c2_mode, 1, 0, frame_list])

                    # Wait while transmitting
                    while TNC.transmitting:
                        threading.Event().wait(0.01)
                except Exception as e:
                    self.log.warning("[MESH] broadcasting routing table", e=e)


    def mesh_rx_dispatcher(self):
        while True:
            data_in = MESH_RECEIVED_QUEUE.get()
            if int.from_bytes(data_in[:1], "big") in [FRAME_TYPE.MESH_BROADCAST.value]:
                self.received_routing_table(data_in[:-2])
            else:
                print("wrong mesh data received")
                print(data_in)
    def received_routing_table(self, data_in):
        try:
            print("data received........")
            print(data_in)

            router = data_in[1:4]  # Extract the first 4 bytes (header)
            payload = data_in[4:]  # Extract the payload (excluding the header)

            print("Router:", router)  # Output the header bytes

            for i in range(0, len(payload)-1, 5):
                callsign_checksum = payload[i:i + 3]  # First 3 bytes of the information (callsign_checksum)
                hops = int.from_bytes(payload[i+3:i + 4], "big")  # Fourth byte of the information (hops)
                score = int.from_bytes(payload[i+4:i + 5], "big")  # Fifth byte of the information (score)
                snr = int(ModemParam.snr)
                score = self.calculate_new_avg_score(score, self.calculate_score_by_snr(snr))
                timestamp = int(time.time())

                # use case 1: add new router to table only if callsign not empty
                _use_case1 = callsign_checksum.startswith(b'\x00')

                # use case 2: add new router to table only if not own callsign
                _use_case2 = callsign_checksum not in [helpers.get_crc_24(Station.mycallsign)]

                # use case 3: increment hop if router not direct
                if router not in [helpers.get_crc_24(b'direct')] and hops == 0:
                    hops += 1

                # use case 4: if callsign is directly available skip route for only keeping shortest way in db
                _use_case4 = False
                for _, call in enumerate(MeshParam.routing_table):
                    # check if callsign already in routing table and is direct connection
                    if callsign_checksum in [MeshParam.routing_table[_][0]] and MeshParam.routing_table[_][1] in [helpers.get_crc_24(b'direct')]:
                        _use_case4 = True

                # use case N: calculate score
                # TODO...

                if not _use_case1 \
                        and _use_case2\
                        and not _use_case4:

                    print("Callsign Checksum:", callsign_checksum)
                    print("Hops:", hops)
                    print("Score:", score)

                    new_router = [callsign_checksum, router, hops, snr, score, timestamp]
                    print(new_router)
                    self.add_router_to_routing_table(new_router)

            print("-------------------------")
            for _, item in enumerate(MeshParam.routing_table):
                print(MeshParam.routing_table[_])
            print("-------------------------")
        except Exception as e:
            self.log.warning("[MESH] error processing received routing broadcast", e=e)

    def calculate_score_by_snr(self, snr):
        if snr < -12 or snr > 12:
            raise ValueError("Value must be in the range of -12 to 12")

        score = (snr + 12) * 100 / 24  # Scale the value to the range [0, 100]
        if score < 0:
            score = 0  # Ensure the score is not less than 0
        elif score > 100:
            score = 100  # Ensure the score is not greater than 100

        return int(score)

    def calculate_new_avg_score(self, value_old, value):
        return int((value_old + value) / 2)