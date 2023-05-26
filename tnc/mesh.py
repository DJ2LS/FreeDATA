# -*- coding: UTF-8 -*-
"""

@author: DJ2LS

HF mesh networking prototype and testing module

        import time
        MeshParam.routing_table = [['AA1AA', 'direct', 0, 1.0, 25, time.time(), ], ['AA1AA', 'AA2BB', 1, 3.1, 10, time.time(), ],
                  ['AA3CC', 'AA2BB', 5, -4.5, -3, time.time(), ]]

        print(MeshParam.routing_table)
        print("---------------------------------")

"""
# pylint: disable=invalid-name, line-too-long, c-extension-no-member
# pylint: disable=import-outside-toplevel, attribute-defined-outside-init

from static import TNC, MeshParam, FRAME_TYPE, Station, ModemParam
from codec2 import FREEDV_MODE
import numpy as np
import time
import threading
import modem
import helpers
from queues import MESH_RECEIVED_QUEUE

class MeshRouter():
    def __init__(self):
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
        dxcallsign = 0
        dxgrid = 1
        timestamp = 2
        type = 3
        snr = 4
        offset = 5
        frequency = 6

        for item in TNC.heard_stations:
            new_router = [helpers.get_crc_24(item[dxcallsign]), helpers.get_crc_24(b'direct'), 0, int(item[snr]), int(item[snr]), item[timestamp]]

            self.add_router_to_routing_table(new_router)

    def add_router_to_routing_table(self, new_router):
        # destination callsign # router callsign # hops # rx snr # route quality # timestamp
        for _, item in enumerate(MeshParam.routing_table):
            # update routing entry if exists
            if new_router[0] in item[0] and new_router[1] in item[1]:
                print(f"UPDATE {MeshParam.routing_table[_]} >>> {new_router}")
                MeshParam.routing_table[_] = new_router

        # add new routing entry if not exists
        if new_router not in MeshParam.routing_table:
            MeshParam.routing_table.append(new_router)

    def broadcast_routing_table(self, interval=60):
        # enable receiving for datac4 if broadcasting
        modem.RECEIVE_DATAC4 = True

        while True:
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
            for route in MeshParam.routing_table:
                dxcall = MeshParam.routing_table[route][0]
                # router = MeshParam.routing_table[i][1]
                hops = MeshParam.routing_table[route][2]
                # snr = MeshParam.routing_table[i][3]
                route_score = np.clip(MeshParam.routing_table[route][4], 0, 254)
                # timestamp = MeshParam.routing_table[i][5]
                result[index:index + 3] = dxcall + hops + route_score
                index += len(route[0])
                index += len(route[2])
                index += len(route[4])

            # Split the result bytearray into a list of fixed-length bytearrays
            split_result = [result[i:i + 50] for i in range(0, len(result), 50)]

            frame_list = []
            for _ in split_result:
                # make sure payload is always 50
                _[len(_):] = bytes(50 - len(_))
                #print(_)
                #print(len(_))
                frame_list.apppend(mesh_broadcast_frame_header + _)

            print(frame_list)
            TNC.transmitting = True
            c2_mode = FREEDV_MODE.datac4.value
            modem.MODEM_TRANSMIT_QUEUE.put([c2_mode, 1, 0, [frame_list]])

            # Wait while transmitting
            while TNC.transmitting:
                threading.Event().wait(0.01)

    def mesh_rx_dispatcher(self):
        while True:
            data_in = MESH_RECEIVED_QUEUE.get()
            if int.from_bytes(data_in[:1], "big") in [FRAME_TYPE.MESH_BROADCAST.value]:
                self.received_routing_table(data_in)
            else:
                print("wrong mesh data received")
                print(data_in)
    def received_routing_table(self, data_in):
        print("data received........")
        print(data_in)

        router = data_in[1:4]  # Extract the first 4 bytes (header)
        payload = data_in[4:]  # Extract the payload (excluding the header)

        print("Router:", router)  # Output the header bytes

        for i in range(0, len(payload), 5):
            callsign_checksum = payload[i:i + 3]  # First 3 bytes of the information (callsign_checksum)
            hops = payload[i + 3]  # Fourth byte of the information (hops)
            score = payload[i + 4]  # Fifth byte of the information (score)
            timestamp = int(time.time())
            snr = int(ModemParam.snr)
            print("Callsign Checksum:", callsign_checksum)
            print("Hops:", hops)
            print("Score:", score)

            # use case 1: add new router to table only if callsign not empty
            _use_case1 = callsign_checksum.startswith(b'\x00')

            # use case 2: add new router to table only if not own callsign
            _use_case2 = callsign_checksum not in [helpers.get_crc_24(Station.mycallsign)]

            # use case 3: increment hop if not direct
            if router not in [helpers.get_crc_24(b'direct')] and hops == 0:
                hops += 1

            # use case 4: calculate score
            # TODO...

            if not _use_case1 \
                    and _use_case2:

                new_router = [callsign_checksum, router, hops, snr, score, timestamp]
                print(new_router)
                self.add_router_to_routing_table(new_router)

        print("-------------------------")
        for _ in MeshParam.routing_table:
            print(MeshParam.routing_table[_])
        print("-------------------------")