import csv
import time
import sqlite3
import pandas as pd
import requests


# database config
DB_PATH = "testdata.db"  

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def get_schema():
    """
    Read the actual SQLite schema and format as text for the LLM.
    """
    lines = []
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    for (table,) in tables:
        lines.append(f"TABLE: {table}")
        cursor.execute(f'PRAGMA table_info("{table}")')
        for col in cursor.fetchall():
            col_name = col[1]
            col_type = col[2]
            lines.append(f"- {col_name} ({col_type})")
        lines.append("")

    return "\n".join(lines)

SCHEMA = get_schema()

def run_sql(query: str):
    """
    Execute SQL on the benchmark DB and return either a DataFrame or an error string.
    """
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        return f"SQL ERROR: {e}"


# ollama chat client
def call_ollama_chat(model_name: str, messages: list, temperature: float = 0.0, timeout: int = 60):
    """
    Call a local Ollama chat completion endpoint and return the message content.
    """
    try:
        r = requests.post(
            "http://localhost:11434/v1/chat/completions",
            json={
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
            },
            timeout=timeout,
        )
        if r.status_code != 200:
            return f"LLM ERROR: HTTP {r.status_code} - {r.text}"

        content = r.json()["choices"][0]["message"]["content"]
        return content
    except Exception as e:
        return f"LLM ERROR: {e}"


def clean_sql_output(text: str) -> str:
    """
    If the model wraps SQL in ``` or adds commentary, try to strip it down to raw SQL.
    """
    if text is None:
        return ""

    sql = text.strip()

    if "```" in sql:
        parts = sql.split("```")
        if len(parts) >= 3:
            sql = parts[1]
        else:
            sql = parts[-1]
        sql = sql.strip()

    return sql


# models and prompts

# local models (all via Ollama)
OLLAMA_MODELS = [
    "llama3.1:latest",
    "qwen2:7b",
    "mistral-nemo:latest",
    "deepseek-r1:latest",
]

ALL_MODELS = OLLAMA_MODELS  

PROMPT_TYPES = ["minimal", "schema_aware", "guardrails", "few_shot"]

BENCHMARK_QUESTIONS = [
    "What was India's CPI in 2020?",
    "Which country had the highest GDP in 2019?",
    "Compare China and Japan's money supply (M2) in 2010.",
    "List the top 5 countries by GDP in 2022.",
    "How did Brazil's inflation change between 2010 and 2020?",
]


def build_messages(prompt_type: str, question: str) -> list:
    """
    Build (system, user) messages for a given prompt style and question.
    Every one *can* see SCHEMA (that’s what we’re testing).
    """

    if prompt_type == "minimal":
        system_msg = (
            "You are a text-to-SQL generator for a SQLite IMF database. "
            "Return ONLY SQL. No explanation, no commentary, no backticks."
        )
        user_msg = f"Question: {question}\nSQL:"

    elif prompt_type == "schema_aware":
        system_msg = (
            "You are a text-to-SQL generator for a SQLite IMF database.\n\n"
            "Here is the database schema:\n"
            f"{SCHEMA}\n\n"
            "Return ONLY SQL. Use only the tables and columns shown. "
            "Do not invent tables or columns. No commentary."
        )
        user_msg = f"Question: {question}\nSQL:"

    elif prompt_type == "guardrails":
        system_msg = (
            "You are a text-to-SQL generator for a SQLite IMF database.\n\n"
            "Schema:\n"
            f"{SCHEMA}\n\n"
            "Rules:\n"
            "- Return ONLY SQL, nothing else.\n"
            "- Use ONLY tables and columns from the schema.\n"
            "- DO NOT invent tables.\n"
            "- DO NOT invent columns.\n"
            "- Dates are stored as TEXT.\n"
            "- Prefer simple SELECT statements without CTEs unless necessary.\n"
        )
        user_msg = f"User question: {question}\nWrite the SQL query only."

    elif prompt_type == "few_shot":
       
        system_msg = (
            "You are a text-to-SQL generator for a SQLite IMF database.\n\n"
            "Here is the database schema:\n"
            f"{SCHEMA}\n\n"
            "Use only the tables and columns shown. Return ONLY SQL.\n"
        )
        user_msg = f"""
Here are examples of how you should respond:

Q: What was India's CPI in 2020?
A: SELECT value
   FROM cpi
   WHERE country = 'India' AND time_period = '2020';

Q: Which country had the highest GDP in 2015?
A: SELECT country
   FROM gdp
   WHERE time_period = '2015'
   ORDER BY value DESC
   LIMIT 1;

Now answer this question with a single SQL query (no explanation):

{question}
SQL:
""".strip()

    else:
        system_msg = (
            "You are a text-to-SQL generator for a SQLite IMF database. "
            "Return ONLY SQL."
        )
        user_msg = f"Question: {question}\nSQL:"

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]


# benchmark logic
def generate_sql(model_name: str, question: str, prompt_type: str) -> str:
    """
    Build messages for given prompt_type, call Ollama, return cleaned SQL string.
    """
    messages = build_messages(prompt_type, question)
    raw = call_ollama_chat(model_name, messages)
    sql = clean_sql_output(raw)
    return sql


def benchmark_one(model_name: str, prompt_type: str, question: str) -> dict:
    """
    Run one (model, prompt_type, question) triple:
        - Generate SQL
        - Execute SQL
        - Record success/rows/error/latency
    """
    start = time.time()

    sql = generate_sql(model_name, question, prompt_type)
    df_or_error = run_sql(sql)

    success = isinstance(df_or_error, pd.DataFrame)
    rows = len(df_or_error) if success else 0
    error = None if success else str(df_or_error)

    end = time.time()

    return {
        "model": model_name,
        "prompt_type": prompt_type,
        "question": question,
        "sql": sql,
        "success": success,
        "rows": rows,
        "error": error,
        "latency_sec": round(end - start, 3),
    }


def run_benchmark(output_csv: str = "benchmark_results.csv"):
    """
    Evaluate every model × prompt × question and save results to CSV.
    """
    results = []

    for model in ALL_MODELS:
        for prompt_type in PROMPT_TYPES:
            for question in BENCHMARK_QUESTIONS:
                print(f"Testing {model} | {prompt_type} | {question}")
                result = benchmark_one(model, prompt_type, question)
                results.append(result)

    if not results:
        print("No results collected; something went wrong.")
        return

    fieldnames = list(results[0].keys())
    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nBenchmark complete → saved to {output_csv}")


if __name__ == "__main__":
    run_benchmark()
   