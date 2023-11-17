# global_instances.py

from deprecated_static import Daemon, ARQ, AudioParam, Beacon, Channel, HamlibParam, ModemParam, Station, Statistics, TCIParam, Modem, MeshParam

# Initialize instances with appropriate default values

# Create single instances of each dataclass
Daemon = Daemon(modemprocess=None, rigctldprocess=None)
ARQ = ARQ()
AudioParam = AudioParam()
Beacon = Beacon()
Channel = Channel()
HamlibParam = HamlibParam()
ModemParam = ModemParam()
Station = Station()
Statistics = Statistics()
TCIParam = TCIParam()
Modem = Modem()
MeshParam = MeshParam()
