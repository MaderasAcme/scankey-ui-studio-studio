import os
import random
from datetime import datetime
from typing import Dict, Any


def normalize_engine_output(raw: Dict[str, Any], input_id: str, proc_time: int) -> Dict[str, Any]:
    """
    Normaliza la salida para cumplir el contrato ScanKey:
    - Siempre 3 resultados
    - high_confidence si top >= 0.95
    - low_confidence si top < 0.60
    - should_store_sample si top >= 0.75 y rand < storage_probability y current_samples < 30
    - manufacturer_hint con gate >= 0.85 para priorizar ranking (si aplica)
    """
    results = list(raw.get("results") or [])
    hint = raw.get("manufacturer_hint") or {"found": False, "name": None, "confidence": 0.0}

    # Prioriza por fabricante si es fuerte
    if bool(hint.get("found")) and float(hint.get("confidence", 0.0)) >= 0.85 and hint.get("name"):
        target = hint.get("name")
        results.sort(key=lambda x: (x.get("brand") == target, x.get("confidence", 0.0)), reverse=True)
    else:
        results.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)

    # defaults para asegurar UI consistente
    def _default_result():
        return {
            "id_model_ref": None,
            "type": "unknown",
            "brand": None,
            "model": None,
            "orientation": None,
            "head_color": None,
            "visual_state": None,
            "patentada": False,
            "compatibility_tags": [],
            "confidence": 0.0,
            "explain_text": "Sin candidato suficiente.",
            "crop_bbox": None,
        }

    while len(results) < 3:
        results.append(_default_result())

    final_results = results[:3]
    for idx, r in enumerate(final_results):
        r["rank"] = idx + 1
        # rellenar keys faltantes
        base = _default_result()
        for k, v in base.items():
            r.setdefault(k, v)
        r["confidence"] = float(max(0.0, min(1.0, r.get("confidence", 0.0))))
        r["compatibility_tags"] = list(r.get("compatibility_tags") or [])

    top = float(final_results[0]["confidence"])

    storage_probability = float(os.getenv("STORAGE_PROBABILITY", "0.75"))
    storage_probability = max(0.0, min(1.0, storage_probability))

    max_samples = int(os.getenv("MAX_SAMPLES_PER_CANDIDATE", "30"))
    current_samples = int(raw.get("current_samples_for_candidate") or 0)

    should_store = (top >= 0.75) and (current_samples < max_samples) and (random.random() < storage_probability)

    return {
        "input_id": input_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "manufacturer_hint": {
            "found": bool(hint.get("found")),
            "name": hint.get("name"),
            "confidence": float(hint.get("confidence", 0.0)),
        },
        "results": final_results,
        "low_confidence": top < 0.60,
        "high_confidence": top >= 0.95,
        "should_store_sample": should_store,
        "storage_probability": storage_probability,
        "current_samples_for_candidate": current_samples,
        "manual_correction_hint": {"fields": ["marca", "modelo", "tipo", "orientacion", "ocr_text"]},
        "debug": {
            "processing_time_ms": int(proc_time),
            "model_version": os.getenv("MODEL_VERSION", "unknown"),
        },
    }
