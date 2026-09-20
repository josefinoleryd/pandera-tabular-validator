"""
src/pipeline.py

Orkestrerar datavalideringsflödet:
1. Läser in rådata med felhantering för fil- och I/O-fel.
2. Kör validering via Pandera DataFrameSchema (lazy=True).
3. Separerar godkänd data från avvikelser.
4. Exporterar tre filer till output/:
    - clean_outages.csv (godkänd data)
    - rejected_outages.csv (felaktiga rader ur rådatan)
    - failure_cases.csv (detaljerad fellogg över brutna regler)
"""

import logging
from pathlib import Path
import pandas as pd
import pandera.pandas as pa

from src.schemas import outage_schema


logger = logging.getLogger(__name__)


def run_validation_pipeline(input_path: Path, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Kör valideringsflödet och exporterar godkänd data samt felloggar."""
    # 1. Kontrollera att indatafilen existerar
    if not input_path.is_file():
        logger.error(f"Kunde inte hitta indatafilen: {input_path.resolve()}")
        raise FileNotFoundError(f"Filen saknas: {input_path}")

    # 2. Läs in rådata säkert
    try:
        logger.info(f"Läser in rådata från: {input_path}")
        raw_df = pd.read_csv(input_path)
    except pd.errors.EmptyDataError:
        logger.error(f"Filen är helt tom: {input_path}")
        raise
    except Exception as exc:
        logger.error(f"Oväntat fel vid inläsning av CSV-fil: {exc}")
        raise

    if raw_df.empty:
        logger.warning("Datasetet innehåller inga datarader att validera.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    clean_df = pd.DataFrame()
    rejected_df = pd.DataFrame()
    errors_df = pd.DataFrame()

    # 3. Validera med Pandera
    try:
        clean_df = outage_schema.validate(raw_df, lazy=True)
        logger.info("Validering slutförd: Alla rader godkändes.")

    except pa.errors.SchemaErrors as exc:
        # Datainnehållsfel och schemadefekt (lazy validation)
        errors_df = (
            exc.failure_cases[["index", "column", "check", "failure_case"]]
            .drop_duplicates()
            .sort_values(by="index")
            .reset_index(drop=True)
        )

        # Kontrollera om det finns fel på tabellnivå (där index är NaN, t.ex. saknad kolumn)
        has_structural_errors = errors_df["index"].isna().any()

        if has_structural_errors:
            logger.warning(
                "Strukturella fel upptäcktes (t.ex. saknade obligatoriska kolumner). Hela datasetet avvisas."
            )
            clean_df = pd.DataFrame(columns=raw_df.columns)
            rejected_df = raw_df.copy()
        else:
            failed_indices = sorted(
                int(idx) for idx in errors_df["index"].dropna().unique()
            )
            clean_df = raw_df.drop(index=failed_indices).reset_index(drop=True)
            rejected_df = raw_df.loc[failed_indices].reset_index(drop=True)

        logger.warning(
            f"Validering klar: {len(clean_df)} rader godkända, {len(rejected_df)} rader avvisade."
        )

    except Exception as exc:
        # Oväntat fel i valideringssteget
        logger.error(f"Ett oväntat fel inträffade under valideringen: {exc}")
        raise

    # 4. Spara filer med felhantering för målmapp och skrivrättigheter
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        clean_df.to_csv(output_dir / "clean_outages.csv", index=False)
        rejected_df.to_csv(output_dir / "rejected_outages.csv", index=False)
        errors_df.to_csv(output_dir / "failure_cases.csv", index=False)
        logger.info(f"Rapporter sparade till mappen: {output_dir}")
    except OSError as exc:
        logger.error(f"Kunde inte spara rapportfilerna till {output_dir}: {exc}")
        raise

    return clean_df, rejected_df, errors_df