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

from static import TNC, MeshParam
import time
import threading

class MeshRouter():

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
            new_router = [item[dxcallsign], 'direct', 0, item[snr], item[snr], item[timestamp]]
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
