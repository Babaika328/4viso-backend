from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, Enum, ForeignKey, Table, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from models.user import Base


# ── Enums ─────────────────────────────────────────────────

class TransportMode(str, enum.Enum):
    air  = "Air"
    road = "Road"
    sea  = "Sea"

class CargoType(str, enum.Enum):
    pharma = "pharma"
    hazmat = "hazmat"
    cold   = "cold"
    air    = "air"

class NodeType(str, enum.Enum):
    warehouse            = "Warehouse"
    factory              = "Factory"
    airport              = "Airport"
    hub                  = "Hub"
    port                 = "Port"
    handler              = "Handler"
    distribution_center  = "Distribution Center"

class CaretakerType(str, enum.Enum):
    stevedore         = "Stevedore"
    ground_handler    = "Ground Handler"
    terminal_operator = "Terminal Operator"
    warehouse_keeper  = "Warehouse Keeper"
    customs_agent     = "Customs Agent"
    cold_store        = "Cold Store"

class LaneStatus(str, enum.Enum):
    ok   = "ok"
    warn = "warn"
    bad  = "bad"

class CertStatus(str, enum.Enum):
    ok   = "ok"
    warn = "warn"
    bad  = "bad"


# ── Node ──────────────────────────────────────────────────

class Node(Base):
    __tablename__ = "nodes"

    id              = Column(Integer, primary_key=True, index=True)
    company         = Column(String, nullable=False)
    type            = Column(Enum(NodeType), nullable=False)
    country         = Column(String(2), nullable=False)   # ISO 2-letter
    region          = Column(String, nullable=False)
    risk            = Column(Float, nullable=False, default=5.0)
    rating          = Column(Float, nullable=False, default=3.0)
    lat             = Column(Float, nullable=True)
    lng             = Column(Float, nullable=True)
    handling_time   = Column(Float, nullable=False, default=1.0)   # hours
    timezone        = Column(String, nullable=True)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # certs stored as {cert_name: "ok"|"warn"|"bad"}
    certs           = Column(JSON, nullable=False, default=dict)

    caretakers      = relationship("Caretaker", back_populates="node")
    lane_nodes      = relationship("LaneNode", back_populates="node")


# ── Carrier ───────────────────────────────────────────────

class Carrier(Base):
    __tablename__ = "carriers"

    id          = Column(Integer, primary_key=True, index=True)
    company     = Column(String, nullable=False)
    mode        = Column(Enum(TransportMode), nullable=False)
    country     = Column(String(2), nullable=False)
    transit     = Column(String, nullable=True)        # human label e.g. "1-2d"
    avg_hours   = Column(Float, nullable=True)
    rating      = Column(Float, nullable=False, default=3.0)
    cutoff      = Column(String, nullable=True)        # e.g. "17:00"
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # certs: list of cert names the carrier holds  e.g. ["GDP", "ADR"]
    # cert_statuses: {cert_name: "ok"|"warn"|"bad"}
    certs           = Column(JSON, nullable=False, default=list)
    cert_statuses   = Column(JSON, nullable=False, default=dict)

    lane_legs       = relationship("LaneLeg", back_populates="carrier")


# ── Lane ──────────────────────────────────────────────────

class Lane(Base):
    __tablename__ = "lanes"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String, nullable=False)
    cargo_type      = Column(Enum(CargoType), nullable=False)
    status          = Column(Enum(LaneStatus), nullable=False, default=LaneStatus.ok)
    risk            = Column(Float, nullable=True)
    transit         = Column(String, nullable=True)     # human label
    total_hours     = Column(Float, nullable=True)
    departure       = Column(String, nullable=True)
    notes           = Column(String, nullable=True)
    temp_min        = Column(String, nullable=True)
    temp_max        = Column(String, nullable=True)
    temp_unit       = Column(String, nullable=True, default="°C")
    extra_certs     = Column(JSON, nullable=False, default=list)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at      = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    owner_id        = Column(Integer, ForeignKey("users.id"), nullable=True)

    # ordered list of nodes with position index
    lane_nodes      = relationship("LaneNode", back_populates="lane", order_by="LaneNode.position", cascade="all, delete-orphan")
    # ordered list of legs (node[i] → node[i+1]) with carrier
    lane_legs       = relationship("LaneLeg",  back_populates="lane", order_by="LaneLeg.position",  cascade="all, delete-orphan")


# ── LaneNode  (lane ↔ node with position) ────────────────

class LaneNode(Base):
    __tablename__ = "lane_nodes"

    id          = Column(Integer, primary_key=True, index=True)
    lane_id     = Column(Integer, ForeignKey("lanes.id"),  nullable=False)
    node_id     = Column(Integer, ForeignKey("nodes.id"),  nullable=False)
    position    = Column(Integer, nullable=False)           # 0 = origin, last = destination

    lane        = relationship("Lane", back_populates="lane_nodes")
    node        = relationship("Node", back_populates="lane_nodes")


# ── LaneLeg  (carrier assignment per leg) ────────────────

class LaneLeg(Base):
    __tablename__ = "lane_legs"

    id          = Column(Integer, primary_key=True, index=True)
    lane_id     = Column(Integer, ForeignKey("lanes.id"),     nullable=False)
    carrier_id  = Column(Integer, ForeignKey("carriers.id"),  nullable=True)   # nullable = unassigned
    position    = Column(Integer, nullable=False)             # leg 0 = node[0]→node[1]
    leg_time    = Column(String,  nullable=True)              # transit label for this leg

    lane        = relationship("Lane",    back_populates="lane_legs")
    carrier     = relationship("Carrier", back_populates="lane_legs")


# ── Caretaker ─────────────────────────────────────────────

class Caretaker(Base):
    __tablename__ = "caretakers"

    id                  = Column(Integer, primary_key=True, index=True)
    company             = Column(String, nullable=False)
    type                = Column(Enum(CaretakerType), nullable=False)
    node_id             = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    country             = Column(String(2), nullable=False)
    contact_name        = Column(String, nullable=True)
    contact_phone       = Column(String, nullable=True)
    contact_email       = Column(String, nullable=True)
    available           = Column(String, nullable=True)
    notes               = Column(String, nullable=True)
    rating              = Column(Float, nullable=False, default=3.0)
    is_active           = Column(Boolean, default=True)
    created_at          = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    responsibilities    = Column(JSON, nullable=False, default=list)   # ["Vessel unloading", ...]
    certs               = Column(JSON, nullable=False, default=list)   # ["GDP", "ISO 28000", ...]

    node                = relationship("Node", back_populates="caretakers")