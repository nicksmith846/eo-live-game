# Your 401(k) Crystal Ball — Live EO Impact Game

A quick, conference-ready Streamlit app for running a live poll/game about the policy (EO) that would open private equity, real estate, and crypto to 401(k) plans. Attendees vote from their phones; you project real-time results.

## Features
- **Presenter mode**: Control the active round, share a QR code, toggle anonymization, and watch results update live.
- **Vote mode**: Clean, phone-friendly voting screen.
- **Results mode**: A simple live results screen (for a secondary display if desired).
- **Editable questions**: Update `questions.yaml` to change rounds/options.
- **Local CSV storage**: Responses are saved to `data/responses.csv`.

## Quick Start
1. Ensure Python 3.10+ is installed.
2. Create and activate a virtual environment (recommended).
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```

## Using It at the Conference
- Connect your laptop to the projector.
- Open the app in **presenter** mode (default), and set your **Session Code**.
- Share the QR code or the participant link (e.g., `http://YOUR-IP:8501?mode=vote&code=ABC123`).
- Ask attendees to join via their phones and submit answers.
- Use the **Next** button to move through rounds.
- Toggle **Anonymize** if you want to hide names.

> **Tip:** If venue Wi‑Fi is unreliable, create a hotspot from your phone and connect your laptop + attendees to it. Share the local IP shown in your browser (e.g., `http://192.168.1.23:8501`).

## Customizing Questions
Edit `questions.yaml`. Example format:
```yaml
title: Your 401(k) Crystal Ball — Live EO Impact Game
rounds:
  - id: adoption
    question: "If the EO is implemented, what % of 401(k) plans will add at least one of the new asset types within 2 years?"
    options: ["<5%", "5–20%", "20–50%", ">50%"]
  - id: beneficiary
    question: "Who benefits most if plans add PE/RE/Crypto exposure?"
    options: ["High earners", "Mass middle", "Near retirees", "No one / negligible"]
```

## Presenter Controls
- **Session Title/Code**: Appears on the screen and in saved responses.
- **Accepting responses**: Toggle to pause/resume voting.
- **Anonymize participant names**: Hides names in the table and prevents social pressure.

## How Data Is Stored
- Responses are appended to `data/responses.csv` with columns:
  `timestamp, session_code, participant_id, participant_name, question_id, choice`
- Session state (current round, anonymization, etc.) is saved in `data/state.json`.
- To clear data, click **Reset Session** in presenter mode (or delete the `data/` folder).

## Optional: Make It Publicly Reachable
- With a hotspot, sharing your local IP is often enough.
- For remote participants, you can use a tunneling service like Cloudflare Tunnel or ngrok (not required for the conference).

## License
MIT