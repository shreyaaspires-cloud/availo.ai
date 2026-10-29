import json
import logging
import uuid
import os
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import httpx
from PIL import Image
import io
import cv2
import numpy as np

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
from app.storage.supabase_storage import upload_file
from app.utils.cache import cache_get, cache_set

logger = logging.getLogger(__name__)

# Configure Gemini API if valid key is set
if settings.GEMINI_API_KEY and "dummy" not in settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("AQ."):
    genai.configure(api_key=settings.GEMINI_API_KEY)


def calculate_perceptual_similarity(img1_bytes: bytes, img2_bytes: bytes) -> float:
    """
    Computes a deterministic visual similarity score (0.0 to 1.0) using 
    normalized grayscale pixel difference (L1 norm).
    Documented Limitation: Sensitive to lighting, shadows, and camera-position alignment.
    """
    try:
        im1 = Image.open(io.BytesIO(img1_bytes)).convert("L").resize((128, 128))
        im2 = Image.open(io.BytesIO(img2_bytes)).convert("L").resize((128, 128))
        p1 = list(im1.getdata())
        p2 = list(im2.getdata())
        diff = sum(abs(a - b) for a, b in zip(p1, p2)) / (128 * 128 * 255.0)
        return round(max(0.0, min(1.0, 1.0 - diff)), 3)
    except Exception as e:
        logger.warning("Perceptual similarity calculation error: %s", e)
        return 0.5


def generate_cv_difference_visualization(
    img1_bytes: bytes, img2_bytes: bytes
) -> Optional[Tuple[bytes, List[Dict[str, Any]]]]:
    """
    Generates a genuine computer-vision difference heatmap and extracts bounding boxes
    of significant visual change clusters.
    Documented Limitation: Serves as an explainable visual aid, not definitive proof of damage.
    """
    try:
        # Decode images into OpenCV BGR numpy arrays
        nparr1 = np.frombuffer(img1_bytes, np.uint8)
        nparr2 = np.frombuffer(img2_bytes, np.uint8)
        cv1 = cv2.imdecode(nparr1, cv2.IMREAD_COLOR)
        cv2_img = cv2.imdecode(nparr2, cv2.IMREAD_COLOR)

        if cv1 is None or cv2_img is None:
            return None

        # Resize before image to match after image dimensions
        h, w = cv2_img.shape[:2]
        cv1_resized = cv2.resize(cv1, (w, h), interpolation=cv2.INTER_AREA)

        # Convert to grayscale
        gray1 = cv2.cvtColor(cv1_resized, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)

        # Apply mild Gaussian blur to suppress camera noise
        blur1 = cv2.GaussianBlur(gray1, (5, 5), 0)
        blur2 = cv2.GaussianBlur(gray2, (5, 5), 0)

        # Compute absolute difference
        abs_diff = cv2.absdiff(blur1, blur2)

        # Threshold to identify significant regions
        _, thresh = cv2.threshold(abs_diff, 45, 255, cv2.THRESH_BINARY)

        # Morphological open to remove specks
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        # Find contours of changed areas
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        bounding_boxes = []
        min_area = (w * h) * 0.005  # minimum 0.5% of image area to exclude minor sensor noise

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= min_area:
                bx, by, bw, bh = cv2.boundingRect(cnt)
                bounding_boxes.append({
                    "x": int(bx),
                    "y": int(by),
                    "width": int(bw),
                    "height": int(bh),
                    "area_pct": round((area / (w * h)) * 100, 2),
                    "label": "Suspected Change Region",
                })
                # Draw bounding box on after image
                cv2.rectangle(cv2_img, (bx, by), (bx + bw, by + bh), (0, 0, 255), 2)
                cv2.putText(
                    cv2_img,
                    "SUSPECTED CHANGE",
                    (bx, max(15, by - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 255),
                    2,
                )

        # Color map the difference
        heatmap = cv2.applyColorMap(abs_diff, cv2.COLORMAP_JET)
        # Alpha blend overlay: 70% return image + 30% heatmap
        diff_overlay = cv2.addWeighted(cv2_img, 0.70, heatmap, 0.30, 0)

        # Add visual aid disclaimer banner on the image
        cv2.putText(
            diff_overlay,
            "XAI DIFFERENCE VISUALIZATION (VISUAL AID ONLY)",
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
        )

        _, buf = cv2.imencode(".jpg", diff_overlay, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        return bytes(buf), bounding_boxes
    except Exception as e:
        logger.warning("Error generating CV difference visualization: %s", e)
        return None


async def load_image_bytes(url: str) -> Optional[bytes]:
    """Loads image bytes from local disk upload directory or HTTP URL."""
    try:
        if "storage/condition-photos/" in url or "condition-photos" in url:
            parts = url.split("condition-photos/")
            if len(parts) > 1:
                rel_path = parts[1].replace("/", os.sep)
                disk_path = os.path.join(os.getcwd(), "uploads", "condition-photos", rel_path)
                if os.path.exists(disk_path):
                    with open(disk_path, "rb") as f:
                        return f.read()

        if url.startswith("http"):
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    return res.content
    except Exception as e:
        logger.error("Error reading image bytes from %s: %s", url, e)
    return None


async def submit_closeup(booking_id: uuid.UUID, angle: str, image_url: str, db: AsyncSession):
    """Saves a close-up photo submitted for an angle flagged with damage."""
    result = await db.execute(
        select(IncidentReport)
        .options(selectinload(IncidentReport.assessments))
        .where(IncidentReport.booking_id == booking_id)
    )
    incident = result.scalars().first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident report not found")

    for assessment in incident.assessments:
        if assessment.angle.value == angle:
            assessment.closeup_image_url = image_url
            assessment.closeup_required = False
            await db.commit()
            return


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

    # Check for missing pairs
    missing_angles = [a.value for a in angles if a not in in_images or a not in out_images]

    ai_failed = False
    ai_failure_reason = ""
    ai_result_dict: Optional[Dict[str, Any]] = None

    if missing_angles:
        ai_failed = True
        ai_failure_reason = f"Missing condition image pairs for angles: {', '.join(missing_angles)}"

    # 2. Invoke Gemini Vision Model if valid API key is present
    has_valid_gemini = bool(
        settings.GEMINI_API_KEY
        and "dummy" not in settings.GEMINI_API_KEY
        and not settings.GEMINI_API_KEY.startswith("AQ.")
    )

    if not ai_failed and has_valid_gemini:
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model_name = settings.GEMINI_MODEL or "gemini-2.0-flash"
            model = genai.GenerativeModel(model_name)

            prompt = (
                "You are an expert Explainable AI (XAI) forensic damage inspector for high-value research equipment.\n"
                "Compare the check-in baseline photos with the return photos for the 6 canonical perspectives:\n"
                "FRONT, BACK, LEFT, RIGHT, TOP, and BOTTOM.\n"
                "For EACH perspective pair, provide an explainable forensic evaluation:\n"
                "1. comparison_status: 'comparable', 'partially_comparable' (e.g. lighting/angle shifts), or 'not_comparable' (e.g. occluded/wrong angle)\n"
                "2. match: boolean (true if identical/undamaged, false if visible anomalies or damage found)\n"
                "3. confidence: float between 0.0 (certainly unchanged) and 1.0 (certainly damaged/different)\n"
                "4. observed_differences: list of specific visual differences observed in photos\n"
                "5. damage_category: one of 'scratch', 'crack', 'dent', 'deformation', 'missing_part', 'stain', 'surface_wear', or 'none'\n"
                "6. location_description: plain language description of WHERE the suspected change is located (e.g. 'top-right corner of casing')\n"
                "7. supporting_evidence: visual proof from the image explaining WHY damage is suspected\n"
                "8. alternative_explanations: list of plausible alternative reasons, such as ['lighting variation', 'specular glare', 'camera angle difference', 'shadowing', 'blur']\n"
                "9. human_review_required: boolean (true if ambiguous, lighting differences, or damage suspected)\n"
                "10. closeup_required: boolean (true if higher-resolution macro photo is recommended)\n\n"
                "Return strictly valid JSON in this structure:\n"
                "{\n"
                '  "overall_damage_detected": boolean,\n'
                '  "overall_confidence": float (0.0 to 1.0),\n'
                '  "summary": string (plain language explanation for both owner and borrower),\n'
                '  "pairs": [\n'
                "    {\n"
                '      "angle": "FRONT",\n'
                '      "comparison_status": "comparable",\n'
                '      "match": true,\n'
                '      "confidence": 0.05,\n'
                '      "observed_differences": [],\n'
                '      "damage_category": "none",\n'
                '      "location_description": "Entire front surface inspected",\n'
                '      "supporting_evidence": "Surface matches baseline without scratches or fissures",\n'
                '      "alternative_explanations": [],\n'
                '      "human_review_required": false,\n'
                '      "closeup_required": false\n'
                "    }\n"
                "  ]\n"
                "}"
            )

            content_parts: List[Any] = [prompt]
            for angle in angles:
                in_img = in_images.get(angle)
                out_img = out_images.get(angle)
                content_parts.append(f"\n--- Perspective: {angle.value} ---")
                if in_img:
                    in_b = await load_image_bytes(in_img.url)
                    if in_b:
                        content_parts.append(f"Baseline Check-in Photo ({angle.value}):")
                        content_parts.append(Image.open(io.BytesIO(in_b)))
                if out_img:
                    out_b = await load_image_bytes(out_img.url)
                    if out_b:
                        content_parts.append(f"Return Inspection Photo ({angle.value}):")
                        content_parts.append(Image.open(io.BytesIO(out_b)))

            response = await model.generate_content_async(
                content_parts,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            ai_result_dict = json.loads(raw_text.strip())
        except Exception as e:
            logger.warning("Gemini AI API call failed or timed out: %s", e)
            ai_failed = True
            ai_failure_reason = f"Gemini API invocation error: {str(e)}"

    # 3. Fail-safe deterministic XAI fallback when Gemini is unavailable or missing
    if ai_failed or not ai_result_dict:
        logger.info("Executing Explainable AI (XAI) forensic assessment fallback")
        pair_list = []
        overall_damage = False

        for angle in angles:
            in_img = in_images.get(angle)
            out_img = out_images.get(angle)
            b_url = in_img.url if in_img else ""
            a_url = out_img.url if out_img else ""

            sim = 0.5
            diff_boxes = []
            diff_img_url = None
            observed_diffs = []
            alt_explanations = []
            category = "none"
            loc_desc = f"Canonical {angle.value} perspective"
            evidence = "No anomalies detected."
            status = "comparable"
            review_req = False

            if in_img and out_img:
                b_bytes = await load_image_bytes(b_url)
                a_bytes = await load_image_bytes(a_url)
                if b_bytes and a_bytes:
                    sim = calculate_perceptual_similarity(b_bytes, a_bytes)
                    cv_res = generate_cv_difference_visualization(b_bytes, a_bytes)
                    if cv_res:
                        diff_bytes, diff_boxes = cv_res
                        diff_path = f"condition/{booking_id}/diff/{angle.value}_xai_diff.jpg"
                        try:
                            diff_img_url = await upload_file(
                                diff_bytes, "condition-photos", diff_path, content_type="image/jpeg"
                            )
                        except Exception as e:
                            logger.warning("Failed uploading diff image: %s", e)

                    if sim < 0.85:
                        observed_diffs.append(f"Visual pixel discrepancy observed (L1 similarity: {sim * 100:.1f}%)")
                        alt_explanations.extend([
                            "Ambient illumination or studio lighting differences",
                            "Slight perspective angle alignment shift during camera positioning",
                            "Surface dust or transient glare reflection",
                        ])
                        loc_desc = f"Localized change detected across {angle.value} perspective"
                        evidence = f"L1 pixel divergence metric calculated at {(1 - sim) * 100:.1f}%. Difference heatmap generated."
                        category = "surface_wear" if sim > 0.70 else "scratch"
                        review_req = True
                    else:
                        evidence = f"High perceptual fidelity confirmed ({sim * 100:.1f}% match). No significant deviations."
                else:
                    status = "partially_comparable"
                    observed_diffs.append("Image binary inaccessible for deep pixel analysis.")
                    alt_explanations.append("Network storage fetch timeout")
                    review_req = True
            else:
                status = "not_comparable"
                observed_diffs.append(f"Missing {angle.value} photograph in submission.")
                review_req = True

            pair_anomaly = (sim < 0.85) or (status != "comparable")
            if pair_anomaly:
                overall_damage = True

            pair_list.append({
                "angle": angle.value,
                "match": not pair_anomaly,
                "confidence": round(1.0 - sim, 3),
                "anomalies": observed_diffs,
                "closeup_required": pair_anomaly and sim < 0.75,
                "before_image_url": b_url,
                "after_image_url": a_url,
                "comparison_status": status,
                "similarity_metric": sim,
                "similarity_algorithm": "Normalized Grayscale L1 Pixel Difference (PIL/OpenCV)",
                "observed_differences": observed_diffs,
                "damage_category": category if pair_anomaly else "none",
                "location_description": loc_desc,
                "supporting_evidence": evidence,
                "alternative_explanations": alt_explanations,
                "human_review_required": review_req,
                "difference_image_url": diff_img_url,
                "bounding_boxes": diff_boxes,
            })

        overall_conf = 0.85 if overall_damage else 0.95
        summary_text = (
            "Explainable AI comparison completed with perceptual difference modeling. Potential condition "
            "variations detected across one or more perspectives requiring human verification."
            if overall_damage
            else "Perceptual XAI comparison verified 6/6 canonical perspectives. No discernible damage detected."
        )
        if ai_failure_reason:
            summary_text += f" (Note: Gemini API deferred to CV engine: {ai_failure_reason})"

        ai_result_dict = {
            "overall_damage_detected": overall_damage,
            "overall_confidence": overall_conf,
            "summary": summary_text,
            "pairs": pair_list,
        }
    else:
        # Augment Gemini output with genuine computer-vision difference heatmaps and metrics
        pair_list = []
        for p in ai_result_dict.get("pairs", []):
            angle_str = p.get("angle", "FRONT")
            try:
                angle_enum = ImageAngle(angle_str)
            except ValueError:
                angle_enum = ImageAngle.FRONT

            in_img = in_images.get(angle_enum)
            out_img = out_images.get(angle_enum)
            b_url = in_img.url if in_img else ""
            a_url = out_img.url if out_img else ""

            sim = 0.9
            diff_img_url = None
            diff_boxes = []
            if in_img and out_img:
                b_bytes = await load_image_bytes(b_url)
                a_bytes = await load_image_bytes(a_url)
                if b_bytes and a_bytes:
                    sim = calculate_perceptual_similarity(b_bytes, a_bytes)
                    cv_res = generate_cv_difference_visualization(b_bytes, a_bytes)
                    if cv_res:
                        diff_bytes, diff_boxes = cv_res
                        diff_path = f"condition/{booking_id}/diff/{angle_enum.value}_xai_diff.jpg"
                        try:
                            diff_img_url = await upload_file(
                                diff_bytes, "condition-photos", diff_path, content_type="image/jpeg"
                            )
                        except Exception as e:
                            logger.warning("Failed uploading diff image: %s", e)

            pair_list.append({
                "angle": angle_str,
                "match": p.get("match", True),
                "confidence": p.get("confidence", 0.0),
                "anomalies": p.get("observed_differences", p.get("anomalies", [])),
                "closeup_required": p.get("closeup_required", False),
                "before_image_url": b_url,
                "after_image_url": a_url,
                "comparison_status": p.get("comparison_status", "comparable"),
                "similarity_metric": sim,
                "similarity_algorithm": "Normalized Grayscale L1 Pixel Difference (PIL/OpenCV)",
                "observed_differences": p.get("observed_differences", []),
                "damage_category": p.get("damage_category", "none"),
                "location_description": p.get("location_description", f"{angle_str} perspective view"),
                "supporting_evidence": p.get("supporting_evidence", "Analyzed by multimodal model"),
                "alternative_explanations": p.get("alternative_explanations", []),
                "human_review_required": p.get("human_review_required", not p.get("match", True)),
                "difference_image_url": diff_img_url,
                "bounding_boxes": diff_boxes,
            })
        ai_result_dict["pairs"] = pair_list

    # 4. Save Incident / DamageAssessment records
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

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

        assessment = DamageAssessment(
            incident_id=incident.id,
            angle=angle_enum,
            before_image_url=p.get("before_image_url", ""),
            after_image_url=p.get("after_image_url", ""),
            confidence_score=float(p.get("confidence", 0.0)),
            anomalies=p.get("anomalies", []),
            closeup_required=bool(p.get("closeup_required", False)),
            comparison_status=p.get("comparison_status", "comparable"),
            similarity_metric=float(p.get("similarity_metric", 1.0)),
            similarity_algorithm=p.get("similarity_algorithm", "Normalized Grayscale L1 Pixel Difference"),
            observed_differences=p.get("observed_differences", []),
            damage_category=p.get("damage_category", "none"),
            location_description=p.get("location_description", ""),
            supporting_evidence=p.get("supporting_evidence", ""),
            alternative_explanations=p.get("alternative_explanations", []),
            human_review_required=bool(p.get("human_review_required", False)),
            difference_image_url=p.get("difference_image_url"),
            bounding_boxes=p.get("bounding_boxes", []),
        )
        db.add(assessment)

        pairs_out.append(DamagePairAssessment(
            angle=angle_enum,
            match=bool(p.get("match", True)),
            confidence=float(p.get("confidence", 0.0)),
            anomalies=p.get("anomalies", []),
            closeup_required=bool(p.get("closeup_required", False)),
            before_image_url=p.get("before_image_url", ""),
            after_image_url=p.get("after_image_url", ""),
            comparison_status=p.get("comparison_status", "comparable"),
            similarity_metric=float(p.get("similarity_metric", 1.0)),
            similarity_algorithm=p.get("similarity_algorithm", "Normalized Grayscale L1 Pixel Difference"),
            observed_differences=p.get("observed_differences", []),
            damage_category=p.get("damage_category"),
            location_description=p.get("location_description"),
            supporting_evidence=p.get("supporting_evidence"),
            alternative_explanations=p.get("alternative_explanations", []),
            human_review_required=bool(p.get("human_review_required", False)),
            difference_image_url=p.get("difference_image_url"),
            bounding_boxes=p.get("bounding_boxes", []),
        ))

        if p.get("closeup_required"):
            closeups_needed.append(angle_enum.value)

    # 5. Handle booking state transition & notifications
    prev_status = booking.status.value
    damage_detected = bool(ai_result_dict.get("overall_damage_detected", False))

    if damage_detected:
        booking.status = BookingStatus.DAMAGE_REVIEW
        incident.status = IncidentStatus.OPEN
        await db.commit()

        await log_transition(
            action="DAMAGE_DETECTED_OR_REVIEW_FLAGGED",
            booking_id=booking.id,
            user_id=None,
            previous_status=prev_status,
            new_status=BookingStatus.DAMAGE_REVIEW.value,
            db=db,
            metadata={"summary": ai_result_dict.get("summary")},
        )

        res_obj = await db.get(ConditionReport, checkin_report_id)
        owner_id = booking.user_id
        if res_obj:
            b_full = await db.execute(
                select(Booking).options(selectinload(Booking.resource)).where(Booking.id == booking_id)
            )
            b_inst = b_full.scalars().first()
            if b_inst and b_inst.resource:
                owner_id = b_inst.resource.owner_id

        await notify_damage_detected(
            user_id=booking.user_id,
            owner_id=owner_id,
            booking_id=booking.id,
            summary=ai_result_dict.get("summary", "Condition discrepancies flagged."),
            db=db,
        )

        if closeups_needed:
            await notify_closeup_required(
                user_id=booking.user_id,
                booking_id=booking.id,
                angles=closeups_needed,
                db=db,
            )
    else:
        booking.status = BookingStatus.COMPLETED
        incident.status = IncidentStatus.RESOLVED_USER
        await db.commit()

        await log_transition(
            action="DAMAGE_INSPECTION_PASSED",
            booking_id=booking.id,
            user_id=None,
            previous_status=prev_status,
            new_status=BookingStatus.COMPLETED.value,
            db=db,
            metadata={"summary": ai_result_dict.get("summary")},
        )

        await notify_escrow_released(
            user_id=booking.user_id,
            booking_id=booking.id,
            deposit_amount=booking.deposit_amount,
            db=db,
        )

    final_result = DamageAnalysisResult(
        pairs=pairs_out,
        overall_damage_detected=damage_detected,
        overall_confidence=float(ai_result_dict.get("overall_confidence", 0.0)),
        summary=ai_result_dict.get("summary", ""),
        model_version=f"{settings.GEMINI_MODEL} + OpenCV XAI Difference Engine",
    )

    # Cache result
    try:
        cache_set(cache_key, json.dumps(final_result.model_dump(), default=str), ex=settings.GEMINI_CACHE_TTL)
    except Exception:
        pass

    return final_result
