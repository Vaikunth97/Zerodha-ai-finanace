import os
import streamlit as st
from openai import OpenAI

api_key = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY is not configured.")

client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

def ask_ai(prompt):
    try:
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b:free",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        if not response.choices:
            return "❌ AI did not return any response."

        return response.choices[0].message.content

    except Exception as e:
        return f"❌ AI Error: {e}"