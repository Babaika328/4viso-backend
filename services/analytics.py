from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.lane import Lane, Carrier, Node, Caretaker, LaneLeg
from models.user import User


async def get_summary(db: AsyncSession) -> dict:
    # total lanes
    total_lanes = await db.scalar(
        select(func.count()).where(Lane.is_active == True)
    )

    # lanes by status
    ok_lanes   = await db.scalar(select(func.count()).where(Lane.is_active == True, Lane.status == "ok"))
    warn_lanes = await db.scalar(select(func.count()).where(Lane.is_active == True, Lane.status == "warn"))
    bad_lanes  = await db.scalar(select(func.count()).where(Lane.is_active == True, Lane.status == "bad"))

    # avg risk
    avg_risk = await db.scalar(
        select(func.avg(Lane.risk)).where(Lane.is_active == True)
    )

    # total nodes, carriers, caretakers, users
    total_nodes      = await db.scalar(select(func.count()).where(Node.is_active == True))
    total_carriers   = await db.scalar(select(func.count()).where(Carrier.is_active == True))
    total_caretakers = await db.scalar(select(func.count()).where(Caretaker.is_active == True))
    total_users      = await db.scalar(select(func.count(User.id)))

    return {
        "total_lanes":      total_lanes or 0,
        "ok_lanes":         ok_lanes or 0,
        "warn_lanes":       warn_lanes or 0,
        "bad_lanes":        bad_lanes or 0,
        "avg_risk":         round(float(avg_risk), 1) if avg_risk else None,
        "total_nodes":      total_nodes or 0,
        "total_carriers":   total_carriers or 0,
        "total_caretakers": total_caretakers or 0,
        "total_users":      total_users or 0,
    }


async def get_risk_distribution(db: AsyncSession) -> dict:
    lanes = await db.scalars(
        select(Lane.risk).where(Lane.is_active == True, Lane.risk != None)
    )
    risks = list(lanes)

    low    = len([r for r in risks if r <= 3])
    medium = len([r for r in risks if 3 < r <= 6])
    high   = len([r for r in risks if r > 6])

    return {
        "low":    low,
        "medium": medium,
        "high":   high,
    }


async def get_mode_breakdown(db: AsyncSession) -> dict:
    legs = await db.execute(
        select(LaneLeg.carrier_id)
        .join(Lane, LaneLeg.lane_id == Lane.id)
        .where(Lane.is_active == True, LaneLeg.carrier_id != None)
    )
    carrier_ids = [row[0] for row in legs.fetchall()]

    air  = 0
    road = 0
    sea  = 0

    if carrier_ids:
        carriers = await db.scalars(
            select(Carrier.mode).where(Carrier.id.in_(carrier_ids))
        )
        for mode in carriers:
            if mode.value == "Air":
                air += 1
            elif mode.value == "Road":
                road += 1
            elif mode.value == "Sea":
                sea += 1

    return {"Air": air, "Road": road, "Sea": sea}


async def get_cargo_breakdown(db: AsyncSession) -> dict:
    result = await db.execute(
        select(Lane.cargo_type, func.count())
        .where(Lane.is_active == True)
        .group_by(Lane.cargo_type)
    )
    return {row[0].value: row[1] for row in result.fetchall()}


async def get_caretaker_breakdown(db: AsyncSession) -> dict:
    result = await db.execute(
        select(Caretaker.type, func.count())
        .where(Caretaker.is_active == True)
        .group_by(Caretaker.type)
    )
    return {row[0].value: row[1] for row in result.fetchall()}