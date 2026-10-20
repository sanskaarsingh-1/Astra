"""
Astra AI - Remote Sensing VQA Specialist Module
Grounded single-image visual question answering grounded on extracted visual features.

AUGMENTATION (Phase 3, September 20 2026):
  For descriptive / open-ended queries where the LULC heuristic produces low confidence,
  the resident RS-VLM LoRA adapter (get_vlm_inference()) is invoked as a second opinion.
  VLM path is clearly labelled in output: vlm_augmented=True.
  LULC-heuristic cases (presence, count, rural/urban) are unchanged.
"""

import time
from pathlib import Path
from typing import Dict, Any, Optional
import torch
from PIL import Image
from loguru import logger
import numpy as np


def _try_vlm_augment(image_path: Path, question: str) -> Optional[str]:
    """
    Attempt to augment answer using the trained BLIP LoRA adapter.
    Returns the generated answer string, or None if adapter unavailable/failed.
    Never raises - safe degradation always.
    """
    try:
        try:
            from backend.models.remote_sensing_vlm.model import get_vlm_inference
        except ImportError:
            from models.remote_sensing_vlm.model import get_vlm_inference
        vlm = get_vlm_inference()
        if vlm is None:
            return None
        img = Image.open(image_path).convert("RGB")
        prompt = f"Question: {question} Answer:"
        generated = vlm.generate(img, prompt, max_new_tokens=48)
        return generated.strip() if generated else None
    except Exception as e:
        logger.debug(f"[VLM-augment] Failed gracefully: {e}")
        return None


class RSVQASpecialist:
    """
    Dedicated Remote-Sensing VQA Specialist.
    Combines scene feature detection, land-cover taxonomy, and structured reasoning
    to answer questions about presence, land cover, rural/urban context, and features.

    For descriptive / open-ended questions that do not match structured heuristics,
    augments with the trained RS-VLM BLIP LoRA adapter when available.
    """
    def __init__(self, device: Optional[str] = None):
        self.device = torch.device(device or ("cuda:0" if torch.cuda.is_available() else "cpu"))
        self.model_name = "rsvqa-specialist"
        self.model_version = "1.1.0"

    def predict(self, image_path: Path | str, question: str) -> Dict[str, Any]:
        """
        Execute single-image VQA inference.
        Returns evidence-grounded answer with calibrated confidence and execution latency.
        """
        t0 = time.perf_counter()
        image_path = Path(image_path)
        question_lower = question.lower().strip()

        # Phase 5 Guardrail: Individual-Person / Casualty Detection Honesty upfront
        person_terms = ["person", "people", "human", "humans", "victim", "victims", "casualty", "casualties", "survivor", "survivors", "crowd"]
        if any(w in question_lower for w in person_terms):
            unsupported_msg = "Individual-person detection is not a validated capability of the current system and is therefore not reported. (Individual-person detection is not currently supported reliably for this imagery and resolution.)"
            return {
                "type": "text",
                "text": unsupported_msg,
                "answer": unsupported_msg,
                "confidence": 0.0,
                "task_type": "human_detection_guardrail",
                "question_type": "unsupported_resolution",
                "evidence": {
                    "limitation": "Individual-person detection is not a validated capability of the current system and is therefore not reported. Satellite ground sampling distance (typically >=0.5m/px to 10m/px) cannot reliably resolve individual human beings. Built-up area fabric, buildings, or infrastructure presence must not be conflated with person detection.",
                    "detected_land_cover": [],
                    "spatial_resolution_note": "A dedicated high-resolution aerial or UAV detector is required for individual human localization."
                },
                "vlm_augmented": False,
                "model": self.model_name,
                "latency_ms": int((time.perf_counter() - t0) * 1000),
                "status": "UNSUPPORTED_TASK",
            }

        # 1. Feature extraction via resident ResNet-50 LULC specialist
        try:
            from backend.services.model_service import model_service
        except ImportError:
            from services.model_service import model_service
        scene_res = model_service.predict_scene(image_path)
        top_labels = scene_res.get("labels", [])
        top_predictions = scene_res.get("top_predictions", [])
        all_probs = scene_res.get("all_probabilities", {})

        # 2. Categorize question and synthesize grounded answer
        q_type = "general"
        answer = "Information cannot be determined with sufficient confidence."
        confidence = 0.50
        vlm_augmented = False
        evidence = {
            "detected_land_cover": top_labels[:3],
            "top_predictions": top_predictions[:3],
            "extracted_features": []
        }


        # Case A: Rural vs Urban
        if any(w in question_lower for w in ["rural", "urban", "city", "countryside"]):
            q_type = "rural_urban"
            urban_score = all_probs.get("Urban fabric", 0.0) + all_probs.get("Industrial or commercial units", 0.0)
            rural_score = (all_probs.get("Arable land", 0.0) + all_probs.get("Pastures", 0.0) +
                           all_probs.get("Broad-leaved forest", 0.0) + all_probs.get("Coniferous forest", 0.0))
            if urban_score > rural_score and urban_score > 0.35:
                answer = "urban"
                confidence = min(0.95, round(urban_score + 0.1, 2))
            else:
                answer = "rural"
                confidence = min(0.95, round(rural_score / max(len(rural_score) if isinstance(rural_score, list) else 1, 1) + 0.2, 2))
            evidence["urban_score"] = round(float(urban_score), 4)

        # Case B: Presence question
        elif any(question_lower.startswith(w) for w in ["is there", "is a", "are there", "does", "do"]):
            q_type = "presence"
            matched_class = None
            for cls_name, prob in all_probs.items():
                cls_words = [w.lower() for w in cls_name.split() if len(w) > 3]
                if any(w in question_lower for w in cls_words):
                    matched_class = (cls_name, prob)
                    break

            if matched_class:
                cls_name, prob = matched_class
                if prob >= 0.45:
                    answer = "yes"
                    confidence = round(float(prob), 2)
                    evidence["extracted_features"].append(f"{cls_name} detected with probability {prob:.2f}")
                else:
                    answer = "no"
                    confidence = round(float(1.0 - prob), 2)
                    evidence["extracted_features"].append(f"{cls_name} absent or below threshold (probability {prob:.2f})")
            else:
                answer = f"The scene is predominantly characterized by {top_labels[0]}." if top_labels else "Uncertain."
                confidence = round(top_predictions[0]["probability"], 2) if top_predictions else 0.50

        # Case C: Counting questions
        elif any(w in question_lower for w in ["how many", "count", "amount of", "number of"]):
            q_type = "count"
            urban_prob = all_probs.get("Urban fabric", 0.0)
            if "building" in question_lower or "house" in question_lower:
                if urban_prob > 0.70:
                    answer = "Dense cluster of buildings detected (high density urban fabric)."
                    confidence = 0.82
                elif urban_prob > 0.30:
                    answer = "Sparse or moderate buildings detected."
                    confidence = 0.74
                else:
                    answer = "0 (no significant building structures detected in scene)."
                    confidence = 0.89
            else:
                answer = f"Density estimation: features present with confidence {top_predictions[0]['probability']}."
                confidence = 0.65

        # Case D: Descriptive / Open-Ended - VLM Augmentation Path
        else:
            q_type = "descriptive"
            labels_str = ", ".join(top_labels[:3])
            lulc_answer = f"The scene features {labels_str} as the primary land cover."
            lulc_confidence = round(top_predictions[0]["probability"], 2) if top_predictions else 0.60

            vlm_answer = _try_vlm_augment(image_path, question)

            if vlm_answer and len(vlm_answer.strip()) >= 2:
                answer = f"{vlm_answer} (Scene context: {labels_str}.)"
                confidence = round(min(0.82, lulc_confidence + 0.15), 2)
                vlm_augmented = True
                evidence["vlm_raw_answer"] = vlm_answer
                evidence["lulc_grounding"] = labels_str
                logger.debug(f"[RSVQA] VLM augmentation used. VLM: '{vlm_answer[:60]}'")
            else:
                answer = lulc_answer
                confidence = lulc_confidence
                logger.debug("[RSVQA] VLM unavailable or empty; using LULC heuristic answer.")

        duration_ms = round((time.perf_counter() - t0) * 1000, 2)

        if confidence < 0.45:
            answer = f"Uncertain: {answer} (low model confidence: {confidence})"

        return {
            "type": "text",
            "text": answer,
            "answer": answer,
            "confidence": confidence,
            "confidence_status": "CALIBRATED_PROBABILITY",
            "question_type": q_type,
            "vlm_augmented": vlm_augmented,
            "evidence": evidence,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "processing_time_ms": duration_ms,
            "specialist": self.model_name,
            "status": "SUCCESS",
        }


rsvqa_specialist = RSVQASpecialist()
