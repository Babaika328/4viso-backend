from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from middleware.auth import require_admin, require_staff, require_user
from models.user import User
from schemas.lane import (
    NodeCreate, NodeOut,
    CarrierCreate, CarrierOut,
    LaneCreate, LaneOut,
    CaretakerCreate, CaretakerOut,
)
import services.lane as svc

router = APIRouter(prefix="/api", tags=["lanes"])


# ── Nodes ─────────────────────────────────────────────────

@router.get("/nodes", response_model=list[NodeOut])
async def list_nodes(
    region:   str | None   = Query(None),
    country:  str | None   = Query(None),
    type:     str | None   = Query(None),
    risk_min: float | None = Query(None),
    risk_max: float | None = Query(None),
    page:     int          = Query(1, ge=1),
    limit:    int          = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_user),
):
    return await svc.get_all_nodes(
        db, region=region, country=country, type=type,
        risk_min=risk_min, risk_max=risk_max, page=page, limit=limit
    )

@router.get("/nodes/{node_id}", response_model=NodeOut)
async def get_node(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_user),
):
    return await svc.get_node(db, node_id)

@router.post("/nodes", response_model=NodeOut)
async def create_node(
    data: NodeCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await svc.create_node(db, data)

@router.put("/nodes/{node_id}", response_model=NodeOut)
async def update_node(
    node_id: int,
    data: NodeCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await svc.update_node(db, node_id, data)

@router.delete("/nodes/{node_id}")
async def delete_node(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await svc.delete_node(db, node_id)
    return {"detail": "Node deactivated"}


# ── Carriers ──────────────────────────────────────────────

@router.get("/carriers", response_model=list[CarrierOut])
async def list_carriers(
    mode:       str | None   = Query(None),
    country:    str | None   = Query(None),
    rating_min: float | None = Query(None),
    page:       int          = Query(1, ge=1),
    limit:      int          = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_user),
):
    return await svc.get_all_carriers(
        db, mode=mode, country=country,
        rating_min=rating_min, page=page, limit=limit
    )

@router.get("/carriers/{carrier_id}", response_model=CarrierOut)
async def get_carrier(
    carrier_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_user),
):
    return await svc.get_carrier(db, carrier_id)

@router.post("/carriers", response_model=CarrierOut)
async def create_carrier(
    data: CarrierCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await svc.create_carrier(db, data)

@router.put("/carriers/{carrier_id}", response_model=CarrierOut)
async def update_carrier(
    carrier_id: int,
    data: CarrierCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await svc.update_carrier(db, carrier_id, data)

@router.delete("/carriers/{carrier_id}")
async def delete_carrier(
    carrier_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await svc.delete_carrier(db, carrier_id)
    return {"detail": "Carrier deactivated"}


# ── Lanes ─────────────────────────────────────────────────

@router.get("/lanes", response_model=list[LaneOut])
async def list_lanes(
    status:     str | None   = Query(None),
    cargo_type: str | None   = Query(None),
    risk_min:   float | None = Query(None),
    risk_max:   float | None = Query(None),
    my_lanes:   bool         = Query(False),
    page:       int          = Query(1, ge=1),
    limit:      int          = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    owner_id = current_user.id if my_lanes else None
    return await svc.get_all_lanes(
        db, status=status, cargo_type=cargo_type,
        risk_min=risk_min, risk_max=risk_max,
        owner_id=owner_id, page=page, limit=limit
    )

@router.get("/lanes/{lane_id}", response_model=LaneOut)
async def get_lane(
    lane_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_user),
):
    return await svc.get_lane(db, lane_id)

@router.post("/lanes", response_model=LaneOut)
async def create_lane(
    data: LaneCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    return await svc.create_lane(db, data, owner_id=current_user.id)

@router.put("/lanes/{lane_id}", response_model=LaneOut)
async def update_lane(
    lane_id: int,
    data: LaneCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    return await svc.update_lane(db, lane_id, data, owner_id=current_user.id)

@router.delete("/lanes/{lane_id}")
async def delete_lane(
    lane_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
):
    await svc.delete_lane(db, lane_id)
    return {"detail": "Lane deactivated"}

@router.post("/lanes/{lane_id}/duplicate", response_model=LaneOut)
async def duplicate_lane(
    lane_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    return await svc.duplicate_lane(db, lane_id, owner_id=current_user.id)

# ── Caretakers ────────────────────────────────────────────

@router.get("/caretakers", response_model=list[CaretakerOut])
async def list_caretakers(
    node_id: int | None = Query(None),
    type:    str | None = Query(None),
    country: str | None = Query(None),
    page:    int        = Query(1, ge=1),
    limit:   int        = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_user),
):
    return await svc.get_all_caretakers(
        db, node_id=node_id, type=type,
        country=country, page=page, limit=limit
    )

@router.get("/caretakers/{ct_id}", response_model=CaretakerOut)
async def get_caretaker(
    ct_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_user),
):
    return await svc.get_caretaker(db, ct_id)

@router.get("/caretakers/{ct_id}/lanes", response_model=list[LaneOut])
async def get_caretaker_lanes(
    ct_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_user),
):
    return await svc.get_lanes_by_caretaker(db, ct_id)

@router.post("/caretakers", response_model=CaretakerOut)
async def create_caretaker(
    data: CaretakerCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
):
    return await svc.create_caretaker(db, data)

@router.put("/caretakers/{ct_id}", response_model=CaretakerOut)
async def update_caretaker(
    ct_id: int,
    data: CaretakerCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
):
    return await svc.update_caretaker(db, ct_id, data)

@router.delete("/caretakers/{ct_id}")
async def delete_caretaker(
    ct_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
):
    await svc.delete_caretaker(db, ct_id)
    return {"detail": "Caretaker deactivated"}