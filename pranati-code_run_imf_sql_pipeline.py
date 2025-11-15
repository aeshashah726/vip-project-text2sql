import os
os.environ["OPENAI_API_KEY"] = "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"
import sqlite3
import pandas as pd
from openai import OpenAI

###########################################
# 0. Set API Key
###########################################
os.environ["OPENAI_API_KEY"] = "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"   # <--- ADD YOUR KEY HERE
###########################################
# 1. Connect to your existing IMF database
###########################################

DB_PATH = "imf_data.db"   # path to your existing DB
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

###########################################
# 2. Extract schema dynamically (REAL schema)
###########################################

def get_schema():
    output = []

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    for (table,) in tables:
        output.append(f"TABLE: {table}")

        # FIX: quote table names (handles hyphens)
        cursor.execute(f'PRAGMA table_info("{table}")')
        cols = cursor.fetchall()

        for col in cols:
            col_name = col[1]
            col_type = col[2]
            output.append(f"- {col_name} ({col_type})")

        output.append("")  # newline

    return "\n".join(output)

# LOAD SCHEMA HERE
SCHEMA_CONTEXT = get_schema()

###########################################
# 3. LLM Client Setup
###########################################

client = OpenAI()

SYSTEM_PROMPT = f"""
You are an IMF text-to-SQL generator for a SQLite database.

ONLY output SQL. No explanations.

Use this schema:

{SCHEMA_CONTEXT}

Rules:
- Use ONLY table/column names shown.
- Dates in SQLite are TEXT, formatted: YYYY or YYYY-MM or YYYY-MM-DD.
- Never invent tables or columns.
"""

###########################################
# 4. LLM → SQL generator
###########################################

def generate_sql(question, model="gpt-4o-mini"):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        temperature=0.0,
        max_tokens=300,
    )
    sql = response.choices[0].message.content.strip()
    return sql

###########################################
# 5. Run SQL on your existing DB
###########################################

def run_sql(query):
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        return f"SQL ERROR: {e}"

###########################################
# 6. Demo: try running a question
###########################################

if __name__ == "__main__":
    question = "Which country had the highest GDP in 2020?"

    sql = generate_sql(question)
    print("\nLLM-Generated SQL:")
    print(sql)

    result = run_sql(sql)
    print("\nQuery Result:")
    print(result)
