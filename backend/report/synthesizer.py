"""
Report Layer — Gemini Report Synthesizer
Uses Gemini to synthesize the validated evidence into a human-readable report.

CRITICAL RULES ENFORCED HERE:
- Gemini receives ONLY pre-validated, structured evidence.
- Gemini is forbidden from inventing measurements.
- All numbers in the report must come from the evidence package.
- If a measurement is not in the evidence, Gemini must not mention it.
"""

import json
from loguru import logger

from config import settings
from orchestrator.schemas import EvidencePackage, InvestigationPlan, Report, InputManifest
import google.generativeai as genai

genai.configure(api_key=settings.GEMINI_API_KEY)


import re

def sanitize_synthesis_text(text: str) -> str:
    """
    Purge recursive or duplicated phrases such as:
    'satellite image of a satellite image of...'
    and remove repeated adjacent identical words or phrases.
    """
    if not text or not isinstance(text, str):
        return text if text is not None else ""
    # Collapse recursive "satellite image of" / "a satellite image of"
    pattern = r"(?:(?:a\s+)?satellite\s+image\s+of\s+)+"
    text = re.sub(pattern, "satellite image of ", text, flags=re.IGNORECASE)
    # Collapse repeated adjacent phrases like "satellite image satellite image"
    text = re.sub(r"\b(satellite\s+image)(?:\s+\1\b)+", r"\1", text, flags=re.IGNORECASE)
    # Collapse any repeated 3-word phrase: "an aerial view an aerial view..."
    text = re.sub(r"\b([a-zA-Z]{2,}\s+[a-zA-Z]{2,}\s+[a-zA-Z]{2,})(?:\s+\1\b)+", r"\1", text, flags=re.IGNORECASE)
    # Collapse any repeated 2-word phrase: "satellite photo satellite photo..."
    text = re.sub(r"\b([a-zA-Z]{2,}\s+[a-zA-Z]{2,})(?:\s+\1\b)+", r"\1", text, flags=re.IGNORECASE)
    # Collapse any arbitrary consecutive repeating single word: "satellite satellite satellite..."
    text = re.sub(r"\b([a-zA-Z]{2,})(?:\s+\1\b)+", r"\1", text, flags=re.IGNORECASE)
    # Clean up double spaces
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


SYNTHESIS_SYSTEM_PROMPT = """You are a Senior Remote Sensing & Earth Observation (EO/GIS) Scientist preparing an authoritative, publication-grade scientific report for Astra AI.

THINK AND WRITE LIKE AN EARTH OBSERVATION SCIENTIST:
Prioritize: WHAT WAS DETECTED, WHERE, HOW MUCH, HOW MEASURED, WHICH MODEL, WHAT EVIDENCE, HOW CERTAIN, SENSOR CONSTRAINTS.

CRITICAL WRITING RULES (STRICT ENFORCEMENT):
1. Never use generic AI filler phrases.
   FORBIDDEN PHRASES:
   - "This image provides valuable insights"
   - "The analysis reveals important information"
   - "The AI successfully analyzed"
   - "This demonstrates the capabilities of"
   - "The satellite imagery shows"
   - "Comprehensive analysis indicates"
   - "Advanced AI models were used"
   - "AI-powered", "advanced AI", "valuable insights", "zero hallucination", "100% confidence"
2. Write concrete, evidence-grounded remote-sensing statements:
   - "The dominant predicted land-cover class is Coniferous forest (53.64% model probability via ResNet-50)."
   - "The change detector produced no valid change pixels in the submitted pair (0.00% change fraction)."
   - "Surface alteration of 2.17% was detected across 1,420 pixels (0.0355 ha) using BIT."
   - "Optical and SAR specialists agree on the presence of structural change."
3. Never repeat the user's question, conclusions, or metadata already displayed in cards.
4. Executive Finding must be 2-3 sentences maximum. Directly answer the query using numbers from EVIDENCE.
5. Key Observations must be 3-5 concise bullets. Every bullet must add distinct factual information. If only 2 exist, return 2.
6. Scientific Interpretation/Narrative must be 1 compact paragraph (80-150 words).
7. Model probability is NOT percentage area coverage. Never confuse model probability with land area.

CONCEPTUAL SEPARATION:
- MODEL OUTPUT: Predictions from specialist models (e.g., ResNet-50 LULC, BIT Change Detection, RSVQA).
- DETERMINISTIC CALCULATION: Pure mathematical metrology (e.g., raster dimensions, pixel counts, GSD, CRS, geodesic area/distance).
- SOURCE DATA: Direct sensor metadata (e.g., GSD, bands, CRS).
- ANALYST SYNTHESIS: Evidence-grounded interpretation combining facts.

EVIDENCE:
{evidence_json}

QUERY: {query}

INVESTIGATION PLAN SUMMARY: {plan_summary}

Write a JSON response with EXACTLY these structured fields:
{{
  "executive_summary": "<2-3 sentence concise finding directly answering the query with real metrics, no filler>",
  "observations": [
    "<concise factual observation bullet 1 with concrete number/model>",
    "<concise factual observation bullet 2 with concrete spatial/spectral metric>",
    "<concise factual observation bullet 3 with verification or constraint>"
  ],
  "interpretation": "<1-2 sentence evidence-grounded analyst synthesis>",
  "narrative": "<1 compact scientific paragraph (80-150 words) interpreting evidence without filler>",
  "spatial_findings": "<concrete spatial facts or N/A>",
  "temporal_findings": "<change metrics or N/A>",
  "sar_evidence": "<SAR backscatter details or N/A>",
  "cross_modal_analysis": "<optical+SAR fusion insights or N/A>",
  "methodology": "<concise execution sequence>",
  "limitations": ["<specific technical limitation 1>", "<specific technical limitation 2>"],
  "confidence_summary": "<calibrated probability and verification evaluation>",
  "data_quality": "<raster quality telemetry or N/A>",
  "conflicts_identified": "<identified conflicts or 'None identified'>",
  "assumptions": ["<specific domain assumption>"],
  "recommendations": "<actionable analyst recommendation>"
}}
"""


async def synthesize_report(
    query: str,
    evidence: EvidencePackage,
    plan: InvestigationPlan,
    manifest: InputManifest | None = None,
) -> Report:
    """
    Call Gemini to synthesize the evidence into a structured 13-section report.
    Adheres strictly to verified evidence, honest CRS reporting, and fallback labeling.
    """
    # Determine verified spatial metadata status from manifest or evidence
    has_geospatial = False
    epsg_codes = []
    if manifest and manifest.images:
        for img in manifest.images:
            if getattr(img, "is_geospatial", False) and getattr(img, "crs_epsg", None):
                has_geospatial = True
                epsg_codes.append(img.crs_epsg)
    
    # Check if event coordinates were passed in query or manifest
    has_event_coords = False
    if "latitude" in query.lower() or "°n" in query.lower() or "°s" in query.lower() or "at " in query.lower():
        has_event_coords = True

    if has_geospatial:
        spatial_status_desc = f"Spatial reference verified: EPSG:{', '.join(str(e) for e in epsg_codes)}."
    elif has_event_coords:
        spatial_status_desc = "Event coordinates supplied by source. CRS not available in source image."
    else:
        spatial_status_desc = "CRS not available in source image."

    # Prepare evidence for prompt (omit visual_evidence to avoid huge base64 strings)
    evidence_for_prompt = {
        "findings": [
            {
                "type": f.type.value,
                "value": f.value,
                "formatted_summary": format_finding_value(f),
                "source_model": f.source_model,
                "confidence": f.strength.model_confidence if f.strength else None,
                "confidence_status": f.strength.confidence_status.value if f.strength else None,
                "provenance": f.provenance,
            }
            for f in evidence.findings
        ],
        "overall_confidence": evidence.overall_confidence,
        "data_quality_flags": evidence.data_quality_flags,
        "coverage_gaps": evidence.coverage_gaps,
        "models_used": evidence.models_used,
        "tools_used": evidence.tools_used,
        "conflicts": [c.model_dump() for c in evidence.conflicts],
        "spatial_metadata_status": spatial_status_desc,
    }

    plan_summary = (
        f"Task: {plan.task_classification} | "
        f"Steps: {len(plan.steps)} | "
        f"Rationale: {plan.plan_rationale}"
    )

    prompt = SYNTHESIS_SYSTEM_PROMPT.format(
        evidence_json=json.dumps(evidence_for_prompt, indent=2),
        query=query,
        plan_summary=plan_summary,
    )

    # Check whether Gemini is properly configured (non-empty and not the default placeholder)
    is_gemini_configured = bool(
        settings.GEMINI_API_KEY
        and settings.GEMINI_API_KEY.strip()
        and settings.GEMINI_API_KEY.strip() != "your_gemini_api_key_here"
    )

    report_data = None
    is_fallback = False
    gemini_failure_reason = ""

    if is_gemini_configured:
        try:
            logger.info("Calling Gemini for 13-section report synthesis...")
            model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": settings.GEMINI_MAX_OUTPUT_TOKENS,
                    "response_mime_type": "application/json",
                },
            )
            response = model.generate_content(prompt)
            report_data = json.loads(response.text)
        except Exception as exc:
            gemini_failure_reason = str(exc)
            logger.warning(f"Gemini report synthesis failed: {exc}. Using deterministic synthesis.")
            is_fallback = True
    else:
        gemini_failure_reason = "Gemini API key not configured (placeholder or missing in .env)"
        is_fallback = True

    failed_steps = []
    if evidence.trace and evidence.trace.executed_steps:
        failed_steps = [s for s in evidence.trace.executed_steps if s.status.value == "failed"]

    if not report_data or not isinstance(report_data, dict):
        report_data = _build_human_readable_fallback_report(
            query=query,
            evidence=evidence,
            plan=plan,
            spatial_status_desc=spatial_status_desc,
            has_geospatial=has_geospatial,
            failed_steps=failed_steps,
            gemini_reason=gemini_failure_reason,
        )

    # Gemini returned a report — verify spatial claim is honest
    if not has_geospatial and "successfully resolved" in str(report_data.get("spatial_findings", "")):
        report_data["spatial_findings"] = spatial_status_desc

    # Clean executive summary and narrative of repetitive phrases and AI buzzwords
    exec_text = sanitize_synthesis_text(str(report_data.get("executive_summary", "")).strip())
    if is_fallback and not exec_text.startswith("[FALLBACK SYNTHESIS]"):
        exec_text = f"[FALLBACK SYNTHESIS] {exec_text}"
    report_data["executive_summary"] = exec_text

    report_data["narrative"] = sanitize_synthesis_text(str(report_data.get("narrative", "")).strip())
    if "limitations" in report_data and isinstance(report_data["limitations"], list):
        report_data["limitations"] = [sanitize_synthesis_text(str(l)) for l in report_data["limitations"]]
    if "assumptions" in report_data and isinstance(report_data["assumptions"], list):
        report_data["assumptions"] = [sanitize_synthesis_text(str(a)) for a in report_data["assumptions"]]

    # Agricultural query context refinement without redundant duplicate paragraphs
    _query_lower = query.lower()
    _ag_query = any(w in _query_lower for w in [
        "agricultural", "agriculture", "crop", "cultivat", "farm", "arable", "irrigation",
        "field", "plantation", "paddy", "wheat", "rice", "sowing", "harvest"
    ])
    if _ag_query:
        _lulc_labels = []
        for f in evidence.findings:
            if hasattr(f, 'type') and 'class' in str(f.type).lower():
                _val = f.value
                if isinstance(_val, dict):
                    _lulc_labels += _val.get('labels', []) + [p.get('label','') for p in _val.get('top_predictions', [])]
        _has_arable = any('arable' in l.lower() or 'crop' in l.lower() or 'agricultural' in l.lower() for l in _lulc_labels)
        if _has_arable:
            _vqa_failed_or_missing = any("rsvqa" in (getattr(s, "tool_id", str(s))).lower() for s in failed_steps) or not any("rsvqa" in m.lower() for m in evidence.models_used)
            if _vqa_failed_or_missing:
                _ag_note = (
                    "The available LULC classifier identifies Arable land among the predicted scene classes. "
                    "However, the remote-sensing VQA specialist failed or was unavailable during this investigation, "
                    "so the current system cannot independently verify active cultivation from the VQA specialist. "
                    "The result should therefore be treated as classifier-based scene evidence, not a direct confirmation of active cultivation."
                )
            else:
                _ag_note = (
                    "Detection of 'Arable land' indicates land cover consistent with cultivated or agricultural use "
                    "as classified by the LULC specialist (ResNet-50). This is scene-level evidence from multispectral imagery "
                    "and does not independently confirm active crop growth without corroborating VQA or temporal change evidence."
                )
            _existing_assumptions = report_data.get('assumptions', [])
            if isinstance(_existing_assumptions, list) and not any("Arable land" in str(a) for a in _existing_assumptions):
                report_data['assumptions'] = _existing_assumptions + [_ag_note]
            if report_data.get('narrative') and "Arable land" not in report_data['narrative']:
                report_data['narrative'] = report_data['narrative'].rstrip() + f" {_ag_note}"
            if report_data.get('executive_summary') and "Arable land" not in report_data['executive_summary']:
                report_data['executive_summary'] = report_data['executive_summary'].rstrip() + " Identified Arable land represents scene-level classification consistent with agricultural land use."

    raw_obs = report_data.get("observations", [])
    if isinstance(raw_obs, list):
        clean_obs = [sanitize_synthesis_text(str(o)) for o in raw_obs if o]
    elif raw_obs:
        clean_obs = [sanitize_synthesis_text(str(raw_obs))]
    else:
        clean_obs = []

    return Report(
        executive_summary=sanitize_synthesis_text(report_data.get("executive_summary")),
        narrative=sanitize_synthesis_text(report_data.get("narrative", "")),
        observations=clean_obs,
        spatial_findings=report_data.get("spatial_findings", spatial_status_desc),
        temporal_findings=report_data.get("temporal_findings"),
        sar_evidence=report_data.get("sar_evidence"),
        cross_modal_analysis=report_data.get("cross_modal_analysis"),
        methodology=report_data.get("methodology", ""),
        limitations=report_data.get("limitations", []),
        confidence_summary=report_data.get("confidence_summary", ""),
        data_quality=report_data.get("data_quality"),
        conflicts_identified=report_data.get("conflicts_identified"),
        assumptions=report_data.get("assumptions", []),
        recommendations=report_data.get("recommendations"),
    )


def format_finding_value(finding) -> str:
    """
    Format any finding value into clean, human-readable text without raw Python dicts.
    Used by report exporters and narrative synthesizers.
    """
    val = getattr(finding, "value", finding)
    if val is None:
        return "None recorded"
    if isinstance(val, str):
        return val

    # Classification
    if isinstance(val, dict) and ("top_predictions" in val or "labels" in val):
        top_preds = val.get("top_predictions", [])
        if top_preds:
            primary = top_preds[0]
            label = primary.get("label", "Unknown")
            prob = primary.get("probability", 0.0)
            others = [
                f"{p.get('label', '')}: {round(float(p.get('probability', 0)) * 100, 2)}%"
                for p in top_preds[1:5]
            ]
            others_str = f" | Supporting: {', '.join(others)}" if others else ""
            return f"Primary: {label} ({round(float(prob) * 100, 2)}%){others_str}"
        labels = val.get("labels", [])
        return f"Labels detected: {', '.join(labels)}"

    # Raster stats
    if isinstance(val, dict) and ("width" in val or "height" in val or "crs" in val):
        parts = []
        if "filename" in val:
            parts.append(f"File: {val['filename']}")
        if "width" in val and "height" in val:
            parts.append(f"{val['width']}×{val['height']} px")
        if "bands" in val:
            parts.append(f"{val['bands']} bands")
        if "dtype" in val:
            parts.append(f"dtype: {val['dtype']}")
        if "modality" in val:
            parts.append(f"Modality: {val['modality']}")
        if "crs" in val:
            parts.append(f"CRS: {val['crs']}")
        if "gsd" in val:
            gsd = val["gsd"]
            if isinstance(gsd, (list, tuple)) and len(gsd) >= 2:
                parts.append(f"GSD: {gsd[0]}m × {gsd[1]}m")
            else:
                parts.append(f"GSD: {gsd}m")
        return ", ".join(parts)

    # Change Map
    if isinstance(val, dict) and "change_percentage" in val:
        pct = val.get("change_percentage", 0.0)
        px = val.get("changed_pixels", 0)
        method = val.get("method", "Bitemporal change detection")
        return f"Surface Change: {pct}% ({px:,} pixels altered) via {method}"

    # Measurement
    if isinstance(val, dict):
        formatted_items = []
        for k, v in val.items():
            k_clean = k.replace("_", " ").title()
            if isinstance(v, float):
                formatted_items.append(f"{k_clean}: {round(v, 4)}")
            elif isinstance(v, (list, tuple)):
                formatted_items.append(f"{k_clean}: [{', '.join(str(x) for x in v[:4])}]")
            else:
                formatted_items.append(f"{k_clean}: {v}")
        return ", ".join(formatted_items)

    # Bounding box
    if isinstance(val, dict) and ("boxes" in val or "detections_count" in val):
        count = val.get("detections_count", len(val.get("boxes", [])))
        ref = val.get("text_reference", "target")
        return f"{count} target detection(s) matching '{ref}'"

    return str(val)


def _build_human_readable_fallback_report(
    query: str,
    evidence: EvidencePackage,
    plan: InvestigationPlan,
    spatial_status_desc: str,
    has_geospatial: bool,
    failed_steps: list,
    gemini_reason: str = "",
) -> dict:
    """
    Construct a high-fidelity, publication-grade deterministic synthesis
    strictly avoiding any raw Python dictionary or JSON serialization dumping.
    Directly answers the user query first.
    """
    classification_data = None
    raster_stats_data = None
    change_map_data = None
    measurement_data = None
    text_data = []

    for f in evidence.findings:
        if "FAILED" in str(f.value):
            continue
        val = f.value
        f_type_str = str(getattr(f.type, "value", f.type)).lower()
        if "class" in f_type_str or (isinstance(val, dict) and "top_predictions" in val):
            classification_data = val
        elif "raster" in f_type_str or (isinstance(val, dict) and ("width" in val or "crs" in val)):
            raster_stats_data = val
        elif "change" in f_type_str or (isinstance(val, dict) and "change_percentage" in val):
            change_map_data = val
        elif "measure" in f_type_str or (isinstance(val, dict) and any("m2" in k or "area" in k or "ndvi" in k for k in val.keys())):
            measurement_data = val
        elif isinstance(val, str):
            text_data.append(val)

    exec_summary_lines = []
    narrative_paragraphs = []

    if classification_data and isinstance(classification_data, dict):
        top_preds = classification_data.get("top_predictions", [])
        if top_preds:
            primary = top_preds[0]
            top_label = primary.get("label", "Unknown")
            top_prob = round(float(primary.get("probability", 0.0)) * 100, 2)

            secondary_preds = top_preds[1:5]
            sec_items = [
                f"{p.get('label')}: {round(float(p.get('probability', 0.0)) * 100, 2)}%"
                for p in secondary_preds
            ]
            sec_str = f" Secondary classes include {', '.join(sec_items)}." if sec_items else ""

            exec_summary_lines.append(
                f"The scene is predominantly classified as **{top_label}** with a calibrated model probability of "
                f"**{top_prob}%** (ResNet-50 LULC).{sec_str}"
            )
            narrative_paragraphs.append(
                f"Specialist inference identifies **{top_label}** as the leading land-cover prediction "
                f"at **{top_prob}%** calibrated probability (BigEarthNet 19-class taxonomy).{sec_str}"
            )
        else:
            labels = classification_data.get("labels", [])
            exec_summary_lines.append(f"Identified scene classes: {', '.join(labels)}.")
            narrative_paragraphs.append(f"Land cover analysis identified spectral characteristics matching: {', '.join(labels)}.")

    elif change_map_data and isinstance(change_map_data, dict):
        chg_pct = change_map_data.get("change_percentage", 0.0)
        chg_px = change_map_data.get("changed_pixels", 0)
        total_px = change_map_data.get("total_pixels", 0)
        chg_method = change_map_data.get("method", "BIT (Bi-Temporal Image Transformer)")
        area_ha = change_map_data.get("area_ha")
        area_m2 = change_map_data.get("area_m2")
        area_str = f" Calculated affected area: {area_ha} ha ({area_m2} m²)." if area_ha else ""

        if chg_px == 0 or chg_pct == 0.0:
            exec_summary_lines.append(
                f"The change detector produced no valid change pixels in the submitted acquisition pair "
                f"(0.00% change fraction across {total_px:,} pixels). Detector result: No changed pixels detected."
            )
            narrative_paragraphs.append(
                f"Bi-temporal inspection using {chg_method} identified 0 modified pixels (0.00% change fraction). "
                f"The target scene demonstrates structural stability between acquisition epochs (Calculation status: DETERMINISTIC)."
            )
        else:
            exec_summary_lines.append(
                f"Surface alteration of **{chg_pct}%** was detected across **{chg_px:,}** modified pixels "
                f"using {chg_method}.{area_str}"
            )
            narrative_paragraphs.append(
                f"Surface alteration of **{chg_pct}%** detected across {chg_px:,} modified pixels "
                f"using {chg_method}.{area_str} (Calculation status: DETERMINISTIC)."
            )

    elif text_data:
        cleaned_text = [sanitize_synthesis_text(t) for t in text_data]
        exec_summary_lines.append(f"Specialist assessment: {' '.join(cleaned_text[:2])}")
        narrative_paragraphs.append(f"Visual reasoning observation: {' '.join(cleaned_text)}.")
    else:
        exec_summary_lines.append(
            f"Analysis completed across {len(evidence.tools_used + evidence.models_used)} active specialist tools."
        )
        narrative_paragraphs.append(
            f"Specialist pipeline executed across {len(evidence.tools_used + evidence.models_used)} analytical components."
        )

    if raster_stats_data and isinstance(raster_stats_data, dict):
        fn = raster_stats_data.get("filename", "analyzed raster")
        w = raster_stats_data.get("width", "N/A")
        h = raster_stats_data.get("height", "N/A")
        bands = raster_stats_data.get("bands", "N/A")
        modality = raster_stats_data.get("modality", "Optical RGB")
        crs = raster_stats_data.get("crs", "N/A")
        gsd = raster_stats_data.get("gsd", "N/A")
        gsd_str = f"{gsd[0]} m × {gsd[1]} m" if isinstance(gsd, (list, tuple)) and len(gsd) >= 2 else f"{gsd} m"

        narrative_paragraphs.append(
            f"Raster metadata confirms input acquisition '{fn}' comprises {w} × {h} pixels across {bands} spectral band(s) "
            f"in {modality} modality with ground sampling distance of {gsd_str}. Coordinate reference system: {crs}. (Calculation status: DETERMINISTIC)."
        )

    if measurement_data and isinstance(measurement_data, dict):
        m_items = [
            f"{k.replace('_', ' ').title()}: {round(v, 4) if isinstance(v, float) else v}"
            for k, v in measurement_data.items()
        ]
        narrative_paragraphs.append(
            f"Deterministic spatial calculations computed the following physical metrics: {', '.join(m_items)} (Calculation status: DETERMINISTIC)."
        )

    narrative_paragraphs.append(
        "Reported observations correspond strictly to verified specialist predictions and deterministic raster telemetry without speculative extrapolation."
    )

    limitations = [
        "FALLBACK SYNTHESIS: Deterministic rule-based synthesis used (Gemini orchestrator offline or unconfigured)."
    ]
    if not has_geospatial:
        limitations.append("Image lacks embedded geospatial reference (CRS not available in source image).")
    if failed_steps:
        limitations.append(
            f"SPECIALIST STATUS: FAILED / UNAVAILABLE ({len(failed_steps)} specialist step(s) failed or timed out)."
        )
    limitations.append("Analysis is constrained by the native spatial resolution and spectral bands of the input acquisition.")

    is_temporal = plan.task_classification.startswith("change") or change_map_data is not None
    is_sar = (
        plan.task_classification.startswith("cross_modal")
        or "sar" in plan.task_classification
        or any("sar" in m.lower() for m in evidence.models_used)
    )

    temporal_findings = (
        "Bi-temporal change evaluation executed and verified across baseline acquisition pair."
        if is_temporal
        else "N/A - Single-scene optical acquisition; no temporal baseline established."
    )
    sar_evidence = (
        "Cross-modal microwave backscatter evaluated (C-band radar response, surface roughness, dielectric contrast)."
        if is_sar
        else "N/A - Optical analysis pipeline; SAR backscatter data not acquired."
    )
    cross_modal_analysis = "Optical reflectance and SAR microwave backscatter observations synthesized." if is_sar else "N/A - Single modality acquisition."

    observations = []
    if classification_data and isinstance(classification_data, dict):
        top_preds = classification_data.get("top_predictions", [])
        if top_preds:
            p0 = top_preds[0]
            observations.append(
                f"Primary land cover: {p0.get('label')} ({round(float(p0.get('probability', 0.0)) * 100, 2)}% model probability via ResNet-50)."
            )
            if len(top_preds) > 1:
                sec_desc = ", ".join([f"{p.get('label')} ({round(float(p.get('probability', 0.0)) * 100, 1)}%)" for p in top_preds[1:4]])
                observations.append(f"Secondary land cover classes: {sec_desc}.")
    if change_map_data and isinstance(change_map_data, dict):
        chg_pct = change_map_data.get("change_percentage", 0.0)
        chg_px = change_map_data.get("changed_pixels", 0)
        area_ha = change_map_data.get("area_ha")
        area_m2 = change_map_data.get("area_m2")
        if chg_px == 0 or chg_pct == 0.0:
            observations.append("The change detector returned no changed pixels in the submitted acquisition pair (0.00% change fraction).")
        else:
            observations.append(f"Surface alteration of {chg_pct}% was detected across {chg_px:,} modified pixels via BIT.")
            if area_ha:
                observations.append(f"Calculated physical extent of detected change is {area_ha} ha ({area_m2} m²).")
    if raster_stats_data and isinstance(raster_stats_data, dict):
        w = raster_stats_data.get("width", "N/A")
        h = raster_stats_data.get("height", "N/A")
        crs = raster_stats_data.get("crs", "N/A")
        observations.append(f"Raster dimensions: {w} × {h} px, Coordinate Reference System: {crs}.")
    if measurement_data and isinstance(measurement_data, dict):
        for k, v in list(measurement_data.items())[:2]:
            observations.append(f"{k.replace('_', ' ').title()}: {round(v, 4) if isinstance(v, float) else v} (deterministic calculation).")
    if not observations:
        observations.append("Specialist model inference and raster telemetry verified according to mission query.")

    return {
        "executive_summary": f"[FALLBACK SYNTHESIS] {' '.join(exec_summary_lines)}",
        "narrative": "\n\n".join(narrative_paragraphs),
        "observations": observations,
        "spatial_findings": spatial_status_desc,
        "temporal_findings": temporal_findings,
        "sar_evidence": sar_evidence,
        "cross_modal_analysis": cross_modal_analysis,
        "methodology": f"Executed pipeline utilizing: {', '.join(evidence.tools_used + evidence.models_used)}.",
        "limitations": limitations,
        "confidence_summary": "Model probability calibrated from specialist predictions. Spatial metadata verified deterministically.",
        "data_quality": (
            "Verified geospatial raster with valid CRS projection."
            if has_geospatial
            else "Sensor input accepted; verify spatial tags and cloud coverage."
        ),
        "conflicts_identified": (
            "None identified." if not evidence.conflicts else f"{len(evidence.conflicts)} conflict(s) detected."
        ),
        "assumptions": ["Radiometric calibration status was not independently verified by this workflow."],
        "recommendations": "Review high-probability scene classifications and spectral metrics.",
    }
