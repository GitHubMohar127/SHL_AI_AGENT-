import streamlit as st
import requests

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="SHL AI Assessment Agent",
    page_icon="🤖",
    layout="centered"
)

# =========================================================
# TITLE
# =========================================================

st.title("🤖 SHL AI Assessment Agent")

st.markdown("""
AI-powered assessment recommendation system.

You can:
- Recommend assessments
- Compare assessments
- Get hiring test suggestions
""")

# =========================================================
# SESSION STATE
# =========================================================

if "chat_history" not in st.session_state:

    st.session_state.chat_history = []

# =========================================================
# INPUT BOX
# =========================================================

user_query = st.text_input(
    "Enter your query:",
    placeholder="Example: Hiring Java backend developer"
)

# =========================================================
# BUTTON
# =========================================================

if st.button("Submit"):

    if user_query.strip() == "":

        st.warning("Please enter a query.")

    else:

        # Save user message
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_query
        })

        # -------------------------------------------------
        # API CALL
        # -------------------------------------------------

        try:

            with st.spinner("Generating response..."):

                response = requests.post(

                    "http://127.0.0.1:8000/chat",

                    json={
                        "query": user_query
                    }
                )

                data = response.json()

                if data.get("success"):

                    assistant_response = data["response"]

                else:

                    assistant_response = data.get(
                        "error",
                        "Unknown error occurred."
                    )

        except Exception as e:

            assistant_response = f"Connection Error: {str(e)}"

        # Save assistant message
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": assistant_response
        })

# =========================================================
# DISPLAY CHAT HISTORY
# =========================================================

st.markdown("---")

st.subheader("Conversation")

for message in st.session_state.chat_history:

    if message["role"] == "user":

        st.markdown(
            f"""
            <div style="
                background-color:black;
                padding:10px;
                border-radius:10px;
                margin-bottom:10px;
            ">
            <b>You:</b><br>{message['content']}
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            f"""
            <div style="
                background-color:black;
                padding:10px;
                border-radius:10px;
                margin-bottom:10px;
            ">
            <b>Assistant:</b><br>{message['content']}
            </div>
            """,
            unsafe_allow_html=True
        )

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("Example Queries")

    st.markdown("""
### Recommendations
- Hiring Java backend developer
- Need leadership assessment
- Hiring React frontend developer

### Comparisons
- compare: Java 8 vs Java Frameworks
- compare: Python vs Java

### Clarifications
- Need assessment for developer
""")