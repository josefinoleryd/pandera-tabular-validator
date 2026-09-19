"""
main.py

Startpunkt (entrypoint) för valideringsflödet.
Konfigurerar loggning, definierar filsökvägar och anropar valideringspipelinen.
"""

import logging
from pathlib import Path
from src.pipeline import run_validation_pipeline


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )

    project_root = Path(__file__).resolve().parent
    input_file = project_root / "data" / "staged_outages.csv"
    output_dir = project_root / "data" / "output"

    run_validation_pipeline(input_file, output_dir)


if __name__ == "__main__":
    main()