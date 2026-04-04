import base64
import subprocess
from datetime import datetime
from html import escape
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
ASSETS_DIR = ROOT / "assets"
RECIPES_DIR = ROOT / "recipes"
INJECTIONS_DIR = ROOT / "injections"

RECIPES_DIR.mkdir(parents=True, exist_ok=True)
INJECTIONS_DIR.mkdir(parents=True, exist_ok=True)

NETWORK_OPTIONS = {
    "5G Stable": "5g_stable",
    "WiFi Office": "wifi_office",
    "3G Degraded": "3g_degraded",
    "Edge Failure": "edge_failure",
}

CPU_OPTIONS = {
    "1 vCPU": "1",
    "2 vCPU": "2",
    "4 vCPU": "4",
}

MEMORY_OPTIONS = {
    "512 MB": "512m",
    "1 GB": "1g",
    "2 GB": "2g",
    "4 GB": "4g",
}

DB_OPTIONS = {
    "Postgres 15": "postgres15",
    "MySQL 8": "mysql8",
    "MongoDB 7": "mongo7",
    "SQLite (No DB Container)": "sqlite",
}

DB_SERVICE_CONFIG = {
    "postgres15": {
        "service_name": "database",
        "image": "postgres:15",
        "port": "5432:5432",
        "env": {
            "POSTGRES_USER": "spooler",
            "POSTGRES_PASSWORD": "spooler",
            "POSTGRES_DB": "targetdb",
        },
    },
    "mysql8": {
        "service_name": "database",
        "image": "mysql:8",
        "port": "3306:3306",
        "env": {
            "MYSQL_ROOT_PASSWORD": "spooler",
            "MYSQL_DATABASE": "targetdb",
        },
    },
    "mongo7": {
        "service_name": "database",
        "image": "mongo:7",
        "port": "27017:27017",
        "env": {},
    },
}

INJECTION_EXTENSIONS = {
    "python": ".py",
    "node": ".js",
    "shell": ".sh",
}

FILE_EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".js": "node",
    ".mjs": "node",
    ".cjs": "node",
    ".ts": "node",
    ".tsx": "node",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
}

PRESET_SCENARIOS = {
    "Slow Mobile + Vulnerable DOM": {
        "intent_text": "Validate generated fixes under degraded mobile conditions with DOM exploit exposure.",
        "network_profile_label": "3G Degraded",
        "latency_ms": 520,
        "packet_loss_pct": 8,
        "cpu_budget_label": "1 vCPU",
        "memory_budget_label": "512 MB",
        "db_engine_label": "Postgres 15",
        "chaos_mode": False,
        "vulnerable_dom": True,
        "sql_injection": False,
        "auth_bypass": False,
        "third_party_outage": False,
        "strict_rate_limit": True,
        "injection_language": "python",
        "target_path": "/workspace/injected/main.py",
        "run_command": "python /workspace/injected/main.py",
        "payload_text": "print('simulate degraded mobile edge case')",
        "spin_now": False,
    },
    "Auth Chaos Drill": {
        "intent_text": "Stress test generated patches for token expiry races, bypass behavior, and partial upstream failures.",
        "network_profile_label": "Edge Failure",
        "latency_ms": 390,
        "packet_loss_pct": 5,
        "cpu_budget_label": "2 vCPU",
        "memory_budget_label": "1 GB",
        "db_engine_label": "MySQL 8",
        "chaos_mode": True,
        "vulnerable_dom": False,
        "sql_injection": False,
        "auth_bypass": True,
        "third_party_outage": True,
        "strict_rate_limit": True,
        "injection_language": "node",
        "target_path": "/workspace/injected/main.js",
        "run_command": "node /workspace/injected/main.js",
        "payload_text": "console.log('auth chaos drill active');",
        "spin_now": False,
    },
    "SQL Storm + Tight Limits": {
        "intent_text": "Benchmark generated sanitization logic under SQL attack pressure and strict rate limiting.",
        "network_profile_label": "WiFi Office",
        "latency_ms": 140,
        "packet_loss_pct": 1,
        "cpu_budget_label": "4 vCPU",
        "memory_budget_label": "2 GB",
        "db_engine_label": "Postgres 15",
        "chaos_mode": True,
        "vulnerable_dom": False,
        "sql_injection": True,
        "auth_bypass": False,
        "third_party_outage": False,
        "strict_rate_limit": True,
        "injection_language": "shell",
        "target_path": "/workspace/injected/main.sh",
        "run_command": "sh /workspace/injected/main.sh",
        "payload_text": "echo 'running sql storm drill'",
        "spin_now": False,
    },
    "Third-Party Timeout Cascade": {
        "intent_text": "Test generated patches when upstream dependencies are unstable and requests timeout intermittently.",
        "network_profile_label": "3G Degraded",
        "latency_ms": 460,
        "packet_loss_pct": 6,
        "cpu_budget_label": "2 vCPU",
        "memory_budget_label": "1 GB",
        "db_engine_label": "Postgres 15",
        "chaos_mode": True,
        "vulnerable_dom": False,
        "sql_injection": False,
        "auth_bypass": False,
        "third_party_outage": True,
        "strict_rate_limit": True,
        "injection_language": "python",
        "target_path": "/workspace/injected/main.py",
        "run_command": "python /workspace/injected/main.py",
        "payload_text": "print('simulate upstream timeout cascade')",
        "spin_now": False,
    },
    "CPU Spike Recovery": {
        "intent_text": "Evaluate whether generated retries and backoff logic survive CPU starvation windows.",
        "network_profile_label": "WiFi Office",
        "latency_ms": 170,
        "packet_loss_pct": 2,
        "cpu_budget_label": "1 vCPU",
        "memory_budget_label": "1 GB",
        "db_engine_label": "MySQL 8",
        "chaos_mode": True,
        "vulnerable_dom": False,
        "sql_injection": False,
        "auth_bypass": False,
        "third_party_outage": True,
        "strict_rate_limit": False,
        "injection_language": "node",
        "target_path": "/workspace/injected/main.js",
        "run_command": "node /workspace/injected/main.js",
        "payload_text": "console.log('cpu spike resilience check');",
        "spin_now": False,
    },
    "Memory Pressure Leak Hunt": {
        "intent_text": "Probe generated code under low-memory constraints to surface hidden leak behavior and crashes.",
        "network_profile_label": "WiFi Office",
        "latency_ms": 120,
        "packet_loss_pct": 1,
        "cpu_budget_label": "2 vCPU",
        "memory_budget_label": "512 MB",
        "db_engine_label": "MongoDB 7",
        "chaos_mode": True,
        "vulnerable_dom": False,
        "sql_injection": False,
        "auth_bypass": False,
        "third_party_outage": False,
        "strict_rate_limit": True,
        "injection_language": "python",
        "target_path": "/workspace/injected/main.py",
        "run_command": "python /workspace/injected/main.py",
        "payload_text": "print('memory pressure leak hunt active')",
        "spin_now": False,
    },
    "Packet Loss Retry Trap": {
        "intent_text": "Validate idempotency and retry logic when packet loss causes duplicate and partial requests.",
        "network_profile_label": "Edge Failure",
        "latency_ms": 410,
        "packet_loss_pct": 18,
        "cpu_budget_label": "2 vCPU",
        "memory_budget_label": "1 GB",
        "db_engine_label": "Postgres 15",
        "chaos_mode": True,
        "vulnerable_dom": False,
        "sql_injection": False,
        "auth_bypass": True,
        "third_party_outage": True,
        "strict_rate_limit": True,
        "injection_language": "python",
        "target_path": "/workspace/injected/main.py",
        "run_command": "python /workspace/injected/main.py",
        "payload_text": "print('packet loss retry trap')",
        "spin_now": False,
    },
    "Offline-First Failover": {
        "intent_text": "Check whether generated code gracefully degrades when the network is mostly unavailable.",
        "network_profile_label": "Edge Failure",
        "latency_ms": 700,
        "packet_loss_pct": 25,
        "cpu_budget_label": "1 vCPU",
        "memory_budget_label": "1 GB",
        "db_engine_label": "SQLite (No DB Container)",
        "chaos_mode": True,
        "vulnerable_dom": False,
        "sql_injection": False,
        "auth_bypass": False,
        "third_party_outage": True,
        "strict_rate_limit": False,
        "injection_language": "shell",
        "target_path": "/workspace/injected/main.sh",
        "run_command": "sh /workspace/injected/main.sh",
        "payload_text": "echo 'offline-first failover check'",
        "spin_now": False,
    },
    "No-DB Fallback Path": {
        "intent_text": "Verify generated fallback logic when no external database container is available.",
        "network_profile_label": "5G Stable",
        "latency_ms": 50,
        "packet_loss_pct": 0,
        "cpu_budget_label": "2 vCPU",
        "memory_budget_label": "2 GB",
        "db_engine_label": "SQLite (No DB Container)",
        "chaos_mode": False,
        "vulnerable_dom": False,
        "sql_injection": False,
        "auth_bypass": False,
        "third_party_outage": False,
        "strict_rate_limit": False,
        "injection_language": "python",
        "target_path": "/workspace/injected/main.py",
        "run_command": "python /workspace/injected/main.py",
        "payload_text": "print('no-db fallback path check')",
        "spin_now": False,
    },
    "Full Chaos Fire Drill": {
        "intent_text": "Push generated code through an intentionally hostile stack: auth bypass, SQL risk, outages, and high loss.",
        "network_profile_label": "Edge Failure",
        "latency_ms": 780,
        "packet_loss_pct": 22,
        "cpu_budget_label": "1 vCPU",
        "memory_budget_label": "512 MB",
        "db_engine_label": "MySQL 8",
        "chaos_mode": True,
        "vulnerable_dom": True,
        "sql_injection": True,
        "auth_bypass": True,
        "third_party_outage": True,
        "strict_rate_limit": True,
        "injection_language": "shell",
        "target_path": "/workspace/injected/main.sh",
        "run_command": "sh /workspace/injected/main.sh",
        "payload_text": "echo 'full chaos fire drill active'",
        "spin_now": False,
    },
}

DIFFICULTY_PROFILES = {
    "Preset Default": {},
    "Mild": {
        "network_profile_label": "WiFi Office",
        "latency_ms": 90,
        "packet_loss_pct": 0,
        "cpu_budget_label": "4 vCPU",
        "memory_budget_label": "2 GB",
        "chaos_mode": False,
        "third_party_outage": False,
        "strict_rate_limit": False,
    },
    "Balanced": {
        "network_profile_label": "3G Degraded",
        "latency_ms": 280,
        "packet_loss_pct": 3,
        "cpu_budget_label": "2 vCPU",
        "memory_budget_label": "1 GB",
        "chaos_mode": False,
        "third_party_outage": False,
        "strict_rate_limit": True,
    },
    "Hard": {
        "network_profile_label": "Edge Failure",
        "latency_ms": 520,
        "packet_loss_pct": 8,
        "cpu_budget_label": "1 vCPU",
        "memory_budget_label": "512 MB",
        "chaos_mode": True,
        "third_party_outage": True,
        "strict_rate_limit": True,
    },
    "Extreme": {
        "network_profile_label": "Edge Failure",
        "latency_ms": 760,
        "packet_loss_pct": 18,
        "cpu_budget_label": "1 vCPU",
        "memory_budget_label": "512 MB",
        "chaos_mode": True,
        "third_party_outage": True,
        "strict_rate_limit": True,
        "vulnerable_dom": True,
        "sql_injection": True,
        "auth_bypass": True,
    },
}

DIFFICULTY_DETAILS = {
    "Preset Default": "Uses the exact values bundled with the selected preset.",
    "Mild": "Fast network, low loss, and higher resources. Good for baseline validation.",
    "Balanced": "Realistic moderate stress. Good default for day-to-day patch checks.",
    "Hard": "High latency + outages + tighter resources. Surfaces brittle assumptions.",
    "Extreme": "Very hostile conditions plus multiple vulnerability toggles. Break-things mode.",
}

CHALLENGE_LEVEL_HELP = (
    "Preset Default: Use preset values as-is.\n"
    "Mild: Easy environment, baseline confidence.\n"
    "Balanced: Realistic stress profile for routine checks.\n"
    "Hard: High friction conditions with likely failure edges.\n"
    "Extreme: Aggressive chaos + vulnerability pressure test."
)

DEFAULT_STATE = {
    "selected_preset": next(iter(PRESET_SCENARIOS)),
    "difficulty_profile": "Preset Default",
    "advanced_mode": False,
    "show_guides": False,
    "quick_prompt": "",
    "preset_initialized": False,
    "intent_text": "",
    "network_profile_label": "3G Degraded",
    "latency_ms": 300,
    "packet_loss_pct": 2,
    "cpu_budget_label": "2 vCPU",
    "memory_budget_label": "1 GB",
    "db_engine_label": "Postgres 15",
    "chaos_mode": False,
    "vulnerable_dom": True,
    "sql_injection": False,
    "auth_bypass": False,
    "third_party_outage": False,
    "strict_rate_limit": True,
    "injection_language": "python",
    "target_path": "/workspace/injected/main.py",
    "run_command": "",
    "payload_text": "",
    "spin_now": False,
    "payload_file_name": "",
    "last_upload_size": 0,
    "ide_choice": "VS Code",
    "ide_concept_requested": False,
}


def default_target_path_for_language(language: str) -> str:
    if language == "python":
        return "/workspace/injected/main.py"
    if language == "node":
        return "/workspace/injected/main.js"
    return "/workspace/injected/main.sh"


def default_run_command_for_language(language: str) -> str:
    if language == "python":
        return "python /workspace/injected/main.py"
    if language == "node":
        return "node /workspace/injected/main.js"
    return "sh /workspace/injected/main.sh"


def infer_language_from_filename(filename: str) -> str | None:
    suffix = Path(filename).suffix.lower()
    return FILE_EXTENSION_TO_LANGUAGE.get(suffix)


def initialize_state() -> None:
    for key, value in DEFAULT_STATE.items():
        st.session_state.setdefault(key, value)

    if not st.session_state["preset_initialized"]:
        apply_preset(st.session_state["selected_preset"])
        st.session_state["preset_initialized"] = True


def apply_preset(name: str) -> None:
    preset = PRESET_SCENARIOS[name]
    st.session_state["selected_preset"] = name
    for key, value in preset.items():
        st.session_state[key] = value


def apply_difficulty(profile_name: str) -> None:
    overrides = DIFFICULTY_PROFILES[profile_name]
    for key, value in overrides.items():
        st.session_state[key] = value


def on_preset_change() -> None:
    apply_preset(st.session_state["selected_preset"])
    if st.session_state["difficulty_profile"] != "Preset Default":
        apply_difficulty(st.session_state["difficulty_profile"])


def on_difficulty_change() -> None:
    profile = st.session_state["difficulty_profile"]
    if profile == "Preset Default":
        apply_preset(st.session_state["selected_preset"])
        return
    apply_difficulty(profile)


def decode_uploaded_file(uploaded_file) -> str:
    raw = uploaded_file.getvalue()
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def sync_uploaded_file(uploaded_file) -> None:
    if uploaded_file is None:
        return

    current_name = uploaded_file.name
    current_size = uploaded_file.size
    if (
        st.session_state.get("payload_file_name") == current_name
        and st.session_state.get("last_upload_size") == current_size
    ):
        return

    content = decode_uploaded_file(uploaded_file)
    st.session_state["payload_text"] = content
    st.session_state["payload_file_name"] = current_name
    st.session_state["last_upload_size"] = current_size

    inferred = infer_language_from_filename(current_name)
    if inferred:
        st.session_state["injection_language"] = inferred
        st.session_state["target_path"] = default_target_path_for_language(inferred)
        st.session_state["run_command"] = default_run_command_for_language(inferred)


def get_base64(path: Path) -> str:
    with path.open("rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")


def find_background_asset() -> Path | None:
    candidates = [
        ASSETS_DIR / "SPOOLER_background.png",
        ASSETS_DIR / "SPOOLER_background.jpg",
        ASSETS_DIR / "SPOOLER_background.jpeg",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def apply_theme(background_path: Path | None) -> None:
    bg_css = ""
    if background_path:
        encoded_bg = get_base64(background_path)
        bg_css = f"background-image: url('data:image/png;base64,{encoded_bg}');"

    led_viewport_bg_css = "background: linear-gradient(110deg, rgba(11, 24, 40, 0.82), rgba(8, 19, 32, 0.72));"
    led_scroller_path = ASSETS_DIR / "Spooler_led_scroller.png"
    if led_scroller_path.exists():
        encoded_led_scroller = get_base64(led_scroller_path)
        led_viewport_bg_css = (
            f"background-image: url('data:image/png;base64,{encoded_led_scroller}');"
            "background-repeat: no-repeat;"
            "background-position: center;"
            "background-size: 100% 100%;"
        )

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Share+Tech+Mono&display=swap');

        :root {{
            --glass-bg: rgba(10, 20, 34, 0.62);
            --glass-bg-strong: rgba(8, 16, 28, 0.82);
            --glass-border: rgba(162, 206, 255, 0.34);
            --glass-glow: rgba(118, 181, 255, 0.28);
            --text-strong: #f7fbff;
            --text-soft: #dcefff;
        }}

        .stApp {{
            {bg_css}
            background-size: cover;
            background-attachment: fixed;
            color: #d7ffd0;
        }}

        .stApp::before {{
            content: "";
            position: fixed;
            inset: 0;
            background: radial-gradient(circle at top, rgba(52, 255, 120, 0.18), rgba(0, 0, 0, 0.95) 45%);
            z-index: -1;
        }}

        h1, h2, h3 {{
            font-family: 'Orbitron', 'Share Tech Mono', monospace !important;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #93ff69 !important;
            text-shadow: 0 0 12px rgba(112, 255, 77, 0.55);
        }}

        p, label, li, input, textarea {{
            font-family: 'Share Tech Mono', monospace !important;
        }}

        /* Preserve Streamlit icon glyphs so labels don't render as text tokens like "upload" or "arrow_right". */
        .material-symbols-rounded,
        .material-symbols-outlined,
        .material-icons {{
            font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
            font-style: normal !important;
            font-weight: 400 !important;
            letter-spacing: normal !important;
            text-transform: none !important;
            white-space: nowrap !important;
            word-wrap: normal !important;
        }}

        .stTextInput label,
        .stTextArea label,
        .stSelectbox label,
        .stCheckbox label,
        .stSlider label,
        .stFileUploader label,
        .stToggle label {{
            color: #cbffc2 !important;
        }}

        .stTextInput input,
        .stTextArea textarea,
        .stSelectbox div[data-baseweb='select'] > div,
        .stSlider [data-baseweb='slider'],
        .stFileUploader section {{
            background: var(--glass-bg) !important;
            border: 1px solid var(--glass-border) !important;
            color: var(--text-strong) !important;
            border-radius: 12px !important;
            backdrop-filter: blur(10px) saturate(130%);
            transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
        }}

        .stTextInput input:hover,
        .stTextArea textarea:hover,
        .stSelectbox div[data-baseweb='select'] > div:hover,
        .stFileUploader section:hover {{
            border-color: rgba(189, 221, 255, 0.7) !important;
            box-shadow: 0 0 0 1px rgba(189, 221, 255, 0.2), 0 8px 24px rgba(43, 104, 173, 0.22) !important;
            transform: translateY(-1px);
        }}

        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stSelectbox div[data-baseweb='select'] > div:focus-within {{
            border-color: rgba(204, 230, 255, 0.9) !important;
            box-shadow: 0 0 0 2px rgba(149, 203, 255, 0.25), 0 10px 28px rgba(54, 123, 201, 0.3) !important;
        }}

        .stButton > button,
        .stDownloadButton > button,
        button[kind='primary'] {{
            background: linear-gradient(115deg, #dff4ff, #a8daff 55%, #88c8ff) !important;
            color: #06223a !important;
            border: 1px solid rgba(213, 236, 255, 0.95) !important;
            border-radius: 999px !important;
            font-family: 'Orbitron', 'Share Tech Mono', monospace !important;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            font-weight: 700 !important;
            box-shadow: 0 8px 22px rgba(60, 129, 199, 0.35);
            transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
        }}

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        button[kind='primary']:hover {{
            filter: brightness(1.04);
            transform: translateY(-2px);
            box-shadow: 0 12px 28px rgba(67, 141, 219, 0.45), 0 0 18px rgba(155, 210, 255, 0.5);
        }}

        section[data-testid='stSidebar'] {{
            display: none !important;
        }}

        [data-testid='collapsedControl'] {{
            display: none !important;
        }}

        .block-container {{
            padding-top: 1.4rem;
            padding-bottom: 3rem;
        }}

        .hero-card {{
            border: 1px solid rgba(173, 214, 255, 0.42);
            border-radius: 16px;
            padding: 14px 18px;
            margin-bottom: 12px;
            background: linear-gradient(145deg, rgba(13, 24, 40, 0.78), rgba(8, 16, 28, 0.65));
            backdrop-filter: blur(12px) saturate(130%);
            box-shadow: 0 16px 40px rgba(16, 47, 84, 0.38), inset 0 1px 0 rgba(228, 242, 255, 0.12);
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }}

        .hero-card:hover {{
            border-color: rgba(200, 228, 255, 0.72);
            box-shadow: 0 18px 44px rgba(21, 66, 118, 0.42), inset 0 1px 0 rgba(244, 251, 255, 0.2);
        }}

        .section-label {{
            font-family: 'Orbitron', 'Share Tech Mono', monospace;
            color: #a5ff87;
            letter-spacing: 0.08em;
            font-size: 1.1rem;
            margin-top: 8px;
            margin-bottom: 8px;
            text-transform: uppercase;
            text-shadow: 0 0 14px rgba(130, 255, 103, 0.48);
        }}

        .preset-ticker-shell {{
            position: relative;
            margin-top: 4px;
            margin-bottom: 12px;
        }}

        .preset-ticker-viewport {{
            position: relative;
            width: 100%;
            aspect-ratio: 3550 / 170;
            min-height: 44px;
            max-height: 92px;
            border-radius: 12px;
            overflow: hidden;
            {led_viewport_bg_css}
            filter: drop-shadow(0 8px 18px rgba(33, 89, 151, 0.28));
            transition: transform 0.2s ease, filter 0.2s ease;
        }}

        .preset-ticker-shell:hover .preset-ticker-viewport {{
            transform: translateY(-1px);
            filter: drop-shadow(0 12px 24px rgba(45, 115, 187, 0.34));
        }}

        .preset-ticker-lane {{
            position: absolute;
            left: 12.45%;
            right: 15.25%;
            top: 33.2%;
            height: 34.2%;
            overflow: hidden;
            display: flex;
            align-items: center;
            pointer-events: none;
        }}

        .preset-ticker-track {{
            display: inline-block;
            white-space: nowrap;
            color: #a5ff87;
            text-shadow: 0 0 8px rgba(130, 255, 103, 0.65), 0 0 14px rgba(116, 255, 91, 0.35);
            font-family: 'Orbitron', 'Share Tech Mono', monospace;
            letter-spacing: 0.05em;
            font-size: clamp(0.5rem, 0.74vw, 1.2rem);
            line-height: 1;
            padding-left: 100%;
            animation: spooler-marquee 76s linear infinite;
        }}

        textarea[aria-label="Environment Prompt"] {{
            background: rgba(255, 255, 255, 0.96) !important;
            color: #0b1b2a !important;
            border: 1px solid rgba(187, 220, 255, 0.85) !important;
            border-radius: 12px !important;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9), 0 8px 20px rgba(43, 104, 173, 0.16);
            font-family: 'Share Tech Mono', monospace !important;
        }}

        textarea[aria-label="Environment Prompt"]::placeholder {{
            color: rgba(16, 36, 58, 0.58) !important;
        }}

        .preset-ticker-shell:hover .preset-ticker-track {{
            animation-play-state: paused;
        }}

        .settings-popover {{
            position: absolute;
            top: calc(100% + 12px);
            left: 50%;
            transform: translate(-50%, 8px);
            width: min(820px, 96vw);
            border: 1px solid rgba(179, 219, 255, 0.72);
            border-radius: 14px;
            background: linear-gradient(140deg, rgba(7, 16, 30, 0.9), rgba(8, 20, 36, 0.82));
            backdrop-filter: blur(14px) saturate(140%);
            box-shadow: 0 18px 38px rgba(18, 49, 88, 0.48), 0 0 18px rgba(146, 204, 255, 0.2);
            padding: 12px 14px;
            opacity: 0;
            visibility: hidden;
            pointer-events: none;
            z-index: 25;
            transition: opacity 0.18s ease, transform 0.18s ease, visibility 0.18s ease;
        }}

        .settings-popover::before {{
            content: "";
            position: absolute;
            top: -7px;
            left: calc(50% - 7px);
            width: 14px;
            height: 14px;
            background: rgba(9, 19, 34, 0.95);
            border-top: 1px solid rgba(179, 219, 255, 0.72);
            border-left: 1px solid rgba(179, 219, 255, 0.72);
            transform: rotate(45deg);
        }}

        .preset-ticker-shell:hover .settings-popover {{
            opacity: 1;
            visibility: visible;
            pointer-events: auto;
            transform: translate(-50%, 0);
        }}

        .settings-popover-title {{
            color: #f5fbff;
            font-family: 'Orbitron', 'Share Tech Mono', monospace;
            font-size: 0.82rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}

        .settings-popover-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(240px, 1fr));
            gap: 7px 18px;
        }}

        .settings-popover-row {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 10px;
            border-bottom: 1px dashed rgba(153, 201, 248, 0.2);
            padding-bottom: 4px;
        }}

        .settings-popover-key {{
            color: #d9ecff;
            font-size: 0.76rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            flex: 0 0 auto;
        }}

        .settings-popover-value {{
            color: #ffffff;
            font-size: 0.78rem;
            line-height: 1.35;
            text-align: right;
            max-width: 62%;
            overflow-wrap: anywhere;
        }}

        @media (max-width: 840px) {{
            .settings-popover {{
                width: min(640px, 96vw);
            }}

            .settings-popover-grid {{
                grid-template-columns: 1fr;
            }}

            .settings-popover-value {{
                max-width: 70%;
            }}
        }}

        .guide-anchor-row {{
            display: flex;
            align-items: flex-start;
            gap: 8px;
            margin-top: 6px;
            margin-bottom: 4px;
        }}

        .guide-line {{
            color: #9fd6ff;
            text-shadow: 0 0 10px rgba(120, 180, 255, 0.4);
            font-family: 'Orbitron', 'Share Tech Mono', monospace;
            font-size: 0.8rem;
            line-height: 1.2;
        }}

        .guide-brief-wrap {{
            display: block;
        }}

        .guide-anchor-title {{
            color: #f3f7ff;
            font-size: 0.76rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 2px;
        }}

        .guide-brief-text {{
            color: #ffffff;
            font-size: 0.8rem;
            line-height: 1.35;
        }}

        details.guide-drawer {{
            margin: 0 0 10px 18px;
            border: 1px solid rgba(144, 194, 255, 0.45);
            border-radius: 8px;
            background: rgba(8, 15, 28, 0.78);
            overflow: hidden;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }}

        details.guide-drawer[open] {{
            border-color: rgba(170, 212, 255, 0.88);
            box-shadow: 0 0 16px rgba(111, 171, 255, 0.25);
        }}

        details.guide-drawer summary {{
            list-style: none;
            cursor: pointer;
            padding: 8px 10px;
            color: #e9f4ff;
            font-size: 0.75rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }}

        details.guide-drawer summary::-webkit-details-marker {{
            display: none;
        }}

        details.guide-drawer summary::after {{
            content: " [+]";
            color: #beddff;
        }}

        details.guide-drawer[open] summary::after {{
            content: " [-]";
        }}

        .guide-drawer-body {{
            border-top: 1px solid rgba(145, 198, 255, 0.28);
            padding: 8px 12px 10px;
        }}

        .guide-drawer-body p {{
            color: #ffffff;
            font-size: 0.82rem;
            line-height: 1.45;
            margin: 0 0 8px 0;
        }}

        .guide-drawer-body p:last-child {{
            margin-bottom: 0;
        }}

        @keyframes spooler-marquee {{
            0% {{ transform: translateX(0%); }}
            100% {{ transform: translateX(-100%); }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def to_env_bool(value: bool) -> str:
    return "true" if value else "false"


def to_yaml_map_lines(data: dict[str, str], indent: int = 6) -> list[str]:
    spaces = " " * indent
    lines: list[str] = []
    for key, value in data.items():
        escaped = str(value).replace('"', '\\"')
        lines.append(f'{spaces}{key}: "{escaped}"')
    return lines


def build_database_service_yaml(db_key: str) -> list[str]:
    if db_key == "sqlite":
        return []

    config = DB_SERVICE_CONFIG[db_key]
    lines = [
        f"  {config['service_name']}:",
        f"    image: {config['image']}",
        "    restart: unless-stopped",
        "    ports:",
        f"      - \"{config['port']}\"",
    ]

    if config["env"]:
        lines.append("    environment:")
        lines.extend(to_yaml_map_lines(config["env"], indent=6))

    return lines


def build_compose_yaml(run_id: str, env_vars: dict[str, str]) -> str:
    lines = [
        'version: "3.9"',
        "services:",
        "  spool-target:",
        "    image: spooler/target-agent:latest",
        f"    container_name: {run_id}",
        "    restart: unless-stopped",
        "    ports:",
        '      - "8080:80"',
        "    environment:",
    ]
    lines.extend(to_yaml_map_lines(env_vars, indent=6))

    lines.extend(
        [
            "    volumes:",
            f"      - ./injections/{run_id}:/opt/spooler/injection",
            "    command: >",
            "      sh -c \"if [ -f /opt/spooler/injection/bootstrap.sh ]; then sh /opt/spooler/injection/bootstrap.sh; fi; tail -f /dev/null\"",
        ]
    )

    lines.extend(build_database_service_yaml(env_vars["DB_ENGINE"]))
    return "\n".join(lines) + "\n"


def write_injection_files(
    run_id: str,
    payload: str,
    language: str,
) -> tuple[Path, Path, str]:
    injection_dir = INJECTIONS_DIR / run_id
    injection_dir.mkdir(parents=True, exist_ok=True)

    extension = INJECTION_EXTENSIONS[language]
    payload_filename = f"payload{extension}"
    payload_path = injection_dir / payload_filename

    content = payload.strip()
    if not content:
        if language == "python":
            content = "print('spooler injection placeholder')"
        elif language == "node":
            content = "console.log('spooler injection placeholder');"
        else:
            content = "echo 'spooler injection placeholder'"

    payload_path.write_text(content + "\n", encoding="utf-8")

    bootstrap = (
        "#!/usr/bin/env sh\n"
        "set -eu\n"
        "TARGET_PATH=\"${SPOOLER_TARGET_PATH:-/workspace/injected/main" + extension + "}\"\n"
        "mkdir -p \"$(dirname \"$TARGET_PATH\")\"\n"
        f"cp /opt/spooler/injection/{payload_filename} \"$TARGET_PATH\"\n"
        "chmod +x \"$TARGET_PATH\" || true\n"
        "if [ -n \"${SPOOLER_RUN_COMMAND:-}\" ]; then\n"
        "  sh -lc \"$SPOOLER_RUN_COMMAND\"\n"
        "fi\n"
    )
    bootstrap_path = injection_dir / "bootstrap.sh"
    bootstrap_path.write_text(bootstrap, encoding="utf-8")
    bootstrap_path.chmod(0o755)

    return payload_path, bootstrap_path, extension


def run_local_compose(recipe_file: Path) -> tuple[bool, str]:
    command = ["docker", "compose", "-f", str(recipe_file), "up", "-d", "--remove-orphans"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=120)
    except FileNotFoundError:
        return False, "Docker CLI not found. Install Docker Desktop, then run the generated compose command."
    except subprocess.TimeoutExpired:
        return False, "Docker compose timed out after 120s."

    output = (result.stdout + "\n" + result.stderr).strip()
    if result.returncode == 0:
        return True, output or "Environment started successfully."
    return False, output or "Docker compose failed with a non-zero exit code."


def build_effective_settings_line() -> str:
    toggles = {
        "chaos": st.session_state["chaos_mode"],
        "vuln_dom": st.session_state["vulnerable_dom"],
        "sqli": st.session_state["sql_injection"],
        "auth_bypass": st.session_state["auth_bypass"],
        "outage": st.session_state["third_party_outage"],
        "rate_limit": st.session_state["strict_rate_limit"],
    }
    toggle_text = " | ".join([f"{name}:{'on' if enabled else 'off'}" for name, enabled in toggles.items()])
    return (
        f"preset={st.session_state['selected_preset']} | "
        f"level={st.session_state['difficulty_profile']} | "
        f"network={NETWORK_OPTIONS[st.session_state['network_profile_label']]} | "
        f"latency={st.session_state['latency_ms']}ms | "
        f"loss={st.session_state['packet_loss_pct']}% | "
        f"cpu={CPU_OPTIONS[st.session_state['cpu_budget_label']]} | "
        f"memory={MEMORY_OPTIONS[st.session_state['memory_budget_label']]} | "
        f"db={DB_OPTIONS[st.session_state['db_engine_label']]} | "
        f"{toggle_text}"
    )


def build_effective_settings_rows() -> list[tuple[str, str]]:
    return [
        ("Preset", st.session_state["selected_preset"]),
        ("Challenge", st.session_state["difficulty_profile"]),
        ("Network", NETWORK_OPTIONS[st.session_state["network_profile_label"]]),
        ("Latency", f"{st.session_state['latency_ms']} ms"),
        ("Packet Loss", f"{st.session_state['packet_loss_pct']}%"),
        ("CPU Budget", CPU_OPTIONS[st.session_state["cpu_budget_label"]]),
        ("Memory Budget", MEMORY_OPTIONS[st.session_state["memory_budget_label"]]),
        ("Database", DB_OPTIONS[st.session_state["db_engine_label"]]),
        ("Chaos Mode", "On" if st.session_state["chaos_mode"] else "Off"),
        ("Vulnerable DOM", "On" if st.session_state["vulnerable_dom"] else "Off"),
        ("SQL Injection Surface", "On" if st.session_state["sql_injection"] else "Off"),
        ("Auth Bypass Path", "On" if st.session_state["auth_bypass"] else "Off"),
        ("Third-Party Outage", "On" if st.session_state["third_party_outage"] else "Off"),
        ("Strict Rate Limiting", "On" if st.session_state["strict_rate_limit"] else "Off"),
    ]


def render_preset_ticker() -> None:
    summary = escape(build_effective_settings_line())
    marquee_text = f"{summary}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{summary}"
    popover_rows = "".join(
        (
            '<div class="settings-popover-row">'
            f'<span class="settings-popover-key">{escape(name)}</span>'
            f'<span class="settings-popover-value">{escape(value)}</span>'
            "</div>"
        )
        for name, value in build_effective_settings_rows()
    )
    st.markdown(
        (
            '<div class="preset-ticker-shell">'
            '<div class="preset-ticker-viewport">'
            '<div class="preset-ticker-lane">'
            f'<div class="preset-ticker-track">{marquee_text}</div>'
            "</div>"
            "</div>"
            '<div class="settings-popover">'
            '<div class="settings-popover-title">Active Environment Profile</div>'
            f'<div class="settings-popover-grid">{popover_rows}</div>'
            "</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_guide(anchor_label: str, brief: str, details: list[str]) -> None:
    detail_blocks = "".join(f"<p>{escape(line)}</p>" for line in details)
    st.markdown(
        (
            '<div class="guide-anchor-row">'
            '<div class="guide-line">└─</div>'
            '<div class="guide-brief-wrap">'
            f'<div class="guide-anchor-title">{escape(anchor_label)}</div>'
            f'<div class="guide-brief-text">{escape(brief)}</div>'
            "</div>"
            "</div>"
            '<details class="guide-drawer">'
            "<summary>Expand guide</summary>"
            f'<div class="guide-drawer-body">{detail_blocks}</div>'
            "</details>"
        ),
        unsafe_allow_html=True,
    )


def maybe_render_guide(anchor_label: str, brief: str, details: list[str]) -> None:
    if st.session_state.get("show_guides"):
        render_guide(anchor_label, brief, details)


def render_advanced_controls() -> None:
    st.markdown('<div class="section-label">Advanced Controls</div>', unsafe_allow_html=True)

    top_left, top_right = st.columns(2)
    with top_left:
        st.text_input(
            "Environment Intent",
            key="intent_text",
            placeholder="e.g. stress generated code behavior under 3G + auth edge-cases",
        )
        maybe_render_guide(
            "Environment Intent",
            "Free-text objective for the current run package.",
            [
                "Write a plain-language outcome statement that explains what this run is meant to prove. Keep it specific enough that someone else can understand the objective without seeing the rest of the setup.",
                "This value is written into the generated environment contract and travels with the artifacts. If you leave it empty, SPOOLER falls back to the selected preset name so the package still has a clear operational label.",
            ],
        )
    with top_right:
        st.selectbox("Injection Language", ["python", "node", "shell"], key="injection_language")
        maybe_render_guide(
            "Injection Language",
            "Selects payload extension and default execution path.",
            [
                "Pick the runtime family that matches the file you plan to inject. This controls payload extension selection and the default execution template used for path and command suggestions.",
                "Python maps to .py paths and python execution defaults, Node maps to .js and node defaults, and Shell maps to .sh with sh defaults. You can still override target path and command manually when needed.",
            ],
        )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.selectbox("1. Network Profile", list(NETWORK_OPTIONS.keys()), key="network_profile_label")
        maybe_render_guide(
            "Network Profile",
            "Sets a coarse network condition profile for scenario context.",
            [
                "Use this selector to establish the baseline operating network for the run. It gives you a fast way to switch between stable and degraded conditions without manually editing every field.",
                "The chosen profile is serialized into the run contract as a stable context label. Combined with latency and packet loss values, it helps downstream logic and reviewers interpret why certain runtime behavior occurred.",
            ],
        )
        st.slider("2. Base Latency (ms)", min_value=0, max_value=900, step=10, key="latency_ms")
        maybe_render_guide(
            "Base Latency",
            "Defines baseline delay injected into the generated environment settings.",
            [
                "Base latency sets the expected request delay floor for this scenario. Increasing it is useful when you want to expose timeout sensitivity, retry behavior, and sequencing assumptions.",
                "Treat this as the main timing pressure dial. Higher values amplify race conditions and brittle timeout defaults, while lower values help you validate nominal behavior before layering on harsher conditions.",
            ],
        )
    with c2:
        st.slider("3. Packet Loss (%)", min_value=0, max_value=40, step=1, key="packet_loss_pct")
        maybe_render_guide(
            "Packet Loss",
            "Models dropped request pressure for retry and idempotency checks.",
            [
                "Packet loss introduces random transport failure pressure so you can evaluate retry logic, duplicate handling, and fallback behavior under imperfect connectivity.",
                "Use lower percentages for routine validation and higher percentages for stress scenarios where resilience is the primary objective. This is one of the most effective controls for surfacing hidden reliability defects.",
            ],
        )
        st.selectbox("4. CPU Budget", list(CPU_OPTIONS.keys()), key="cpu_budget_label")
        maybe_render_guide(
            "CPU Budget",
            "Sets CPU constraint metadata for the environment package.",
            [
                "CPU budget defines available processing headroom for the run. Lower allocations create contention faster and expose latency amplification in compute-heavy code paths.",
                "When failures only appear under constrained throughput, reducing CPU budget is often the fastest way to reproduce them. Pair this with higher latency or strict rate limiting for stronger pressure profiles.",
            ],
        )
    with c3:
        st.selectbox("5. Memory Budget", list(MEMORY_OPTIONS.keys()), key="memory_budget_label")
        maybe_render_guide(
            "Memory Budget",
            "Sets memory constraint metadata for runtime pressure scenarios.",
            [
                "Memory budget controls the runtime footprint allowance used in the scenario package. Tight memory profiles make allocation spikes, leak behavior, and large-buffer assumptions easier to detect.",
                "Use conservative memory limits during hardening passes to surface OOM-adjacent issues early. For baseline checks, increase the budget to isolate logic issues from resource starvation noise.",
            ],
        )
        st.selectbox("6. DB Engine", list(DB_OPTIONS.keys()), key="db_engine_label")
        maybe_render_guide(
            "DB Engine",
            "Chooses which database sidecar is emitted in the compose recipe.",
            [
                "This selector determines which persistence dependency is represented in the generated compose stack. It lets you test compatibility and fallback behavior across different backing data services.",
                "Selecting SQLite keeps the run single-service with no database sidecar, while Postgres, MySQL, and Mongo emit dedicated sidecar services. Choose the option that best matches the integration path you want to validate.",
            ],
        )

    st.markdown("#### Fault + Security Toggles")
    maybe_render_guide(
        "Fault + Security Toggles",
        "Applies boolean switches that shape hostile-path scenario behavior.",
        [
            "These toggles let you compose targeted stress behavior without rewriting presets. Each switch activates a specific class of pressure so you can model realistic failure paths quickly.",
            "Every toggle is serialized into the emitted environment contract for traceable replay. Combine multiple toggles with challenge levels when you want reproducible, high-intensity scenarios.",
        ],
    )
    st.checkbox("7. Chaos Mode", key="chaos_mode")
    maybe_render_guide(
        "Chaos Mode",
        "Enables generalized instability for stress-oriented runs.",
        [
            "Chaos Mode is a broad instability flag used when you want the entire scenario interpreted as hostile rather than nominal. It is useful for resilience-focused validation sessions.",
            "Use this with elevated latency, packet loss, and constrained resources to expose assumptions that only fail under sustained operational turbulence.",
        ],
    )
    st.checkbox("8. Vulnerable DOM", key="vulnerable_dom")
    maybe_render_guide(
        "Vulnerable DOM",
        "Flags DOM risk scenario context for client-side defensive checks.",
        [
            "Enable this when your objective includes client-side rendering safety and DOM-related trust boundaries. It signals that UI-facing paths should be treated with stricter validation expectations.",
            "This is most useful when verifying sanitization, output encoding, and safe rendering behavior across untrusted content flows.",
        ],
    )
    st.checkbox("9. SQL Injection Surface", key="sql_injection")
    maybe_render_guide(
        "SQL Injection Surface",
        "Flags SQL-risk context to test parameterization and query guardrails.",
        [
            "Use this toggle to classify the run as SQL-risk oriented so query handling and input boundaries are tested under stricter assumptions.",
            "Pairing this with strict rate limiting and elevated failure pressure can reveal brittle query retry behavior and weak guardrails in data-access paths.",
        ],
    )
    st.checkbox("10. Auth Bypass Path", key="auth_bypass")
    maybe_render_guide(
        "Auth Bypass Path",
        "Signals authentication edge-case pressure in the scenario package.",
        [
            "Turn this on when you want authentication and authorization flows to be evaluated under bypass-like edge conditions.",
            "It is especially useful for validating token lifecycle handling, boundary checks, and fallback behavior when trust assumptions are stressed.",
        ],
    )
    st.checkbox("11. Third-Party Outage", key="third_party_outage")
    maybe_render_guide(
        "Third-Party Outage",
        "Simulates upstream dependency instability in scenario context.",
        [
            "This toggle marks the scenario as dependency-outage sensitive so external service failure behavior becomes a first-class validation target.",
            "Use it to evaluate timeout handling, circuit-breaker posture, degraded-mode operation, and recovery behavior when upstream systems are unavailable.",
        ],
    )
    st.checkbox("12. Strict Rate Limiting", key="strict_rate_limit")
    maybe_render_guide(
        "Strict Rate Limiting",
        "Applies tighter request-throttling assumptions for the run.",
        [
            "Enable strict rate limiting when you need to pressure request pacing logic and ensure clients do not thrash under constrained throughput policies.",
            "This works well with retry-heavy scenarios where backoff discipline and request budgeting are critical to stability.",
        ],
    )

    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        st.text_input("Target Path Inside Container", key="target_path")
        maybe_render_guide(
            "Target Path",
            "Destination path where bootstrap copies the payload in-container.",
            [
                "Target path is the exact in-container file location that receives the generated payload at startup. It should align with how your runtime discovers executable entry files.",
                "If the path does not reflect the real execution flow, runs may appear healthy while validating the wrong surface. Keep this aligned with your actual application entrypoint strategy.",
            ],
        )
    with bottom_right:
        st.text_input("Optional Command After Injection", key="run_command")
        maybe_render_guide(
            "Run Command",
            "Optional command executed after payload copy.",
            [
                "Run command is optional and controls whether the payload is executed automatically after injection. Leave it empty when you only need artifact packaging.",
                "Set a command when you want startup-time execution for quick validation loops. Ensure it matches the selected runtime and target path to avoid false negatives.",
            ],
        )


st.set_page_config(page_title="SPOOLER | Environment Builder", page_icon="⚡", layout="wide")
initialize_state()
apply_theme(find_background_asset())

logo_path = ASSETS_DIR / "Spooler_logo.png"
top_logo_col, top_meta_col = st.columns([1, 3])
with top_logo_col:
    if logo_path.exists():
        st.image(str(logo_path), width="stretch")
with top_meta_col:
    st.markdown("### SPOOLER // Adaptive Environment Forge")
    st.caption("v1.4.0 · streamlined quick setup with optional deep control")

st.markdown('<div class="hero-card">', unsafe_allow_html=True)
st.title("Define Your Runtime Scenario")
st.caption("Type what you want, pick a preset and challenge level, then build. Advanced mode exposes full controls.")
st.text_area(
    "Environment Prompt",
    key="quick_prompt",
    placeholder="Example: build a harsh network profile with retry pressure and auth edge-case validation.",
    height=86,
)
maybe_render_guide(
    "Environment Prompt",
    "Describe the outcome you want in plain language.",
    [
        "This prompt is the fastest way to describe run intent without opening advanced controls. Write one clear statement of what behavior you want to validate, and SPOOLER will carry it into the generated environment contract.",
        "If both prompt and advanced intent are set, the prompt is used as the primary intent value. If prompt is empty, SPOOLER falls back to advanced intent and then preset name, so every package still has a meaningful objective label.",
    ],
)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="section-label">Quick Setup (Simple Mode)</div>', unsafe_allow_html=True)
setup_col_1, setup_col_2, setup_col_3, setup_col_4 = st.columns([2, 1, 1, 1])
with setup_col_1:
    st.selectbox(
        "Preset Scenario",
        list(PRESET_SCENARIOS.keys()),
        key="selected_preset",
        on_change=on_preset_change,
    )
    maybe_render_guide(
        "Preset Scenario",
        "Loads a full baseline profile for environment settings and payload defaults.",
        [
            "A preset is the fastest way to load a complete scenario profile with coherent defaults. It sets network, resource, and fault posture in one step so setup stays consistent across runs.",
            "Use presets when you want repeatability and fast onboarding. You can still layer challenge-level overrides or advanced control edits on top without losing the baseline profile intent.",
        ],
    )
with setup_col_2:
    st.selectbox(
        "Challenge Level",
        list(DIFFICULTY_PROFILES.keys()),
        key="difficulty_profile",
        help=CHALLENGE_LEVEL_HELP,
        on_change=on_difficulty_change,
    )
    maybe_render_guide(
        "Challenge Level",
        "Applies preconfigured stress overrides on top of the current preset.",
        [
            "Challenge level adjusts operational stress intensity while preserving the scenario theme selected by the preset. It is the quickest way to scale pressure up or down.",
            "Use Preset Default to keep baseline values unchanged, then move to Hard or Extreme when validating robustness under heavier latency, loss, and fault pressure.",
        ],
    )
with setup_col_3:
    st.toggle("Advanced mode", key="advanced_mode")
    maybe_render_guide(
        "Advanced Mode",
        "Reveals full control over network, compute, database, and fault toggles.",
        [
            "Advanced mode expands the full control plane so you can tune every environment variable directly. This is useful when presets are close but not exact for your target condition.",
            "Keep this off for fast, standardized runs and turn it on when you need precise shaping for a specific edge case or reproduction workflow.",
        ],
    )
with setup_col_4:
    st.toggle("Show guides", key="show_guides")

st.caption(f"Challenge note: {DIFFICULTY_DETAILS[st.session_state['difficulty_profile']]}")
render_preset_ticker()
maybe_render_guide(
    "Effective Settings Ticker",
    "Real-time summary of the exact effective environment profile.",
    [
        "The ticker gives an immediate serialized summary of the currently effective configuration. It is useful as a pre-flight checkpoint before generating artifacts.",
        "Because it updates live as controls change, it helps you verify that overrides were applied as expected and prevents accidental builds with stale assumptions.",
    ],
)

st.markdown('<div class="section-label">Injection Zone</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "Drag + drop a code file here, or click to browse",
    type=["py", "js", "ts", "tsx", "sh", "bash", "zsh", "txt", "json", "md"],
)
sync_uploaded_file(uploaded_file)
maybe_render_guide(
    "File Upload",
    "Imports a source file and syncs it into the payload editor.",
    [
        "Upload lets you bring in an existing file directly from your workstation for immediate packaging. The file contents are copied into the payload editor so you can inspect or modify before build.",
        "When extension mapping is recognized, language-specific defaults are updated automatically for target path and run command. This reduces manual setup mistakes during repeated runs.",
    ],
)

if uploaded_file is not None:
    st.caption(
        f"Loaded `{uploaded_file.name}` ({uploaded_file.size} bytes). "
        "The file content was copied into the payload editor below."
    )

st.text_area(
    "Injected Code Payload",
    key="payload_text",
    placeholder="Paste code here if you are not uploading a file...",
    height=190,
)
maybe_render_guide(
    "Injected Code Payload",
    "Editable payload content that gets written into generated injection artifacts.",
    [
        "This editor is the exact source that becomes the injected payload artifact. Use it for quick iteration when you want to adjust behavior without switching tools.",
        "If no payload content is provided, SPOOLER writes a language-matched placeholder so the package remains executable and structurally complete.",
    ],
)

if st.session_state["advanced_mode"]:
    st.checkbox("Attempt local spin-up now (docker compose up -d)", key="spin_now")
    maybe_render_guide(
        "Local Spin-Up",
        "Immediately attempts docker compose start after artifact generation.",
        [
            "Enable this when you want SPOOLER to execute compose startup right after writing artifacts. It shortens feedback time for end-to-end checks.",
            "Disable it when you are generating packages for handoff, versioning, or later execution in another environment.",
        ],
    )
else:
    st.session_state["spin_now"] = False

with st.expander("IDE Connect (Concept)"):
    st.write(
        "Future workflow concept: connect your IDE and request read-only project access so SPOOLER can pull the "
        "latest file automatically before injection."
    )
    st.selectbox("IDE", ["VS Code", "Cursor", "JetBrains"], key="ide_choice")
    if st.button("Request IDE read permission (concept)"):
        st.session_state["ide_concept_requested"] = True
    if st.session_state["ide_concept_requested"]:
        st.info("Concept event captured: IDE permission request staged (not yet wired).")
    maybe_render_guide(
        "IDE Connect Concept",
        "Preview of future direct pull flow from IDE workspaces.",
        [
            "This section represents the planned workflow for controlled read-only file pull from an IDE workspace into the injection path.",
            "Current behavior records intent only and does not call external IDE APIs. It remains intentionally non-operational in this version.",
        ],
    )

if st.session_state["advanced_mode"]:
    render_advanced_controls()

maybe_render_guide(
    "Build It",
    "Generates a timestamped compose recipe plus injection artifacts for this run.",
    [
        "Build It freezes the current control state into a deterministic environment package. The output includes compose recipe, payload artifact, and bootstrap script for reproducible execution.",
        "When Local Spin-Up is enabled, startup is attempted immediately after artifact generation. Otherwise, the package is still complete and ready for manual execution.",
    ],
)

if st.button("Build It", type="primary"):
    run_id = f"spool-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    recipe_path = RECIPES_DIR / f"{run_id}.yml"

    prompt_value = st.session_state["quick_prompt"].strip()
    intent_value = prompt_value or st.session_state["intent_text"].strip()
    if not intent_value:
        intent_value = st.session_state["selected_preset"]
    if st.session_state["difficulty_profile"] != "Preset Default":
        intent_value = f"{intent_value} | difficulty={st.session_state['difficulty_profile'].lower()}"

    env_vars = {
        "INTENT": intent_value,
        "NETWORK_PROFILE": NETWORK_OPTIONS[st.session_state["network_profile_label"]],
        "LATENCY_MS": str(st.session_state["latency_ms"]),
        "PACKET_LOSS_PCT": str(st.session_state["packet_loss_pct"]),
        "CPU_BUDGET": CPU_OPTIONS[st.session_state["cpu_budget_label"]],
        "MEMORY_BUDGET": MEMORY_OPTIONS[st.session_state["memory_budget_label"]],
        "DB_ENGINE": DB_OPTIONS[st.session_state["db_engine_label"]],
        "SPOOLER_TARGET_PATH": st.session_state["target_path"].strip() or "/workspace/injected/main.py",
        "SPOOLER_RUN_COMMAND": st.session_state["run_command"].strip(),
        "CHAOS_MODE": to_env_bool(st.session_state["chaos_mode"]),
        "VULNERABLE_DOM": to_env_bool(st.session_state["vulnerable_dom"]),
        "SQL_INJECTION": to_env_bool(st.session_state["sql_injection"]),
        "AUTH_BYPASS": to_env_bool(st.session_state["auth_bypass"]),
        "THIRD_PARTY_OUTAGE": to_env_bool(st.session_state["third_party_outage"]),
        "STRICT_RATE_LIMIT": to_env_bool(st.session_state["strict_rate_limit"]),
    }

    injection_language = st.session_state["injection_language"]
    payload = st.session_state["payload_text"]

    with st.status("Spooling environment...", expanded=True) as status:
        st.write("Generating compose recipe...")
        compose_yaml = build_compose_yaml(run_id, env_vars)
        recipe_path.write_text(compose_yaml, encoding="utf-8")

        st.write("Creating injection files...")
        payload_path, bootstrap_path, extension = write_injection_files(
            run_id=run_id,
            payload=payload,
            language=injection_language,
        )

        if not st.session_state["target_path"].strip().endswith(extension):
            st.warning(
                f"Target path extension does not match selected language ({extension}). "
                "This is allowed, but can be confusing during live walkthroughs."
            )

        if st.session_state["spin_now"]:
            st.write("Attempting local docker compose spin-up...")
            ok, output = run_local_compose(recipe_path)
            if ok:
                st.write("Docker compose spin-up succeeded.")
                status.update(label="Environment Ready", state="complete", expanded=False)
                st.success("Local environment is up.")
            else:
                status.update(label="Recipe Ready (Spin-up failed)", state="error", expanded=True)
                st.error("Recipe and injection files were created, but local spin-up failed.")
            st.code(output, language="bash")
        else:
            status.update(label="Environment Recipe Ready", state="complete", expanded=False)

    st.success(f"Environment package written: `{run_id}`")

    up_command = f"docker compose -f {recipe_path} up -d --remove-orphans"
    down_command = f"docker compose -f {recipe_path} down -v"

    command_col_1, command_col_2 = st.columns(2)
    with command_col_1:
        st.caption("Spin Up")
        st.code(up_command, language="bash")
    with command_col_2:
        st.caption("Tear Down")
        st.code(down_command, language="bash")

    st.caption("Generated Compose Recipe")
    st.code(compose_yaml, language="yaml")

    st.caption("Injected Payload")
    preview_lang = "python" if injection_language == "python" else "bash"
    st.code(payload_path.read_text(encoding="utf-8"), language=preview_lang)

    st.download_button(
        "Download Recipe",
        data=compose_yaml,
        file_name=recipe_path.name,
        mime="text/yaml",
    )

    st.info(
        "Inject files are mounted into `/opt/spooler/injection` and copied by `bootstrap.sh` to `SPOOLER_TARGET_PATH` "
        "when the container starts."
    )

    st.caption(f"Files created: `{recipe_path}` | `{payload_path}` | `{bootstrap_path}`")
