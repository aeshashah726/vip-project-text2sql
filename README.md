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

## License
This project is provided *as-is*. Ensure compliance with IMF data usage rules and API terms.
