import os
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Literal, Optional

from fastapi import HTTPException
from fpdf import FPDF

try:
    # When running from within backend/ (e.g. `uvicorn main:app --reload`)
    from database import supabase as _supabase  # type: ignore
except ModuleNotFoundError:
    # When importing as a package (e.g. `uvicorn backend.main:app --reload`)
    from backend.database import supabase as _supabase  # type: ignore


TemplateKind = Literal["police", "internal", "verdict"]


def _require_supabase():
    if _supabase is None:
        raise HTTPException(
            status_code=500,
            detail="Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env",
        )
    return _supabase


def _bucket_name() -> str:
    # Dev 2 creates the bucket; keep this configurable.
    return os.getenv("SUPABASE_VERDICT_BUCKET") or "verdict-pdfs"


def _public_url(bucket: str, path: str) -> str:
    res = _require_supabase().storage.from_(bucket).get_public_url(path)
    # supabase-py returns either { "publicUrl": ... } or a plain string depending on version
    if isinstance(res, str):
        return res
    if isinstance(res, dict):
        return (
            res.get("publicUrl")
            or res.get("publicURL")
            or res.get("public_url")
            or res.get("publicUrl".lower())
            or ""
        )
    return ""


def fetch_dispute_bundle(dispute_id: str) -> Dict[str, Any]:
    """
    Fetch dispute row + related system logs used for evidence packs.
    """
    sb = _require_supabase()

    dispute_res = sb.table("disputes").select("*").eq("id", dispute_id).execute()
    if not dispute_res.data:
        raise HTTPException(status_code=404, detail="Dispute not found.")

    dispute = dispute_res.data[0]

    # system_logs payload stores dispute_id inside JSONB; select recent logs for context
    logs_res = (
        sb.table("system_logs")
        .select("id, created_at, event_name, visibility, payload")
        .eq("payload->>dispute_id", dispute_id)
        .order("created_at", desc=True)
        .limit(100)
        .execute()
    )

    return {"dispute": dispute, "system_logs": logs_res.data or []}


def _wrap(pdf: FPDF, text: str, max_w: float, line_h: float) -> None:
    for line in pdf.multi_cell(max_w, line_h, text, new_x="LMARGIN", new_y="NEXT", split_only=True):
        pdf.cell(0, line_h, line, ln=1)


def _header(pdf: FPDF, title: str, subtitle: str) -> None:
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, title, ln=1)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 6, subtitle, ln=1)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    pdf.set_draw_color(220, 220, 220)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)


def _kv(pdf: FPDF, k: str, v: str) -> None:
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(50, 6, k)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, v)


def _render_police_kit(pdf: FPDF, bundle: Dict[str, Any], summary: Dict[str, Any]) -> None:
    dispute = bundle["dispute"]
    logs = bundle["system_logs"]

    _header(
        pdf,
        "ResolveMesh Evidence Pack — Police Kit",
        f"Dispute {dispute.get('id')} · Generated {datetime.now(timezone.utc).isoformat()}",
    )

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Facts (timestamps, hashes, identifiers)", ln=1)
    pdf.set_font("Helvetica", "", 10)

    customer = dispute.get("customer_info") or {}
    _kv(pdf, "Order ID", str(customer.get("order_id", "N/A")))
    _kv(pdf, "Platform", str(customer.get("platform", "N/A")))
    _kv(pdf, "Amount", str(customer.get("amount", "N/A")))
    _kv(pdf, "Issue Type", str(customer.get("issue_type", "N/A")))
    _kv(pdf, "Status", str(dispute.get("status", "N/A")))
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Key Evidence (Supabase row citations)", ln=1)
    pdf.set_font("Helvetica", "", 10)
    for i, ev in enumerate(summary.get("evidence") or [], start=1):
        sb = (ev or {}).get("supabase") or {}
        ident = (ev or {}).get("hash") or (ev or {}).get("transaction_id") or ""
        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(
            0,
            6,
            f"{i}. {ident} — {sb.get('table')}:{sb.get('row_id')} {sb.get('json_path') or ''}".strip(),
        )
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, str((ev or {}).get("details") or ""))
        pdf.ln(1)

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Relevant System Logs (latest 10)", ln=1)
    pdf.set_font("Helvetica", "", 9)
    for row in (logs or [])[:10]:
        pdf.multi_cell(
            0,
            5,
            f"- {row.get('created_at')} · {row.get('event_name')} · log_id={row.get('id')}",
        )


def _render_internal_brief(pdf: FPDF, bundle: Dict[str, Any], summary: Dict[str, Any]) -> None:
    dispute = bundle["dispute"]
    _header(
        pdf,
        "ResolveMesh Evidence Pack — Internal Brief",
        f"Dispute {dispute.get('id')} · Generated {datetime.now(timezone.utc).isoformat()}",
    )

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Staff TL;DR (≤30 words)", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, str(summary.get("summary_tldr") or ""))
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Reasoning", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, str(summary.get("reasoning") or ""))
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Confidence", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, f"{summary.get('confidence_score', 'N/A')} / 100")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Evidence (explicit Supabase rows)", ln=1)
    pdf.set_font("Helvetica", "", 10)
    for i, ev in enumerate(summary.get("evidence") or [], start=1):
        sb = (ev or {}).get("supabase") or {}
        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(0, 6, f"{i}. {sb.get('table')}:{sb.get('row_id')} {sb.get('json_path') or ''}".strip())
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, str((ev or {}).get("details") or ""))
        pdf.ln(1)


def _render_final_verdict(pdf: FPDF, bundle: Dict[str, Any], summary: Dict[str, Any]) -> None:
    dispute = bundle["dispute"]
    customer = dispute.get("customer_info") or {}
    _header(
        pdf,
        "ResolveMesh — Final Resolution Letter",
        f"Reference: {dispute.get('id')} · Date: {datetime.now(timezone.utc).date().isoformat()}",
    )

    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(
        0,
        6,
        "Dear Customer,\n\n"
        "We have completed our review of your dispute. This determination is based on the system records and audit logs "
        "available at the time of investigation, including time-stamped ledger events and transaction hashes.\n",
    )

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Case Details", ln=1)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(
        0,
        6,
        f"- Order ID: {customer.get('order_id', 'N/A')}\n"
        f"- Platform: {customer.get('platform', 'N/A')}\n"
        f"- Issue Type: {customer.get('issue_type', 'N/A')}\n",
    )

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Decision and Basis", ln=1)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, str(summary.get("reasoning") or ""))

    pdf.ln(2)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 90, 90)
    pdf.multi_cell(
        0,
        5,
        "Evidence references (Supabase row citations) are available internally and can be provided to relevant authorities upon request.",
    )
    pdf.set_text_color(0, 0, 0)

    pdf.ln(6)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(
        0,
        6,
        "Sincerely,\nResolveMesh Disputes Operations",
    )


def build_pdf_bytes(template: TemplateKind, bundle: Dict[str, Any], summary: Dict[str, Any]) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    if template == "police":
        _render_police_kit(pdf, bundle, summary)
    elif template == "internal":
        _render_internal_brief(pdf, bundle, summary)
    elif template == "verdict":
        _render_final_verdict(pdf, bundle, summary)
    else:
        raise HTTPException(status_code=400, detail="Unknown template.")

    out = BytesIO()
    pdf.output(out)
    return out.getvalue()


def upload_pdf(dispute_id: str, template: TemplateKind, pdf_bytes: bytes) -> str:
    bucket = _bucket_name()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = f"{dispute_id}/{template}-{ts}.pdf"

    _require_supabase().storage.from_(bucket).upload(
        path=path,
        file=pdf_bytes,
        file_options={"content-type": "application/pdf", "upsert": "true"},
    )

    url = _public_url(bucket, path)
    if not url:
        # Still return the storage path so n8n can request a signed URL later if needed.
        raise HTTPException(
            status_code=500,
            detail=f"PDF uploaded to {bucket}:{path} but could not resolve public URL (bucket may be private).",
        )
    return url
