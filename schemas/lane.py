from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models.lane import TransportMode, CargoType, NodeType, CaretakerType, LaneStatus


# ── Node ──────────────────────────────────────────────────

class NodeCreate(BaseModel):
    company:       str   = Field(..., min_length=1, max_length=200)
    type:          NodeType
    country:       str   = Field(..., min_length=2, max_length=2)
    region:        str   = Field(..., min_length=1, max_length=100)
    risk:          float = Field(5.0, ge=0, le=10)
    rating:        float = Field(3.0, ge=0, le=5)
    lat:           Optional[float] = Field(None, ge=-90,  le=90)
    lng:           Optional[float] = Field(None, ge=-180, le=180)
    handling_time: float = Field(1.0, ge=0, le=720)
    timezone:      Optional[str] = Field(None, max_length=50)
    certs:         dict = {}

class NodeOut(NodeCreate):
    id:         int
    is_active:  bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Carrier ───────────────────────────────────────────────

class CarrierCreate(BaseModel):
    company:       str   = Field(..., min_length=1, max_length=200)
    mode:          TransportMode
    country:       str   = Field(..., min_length=2, max_length=2)
    transit:       Optional[str]   = Field(None, max_length=100)
    avg_hours:     Optional[float] = Field(None, ge=0, le=100000)
    rating:        float = Field(3.0, ge=0, le=5)
    cutoff:        Optional[str]   = Field(None, max_length=10)
    certs:         list[str] = []
    cert_statuses: dict = {}

class CarrierOut(CarrierCreate):
    id:         int
    is_active:  bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Lane ──────────────────────────────────────────────────

class LegIn(BaseModel):
    carrier_id: Optional[int] = None
    leg_time:   Optional[str] = Field(None, max_length=50)

class LaneCreate(BaseModel):
    name:        str  = Field(..., min_length=1, max_length=300)
    cargo_type:  CargoType
    node_ids:    list[int]   = Field(..., min_length=2, max_length=20)
    legs:        list[LegIn] = Field(..., max_length=19)
    departure:   Optional[str] = Field(None, max_length=100)
    notes:       Optional[str] = Field(None, max_length=2000)
    temp_min:    Optional[str] = Field(None, max_length=20)
    temp_max:    Optional[str] = Field(None, max_length=20)
    temp_unit:   str = Field("°C", max_length=10)
    extra_certs: list[str] = Field(default=[], max_length=50)

class LaneNodeOut(BaseModel):
    position: int
    node:     NodeOut
    model_config = {"from_attributes": True}

class LaneLegOut(BaseModel):
    position: int
    carrier:  Optional[CarrierOut] = None
    leg_time: Optional[str] = None
    model_config = {"from_attributes": True}

class LaneOut(BaseModel):
    id:          int
    name:        str
    cargo_type:  CargoType
    status:      LaneStatus
    risk:        Optional[float]
    transit:     Optional[str]
    total_hours: Optional[float]
    departure:   Optional[str]
    notes:       Optional[str]
    temp_min:    Optional[str]
    temp_max:    Optional[str]
    temp_unit:   Optional[str]
    extra_certs: list[str]
    is_active:   bool
    created_at:  datetime
    updated_at:  datetime
    lane_nodes:  list[LaneNodeOut]
    lane_legs:   list[LaneLegOut]
    model_config = {"from_attributes": True}


# ── Caretaker ─────────────────────────────────────────────

class CaretakerCreate(BaseModel):
    company:          str   = Field(..., min_length=1, max_length=200)
    type:             CaretakerType
    node_id:          int
    country:          str   = Field(..., min_length=2, max_length=2)
    contact_name:     Optional[str] = Field(None, max_length=200)
    contact_phone:    Optional[str] = Field(None, max_length=50)
    contact_email:    Optional[str] = Field(None, max_length=200)
    available:        Optional[str] = Field(None, max_length=100)
    notes:            Optional[str] = Field(None, max_length=2000)
    rating:           float = Field(3.0, ge=0, le=5)
    responsibilities: list[str] = Field(default=[], max_length=50)
    certs:            list[str] = Field(default=[], max_length=50)

class CaretakerOut(CaretakerCreate):
    id:         int
    is_active:  bool
    created_at: datetime
    model_config = {"from_attributes": True}