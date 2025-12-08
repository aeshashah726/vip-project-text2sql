# IMF Natural-Language Question Answering Pipeline

This project provides an end-to-end workflow to convert IMF Excel tables into a SQLite database and enable natural-language queries using an OpenAI model. The system ingests Excel files, builds a schema summary, generates SQL from natural language, executes the SQL, and returns a final model-generated answer.

---

## Features
- Automatic ingestion of all `.xlsx` files in the `imf_tables/` directory  
- SQLite database creation (`imf_data.db`)  
- Text-based schema summary for LLM context (`schema_text.txt`)  
- Natural-language → SQL → Answer workflow  
- Modular scripts for easy extension and customization  

---

## Repository Structure

```
├── creating_database.py   – Loads Excel files, builds SQLite DB, generates schema summary  
├── imf_nlqa.py            – Natural language → SQL → Answer pipeline  
├── run_pipeline.py        – Runs the full workflow end to end  
└── imf_tables/            – Folder where IMF Excel files must be placed  
```

---

## Requirements

**Recommended Python version:** 3.9–3.12

### Required packages
- pandas  
- sqlalchemy  
- openai  
- python-dotenv  

Install with:

```bash
pip install pandas sqlalchemy openai python-dotenv
```

(`sqlite3` is included with Python.)

---

## Setup

### 1. Add IMF Excel Files
Create the folder and place all IMF `.xlsx` files inside:

```
imf_tables/
```

### 2. Set Your OpenAI API Key

**macOS/Linux**
```bash
export OPENAI_API_KEY="your-key-here"
```

**Windows (PowerShell)**
```powershell
setx OPENAI_API_KEY "your-key-here"
```

**Or create a `.env` file:**
```
OPENAI_API_KEY=your-key-here
```

---

## Running the Pipeline

### Quick Start

```bash
# 1. Build the database
python creating_database.py

# 2. Ask a natural-language question
python imf_nlqa.py

# 3. Or run everything end-to-end
python run_pipeline.py

### A. Build the SQLite Database

```bash
python creating_database.py
```

This script will:

- Load all Excel files from `imf_tables/`  
- Build `imf_data.db`  
- Generate `schema_text.txt` (table names + column descriptions)  

---

### B. Ask Natural-Language Questions

```bash
python imf_nlqa.py
```

You will be prompted:

```
Enter your question:
```
Here is our list of query templates: https://docs.google.com/spreadsheets/d/1PbC8GyBNfBSMvDZnbVjTVLorU41SzH8-p8y62U-Xl8Q/edit?usp=sharing

The system will then:

1. Convert your question into SQL  
2. Execute SQL on `imf_data.db`  
3. Return raw SQL results  
4. Generate a final narrative answer via the model  

---

### C. Run Everything Automatically

```bash
python run_pipeline.py
```

This command:

- Builds the database (if needed)  
- Loads schema context  
- Prompts for a question  
- Generates SQL  
- Executes SQL  
- Produces a final answer  

---

## Customization

### Change the OpenAI Model

Inside `imf_nlqa.py`, modify:

```python
model = "gpt-4.1"
```

Other supported options:

- `gpt-4.1-mini`  
- `gpt-4o`  
- `gpt-o3-mini`  

---

### Change the Database Path

Update in any script:

```python
DB_PATH = "imf_data.db"
```

---

### Add More IMF Tables

Just place additional `.xlsx` files into `imf_tables/` and rebuild:

```bash
python creating_database.py
```

---

## Troubleshooting

### “No tables found”
- Ensure `imf_tables/` exists  
- Confirm the folder contains valid Excel files  

### “Database is locked”
Reset by removing and rebuilding:

```bash
rm imf_data.db
python creating_database.py
```

### Pipeline can't find the IMF database (`imf_data.db`)

If you get errors like "file not found", "no such table", or "database does not exist", check these:

1. Make sure `creating_database.py` was run successfully.
   It must finish without errors and produce `imf_data.db` in the project directory.

2. Confirm that all Excel files are inside the `imf_tables/` folder.
   The folder must exist and contain valid `.xlsx` files.

3. Ensure your Python working directory is the project root.
   For example, if you're in VS Code, run:
       `pwd`  (Mac/Linux)
       `cd`   (Windows PowerShell)
   You should see the folder containing `creating_database.py`.

4. Install Excel parsing libraries:
       pip install openpyxl xlrd

5. Delete and rebuild the database if it becomes corrupted:
       rm imf_data.db   (Mac/Linux)
       del imf_data.db  (Windows)
       python creating_database.py

### Excel parsing issues
Install common parsing engines:

```bash
pip install openpyxl xlrd
```

### API key not detected
Verify with:

```bash
echo $OPENAI_API_KEY
```

---

**### Example Output
**
Below are sample interactions showing how the system handles natural-language questions, generates SQL using Ollama, and returns final answers based on the IMF SQLite database.

Example 1 — Money Supply (M2) Comparison

Question

Compare India and China’s money supply (M2) in 2018.


Pipeline Output (abridged)

Sending request to Ollama… this may take a minute or two for complex queries.
STATUS: 200
Sending request to Ollama… this may take a minute or two for complex queries.
STATUS: 200


Final Answer
According to the IMF data, in 2018:

India’s M2 money supply was approximately 11.35 trillion USD

China’s M2 money supply was approximately 32.85 trillion USD

Generated SQL

SELECT
    Country,
    M2
FROM imf_data
WHERE Year = 2018
  AND Country IN ('India', 'China')
ORDER BY Country;

Example 2 — Highest Median GDP Growth (2010–2020)

Question

Which country had the highest median GDP growth rate in the last decade?


Pipeline Output

Sending request to Ollama… this may take a minute or two for complex queries.
STATUS: 200
Sending request to Ollama… this may take a minute or two for complex queries.
STATUS: 200


Final Answer
Based on the IMF data, the country with the highest median GDP growth rate from 2010–2020 is Qatar, with a median growth rate of 6.3%.

Generated SQL

SELECT
    country_name,
    AVG(gdp_growth_rate) AS median_gdp_growth_rate
FROM imf_data
WHERE year BETWEEN 2010 AND 2020
GROUP BY country_name
ORDER BY median_gdp_growth_rate DESC
LIMIT 1;



## License
This project is provided *as-is*. Ensure compliance with IMF data usage rules and API terms.
