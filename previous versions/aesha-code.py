import pandas as pd
from openai import OpenAI

# load database table
df = pd.read_csv("my_table.csv")        # pretend this is data
table_text = df.to_csv(index=False)     # reusable table text

# LLM client, add more as needed
client = OpenAI()

# Make reusable system/context prompt
SYSTEM_CONTEXT = f"""
insert system context here
Use ONLY the following table to answer questions:

{table_text}

If the MySQL query can not be created from the table, say "Cannot create MySQL".
Always answer briefly.
"""

def ask_llm(question):
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": SYSTEM_CONTEXT},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content.strip()

# Example usage
question = "question" # sample question
correct_answer = "Australia" # expected answer

llm_answer = ask_llm(question)

print("LLM Answer:", llm_answer)
print("Correct Answer:", correct_answer)
# need to create comparison logic because there can be 1+ correct answers
