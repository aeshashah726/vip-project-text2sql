import os
import sqlite3
import pandas as pd
from openai import OpenAI

#############################################
# SETTINGS
#############################################

DB_PATH = "pranati_imf_data.db"

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

# def try_ollama(messages):
#     import requests
#     try:
#         r = requests.post(
#             "http://localhost:11434/v1/chat/completions",
#             json={
#                 "model": "llama3.1:latest",
#                 "messages": messages,
#                 "temperature": 0.2,
#             },
#             timeout=60
#         )
#         print("STATUS:", r.status_code)
#         print("RAW:", r.text[:500])  # debug first 500 chars

#         j = r.json()
#         # debug: see the full parsed JSON structure
#         print("JSON keys:", j.keys())
#         print("First choice keys:", j["choices"][0].keys())
#         return j["choices"][0]["message"]["content"].strip()
#     except Exception as e:
#         print("ERROR:", e)
#         return None

def try_ollama(messages):
    import requests
    import json

    try:
        print("Sending request to Ollama… this may take a minute or two for complex queries.")
        r = requests.post(
            "http://localhost:11434/v1/chat/completions",
            json={
                "model": "llama3.1:latest",
                "messages": messages,
                "temperature": 0.2,
            },
            timeout=180  # increase to 3 minutes
        )

        print("STATUS:", r.status_code)
        if r.status_code != 200:
            print("Server returned error:", r.text)
            return None

        # Safely parse JSON
        try:
            j = r.json()
        except json.JSONDecodeError as e:
            print("JSON parse error:", e)
            print("RAW response:", r.text[:1000])
            return None

        # Check structure
        if "choices" not in j or len(j["choices"]) == 0:
            print("No choices in response. RAW:", r.text[:500])
            return None

        content = j["choices"][0].get("message", {}).get("content", "")
        if not content:
            print("Empty content in response. RAW:", r.text[:500])
            return None

        return content.strip()

    except requests.exceptions.ReadTimeout:
        print("ERROR: Request timed out (increase timeout if needed).")
        return None
    except Exception as e:
        print("ERROR:", e)
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
#litellm
def explain_answer(question, df):
    msg = f"""
You are an IMF financial data analyst. The user asked:

{question}

Here is the raw dataframe of results:

{df.to_string(index=False) if isinstance(df, pd.DataFrame) else df}

Please answer the question in clear English. 
Summarize the results naturally. Show SQL.
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
    q = "Which country had the highest median GDP growth rate in the last decade?"
# What was the GDP for India in 2018?
# What was the inflation rate in China during March 2019?
# What is the most recent recorded foreign reserves for Japan?
# Aggregation / Comparison
# What was the average interest rate in Brazil between 2015 and 2020?
# Which country had the highest median GDP growth rate in the last decade?
# How many consecutive years did Germany experience positive GDP growth?
# Time-Series / Nested
# Compare India and China’s money supply (M2) in 2018.
# For each country, what was the maximum current account deficit between 2010–2020?
    print("\nQuestion:", q)
    print("Answer:")
    print(ask_imf(q))
