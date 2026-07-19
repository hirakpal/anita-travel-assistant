import sys
import json
from urllib.parse import urlencode, quote
import streamlit as st
import streamlit.components.v1 as components

# Must be the very first Streamlit command in the script.
st.set_page_config(page_title="ANITA — Boarding Pass", page_icon="🎫", layout="wide")

from utils.audit_trail import (
    log_step, get_recent_entries, get_log_file_text, format_entries_as_text,
    get_recent_network_entries, get_network_log_file_text, format_network_entries_as_text,
)

# Imported first and wrapped in try/except so an import-time crash (missing
# package, bad env var, etc.) shows its full traceback directly on the page
# instead of only in Streamlit Cloud's "Manage app" logs, which aren't
# always available to us.
log_step("startup:import_core_modules", "start")
try:
    from orchestrator.anita import ANITA
    from utils.cache import get_cache_stats
    from utils.semantic_cache import get_semantic_cache_stats
    from utils.prompt_cache import get_prompt_cache_stats
    log_step("startup:import_core_modules", "success")
except Exception as e:
    log_step("startup:import_core_modules", "error", error=e)
    st.error("🚨 Startup failed while importing core modules.")
    st.exception(e)
    with st.expander("📋 Audit trail (this run)", expanded=True):
        st.code(format_entries_as_text(get_recent_entries()) or "(empty)")
    with st.expander("📋 Audit trail (persisted log file, across reruns)"):
        st.code(get_log_file_text())
    st.stop()

# Avoid UnicodeEncodeError when agents print emoji on Windows consoles (cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Secure API key from secrets
log_step("startup:read_secrets", "start")
try:
    API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
    log_step("startup:read_secrets", "success")
except Exception as e:
    log_step("startup:read_secrets", "error", error=e)
    st.error("🚨 Startup failed while reading st.secrets['GOOGLE_MAPS_API_KEY'] — is it set in the app's Secrets?")
    st.exception(e)
    with st.expander("📋 Audit trail (this run)", expanded=True):
        st.code(format_entries_as_text(get_recent_entries()) or "(empty)")
    st.stop()

# ---------------- Theme: "Boarding Pass" — kraft ticket stock, postal red, stamp green ----------------
THEME_CSS = """
:root {
  --ticket-bg: #e7dcc2;
  --ticket-paper: #f2e9d3;
  --ticket-ink: #22201a;
  --ticket-muted: #6c6350;
  --ticket-line: #c9bb95;
  --ticket-accent: #c23b2e;
  --ticket-stamp: #2f6b4f;
}

html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
  background: var(--ticket-bg) !important;
  color: var(--ticket-ink);
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stBottom"], [data-testid="stBottomBlockContainer"],
[data-testid="stChatInputContainer"], [data-testid="stChatInput"] {
  background: var(--ticket-bg) !important;
}
[data-testid="stChatInputContainer"] { border-top: 2px dashed var(--ticket-line) !important; }
/* Streamlit wraps stChatInputTextArea in a couple of unlabeled divs that
   carry their own dark background — caught these via live DOM inspection
   rather than guessing, since their class names are build-hashed and not
   stable across versions. Scoped to the bottom bar only. */
[data-testid="stBottomBlockContainer"] div:has(> [data-testid="stChatInputTextArea"]),
[data-testid="stBottomBlockContainer"] div:has(textarea) {
  background: var(--ticket-paper) !important;
}
[data-testid="stChatInputTextArea"] { background: transparent !important; color: var(--ticket-ink) !important; }
/* Serif body copy — scoped to actual text containers only, never to icon-font
   elements (Streamlit renders its arrows/chevrons as icon-font ligatures on
   bare <span>/<label> tags; a blanket font-family override there breaks
   those glyphs into literal text like "arrow_right"). */
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
[data-testid="stCaptionContainer"], [data-testid="stText"],
.stTextInput input, .stTextArea textarea {
  font-family: Georgia, "Iowan Old Style", "Palatino Linotype", "Times New Roman", serif;
}

h1, h2, h3, .stApp [data-testid="stMarkdownContainer"] h1,
.stApp [data-testid="stMarkdownContainer"] h2, .stApp [data-testid="stMarkdownContainer"] h3 {
  font-family: -apple-system, "Segoe UI", Arial, sans-serif !important;
  font-weight: 800 !important;
  letter-spacing: 0.02em;
  color: var(--ticket-ink) !important;
}

/* Sidebar — ticket stub */
[data-testid="stSidebar"] {
  background: var(--ticket-paper);
  border-right: 2px dashed var(--ticket-line);
}
[data-testid="stSidebar"] * { color: var(--ticket-ink); }

/* Buttons — rubber-stamp style */
.stButton > button, .stDownloadButton > button {
  background: var(--ticket-paper);
  color: var(--ticket-accent);
  border: 2px solid var(--ticket-accent) !important;
  border-radius: 4px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .06em;
  font-size: 12.5px;
  padding: 8px 18px;
  transition: transform .12s ease, background .12s ease, color .12s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  background: var(--ticket-accent);
  color: var(--ticket-paper) !important;
  transform: rotate(-1deg);
}
button[kind="primary"], [data-testid="baseButton-primary"] {
  background: var(--ticket-stamp) !important;
  color: var(--ticket-paper) !important;
  border: 2px solid var(--ticket-stamp) !important;
}
button[kind="primary"]:hover, [data-testid="baseButton-primary"]:hover {
  background: #244f3a !important;
  border-color: #244f3a !important;
}

/* Expanders — ticket cards */
[data-testid="stExpander"] {
  background: var(--ticket-paper);
  border: 1px solid var(--ticket-line) !important;
  border-radius: 3px;
  margin-bottom: 10px;
}
[data-testid="stExpander"] summary, [data-testid="stExpander"] p {
  color: var(--ticket-ink) !important;
  font-weight: 600;
}

/* Tabs — ticket divider */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
  border-bottom: 2px solid var(--ticket-line);
  gap: 4px;
}
[data-testid="stTabs"] button {
  font-family: -apple-system, "Segoe UI", Arial, sans-serif !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  font-size: 12px;
  letter-spacing: .05em;
  color: var(--ticket-muted) !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
  color: var(--ticket-accent) !important;
  border-bottom: 3px solid var(--ticket-accent) !important;
}

/* Chat */
[data-testid="stChatMessage"] {
  background: var(--ticket-paper);
  border: 1px solid var(--ticket-line);
  border-radius: 6px;
}
[data-testid="stChatInput"] textarea {
  background: var(--ticket-paper) !important;
  border: 1px solid var(--ticket-line) !important;
  color: var(--ticket-ink) !important;
}

/* Metrics — ticket-stub numbers */
[data-testid="stMetricValue"] {
  color: var(--ticket-accent) !important;
  font-family: -apple-system, "Segoe UI", Arial, sans-serif !important;
  font-weight: 800 !important;
}
[data-testid="stMetricLabel"] {
  color: var(--ticket-muted) !important;
  text-transform: uppercase;
  font-size: 11px;
  letter-spacing: .06em;
}

/* Alerts */
.stAlert { border-radius: 3px; }

/* Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
  background: var(--ticket-paper) !important;
  border: 1px solid var(--ticket-line) !important;
  color: var(--ticket-ink) !important;
}

/* Dividers */
hr { border-color: var(--ticket-line) !important; }

/* Masthead banner */
.boarding-pass-header {
  display: flex;
  background: var(--ticket-paper);
  border: 1px solid var(--ticket-line);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 22px;
}
.bp-main {
  flex: 1;
  padding: 18px 24px;
}
.bp-main .eyebrow {
  font-family: -apple-system, "Segoe UI", Arial, sans-serif;
  font-size: 11px;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--ticket-muted);
  margin-bottom: 6px;
}
.bp-main .title {
  font-family: -apple-system, "Segoe UI", Arial, sans-serif;
  font-weight: 800;
  font-size: 26px;
  letter-spacing: .01em;
  color: var(--ticket-ink);
  margin-bottom: 4px;
}
.bp-main .sub {
  font-family: Georgia, serif;
  font-size: 14.5px;
  color: var(--ticket-muted);
}
.bp-stub {
  width: 150px;
  border-left: 2px dashed var(--ticket-line);
  padding: 18px 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: #ece0c4;
}
.bp-stub .rot {
  writing-mode: vertical-rl;
  font-family: -apple-system, "Segoe UI", Arial, sans-serif;
  font-size: 10px;
  letter-spacing: .16em;
  color: var(--ticket-muted);
  text-transform: uppercase;
}
.bp-stub .code {
  font-family: ui-monospace, "SF Mono", Consolas, monospace;
  font-size: 11px;
  color: var(--ticket-stamp);
  font-weight: 700;
}
"""
st.markdown(f"<style>{THEME_CSS}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="boarding-pass-header">
  <div class="bp-main">
    <div class="eyebrow">Boarding Pass · AI Travel Concierge</div>
    <div class="title">✈️ ANITA</div>
    <div class="sub">Your itinerary, coordinated by nine specialist agents — grounded in real reviews, real transcripts, real maps.</div>
  </div>
  <div class="bp-stub">
    <span class="rot">ANITA · TRIP</span>
    <span class="code">PNR 4B7Q1</span>
  </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    with st.expander("📋 Audit Trail"):
        st.caption("Every startup/pipeline step this run, for diagnosing issues without Cloud logs.")
        if st.button("Refresh"):
            st.rerun()

        tab_steps, tab_network = st.tabs(["Steps", "Network"])

        with tab_steps:
            st.code(format_entries_as_text(get_recent_entries()) or "(empty)")
            st.download_button(
                "Download persisted log file",
                data=get_log_file_text(),
                file_name="audit_trail.log",
                mime="text/plain",
                key="download_steps_log",
            )

        with tab_network:
            st.caption("Request/response between agents and Gemini/Pinecone — what was sent, what came back, cache hits, and timing.")
            network_entries = get_recent_network_entries()
            if not network_entries:
                st.info("No network calls recorded yet.")
            else:
                # Streamlit doesn't allow nesting an expander inside another
                # expander (this panel is already one), so each call is a
                # plain divided section instead of its own expander.
                for entry in reversed(network_entries):
                    icon = "💾" if entry.get("cache_hit") else ("❌" if entry.get("error") else "🌐")
                    label = f"{icon} **{entry['ts']} — {entry['service']}**"
                    if entry.get("duration_ms") is not None:
                        label += f" ({entry['duration_ms']} ms)"
                    st.markdown(label)
                    st.caption("Request")
                    st.code(entry.get("request", ""))
                    if entry.get("error"):
                        st.caption("Error")
                        st.code(entry["error"])
                    elif "response" in entry:
                        st.caption("Response")
                        st.code(entry["response"])
                    st.divider()
            st.download_button(
                "Download persisted network log file",
                data=get_network_log_file_text(),
                file_name="audit_network.log",
                mime="text/plain",
                key="download_network_log",
            )

# Mode toggle (only Online and Demo)
mode = st.radio("Select Mode", ["Online", "Demo"])

# ---------------- Helper: Google Maps Embed ----------------
def show_map(origin, destination, waypoints=None):
    if mode == "Online":
        if not origin or not destination:
            st.info("Trip Map unavailable — origin or destination missing.")
            return
        # Every component must be URL-encoded: place names contain spaces and
        # commas (e.g. "Fatehabad Road, Agra") which Google Maps' Embed API
        # rejects as "Unexpected parameter" if sent raw.
        params = {"key": API_KEY, "origin": origin, "destination": destination}
        if waypoints and len(waypoints) > 0:
            wp_str = "|".join(w for w in waypoints if w)
            if wp_str:
                params["waypoints"] = wp_str
        maps_url = "https://www.google.com/maps/embed/v1/directions?" + urlencode(params, quote_via=quote)
        st.markdown(f"""
            <iframe width="100%" height="400" frameborder="0" style="border:0"
            src="{maps_url}" allowfullscreen></iframe>
        """, unsafe_allow_html=True)
    elif mode == "Demo":
        st.success(f"🎬 Demo Mode: Simulated route {origin} → {destination} with waypoints {waypoints}")

# ---------------- Helper: Google Maps with individually pinned locations ----------------
def show_pin_map(locations, height=420):
    """
    locations: list of {"label": str, "query": str} — query is geocoded
    client-side (Maps JavaScript API + Geocoder) and dropped as a labeled
    pin, so each hotel/activity/restaurant shows up as its own correctly
    placed marker instead of a single directions route between two points.
    """
    locations = [loc for loc in locations if loc.get("query")]
    if mode == "Demo":
        if locations:
            st.success("🎬 Demo Mode: pins for " + ", ".join(loc["label"] for loc in locations))
        return
    if not locations:
        st.info("No locations to show on the map yet.")
        return

    locations_json = json.dumps(locations)
    html = f"""
        <div id="anita-pin-map" style="width:100%;height:{height}px;border-radius:8px;"></div>
        <script>
          function initAnitaPinMap() {{
            var locations = {locations_json};
            var map = new google.maps.Map(document.getElementById("anita-pin-map"), {{
              zoom: 12, center: {{lat: 20.5937, lng: 78.9629}}
            }});
            var geocoder = new google.maps.Geocoder();
            var bounds = new google.maps.LatLngBounds();
            var remaining = locations.length;
            if (remaining === 0) return;
            locations.forEach(function(loc) {{
              geocoder.geocode({{ address: loc.query }}, function(results, status) {{
                remaining -= 1;
                if (status === "OK" && results[0]) {{
                  var pos = results[0].geometry.location;
                  new google.maps.Marker({{ map: map, position: pos, title: loc.label }});
                  bounds.extend(pos);
                }}
                if (remaining === 0 && !bounds.isEmpty()) {{ map.fitBounds(bounds); }}
              }});
            }});
          }}
        </script>
        <script src="https://maps.googleapis.com/maps/api/js?key={API_KEY}&callback=initAnitaPinMap" async defer></script>
    """
    components.html(html, height=height + 10)

# ---------------- Helper: Suggestion Card ----------------
def suggestion_card(icon, title, price, rating, popularity, distance=None, duration=None, cuisine=None):
    st.markdown(f"""
    {icon} **{title}**
    💰 Price: {price}
    ⭐ Popularity: {popularity} (Rating: {rating})
    {f"🚶 Distance: {distance} | ⏱️ Time: {duration}" if distance and duration else ""}
    {f"🍴 Cuisine: {cuisine}" if cuisine else ""}
    """)

# ---------------- Helper: selection checkbox (add/remove from itinerary) ----------------
def selection_checkbox(key, label="Include in my itinerary"):
    col_check, col_card = st.columns([1, 11])
    with col_check:
        included = st.checkbox("", value=True, key=key, label_visibility="collapsed")
    return included, col_card

# ---------------- Helper: Interactive Cards (click to reveal traveler-DNA details) ----------------
def hotel_card(h, idx):
    name = h.get("name", "Unknown")
    key = f"sel_hotel_{idx}_{name}"
    included, col_card = selection_checkbox(key)
    with col_card:
        if "raw_output" in h or "error" in h:
            suggestion_card("🏨", name, h.get("price", "N/A"), h.get("rating", "N/A"), h.get("popularity", ""))
            return
        with st.expander(f"🏨 {name} — {h.get('price', 'N/A')} · ⭐ {h.get('rating', 'N/A')}{'' if included else ' (excluded)'}"):
            if h.get("highlights"):
                st.write(f"✨ {h['highlights']}")
            room_bits = [b for b in [h.get("room_type"), h.get("bed_size"), h.get("style")] if b]
            if room_bits:
                st.write(f"🛏️ **Room:** {' · '.join(room_bits)}")
            if h.get("amenities"):
                st.write(f"🧳 **Amenities:** {', '.join(h['amenities'])}")
            if h.get("review_summary"):
                st.write(f"📝 **Guest reviews:** {h['review_summary']}")
            if h.get("distances"):
                st.write("📍 **Distance to key spots:**")
                for d in h["distances"]:
                    st.write(f"- {d.get('landmark', '')}: {d.get('distance', '')}")
            if h.get("traveler_summary"):
                st.write("📺 **What travelers say** (Google reviews + YouTube):")
                for point in h["traveler_summary"]:
                    st.write(f"- {point}")
            if h.get("fit"):
                st.info(f"✅ **Why this fits you:** {h['fit']}")

def food_card(f, cuisine_filter, idx):
    name = f.get("name", "Restaurant")
    key = f"sel_food_{idx}_{name}"
    included, col_card = selection_checkbox(key)
    with col_card:
        if "raw_output" in f or "error" in f:
            suggestion_card("🍽️", name, f.get("price", "N/A"), f.get("rating", "N/A"),
                             f.get("popularity", ""), distance=f.get("distance"), duration=f.get("duration"), cuisine=cuisine_filter)
            return
        with st.expander(f"🍽️ {name} — {f.get('price', 'N/A')} · ⭐ {f.get('rating', 'N/A')}{'' if included else ' (excluded)'}"):
            if f.get("cuisine"):
                st.write(f"🍴 **Cuisine:** {f['cuisine']}")
            if f.get("distance") and f.get("duration"):
                st.write(f"🚶 **Distance:** {f['distance']} | ⏱️ {f['duration']}")
            if f.get("specialties"):
                st.write(f"⭐ **Must-try:** {', '.join(f['specialties'])}")
            if f.get("ambiance"):
                st.write(f"🎭 **Ambiance:** {f['ambiance']}")
            if f.get("dietary_options"):
                st.write(f"🥗 **Dietary options:** {', '.join(f['dietary_options'])}")
            if f.get("review_summary"):
                st.write(f"📝 **Diner reviews:** {f['review_summary']}")
            if f.get("fit"):
                st.info(f"✅ **Why this fits you:** {f['fit']}")

def tour_card(t, idx):
    title = t.get("title", "Activity")
    key = f"sel_tour_{idx}_{title}"
    included, col_card = selection_checkbox(key)
    with col_card:
        if "raw_output" in t or "error" in t or "description" in t:
            suggestion_card("🎯", title, t.get("price", "N/A"), t.get("rating", "N/A"), t.get("popularity", "🔥 Popular"))
            return
        with st.expander(f"🎯 {title} — {t.get('price', 'N/A')} · ⭐ {t.get('rating', 'N/A')}{'' if included else ' (excluded)'}"):
            if t.get("what_to_expect"):
                st.write(f"📖 **What to expect:** {t['what_to_expect']}")
            if t.get("duration"):
                st.write(f"⏱️ **Duration:** {t['duration']}")
            if t.get("best_time"):
                st.write(f"🕒 **Best time to go:** {t['best_time']}")
            if t.get("accessibility_notes"):
                st.write(f"♿ **Accessibility:** {t['accessibility_notes']}")
            if t.get("tips"):
                st.write(f"💡 **Tip:** {t['tips']}")
            if t.get("fit"):
                st.info(f"✅ **Why this fits you:** {t['fit']}")

def flight_card(f, leg, idx):
    airline = f.get("airline", "Unknown")
    key = f"sel_flight_{leg}_{idx}_{airline}"
    included, col_card = selection_checkbox(key)
    with col_card:
        if "raw_output" in f or "error" in f:
            suggestion_card("✈️", airline, f.get("price_range", "N/A"), f.get("rating", "N/A"), f.get("route", ""))
            return
        with st.expander(f"✈️ {airline} — {f.get('price_range', 'N/A')} · ⭐ {f.get('rating', 'N/A')}{'' if included else ' (excluded)'}"):
            if f.get("route"):
                st.write(f"🛫 **Route:** {f['route']}")
            if f.get("departure") or f.get("arrival"):
                st.write(f"🕐 **Departure:** {f.get('departure', 'N/A')} → **Arrival:** {f.get('arrival', 'N/A')}")
            if f.get("duration"):
                st.write(f"⏱️ **Duration:** {f['duration']}")
            if f.get("class_options"):
                st.write(f"💺 **Class options:** {', '.join(f['class_options'])}")
            if f.get("baggage_allowance"):
                st.write(f"🧳 **Baggage:** {f['baggage_allowance']}")
            if f.get("url"):
                st.write(f"🔗 [View on Google Flights]({f['url']})")
            if f.get("fit"):
                st.info(f"✅ **Why this fits you:** {f['fit']}")

# ---------------- Session state: conversation + ANITA instance ----------------
if "anita" not in st.session_state or st.session_state.get("mode") != mode:
    st.session_state.anita = ANITA({}, mode=mode)
    st.session_state.mode = mode
    st.session_state.messages = []
    st.session_state.results = None
    st.session_state.approval_state = "pending"  # pending -> awaiting_feedback -> approved

    greeting, _ready = st.session_state.anita.chat("", [])
    st.session_state.messages.append({"role": "assistant", "content": greeting})

if st.button("🔄 Start Over"):
    st.session_state.anita = ANITA({}, mode=mode)
    st.session_state.messages = []
    st.session_state.results = None
    st.session_state.approval_state = "pending"
    greeting, _ready = st.session_state.anita.chat("", [])
    st.session_state.messages.append({"role": "assistant", "content": greeting})
    st.rerun()

anita = st.session_state.anita
trip = anita.state_manager.state

# ---------------- Chat with Anita ----------------
st.subheader("💬 Chat with Anita")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_message = st.chat_input("Tell Anita about your trip...")
if user_message:
    st.session_state.messages.append({"role": "user", "content": user_message})
    history = st.session_state.messages[:-1]  # everything before this new user turn

    reply, ready = anita.chat(user_message, history)
    st.session_state.messages.append({"role": "assistant", "content": reply})

    if ready and st.session_state.results is None:
        with st.spinner("Building your itinerary — coordinating with Hotel, Food, Tour, Flight, Weather, Transport, and News agents..."):
            try:
                st.session_state.results = anita.orchestrate(traveler_type=trip.get("traveler_type", "general"))
                st.session_state.approval_state = "pending"
            except Exception as e:
                st.error("🚨 Building the itinerary failed — see details below instead of a silent timeout.")
                st.exception(e)
                with st.expander("📋 Audit trail (this run)", expanded=True):
                    st.code(format_entries_as_text(get_recent_entries()) or "(empty)")
                st.stop()

    st.rerun()

results = st.session_state.results

# ---------------- Itinerary tabs (shown once Anita has enough info) ----------------
if results is None:
    st.info("Chat with Anita above to plan your trip — once she has your origin, destination, and dates, your itinerary will appear here.")
else:
    tab_itinerary, tab_flights, tab_hotels, tab_transport, tab_activities, tab_culinary, tab_guide, tab_disruptions, tab_alerts = st.tabs(
        ["Itinerary", "Flights", "Hotels", "Transport", "Activities", "Culinary", "Guide", "Disruptions", "Proactive Alerts"]
    )

    # ---------------- ITINERARY TAB ----------------
    with tab_itinerary:
        st.header("Itinerary Overview")
        st.write(f"Mode: {mode}")
        st.write(f"**Trip:** {trip.get('origin')} → {trip.get('destination')} ({trip.get('dates')})")
        st.write(f"**Budget:** {trip.get('budget')} | **Food preference:** {trip.get('food_pref')}")

        # ---------------- Human-in-the-loop: Approve or Request Changes ----------------
        st.subheader("🧑‍💼 Human-in-the-Loop: Review Your Itinerary")
        approval_state = st.session_state.approval_state

        if approval_state == "approved":
            st.success("🎉 Itinerary approved! Handing off to the Booking Agent...")
            booking = st.session_state.get("booking_result")
            if booking:
                for b in booking.get("booking", []):
                    if "error" in b:
                        st.error(b["error"])
                    else:
                        st.write(f"✅ **Confirmation:** {b.get('confirmation', 'N/A')}")
                        st.write(f"📄 **Cancellation policy:** {b.get('cancellation_policy', 'N/A')}")
                        st.write(f"💳 **Payment options:** {', '.join(b.get('payment_options', []))}")
                        st.write(f"📌 **Status:** {b.get('status', 'N/A')}")

        elif approval_state == "awaiting_feedback":
            clarifying_question = st.session_state.get("revision_clarifying_question")
            if clarifying_question:
                st.warning(f"❓ {clarifying_question}")
            else:
                st.warning("What would you like changed? Anita will rebuild the itinerary and bring it back for your approval.")
            feedback = st.text_area("Your feedback", key="revision_feedback", placeholder="e.g. I'd like cheaper hotels, or fewer activities on Day 2...")
            col_submit, col_cancel = st.columns(2)
            with col_submit:
                if st.button("📨 Submit Feedback & Rebuild", type="primary") and feedback.strip():
                    with st.spinner("Rebuilding your itinerary based on your feedback..."):
                        revision_result = anita.revise_itinerary(feedback.strip(), traveler_type=trip.get("traveler_type", "general"))
                    if revision_result.get("needs_clarification"):
                        # Ambiguous feedback (e.g. an unanswered routing choice) — ask
                        # instead of silently guessing and rebuilding anyway. Stay in
                        # awaiting_feedback so the traveler can answer and resubmit.
                        st.session_state.revision_clarifying_question = revision_result["clarifying_question"]
                    else:
                        st.session_state.results = revision_result
                        st.session_state.pop("revision_clarifying_question", None)
                        st.session_state.approval_state = "pending"
                    st.rerun()
            with col_cancel:
                if st.button("↩️ Cancel"):
                    st.session_state.pop("revision_clarifying_question", None)
                    st.session_state.approval_state = "pending"
                    st.rerun()

        else:  # pending
            st.info("Review the details below (Flights, Hotels, Transport, Activities, Culinary, Guide), then approve or request changes.")
            col_approve, col_reject = st.columns(2)
            with col_approve:
                if st.button("✅ Approve Itinerary", type="primary"):
                    itinerary_summary = {
                        "origin": trip.get("origin"), "destination": trip.get("destination"), "dates": trip.get("dates"),
                        "hotel": next((h.get("name") for h in results.get("hotel", {}).get("hotels", [])), None),
                        "restaurants": [f.get("name") for f in results.get("food", {}).get("restaurants", [])],
                        "activities": [t.get("title") for t in results.get("tour", {}).get("tour_summary", {}).get("tours", [])],
                        "outbound_flight": next((f.get("airline") for f in results.get("flight", {}).get("flights", {}).get("outbound", [])), None),
                        "return_flight": next((f.get("airline") for f in results.get("flight", {}).get("flights", {}).get("return", [])), None),
                    }
                    st.session_state.approval_state = "approved"
                    st.session_state.booking_result = anita.finalize_booking(itinerary_summary, True)
                    st.rerun()
            with col_reject:
                if st.button("✏️ Request Changes"):
                    st.session_state.approval_state = "awaiting_feedback"
                    st.rerun()

        st.subheader("Caching & Token Savings")

        st.caption("Fragment cache — per tool-call (Gemini/API) caching")
        fragment_stats = get_cache_stats()
        col1, col2, col3 = st.columns(3)
        col1.metric("Cache Hits", fragment_stats["hits"])
        col2.metric("Cache Misses", fragment_stats["misses"])
        col3.metric("Token Savings", f"{fragment_stats['savings_percent']}%")

        st.caption("Semantic cache — whole-request dedup at the orchestrator level")
        semantic_stats = get_semantic_cache_stats()
        col4, col5, col6 = st.columns(3)
        col4.metric("Semantic Hits", semantic_stats["hits"])
        col5.metric("Semantic Misses", semantic_stats["misses"])
        col6.metric("Pipeline Runs Saved", f"{semantic_stats['savings_percent']}%")

        st.caption("Prompt cache — static system-prompt handle reuse")
        prompt_stats = get_prompt_cache_stats()
        col7, col8, col9 = st.columns(3)
        col7.metric("Handle Reuses", prompt_stats["handle_reuses"])
        col8.metric("Handles Created", prompt_stats["handles_created"])
        col9.metric("Reuse Rate", f"{prompt_stats['reuse_percent']}%")

        st.subheader("📅 Day-by-Day Timeline")
        st.caption("Add/remove hotels, restaurants, and activities in their tabs below, then click Update to re-sequence your timeline.")
        if st.button("🔄 Update Itinerary with My Selections"):
            all_hotels = results.get("hotel", {}).get("hotels", [])
            all_foods = results.get("food", {}).get("restaurants", [])
            all_tours = results.get("tour", {}).get("tour_summary", {}).get("tours", [])

            selected_hotels = [
                h.get("name") for i, h in enumerate(all_hotels)
                if h.get("name") and st.session_state.get(f"sel_hotel_{i}_{h.get('name')}", True)
            ]
            selected_foods = [
                f.get("name") for i, f in enumerate(all_foods)
                if f.get("name") and st.session_state.get(f"sel_food_{i}_{f.get('name')}", True)
            ]
            selected_tours = [
                t.get("title") for i, t in enumerate(all_tours)
                if t.get("title") and st.session_state.get(f"sel_tour_{i}_{t.get('title')}", True)
            ]

            with st.spinner("Re-sequencing your itinerary..."):
                results["timeline"] = anita.rebuild_timeline_from_selection(selected_hotels, selected_foods, selected_tours)
            st.session_state.results = results
            st.rerun()

        timeline = results.get("timeline", [])
        if timeline:
            for day in timeline:
                label = f" — {day['label']}" if day.get("label") else ""
                with st.expander(f"Day {day.get('day', '?')}{label}", expanded=(day.get("day") == 1)):
                    for slot in day.get("schedule", []):
                        st.write(f"**{slot.get('time', '')}:** {slot.get('activity', '')}")
        else:
            st.info("Timeline unavailable for this trip.")

        st.subheader("🗺️ Trip Map")
        hotel_names = [h.get("name") for h in results.get("hotel", {}).get("hotels", []) if h.get("name")]
        food_names = [f.get("name") for f in results.get("food", {}).get("restaurants", []) if f.get("name")]
        tour_locations = [t.get("location") for t in results.get("tour", {}).get("tour_summary", {}).get("tours", []) if t.get("location")]
        stops = (hotel_names[:1] + tour_locations + food_names[:2])
        show_map(trip.get("origin"), hotel_names[0] if hotel_names else trip.get("destination"), waypoints=stops)

    # ---------------- FLIGHTS TAB ----------------
    with tab_flights:
        st.header("Flights")
        st.caption("Uncheck an option to exclude it, then click Update Itinerary on the Itinerary tab.")
        flights = results.get("flight", {}).get("flights", {})
        outbound = flights.get("outbound", []) if isinstance(flights, dict) else []
        returning = flights.get("return", []) if isinstance(flights, dict) else []

        st.subheader(f"🛫 Outbound: {trip.get('origin')} → {trip.get('destination')}")
        if outbound:
            for i, f in enumerate(outbound):
                flight_card(f, "out", i)
        else:
            st.info("No outbound flight options available.")

        st.subheader(f"🛬 Return: {trip.get('destination')} → {trip.get('origin')}")
        if returning:
            for i, f in enumerate(returning):
                flight_card(f, "ret", i)
        else:
            st.info("No return flight options available.")

    # ---------------- HOTELS TAB ----------------
    with tab_hotels:
        st.header("Hotels")
        st.caption("Click a hotel to see room details, amenities, distances, and why it fits you.")
        hotels = results.get("hotel", {}).get("hotels", [])
        if hotels:
            for i, h in enumerate(hotels):
                hotel_card(h, i)
            st.subheader("🗺️ Hotels on the Map")
            show_pin_map([
                {"label": h.get("name", "Hotel"), "query": f"{h.get('name', '')}, {h.get('location') or trip.get('destination')}"}
                for h in hotels if h.get("name") and "error" not in h
            ])

    # ---------------- TRANSPORT TAB ----------------
    with tab_transport:
        st.header("Transport")
        transport = results.get("transport", {}).get("transport", [])
        if transport:
            for t in transport:
                suggestion_card("🚖", t.get("name", "Transport"), t.get("price", "N/A"),
                                t.get("rating", "N/A"), t.get("popularity", ""),
                                distance=t.get("distance"), duration=t.get("duration"))

    # ---------------- ACTIVITIES TAB ----------------
    with tab_activities:
        st.header("Activities")
        st.caption("Click an activity to see what to expect, timing tips, and why it fits you.")
        tours = results.get("tour", {}).get("tour_summary", {}).get("tours", [])
        if tours:
            for i, t in enumerate(tours):
                tour_card(t, i)
            st.subheader("🗺️ Activities on the Map")
            show_pin_map([
                {"label": t.get("title", "Activity"), "query": f"{t.get('location') or trip.get('destination')}"}
                for t in tours if t.get("location") and "error" not in t
            ])

    # ---------------- CULINARY TAB ----------------
    with tab_culinary:
        st.header("Culinary")
        st.caption("Click a restaurant to see specialties, ambiance, dietary options, and why it fits you.")
        cuisine_filter = st.selectbox("Cuisine Preference", ["Any", "Vegetarian", "Vegan", "Street Food", "Fine Dining"])
        foods = results.get("food", {}).get("restaurants", [])
        if foods:
            for i, f in enumerate(foods):
                food_card(f, cuisine_filter, i)
            st.subheader("🗺️ Restaurants on the Map")
            show_pin_map([
                {"label": f.get("name", "Restaurant"), "query": f"{f.get('name', '')}, {trip.get('destination')}"}
                for f in foods if f.get("name") and "error" not in f
            ])
        food_vlogs = results.get("food", {}).get("vlog_insights", [])
        if food_vlogs:
            st.caption("📺 What travelers say (from YouTube)")
            for v in food_vlogs:
                st.write(f"- {v}")

    # ---------------- GUIDE TAB ----------------
    with tab_guide:
        st.header("Traveler Guide")
        guide = results.get("guide", {})

        st.subheader("🛂 Visa")
        visa_info = guide.get("visa", [])
        if visa_info:
            for v in visa_info:
                st.write(f"- {v}")
        else:
            st.info("No visa information available yet for this destination.")

        st.subheader("📱 SIM & Currency")
        sim_info = guide.get("sim_currency", [])
        if sim_info:
            for s in sim_info:
                st.write(f"- {s}")
        else:
            st.info("No SIM/currency information available yet for this destination.")

        st.subheader("💡 Local Tips")
        local_tips = guide.get("local_tips", [])
        if local_tips:
            for t in local_tips:
                st.write(f"- {t}")
        else:
            st.info("No local tips available yet for this destination.")

        st.subheader("📺 Video Highlights")
        video_highlights = guide.get("video_highlights", {})
        video_summary = video_highlights.get("summary", []) if isinstance(video_highlights, dict) else video_highlights
        video_sources = video_highlights.get("sources", []) if isinstance(video_highlights, dict) else []
        if video_summary:
            for point in video_summary:
                st.write(f"- {point}")
            if video_sources:
                with st.expander(f"Sources ({len(video_sources)} videos)"):
                    for s in video_sources:
                        st.caption(f"🎥 {s.get('title')} — {s.get('creator')}")
        else:
            st.info("No indexed travel-vlog content yet for this destination — this section fills in once real video data is indexed (see Local Tips above for AI-generated guidance in the meantime).")

    # ---------------- DISRUPTIONS TAB ----------------
    with tab_disruptions:
        st.header("Disruption Alerts")
        alerts = results.get("impact_assessment", {}).get("risk", {})
        if mode == "Demo":
            st.error("🚨 Demo Disruption: Flight simulated delay")
            st.success("✅ Demo Alternative Approved")
        else:
            if alerts.get("risk_level") == "High":
                st.error("🚨 High risk detected in itinerary")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Approve Alternate Plan"):
                        st.success("✅ Approved. Itinerary updated.")
                        st.info("♻️ Realignment triggered.")
                with col2:
                    if st.button("Keep Original Plan"):
                        st.warning("🛑 Original plan retained. Risks acknowledged.")
            else:
                st.success(f"✅ No major risks detected (risk level: {alerts.get('risk_level', 'Unknown')}).")
                if alerts.get("weather"):
                    st.write(f"🌦️ Weather: {alerts['weather']}")
                if alerts.get("political"):
                    st.write(f"🏛️ Political/local: {alerts['political']}")

    # ---------------- PROACTIVE ALERTS TAB ----------------
    with tab_alerts:
        st.header("Proactive Alerts")
        if mode == "Demo":
            st.warning("🌦️ Demo Alert: Simulated rain forecast → Indoor activity suggested.")
        else:
            weather = results.get("weather", {})
            forecast_text = str(weather.get("forecast", ""))
            advisories_text = str(weather.get("advisories", ""))

            shown_alert = False
            if "rain" in forecast_text.lower() or "rain" in advisories_text.lower():
                st.warning("🌦️ Rain forecast detected → Suggest indoor museum instead of outdoor walk.")
                shown_alert = True
            if weather.get("advisories") and weather["advisories"] != "No major advisories":
                st.info(f"ℹ️ {weather['advisories']}")
                shown_alert = True

            if not shown_alert:
                st.success("✅ No proactive alerts right now — conditions look normal for your trip.")
