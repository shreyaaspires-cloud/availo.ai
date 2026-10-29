import io
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.models.booking import Booking
from app.models.resource import Resource
from app.models.user import User
from app.models.contract import Contract
from app.models.incident import IncidentReport, DamageClaim


def generate_closure_receipt_pdf_bytes(
    booking: Booking,
    resource: Resource,
    borrower: User,
    owner: User,
    contract: Optional[Contract] = None,
    incident: Optional[IncidentReport] = None,
    claim: Optional[DamageClaim] = None,
) -> bytes:
    """
    Renders an official, immutable Availo Agreement Closure & Settlement PDF Receipt.
    Reflects genuine persisted database fields across booking, contract, condition decision,
    and escrow financial settlement.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'ReceiptTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold',
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        'ReceiptSubtitle',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=10,
    )
    h2_style = ParagraphStyle(
        'ReceiptH2',
        parent=styles['Heading2'],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1e40af'),
        fontName='Helvetica-Bold',
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        'ReceiptBody',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1e293b'),
    )
    badge_style = ParagraphStyle(
        'ReceiptBadge',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#047857'),
        fontName='Helvetica-Bold',
    )
    mono_style = ParagraphStyle(
        'ReceiptMono',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        fontName='Courier',
        textColor=colors.HexColor('#334155'),
    )

    elements = []

    # Header
    receipt_id = f"REC-AVAILO-{str(booking.id)[:8].upper()}"
    elements.append(Paragraph("AVAILO RESOURCE NETWORK — AGREEMENT CLOSURE RECEIPT", title_style))
    elements.append(Paragraph(
        f"Official Settlement Document · Receipt ID: {receipt_id} · Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        subtitle_style
    ))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563eb'), spaceAfter=12))

    # 1. Summary Box
    decision_text = "No Damage Reported — Normal Closure"
    if incident and incident.owner_decision:
        decision_val = incident.owner_decision.value if hasattr(incident.owner_decision, "value") else str(incident.owner_decision)
        if decision_val == "NO_DAMAGE_REPORTED":
            decision_text = "No Damage Reported (Confirmed by Resource Owner)"
        elif decision_val == "DAMAGE_REPORTED":
            decision_text = "Damage Reported & Mutual Resolution Finalized"

    summary_data = [
        [
            Paragraph("<b>Booking Status:</b>", body_style),
            Paragraph(f"<b>{booking.status.value if hasattr(booking.status, 'value') else str(booking.status)}</b>", badge_style),
            Paragraph("<b>Contract Status:</b>", body_style),
            Paragraph(f"{contract.status.value if contract and hasattr(contract.status, 'value') else 'CLOSED / COMPLETED'}", body_style),
        ],
        [
            Paragraph("<b>Closure Decision:</b>", body_style),
            Paragraph(decision_text, body_style),
            Paragraph("<b>Resolution Timestamp:</b>", body_style),
            Paragraph(
                incident.resolved_at.strftime('%Y-%m-%d %H:%M UTC')
                if incident and incident.resolved_at
                else datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
                body_style
            ),
        ]
    ]
    t_summary = Table(summary_data, colWidths=[110, 155, 120, 145])
    t_summary.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#10b981')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(t_summary)
    elements.append(Spacer(1, 10))

    # 2. Contracting Parties
    elements.append(Paragraph("1. CONTRACTING PARTIES", h2_style))
    parties_data = [
        [Paragraph("<b>BORROWER / RESEARCHER</b>", body_style), Paragraph("<b>EQUIPMENT OWNER</b>", body_style)],
        [
            Paragraph(
                f"<b>Name:</b> {borrower.full_name}<br/>"
                f"<b>Email:</b> {borrower.email}<br/>"
                f"<b>Account ID:</b> {str(borrower.id)[:8]}...<br/>"
                f"<b>Trust Score:</b> {borrower.trust_score}/100",
                body_style
            ),
            Paragraph(
                f"<b>Name:</b> {owner.full_name}<br/>"
                f"<b>Email:</b> {owner.email}<br/>"
                f"<b>Account ID:</b> {str(owner.id)[:8]}...<br/>"
                f"<b>Role:</b> Verified Platform Host",
                body_style
            )
        ]
    ]
    t_parties = Table(parties_data, colWidths=[265, 265])
    t_parties.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(t_parties)
    elements.append(Spacer(1, 10))

    # 3. Resource & Session Specifics
    elements.append(Paragraph("2. RESOURCE & RESERVATION TIMELINE", h2_style))
    details_data = [
        [Paragraph("<b>Resource Name:</b>", body_style), Paragraph(resource.title, body_style)],
        [Paragraph("<b>Resource Category / Loc:</b>", body_style), Paragraph(f"{resource.category} · {resource.location}", body_style)],
        [Paragraph("<b>Reservation Window:</b>", body_style), Paragraph(
            f"{booking.start_dt.strftime('%b %d, %Y %H:%M UTC')} to {booking.end_dt.strftime('%b %d, %Y %H:%M UTC')}",
            body_style
        )],
        [Paragraph("<b>Purpose of Use:</b>", body_style), Paragraph(booking.purpose or "Institutional research & laboratory experimentation", body_style)],
    ]
    t_details = Table(details_data, colWidths=[160, 370])
    t_details.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_details)
    elements.append(Spacer(1, 10))

    # 4. Financial & Escrow Settlement
    elements.append(Paragraph("3. FINANCIAL SETTLEMENT & ESCROW RECONCILIATION", h2_style))
    dep_amt = float(booking.deposit_amount or 0)
    rental_fee = float(booking.total_amount or 0)

    deduction = 0.0
    settlement_status = "ESCROW DEPOSIT RELEASED IN FULL TO BORROWER"
    payment_ref = booking.payment_reference or "ESCROW_SETTLED_SYSTEM"

    if claim and (claim.status.value if hasattr(claim.status, "value") else str(claim.status)) == "ACCEPTED":
        deduction = float(claim.agreed_compensation or claim.estimated_cost or 0)
        payment_ref = claim.payment_reference or payment_ref
        refund_amt = max(0.0, dep_amt - deduction)
        settlement_status = f"DAMAGE SETTLEMENT: ${deduction:,.2f} RETAINED FOR OWNER · ${refund_amt:,.2f} REFUNDED TO BORROWER"
    elif incident and incident.status == "RESOLVED_OWNER":
        settlement_status = "CLAIM RESOLVED IN FAVOR OF RESOURCE OWNER"

    fin_data = [
        [Paragraph("<b>Description</b>", body_style), Paragraph("<b>Amount (USD)</b>", body_style), Paragraph("<b>Status</b>", body_style)],
        [Paragraph("Total Rental Fee", body_style), Paragraph(f"${rental_fee:,.2f}", body_style), Paragraph("SETTLED", body_style)],
        [Paragraph("Escrow Security Deposit", body_style), Paragraph(f"${dep_amt:,.2f}", body_style), Paragraph("ESCROWED", body_style)],
        [Paragraph("Agreed Damage Compensation / Deduction", body_style), Paragraph(f"${deduction:,.2f}", body_style), Paragraph("DEDUCTED" if deduction > 0 else "NONE", body_style)],
        [
            Paragraph("<b>Final Net Deposit Refund to Borrower:</b>", body_style),
            Paragraph(f"<b>${max(0.0, dep_amt - deduction):,.2f}</b>", badge_style),
            Paragraph("<b>RELEASED</b>", badge_style)
        ],
    ]
    t_fin = Table(fin_data, colWidths=[240, 140, 150])
    t_fin.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_fin)
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(f"<b>Reconciliation Policy:</b> {settlement_status}", body_style))
    elements.append(Paragraph(f"<b>Transaction Reference:</b> {payment_ref}", mono_style))
    elements.append(Spacer(1, 10))

    # 5. Non-repudiation & Verification
    elements.append(Paragraph("4. AUDIT COMPLIANCE & LEGAL NOTICE", h2_style))
    audit_notes = (
        "This document certifies that the rental period has terminated, 6-angle before/after return inspection "
        "evidence has been processed through the Availo Visual Verification protocol, and the agreement has been "
        "formally closed in the platform ledger. Dual cryptographic signatures on the primary agreement remain immutable "
        "and archived under Availo tamper-proof verification standards."
    )
    elements.append(Paragraph(audit_notes, subtitle_style))
    if contract and contract.sha256_hash:
        elements.append(Paragraph(f"Underlying Agreement SHA-256 Digest: {contract.sha256_hash}", mono_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

