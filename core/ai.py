import anthropic
import streamlit as st


@st.cache_data(show_spinner=False)
def ai_insight(prompt: str, api_key: str) -> str:
    if not api_key:
        return ""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            messages=[{
                "role": "user",
                "content": (
                    "You are a quant finance tutor. In exactly 2 plain-English sentences, "
                    "explain what these results mean for a beginner learning quant trading. "
                    "Be specific about the numbers. No jargon without explanation. "
                    f"Context: {prompt}"
                ),
            }],
        )
        return msg.content[0].text.strip()
    except Exception:
        return ""

