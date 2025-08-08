
import streamlit as st
import pandas as pd
import time
import json
import uuid
from datetime import datetime
from pathlib import Path

APP_TITLE = "Your 401(k) Crystal Ball — Live EO Impact Game"

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
RESP_FILE = DATA_DIR / "responses.csv"
STATE_FILE = DATA_DIR / "state.json"
QUESTIONS_FILE = Path("questions.yaml")

# ---------- Utilities ----------

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    # default state
    state = {
        "session_code": "ABC123",
        "current_q": 0,
        "is_open": True,
        "anonymize": True,
        "title": APP_TITLE
    }
    STATE_FILE.write_text(json.dumps(state, indent=2))
    return state

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def init_responses():
    if not RESP_FILE.exists():
        RESP_FILE.write_text("timestamp,session_code,participant_id,participant_name,question_id,choice\n")

def append_response(session_code, participant_id, participant_name, question_id, choice):
    ts = datetime.utcnow().isoformat()
    line = f"{ts},{session_code},{participant_id},{participant_name},{question_id},{choice}\n"
    with open(RESP_FILE, "a") as f:
        f.write(line)

def load_responses():
    if not RESP_FILE.exists():
        init_responses()
    try:
        df = pd.read_csv(RESP_FILE)
    except Exception:
        init_responses()
        df = pd.read_csv(RESP_FILE)
    return df

def load_questions():
    import yaml
    if QUESTIONS_FILE.exists():
        with open(QUESTIONS_FILE, "r") as f:
            return yaml.safe_load(f)
    # Fallback default questions
    default_yaml = """
title: Your 401(k) Crystal Ball — Live EO Impact Game
rounds:
  - id: adoption
    question: "If the EO is implemented, what % of 401(k) plans will add at least one of the new asset types within 2 years?"
    options: ["<5%", "5–20%", "20–50%", ">50%"]
  - id: beneficiary
    question: "Who benefits most if plans add PE/RE/Crypto exposure?"
    options: ["High earners", "Mass middle", "Near retirees", "No one / negligible"]
  - id: risk
    question: "Which asset type worries you most in a retirement plan context?"
    options: ["Private equity", "Real estate", "Cryptocurrency", "All equally", "None"]
  - id: longterm
    question: "In 10 years, this change will be seen as…"
    options: ["Positive innovation", "Neutral", "Major mistake"]
  - id: hurdles
    question: "Biggest implementation hurdle for plan sponsors?"
    options: ["Fiduciary risk", "Fees", "Liquidity/valuation", "Participant comms", "Recordkeeping ops"]
"""
    import io
    return yaml.safe_load(io.StringIO(default_yaml))

def get_base_url():
    # Best effort base URL for QR/links; presenter can edit.
    # Streamlit cloud or local host; we let user override in UI.
    return st.session_state.get("base_url", "http://localhost:8501")

def autorefresh(seconds=2, key="autoreload"):
    st.experimental_rerun

# ---------- Views ----------


def _safe_get_query_param(name, default=None):
    """Return a lowercased string for the query param, handling both string and list cases."""
    try:
        qp = st.query_params
    except Exception:
        return default
    if qp is None:
        return default
    val = qp.get(name, default)
    # Newer Streamlit returns a string, older returns list
    if isinstance(val, list):
        val = val[0] if val else default
    if isinstance(val, str):
        return val
    return default

def presenter_view():
    st.title("Presenter Console")
    state = load_state()
    questions = load_questions()
    title = st.text_input("Session Title", value=state.get("title", APP_TITLE))
    st.caption("Edit in questions.yaml for permanent changes.")
    state["title"] = title

    col1, col2, col3 = st.columns(3)
    with col1:
        session_code = st.text_input("Session Code", value=state["session_code"])
        state["session_code"] = session_code
    with col2:
        is_open = st.toggle("Accepting responses", value=state["is_open"])
        state["is_open"] = is_open
    with col3:
        anonymize = st.toggle("Anonymize participant names", value=state["anonymize"])
        state["anonymize"] = anonymize

    save_state(state)
    st.write("---")

    base_url = st.text_input("Shareable URL (for QR)", value=get_base_url())
    st.session_state["base_url"] = base_url
    vote_url = f"{base_url}?mode=vote&code={state['session_code']}"
    st.markdown(f"**Participant link:** {vote_url}")
    try:
        import qrcode
        import io
        img = qrcode.make(vote_url)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        st.image(buf.getvalue(), caption="Scan to join")
    except Exception as e:
        st.info("Install `qrcode` package to show QR (pip install qrcode[pil]).")

    # Navigation of questions
    rounds = questions["rounds"]
    st.subheader("Round Control")
    cols = st.columns([3,1,1,1])
    with cols[0]:
        current_idx = st.number_input("Current round index", min_value=0, max_value=len(rounds)-1, value=state["current_q"], step=1)
    with cols[1]:
        if st.button("⟵ Prev", use_container_width=True) and state["current_q"] > 0:
            state["current_q"] -= 1
    with cols[2]:
        if st.button("Next ⟶", use_container_width=True) and state["current_q"] < len(rounds)-1:
            state["current_q"] += 1
    with cols[3]:
        if st.button("Reset Session", type="secondary", use_container_width=True):
            init_responses()
            RESP_FILE.unlink(missing_ok=True)
            init_responses()
            state["current_q"] = 0
    save_state(state)

    # Display current question & live results
    st.write("---")
    st.header(f"Round {state['current_q']+1} of {len(rounds)}")
    q = rounds[state["current_q"]]
    st.subheader(q["question"])
    st.caption("Options: " + " | ".join(q["options"]))

    st.write("### Live Results")
    st.caption("Auto-refresh every ~2 seconds.")
    df = load_responses()

    # Filter by session code & question
    df = df[df["session_code"] == state["session_code"]]
    df_q = df[df["question_id"] == q["id"]]
    if state["anonymize"]:
        df_q = df_q.assign(participant_name="(hidden)")

    if df_q.empty:
        st.info("No responses yet. Ask folks to scan the QR/link!")
    else:
        counts = df_q["choice"].value_counts().reindex(q["options"]).fillna(0).astype(int)
        st.bar_chart(counts)
        with st.expander("See raw responses"):
            st.dataframe(df_q)

    st.write("---")
    st.caption("Tip: For a large room, set your laptop as a hotspot and share the link/QR.")

def vote_view():
    st.title("Vote")
    init_responses()
    state = load_state()
    questions = load_questions()

    code_raw = _safe_get_query_param("code", "")
    code = code_raw or state["session_code"]
    code = st.text_input("Enter Session Code", value=code or state["session_code"])
    if code != state["session_code"]:
        st.warning("Waiting for the correct session code.")
        return

    if not state["is_open"]:
        st.stop()

    # Participant identity (optional)
    if state.get("anonymize", True):
        st.text_input("Your name (optional)", value="", key="participant_name")
    else:
        st.text_input("Your name", value="", key="participant_name", placeholder="e.g., Alex (Acme)")

    # Persist a browser-scoped participant id
    if "participant_id" not in st.session_state:
        st.session_state["participant_id"] = str(uuid.uuid4())

    q = load_questions()["rounds"][state["current_q"]]
    st.header(f"Round {state['current_q']+1}")
    st.subheader(q["question"])
    choice = st.radio("Choose one:", q["options"], index=None)

    if st.button("Submit"):
        if choice is None:
            st.error("Please select an option.")
        else:
            append_response(
                session_code=state["session_code"],
                participant_id=st.session_state["participant_id"],
                participant_name=st.session_state.get("participant_name",""),
                question_id=q["id"],
                choice=choice
            )
            st.success("Response recorded!")
            st.toast("Thanks! Watch the big screen for live results.")

    st.caption("Note: You can change your answer by resubmitting; latest submission counts in analysis.")

def results_only_view():
    st.title("Live Results (Read-Only)")
    state = load_state()
    questions = load_questions()
    q = questions["rounds"][state["current_q"]]

    st.subheader(q["question"])
    st.caption("Auto-refresh every ~2 seconds.")

    df = load_responses()
    df = df[df["session_code"] == state["session_code"]]
    df_q = df[df["question_id"] == q["id"]]
    if df_q.empty:
        st.info("No responses yet.")
    else:
        counts = df_q["choice"].value_counts().reindex(q["options"]).fillna(0).astype(int)
        st.bar_chart(counts)

# ---------- Router ----------

def main():
    st.set_page_config(page_title="401(k) EO Live Game", page_icon="📊", layout="wide")
    init_responses()
    state = load_state()
    questions = load_questions()

    # Tabs or URL param for mode
    mode_raw = _safe_get_query_param("mode", "presenter")
    mode = (mode_raw or "presenter").lower()

    with st.sidebar:
        st.markdown("## Navigation")
        mode = st.radio("Mode", ["presenter", "vote", "results"], index=["presenter", "vote", "results"].index(mode))
        st.markdown("---")
        st.markdown("**Rounds**")
        for i, r in enumerate(questions["rounds"]):
            st.write(f"{i+1}. {r['question']}")

        st.markdown("---")
        st.markdown("**Tips**")
        st.write("- Share the **vote** link/QR.\n- Use a hotspot if venue Wi‑Fi is flaky.\n- Turn on anonymization if needed.")

    if mode == "presenter":
        presenter_view()
    elif mode == "vote":
        vote_view()
    else:
        results_only_view()

if __name__ == "__main__":
    main()
