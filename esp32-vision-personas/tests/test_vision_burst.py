from app.vision_burst import decide_verdict


def frame(persons=0, objects=(), error=None):
    return {
        "persons": [{"class": "person", "confidence": 0.8, "box": [0, 0, 1, 1]}] * persons,
        "objects": [{"class": o, "confidence": 0.6, "box": [0, 0, 1, 1]} for o in objects],
        "error": error,
    }


def test_persona_confirmada():
    r = decide_verdict([frame(1), frame(1), frame(0), frame(1), frame(0)], min_person_frames=2)
    assert r["verdict"] == "PERSONA"
    assert r["person_frames"] == 3


def test_objeto_sin_persona():
    r = decide_verdict([frame(0, ["suitcase"])] * 5, min_person_frames=2)
    assert r["verdict"] == "OBJETO"
    assert r["objects"][0]["class"] == "suitcase"


def test_objeto_no_identificado():
    r = decide_verdict([frame(0)] * 5, min_person_frames=2)
    assert r["verdict"] == "OBJETO"
    assert r["objects"] == []


def test_incierto_una_sola_foto():
    r = decide_verdict([frame(1), frame(0), frame(0), frame(0), frame(0)], min_person_frames=2)
    assert r["verdict"] == "INCIERTO"


def test_sin_captura():
    r = decide_verdict([frame(error="timeout"), frame(error="timeout")], min_person_frames=2)
    assert r["verdict"] == "SIN_CAPTURA"


def test_minimo_se_ajusta_si_hay_pocas_fotos():
    r = decide_verdict([frame(1)], min_person_frames=2)
    assert r["verdict"] == "PERSONA"

