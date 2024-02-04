# models.py

from sqlalchemy import Index, Boolean, Column, String, Integer, JSON, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Beacon(Base):
    __tablename__ = 'beacon'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    snr = Column(Integer)
    callsign = Column(String, ForeignKey('station.callsign'))
    station = relationship("Station", back_populates="beacons")

    Index('idx_beacon_callsign', 'callsign')

class Station(Base):
    __tablename__ = 'station'
    callsign = Column(String, primary_key=True)
    checksum = Column(String, nullable=True)
    location = Column(JSON, nullable=True)
    info = Column(JSON, nullable=True)
    beacons = relationship("Beacon", order_by="Beacon.id", back_populates="station")

    Index('idx_station_callsign_checksum', 'callsign', 'checksum')

    def to_dict(self):
        return {
            'callsign': self.callsign,
            'checksum': self.checksum,
            'location': self.location,
            'info': self.info,

        }
class Status(Base):
    __tablename__ = 'status'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

class P2PMessage(Base):
    __tablename__ = 'p2p_message'
    id = Column(String, primary_key=True)
    origin_callsign = Column(String, ForeignKey('station.callsign'))
    via_callsign = Column(String, ForeignKey('station.callsign'), nullable=True)
    destination_callsign = Column(String, ForeignKey('station.callsign'))
    body = Column(String, nullable=True)
    attachments = relationship('Attachment', backref='p2p_message')
    attempt = Column(Integer, default=0)
    timestamp = Column(DateTime)
    status_id = Column(Integer, ForeignKey('status.id'), nullable=True)
    status = relationship('Status', backref='p2p_messages')
    priority = Column(Integer, default=10)
    direction = Column(String)
    statistics = Column(JSON, nullable=True)
    is_read = Column(Boolean, default=True)

    Index('idx_p2p_message_origin_timestamp', 'origin_callsign', 'via_callsign', 'destination_callsign', 'timestamp', 'attachments')

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'attempt': self.attempt,
            'origin': self.origin_callsign,
            'via': self.via_callsign,
            'destination': self.destination_callsign,
            'direction': self.direction,
            'body': self.body,
            'attachments': [attachment.to_dict() for attachment in self.attachments],
            'status': self.status.name if self.status else None,
            'priority': self.priority,
            'is_read': self.is_read,
            'statistics': self.statistics
        }

class Attachment(Base):
    __tablename__ = 'attachment'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    data_type = Column(String)
    data = Column(String)
    message_id = Column(String, ForeignKey('p2p_message.id'))

    Index('idx_attachments_id_message_id', 'id', 'message_id')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'data_type': self.data_type,
            'data': self.data  # Be cautious with large binary data
        }
