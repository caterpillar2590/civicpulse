"""Idempotent seed loader. Run twice, get the same 30 rows, not 60.

Idempotency strategy: each seed complaint gets a deterministic UUID5 derived
from its text, so `session.merge()` upserts rather than duplicates.
"""
from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import SessionLocal  # noqa: E402
from app.models.complaint import Complaint  # noqa: E402
from app.models.schemas import Category, Priority, Status  # noqa: E402

SEED_NAMESPACE = uuid.UUID("6f6a1f2e-4b1a-4e2a-9c3e-111111111111")

COMPLAINTS = [
    ("Burst water main flooding Street 12 since fajr, water entering ground floors", "Street 12, Sector G-9", Category.water, Priority.high),
    ("WAPDA transformer sparking near the mosque, bohat khatarnak lag raha hai", "Chowk Yadgar, Sector F-7", Category.electricity, Priority.high),
    ("Sewage line overflow outside house number 45, boo bohat zyada hai", "House 45, Street 3, G-10", Category.sanitation, Priority.high),
    ("Bara pothole bann gaya hai on the main road, do gaariyan already crash hui hain", "Main Boulevard, F-8", Category.roads, Priority.high),
    ("Streetlight band hai past three weeks, bohat andhera hota hai raat ko", "Street 9, G-11", Category.streetlights, Priority.normal),
    ("Garbage collection nahi hua is hafte, trash overflowing from the bins", "Sector I-8 Markaz", Category.sanitation, Priority.normal),
    ("Water supply bohat kam pressure se aa raha hai subah subah", "Street 22, F-10", Category.water, Priority.normal),
    ("Electric wire latak rahi hai near the park, bachay khelte hain wahan", "Park Road, G-6", Category.electricity, Priority.high),
    ("Footpath tootaa hua hai outside the school, walking is dangerous for kids", "School Road, F-11", Category.roads, Priority.normal),
    ("Streetlight pole tilted after the storm, may gir jaye", "Street 5, I-9", Category.streetlights, Priority.high),
    ("Drain block ho gaya hai, paani sarak par khara ho raha hai", "Sector G-8, Street 14", Category.sanitation, Priority.normal),
    ("Power outage since yesterday evening, transformer shayad phat gaya", "Sector F-6/2", Category.electricity, Priority.high),
    ("Road construction leftover debris blocking half the street for a month", "Service Road, G-7", Category.roads, Priority.low),
    ("Water tanker mafia charging extra, official supply line ka connection tootaa hua hai", "Sector I-10", Category.water, Priority.normal),
    ("Community park ka streetlight kaam nahi karta, security issue for evening walkers", "Park F-9", Category.streetlights, Priority.normal),
    ("Trash burning smell every evening near the corner shop, health issue", "Corner Market, G-9/1", Category.sanitation, Priority.normal),
    ("Manhole cover missing on the main road, bohat khatarnak hai for motorcyclists", "Main Road, F-7/3", Category.roads, Priority.high),
    ("Voltage fluctuation is damaging appliances, please check the local transformer", "Street 18, I-8", Category.electricity, Priority.normal),
    ("Water leaking from an underground pipe, sarak dheeli ho rahi hai", "Street 2, G-10/4", Category.water, Priority.normal),
    ("Streetlights sab band hain is poori gali mein for over a month", "Gali 6, F-10/2", Category.streetlights, Priority.normal),
    ("Sewer smell unbearable near the market entrance, customers complaining", "Market Entrance, I-9", Category.sanitation, Priority.high),
    ("Speed breaker needed urgently, bachay road cross karte hain school ke saamne", "School Crossing, G-11/1", Category.roads, Priority.normal),
    ("Exposed electric cable hanging low, touching hai delivery trucks ko", "Truck Route, F-8/5", Category.electricity, Priority.high),
    ("No water supply for three days now, tanker bhi nahi aaya", "Sector G-6, Street 9", Category.water, Priority.high),
    ("Broken streetlight causing accidents at the turn, please fix on priority", "Turn near Masjid, I-10/2", Category.streetlights, Priority.high),
    ("Garbage bin overflowing for two weeks, stray dogs spreading it around", "Sector F-9/3", Category.sanitation, Priority.low),
    ("Crack in the road widening after rain, ambulance route se guzarta hai yeh", "Ambulance Route, G-8", Category.roads, Priority.high),
    ("Low voltage complaint, fridge aur AC theek se chal nahi rahe", "Street 27, F-11/1", Category.electricity, Priority.low),
    ("Water quality looks murky today, thora sa smell bhi aa raha hai", "Street 4, I-8/2", Category.water, Priority.normal),
    ("New streetlight request for the newly built street, abhi koi light nahi hai", "New Street, G-12", Category.streetlights, Priority.low),
    ("Illegal dumping near the canal bank, sanitation team ko inform karein please", "Canal Bank, F-6", Category.sanitation, Priority.normal),
]


async def seed() -> None:
    async with SessionLocal() as session:
        for text, location, category, priority in COMPLAINTS:
            complaint_id = uuid.uuid5(SEED_NAMESPACE, text)
            complaint = Complaint(
                id=complaint_id,
                text=text,
                location=location,
                reporter_contact=None,
                category=category,
                priority=priority,
                status=Status.open,
                ai_summary=text[:137] + ("..." if len(text) > 137 else ""),
                triaged_by="rules:seed",
                triage_latency_ms=0,
            )
            await session.merge(complaint)  # upsert by primary key -> idempotent
        await session.commit()
        print(f"Seeded {len(COMPLAINTS)} complaints (idempotent).")


if __name__ == "__main__":
    asyncio.run(seed())
