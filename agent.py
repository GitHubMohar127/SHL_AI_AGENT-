import os
import json
import re
from google import genai

from dotenv import load_dotenv

from retriever import (
    search_assessments,
    compare_assessments
)

# =========================================================
# Load Environment Variables
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

# =========================================================
# Configure Gemini
# =========================================================

# genai.configure(api_key=GEMINI_API_KEY)
client = genai.Client(api_key=GEMINI_API_KEY)

# model = genai.GenerativeModel("gemini-2.0-flash")
# model = genai.GenerativeModel("gemini-1.5-pro-latest")
# model = genai.GenerativeModel("gemini-pro")

# =========================================================
# Conversation Memory
# =========================================================

conversation_history = []

# =========================================================
# Intent Detection
# =========================================================

def detect_intent(query):

    query_lower = query.lower()

    # -----------------------------------------------------
    # Comparison Intent
    # -----------------------------------------------------

    if query_lower.startswith("compare:"):
        return "compare"

    # -----------------------------------------------------
    # Recommendation Intent
    # -----------------------------------------------------

    hiring_keywords = [
        "hire",
        "hiring",
        "assessment",
        "test",
        "developer",
        "engineer",
        "manager",
        "leadership",
        "communication",
        "backend",
        "frontend",
        "python",
        "java",
        "candidate",
        "teamwork",
        "software"
    ]

    if any(keyword in query_lower for keyword in hiring_keywords):
        return "recommend"

    # -----------------------------------------------------
    # Refinement Intent
    # -----------------------------------------------------

    refinement_keywords = [
        "more",
        "better",
        "shorter",
        "longer",
        "technical",
        "behavioral",
        "personality"
    ]

    if any(keyword in query_lower for keyword in refinement_keywords):
        return "refine"

    # -----------------------------------------------------
    # Unknown
    # -----------------------------------------------------

    return "unknown"

# =========================================================
# Clarification Logic
# =========================================================

def needs_clarification(query):

    query_lower = query.lower()

    vague_terms = [
        "developer",
        "engineer",
        "assessment",
        "test",
        "candidate",
        "software role"
    ]

    specific_terms = [
        "java",
        "python",
        "sql",
        "backend",
        "frontend",
        "leadership",
        "management",
        "communication",
        "teamwork",
        "sales",
        "cloud",
        "devops",
        "ai"
    ]

    vague = any(term in query_lower for term in vague_terms)

    specific = any(term in query_lower for term in specific_terms)

    return vague and not specific

# =========================================================
# Clarification Response
# =========================================================

def generate_clarification():

    return """
Could you provide more details about the role?

Examples:
- Technology stack (Java, Python, SQL, etc.)
- Experience level
- Technical or behavioral assessment
- Leadership or communication focus
- Backend, frontend, or management role
"""

# =========================================================
# Recommendation Response
# =========================================================

def generate_recommendation_response(query):

    results = search_assessments(query, top_k=3)

    if not results:
        return []

    cleaned_results = []

    for result in results:

        cleaned_item = {
            "name": result.get("name", ""),
            "test_type": result.get("test_type", ""),
            "skills": result.get("skills", []),
            "duration": result.get("duration", ""),
            "description": result.get("description", ""),
            "url": result.get("url", "")
        }

        cleaned_results.append(cleaned_item)

    return cleaned_results

# =========================================================
# Comparison Response
# =========================================================

def generate_comparison_response(query):

    try:

        compare_text = query[len("compare:"):].strip()

        # Split using regex (case insensitive)
        parts = re.split(r"\bvs\b", compare_text, flags=re.IGNORECASE)

        if len(parts) != 2:
            return "Invalid comparison format. Use: compare: A vs B"

        name1 = parts[0].strip()
        name2 = parts[1].strip()

        comparison = compare_assessments(name1, name2)

        return json.dumps(comparison, indent=2, ensure_ascii=False)

    except Exception as e:

        return f"Comparison failed: {str(e)}"

# =========================================================
# Gemini LLM Response
# =========================================================

# =========================================================
# Gemini Response Generation
# =========================================================

def generate_llm_response(user_query, retrieved_data):

    prompt = f"""
You are an SHL assessment recommendation assistant.

STRICT RULES:
- ONLY use retrieved information
- DO NOT hallucinate
- Keep concise and professional

User Query:
{user_query}

Retrieved Data:
{retrieved_data}

Generate a helpful response.
"""

    try:

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )

        return response.text

    except Exception as e:

        print(f"\nGemini Error: {str(e)}\n")

        # =================================================
        # FALLBACK FOR COMPARISON
        # =================================================

        if isinstance(retrieved_data, str):

            return f"""
Comparison Result:

{retrieved_data}
"""

        # =================================================
        # FALLBACK FOR RECOMMENDATIONS
        # =================================================

        elif isinstance(retrieved_data, list):

            fallback = "\nRecommended Assessments:\n"

            for i, item in enumerate(retrieved_data, start=1):

                fallback += f"""
{i}. {item.get('name', 'N/A')}

Type: {item.get('test_type', 'N/A')}

Skills:
{", ".join(item.get('skills', [])) if item.get('skills') else 'N/A'}

Duration:
{item.get('duration', 'N/A')}

Description:
{item.get('description', 'N/A')}

URL:
{item.get('url', 'N/A')}

--------------------------------------------------
"""

            return fallback

        # =================================================
        # UNKNOWN FALLBACK
        # =================================================

        return "Unable to generate response."

# =========================================================
# Main Agent Logic
# =========================================================

def run_agent(query):

    # Save user history
    conversation_history.append({
        "role": "user",
        "content": query
    })

    # -----------------------------------------------------
    # Detect Intent
    # -----------------------------------------------------

    intent = detect_intent(query)

    # -----------------------------------------------------
    # Comparison Intent
    # -----------------------------------------------------

    if intent == "compare":

        raw_response = generate_comparison_response(query)

        final_response = generate_llm_response(
            query,
            raw_response
        )

        return final_response

    # -----------------------------------------------------
    # Clarification Logic
    # -----------------------------------------------------

    if needs_clarification(query):

        return generate_clarification()

    # -----------------------------------------------------
    # Recommendation / Refinement
    # -----------------------------------------------------

    if intent in ["recommend", "refine"]:

        raw_response = generate_recommendation_response(query)

        final_response = generate_llm_response(
            query,
            raw_response
        )

        return final_response

    # -----------------------------------------------------
    # Unknown Intent
    # -----------------------------------------------------

    return """
I can help with:

- SHL assessment recommendations
- Hiring assessment selection
- Leadership/personality assessments
- Assessment comparisons

Examples:
- Hiring Java backend developer
- Need leadership assessment
- compare: Java 8 vs Java Frameworks
"""

# =========================================================
# Interactive CLI Chat
# =========================================================

if __name__ == "__main__":

    print("\n=================================================")
    print("SHL Conversational AI Agent")
    print("=================================================")
    print("Type 'exit' to quit")
    print("=================================================\n")

    while True:

        query = input("You: ").strip()

        if query.lower() == "exit":

            print("\nGoodbye!\n")
            break

        response = run_agent(query)

        print("\nAssistant:\n")
        print(response)
        print("\n")