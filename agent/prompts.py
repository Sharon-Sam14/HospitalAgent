"""
LLM prompt templates for the triage agent.
All prompts are plain strings; format them with .format(**kwargs) before use.
"""

# ── Ward classification prompt ────────────────────────────────────────────────
WARD_CLASSIFICATION_PROMPT = """\
You are a hospital triage AI. Your only job is to classify a patient's symptoms into one of three wards.

Available wards:
- emergency     : Life-threatening conditions, severe physical trauma, acute cardiac/respiratory events
- mental_health : Mental health crises, psychological distress, psychiatric symptoms
- general       : All other conditions — routine illnesses, mild injuries, chronic condition management

Patient query: "{query}"
Patient age  : {age}
Patient gender: {gender}

Instructions:
1. Return ONLY a JSON object with exactly two keys: "ward" and "reasoning".
2. "ward" must be one of: emergency, mental_health, general (lowercase only).
3. "reasoning" must be a single concise sentence (max 30 words) explaining why.
4. Do NOT add any text outside the JSON object.

Example output:
{{"ward": "general", "reasoning": "Patient reports mild fever and sore throat, consistent with a common cold."}}
"""

# ── Age normalisation prompt (used only when regex fails) ────────────────────
AGE_PARSE_PROMPT = """\
Extract a single integer age from the following text. 
Return ONLY the integer number and nothing else.
If you cannot determine an age, return 0.

Text: "{raw_age}"
"""
