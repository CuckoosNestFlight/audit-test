import streamlit as st
import streamlit.components.v1
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Team Scientist | Diagnostic Strategic", layout="wide")

st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: rgba(128,128,128,0.1);
        padding: 15px; border-radius: 10px;
        border: 1px solid rgba(128,128,128,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# ── LIMBĂ ────────────────────────────────────────────────────
if 'lang' not in st.session_state:
    st.session_state.lang = "Română"

def change_lang():
    st.session_state.lang = st.session_state.lang_select

st.sidebar.selectbox(
    "Limbă / Language", ["Română", "English"],
    key="lang_select", on_change=change_lang
)
lang = st.session_state.lang

# ── SIDEBAR — CONCEPTE ───────────────────────────────────────
with st.sidebar.expander("ℹ️ Ce măsurăm" if lang == "Română" else "ℹ️ What we measure", expanded=False):
    if lang == "Română":
        st.markdown("""
**🧩 Insights** — Sinteza datelor: urgențe, tipare de echipă și acțiuni recomandate.

**🔥 Stres & Burnout** — Riscul de epuizare cronică bazat pe ore lucrate, concediu efectuat, energie și presiune externă.

**🤐 Masca Politicoasă** — Siguranța psihologică: cât de mult se simt oamenii în siguranță să greșească și să propună idei.

**✈️ Risc Plecare** — Probabilitatea de plecare bazată pe stagnare financiară, stare de bine și importanța în rețea.

**🕸️ Rețeaua de Relații** — Cine consultă pe cine informal. Identifică persoanele-cheie, noduri izolate și silozuri de colaborare.
""")
    else:
        st.markdown("""
**🧩 Insights** — Data synthesis: urgencies, team patterns and recommended actions.

**🔥 Stress & Burnout** — Chronic burnout risk based on hours worked, vacation taken, energy and external pressure.

**🤐 Polite Mask** — Psychological safety: how safe people feel to admit mistakes and propose ideas.

**✈️ Leaving Risk** — Departure probability based on financial stagnation, wellbeing and network importance.

**🕸️ Relationship Network** — Who consults whom informally. Identifies key people, isolated nodes and collaboration silos.
""")

# ── SIDEBAR — SALARIU ────────────────────────────────────────
st.sidebar.markdown("---")
salary_label = "Salariu mediu lunar estimat (€)" if lang == "Română" else "Estimated avg monthly salary (€)"
salary_help = (
    "Opțional. Folosit pentru estimarea pierderilor financiare generate de disfuncții de echipă."
    if lang == "Română" else
    "Optional. Used to estimate financial losses from team dysfunctions."
)
salary = st.sidebar.number_input(salary_label, value=1000, step=500, help=salary_help)

# ── SIDEBAR — DISCLAIMER ─────────────────────────────────────
st.sidebar.markdown("---")
if lang == "Română":
    st.sidebar.caption(
        "⚠️ Concluziile din acest raport sunt extrase din date și reprezintă indicatori de analiză, "
        "nu verdicte. Se recomandă discuții directe cu oamenii și eventual analize suplimentare înainte de orice decizie."
    )
else:
    st.sidebar.caption(
        "⚠️ The conclusions in this report are data-driven indicators, not verdicts. "
        "Direct conversations with team members and eventually further analysis are recommended before any decision."
    )

# ── COLUMN MAPPING — human-readable → tehnic ────────────────
COLUMN_MAP = {
    'Cod\nAngajat':              'Nume',
    'Ore\nSăptămână':            'Ore_Saptamana',
    'Vechime\nRol\n(luni)':      'Vechime_Rol',
    'Ultima\nMărire\n(luni)':    'Ultima_Marire',
    'Zile\nConcediu':            'Zile_Concediu',
    'Presiune\nExternă\n(1–5)':  'Presiune_Externa',
    'Scor\nEnergie\n(1–5)':      'Scor_Energie',
    'Idei\nNoi\n(1–5)':          'Idei_Noi',
    'Erori\nAsumate\n(1–5)':     'Erori_Asumate',
    'Sfat De La\n(max. 2, virgulă)': 'Sfat_De_La',
    # fallback fără newline
    'Cod Angajat':               'Nume',
    'Ore Săptămână':             'Ore_Saptamana',
    'Vechime Rol (luni)':        'Vechime_Rol',
    'Ultima Mărire (luni)':      'Ultima_Marire',
    'Zile Concediu':             'Zile_Concediu',
    'Presiune Externă (1–5)':    'Presiune_Externa',
    'Scor Energie (1–5)':        'Scor_Energie',
    'Idei Noi (1–5)':            'Idei_Noi',
    'Erori Asumate (1–5)':       'Erori_Asumate',
    'Sfat De La (max. 2, virgulă)': 'Sfat_De_La',
}

REQUIRED_COLUMNS = [
    'Nume', 'Ore_Saptamana', 'Vechime_Rol', 'Ultima_Marire',
    'Zile_Concediu', 'Presiune_Externa', 'Scor_Energie',
    'Idei_Noi', 'Erori_Asumate', 'Sfat_De_La'
]

PLACEHOLDER_NAMES = ['cod anonim', 'ex:', 'exemplu', 'sample', 'test', 'angajat_ex']
SHEET_ID = "1wY_YZQf72T6d_smb0qYrIWnB_eIolB88IVae4J94ZU0"
SURVEY_LINK = "https://forms.gle/teQU1NCG3Jqao8th9"

# ════════════════════════════════════════════════════════════
# GOOGLE SHEETS LOGGING
# ════════════════════════════════════════════════════════════

def log_to_sheets(df, lang):
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).sheet1
        n = len(df)
        n_critical = int(((df['B_Score'] > 70) | (df['F_Score'] > 65)).sum())
        n_warning  = int(((df['B_Score'].between(50, 70)) | (df['F_Score'].between(40, 65))).sum())
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M"), lang, n,
            round(df['B_Score'].mean(), 1), round(df['F_Score'].mean(), 1),
            round(df['S_Score'].mean(), 1), n_critical, n_warning,
            n - n_critical - n_warning,
            int((df['ONA_InDegree'] >= 3).sum()),
            round((df['S_Raw'] < 3).sum() / n * 100, 1),
            round(df['Ore_Saptamana'].mean(), 1),
            round(df['Zile_Concediu'].mean(), 1),
            round(df['Scor_Energie'].mean(), 1),
            round(df['Presiune_Externa'].mean(), 1),
        ]
        if not sheet.get_all_values():
            sheet.append_row([
                "Timestamp", "Limba", "Nr_Membri",
                "Avg_Burnout", "Avg_FlightRisk", "Avg_MaskRisk",
                "N_Critical", "N_Warning", "N_OK", "N_Hubs", "Silent_Pct",
                "Avg_Ore", "Avg_Concediu", "Avg_Energie", "Avg_Presiune"
            ])
        sheet.append_row(row)
    except Exception:
        pass

# ════════════════════════════════════════════════════════════
# IMPACT FINANCIAR
# ════════════════════════════════════════════════════════════

def compute_financial_impact(df, salary_monthly):
    s = salary_monthly if salary_monthly > 0 else 1000

    # Burnout
    n_burnout_high = int((df['B_Score'] > 70).sum())
    n_burnout_med  = int((df['B_Score'].between(50, 70)).sum())
    burnout_cost   = (n_burnout_high * s * 12 * 0.30) + (n_burnout_med * s * 12 * 0.15)

    # Risc plecare
    n_leaving     = int((df['F_Score'] > 65).sum())
    leaving_min   = n_leaving * s * 6
    leaving_max   = n_leaving * s * 9

    # Mască politicoasă
    n_mask        = int((df['S_Raw'] < 3).sum())
    mask_cost     = n_mask * s * 12 * 0.20

    total_min = burnout_cost + leaving_min + mask_cost
    total_max = burnout_cost + leaving_max + mask_cost

    return {
        "burnout":     burnout_cost,
        "leaving_min": leaving_min,
        "leaving_max": leaving_max,
        "mask":        mask_cost,
        "total_min":   total_min,
        "total_max":   total_max,
        "n_burnout_high": n_burnout_high,
        "n_burnout_med":  n_burnout_med,
        "n_leaving":      n_leaving,
        "n_mask":         n_mask,
        "salary_used":    s,
        "salary_default": salary_monthly <= 0 or salary_monthly == 1000,
    }


def fmt_eur(val):
    return f"€{val:,.0f}".replace(",", ".")


def render_financial_banner(fi, lang, salary_monthly):
    is_default = salary_monthly <= 0 or salary_monthly == 1000
    note = (
        f"{'Calcul bazat pe salariu mediu estimat de' if lang=='Română' else 'Calculated using estimated avg salary of'} "
        f"€{fi['salary_used']:,.0f}{'.' if not is_default else ' (implicit). '}"
        f"{'Ajustați suma în bara laterală pentru situația dvs.' if is_default else ''}"
    )
    total_txt  = "Total pierderi estimate" if lang == "Română" else "Estimated total losses"
    per_year   = "/an" if lang == "Română" else "/year"

    st.markdown(
        f"<div style='background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:14px;"
        f"padding:20px 24px;margin:16px 0;border:1px solid rgba(255,255,255,0.1);'>"
        f"<div style='font-size:12px;color:rgba(255,255,255,0.5);margin-bottom:6px;'>"
        f"{total_txt}</div>"
        f"<div style='font-size:32px;font-weight:700;color:#FF6B6B;line-height:1;'>"
        f"{fmt_eur(fi['total_min'])} – {fmt_eur(fi['total_max'])}"
        f"<span style='font-size:16px;font-weight:400;color:rgba(255,255,255,0.6);'>{per_year}</span></div>"
        f"<div style='margin-top:14px;display:flex;gap:16px;flex-wrap:wrap;'>"
        f"<div style='background:rgba(255,255,255,0.07);border-radius:8px;padding:10px 14px;flex:1;min-width:160px;'>"
        f"<div style='font-size:11px;color:rgba(255,255,255,0.5);margin-bottom:3px;'>🔥 Burnout</div>"
        f"<div style='font-size:18px;font-weight:600;color:#FFA07A;'>{fmt_eur(fi['burnout'])}<span style='font-size:11px;color:rgba(255,255,255,0.4);'>{per_year}</span></div>"
        f"<div style='font-size:11px;color:rgba(255,255,255,0.4);margin-top:3px;'>{'Angajații epuizați lucrează la 70–85% din capacitate. Restul se pierde în erori, lentoare și absenteism ascuns (sunt prezenți doar fizic).' if lang=='Română' else 'Exhausted employees work at 70–85% capacity. The rest is lost in errors, slowdowns and hidden absenteeism (physically present only).'}</div>"
        f"</div>"
        f"<div style='background:rgba(255,255,255,0.07);border-radius:8px;padding:10px 14px;flex:1;min-width:160px;'>"
        f"<div style='font-size:11px;color:rgba(255,255,255,0.5);margin-bottom:3px;'>✈️ {'Risc plecare' if lang=='Română' else 'Leaving risk'}</div>"
        f"<div style='font-size:18px;font-weight:600;color:#FFA07A;'>{fmt_eur(fi['leaving_min'])}–{fmt_eur(fi['leaving_max'])}</div>"
        f"<div style='font-size:11px;color:rgba(255,255,255,0.4);margin-top:3px;'>{'Înlocuirea unui angajat costă 6–9 luni de salariu — recrutare, onboarding și timp până la productivitate deplină.' if lang=='Română' else 'Replacing an employee costs 6–9 months salary — recruitment, onboarding and ramp-up time.'}</div>"
        f"</div>"
        f"<div style='background:rgba(255,255,255,0.07);border-radius:8px;padding:10px 14px;flex:1;min-width:160px;'>"
        f"<div style='font-size:11px;color:rgba(255,255,255,0.5);margin-bottom:3px;'>🤐 {'Mască politicoasă' if lang=='Română' else 'Polite mask'}</div>"
        f"<div style='font-size:18px;font-weight:600;color:#FFA07A;'>{fmt_eur(fi['mask'])}<span style='font-size:11px;color:rgba(255,255,255,0.4);'>{per_year}</span></div>"
        f"<div style='font-size:11px;color:rgba(255,255,255,0.4);margin-top:3px;'>{'Oamenii care tac nu propun, nu semnalează probleme la timp și nu contribuie la soluții. Inovația și calitatea deciziilor scad.' if lang=='Română' else 'People who stay silent dont propose, dont flag problems in time and dont contribute to solutions. Innovation and decision quality decline.'}</div>"
        f"</div>"
        f"</div>"
        f"<div style='margin-top:10px;font-size:11px;color:rgba(255,255,255,0.35);'>{note}</div>"
        f"</div>",
        unsafe_allow_html=True
    )


def render_tab_cost(cost_min, cost_max, label, description, lang, salary_monthly=1000):
    per_year = "/an" if lang == "Română" else "/year"
    range_txt = f"{fmt_eur(cost_min)}–{fmt_eur(cost_max)}" if cost_min != cost_max else fmt_eur(cost_min)
    salary_note = (
        f"Calculat la salariu mediu €{salary_monthly:,.0f}/lună. Ajustați în bara din stânga pentru situația dvs."
        if lang == "Română" else
        f"Calculated at avg salary €{salary_monthly:,.0f}/month. Adjust in the left sidebar for your situation."
    )
    st.markdown(
        f"<div style='background:#FFF8F0;border-left:4px solid #E67E22;border-radius:0 8px 8px 0;"
        f"padding:12px 16px;margin:8px 0;'>"
        f"<div style='font-size:12px;color:#784212;font-weight:600;'>"
        f"💰 {label}: <span style='font-size:16px;'>{range_txt}{per_year}</span></div>"
        f"<div style='font-size:12px;color:#784212;margin-top:4px;'>{description}</div>"
        f"<div style='font-size:11px;color:#A04000;margin-top:6px;font-style:italic;'>ℹ️ {salary_note}</div>"
        f"</div>",
        unsafe_allow_html=True
    )


# ════════════════════════════════════════════════════════════
# FORMULE
# ════════════════════════════════════════════════════════════

def compute_indicators(df):
    df = df.copy()
    mask_placeholder = df['Nume'].astype(str).str.lower().apply(
        lambda x: any(p in x for p in PLACEHOLDER_NAMES)
    )
    df = df[~mask_placeholder].copy()
    df = df[df['Nume'].astype(str).str.strip() != ''].copy()
    df = df.dropna(subset=['Nume']).copy()
    df = df.reset_index(drop=True)

    num_cols = ['Ore_Saptamana', 'Presiune_Externa', 'Idei_Noi', 'Erori_Asumate',
                'Vechime_Rol', 'Ultima_Marire', 'Scor_Energie', 'Zile_Concediu']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df['Ultima_Marire']    = df['Ultima_Marire'].fillna(24)
    df['Zile_Concediu']    = df['Zile_Concediu'].fillna(0)
    df['Scor_Energie']     = df['Scor_Energie'].fillna(3)
    df['Presiune_Externa'] = df['Presiune_Externa'].fillna(3)
    df['Idei_Noi']         = df['Idei_Noi'].fillna(3)
    df['Erori_Asumate']    = df['Erori_Asumate'].fillna(3)
    df['Ore_Saptamana']    = df['Ore_Saptamana'].fillna(40)
    df['Vechime_Rol']      = df['Vechime_Rol'].fillna(12) if 'Vechime_Rol' in df.columns else 12

    S_hours    = ((df['Ore_Saptamana'] - 40) / 20 * 100).clip(0, 100)
    S_vacation = ((20 - df['Zile_Concediu']) / 20 * 100).clip(0, 100)
    S_energy   = ((5 - df['Scor_Energie']) / 4 * 100).clip(0, 100)
    S_pressure = ((df['Presiune_Externa'] - 1) / 4 * 100).clip(0, 100)
    df['B_Score'] = (0.30*S_hours + 0.20*S_vacation + 0.25*S_energy + 0.25*S_pressure).clip(0,100).round(1)

    mask_raw      = (df['Erori_Asumate'] + df['Idei_Noi']) / 2
    df['S_Raw']   = mask_raw.round(2)
    df['S_Score'] = ((5 - mask_raw) / 4 * 100).clip(0, 100).round(1)
    df['S_Size']  = (df['S_Score'] / 10 + 5).clip(5, 20)

    G = nx.DiGraph()
    valid_names = set(df['Nume'].astype(str).values)
    for _, row in df.iterrows():
        name = str(row['Nume'])
        G.add_node(name, B=row['B_Score'])
        sfat = str(row.get('Sfat_De_La', ''))
        if sfat.lower() in ('nan', 'none', ''):
            continue
        for a in [x.strip() for x in sfat.split(',') if x.strip() in valid_names]:
            G.add_edge(name, a)

    n = len(df)
    max_possible = max(n - 1, 1)
    df['ONA_InDegree'] = df['Nume'].apply(lambda x: G.in_degree(str(x)) if str(x) in G else 0)
    df['ONA_Conn']     = df['Nume'].apply(lambda x: G.in_degree(str(x)) + G.out_degree(str(x)) if str(x) in G else 0)
    S_ona = (df['ONA_InDegree'] / max_possible * 100).clip(0, 100)

    S_stagnation = (df['Ultima_Marire'] / df['Vechime_Rol'].clip(lower=1) * 100).clip(0, 100)
    S_wellbeing  = (((5 - df['Scor_Energie']) + (df['Presiune_Externa'] - 1)) / 8 * 100).clip(0, 100)
    df['F_Score'] = (0.40*S_stagnation + 0.40*S_wellbeing + 0.20*S_ona).clip(0, 100).round(1)

    return df, G


# ════════════════════════════════════════════════════════════
# INSIGHTS ENGINE
# ════════════════════════════════════════════════════════════

TEXTS = {
    "Română": {
        "exec_title":    "Rezumat executiv",
        "key_insights":  "Concluzii cheie",
        "exec_all_ok":   "Echipa funcționează în parametri normali. Niciun risc semnificativ identificat în acest ciclu de analiză.",
        "exec_critical": "{n_critical} angajat(ți) prezintă indicatori care sugerează intervenție imediată.",
        "exec_some_risk":"Au fost identificate {n_risk} situații care merită atenție în perioada următoare.",
        "sec_urgent":    "Situații care sugerează intervenție imediată",
        "sec_monitor":   "De urmărit în următoarele 30 de zile",
        "sec_patterns":  "Tipare la nivel de echipă",
        "sec_ok":        "Ce pare să funcționeze bine",
        "action_title":  "Ce poți face concret — sugestii pentru perioada imediat următoare",
        "action_w1":     "🔴 Prioritar — această săptămână",
        "action_w2":     "🟡 Important — în 30 de zile",
        "action_w3":     "🟢 De monitorizat",
        "causes_note":   "Cauzele pot fi la nivel de angajat, de sistem sau de stilul de conducere. Pornind de la rezultatele acestui audit, cauzele pot fi în viitor explorate mai ușor.",
        "pattern_cultural_silence": "Posibilă problemă de microcultură — siguranță psihologică",
        "pattern_cultural_silence_desc": (
            "{pct}% din echipă are scor Polite Mask sub 3. Aceasta poate indica o problemă sistemică "
            "de microcultură, nu individuală. Oamenii tac pentru că nu se simt în siguranță să greșească "
            "sau să propună. Intervenția necesară este la nivel de echipă, nu de angajat."
        ),
        "pattern_hub_risk": "Persoană-cheie supraîncărcată — risc sistemic",
        "pattern_hub_risk_desc": (
            "{name} este consultat(ă) de {n_conn} colegi și prezintă simultan indicatori ridicați "
            "de stres & burnout ({b:.0f}/100) și risc de plecare ({f:.0f}/100). "
            "Dacă această persoană pleacă sau se epuizează, fluxul informal de cunoaștere al echipei "
            "se poate întrerupe brusc. Acesta este cel mai costisitor scenariu de risc din această analiză."
        ),
        "pattern_isolation": "Deconectare dublă — izolare și tăcere",
        "pattern_isolation_desc": (
            "{names} prezintă izolare în rețeaua de relații combinată cu un scor scăzut de siguranță "
            "psihologică. Aceștia nu solicită ajutor și contribuie limitat — un posibil semnal timpuriu "
            "de dezangajare. De luat în calcul și alți factori (stil de lucru, personalitate)."
        ),
        "pattern_silent_stars": "Performeri cu potențial neexploatat",
        "pattern_silent_stars_desc": (
            "{names} prezintă indicatori de stres și risc în parametri buni, dar un scor scăzut "
            "de siguranță psihologică. Contribuția lor poate fi mai mare dacă mediul devine "
            "mai permisiv cu greșelile și propunerile."
        ),
        "pattern_ok": "Nucleu cu indicatori stabili",
        "pattern_ok_desc": "{names} prezintă toți indicatorii în parametri normali în această analiză.",
        "burnout_critical": (
            "{name} prezintă indicatori de stres ridicat ({b:.0f}/100). "
            "Lucrează {ore}h/săptămână, {concediu} zi(e) concediu efectuate, energie {energie}/5. "
            "Merită o conversație 1:1 în perioada imediat următoare."
        ),
        "burnout_warning": (
            "{name} prezintă semne de acumulare a oboselii ({b:.0f}/100). "
            "Energie {energie}/5, {ore}h/săpt. — de urmărit în următoarele săptămâni."
        ),
        "burnout_ok": "{name} prezintă indicatori de energie și efort în parametri normali.",
        "leaving_critical": (
            "{name} prezintă factori de risc de plecare ridicați ({f:.0f}/100). "
            "Ultima ajustare salarială: acum {marire} luni | Energie: {energie}/5 | "
            "Consultat de {conn} colegi.{cost_str}"
        ),
        "leaving_monitor": (
            "{name} prezintă factori de risc moderați ({f:.0f}/100). "
            "Stagnare financiară ({marire} luni) — o conversație de carieră în 30 de zile ar fi utilă."
        ),
        "leaving_ok": "{name} prezintă indicatori de stabilitate în această analiză.",
        "mask_critical": (
            "{name} are un scor scăzut de siguranță psihologică ({mask:.1f}/5). "
            "Contribuie limitat cu idei și recunoașterea greșelilor. "
            "O conversație 1:1 axată pe siguranță, nu pe performanță, poate fi utilă."
        ),
        "mask_silent": (
            "{name} are potențial de contribuție mai mare ({mask:.1f}/5). "
            "Un mediu mai permisiv cu greșelile poate debloca această contribuție."
        ),
        "mask_ok": "{name} contribuie activ și pare să se simtă în siguranță să greșească și să propună.",
        "action_burnout_critical": "Planifică o discuție 1:1 cu {name} — axată pe ascultare, nu evaluare.",
        "action_leaving_critical": "Inițiază o conversație de carieră cu {name} despre perspective și satisfacție.",
        "action_mask_critical": "Cu {name}: creează un context privat unde greșeala este tratată ca informație, nu eșec.",
        "action_hub": "Distribuie treptat din responsabilitățile informale ale lui {name} către alți colegi.",
        "action_isolated": "Include {name} explicit în cel puțin o decizie de echipă în perioada imediat următoare.",
        "cost_str_template": " Cost estimat înlocuire: {cost}.",
        "replacement_cost": "~{min}–{max} (6–9 luni)",
    },
    "English": {
        "exec_title":    "Executive summary",
        "key_insights":  "Key insights",
        "exec_all_ok":   "The team is operating within normal parameters. No significant risks identified in this analysis cycle.",
        "exec_critical": "{n_critical} employee(s) show indicators that suggest immediate attention.",
        "exec_some_risk":"{n_risk} situation(s) were identified that warrant attention in the coming period.",
        "sec_urgent":    "Situations suggesting immediate attention",
        "sec_monitor":   "To follow up within 30 days",
        "sec_patterns":  "Team-level patterns",
        "sec_ok":        "What appears to be working well",
        "action_title":  "What you can do concretely — suggestions for the immediate period ahead",
        "action_w1":     "🔴 Priority — this week",
        "action_w2":     "🟡 Important — within 30 days",
        "action_w3":     "🟢 To monitor",
        "causes_note":   "Causes may lie at the employee level, the system level, or in leadership style. Based on the results of this audit, causes can be explored more easily in the future.",
        "pattern_cultural_silence": "Possible micro-culture issue — psychological safety",
        "pattern_cultural_silence_desc": (
            "{pct}% of the team scores below 3 on the Polite Mask indicator. This may indicate a systemic "
            "micro-culture issue, not an individual one. People are staying silent because they don't feel "
            "safe to make mistakes or propose ideas. The intervention needed is at team level, not per person."
        ),
        "pattern_hub_risk": "Overloaded key person — systemic risk",
        "pattern_hub_risk_desc": (
            "{name} is consulted by {n_conn} colleagues and simultaneously shows elevated "
            "stress & burnout indicators ({b:.0f}/100) and leaving risk ({f:.0f}/100). "
            "If this person leaves or burns out, the team's informal knowledge flow may break down abruptly. "
            "This is the most costly risk scenario in this analysis."
        ),
        "pattern_isolation": "Dual disconnection — isolation and silence",
        "pattern_isolation_desc": (
            "{names} show network isolation combined with a low psychological safety score. "
            "They don't seek help and contribute minimally — a possible early signal of disengagement. "
            "Other factors should also be considered (work style, personality)."
        ),
        "pattern_silent_stars": "Performers with untapped potential",
        "pattern_silent_stars_desc": (
            "{names} show good stress and risk indicators but a low psychological safety score. "
            "Their contribution could be greater if the environment becomes more permissive "
            "with mistakes and proposals."
        ),
        "pattern_ok": "Core with stable indicators",
        "pattern_ok_desc": "{names} show all indicators within normal parameters in this analysis.",
        "burnout_critical": (
            "{name} shows elevated stress indicators ({b:.0f}/100). "
            "Working {ore}h/week, {concediu} vacation day(s) taken, energy {energie}/5. "
            "A 1:1 conversation in the near term is worth considering."
        ),
        "burnout_warning": (
            "{name} shows signs of accumulating fatigue ({b:.0f}/100). "
            "Energy {energie}/5, {ore}h/week — worth monitoring over the next few weeks."
        ),
        "burnout_ok": "{name} shows energy and effort indicators within normal parameters.",
        "leaving_critical": (
            "{name} shows elevated leaving risk factors ({f:.0f}/100). "
            "Last salary adjustment: {marire} months ago | Energy: {energie}/5 | "
            "Consulted by {conn} colleagues.{cost_str}"
        ),
        "leaving_monitor": (
            "{name} shows moderate risk factors ({f:.0f}/100). "
            "Financial stagnation ({marire} months) — a career conversation within 30 days would be useful."
        ),
        "leaving_ok": "{name} shows stability indicators in this analysis.",
        "mask_critical": (
            "{name} has a low psychological safety score ({mask:.1f}/5). "
            "Contributes minimally with ideas and error acknowledgment. "
            "A 1:1 conversation focused on safety, not performance, may be helpful."
        ),
        "mask_silent": (
            "{name} has potential for greater contribution ({mask:.1f}/5). "
            "A more permissive environment around mistakes may unlock this."
        ),
        "mask_ok": "{name} contributes actively and appears to feel safe to make mistakes and propose ideas.",
        "action_burnout_critical": "Schedule a 1:1 with {name} — focused on listening, not evaluation.",
        "action_leaving_critical": "Initiate a career conversation with {name} about prospects and satisfaction.",
        "action_mask_critical": "With {name}: create a private context where mistakes are treated as information, not failure.",
        "action_hub": "Gradually distribute some of {name}'s informal responsibilities to other colleagues.",
        "action_isolated": "Explicitly include {name} in at least one team decision in the near term.",
        "cost_str_template": " Estimated replacement cost: {cost}.",
        "replacement_cost": "~{min}–{max} (6–9 months)",
    }
}


def fmt_cost(salary_monthly, t):
    if salary_monthly <= 0:
        return ""
    s = salary_monthly
    return t["cost_str_template"].format(
        cost=t["replacement_cost"].format(
            min=f"€{s*6:,.0f}", max=f"€{s*9:,.0f}"
        )
    )


def insight_card(text, level="info"):
    colors = {
        "critical": ("#FDEDEC", "#C0392B", "▲", "#7B241C"),
        "warning":  ("#FEF9E7", "#E67E22", "◉", "#784212"),
        "ok":       ("#EAFAF1", "#1E8449", "✓", "#1D6A39"),
        "info":     ("#EBF5FB", "#2471A3", "→", "#1A5276"),
    }
    bg, border, icon, tc = colors.get(level, colors["info"])
    st.markdown(
        f"<div style='background:{bg};border-left:3px solid {border};"
        f"border-radius:0 8px 8px 0;padding:12px 16px;margin:6px 0;"
        f"font-size:16px;line-height:1.7;color:{tc}'>"
        f"<span style='color:{border};margin-right:8px'>{icon}</span>{text}</div>",
        unsafe_allow_html=True
    )


def action_card(text, level="w2"):
    bg = {"w1": "#FEF5F5", "w2": "#FEFDF0", "w3": "#F0FEF5"}.get(level, "#F4F6F7")
    st.markdown(
        f"<div style='background:{bg};border:1px solid #D5D8DC;"
        f"border-radius:8px;padding:10px 16px;margin:4px 0;"
        f"font-size:13px;line-height:1.6;color:#2C3E50'>"
        f"<span style='color:#E67E22;margin-right:8px;font-weight:600'>→</span>{text}</div>",
        unsafe_allow_html=True
    )


def section_header(title, color="#1C2833"):
    st.markdown(
        f"<div style='margin:24px 0 10px;padding:8px 14px;"
        f"background:rgba(255,255,255,0.85);border-left:4px solid {color};"
        f"border-radius:0 6px 6px 0;font-weight:600;font-size:15px;color:{color}'>"
        f"{title}</div>",
        unsafe_allow_html=True
    )


def generate_individual_insights(row, t, salary):
    name     = str(row['Nume'])
    b        = float(row['B_Score'])
    f        = float(row['F_Score'])
    mask     = float(row['S_Raw'])
    ore      = int(row.get('Ore_Saptamana', 40))
    energie  = int(row.get('Scor_Energie', 3))
    concediu = int(row.get('Zile_Concediu', 0))
    marire   = int(row.get('Ultima_Marire', 24))
    conn     = int(row.get('ONA_InDegree', 0))
    cost_str = fmt_cost(salary, t)
    actions_w1, actions_w2, actions_w3 = [], [], []

    if b > 70:
        bt, bl = t["burnout_critical"].format(name=name,b=b,ore=ore,concediu=concediu,energie=energie), "critical"
        actions_w1.append(t["action_burnout_critical"].format(name=name))
    elif b > 50:
        bt, bl = t["burnout_warning"].format(name=name,b=b,ore=ore,energie=energie), "warning"
        actions_w2.append(t["action_burnout_critical"].format(name=name))
    else:
        bt, bl = t["burnout_ok"].format(name=name), "ok"

    if f > 65:
        ft, fl = t["leaving_critical"].format(name=name,f=f,marire=marire,energie=energie,conn=conn,cost_str=cost_str), "critical"
        actions_w1.append(t["action_leaving_critical"].format(name=name))
    elif f > 40:
        ft, fl = t["leaving_monitor"].format(name=name,f=f,marire=marire), "warning"
        actions_w2.append(t["action_leaving_critical"].format(name=name))
    else:
        ft, fl = t["leaving_ok"].format(name=name), "ok"

    if mask < 3:
        mt, ml = t["mask_critical"].format(name=name,mask=mask), "critical"
        actions_w2.append(t["action_mask_critical"].format(name=name))
    elif mask <= 4:
        mt, ml = t["mask_silent"].format(name=name,mask=mask), "warning"
        actions_w3.append(t["action_mask_critical"].format(name=name))
    else:
        mt, ml = t["mask_ok"].format(name=name), "ok"

    return {
        "burnout": (bt, bl), "leaving": (ft, fl), "mask": (mt, ml),
        "actions_w1": actions_w1, "actions_w2": actions_w2, "actions_w3": actions_w3,
        "is_critical": b > 70 or f > 65,
        "is_warning":  (50 < b <= 70) or (40 < f <= 65),
    }


def detect_team_patterns(df, G, t):
    patterns = []
    n = len(df)
    silent_pct = (df['S_Raw'] < 3).sum() / n * 100
    if silent_pct >= 30:
        patterns.append({
            "title": t["pattern_cultural_silence"],
            "text":  t["pattern_cultural_silence_desc"].format(pct=int(silent_pct)),
            "level": "critical" if silent_pct >= 50 else "warning"
        })
    for _, row in df[df['ONA_InDegree'] >= 3].iterrows():
        if row['B_Score'] > 60 and row['F_Score'] > 50:
            patterns.append({
                "title": t["pattern_hub_risk"],
                "text":  t["pattern_hub_risk_desc"].format(
                    name=row['Nume'], n_conn=int(row['ONA_InDegree']),
                    b=row['B_Score'], f=row['F_Score']),
                "level": "critical"
            })
    isolated = df[(df['ONA_Conn'] <= 1) & (df['S_Raw'] < 3)]
    if not isolated.empty:
        patterns.append({
            "title": t["pattern_isolation"],
            "text":  t["pattern_isolation_desc"].format(names=", ".join(isolated['Nume'].tolist())),
            "level": "warning"
        })
    silent_stars = df[(df['B_Score'] < 50) & (df['F_Score'] < 40) & (df['S_Raw'] < 3)]
    if not silent_stars.empty:
        patterns.append({
            "title": t["pattern_silent_stars"],
            "text":  t["pattern_silent_stars_desc"].format(names=", ".join(silent_stars['Nume'].tolist())),
            "level": "info"
        })
    stable = df[(df['B_Score'] < 40) & (df['F_Score'] < 35) & (df['S_Raw'] >= 3.5)]
    if not stable.empty:
        patterns.append({
            "title": t["pattern_ok"],
            "text":  t["pattern_ok_desc"].format(names=", ".join(stable['Nume'].tolist())),
            "level": "ok"
        })
    return patterns


def render_insights_tab(df, G, lang, salary, fi):
    t = TEXTS[lang]
    n_critical = int(((df['B_Score'] > 70) | (df['F_Score'] > 65)).sum())
    n_warning  = int(((df['B_Score'].between(50, 70)) | (df['F_Score'].between(40, 65))).sum())
    n_ok       = len(df) - n_critical - n_warning
    n_risk     = n_critical + n_warning

    section_header(f"🔬 {t['exec_title']}", "#2E4057")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div style='background:#FDEDEC;border-radius:12px;padding:20px;text-align:center;border:1px solid #E74C3C22'><div style='font-size:42px;font-weight:700;color:#C0392B'>{n_critical}</div><div style='font-size:13px;color:#7B241C;margin-top:4px'>{'🔴 Intervenție imediată' if lang=='Română' else '🔴 Immediate attention'}</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='background:#FEF9E7;border-radius:12px;padding:20px;text-align:center;border:1px solid #E67E2222'><div style='font-size:42px;font-weight:700;color:#E67E22'>{n_warning}</div><div style='font-size:13px;color:#784212;margin-top:4px'>{'🟡 De urmărit' if lang=='Română' else '🟡 To monitor'}</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div style='background:#EAFAF1;border-radius:12px;padding:20px;text-align:center;border:1px solid #27AE6022'><div style='font-size:42px;font-weight:700;color:#1E8449'>{n_ok}</div><div style='font-size:13px;color:#1D6A39;margin-top:4px'>{'🟢 În parametri' if lang=='Română' else '🟢 Within range'}</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)

    # Mențiunea despre cauze
    insight_card(t["causes_note"], "info")

    section_header(f"💡 {t['key_insights']}", "#2E4057")
    if n_critical > 0:
        insight_card(t["exec_critical"].format(n_critical=n_critical), "critical")
    if n_warning > 0:
        insight_card(t["exec_some_risk"].format(n_risk=n_risk), "warning")
    if n_critical == 0 and n_warning == 0:
        insight_card(t["exec_all_ok"], "ok")

    hubs = df[(df['ONA_InDegree'] >= 3) & (df['B_Score'] > 60) & (df['F_Score'] > 50)]
    for _, row in hubs.iterrows():
        if lang == "Română":
            insight_card(f"<b>{row['Nume']}</b> este persoana-cheie a echipei și prezintă simultan stres ridicat ({row['B_Score']:.0f}) și risc de plecare ridicat ({row['F_Score']:.0f}). Acesta este scenariul prioritar din această analiză.", "critical")
        else:
            insight_card(f"<b>{row['Nume']}</b> is the team's key person and simultaneously shows elevated stress ({row['B_Score']:.0f}) and leaving risk ({row['F_Score']:.0f}). This is the priority scenario in this analysis.", "critical")

    patterns = detect_team_patterns(df, G, t)
    if patterns:
        section_header(f"🕸️ {t['sec_patterns']}", "#8E44AD")
        for p in patterns:
            with st.expander(p["title"], expanded=(p["level"] == "critical")):
                insight_card(p["text"], p["level"])

    urgent = df[(df['B_Score'] > 70) | (df['F_Score'] > 65)].copy()
    urgent['_max'] = urgent[['B_Score', 'F_Score']].max(axis=1)
    urgent = urgent.sort_values('_max', ascending=False)
    if not urgent.empty:
        section_header(f"⚠️ {t['sec_urgent']}", "#C0392B")
        for _, row in urgent.iterrows():
            ins = generate_individual_insights(row, t, salary)
            with st.expander(f"{row['Nume']} — Burnout: {row['B_Score']:.0f} | {'Risc Plecare' if lang=='Română' else 'Leaving Risk'}: {row['F_Score']:.0f} | Mask: {row['S_Raw']:.1f}", expanded=True):
                insight_card(f"🔥 {ins['burnout'][0]}", ins['burnout'][1])
                insight_card(f"✈️ {ins['leaving'][0]}", ins['leaving'][1])
                insight_card(f"🤐 {ins['mask'][0]}", ins['mask'][1])

    monitor = df[~((df['B_Score'] > 70) | (df['F_Score'] > 65)) & ((df['B_Score'] > 50) | (df['F_Score'] > 40))].copy()
    monitor['_max'] = monitor[['B_Score', 'F_Score']].max(axis=1)
    monitor = monitor.sort_values('_max', ascending=False)
    if not monitor.empty:
        section_header(f"👁️ {t['sec_monitor']}", "#E67E22")
        for _, row in monitor.iterrows():
            ins = generate_individual_insights(row, t, salary)
            with st.expander(f"{row['Nume']} — Burnout: {row['B_Score']:.0f} | {'Risc Plecare' if lang=='Română' else 'Leaving Risk'}: {row['F_Score']:.0f} | Mask: {row['S_Raw']:.1f}", expanded=False):
                insight_card(f"🔥 {ins['burnout'][0]}", ins['burnout'][1])
                insight_card(f"✈️ {ins['leaving'][0]}", ins['leaving'][1])
                insight_card(f"🤐 {ins['mask'][0]}", ins['mask'][1])

    all_w1, all_w2, all_w3 = [], [], []
    for _, row in df.iterrows():
        ins = generate_individual_insights(row, t, salary)
        all_w1.extend(ins["actions_w1"])
        all_w2.extend(ins["actions_w2"])
        all_w3.extend(ins["actions_w3"])
    hubs_df = df[df['ONA_InDegree'] >= 3].sort_values('ONA_InDegree', ascending=False)
    if not hubs_df.empty:
        all_w1.append(t["action_hub"].format(name=hubs_df.iloc[0]['Nume']))
    for _, row in df[(df['ONA_Conn'] <= 1) & (df['S_Raw'] < 3)].iterrows():
        all_w3.append(t["action_isolated"].format(name=row['Nume']))

    if any([all_w1, all_w2, all_w3]):
        section_header(f"✅ {t['action_title']}", "#1E8449")
        if all_w1:
            st.markdown(f"**{t['action_w1']}**")
            for a in all_w1[:3]: action_card(a, "w1")
        if all_w2:
            st.markdown(f"**{t['action_w2']}**")
            for a in all_w2[:3]: action_card(a, "w2")
        if all_w3:
            st.markdown(f"**{t['action_w3']}**")
            for a in all_w3[:3]: action_card(a, "w3")

    stable = df[(df['B_Score'] < 40) & (df['F_Score'] < 35) & (df['S_Raw'] >= 3.5)]
    if not stable.empty:
        section_header(f"💚 {t['sec_ok']}", "#1E8449")
        insight_card(t["pattern_ok_desc"].format(names=", ".join(stable['Nume'].tolist())), "ok")


# ════════════════════════════════════════════════════════════
# LANDING PAGE
# ════════════════════════════════════════════════════════════

def render_landing_page(lang, template_bytes):
    if lang == "Română":
        st.markdown("""
<div style='max-width:780px;margin:0 auto;padding:2rem 0 0.5rem;'>
  <div style='font-size:12px;font-weight:500;color:#888;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:1.2rem;'>🔬 TeamScientist</div>
  <p style='font-size:17px;line-height:1.8;margin:0 0 1rem;'>
    Mă numesc <strong>Răzvan Ghebaur</strong> și de peste 20 de ani ajut manageri și antreprenori să creeze și să mențină echipe eficiente.
  </p>
  <p style='font-size:17px;line-height:1.8;margin:0 0 1rem;'>
    Vă invit să testați un instrument care vă arată concret ce funcționează bine în echipa dvs., dar și ce pierderi financiare vin din comportamentele care nu susțin performanța. Veți avea nevoie de 15–20 de minute să adunați câteva date anonimizate pe care le aveți la îndemână. Veți primi în schimb o diagnoză valoroasă și un set de acțiuni concrete de management pe care să le puneți în practică.
  </p>
  <p style='font-size:17px;line-height:1.8;margin:0 0 1rem;'>
    Dacă aveți în coordonare directă între <strong>8 și 20 de oameni</strong> — acest instrument este pentru dvs.
  </p>
  <p style='font-size:17px;line-height:1.8;margin:0 0 1.5rem;'>
    Cei care testează acum și vor să rămână la curent cu evoluția instrumentului sunt bineveniți să mă contacteze direct pe <a href='https://linkedin.com/in/razvanghebaur' target='_blank' style='color:#2471A3;'>LinkedIn</a>.
  </p>
  <div style='border-left:3px solid rgba(128,128,128,0.25);padding:0.75rem 1.1rem;margin:0 0 0.5rem;background:rgba(128,128,128,0.04);border-radius:0 8px 8px 0;'>
    <p style='font-size:13px;line-height:1.7;margin:0;opacity:0.75;'>
      💡 La finalul diagnosticului veți găsi un formular scurt de feedback — 2 minute, anonim.
    </p>
  </div>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
<div style='max-width:780px;margin:0 auto;padding:2rem 0 0.5rem;'>
  <div style='font-size:12px;font-weight:500;color:#888;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:1.2rem;'>🔬 TeamScientist</div>
  <p style='font-size:17px;line-height:1.8;margin:0 0 1rem;'>
    My name is <strong>Răzvan Ghebaur</strong> and for over 20 years I have been helping managers and entrepreneurs build and maintain efficient teams.
  </p>
  <p style='font-size:17px;line-height:1.8;margin:0 0 1rem;'>
    I invite you to test an instrument that shows you concretely what is working well in your team, and what financial losses come from behaviours that don't support performance. You'll need 15–20 minutes to gather some anonymised data you already have at hand. In return, you'll receive a valuable diagnosis and a concrete set of management actions to put into practice.
  </p>
  <p style='font-size:17px;line-height:1.8;margin:0 0 1rem;'>
    If you directly manage between <strong>8 and 20 people</strong> — this instrument is for you.
  </p>
  <p style='font-size:17px;line-height:1.8;margin:0 0 1.5rem;'>
    Those who test now and want to stay informed about the instrument's evolution are welcome to contact me directly on <a href='https://linkedin.com/in/razvanghebaur' target='_blank' style='color:#2471A3;'>LinkedIn</a>.
  </p>
  <div style='border-left:3px solid rgba(128,128,128,0.25);padding:0.75rem 1.1rem;margin:0 0 0.5rem;background:rgba(128,128,128,0.04);border-radius:0 8px 8px 0;'>
    <p style='font-size:13px;line-height:1.7;margin:0;opacity:0.75;'>
      💡 At the end of the diagnostic you will find a short feedback form — 2 minutes, anonymous.
    </p>
  </div>
</div>""", unsafe_allow_html=True)

    # ── CE CÂȘTIGI ────────────────────────────────────────────
    st.markdown(f"<p style='font-size:13px;font-weight:500;color:#888;letter-spacing:0.06em;text-transform:uppercase;margin:1.5rem 0 0.75rem;'>{'Ce câștigi' if lang=='Română' else 'What you gain'}</p>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div style='background:#FCEBEB;border-radius:12px;padding:1.25rem;border:1px solid #F09595;'><div style='font-size:22px;margin-bottom:10px;'>🔥</div><p style='font-size:14px;font-weight:600;color:#A32D2D;margin:0 0 8px;'>Previi burnout-ul</p><p style='font-size:13px;line-height:1.55;color:#791F1F;margin:0;'>Identifici cine lucrează peste limită și cine are energia în scădere — înainte ca problema să devină vizibilă.</p></div>" if lang=="Română" else "<div style='background:#FCEBEB;border-radius:12px;padding:1.25rem;border:1px solid #F09595;'><div style='font-size:22px;margin-bottom:10px;'>🔥</div><p style='font-size:14px;font-weight:600;color:#A32D2D;margin:0 0 8px;'>Prevent burnout</p><p style='font-size:13px;line-height:1.55;color:#791F1F;margin:0;'>Identify who is working beyond their limit and whose energy is declining — before it becomes a visible problem.</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='background:#FAEEDA;border-radius:12px;padding:1.25rem;border:1px solid #FAC775;'><div style='font-size:22px;margin-bottom:10px;'>✈️</div><p style='font-size:14px;font-weight:600;color:#854F0B;margin:0 0 8px;'>Reduci riscul de plecare</p><p style='font-size:13px;line-height:1.55;color:#633806;margin:0;'>Afli cine are factori de risc și cât te-ar costa înlocuirea — cu cifre, nu cu presupuneri.</p></div>" if lang=="Română" else "<div style='background:#FAEEDA;border-radius:12px;padding:1.25rem;border:1px solid #FAC775;'><div style='font-size:22px;margin-bottom:10px;'>✈️</div><p style='font-size:14px;font-weight:600;color:#854F0B;margin:0 0 8px;'>Reduce leaving risk</p><p style='font-size:13px;line-height:1.55;color:#633806;margin:0;'>Find out who has risk factors and what replacement would cost — with numbers, not assumptions.</p></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div style='background:#E1F5EE;border-radius:12px;padding:1.25rem;border:1px solid #5DCAA5;'><div style='font-size:22px;margin-bottom:10px;'>🕸️</div><p style='font-size:14px;font-weight:600;color:#0F6E56;margin:0 0 8px;'>Vezi rețeaua de relații din echipă</p><p style='font-size:13px;line-height:1.55;color:#085041;margin:0;'>Descoperi cine sunt persoanele-cheie la care apelează cei mai mulți din echipă, cine e izolat și unde există grupuri sau persoane care nu colaborează între ele.</p></div>" if lang=="Română" else "<div style='background:#E1F5EE;border-radius:12px;padding:1.25rem;border:1px solid #5DCAA5;'><div style='font-size:22px;margin-bottom:10px;'>🕸️</div><p style='font-size:14px;font-weight:600;color:#0F6E56;margin:0 0 8px;'>See the relationship network</p><p style='font-size:13px;line-height:1.55;color:#085041;margin:0;'>Discover who the key people are that most of the team turns to, who is isolated, and where groups or individuals are not collaborating.</p></div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:2rem'></div>", unsafe_allow_html=True)

    # ── CUM FUNCȚIONEAZĂ ─────────────────────────────────────
    st.markdown(f"<p style='font-size:13px;font-weight:500;color:#888;letter-spacing:0.06em;text-transform:uppercase;margin:0 0 0.75rem;'>{'Cum funcționează' if lang=='Română' else 'How it works'}</p>", unsafe_allow_html=True)

    p1, p2, p3 = st.columns(3)
    num_style = "width:32px;height:32px;border-radius:50%;background:#1F3864;display:inline-flex;align-items:center;justify-content:center;font-size:14px;font-weight:600;color:#fff;flex-shrink:0;"
    card_style = "background:var(--color-background-primary);border-radius:12px;border:1px solid var(--color-border-secondary);padding:1.25rem;"

    with p1:
        st.markdown(
            f"<div style='{card_style}'>"
            f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:10px;'>"
            f"<span style='{num_style}'>1</span>"
            f"<div><p style='font-size:11px;color:#888;margin:0;'>{'Pasul 1' if lang=='Română' else 'Step 1'}</p>"
            f"<p style='font-size:14px;font-weight:600;color:inherit;margin:0;'>{'Descarcă și completează' if lang=='Română' else 'Download and fill in'}</p></div></div>"
            f"<p style='font-size:11px;color:#888;margin:0 0 8px;'>{'~15 minute' if lang=='Română' else '~15 minutes'}</p>"
            f"<p style='font-size:12px;line-height:1.55;opacity:0.75;margin:0 0 1rem;'>{'Descarcă template-ul Excel și completează datele echipei tale urmând instrucțiunile din fișier. Datele sunt cele pe care le știi deja sau pe care le poți afla ușor.' if lang=='Română' else 'Download the Excel template and fill in your team data following the instructions in the file. The data is what you already know or can easily find out.'}"
            f"</p></div>", unsafe_allow_html=True)
        st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
        if template_bytes:
            st.download_button(
                label="📥 Descarcă template Excel" if lang=="Română" else "📥 Download Excel template",
                data=template_bytes,
                file_name="TeamScientist_Template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    with p2:
        st.markdown(
            f"<div style='{card_style}'>"
            f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:10px;'>"
            f"<span style='{num_style}'>2</span>"
            f"<div><p style='font-size:11px;color:#888;margin:0;'>{'Pasul 2' if lang=='Română' else 'Step 2'}</p>"
            f"<p style='font-size:14px;font-weight:600;color:inherit;margin:0;'>{'Încarcă fișierul completat' if lang=='Română' else 'Upload the completed file'}</p></div></div>"
            f"<p style='font-size:11px;color:#888;margin:0 0 8px;'>{'30 secunde' if lang=='Română' else '30 seconds'}</p>"
            f"<p style='font-size:12px;line-height:1.55;opacity:0.75;margin:0 0 1rem;'>{'Încarcă fișierul completat direct în aplicație. Diagnosticul se generează automat.' if lang=='Română' else 'Upload the completed file directly into the application. The diagnostic is generated automatically.'}"
            f"</p></div>", unsafe_allow_html=True)
        st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "upload", type=["xlsx"], label_visibility="collapsed"
        )

    with p3:
        st.markdown(
            f"<div style='{card_style}'>"
            f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:10px;'>"
            f"<span style='{num_style}'>3</span>"
            f"<div><p style='font-size:11px;color:#888;margin:0;'>{'Pasul 3' if lang=='Română' else 'Step 3'}</p>"
            f"<p style='font-size:14px;font-weight:600;color:inherit;margin:0;'>{'Explorează diagnosticul' if lang=='Română' else 'Explore the diagnostic'}</p></div></div>"
            f"<p style='font-size:11px;color:#888;margin:0 0 8px;'>{'cât vrei' if lang=='Română' else 'as long as you want'}</p>"
            f"<p style='font-size:12px;line-height:1.55;opacity:0.75;margin:0;'>{'5 tab-uri cu vizualizări clare și recomandări concrete. De la rezumat executiv până la harta relațiilor din echipă.' if lang=='Română' else '5 tabs with clear visualizations and concrete recommendations. From executive summary to the team relationship map.'}"
            f"</p></div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

    anon = "Date 100% anonimizate. Niciun nume real nu este stocat sau procesat." if lang=="Română" else "100% anonymized data. No real names are stored or processed."
    li   = "Întrebări? LinkedIn →" if lang=="Română" else "Questions? LinkedIn →"
    st.markdown(
        f"<div style='display:flex;align-items:center;justify-content:space-between;"
        f"padding:0.75rem 1rem;background:rgba(128,128,128,0.05);border-radius:8px;"
        f"border:0.5px solid rgba(128,128,128,0.15);'>"
        f"<div style='display:flex;align-items:center;gap:8px;'>"
        f"<div style='width:8px;height:8px;border-radius:50%;background:#1D9E75;flex-shrink:0;'></div>"
        f"<span style='font-size:12px;opacity:0.7;'>{anon}</span></div>"
        f"<a href='https://linkedin.com/in/razvanghebaur' target='_blank' "
        f"style='font-size:12px;color:#2471A3;text-decoration:none;white-space:nowrap;margin-left:1rem;'>{li}</a>"
        f"</div>", unsafe_allow_html=True
    )
    return uploaded_file


# ════════════════════════════════════════════════════════════
# APP PRINCIPAL
# ════════════════════════════════════════════════════════════

try:
    with open("TeamScientist_Template.xlsx", "rb") as f:
        template_bytes = f.read()
except FileNotFoundError:
    template_bytes = b""

uploaded_file = render_landing_page(lang, template_bytes)

if uploaded_file:
    try:
        # Detectăm sheet-ul cu date (cel care contine 'Date' in nume)
        xl = pd.ExcelFile(uploaded_file)
        target_sheet = xl.sheet_names[0]
        for sh in xl.sheet_names:
            if 'Date' in sh or 'Data' in sh or 'date' in sh.lower():
                target_sheet = sh
                break

        df_raw = pd.read_excel(uploaded_file, sheet_name=target_sheet, header=None)

        # Detectăm rândul de header
        header_row = 0
        for i, row in df_raw.iterrows():
            row_vals = [str(v).strip() for v in row.values if pd.notna(v)]
            if any('Cod' in v or 'Nume' in v or 'Ore' in v for v in row_vals):
                header_row = i
                break

        df_raw = pd.read_excel(uploaded_file, sheet_name=target_sheet, header=header_row)

        # Curăm coloanele și aplicăm mapping
        df_raw.columns = [str(c).strip() if pd.notna(c) else '' for c in df_raw.columns]
        df_raw = df_raw.rename(columns=COLUMN_MAP)
        df_raw = df_raw.loc[:, df_raw.columns != '']
        df_raw = df_raw.dropna(how='all')

        # Validare coloane
        missing = [c for c in REQUIRED_COLUMNS if c not in df_raw.columns]
        if missing:
            st.error(f"❌ {'Lipsesc coloanele obligatorii' if lang=='Română' else 'Missing required columns'}: {', '.join(missing)}")
            st.stop()

        df, G = compute_indicators(df_raw)

        if len(df) == 0:
            st.error("Nu au fost găsiți membri valizi în fișier." if lang=="Română" else "No valid team members found in the file.")
            st.stop()

        log_to_sheets(df, lang)

        # Warnings calitate date
        if (df['Ore_Saptamana'] > 80).any():
            st.warning("⚠ Ore > 80h/săpt detectate — verifică datele introduse." if lang=="Română" else "⚠ Hours > 80h/week detected — please check the data.")
        if (df['Zile_Concediu'] > 30).any():
            st.warning("⚠ Zile concediu > 30 detectate — posibil eroare de input." if lang=="Română" else "⚠ Vacation days > 30 detected — possible input error.")
        sfat_empty = df['Sfat_De_La'].astype(str).str.lower().isin(['nan', 'none', ''])
        if sfat_empty.sum() > len(df) * 0.5:
            st.warning("⚠ Peste 50% din membri nu au conexiuni ONA — rețeaua poate fi incompletă." if lang=="Română" else "⚠ Over 50% of members have no ONA connections — network may be incomplete.")

        # Banner financiar
        fi = compute_financial_impact(df, salary)
        render_financial_banner(fi, lang, salary)

        # Banner branding compact
        st.markdown(
            f"<div style='background:rgba(128,128,128,0.07);border-radius:8px;padding:10px 16px;margin:8px 0;font-size:13px;'>"
            f"🔬 TeamScientist | {'Diagnostic generat ✓' if lang=='Română' else 'Diagnostic generated ✓'} | "
            f"<a href='https://linkedin.com/in/razvanghebaur' target='_blank' style='color:#2471A3;'>LinkedIn — Răzvan Ghebaur</a>"
            f"</div>", unsafe_allow_html=True
        )

        # Auto-scroll la diagnostic după upload
        st.components.v1.html(
            "<script>window.parent.document.querySelector('section.main').scrollTo({top: 999999, behavior: 'smooth'});</script>",
            height=0
        )

        # Text ghid tab-uri
        tab_guide = (
            "👇 **Diagnosticul dvs. este gata.** Explorați rezultatele în cele 5 tab-uri de mai jos — dați click pe fiecare pentru detalii."
            if lang == "Română" else
            "👇 **Your diagnostic is ready.** Explore the results in the 5 tabs below — click each one for details."
        )
        st.info(tab_guide)

        # TABS
        tab_labels = (
            ["🧩 Insights", "🔥 Stres & Burnout", "🤐 Masca Politicoasă", "✈️ Risc Plecare", "🕸️ Rețeaua de Relații"]
            if lang == "Română" else
            ["🧩 Insights", "🔥 Stress & Burnout", "🤐 Polite Mask", "✈️ Leaving Risk", "🕸️ Relationship Network"]
        )
        tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_labels)

        # TAB 1: INSIGHTS
        with tab1:
            render_insights_tab(df, G, lang, salary, fi)

        # TAB 2: STRES & BURNOUT
        with tab2:
            st.markdown("**Scor 0–100. Peste 70 = Risc Ridicat | 50–70 = Atenție.**" if lang=="Română" else "**Score 0–100. Over 70 = Elevated Risk | 50–70 = Warning.**")
            st.markdown("**Roșu** = risc ridicat (>70) | **Galben** = atenție (50–70) | **Verde** = în parametri (<50)" if lang=="Română" else "**Red** = elevated risk (>70) | **Yellow** = warning (50–70) | **Green** = within range (<50)")

            b_desc = ("Angajații epuizați lucrează la 70–85% din capacitate. Restul se pierde în erori, lentoare și absenteism ascuns (sunt prezenți doar fizic)."
                      if lang=="Română" else
                      "Exhausted employees work at 70–85% capacity. The rest is lost in errors, slowdowns and hidden absenteeism (physically present only).")
            render_tab_cost(fi['burnout'], fi['burnout'],
                            "Pierderi estimate — Burnout" if lang=="Română" else "Estimated losses — Burnout",
                            b_desc, lang, salary)

            df_b = df.sort_values('B_Score', ascending=True)
            colors_b = ['#E74C3C' if s > 70 else '#F39C12' if s > 50 else '#27AE60' for s in df_b['B_Score']]
            ore_lbl  = "Ore/săpt" if lang=="Română" else "Hours/week"
            conc_lbl = "Zile concediu" if lang=="Română" else "Vacation days"
            en_lbl   = "Energie" if lang=="Română" else "Energy"

            fig_b = go.Figure(go.Bar(
                x=df_b['B_Score'], y=df_b['Nume'], orientation='h',
                marker_color=colors_b, text=df_b['B_Score'].round(1), textposition='outside',
                customdata=np.stack([df_b['Ore_Saptamana'], df_b['Zile_Concediu'], df_b['Scor_Energie']], axis=-1),
                hovertemplate=f"<b>%{{y}}</b><br>Burnout: %{{x:.1f}}/100<br>{ore_lbl}: %{{customdata[0]:.0f}}<br>{conc_lbl}: %{{customdata[1]:.0f}}<br>{en_lbl}: %{{customdata[2]:.0f}}/5<extra></extra>"
            ))
            fig_b.update_layout(xaxis=dict(range=[0,115], title="Burnout Score"), yaxis=dict(title=""),
                                height=max(420, len(df)*26), margin=dict(l=10,r=50,t=20,b=20),
                                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_b, use_container_width=True)

        # TAB 3: MASCA POLITICOASĂ
        with tab3:
            st.markdown(f"### {'Harta siguranței psihologice' if lang=='Română' else 'Psychological safety map'}")
            s_desc = (
                "**Siguranța psihologică** înseamnă că oamenii pot exprima ce gândesc fără teama de repercusiuni. Când aceasta lipsește, apare **masca politicoasă** — oamenii par ok, dar tac.\n\n"
                "**Axa X:** cât de des recunoaște greșeli în fața echipei (1 = deloc, 5 = deschis).\n\n"
                "**Axa Y:** cât de des propune idei și inițiative noi (1 = rar, 5 = frecvent).\n\n"
                "**Mărimea punctului:** proporțională cu riscul de mască.\n\n"
                "**Culoarea:** intensitatea riscului de nesiguranță psihologică (portocaliu închis = risc ridicat).\n\n"
                "**Cadrane:** Stânga-sus = Creativ/Defensiv | Dreapta-sus = Autentic & Sigur | Stânga-jos = Tăcere Critică | Dreapta-jos = Se simte sigur, e tăcut(ă)."
                if lang=="Română" else
                "**Psychological safety** means people can express what they think without fear of repercussions. When it is missing, the **polite mask** appears — people seem fine, but stay silent.\n\n"
                "**X axis:** how often they acknowledge mistakes in front of the team (1 = never, 5 = openly).\n\n"
                "**Y axis:** how often they propose new ideas (1 = rarely, 5 = frequently).\n\n"
                "**Dot size:** proportional to mask risk.\n\n"
                "**Color:** intensity of psychological safety risk (dark orange = high risk).\n\n"
                "**Quadrants:** Top-left = Creative/Defensive | Top-right = Authentic & Safe | Bottom-left = Critical Silence | Bottom-right = Safe but Silent."
            )
            st.markdown(s_desc)

            m_desc = ("Oamenii care tac nu propun, nu semnalează probleme la timp și nu contribuie la soluții. Inovația și calitatea deciziilor scad."
                      if lang=="Română" else
                      "People who stay silent don't propose, don't flag problems in time and don't contribute to solutions. Innovation and decision quality decline.")
            render_tab_cost(fi['mask'], fi['mask'],
                            "Pierderi estimate — Mască politicoasă" if lang=="Română" else "Estimated losses — Polite mask",
                            m_desc, lang, salary)

            st.markdown("---")
            fig_s = px.scatter(df, x="Erori_Asumate", y="Idei_Noi", size="S_Size", color="S_Score",
                color_continuous_scale='Oranges', hover_name="Nume",
                hover_data={"Erori_Asumate":":.1f","Idei_Noi":":.1f","S_Score":":.0f","S_Size":False},
                labels={"Erori_Asumate":"Asumare erori (1–5)" if lang=="Română" else "Error acknowledgment (1–5)",
                        "Idei_Noi":"Propunere idei (1–5)" if lang=="Română" else "Idea proposals (1–5)",
                        "S_Score":"Risc mască (%)" if lang=="Română" else "Mask risk (%)"})
            erori_lbl = "Asumare erori" if lang=="Română" else "Error acknowledgment"
            idei_lbl  = "Propunere idei" if lang=="Română" else "Idea proposals"
            risk_lbl  = "Risc nesiguranță" if lang=="Română" else "Safety risk"
            fig_s.update_traces(hovertemplate=f"<b>%{{hovertext}}</b><br>{erori_lbl}: %{{x:.1f}}/5<br>{idei_lbl}: %{{y:.1f}}/5<br>{risk_lbl}: %{{marker.color:.0f}}%<extra></extra>")
            fig_s.add_vline(x=3.0, line_dash="dot", line_color="rgba(150,150,150,0.6)")
            fig_s.add_hline(y=3.0, line_dash="dot", line_color="rgba(150,150,150,0.6)")
            q_labels = (["Creativ / Defensiv","Autentic & Sigur","Tăcere Critică","Se simte sigur, e tăcut(ă)"]
                        if lang=="Română" else ["Creative / Defensive","Authentic & Safe","Critical Silence","Safe but Silent"])
            q_colors = ["rgba(150,150,150,0.9)","rgba(100,180,100,0.9)","rgba(200,80,80,0.9)","rgba(200,150,50,0.9)"]
            q_pos = [(1.5,4.5),(4.2,4.5),(1.5,1.2),(4.2,1.2)]
            for (x,y), txt, col in zip(q_pos, q_labels, q_colors):
                fig_s.add_annotation(x=x, y=y, text=txt, showarrow=False, font=dict(size=13, color=col))
            fig_s.update_layout(height=500, margin=dict(l=10,r=10,t=20,b=20),
                                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_s, use_container_width=True)

        # TAB 4: RISC PLECARE
        with tab4:
            st.markdown("**Scor 0–100. Peste 65 = Risc Ridicat | 40–65 = Monitorizare.**" if lang=="Română" else "**Score 0–100. Over 65 = Elevated Risk | 40–65 = Monitor.**")
            st.info("Înlocuirea unui angajat costă 6–9 luni de salariu — recrutare, onboarding și timp până la productivitate deplină." if lang=="Română" else "Replacing an employee costs 6–9 months salary — recruitment, onboarding and ramp-up time.")

            l_desc = ("Înlocuirea unui angajat costă 6–9 luni de salariu — recrutare, onboarding și timp până la productivitate deplină."
                      if lang=="Română" else
                      "Replacing an employee costs 6–9 months salary — recruitment, onboarding and ramp-up time.")
            render_tab_cost(fi['leaving_min'], fi['leaving_max'],
                            "Pierderi estimate — Risc plecare" if lang=="Română" else "Estimated losses — Leaving risk",
                            l_desc, lang, salary)

            df_f = df.sort_values('F_Score', ascending=True).copy()
            if salary > 0:
                df_f['Cost_Est'] = df_f['F_Score'].apply(lambda s: f"€{salary*6:,.0f}–€{salary*9:,.0f}" if s > 65 else "")
            colors_f = ['#E74C3C' if s > 65 else '#F39C12' if s > 40 else '#27AE60' for s in df_f['F_Score']]
            marire_lbl = "Ultima mărire" if lang=="Română" else "Last raise"
            en_lbl2    = "Energie" if lang=="Română" else "Energy"
            cons_lbl   = "Consultat de" if lang=="Română" else "Consulted by"

            fig_f = go.Figure(go.Bar(
                x=df_f['F_Score'], y=df_f['Nume'], orientation='h',
                marker_color=colors_f, text=df_f['F_Score'].round(1), textposition='outside',
                customdata=np.stack([df_f['Ultima_Marire'], df_f['Scor_Energie'], df_f['ONA_InDegree']], axis=-1),
                hovertemplate=(
                    f"<b>%{{y}}</b><br>"
                    f"{'Risc plecare' if lang=='Română' else 'Leaving risk'}: %{{x:.1f}}/100<br>"
                    f"{marire_lbl}: %{{customdata[0]:.0f}} {'luni' if lang=='Română' else 'months'}<br>"
                    f"{en_lbl2}: %{{customdata[1]:.0f}}/5<br>"
                    f"{cons_lbl}: %{{customdata[2]:.0f}} {'colegi' if lang=='Română' else 'colleagues'}"
                    "<extra></extra>"
                )
            ))
            fig_f.update_layout(xaxis=dict(range=[0,115], title="Leaving Risk Score"), yaxis=dict(title=""),
                                height=max(420, len(df)*26), margin=dict(l=10,r=50,t=20,b=20),
                                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_f, use_container_width=True)

            if salary > 0:
                high_risk = df_f[df_f['F_Score'] > 65][['Nume','F_Score','Cost_Est']].sort_values('F_Score', ascending=False)
                if not high_risk.empty:
                    st.markdown(f"**{'Cost estimat înlocuire — membri cu risc ridicat' if lang=='Română' else 'Estimated replacement cost — high-risk members'}**")
                    high_risk.columns = ['Cod' if lang=='Română' else 'Code', 'Scor risc' if lang=='Română' else 'Risk score', 'Cost estimat' if lang=='Română' else 'Estimated cost']
                    st.dataframe(high_risk, hide_index=True, use_container_width=True)

        # TAB 5: REȚEAUA DE RELAȚII
        with tab5:
            st.markdown("**Dimensiunea nodului** = câți colegi consultă / solicită acel membru al echipei | **Culoarea** = risc burnout" if lang=="Română" else "**Node size** = how many colleagues consult / reach out to that team member | **Color** = burnout risk")
            st.markdown("**Săgeata** indică direcția consultării: de la cel care întreabă spre cel consultat." if lang=="Română" else "**Arrow** direction: from the person asking toward the person being consulted.")

            pos = nx.spring_layout(G, k=1.2, seed=42)
            fig_ona = go.Figure()
            for e in G.edges():
                x0,y0 = pos[e[0]]; x1,y1 = pos[e[1]]
                fig_ona.add_trace(go.Scatter(
                    x=[x0,(x0+x1)/2,x1], y=[y0,(y0+y1)/2,y1],
                    mode='lines+markers',
                    marker=dict(symbol="arrow",size=8,angleref="previous",color="rgba(150,150,150,0.5)"),
                    line=dict(width=1,color='rgba(150,150,150,0.35)'),
                    hoverinfo='none', showlegend=False
                ))
            nx_nodes = list(G.nodes())
            b_vals   = [G.nodes[n].get('B',0) for n in nx_nodes]
            sizes    = [(G.in_degree(n)*12)+14 for n in nx_nodes]
            in_deg   = [G.in_degree(n) for n in nx_nodes]
            cons_lbl2 = "consultat de" if lang=="Română" else "consulted by"
            col_lbl2  = "colegi" if lang=="Română" else "colleagues"

            fig_ona.add_trace(go.Scatter(
                x=[pos[n][0] for n in nx_nodes], y=[pos[n][1] for n in nx_nodes],
                mode='markers+text', text=nx_nodes, textposition="bottom center",
                customdata=list(zip(in_deg, b_vals)),
                marker=dict(size=sizes, color=b_vals, colorscale='RdYlGn_r', showscale=True,
                            colorbar=dict(title="Burnout",tickvals=[0,50,100],ticktext=["0","50","100"]),
                            line=dict(width=1,color='rgba(255,255,255,0.3)')),
                hovertemplate=f"<b>%{{text}}</b><br>{cons_lbl2} %{{customdata[0]}} {col_lbl2}<br>Burnout: %{{customdata[1]:.0f}}/100<extra></extra>",
                showlegend=False
            ))
            fig_ona.update_layout(showlegend=False, height=600,
                xaxis=dict(showgrid=False,zeroline=False,showticklabels=False),
                yaxis=dict(showgrid=False,zeroline=False,showticklabels=False),
                margin=dict(l=20,r=20,t=20,b=20),
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_ona, use_container_width=True)

        # ── SURVEY BANNER ─────────────────────────────────────
        st.markdown("---")
        survey_text = (
            "💬 V-a fost util diagnosticul? Ajutați-ne să îmbunătățim instrumentul — 2 minute, anonim."
            if lang=="Română" else
            "💬 Was the diagnostic useful? Help us improve the instrument — 2 minutes, anonymous."
        )
        survey_btn = "Completează formularul →" if lang=="Română" else "Fill in the form →"
        st.markdown(
            f"<div style='background:#EBF5FB;border-radius:10px;padding:14px 20px;margin:8px 0;"
            f"display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;'>"
            f"<span style='font-size:14px;color:#1A5276;'>{survey_text}</span>"
            f"<a href='{SURVEY_LINK}' target='_blank' "
            f"style='background:#2471A3;color:#fff;padding:8px 18px;border-radius:6px;"
            f"font-size:13px;font-weight:600;text-decoration:none;white-space:nowrap;'>{survey_btn}</a>"
            f"</div>", unsafe_allow_html=True
        )

    except Exception as e:
        st.error(f"{'Eroare la procesarea fișierului' if lang=='Română' else 'Error processing file'}: {e}")
        st.exception(e)
