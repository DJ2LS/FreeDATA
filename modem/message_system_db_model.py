# models.py

from sqlalchemy import Column, String, Integer, JSON, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Station(Base):
    __tablename__ = 'station'
    callsign = Column(String, primary_key=True)
    location = Column(JSON, nullable=True)
    info = Column(JSON, nullable=True)

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
    timestamp = Column(DateTime)
    status_id = Column(Integer, ForeignKey('status.id'), nullable=True)
    status = relationship('Status', backref='p2p_messages')
    direction = Column(String)
    statistics = Column(JSON, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'origin': self.origin_callsign,
            'via': self.via_callsign,
            'destination': self.destination_callsign,
            'direction': self.direction,
            'body': self.body,
            'attachments': [attachment.to_dict() for attachment in self.attachments],
            'status': self.status.name if self.status else None,
            'statistics': self.statistics
        }

class Attachment(Base):
    __tablename__ = 'attachment'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    data_type = Column(String)
    data = Column(String)
    message_id = Column(String, ForeignKey('p2p_message.id'))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'data_type': self.data_type,
            'data': self.data  # Be cautious with large binary data
        }
