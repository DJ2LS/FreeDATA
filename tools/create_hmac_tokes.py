import argparse
import numpy as np
import time


def create_hmac_salts(dxcallsign: str, mycallsign: str, num_tokens: int = 10000):
    """
    Creates a file with tokens for hmac signing

    Args:
        dxcallsign:
        mycallsign:
        int:

    Returns:
        bool
    """
    try:
        # Create and write random strings to a file
        with open(f"freedata_hmac_tokens_{dxcallsign}_{mycallsign}.txt", "w") as file:
            for _ in range(num_tokens):
                random_str = np.random.bytes(4).hex()
                file.write(random_str + '\n')
    except Exception:
        print("error creating hmac file")



parser = argparse.ArgumentParser(description='FreeDATA token generator')

parser.add_argument('--dxcallsign', dest="dxcallsign", default='AA0AA', help="Select the destination callsign", type=str)
parser.add_argument('--mycallsign', dest="mycallsign", default='AA0AA', help="Select the own callsign", type=str)
parser.add_argument('--tokens', dest="tokens", default='10000', help="Amount of tokens to create", type=int)

args = parser.parse_args()

create_hmac_salts(args.dxcallsign, args.mycallsign, int(args.tokens))