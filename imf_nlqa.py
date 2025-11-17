import os
import sqlite3
import pandas as pd
from openai import OpenAI

#############################################
# SETTINGS
#############################################

DB_PATH = "imf_data.db"

# FORCE OPENAI OFF (no more quota errors)
os.environ["OPENAI_API_KEY"] = ""

#############################################
# DATABASE CONNECTION + SCHEMA
#############################################

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def get_schema():
    out = []
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    for (table,) in tables:
        out.append(f"TABLE: {table}")
        # QUOTED TABLE NAME (IMPORTANT)
        cursor.execute(f'PRAGMA table_info("{table}")')
        for col in cursor.fetchall():
            out.append(f"- {col[1]} ({col[2]})")
        out.append("")
    return "\n".join(out)

SCHEMA = get_schema()

#############################################
# OLLAMA CLIENT ONLY (FREE + LOCAL)
#############################################

def try_ollama(messages):
    import requests
    try:
        r = requests.post(
            "http://localhost:11434/v1/chat/completions",
            json={
                "model": "llama3.1:latest",  # <-- FIXED MODEL NAME
                "messages": messages,
                "temperature": 0.2,
            },
            timeout=60
        )
        # Optional debug:
        # print("STATUS:", r.status_code)
        # print("RAW:", r.text[:300])

        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        return None
    except Exception:
        return None

#############################################
# ASK MODEL
#############################################

def ask_llm(messages):
    # ALWAYS use Ollama (OpenAI disabled)
    ans = try_ollama(messages)
    if ans:
        return ans
    return "The assistant could not access Ollama."

#############################################
# SQL GENERATOR (HIDDEN FROM USER)
#############################################

def gen_sql(question):
    prompt = f"""
You are an expert IMF analyst. You have access to a SQLite database with this schema:

{SCHEMA}

Your job:
1. Interpret the user's question.
2. Write ONLY the SQL query needed to answer it.
3. Use correct table + column names.
4. No commentary. No backticks. SQL ONLY.
    """

    messages = [
        {"role": "system", "content": "You generate SQL queries for IMF data."},
        {"role": "user", "content": prompt},
        {"role": "user", "content": f"Question: {question}\nSQL:"}
    ]

    sql = ask_llm(messages)
    return sql.strip()

#############################################
# RUN SQL
#############################################

def run_sql(query):
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        return f"SQL ERROR: {e}"

#############################################
# EXPLAIN RESULTS IN ENGLISH
#############################################

def explain_answer(question, df):
    msg = f"""
You are an IMF financial data analyst. The user asked:

{question}

Here is the raw dataframe of results:

{df.to_string(index=False) if isinstance(df, pd.DataFrame) else df}

Please answer the question in clear English. 
Summarize the results naturally. Do not show SQL.
    """

    messages = [
        {"role": "system", "content": "You summarize IMF data professionally."},
        {"role": "user", "content": msg}
    ]

    return ask_llm(messages)

#############################################
# MAIN PIPELINE — NL → SQL → EXECUTE → EXPLAIN
#############################################

def ask_imf(question):
    sql = gen_sql(question)
    df = run_sql(sql)
    answer = explain_answer(question, df)
    return answer

#############################################
# DEMO
#############################################

if __name__ == "__main__":
    q = "Compare India and China’s money supply (M2) in 2018."
    print("\nQuestion:", q)
    print("Answer:")
    print(ask_imf(q))
