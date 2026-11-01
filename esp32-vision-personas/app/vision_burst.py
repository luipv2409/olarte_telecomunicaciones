from typing import Any, Dict, List

VERDICT_PERSON = "PERSONA"
VERDICT_OBJECT = "OBJETO"
VERDICT_UNCERTAIN = "INCIERTO"
VERDICT_NO_CAPTURE = "SIN_CAPTURA"


def decide_verdict(frame_results: List[Dict[str, Any]], min_person_frames: int) -> Dict[str, Any]:
    """
    Decide si lo que activó el IR es una persona u otro objeto a partir de la ráfaga de fotos.

    Cada elemento de frame_results es el resultado de PersonDetector.classify():
      {"persons": [...], "objects": [...], "error": Optional[str]}

    Reglas:
      - Sin ninguna foto válida              -> SIN_CAPTURA
      - Persona en >= min_person_frames fotos -> PERSONA
      - Persona en menos fotos que el mínimo  -> INCIERTO
      - Ninguna persona (con o sin objetos)   -> OBJETO (objeto no identificado como persona)
    """
    valid = [f for f in frame_results if not f.get("error")]
    if not valid:
        return {
            "verdict": VERDICT_NO_CAPTURE,
            "frames_analyzed": 0,
            "person_frames": 0,
            "max_person_confidence": 0.0,
            "objects": [],
        }

    person_frames = sum(1 for f in valid if f.get("persons"))
    max_conf = 0.0
    for f in valid:
        for p in f.get("persons", []):
            max_conf = max(max_conf, float(p.get("confidence", 0.0)))

    objects: Dict[str, int] = {}
    for f in valid:
        for o in f.get("objects", []):
            name = o.get("class", "desconocido")
            objects[name] = objects.get(name, 0) + 1

    required = min(max(1, min_person_frames), len(valid))
    if person_frames >= required:
        verdict = VERDICT_PERSON
    elif person_frames > 0:
        verdict = VERDICT_UNCERTAIN
    else:
        verdict = VERDICT_OBJECT

    return {
        "verdict": verdict,
        "frames_analyzed": len(valid),
        "person_frames": person_frames,
        "max_person_confidence": round(max_conf, 3),
        "objects": [{"class": k, "frames": v} for k, v in sorted(objects.items(), key=lambda x: -x[1])],
    }

