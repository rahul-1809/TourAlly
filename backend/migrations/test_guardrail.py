import os
from dotenv import load_dotenv
load_dotenv()
from groq import Groq
client = Groq()

sys_prompt = "You are a strict travel safety guardrail. Your job is to classify if the user query is travel-related (e.g., planning a trip, booking flights, hotels, activities, checking weather, or suggesting a budget). Respond ONLY with a JSON object in this format: {\"allowed\": true/false, \"reason\": \"Explanation why it is blocked or allowed\"}."
user_prompt = "Query: Plan a 3-day trip to Paris from London with $1500 budget"

completion = client.chat.completions.create(
    messages=[
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt}
    ],
    model="groq/compound",
    temperature=0.0
)
print("Response from Groq:")
print(completion.choices[0].message.content)
