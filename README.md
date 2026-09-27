# Individuell inlämningsuppgift – Valfri fördjupning inom Python: Datavalidering med Pandera

Det här projektet är en teknisk fördjupning i deklarativ datavalidering för tabulär data med biblioteket Pandera. 

Fokus ligger på att etablera en automatiserad kvalitetsgrind (*Quality Gate*) för elnätsdata (avbrottsstatistik) som stoppar semantiska affärsregler och "tysta fel" innan datan når nedströms analys och beräkning av nyckeltal (t.ex. SAIDI/SAIFI). Pipelinen implementerar ett karantänsmönster (*triage*) via ```lazy=True``` som separerar godkända observationer från felaktiga utan att avbryta körningen i förtid. 

## Installation och hur man kör 

### Förutsättningar 

* Python-version: ```>=3.10``` (utvecklat och testat på Python 3.13)

### Installation

1. Klona repot från GitHub:
   ```bash
   git clone https://github.com/josefinoleryd/pandera-tabular-validator.git
   cd order-report-refactoring
   ```
2. Skapa och aktivera en virtuell miljö:
    ```bash
    python -m venv .venv
    # På Windows:
    .venv\Scripts\activate
    # På macOS/Linux:
    source .venv/bin/activate
    ```
3. Installera projektets beroenden:
    ```bash
    pip install -r requirements.txt
    ```

### Så kör du programmet 

Starta valideringen från projektets rotkatalog: 

```bash
python main.py
```

Programmet läser in rådata från ```data/staged_outages.csv```, kör schemavalideringen och genererar tre CSV-filer i ```data/output/```:

* ```clean_outages.csv```: Rader som uppfyller samtliga tekniska format och affärsregler (redo för analys).
* ```rejected_outages.csv```: Karantänsatta rader som brutit mot minst en regel.
* ```failure_cases.csv```: Detaljerad fellogg från Pandera med radindex, kolumn, felaktigt värde och bruten kontroll.

### Så kör du testerna 

Kör enhetstesterna med pytest via modulflaggan:

```bash
python -m pytest -v
```

Kommandot kör testsviten i ```tests/test_pipeline_errors.py``` och verifierar pipelinens defensiva felhantering med isolerade ```tmp_path```-miljöer:

* Att ```FileNotFoundError``` reses med tydlig loggning om indatafilen saknas.
* Att ```EmptyDataError``` fångas och hanteras korrekt vid tomma 0-byte-filer.
* Att strukturella fel (t.ex. saknad obligatorisk kolumn) underkänenr hela datasetet och identifieras med felkoden ```column_in_dataframe``` i felloggen. 

## Utforskning och valideringsfacit (Notebook)

I katalogen ```notebooks/``` finns notebooken ```pandera_exploration.ipynb``` som dokumenterar utvecklingsprocessen och experimenterande med Panderas funktioner, exempelvis:

* Jämförelse mellan ```DataFrameSchema``` och klassbaserade ```DataFrameModel```.
* Vektoriserade flerkolumnskontroller (*wide checks*)
* Utvärdering av felrapporter via ```SchemaErrors``` och ```exc.failure_cases```. 

Notebooken innehåller även ett detaljerat facit över samtliga 25 rader i ```staged_outages.csv``` som specificerar vilka rader som ska passera respektive underkännas och varför.

## Datamodell & Affärsregler 

Indatan (```staged_outages.csv```) valideras mot följande schema och domänspecifika regler i ```src/schemas.py```: 

| Kolumn | Typ | Validering och affärsregel |
| :--- | :--- | :--- |
| ```incident_id``` | ```str``` | Unikt händelse-ID för varje avbrott (```unique=True```). |
| ```voltage_level_kv``` | ```float``` | Tillåtna spänningsnivåer i lokalnät: 0.4, 10.0 eller 20.0 kV. |
| ```start_time``` | ```datetime``` | Starttidpunkt; får inte ligga i framtiden. |
| ```end_time``` | ```datetime``` | Sluttidpunkt; måste inträffa samtidigt som eller efter ```start_time```. |
| ```duration_minutes``` | ```int``` | Avbrottstid i minuter; får inte vara negativ (>= 0). |
| ```outage_type``` | ```str``` | Klassificering: ```planerat``` eller ```oplanerat```. |
| ```cause_category``` | ```str``` | Tillåtna kategorier (```tekniskt_fel```, ```underhåll```, ```väder```, ```grävskada```, ```personal```, ```okänd```). Planerat avbrott kräver ```underhåll``` och vice versa. |
| ```customers_affected``` | ```int``` | Antal drabbade abonnenter; får inte vara negativ (>= 0). |
| ```compensation_eligible``` | ```bool``` | Får endast vara ```True``` om avbrottet är ```oplanerat``` OCH ```duration_minutes``` >= 720. |

## Projektstruktur

```bash
pandera-tabular-validator/
├── data/
│   ├── data_for_exploration/       # Test- och utforskningsdata från notebook-stadiet
│   ├── output/                     # Genererad utdata från valideringskörning
│   │   ├── clean_outages.csv       # Godkända rader (redo för analys)
│   │   ├── rejected_outages.csv    # Avvisade rader i karantän
│   │   └── failure_cases.csv       # Detaljerad fellogg från Pandera
│   └── staged_outages.csv          # Indataset med simulerad avbrottsstatistik
├── notebooks/
│   └── pandera_exploration.ipynb   # Utforskning, prototyper och facit för avbrottsdata
├── src/
│   ├── __init__.py                 # Paketmarkör
│   ├── pipeline.py                 # Orkestrering av filläsning, triage, felhantering och export
│   └── schemas.py                  # Schemadefinition, typkonstanter (Final) och flerkolumnsregler
├── tests/
│   └── test_pipeline_errors.py     # Enhetstester för felhantering och kantfall med pytest
├── main.py                         # Startpunkt för terminalkörning och centraliserad logging
├── requirements.txt                # Beroenden
└── README.md                       # Projekt- och körinstruktioner
```

## Teknikstack och beroenden

* Programmeringsspråk: Python
* Datavalidering: Pandera
* Databehandling: Pandas
* Testramverk: pytest 
* Versionshantering: Git och Github
