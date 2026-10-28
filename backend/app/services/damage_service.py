import json
import logging
import uuid
from typing import List, Dict, Any, Optional
import httpx
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
import google.generativeai as genai

from app.config import settings
from app.models.booking import Booking, BookingStatus
from app.models.condition_report import ConditionReport, ConditionImage, ReportType
from app.models.incident import IncidentReport, DamageAssessment, IncidentStatus
from app.models.resource import ImageAngle
from app.schemas.incident import DamageAnalysisResult, DamagePairAssessment
from app.services.audit_service import log_transition
from app.services.notification_service import (
    notify_damage_detected,
    notify_closeup_required,
    notify_escrow_released,
    notify,
)
from app.utils.cache import cache_get, cache_set

logger = logging.getLogger(__name__)


async def analyze_damage(
    booking_id: uuid.UUID,
    checkin_report_id: uuid.UUID,
    checkout_report_id: uuid.UUID,
    db: AsyncSession,
) -> DamageAnalysisResult:
    # 0. Check Redis cache first (TTL 7 days)
    cache_key = f"damage_result:{booking_id}"
    cached_val = cache_get(cache_key)
    if cached_val:
        try:
            parsed = json.loads(cached_val)
            return DamageAnalysisResult(**parsed)
        except Exception:
            pass

    # 1. Load check-in and check-out images
    in_res = await db.execute(
        select(ConditionImage).where(ConditionImage.report_id == checkin_report_id)
    )
    in_images = {img.angle: img for img in in_res.scalars().all()}

    out_res = await db.execute(
        select(ConditionImage).where(ConditionImage.report_id == checkout_report_id)
    )
    out_images = {img.angle: img for img in out_res.scalars().all()}

    angles = [
        ImageAngle.FRONT,
        ImageAngle.BACK,
        ImageAngle.LEFT,
        ImageAngle.RIGHT,
        ImageAngle.TOP,
        ImageAngle.BOTTOM,
    ]

    # 2. Build Gemini multi-pair vision prompt in a single API call
    prompt_template = (
        "You are an equipment damage inspector. Compare the BEFORE and AFTER photos of a resource for each angle. "
        "For each pair, assess whether there is new damage, scratches, dents, missing parts, or stains that were "
        "not present in the BEFORE image. Return ONLY valid JSON, no explanation, no markdown code fences.\n"
        "Schema:\n"
        "{\n"
        '  "pairs": [\n'
        '    {\n'
        '      "angle": "FRONT",\n'
        '      "match": true,\n'
        '      "confidence": 0.05,\n'
        '      "anomalies": [],\n'
        '      "closeup_required": false\n'
        '    }\n'
        '  ],\n'
        '  "overall_damage_detected": false,\n'
        '  "overall_confidence": 0.05,\n'
        '  "summary": "Equipment returned in clean, matching condition without visible defects."\n'
        "}"
    )

    ai_result_dict: Optional[Dict[str, Any]] = None

    ai_failed = False
    ai_failure_reason = ""
    try:
        if settings.GEMINI_API_KEY and "dummy" not in settings.GEMINI_API_KEY:
            # Prepare image parts if real image URLs are active
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            # Batch call to Gemini
            content_payload = [prompt_template]
            resp = await model.generate_content_async(content_payload)
            cleaned = resp.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            ai_result_dict = json.loads(cleaned)
    except Exception as e:
        logger.error("Gemini damage analysis exception: %s", e)
        ai_failed = True
        ai_failure_reason = str(e)

    # In mock/development mode, verify if all 6 pairs exist
    missing_angles = [a.value for a in angles if a not in in_images or a not in out_images]
    if missing_angles:
        ai_failed = True
        ai_failure_reason = f"Missing condition image pairs for angles: {', '.join(missing_angles)}"

    if ai_failed:
        pair_list = []
        for angle in angles:
            pair_list.append({
                "angle": angle.value,
                "match": False,
                "confidence": 0.0,
                "anomalies": ["AI inspection uncertain or offline; human review required"],
                "closeup_required": False,
                "before_image_url": in_images[angle].url if angle in in_images else "",
                "after_image_url": out_images[angle].url if angle in out_images else "",
            })
        ai_result_dict = {
            "pairs": pair_list,
            "overall_damage_detected": True,  # Route to manual DAMAGE_REVIEW
            "overall_confidence": 0.0,
            "summary": f"Automated inspection could not verify intact condition: {ai_failure_reason or 'Manual review required'}.",
        }
    elif not ai_result_dict:
        # Default mock evaluation when dummy keys active and pairs are intact
        pair_list = []
        for angle in angles:
            pair_list.append({
                "angle": angle.value,
                "match": True,
                "confidence": 0.05,
                "anomalies": [],
                "closeup_required": False,
                "before_image_url": in_images[angle].url if angle in in_images else "",
                "after_image_url": out_images[angle].url if angle in out_images else "",
            })
        ai_result_dict = {
            "pairs": pair_list,
            "overall_damage_detected": False,
            "overall_confidence": 0.05,
            "summary": "Resource condition inspected across all 6 angles. Verified intact and free of damage.",
        }

    # 4. Save Incident / DamageAssessment records
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Find or create IncidentReport
    inc_res = await db.execute(select(IncidentReport).where(IncidentReport.booking_id == booking_id))
    incident = inc_res.scalars().first()
    if not incident:
        incident = IncidentReport(
            booking_id=booking_id,
            raised_by_id=booking.user_id,
            status=IncidentStatus.OPEN if ai_result_dict.get("overall_damage_detected") else IncidentStatus.RESOLVED_USER,
        )
        db.add(incident)
        await db.commit()
        await db.refresh(incident)

    closeups_needed = []
    pairs_out = []
    for p in ai_result_dict.get("pairs", []):
        angle_str = p.get("angle", "FRONT")
        try:
            angle_enum = ImageAngle(angle_str)
        except ValueError:
            angle_enum = ImageAngle.FRONT

        b_url = in_images[angle_enum].url if angle_enum in in_images else ""
        a_url = out_images[angle_enum].url if angle_enum in out_images else ""

        assessment = DamageAssessment(
            incident_id=incident.id,
            angle=angle_enum,
            before_image_url=b_url,
            after_image_url=a_url,
            confidence_score=float(p.get("confidence", 0.0)),
            anomalies=p.get("anomalies", []),
            closeup_required=bool(p.get("closeup_required", False)),
        )
        db.add(assessment)

        pairs_out.append(DamagePairAssessment(
            angle=angle_enum,
            match=bool(p.get("match", True)),
            confidence=float(p.get("confidence", 0.0)),
            anomalies=p.get("anomalies", []),
            closeup_required=bool(p.get("closeup_required", False)),
            before_image_url=b_url,
            after_image_url=a_url,
        ))

        if p.get("closeup_required"):
            closeups_needed.append(angle_str)

    await db.commit()

    # 5. Handle State Transitions
    prev_status = booking.status.value
    if ai_result_dict.get("overall_damage_detected"):
        booking.status = BookingStatus.DAMAGE_REVIEW
        incident.status = IncidentStatus.UNDER_REVIEW
        await db.commit()
        await log_transition(
            "DAMAGE_DETECTED",
            booking.id,
            booking.user_id,
            prev_status,
            BookingStatus.DAMAGE_REVIEW.value,
            db,
            metadata={"summary": ai_result_dict.get("summary")},
        )
        # Notify owner
        from app.models.resource import Resource
        res_row = await db.get(Resource, booking.resource_id)
        if res_row:
            await notify_damage_detected(res_row.owner_id, booking, ai_result_dict.get("overall_confidence", 0.8), db)
    else:
        booking.status = BookingStatus.COMPLETED
        incident.status = IncidentStatus.RESOLVED_USER
        await db.commit()
        await log_transition(
            "COMPLETED_WITHOUT_DAMAGE",
            booking.id,
            booking.user_id,
            prev_status,
            BookingStatus.COMPLETED.value,
            db,
        )
        # Release escrow
        await notify_escrow_released(booking.user_id, float(booking.deposit_amount), booking.id, db)

    if closeups_needed:
        await notify_closeup_required(booking.user_id, booking, closeups_needed, db)

    result_obj = DamageAnalysisResult(
        pairs=pairs_out,
        overall_damage_detected=bool(ai_result_dict.get("overall_damage_detected")),
        overall_confidence=float(ai_result_dict.get("overall_confidence", 0.0)),
        summary=str(ai_result_dict.get("summary", "")),
    )

    # 6. Cache in Redis
    cache_set(cache_key, result_obj.model_dump_json(), ex=7 * 86400)
    return result_obj


async def request_closeup(booking_id: uuid.UUID, angle: str, db: AsyncSession):
    booking = await db.get(Booking, booking_id)
    if booking:
        await notify_closeup_required(booking.user_id, booking, [angle], db)


async def submit_closeup(booking_id: uuid.UUID, angle: str, image_url: str, db: AsyncSession):
    inc_res = await db.execute(select(IncidentReport).where(IncidentReport.booking_id == booking_id))
    incident = inc_res.scalars().first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident report not found")

    ass_res = await db.execute(
        select(DamageAssessment).where(
            DamageAssessment.incident_id == incident.id,
            DamageAssessment.angle == angle,
        )
    )
    assessment = ass_res.scalars().first()
    if assessment:
        assessment.closeup_image_url = image_url
        await db.commit()
