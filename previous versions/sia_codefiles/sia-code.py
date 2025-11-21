import os
from openai import OpenAI
#pip install openai pandas


# 1. Setup API keys for different models

os.environ["API_KEY"] = "api_key"

# can use a number of different models (below)

# export GOOGLE_API_KEY="gemini_api_key"

# export ANTHROPIC_API_KEY="claude_api_key"

# export OPENAI_API_KEY="openai_api_key"

# from huggingface_hub import InferenceClient

# client = InferenceClient(model="defog/sqlcoder-2")



# System Prompt + Schema
# can test different system prompts to evalute strongest one

SCHEMA_CONTEXT = """
You are a financial data analyst converting natural-language questions
into SQL queries for the IMF International Financial Statistics (IFS) database. 

Follow these rules:
1. Return a syntactically valid SQL query using standard SQL syntax.
2. Only output SQL (no explanations or extra commentary).
3. Base all answers on the provided schema and table structure.
4. Use column names exactly as defined in the schema.
5. When filtering by year or range, use standard date comparison operations.
6. When aggregating data, always include proper GROUP BY clauses.

"""


DATABASE_CONTEXT = """
Database: IMF_International_Financial_Statistics

Schema
Table: imf_ifs
Columns:
- country (TEXT) — Country name
- indicator_code (TEXT) — Unique IMF indicator ID
- indicator_name (TEXT) — Full indicator name (e.g., "GDP, current prices")
- time_period (DATE) — Year or month of observation
- value (FLOAT) — Recorded value of the indicator
- unit (TEXT) — Measurement unit (e.g., "USD", "Percent")
- scale (TEXT) — Scale factor (e.g., "Millions", "Billions")

Example rows:
| country | indicator_code | indicator_name     | time_period | value     | unit | scale  |
|----------|----------------|--------------------|-------------|-----------|------|--------|
| Japan    | NGDP_R_SA_XDC  | GDP, current prices | 2020-01-01 | 5.06e+12  | USD  | Billions |
| Japan    | PCPI_IX        | Consumer Price Index | 2020-01-01 | 103.2     | Index | Base Year=2015 |


"""

# Model Wrapper 
# function that actually calls the model with the prompt + question
# and returns the sql output response

def generate_sql(question, model="llama3-70b-8192"):
    prompt = f"""
    {SCHEMA_CONTEXT}
    {DATABASE_CONTEXT}
    Question: {question}
    SQL Query:
    """

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert text-to-SQL generator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=300,
    )

    sql_output = response.choices[0].message.content.strip()
    return sql_output


# testing the script with sample questions

if __name__ == "__main__":
    example_questions = [
        "What was the inflation rate in Japan in 2020?",
        "Which country had the highest GDP in 2022?",
        "Find countries whose reserves increased faster than their GDP between 2010 and 2020."
    ]

    for q in example_questions:
        sql = generate_sql(q)
        print(f"\n Question: {q}\n SQL:\n{sql}\n{'='*60}")
