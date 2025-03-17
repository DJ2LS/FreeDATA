from command import TxCommand

class BeaconCommand(TxCommand):
    """Command for transmitting beacon frames.

    This command builds and transmits beacon frames, indicating the station's
    status (away from key or not).
    """

    def build_frame(self):
        """Builds a beacon frame.

        This method retrieves the station's "away from key" status from the
        state manager and uses it to build a beacon frame.

        Returns:
            bytearray: The built beacon frame.
        """
        beacon_state = self.state_manager.is_away_from_key
        return self.frame_factory.build_beacon(beacon_state)


    #def transmit(self, freedata_server):
    #    super().transmit(freedata_server)
    #    if self.config['MODEM']['enable_morse_identifier']:
    #        mycall = f"{self.config['STATION']['mycall']}-{self.config['STATION']['myssid']}"
    #        freedata_server.transmit_morse("morse", 1, 0, mycall)
