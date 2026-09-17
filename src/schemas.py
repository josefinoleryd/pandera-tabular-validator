"""
src/schemas.py

Valideringsschema för elnätsdata (avbrottsstatistik) definierat med Pandera.
Innehåller typkontroller, intervallkrav samt flerkolumnsregler för affärslogik.
"""

from typing import Final
import pandas as pd
import pandera.pandas as pa


# Domänkonstanter och tillåtna värdemängder
ALLOWED_VOLTAGE_LEVELS: Final[list[float]] = [0.4, 10.0, 20.0]
ALLOWED_OUTAGE_TYPES: Final[list[str]] = ["planerat", "oplanerat"]
ALLOWED_CAUSE_CATEGORIES: Final[list[str]] = [
    "tekniskt_fel",
    "underhåll",
    "väder",
    "grävskada",
    "personal",
    "okänd"
]
MAX_VALID_TIMESTAMP: Final[pd.Timestamp] = pd.Timestamp("2026-06-30 23:59:59")             # Eventuellt ändra till dagens datum?
COMPENSATION_THRESHOLD_MINUTES: Final[int] = 720 


# Valideringsfunktioner för flerkolumnsregler
def check_end_time_chronology(df: pd.DataFrame) -> pd.Series:
    """Validerar att avbrottets sluttid inträffar samtidigt som eller efter starttiden."""
    return df["end_time"] >= df["start_time"]

def check_outage_cause_relation(df: pd.DataFrame) -> pd.Series:
    """
    Validerar sambandet mellan avbrottstyp och orsakskod:
    - Ett planerat avbrott måste ha orsakskoden 'underhåll'.
    - Ett oplanerat avbrott får inte ha orsakskoden 'underhåll'.
    """
    is_planned = df["outage_type"] == "planerat"
    is_maintenance = df["cause_category"] == "underhåll"
    return is_planned == is_maintenance

def check_compensation_eligibility(df: pd.DataFrame) -> pd.Series:
    """
    Validerar affärslogiken för avbrottsersättning:
    Ersättning är endast tillåten om avbrottet är oplanerar OCH varar >= 720 minuter.
    """
    qualifies_for_compensation = (df["outage_type"] == "oplanerat") & (
        df["duration_minutes"] >= COMPENSATION_THRESHOLD_MINUTES
    )
    return df["compensation_eligible"] == qualifies_for_compensation


# Huvudschema för avbrottsdata
outage_schema = pa.DataFrameSchema(
    columns={
        "incident_id": pa.Column(
            str,
            unique=True,
            description="Unikt incident-ID för varje avbrottshändelse"
        ),
        "voltage_level_kv": pa.Column(
            float,
            pa.Check.isin(ALLOWED_VOLTAGE_LEVELS),
            description="Lokalnätets nominella driftspänning i kV (0.4, 10.0, 20.0)"
        ),
        "start_time": pa.Column(
            pa.DateTime,
            checks=pa.Check.le(
                MAX_VALID_TIMESTAMP,
                error=f"start_time kan inte ligga i framtiden (> {MAX_VALID_TIMESTAMP.date()})"
            ),
            coerce=True,
            description="Starttidpunkt för avbrottet"
        ),
        "end_time": pa.Column(
            pa.DateTime,
            coerce=True,
            description="Sluttidpunkt för avbrottet"
        ),
        "duration_minutes": pa.Column(
            int,
            pa.Check.ge(0, error="duration_minutes kan inte vara negativ"),
            description="Avbrottets varaktighet i minuter"
        ),
        "outage_type": pa.Column(
            str,
            pa.Check.isin(ALLOWED_OUTAGE_TYPES),
            description="Klassificering av avbrottstyp (planerat eller oplanerat)"
        ),
        "cause_category": pa.Column(
            str,
            pa.Check.isin(ALLOWED_CAUSE_CATEGORIES),
            description="Fastställd orsakskategori för händelsen"
        ),
        "customers_affected": pa.Column(
            int,
            pa.Check.ge(0, error="customers_affected kan inte vara negativ"),
            description="Antal berörda elnätskunder"
        ),
        "compensation_eligible": pa.Column(
            bool,
            description="Indikerar om händelsen kvalificerar för lagstadgad avbrottsersättning"
        )
    },
    checks=[
        pa.Check(
            check_end_time_chronology,
            name="check_end_time_chronology",
            error="end_time inträffar före start_time"
        ),
        pa.Check(
            check_outage_cause_relation,
            name="check_outage_cause_relation",
            error="Konflikt mellan outage_type och cause_category"
        ),
        pa.Check(
            check_compensation_eligibility,
            name="check_compensation_eligibility",
            error="Ogiltig ersättningsstatus i förhållande till duration_minutes och outage_type"
        )
    ],
    strict=True,
    name="OutageValidationSchema"
)