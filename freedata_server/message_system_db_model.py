# models.py

from sqlalchemy import Index, Boolean, Column, String, Integer, JSON, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class MessageAttachment(Base):
    """Represents the association between a message and an attachment.

    This association object links P2PMessage and Attachment records in
    the database, representing a many-to-many relationship between
    messages and attachments. It uses foreign keys and cascading deletes
    to maintain data integrity.
    """
    __tablename__ = 'message_attachment'
    message_id = Column(String, ForeignKey('p2p_message.id', ondelete='CASCADE'), primary_key=True)
    attachment_id = Column(Integer, ForeignKey('attachment.id', ondelete='CASCADE'), primary_key=True)

    message = relationship('P2PMessage', back_populates='message_attachments')
    attachment = relationship('Attachment', back_populates='message_attachments')

class Config(Base):
    """Represents a configuration setting in the database.

    This class maps to the 'config' table in the database and stores
    configuration settings. It currently only stores the database
    version.
    """
    __tablename__ = 'config'
    db_variable = Column(String, primary_key=True)  # Unique identifier for the configuration setting
    db_version = Column(String)

    def to_dict(self):
        """Converts the Config object to a dictionary.

        Returns:
            dict: A dictionary representation of the Config object.
        """
        return {
            'db_variable': self.db_variable,
            'db_version': self.db_version
        }


class Beacon(Base):
    """Represents a beacon signal received by the station.

    This class maps to the 'beacon' table and stores information about
    received beacon signals, including the timestamp, signal-to-noise
    ratio (SNR), and the callsign of the transmitting station. It is
    linked to the Station table via a foreign key.
    """
    __tablename__ = 'beacon'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    snr = Column(Integer)
    callsign = Column(String, ForeignKey('station.callsign'))
    station = relationship("Station", back_populates="beacons")

    Index('idx_beacon_callsign', 'callsign')

class Station(Base):
    """Represents a station in the network.

    This class maps to the 'station' table and stores information about
    stations, including their callsign, checksum, location (as JSON),
    and additional info (as JSON). It has a relationship with the Beacon
    table, representing the beacons received from this station.
    """
    __tablename__ = 'station'
    callsign = Column(String, primary_key=True)
    checksum = Column(String, nullable=True)
    location = Column(JSON, nullable=True)
    info = Column(JSON, nullable=True)
    beacons = relationship("Beacon", order_by="Beacon.id", back_populates="station")

    Index('idx_station_callsign_checksum', 'callsign', 'checksum')

    def to_dict(self):
        """Converts the Station object to a dictionary.

        Returns:
            dict: A dictionary representation of the Station object.
        """
        return {
            'callsign': self.callsign,
            'checksum': self.checksum,
            'location': self.location,
            'info': self.info,

        }
class Status(Base):
    """Represents the status of a P2P message.

    This class maps to the 'status' table and stores the possible
    statuses a message can have (e.g., 'queued', 'transmitted',
    'received', 'failed'). The `name` field is unique to prevent
    duplicate status entries.
    """
    __tablename__ = 'status'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

class P2PMessage(Base):
    """Represents a peer-to-peer (P2P) message.

    This class maps to the 'p2p_message' table and stores information
    about P2P messages, including sender, recipient, message body,
    attachments, transmission attempts, timestamp, status, priority,
    direction, statistics (JSON), and read status. It has relationships
    with the Station, Status, and Attachment tables.
    """
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

    Index('idx_p2p_message_origin_timestamp', 'origin_callsign', 'via_callsign', 'destination_callsign', 'timestamp')

    def to_dict(self):
        """Converts the P2PMessage object to a dictionary.

        This method converts the P2PMessage object and its associated
        attachments to a dictionary format, suitable for serialization or
        other data processing. It retrieves the attachment data using
        the to_dict method of each attachment object. It formats the
        timestamp as an ISO 8601 string.

        Returns:
            dict: A dictionary representation of the P2PMessage object,
            including its attachments.
        """
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
    """Represents a file attachment associated with a message.

    This class maps to the 'attachment' table and stores information
    about attachments, including their name, data type, data content,
    CRC32 checksum, and SHA-512 hash. It has a relationship with the
    MessageAttachment association table.
    """
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
        """Converts the Attachment object to a dictionary.

        Returns:
            dict: A dictionary representation of the Attachment object.
        """
        return {
            'id': self.id,
            'name': self.name,
            'type': self.data_type,
            'data': self.data,
            'checksum_crc32': self.checksum_crc32,
            'hash_sha512' : self.hash_sha512
        }
