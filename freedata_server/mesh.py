# -*- coding: UTF-8 -*-
"""

@author: DJ2LS

HF mesh networking prototype and testing module

        import time
        self.states.mesh_routing_table = [['AA1AA', 'direct', 0, 1.0, 25, time.time(), ], ['AA1AA', 'AA2BB', 1, 3.1, 10, time.time(), ],
                  ['AA3CC', 'AA2BB', 5, -4.5, -3, time.time(), ]]

        print(self.states.mesh_routing_table)
        print("---------------------------------")




TODO SIGNALLING FOR ACK/NACK:
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

TODO SCORE CALCULATION:
SNR: negative --> * 2

"""
# pylint: disable=invalid-name, line-too-long, c-extension-no-member
# pylint: disable=import-outside-toplevel, attribute-defined-outside-init

from modem_frametypes import FRAME_TYPE

#from global_instances import ARQ,ModemParam, MeshParam, Station, Modem

from codec2 import FREEDV_MODE
import numpy as np
import time
import threading
import modem
import helpers
import structlog

from queues import MESH_RECEIVED_QUEUE, MESH_QUEUE_TRANSMIT, MESH_SIGNALLING_TABLE

class MeshRouter():
    def __init__(self, config, event_queue, states):

        self.log = structlog.get_logger("RF")

        self.mycallsign = config['STATION']['mycall']
        self.mycallsign_crc = helpers.get_crc_24(self.mycallsign)

        self.transmission_time_list = [
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360,
            60, 90, 120, 180, 180, 180, 180, 180, 180, 360, 360, 360, 360, 360, 360
        ]
        # for testing only: self.transmission_time_list = [30, 30]
        self.signalling_max_attempts = len(self.transmission_time_list)



        self.mesh_broadcasting_thread = threading.Thread(
            target=self.broadcast_routing_table, name="worker thread receive", daemon=True
        )
        self.mesh_broadcasting_thread.start()

        self.mesh_rx_dispatcher_thread = threading.Thread(
            target=self.mesh_rx_dispatcher, name="worker thread receive", daemon=True
        )
        self.mesh_rx_dispatcher_thread.start()

        self.mesh_tx_dispatcher_thread = threading.Thread(
            target=self.mesh_tx_dispatcher, name="worker thread receive", daemon=True
        )
        self.mesh_tx_dispatcher_thread.start()

        self.mesh_signalling_dispatcher_thread = threading.Thread(
            target=self.mesh_signalling_dispatcher, name="worker thread receive", daemon=True
        )
        self.mesh_signalling_dispatcher_thread.start()

    def get_from_heard_stations(self):
        """
        get data from heard stations
        heard stations format:
        [dxcallsign,dxgrid,int(time.time()),datatype,snr,offset,frequency]

        self.states.heard_stations.append(
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
            for item in self.states.heard_stations:
                #print("-----------")
                #print(item)
                #print(item[snr_position])
                try:
                    #print(item[snr_position])
                    snr = bytes(item[snr_position], "utf-8").split(b"/")
                    snr = int(float(snr[0]))
                except Exception as err:
                    self.log.debug("[MESH] error handling SNR calculation", e=err)
                    snr = int(float(item[snr_position]))

                snr = np.clip(snr, -12, 12)  # limit to max value of -12/12
                new_router = [helpers.get_crc_24(item[dxcallsign_position]), helpers.get_crc_24(b'direct'), 0, snr, self.calculate_score_by_snr(snr), item[timestamp_position]]
                self.add_router_to_routing_table(new_router)

        except Exception as e:
            self.log.warning("[MESH] error fetching data from heard station list", e=e)

    def add_router_to_routing_table(self, new_router):
        try:
            # destination callsign # router callsign # hops # rx snr # route quality # timestamp
            for _, item in enumerate(self.states.mesh_routing_table):
                # update routing entry if exists
                if new_router[0] in item[0] and new_router[1] in item[1]:
                    #print(f"UPDATE {self.states.mesh_routing_table[_]} >>> {new_router}")
                    self.log.info(f"[MESH] [ROUTING TABLE] [UPDATE]: {self.states.mesh_routing_table[_]} >>> ",
                                  update=new_router)

                    self.states.mesh_routing_table[_] = new_router

            # add new routing entry if not exists
            if new_router not in self.states.mesh_routing_table:
                #print(f"INSERT {new_router} >>> ROUTING TABLE")
                self.log.info("[MESH] [ROUTING TABLE] [INSERT]:", insert=new_router)

                self.states.mesh_routing_table.append(new_router)
        except Exception as e:
            self.log.warning("[MESH] error adding data to routing table", e=e, router=new_router)

    def broadcast_routing_table(self, interval=600):

        while True:
            # always enable receiving for datac4 if broadcasting
            modem.RECEIVE_DATAC4 = True

            threading.Event().wait(1)
            if not self.states.arq_state and not self.states.channel_busy:
                try:

                    # wait some time until sending routing table
                    threading.Event().wait(interval)

                    # before we are transmitting, let us update our routing table
                    self.get_from_heard_stations()

                    #[b'DJ2LS-0', 'direct', 0, 9.6, 9.6, 1684912305]
                    mesh_broadcast_frame_header = bytearray(4)
                    mesh_broadcast_frame_header[:1] = bytes([FRAME_TYPE.MESH_BROADCAST.value])
                    mesh_broadcast_frame_header[1:4] = helpers.get_crc_24(self.mycallsign)

                    # callsign(6), router(6), hops(1), path_score(1) == 14 ==> 14 28 42 ==> 3 mesh routing entries
                    # callsign_crc(3), router_crc(3), hops(1), path_score(1) == 8 --> 6
                    # callsign_crc(3), hops(1), path_score(1) == 5 --> 10

                    # Create a new bytearray with a fixed length of 50
                    result = bytearray(50)

                    # Iterate over the route subarrays and add the selected entries to the result bytearray
                    index = 0
                    for route_id, route in enumerate(self.states.mesh_routing_table):
                        # the value 5 is the length of crc24 + hops + score

                        dxcall = self.states.mesh_routing_table[route_id][0]
                        # router = self.states.mesh_routing_table[i][1]
                        hops = self.states.mesh_routing_table[route_id][2]
                        # snr = self.states.mesh_routing_table[i][3]
                        route_score = np.clip(self.states.mesh_routing_table[route_id][4], 0, 254)
                        # timestamp = self.states.mesh_routing_table[i][5]
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

                    c2_mode = FREEDV_MODE.datac4.value
                    self.log.info("[MESH] broadcasting routing table", frame_list=frame_list, frames=len(split_result))
                    modem.MODEM_TRANSMIT_QUEUE.put([c2_mode, 1, 0, frame_list])

                except Exception as e:
                    self.log.warning("[MESH] broadcasting routing table", e=e)


    def mesh_rx_dispatcher(self):
        while True:
            data = MESH_RECEIVED_QUEUE.get()
            data_in = data[0]
            snr = data[1]

            if int.from_bytes(data_in[:1], "big") in [FRAME_TYPE.MESH_BROADCAST.value]:
                self.received_routing_table(data_in[:-2], snr)
            elif int.from_bytes(data_in[:1], "big") in [FRAME_TYPE.MESH_SIGNALLING_PING.value]:
                self.received_mesh_ping(data_in[:-2])
            elif int.from_bytes(data_in[:1], "big") in [FRAME_TYPE.MESH_SIGNALLING_PING_ACK.value]:
                self.received_mesh_ping_ack(data_in[:-2])

            else:
                print("wrong mesh data received")
                #print(data_in)

    def mesh_tx_dispatcher(self):
        while True:
            data = MESH_QUEUE_TRANSMIT.get()
            #print(data)
            if data[0] == "PING":
                destination = helpers.get_crc_24(data[2]).hex()
                origin = helpers.get_crc_24(data[1]).hex()
                self.add_mesh_ping_to_signalling_table(destination, origin, frametype="PING", status="awaiting_ack")
            else:
                print("wrong mesh command")



    def mesh_signalling_dispatcher(self):
        #           [timestamp, destination, origin, frametype, payload, attempt, status]
        # --------------0------------1---------2---------3--------4---------5--------6 #


        while True:
            threading.Event().wait(1.0)
            for entry in MESH_SIGNALLING_TABLE:
                # if in arq state, interrupt dispatcher
                if self.states.arq_state or self.states.arq_session:
                    break

                #print(entry)
                attempt = entry[5]
                status = entry[6]
                # check for PING cases
                if entry[3] in ["PING"] and attempt < len(self.transmission_time_list) and status not in ["acknowledged"]:
                    # Calculate the transmission time with exponential increase
                    #transmission_time = timestamp + (2 ** attempt) * 10
                    # Calculate transmission times for attempts 0 to 30 with stronger S-curves in minutes
                    #correction_factor = 750
                    timestamp = entry[0]
                    #transmission_time = timestamp + (4.5 / (1 + np.exp(-1. * (attempt - 5)))) * correction_factor * attempt
                    transmission_time = timestamp + sum(self.transmission_time_list[:attempt])
                    # check if it is time to transmit
                    if time.time() >= transmission_time:
                        entry[5] += 1
                        self.log.info("[MESH] [TX] Ping", destination=entry[1], origin=entry[2])
                        channel_busy_timeout = time.time() + 5
                        while self.states.channel_busy and time.time() < channel_busy_timeout:
                            threading.Event().wait(0.01)
                        self.transmit_mesh_signalling_ping(bytes.fromhex(entry[1]), bytes.fromhex(entry[2]))
                    #print("...")
                elif entry[3] in ["PING-ACK"] and attempt < len(self.transmission_time_list) and status not in ["acknowledged"]:
                    timestamp = entry[0]
                    #transmission_time = timestamp + (4.5 / (1 + np.exp(-1. * (attempt - 5)))) * correction_factor * attempt
                    transmission_time = timestamp + sum(self.transmission_time_list[:attempt])
                    # check if it is time to transmit
                    if time.time() >= transmission_time:
                        entry[5] += 1
                        self.log.info("[MESH] [TX] Ping ACK", destination=entry[1], origin=entry[2])
                        channel_busy_timeout = time.time() + 5
                        while self.states.channel_busy and time.time() < channel_busy_timeout:
                            threading.Event().wait(0.01)
                        self.transmit_mesh_signalling_ping_ack(bytes.fromhex(entry[1]), bytes.fromhex(entry[2]))
                else:
                    pass


    def received_routing_table(self, data_in, snr):
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
                snr = int(snr)
                score = self.calculate_new_avg_score(score, self.calculate_score_by_snr(snr))
                timestamp = int(time.time())

                # use case 1: add new router to table only if callsign not empty
                _use_case1 = callsign_checksum.startswith(b'\x00')

                # use case 2: add new router to table only if not own callsign
                _use_case2 = callsign_checksum not in [helpers.get_crc_24(self.mycallsign)]

                # use case 3: increment hop if router not direct
                if router not in [helpers.get_crc_24(b'direct')] and hops == 0:
                    hops += 1

                # use case 4: if callsign is directly available skip route for only keeping shortest way in db
                _use_case4 = False
                for _, call in enumerate(self.states.mesh_routing_table):
                    # check if callsign already in routing table and is direct connection
                    if callsign_checksum in [self.states.mesh_routing_table[_][0]] and self.states.mesh_routing_table[_][1] in [helpers.get_crc_24(b'direct')]:
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
            for _, item in enumerate(self.states.mesh_routing_table):
                print(self.states.mesh_routing_table[_])
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

    def received_mesh_ping(self, data_in):
        destination = data_in[1:4].hex()
        origin = data_in[4:7].hex()
        if destination == self.mycallsign_crc.hex():
            self.log.info("[MESH] [RX] [PING] [REQ]", destination=destination, origin=origin, mycall=self.mycallsign_crc.hex())
            # use case 1: set status to acknowleding if we are the receiver of a PING
            self.add_mesh_ping_to_signalling_table(destination, origin, frametype="PING-ACK", status="acknowledging")

            channel_busy_timeout = time.time() + 5
            while self.states.channel_busy and time.time() < channel_busy_timeout:
                threading.Event().wait(0.01)

            # dxcallsign_crc = self.mycallsign_crc
            self.transmit_mesh_signalling_ping_ack(bytes.fromhex(destination), bytes.fromhex(origin))
        elif origin == self.mycallsign_crc.hex():
            pass
        else:
            self.log.info("[MESH] [RX] [PING] [REQ]", destination=destination, origin=origin, mycall=self.mycallsign_crc.hex())
            # lookup if entry is already in database - if so, udpate and exit
            for item in MESH_SIGNALLING_TABLE:
                if item[1] == destination and item[5] >= self.signalling_max_attempts:
                    # use case 2: set status to forwarded if we are not the receiver of a PING and out of retries
                    self.add_mesh_ping_to_signalling_table(destination, origin, frametype="PING", status="forwarded")
                    return

            print("......................")
            # use case 1: set status to forwarding if we are not the receiver of a PING and we don't have an entry in our database
            self.add_mesh_ping_to_signalling_table(destination, origin, frametype="PING", status="forwarding")

    def received_mesh_ping_ack(self, data_in):
        # TODO
        # Check if we have a ping callsign already in signalling table
        # if PING, then override and make it a PING-ACK
        # if not, then add to table

        destination = data_in[1:4].hex()
        origin = data_in[4:7].hex()
        timestamp = time.time()
        #router = ""
        frametype = "PING-ACK"
        payload = ""
        attempt = 0


        if destination == self.mycallsign_crc.hex():
            #self.log.info("[MESH] [RX] [PING] [ACK]", destination=destination, origin=origin, mycall=self.mycallsign_crc.hex())
            #self.add_mesh_ping_ack_to_signalling_table(destination, origin, status="sending_ack")
            pass
        elif origin == self.mycallsign_crc.hex():
            self.log.info("[MESH] [RX] [PING] [ACK]", destination=destination, origin=origin, mycall=self.mycallsign_crc.hex())
            self.add_mesh_ping_ack_to_signalling_table(destination, origin, status="acknowledged")
        else:
            #status = "forwarding"
            #self.add_mesh_ping_ack_to_signalling_table(destination, status)
            self.log.info("[MESH] [RX] [PING] [ACK]", destination=destination, mycall=self.mycallsign_crc.hex())
            for item in MESH_SIGNALLING_TABLE:
                if item[1] == destination and item[2] == origin and item[5] >= self.signalling_max_attempts:
                    # use case 2: set status to forwarded if we are not the receiver of a PING and out of retries
                    self.add_mesh_ping_ack_to_signalling_table(destination, status="forwarded")
                    return

            self.add_mesh_ping_ack_to_signalling_table(destination, origin, status="forwarding")
                #dxcallsign_crc = bytes.fromhex(destination)
                #self.transmit_mesh_signalling_ping_ack(dxcallsign_crc)

        print(MESH_SIGNALLING_TABLE)


    def add_mesh_ping_to_signalling_table(self, destination, origin, frametype, status):
        try:
            timestamp = time.time()
            #router = ""
            #frametype = "PING"
            payload = ""
            attempt = 0

            #           [timestamp, destination, origin, frametype, payload, attempt, status]
            # --------------0------------1---------2---------3--------4---------5--------6-----#
            new_entry = [timestamp, destination, origin, frametype, payload, attempt, status]
            for _, item in enumerate(MESH_SIGNALLING_TABLE):
                # update entry if exists
                if destination in item[1] and origin in item[2] and frametype in item[3]:
                    # reset attempts if entry exists and it failed or is acknowledged
                    attempt = 0 if item[6] in ["failed", "acknowledged"] else item[5]
                    update_entry = [item[0], destination, origin, frametype, "",attempt, status]
                    #print(f"UPDATE {MESH_SIGNALLING_TABLE[_]} >>> {update_entry}")

                    self.log.info(f"[MESH] [SIGNALLING TABLE] [UPDATE]: {MESH_SIGNALLING_TABLE[_]} >>> ", update=update_entry)

                    MESH_SIGNALLING_TABLE[_] = update_entry
                    return

            # add new routing entry if not exists
            if new_entry not in MESH_SIGNALLING_TABLE:
                #print(f"INSERT {new_entry} >>> SIGNALLING TABLE")
                self.log.info("[MESH] [SIGNALLING TABLE] [INSERT]:", insert=new_entry)

                MESH_SIGNALLING_TABLE.append(new_entry)

        except Exception as e:
            self.log.warning(f"[MESH] [SIGNALLING TABLE] [INSERT] [PING] [ERROR] ", e=e)
    def add_mesh_ping_ack_to_signalling_table(self, destination, origin, status):
        try:
            timestamp = time.time()
            #router = ""
            frametype = "PING-ACK"
            payload = ""
            attempt = 0
            new_entry = [timestamp, destination, origin, frametype, payload, attempt, status]

            for _, item in enumerate(MESH_SIGNALLING_TABLE):
                # update entry if exists
                if destination in item[1] and origin in item[2] and item[3] in ["PING", "PING-ACK"]:
                    # reset attempts if entry exists and it failed or is acknowledged
                    attempt = 0 if item[6] in ["failed", "acknowledged"] else item[5]
                    update_entry = [item[0], destination, origin, "PING-ACK", "", attempt, status]
                    #print(f"UPDATE {MESH_SIGNALLING_TABLE[_]} >>> {update_entry}")
                    self.log.info(f"[MESH] [SIGNALLING TABLE] [UPDATE]: {MESH_SIGNALLING_TABLE[_]} >>> ", update=update_entry)

                    MESH_SIGNALLING_TABLE[_] = update_entry
                    return

            # add new routing entry if not exists
            if new_entry not in MESH_SIGNALLING_TABLE:
                #print(f"INSERT {new_entry} >>> SIGNALLING TABLE")
                self.log.info(f"[MESH] [SIGNALLING TABLE] [INSERT] >>> ", update=new_entry)

                MESH_SIGNALLING_TABLE.append(new_entry)
        except Exception as e:
            self.log.warning(f"[MESH] [SIGNALLING TABLE] [INSERT] [PING ACK] [ERROR] ", e=e)


    def enqueue_frame_for_tx(
            self,
            frame_to_tx,  # : list[bytearray], # this causes a crash on python 3.7
            c2_mode=FREEDV_MODE.sig0.value,
            copies=1,
            repeat_delay=0,
    ) -> None:
        """
        Send (transmit) supplied frame to Modem

        :param frame_to_tx: Frame data to send
        :type frame_to_tx: list of bytearrays
        :param c2_mode: Codec2 mode to use, defaults to datac13
        :type c2_mode: int, optional
        :param copies: Number of frame copies to send, defaults to 1
        :type copies: int, optional
        :param repeat_delay: Delay time before sending repeat frame, defaults to 0
        :type repeat_delay: int, optional
        """
        #print(frame_to_tx[0])
        #print(frame_to_tx)
        frame_type = FRAME_TYPE(int.from_bytes(frame_to_tx[0][:1], byteorder="big")).name
        self.log.debug("[Modem] enqueue_frame_for_tx", c2_mode=FREEDV_MODE(c2_mode).name, data=frame_to_tx,
                       type=frame_type)

        modem.MODEM_TRANSMIT_QUEUE.put([c2_mode, copies, repeat_delay, frame_to_tx])


    def transmit_mesh_signalling_ping(self, destination, origin):

        frame_type = bytes([FRAME_TYPE.MESH_SIGNALLING_PING.value])

        ping_frame = bytearray(14)
        ping_frame[:1] = frame_type
        ping_frame[1:4] = destination
        ping_frame[4:7] = origin
        ping_frame[7:13] = helpers.callsign_to_bytes(self.mycallsign)

        self.enqueue_frame_for_tx([ping_frame], c2_mode=FREEDV_MODE.sig0.value)

    def transmit_mesh_signalling_ping_ack(self, destination, origin):
        #dxcallsign_crc = bytes.fromhex(data[1])

        frame_type = bytes([FRAME_TYPE.MESH_SIGNALLING_PING_ACK.value])

        ping_frame = bytearray(14)
        ping_frame[:1] = frame_type
        ping_frame[1:4] = destination
        ping_frame[4:7] = origin
        #ping_frame[7:13] = helpers.callsign_to_bytes(self.mycallsign)

        self.enqueue_frame_for_tx([ping_frame], c2_mode=FREEDV_MODE.sig0.value)