# DEV ONLY — run once to populate a fresh database
import asyncio
from database import AsyncSessionLocal, engine
from models.user import Base
from models.lane import Node, Carrier, Caretaker
from services.lane import create_node, create_carrier, create_caretaker
from schemas.lane import NodeCreate, CarrierCreate, CaretakerCreate
from sqlalchemy import select, func
from models.lane import Node

NODES = [
    NodeCreate(company="DB Schenker BRU",    type="Warehouse",           country="BE", region="Europe",      risk=1.8, rating=4.2, lat=50.85, lng=4.35,   handling_time=1.5, timezone="CET", certs={"GDP":"ok","ISO 9001":"ok","IATA":"ok","AEO":"ok"}),
    NodeCreate(company="Cipla Mumbai",        type="Factory",             country="IN", region="South Asia",  risk=2.1, rating=4.5, lat=19.08, lng=72.88,  handling_time=3.0, timezone="IST", certs={"GDP":"ok","ISO 9001":"ok","GMP":"ok"}),
    NodeCreate(company="Air India DEL",       type="Airport",             country="IN", region="South Asia",  risk=1.9, rating=3.8, lat=28.56, lng=77.10,  handling_time=2.0, timezone="IST", certs={"IATA":"ok","GDP":"ok","IATA CASS":"ok"}),
    NodeCreate(company="Kuehne+Nagel LDN",   type="Warehouse",           country="GB", region="Europe",      risk=8.5, rating=2.1, lat=51.51, lng=-0.12,  handling_time=4.0, timezone="GMT", certs={"GDP":"bad"}),
    NodeCreate(company="DB Schenker FRA",    type="Hub",                 country="DE", region="Europe",      risk=3.8, rating=4.0, lat=50.11, lng=8.68,   handling_time=2.0, timezone="CET", certs={"GDP":"ok","ISO 9001":"warn","AEO":"ok"}),
    NodeCreate(company="PSA Antwerp",        type="Port",                country="BE", region="Europe",      risk=1.7, rating=4.6, lat=51.23, lng=4.40,   handling_time=6.0, timezone="CET", certs={"ISO 28000":"ok","GDP":"ok","AEO":"ok"}),
    NodeCreate(company="Aramex Dubai",       type="Hub",                 country="AE", region="Middle East", risk=2.3, rating=4.3, lat=25.20, lng=55.27,  handling_time=2.0, timezone="GST", certs={"GDP":"ok","IATA":"ok","IATA CASS":"ok"}),
    NodeCreate(company="DHL Singapore",      type="Hub",                 country="SG", region="SE Asia",     risk=2.0, rating=4.7, lat=1.35,  lng=103.82, handling_time=2.0, timezone="SGT", certs={"GDP":"ok","IATA":"ok","ISO 9001":"ok"}),
    NodeCreate(company="Menzies BRU",        type="Handler",             country="BE", region="Europe",      risk=2.2, rating=4.1, lat=50.90, lng=4.48,   handling_time=1.0, timezone="CET", certs={"IATA":"ok","GDP":"ok"}),
    NodeCreate(company="Swissport BOM",      type="Handler",             country="IN", region="South Asia",  risk=2.4, rating=3.9, lat=19.09, lng=72.87,  handling_time=1.0, timezone="IST", certs={"IATA":"ok","GDP":"warn"}),
    NodeCreate(company="McKesson Chicago",   type="Distribution Center", country="US", region="N. America",  risk=1.5, rating=4.8, lat=41.88, lng=-87.63, handling_time=2.0, timezone="CST", certs={"GDP":"ok","ISO 9001":"ok","C-TPAT":"ok"}),
    NodeCreate(company="Roche Basel",        type="Distribution Center", country="CH", region="Europe",      risk=1.2, rating=4.9, lat=47.56, lng=7.59,   handling_time=1.5, timezone="CET", certs={"GDP":"ok","ISO 9001":"ok","IATA":"ok","GMP":"ok"}),
]

CARRIERS = [
    CarrierCreate(company="EuroCargo GmbH",   mode="Road", country="DE", transit="1-2d",     avg_hours=28,  rating=4.3, cutoff="17:00", certs=["GDP","ADR"],               cert_statuses={"GDP":"ok","ADR":"ok"}),
    CarrierCreate(company="SkyFreight NV",    mode="Air",  country="BE", transit="Same day",  avg_hours=8,   rating=3.7, cutoff="14:00", certs=["IATA","GDP","IATA CASS"],  cert_statuses={"IATA":"ok","GDP":"warn","IATA CASS":"ok"}),
    CarrierCreate(company="OceanLink Ltd",    mode="Sea",  country="NL", transit="14-21d",    avg_hours=408, rating=4.1, cutoff="09:00", certs=["ISO 28000","IMDG"],         cert_statuses={"ISO 28000":"ok","IMDG":"ok"}),
    CarrierCreate(company="PharmaRoad UK",    mode="Road", country="GB", transit="1d",        avg_hours=18,  rating=2.2, cutoff="12:00", certs=["GDP"],                     cert_statuses={"GDP":"bad"}),
    CarrierCreate(company="Air India Cargo",  mode="Air",  country="IN", transit="Same day",  avg_hours=9,   rating=4.0, cutoff="15:00", certs=["IATA","GDP","IATA CASS"],  cert_statuses={"IATA":"ok","GDP":"ok","IATA CASS":"ok"}),
    CarrierCreate(company="TransMed SAS",     mode="Road", country="FR", transit="2-3d",      avg_hours=48,  rating=3.8, cutoff="16:00", certs=["GDP","ADR"],               cert_statuses={"GDP":"ok","ADR":"warn"}),
    CarrierCreate(company="ColdEx Logistics", mode="Road", country="BE", transit="1d",        avg_hours=20,  rating=4.4, cutoff="16:00", certs=["GDP","ADR","HACCP"],       cert_statuses={"GDP":"ok","ADR":"ok","HACCP":"ok"}),
]

CARETAKERS = [
    CaretakerCreate(company="Antwerp Stevedoring Co.", type="Stevedore",         node_id=6,  country="BE", contact_name="Jan Van Dyck",    contact_phone="+32 3 234 5678",  contact_email="ops@asc-antwerp.be",       available="24/7",                rating=4.4, responsibilities=["Vessel unloading","Container handling","Storage","Stacking"],                           certs=["ISO 28000","IMDG"],        notes="Primary stevedore at North Quay."),
    CaretakerCreate(company="PSA Cargo Handlers NV",   type="Terminal Operator", node_id=6,  country="BE", contact_name="Marie Dubois",    contact_phone="+32 3 345 6789",  contact_email="cargo@psa-handlers.be",    available="Mon–Sun 06:00–22:00", rating=4.6, responsibilities=["Gate control","Reefer monitoring","Documentation","Transit handling"],                   certs=["ISO 28000","AEO","GDP"],   notes="GDP-certified reefer plugs available."),
    CaretakerCreate(company="Menzies Ground Services", type="Ground Handler",    node_id=9,  country="BE", contact_name="Pieter Claes",    contact_phone="+32 2 753 1234",  contact_email="groundops@menzies-bru.be", available="24/7",                rating=4.1, responsibilities=["Ramp handling","Loading / unloading","Aircraft transfer"],                           certs=["IATA","GDP"],              notes="Terminal B, ramp side."),
    CaretakerCreate(company="Swissport Cargo BRU",     type="Ground Handler",    node_id=9,  country="BE", contact_name="Lena Haas",       contact_phone="+32 2 753 9876",  contact_email="cargo.bru@swissport.com",  available="24/7",                rating=4.5, responsibilities=["Cargo acceptance","Build-up / breakdown","Cool room management","Segregation"],        certs=["IATA","GDP","IATA CASS"], notes="Dedicated pharma lane."),
    CaretakerCreate(company="Air India Ground DEL",    type="Ground Handler",    node_id=3,  country="IN", contact_name="Rajesh Kumar",    contact_phone="+91 11 2345 6789", contact_email="cargo@aiground-del.in",   available="Daily 05:00–23:00",   rating=3.7, responsibilities=["Export acceptance","Documentation","Cool chain handoff","Temp monitoring"],            certs=["IATA","GDP"],              notes="Coordinate at least 4h before flight cutoff."),
    CaretakerCreate(company="Frankfurt Cargo GmbH",    type="Warehouse Keeper",  node_id=5,  country="DE", contact_name="Klaus Weber",     contact_phone="+49 69 6900 1234", contact_email="ops@fcs-fra.de",          available="Mon–Fri 07:00–20:00", rating=4.0, responsibilities=["Bonded warehouse","Customs liaison","Repackaging","Quality check"],                   certs=["GDP","ISO 9001","AEO"],    notes="Bonded storage."),
    CaretakerCreate(company="DHL Express BOM",         type="Ground Handler",    node_id=10, country="IN", contact_name="Priya Nair",      contact_phone="+91 22 6789 0123", contact_email="cargo.bom@dhl.com",       available="24/7",                rating=4.2, responsibilities=["Acceptance","Segregation","Cool room management","Export acceptance"],               certs=["IATA","GDP"],              notes="Dedicated pharma bay — Zone C."),
    CaretakerCreate(company="Changi Cargo Terminal",   type="Terminal Operator", node_id=8,  country="SG", contact_name="Wei Liang",       contact_phone="+65 6541 2345",   contact_email="ops@changi-cargo.sg",      available="24/7",                rating=4.8, responsibilities=["Transit storage","Cool chain","Customs coordination","Documentation"],                 certs=["IATA","GDP","ISO 9001"],   notes="World-class cold chain."),
    CaretakerCreate(company="Emirates SkyCargo Ground",type="Ground Handler",    node_id=7,  country="AE", contact_name="Ahmed Al Rashid", contact_phone="+971 4 220 3456", contact_email="cargo@esc-dxb.ae",         available="24/7",                rating=4.5, responsibilities=["Unloading","Temp monitoring","Transit handling","Build-up / breakdown"],               certs=["IATA","GDP","IATA CASS"], notes="Hub for ME redistribution."),
    CaretakerCreate(company="McKesson Site Logistics", type="Warehouse Keeper",  node_id=11, country="US", contact_name="Sarah Johnson",   contact_phone="+1 312 555 0192", contact_email="logistics@mckesson-chi.com",available="Mon–Fri 06:00–18:00",rating=4.7, responsibilities=["Receiving","Quality check","Storage","Repackaging"],                                 certs=["GDP","C-TPAT","ISO 9001"],notes="GMP-compliant cold storage."),
    CaretakerCreate(company="Antwerp Cold Logistics",  type="Cold Store",        node_id=6,  country="BE", contact_name="Stef Mertens",    contact_phone="+32 3 456 7890",  contact_email="coldops@acl-antwerp.be",   available="24/7",                rating=4.3, responsibilities=["Reefer monitoring","Storage","Temperature logging","Segregation"],                   certs=["GDP","HACCP","ISO 9001"], notes="Specialist cold store adjacent to North Quay."),
    CaretakerCreate(company="IGS Customs Antwerp",     type="Customs Agent",     node_id=6,  country="BE", contact_name="Katrien Smits",   contact_phone="+32 3 567 8901",  contact_email="customs@igs-antwerp.be",   available="Mon–Fri 08:00–18:00", rating=4.0, responsibilities=["Customs liaison","Documentation","Import / export clearance","Gate control"],         certs=["AEO"],                     notes="AEO-certified."),
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")

    async with AsyncSessionLocal() as db:
        # check if already seeded
        existing = await db.scalar(select(func.count()).where(Node.is_active == True))
        if existing > 0:
            print(f"Database already has {existing} nodes — skipping seed.")
            return

        print("Seeding nodes...")
        for n in NODES:
            await create_node(db, n)

        print("Seeding carriers...")
        for c in CARRIERS:
            await create_carrier(db, c)

        print("Seeding caretakers...")
        for ct in CARETAKERS:
            await create_caretaker(db, ct)

        print("Done.")


if __name__ == "__main__":
    asyncio.run(seed())