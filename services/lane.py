import math
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from models.lane import Lane, LaneNode, LaneLeg, Node, Carrier, Caretaker, LaneStatus
from schemas.lane import LaneCreate, CaretakerCreate, NodeCreate, CarrierCreate


# ── Risk helpers ──────────────────────────────────────────

CARGO_REQS: dict[str, list[str]] = {
    "pharma": ["GDP"],
    "hazmat": ["ADR", "GDP"],
    "cold":   ["GDP"],
    "air":    ["IATA"],
}

def get_lane_requirements(cargo_type: str, extra_certs: list[str]) -> list[str]:
    base = CARGO_REQS.get(cargo_type, [])
    return list(set(base + extra_certs))

def calc_node_cert_status(node: Node, req: list[str]) -> str:
    for r in req:
        cert = node.certs.get(r)
        if not cert or cert == "bad":
            return "bad"
    for r in req:
        if node.certs.get(r) == "warn":
            return "warn"
    return "ok"

def calc_carrier_cert_status(carrier: Carrier, req: list[str]) -> str:
    for r in req:
        if r not in carrier.certs or carrier.cert_statuses.get(r) == "bad":
            return "bad"
    for r in req:
        if carrier.cert_statuses.get(r) == "warn":
            return "warn"
    return "ok"

def calc_lane_risk(
    nodes: list[Node],
    carriers: list[Carrier | None],
    req: list[str],
    total_hours: float
) -> float:
    scores = []

    for node in nodes:
        scores.append(node.risk)

    for node in nodes:
        st = calc_node_cert_status(node, req)
        if st == "bad":
            scores.append(9.0)
        elif st == "warn":
            scores.append(6.0)

    for carrier in carriers:
        if carrier is None:
            scores.append(8.0)
            continue
        if carrier.rating < 3:
            scores.append(8.0)
        elif carrier.rating < 4:
            scores.append(5.0)
        st = calc_carrier_cert_status(carrier, req)
        if st == "bad":
            scores.append(9.0)
        elif st == "warn":
            scores.append(6.0)

    if total_hours > 168:
        scores.append(8.0)
    elif total_hours > 72:
        scores.append(5.0)

    if not scores:
        return 5.0

    avg = sum(scores) / len(scores)
    mx  = max(scores)
    return round(0.6 * mx + 0.4 * avg, 1)

def derive_status(risk: float) -> LaneStatus:
    if risk <= 3:
        return LaneStatus.ok
    if risk <= 6:
        return LaneStatus.warn
    return LaneStatus.bad

def derive_transit_label(total_hours: float) -> str:
    if total_hours <= 0:
        return "TBD"
    if total_hours < 24:
        return f"{round(total_hours)}h"
    days = math.ceil(total_hours / 24)
    if days == 1:
        return "1 day"
    return f"{days} days"

def paginate(query, page: int, limit: int):
    offset = (page - 1) * limit
    return query.offset(offset).limit(limit)


# ── Node CRUD ─────────────────────────────────────────────

async def create_node(db: AsyncSession, data: NodeCreate) -> Node:
    node = Node(**data.model_dump())
    db.add(node)
    await db.commit()
    await db.refresh(node)
    return node

async def get_all_nodes(
    db: AsyncSession,
    region:   str | None   = None,
    country:  str | None   = None,
    type:     str | None   = None,
    risk_min: float | None = None,
    risk_max: float | None = None,
    page:     int          = 1,
    limit:    int          = 50,
) -> list[Node]:
    query = select(Node).where(Node.is_active == True)
    if region:
        query = query.where(Node.region == region)
    if country:
        query = query.where(Node.country == country)
    if type:
        query = query.where(Node.type == type)
    if risk_min is not None:
        query = query.where(Node.risk >= risk_min)
    if risk_max is not None:
        query = query.where(Node.risk <= risk_max)
    query = paginate(query, page, limit)
    result = await db.execute(query)
    return result.scalars().all()

async def get_node(db: AsyncSession, node_id: int) -> Node:
    result = await db.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node

async def update_node(db: AsyncSession, node_id: int, data: NodeCreate) -> Node:
    node = await get_node(db, node_id)
    for k, v in data.model_dump().items():
        setattr(node, k, v)
    await db.commit()
    await db.refresh(node)
    return node

async def delete_node(db: AsyncSession, node_id: int):
    node = await get_node(db, node_id)
    node.is_active = False
    await db.commit()


# ── Carrier CRUD ──────────────────────────────────────────

async def create_carrier(db: AsyncSession, data: CarrierCreate) -> Carrier:
    carrier = Carrier(**data.model_dump())
    db.add(carrier)
    await db.commit()
    await db.refresh(carrier)
    return carrier

async def get_all_carriers(
    db: AsyncSession,
    mode:       str | None   = None,
    country:    str | None   = None,
    rating_min: float | None = None,
    page:       int          = 1,
    limit:      int          = 50,
) -> list[Carrier]:
    query = select(Carrier).where(Carrier.is_active == True)
    if mode:
        query = query.where(Carrier.mode == mode)
    if country:
        query = query.where(Carrier.country == country)
    if rating_min is not None:
        query = query.where(Carrier.rating >= rating_min)
    query = paginate(query, page, limit)
    result = await db.execute(query)
    return result.scalars().all()

async def get_carrier(db: AsyncSession, carrier_id: int) -> Carrier:
    result = await db.execute(select(Carrier).where(Carrier.id == carrier_id))
    carrier = result.scalar_one_or_none()
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")
    return carrier

async def update_carrier(db: AsyncSession, carrier_id: int, data: CarrierCreate) -> Carrier:
    carrier = await get_carrier(db, carrier_id)
    for k, v in data.model_dump().items():
        setattr(carrier, k, v)
    await db.commit()
    await db.refresh(carrier)
    return carrier

async def delete_carrier(db: AsyncSession, carrier_id: int):
    carrier = await get_carrier(db, carrier_id)
    carrier.is_active = False
    await db.commit()


# ── Lane CRUD ─────────────────────────────────────────────

async def create_lane(
    db: AsyncSession,
    data: LaneCreate,
    owner_id: int | None = None
) -> Lane:
    if len(data.node_ids) < 2:
        raise HTTPException(status_code=400, detail="A lane needs at least 2 nodes")
    if len(data.legs) != len(data.node_ids) - 1:
        raise HTTPException(status_code=400, detail="legs count must equal nodes count minus 1")

    nodes = []
    for nid in data.node_ids:
        nodes.append(await get_node(db, nid))

    carriers = []
    for leg in data.legs:
        if leg.carrier_id:
            carriers.append(await get_carrier(db, leg.carrier_id))
        else:
            carriers.append(None)

    req           = get_lane_requirements(data.cargo_type, data.extra_certs)
    total_hours   = sum(c.avg_hours for c in carriers if c and c.avg_hours)
    risk          = calc_lane_risk(nodes, carriers, req, total_hours)
    transit_label = derive_transit_label(total_hours)
    lane_status   = derive_status(risk)

    lane = Lane(
        name        = data.name,
        cargo_type  = data.cargo_type,
        status      = lane_status,
        risk        = risk,
        transit     = transit_label,
        total_hours = total_hours,
        departure   = data.departure,
        notes       = data.notes,
        temp_min    = data.temp_min,
        temp_max    = data.temp_max,
        temp_unit   = data.temp_unit,
        extra_certs = data.extra_certs,
        owner_id    = owner_id,
    )
    db.add(lane)
    await db.flush()

    for i, node in enumerate(nodes):
        db.add(LaneNode(lane_id=lane.id, node_id=node.id, position=i))

    for i, (leg, carrier) in enumerate(zip(data.legs, carriers)):
        db.add(LaneLeg(
            lane_id    = lane.id,
            carrier_id = carrier.id if carrier else None,
            position   = i,
            leg_time   = leg.leg_time,
        ))

    await db.commit()
    return await get_lane(db, lane.id)

async def get_lane(db: AsyncSession, lane_id: int) -> Lane:
    result = await db.execute(
        select(Lane)
        .where(Lane.id == lane_id)
        .options(
            selectinload(Lane.lane_nodes).selectinload(LaneNode.node),
            selectinload(Lane.lane_legs).selectinload(LaneLeg.carrier),
        )
    )
    lane = result.scalar_one_or_none()
    if not lane:
        raise HTTPException(status_code=404, detail="Lane not found")
    return lane

async def get_all_lanes(
    db: AsyncSession,
    status:     str | None   = None,
    cargo_type: str | None   = None,
    risk_min:   float | None = None,
    risk_max:   float | None = None,
    owner_id:   int | None   = None,
    page:       int          = 1,
    limit:      int          = 50,
) -> list[Lane]:
    query = (
        select(Lane)
        .where(Lane.is_active == True)
        .options(
            selectinload(Lane.lane_nodes).selectinload(LaneNode.node),
            selectinload(Lane.lane_legs).selectinload(LaneLeg.carrier),
        )
    )
    if status:
        query = query.where(Lane.status == status)
    if cargo_type:
        query = query.where(Lane.cargo_type == cargo_type)
    if risk_min is not None:
        query = query.where(Lane.risk >= risk_min)
    if risk_max is not None:
        query = query.where(Lane.risk <= risk_max)
    if owner_id is not None:
        query = query.where(Lane.owner_id == owner_id)
    query = paginate(query, page, limit)
    result = await db.execute(query)
    return result.scalars().all()

async def update_lane(
    db: AsyncSession,
    lane_id: int,
    data: LaneCreate,
    owner_id: int | None = None
) -> Lane:
    lane = await get_lane(db, lane_id)

    await db.execute(delete(LaneNode).where(LaneNode.lane_id == lane_id))
    await db.execute(delete(LaneLeg).where(LaneLeg.lane_id  == lane_id))

    nodes = []
    for nid in data.node_ids:
        nodes.append(await get_node(db, nid))

    carriers = []
    for leg in data.legs:
        if leg.carrier_id:
            carriers.append(await get_carrier(db, leg.carrier_id))
        else:
            carriers.append(None)

    req           = get_lane_requirements(data.cargo_type, data.extra_certs)
    total_hours   = sum(c.avg_hours for c in carriers if c and c.avg_hours)
    risk          = calc_lane_risk(nodes, carriers, req, total_hours)
    transit_label = derive_transit_label(total_hours)

    lane.name        = data.name
    lane.cargo_type  = data.cargo_type
    lane.status      = derive_status(risk)
    lane.risk        = risk
    lane.transit     = transit_label
    lane.total_hours = total_hours
    lane.departure   = data.departure
    lane.notes       = data.notes
    lane.temp_min    = data.temp_min
    lane.temp_max    = data.temp_max
    lane.temp_unit   = data.temp_unit
    lane.extra_certs = data.extra_certs
    lane.updated_at  = datetime.now(timezone.utc)

    for i, node in enumerate(nodes):
        db.add(LaneNode(lane_id=lane.id, node_id=node.id, position=i))

    for i, (leg, carrier) in enumerate(zip(data.legs, carriers)):
        db.add(LaneLeg(
            lane_id    = lane.id,
            carrier_id = carrier.id if carrier else None,
            position   = i,
            leg_time   = leg.leg_time,
        ))

    await db.commit()
    return await get_lane(db, lane.id)

async def delete_lane(db: AsyncSession, lane_id: int):
    lane = await get_lane(db, lane_id)
    lane.is_active = False
    await db.commit()


async def duplicate_lane(db: AsyncSession, lane_id: int, owner_id: int | None = None) -> Lane:
    original = await get_lane(db, lane_id)

    new_lane = Lane(
        name        = f"{original.name} (copy)",
        cargo_type  = original.cargo_type,
        status      = original.status,
        risk        = original.risk,
        transit     = original.transit,
        total_hours = original.total_hours,
        departure   = original.departure,
        notes       = original.notes,
        temp_min    = original.temp_min,
        temp_max    = original.temp_max,
        temp_unit   = original.temp_unit,
        extra_certs = original.extra_certs,
        owner_id    = owner_id,
    )
    db.add(new_lane)
    await db.flush()

    for ln in original.lane_nodes:
        db.add(LaneNode(lane_id=new_lane.id, node_id=ln.node_id, position=ln.position))

    for ll in original.lane_legs:
        db.add(LaneLeg(
            lane_id    = new_lane.id,
            carrier_id = ll.carrier_id,
            position   = ll.position,
            leg_time   = ll.leg_time,
        ))

    await db.commit()
    return await get_lane(db, new_lane.id)

async def get_lanes_by_caretaker(db: AsyncSession, ct_id: int) -> list[Lane]:
    ct = await get_caretaker(db, ct_id)

    result = await db.execute(
        select(Lane)
        .join(LaneNode, LaneNode.lane_id == Lane.id)
        .where(
            Lane.is_active == True,
            LaneNode.node_id == ct.node_id,
        )
        .options(
            selectinload(Lane.lane_nodes).selectinload(LaneNode.node),
            selectinload(Lane.lane_legs).selectinload(LaneLeg.carrier),
        )
    )
    return result.scalars().all()

# ── Caretaker CRUD ────────────────────────────────────────

async def create_caretaker(db: AsyncSession, data: CaretakerCreate) -> Caretaker:
    await get_node(db, data.node_id)
    ct = Caretaker(**data.model_dump())
    db.add(ct)
    await db.commit()
    await db.refresh(ct)
    return ct

async def get_all_caretakers(
    db: AsyncSession,
    node_id: int | None = None,
    type:    str | None = None,
    country: str | None = None,
    page:    int        = 1,
    limit:   int        = 50,
) -> list[Caretaker]:
    query = select(Caretaker).where(Caretaker.is_active == True)
    if node_id:
        query = query.where(Caretaker.node_id == node_id)
    if type:
        query = query.where(Caretaker.type == type)
    if country:
        query = query.where(Caretaker.country == country)
    query = paginate(query, page, limit)
    result = await db.execute(query)
    return result.scalars().all()

async def get_caretaker(db: AsyncSession, ct_id: int) -> Caretaker:
    result = await db.execute(select(Caretaker).where(Caretaker.id == ct_id))
    ct = result.scalar_one_or_none()
    if not ct:
        raise HTTPException(status_code=404, detail="Caretaker not found")
    return ct

async def update_caretaker(db: AsyncSession, ct_id: int, data: CaretakerCreate) -> Caretaker:
    ct = await get_caretaker(db, ct_id)
    await get_node(db, data.node_id)
    for k, v in data.model_dump().items():
        setattr(ct, k, v)
    await db.commit()
    await db.refresh(ct)
    return ct

async def delete_caretaker(db: AsyncSession, ct_id: int):
    ct = await get_caretaker(db, ct_id)
    ct.is_active = False
    await db.commit()
