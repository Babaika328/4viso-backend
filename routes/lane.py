from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from middleware.auth import get_current_user, require_admin, require_staff
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
async def list_nodes(db: AsyncSession = Depends(get_db)):
    return await svc.get_all_nodes(db)

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
async def list_carriers(db: AsyncSession = Depends(get_db)):
    return await svc.get_all_carriers(db)

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
async def list_lanes(db: AsyncSession = Depends(get_db)):
    return await svc.get_all_lanes(db)

@router.get("/lanes/{lane_id}", response_model=LaneOut)
async def get_lane(
    lane_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await svc.get_lane(db, lane_id)

@router.post("/lanes", response_model=LaneOut)
async def create_lane(
    data: LaneCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await svc.create_lane(db, data, owner_id=current_user.id)

@router.put("/lanes/{lane_id}", response_model=LaneOut)
async def update_lane(
    lane_id: int,
    data: LaneCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
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


# ── Caretakers ────────────────────────────────────────────

@router.get("/caretakers", response_model=list[CaretakerOut])
async def list_caretakers(db: AsyncSession = Depends(get_db)):
    return await svc.get_all_caretakers(db)

@router.get("/caretakers/{ct_id}", response_model=CaretakerOut)
async def get_caretaker(
    ct_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await svc.get_caretaker(db, ct_id)

@router.post("/caretakers", response_model=CaretakerOut)
async def create_caretaker(
    data: CaretakerCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await svc.create_caretaker(db, data)

@router.put("/caretakers/{ct_id}", response_model=CaretakerOut)
async def update_caretaker(
    ct_id: int,
    data: CaretakerCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
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