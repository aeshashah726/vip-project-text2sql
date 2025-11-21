# IMF Natural-Language Question Answering Pipeline

This project provides an end-to-end workflow to convert IMF Excel tables into a SQLite database and enable natural-language questions using an OpenAI model. The system ingests Excel files, builds a schema summary, generates SQL from natural language, executes the SQL, and returns final model-written answers.

## Features
- Automatic ingestion of all .xlsx files in the `imf_tables/` directory
- SQLite database creation (`imf_data.db`)
- Text-based schema summary for LLM context (`schema_text.txt`)
- Natural-language → SQL → Answer workflow
- Modular scripts for easy modification and expansion

## Repository Structure
.
├── creating_database.py  – Loads Excel files, builds SQLite database, generates schema summary  
├── imf_nlqa.py           – Natural language → SQL → Answer pipeline  
├── run_pipeline.py       – Runs the full workflow end to end  
└── imf_tables/           – Folder where IMF Excel files must be placed  

## Requirements
Python 3.9–3.12 is recommended.

Required packages:
- pandas  
- sqlalchemy  
- openai  
- python-dotenv  

Install them with:
`pip install pandas sqlalchemy openai python-dotenv`

(sqlite3 is included in Python by default)

## Setup

### 1. Add IMF Excel Files
Create a folder and place all IMF .xlsx files inside it:
`imf_tables/`

### 2. Set Your OpenAI API Key
On macOS/Linux:
export OPENAI_API_KEY="your-key-here"

On Windows (PowerShell):
setx OPENAI_API_KEY "your-key-here"

Or create a .env file in the project directory:
OPENAI_API_KEY=your-key-here

## Running the Pipeline

### A. Build the SQLite Database
Run:
`python creating_database.py`

This script will:
- Load all Excel files in imf_tables/  
- Build imf_data.db  
- Generate schema_text.txt (contains table names & column descriptions)

### B. Ask Natural-Language Questions
Run:
`python imf_nlqa.py`

You will be asked:
Enter your question:

The system will:
1. Convert your question into SQL  
2. Execute SQL against imf_data.db  
3. Return the raw SQL results  
4. Ask the model to produce a final narrative answer  

### C. Run Everything Automatically
Run:
`python run_pipeline.py`

This will:
- Build the database if needed  
- Load schema context  
- Ask for a question  
- Generate SQL  
- Execute SQL  
- Return a final LLM answer  

## Customization

### Change the OpenAI Model
Inside imf_nlqa.py, modify:
`model="gpt-4.1`

Other valid options:
gpt-4.1-mini
gpt-4o  
gpt-o3-mini  

### Change the Database Path
In any script, update:
`DB_PATH = "imf_data.db"`

### Add More IMF Tables
Just add more .xlsx files to imf_tables/ and rerun:
`python creating_database.py`

## Troubleshooting

### “No tables found”
Ensure imf_tables/ exists and contains valid Excel files.

### “Database is locked”
Delete the DB and rebuild:
`rm imf_data.db`  
`python creating_database.py`

### Excel parsing issues
Install these engines:
`pip install openpyxl xlrd`

### API key not detected
Check:
`echo $OPENAI_API_KEY`

## License
This project is provided as-is. Ensure compliance with IMF data usage rules and model (OpenAI, etc.) API terms.
