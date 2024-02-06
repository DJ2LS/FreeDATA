# models.py

from sqlalchemy import Index, Boolean, Column, String, Integer, JSON, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class MessageAttachment(Base):
    __tablename__ = 'message_attachment'
    message_id = Column(String, ForeignKey('p2p_message.id', ondelete='CASCADE'), primary_key=True)
    attachment_id = Column(Integer, ForeignKey('attachment.id', ondelete='CASCADE'), primary_key=True)

    message = relationship('P2PMessage', back_populates='message_attachments')
    attachment = relationship('Attachment', back_populates='message_attachments')

class Config(Base):
    __tablename__ = 'config'
    db_variable = Column(String, primary_key=True)  # Unique identifier for the configuration setting
    db_version = Column(String)

    def to_dict(self):
        return {
            'db_variable': self.db_variable,
            'db_settings': self.db_settings
        }


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
    message_attachments = relationship('MessageAttachment',
                                       back_populates='message',
                                       cascade='all, delete-orphan')
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
        attachments_list = [ma.attachment.to_dict() for ma in self.message_attachments]

        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'attempt': self.attempt,
            'origin': self.origin_callsign,
            'via': self.via_callsign,
            'destination': self.destination_callsign,
            'direction': self.direction,
            'body': self.body,
            'attachments': attachments_list,
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
    checksum_crc32 = Column(String)
    hash_sha512 = Column(String)
    message_attachments = relationship("MessageAttachment", back_populates="attachment")

    Index('idx_attachments_id_message_id', 'id', 'hash_sha512')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.data_type,
            'data': self.data,
            'checksum_crc32': self.checksum_crc32,
            'hash_sha512' : self.hash_sha512
        }
