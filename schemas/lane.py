from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models.lane import TransportMode, CargoType, NodeType, CaretakerType, LaneStatus, CertStatus


# ── Node ──────────────────────────────────────────────────

class NodeCreate(BaseModel):
    company:        str
    type:           NodeType
    country:        str = Field(..., min_length=2, max_length=2)
    region:         str
    risk:           float = Field(5.0, ge=0, le=10)
    rating:         float = Field(3.0, ge=0, le=5)
    lat:            Optional[float] = None
    lng:            Optional[float] = None
    handling_time:  float = 1.0
    timezone:       Optional[str] = None
    certs:          dict = {}       # {"GDP": "ok", "IATA": "warn"}

class NodeOut(NodeCreate):
    id:         int
    is_active:  bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Carrier ───────────────────────────────────────────────

class CarrierCreate(BaseModel):
    company:        str
    mode:           TransportMode
    country:        str = Field(..., min_length=2, max_length=2)
    transit:        Optional[str] = None
    avg_hours:      Optional[float] = None
    rating:         float = Field(3.0, ge=0, le=5)
    cutoff:         Optional[str] = None
    certs:          list[str] = []          # ["GDP", "ADR"]
    cert_statuses:  dict = {}               # {"GDP": "ok", "ADR": "warn"}

class CarrierOut(CarrierCreate):
    id:         int
    is_active:  bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Lane ──────────────────────────────────────────────────

class LegIn(BaseModel):
    carrier_id: Optional[int] = None
    leg_time:   Optional[str] = None

class LaneCreate(BaseModel):
    name:           str
    cargo_type:     CargoType
    node_ids:       list[int]               # ordered: [origin, stop1, ..., destination]
    legs:           list[LegIn]             # len == len(node_ids) - 1
    departure:      Optional[str] = None
    notes:          Optional[str] = None
    temp_min:       Optional[str] = None
    temp_max:       Optional[str] = None
    temp_unit:      str = "°C"
    extra_certs:    list[str] = []

class LaneNodeOut(BaseModel):
    position:   int
    node:       NodeOut
    model_config = {"from_attributes": True}

class LaneLegOut(BaseModel):
    position:   int
    carrier:    Optional[CarrierOut] = None
    leg_time:   Optional[str] = None
    model_config = {"from_attributes": True}

class LaneOut(BaseModel):
    id:             int
    name:           str
    cargo_type:     CargoType
    status:         LaneStatus
    risk:           Optional[float]
    transit:        Optional[str]
    total_hours:    Optional[float]
    departure:      Optional[str]
    notes:          Optional[str]
    temp_min:       Optional[str]
    temp_max:       Optional[str]
    temp_unit:      Optional[str]
    extra_certs:    list[str]
    is_active:      bool
    created_at:     datetime
    updated_at:     datetime
    lane_nodes:     list[LaneNodeOut]
    lane_legs:      list[LaneLegOut]
    model_config = {"from_attributes": True}


# ── Caretaker ─────────────────────────────────────────────

class CaretakerCreate(BaseModel):
    company:            str
    type:               CaretakerType
    node_id:            int
    country:            str = Field(..., min_length=2, max_length=2)
    contact_name:       Optional[str] = None
    contact_phone:      Optional[str] = None
    contact_email:      Optional[str] = None
    available:          Optional[str] = None
    notes:              Optional[str] = None
    rating:             float = Field(3.0, ge=0, le=5)
    responsibilities:   list[str] = []
    certs:              list[str] = []

class CaretakerOut(CaretakerCreate):
    id:         int
    is_active:  bool
    created_at: datetime
    model_config = {"from_attributes": True}