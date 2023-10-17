# global_instances.py

from static import Daemon, ARQ, AudioParam, Beacon, Channel, HamlibParam, ModemParam, Station, Statistics, TCIParam, TNC, MeshParam

# Initialize instances with appropriate default values

# Create single instances of each dataclass
Daemon = Daemon(tncprocess=None, rigctldprocess=None)
ARQ = ARQ()
AudioParam = AudioParam()
Beacon = Beacon()
Channel = Channel()
HamlibParam = HamlibParam()
ModemParam = ModemParam()
Station = Station()
Statistics = Statistics()
TCIParam = TCIParam()
TNC = TNC()
MeshParam = MeshParam()
