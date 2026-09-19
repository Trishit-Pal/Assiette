from assiette.crous_client import flatten_menu, normalize_restaurant


def test_normalize_extracts_18th():
    raw = {
        "code": 1637,
        "nom": "Libre-service sorbonne - clignancourt",
        "adresse": "4 rue Francis de Croisset, 75018 Paris",
        "latitude": 48.89969,
        "longitude": 2.3467278,
        "horaires": '["Du lundi au vendredi"]',
        "jours_ouvert": [],
        "type": {"libelle": "Libre-service"},
        "zone": "Paris 18",
        "ouvert": True,
    }
    n = normalize_restaurant(raw)
    assert n["arrondissement"] == 18
    assert n["source"] == "crous"
    assert n["price_eur"] == 3.3


def test_flatten_menu_accepts_dict_payload():
    payload = {
        "data": {
            "repas": [
                {
                    "type": "midi",
                    "categories": [{"libelle": "Plats", "plats": [{"libelle": "Dal"}]}],
                }
            ]
        }
    }
    assert "Dal" in flatten_menu(payload, "midi")
    payload = {
        "data": [
            {
                "repas": [
                    {
                        "type": "midi",
                        "categories": [
                            {"libelle": "Plats", "plats": [{"libelle": "Lentilles"}]}
                        ],
                    },
                    {
                        "type": "soir",
                        "categories": [
                            {"libelle": "Plats", "plats": [{"libelle": "Pizza"}]}
                        ],
                    },
                ]
            }
        ]
    }
    text = flatten_menu(payload, "soir")
    assert "Pizza" in text
    assert "Lentilles" not in text
