"""
tests/test_pipeline_errors.py

Enhetstester för defensiv felhantering i valideringspipelinen.
Använder pytests inbyggda tmp_path fixture för att skapa isolerad testdata.
"""

from pathlib import Path
import pandas as pd
import pandera.pandas as pa
import pytest

from src.pipeline import run_validation_pipeline


def test_missing_input_file_raises_not_found(tmp_path: Path) -> None:
    """Verifierar att FileNotFoundError kastas om indatafilen inte existerar."""
    non_existent_file = tmp_path / "finns_inte.csv"
    output_dir = tmp_path / "output"

    with pytest.raises(FileNotFoundError, match="Filen saknas"):
        run_validation_pipeline(non_existent_file, output_dir)


def test_empty_input_file_raises_empty_data_error(tmp_path: Path) -> None:
    """Verifierar att EmptyDataError kastas om en nollbyte-fil levereras."""
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("", encoding="utf-8")     # Skapar en tom fejkfil
    output_dir = tmp_path / "output"

    with pytest.raises(pd.errors.EmptyDataError):
        run_validation_pipeline(empty_file, output_dir)


def test_missing_required_column_raises_schema_error(tmp_path: Path) -> None:
    """Verifierar att saknade obligatoriska kolumner fångas av lazy-valideringen och avvisas."""
    broken_csv = tmp_path / "broken_columns.csv"
    # Fejkdata där incident_id saknas helt
    fejk_data = (
        "voltage_level_kv,start_time,end_time,duration_minutes,"
        "outage_type,cause_category,customers_affected,compensation_eligible\n"
        "10.0,2026-01-01 10:00:00,2026-01-01 11:00:00,60,oplanerat,tekniskt_fel,15,False\n"
    )
    broken_csv.write_text(fejk_data, encoding="utf-8")
    output_dir = tmp_path / "output"

    clean_df, rejected_df, errors_df = run_validation_pipeline(broken_csv, output_dir)

    # Verifiera att raden underkändes och inte släpptes igenom som ren data
    assert clean_df.empty
    assert len(rejected_df) == 1
    # Verifiera att Pandera flaggade just den saknade kolumnen i fellogen
    assert "column_in_dataframe" in errors_df["check"].values