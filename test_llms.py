import csv
import time
import pandas as pd
import os
import sqlite3
# importing existing pipeline scripts
from imf_nlqa import gen_sql as gen_sql_ollama, run_sql as run_sql_ollama
#from run_imf_sql_pipeline import generate_sql as gen_sql_openai, run_sql as run_sql_openai

# os.environ["OPENAI_API_KEY"] = 
DB_PATH = "imf_data.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# loading real IMF schema directly from saved database 
def get_schema():
    schema_lines = []

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    for (table,) in tables:
        schema_lines.append(f"TABLE: {table}")

        cursor.execute(f'PRAGMA table_info("{table}")')
        cols = cursor.fetchall()

        for col in cols:
            col_name = col[1]
            col_type = col[2]
            schema_lines.append(f"- {col_name} ({col_type})")

        schema_lines.append("")  

    return "\n".join(schema_lines)

SCHEMA_CONTEXT = get_schema()




# MODEL DEFINITIONS

# Local models (Ollama)
OLLAMA_MODELS = [
    "llama3.1:latest",
    "llama3.1:latest",
    "qwen2:7b",
    "mistral-nemo:latest",
    "phi3:latest",
    "deepseek-r1:latest",
]

# # OpenAI models
# OPENAI_MODELS = [
#     "gpt-4o-mini",
#     "gpt-4o",
# ]



# All models to test
ALL_MODELS = OLLAMA_MODELS 
# + OPENAI_MODELS


# prompt variants
PROMPT_TEMPLATES = {
    "minimal": "Return only SQL.",
    "schema_aware": (
        "You are a text-to-SQL generator. Use the schema:\n\n"
        f"{SCHEMA_CONTEXT}\n\n"
        "Return ONLY SQL. Do not invent tables."
    ),
    "guardrails": (
        "Return ONLY SQL.\n"
        "Follow these rules:\n"
        "- Use ONLY the tables and columns listed below.\n"
        "- DO NOT invent tables.\n"
        "- DO NOT invent columns.\n"
        "- Dates are TEXT.\n\n"
        f"{SCHEMA_CONTEXT}"
    ),
    "few_shot": """
You are a text-to-SQL generator. Use this schema:\n
Example:
Q: What was India's CPI in 2020?
SQL: SELECT value FROM cpi WHERE country='India' AND time_period='2020';

Example:
Q: What was China's GDP in 2015?
SQL: SELECT value FROM gdp WHERE country='China' AND time_period='2015';

Now return SQL for the user's question.
""",
}


# benchmark questions (add entire list later)
BENCHMARK_QUESTIONS = [
    "What was India's CPI in 2020?",
    "Which country had the highest GDP in 2019?",
    "Compare China and Japan's money supply (M2) in 2010.",
    "List the top 5 countries by GDP in 2022.",
    "How did Brazil's inflation change between 2010 and 2020?",
]


# model routing
def generate_sql(model_name, question, prompt_type):
    """
    Routes SQL generation to the correct script depending on model.
    Adds custom prompt templates.
    """

    prompt_template = PROMPT_TEMPLATES[prompt_type]
    full_question = f"{prompt_template}\n\nQuestion: {question}"

    if model_name in OLLAMA_MODELS:
        # using imf_nlqa.py's pipeline for local Llama via Ollama
        # gen_sql_ollama(question) only takes question, so prepend prompt variant
        return gen_sql_ollama(full_question)

    # if model_name in OPENAI_MODELS:
    #     # Use script_3's OpenAI SQL generator
    #     return gen_sql_openai(full_question, model=model_name)

    raise ValueError(f"Unknown model: {model_name}")

def execute_sql(model_name, sql):
    """
    Use appropriate run_sql depending on backend.
    """
    if model_name in OLLAMA_MODELS:
        return run_sql_ollama(sql)

    # if model_name in OPENAI_MODELS:
    #     return run_sql_openai(sql)

    raise ValueError(f"Unknown model: {model_name}")


# benchmarking function
def benchmark_one_question(model_name, prompt_type, question):
    """
    Returns a dict of results for one (model, prompt, question) combination.
    """

    start = time.time()

    # 1. generating SQL
    sql = generate_sql(model_name, question, prompt_type)

    # 2. executing SQL
    df = execute_sql(model_name, sql)

    # measure of success / error
    success = isinstance(df, pd.DataFrame)
    rows = len(df) if success else 0
    error = None if success else str(df)

    end = time.time()

    # output shown in saved csv
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

# running full benchmark
def run_benchmark(output_csv="benchmark_results.csv"):
    """
    Evaluates every model × prompt × question and saves results.
    """

    results = []

    for model in ALL_MODELS:
        for prompt_type in PROMPT_TEMPLATES.keys():
            for question in BENCHMARK_QUESTIONS:
                print(f"Testing {model} | {prompt_type} | {question}")
                result = benchmark_one_question(model, prompt_type, question)
                results.append(result)

    # saving output as benchmark_results.csv
    keys = results[0].keys()
    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nBenchmark complete → saved to {output_csv}")


if __name__ == "__main__":
    run_benchmark()
