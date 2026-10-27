from pathlib import Path

from business_layer.config import Settings


def test_settings_do_not_include_vehicle_pricing():
    pricing_fields = {"rate_car", "rate_motorbike", "rate_bicycle"}
    assert pricing_fields.isdisjoint(Settings.model_fields)


def test_env_example_does_not_configure_vehicle_pricing():
    template = Path(".env.example").read_text(encoding="utf-8")
    assert "RATE_CAR=" not in template
    assert "RATE_MOTORBIKE=" not in template
    assert "RATE_BICYCLE=" not in template
