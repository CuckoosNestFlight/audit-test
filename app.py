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
        f"<div style='font-size:15px;color:rgba(255,255,255,0.6);margin-bottom:6px;'>"
        f"{total_txt}</div>"
        f"<div style='font-size:32px;font-weight:700;color:#FF6B6B;line-height:1;'>"
        f"{fmt_eur(fi['total_min'])} – {fmt_eur(fi['total_max'])}"
        f"<span style='font-size:16px;font-weight:400;color:rgba(255,255,255,0.6);'>{per_year}</span></div>"
        f"<div style='margin-top:14px;display:flex;gap:16px;flex-wrap:wrap;'>"
        f"<div style='background:rgba(255,255,255,0.07);border-radius:8px;padding:10px 14px;flex:1;min-width:160px;'>"
        f"<div style='font-size:13px;color:rgba(255,255,255,0.6);margin-bottom:3px;'>🔥 Burnout</div>"
        f"<div style='font-size:18px;font-weight:600;color:#FFA07A;'>{fmt_eur(fi['burnout'])}<span style='font-size:11px;color:rgba(255,255,255,0.4);'>{per_year}</span></div>"
        f"<div style='font-size:13px;color:rgba(255,255,255,0.55);margin-top:3px;'>{'Angajații epuizați lucrează la 70–85% din capacitate. Restul se pierde în erori, lentoare și absenteism ascuns (sunt prezenți doar fizic).' if lang=='Română' else 'Exhausted employees work at 70–85% capacity. The rest is lost in errors, slowdowns and hidden absenteeism (physically present only).'}</div>"
        f"</div>"
        f"<div style='background:rgba(255,255,255,0.07);border-radius:8px;padding:10px 14px;flex:1;min-width:160px;'>"
        f"<div style='font-size:13px;color:rgba(255,255,255,0.6);margin-bottom:3px;'>✈️ {'Risc plecare' if lang=='Română' else 'Leaving risk'}</div>"
        f"<div style='font-size:18px;font-weight:600;color:#FFA07A;'>{fmt_eur(fi['leaving_min'])}–{fmt_eur(fi['leaving_max'])}</div>"
        f"<div style='font-size:13px;color:rgba(255,255,255,0.55);margin-top:3px;'>{'Înlocuirea unui angajat costă 6–9 luni de salariu — recrutare, onboarding și timp până la productivitate deplină.' if lang=='Română' else 'Replacing an employee costs 6–9 months salary — recruitment, onboarding and ramp-up time.'}</div>"
        f"</div>"
        f"<div style='background:rgba(255,255,255,0.07);border-radius:8px;padding:10px 14px;flex:1;min-width:160px;'>"
        f"<div style='font-size:13px;color:rgba(255,255,255,0.6);margin-bottom:3px;'>🤐 {'Mască politicoasă' if lang=='Română' else 'Polite mask'}</div>"
        f"<div style='font-size:18px;font-weight:600;color:#FFA07A;'>{fmt_eur(fi['mask'])}<span style='font-size:11px;color:rgba(255,255,255,0.4);'>{per_year}</span></div>"
        f"<div style='font-size:13px;color:rgba(255,255,255,0.55);margin-top:3px;'>{'Oamenii care tac nu propun, nu semnalează probleme la timp și nu contribuie la soluții. Inovația și calitatea deciziilor scad.' if lang=='Română' else 'People who stay silent dont propose, dont flag problems in time and dont contribute to solutions. Innovation and decision quality decline.'}</div>"
        f"</div>"
        f"</div>"
        f"<div style='margin-top:10px;font-size:13px;color:rgba(255,255,255,0.45);'>{note}</div>"
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

    # ── METODOLOGIE ───────────────────────────────────────────
    st.markdown("<div style='margin-top:2rem'></div>", unsafe_allow_html=True)
    if lang == "Română":
        st.markdown(
            "<div style='border-left:3px solid rgba(128,128,128,0.25);padding:0.75rem 1.1rem;"
            "background:rgba(128,128,128,0.04);border-radius:0 8px 8px 0;'>"
            "<p style='font-size:13px;font-weight:600;color:#555;margin:0 0 4px;'>Despre metodologie</p>"
            "<p style='font-size:12px;line-height:1.7;color:#666;margin:0;'>"
            "Indicatorii din această diagnoză sunt construiți pe baza unor modele validate în cercetarea organizațională: "
            "Maslach &amp; Leiter (burnout cronic), Karasek (stres ocupațional), Edmondson (siguranță psihologică), "
            "Gallup &amp; Google Project Aristotle (engagement și dinamică de echipă), Cross et al. (rețele organizaționale informale).<br><br>"
            "Datele sunt introduse de manager și reflectă observații directe — nu autopercepție subiectivă a angajaților. "
            "Scorurile sunt indicatori de direcție, nu măsurători clinice."
            "</p></div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div style='border-left:3px solid rgba(128,128,128,0.25);padding:0.75rem 1.1rem;"
            "background:rgba(128,128,128,0.04);border-radius:0 8px 8px 0;'>"
            "<p style='font-size:13px;font-weight:600;color:#555;margin:0 0 4px;'>About the methodology</p>"
            "<p style='font-size:12px;line-height:1.7;color:#666;margin:0;'>"
            "The indicators in this diagnosis are built on models validated in organisational research: "
            "Maslach &amp; Leiter (chronic burnout), Karasek (occupational stress), Edmondson (psychological safety), "
            "Gallup &amp; Google Project Aristotle (engagement and team dynamics), Cross et al. (informal organisational networks).<br><br>"
            "Data is entered by the manager and reflects direct observations — not subjective self-perception of employees. "
            "Scores are directional indicators, not clinical measurements."
            "</p></div>",
            unsafe_allow_html=True
        )


# ════════════════════════════════════════════════════════════
# LANDING PAGE
# ════════════════════════════════════════════════════════════


# ════════════════════════════════════════════════════════════
# PDF GENERATION
# ════════════════════════════════════════════════════════════

def generate_pdf_report(df, G, fi, lang, salary, team_name=""):
    import io
    import os
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import networkx as nx
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     PageBreak, Table, TableStyle, Image, HRFlowable)
    from reportlab.platypus import KeepTogether
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import numpy as np

    # ── FONTURI UNICODE (suport diacritice) ──────────────────
    # Caută DejaVuSans în locațiile standard Linux / Streamlit Cloud
    _font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/local/lib/python3.12/dist-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSans.ttf",
        "/usr/local/lib/python3.12/dist-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSans-Bold.ttf",
    ]
    _reg_normal = next((p for p in _font_paths if "Bold" not in p and os.path.exists(p)), None)
    _reg_bold   = next((p for p in _font_paths if "Bold" in p and os.path.exists(p)), None)

    if _reg_normal and _reg_bold:
        try:
            pdfmetrics.registerFont(TTFont('DVSans',     _reg_normal))
            pdfmetrics.registerFont(TTFont('DVSans-Bold', _reg_bold))
            F_NORMAL = 'DVSans'
            F_BOLD   = 'DVSans-Bold'
        except Exception:
            F_NORMAL = 'Helvetica'
            F_BOLD   = 'Helvetica-Bold'
    else:
        F_NORMAL = 'Helvetica'
        F_BOLD   = 'Helvetica-Bold'

    # ── CULORI ───────────────────────────────────────────────
    C_DARK   = colors.HexColor('#1F3864')
    C_RED    = colors.HexColor('#E74C3C')
    C_ORANGE = colors.HexColor('#E67E22')
    C_GREEN  = colors.HexColor('#27AE60')
    C_PURPLE = colors.HexColor('#6C3483')
    C_GRAY   = colors.HexColor('#7F8C8D')
    C_LIGHT  = colors.HexColor('#F4F6F7')
    C_BG_RED = colors.HexColor('#FDEDEC')
    C_BG_YEL = colors.HexColor('#FEF9E7')
    C_BG_GRN = colors.HexColor('#EAFAF1')

    buf = io.BytesIO()
    date_str = datetime.now().strftime("%d.%m.%Y")

    # ── HEADER / FOOTER ──────────────────────────────────────
    def header_footer(canvas, doc):
        canvas.saveState()
        w, h = A4
        canvas.setStrokeColor(C_DARK)
        canvas.setLineWidth(0.5)
        canvas.line(1.5*cm, h - 1.2*cm, w - 1.5*cm, h - 1.2*cm)
        canvas.setFont(F_BOLD, 8)
        canvas.setFillColor(C_DARK)
        canvas.drawString(1.5*cm, h - 1.05*cm, "Team Scientist | Răzvan Ghebaur")
        canvas.setFont(F_NORMAL, 8)
        canvas.setFillColor(C_GRAY)
        canvas.drawRightString(w - 1.5*cm, h - 1.05*cm, "linkedin.com/in/razvanghebaur")
        canvas.line(1.5*cm, 1.3*cm, w - 1.5*cm, 1.3*cm)
        canvas.setFont(F_NORMAL, 7)
        canvas.setFillColor(C_GRAY)
        footer_left = (
            "Generat de Team Scientist — indicatori de direcție, nu verdicte."
            if lang == "Română" else
            "Generated by Team Scientist — directional indicators, not verdicts."
        )
        canvas.drawString(1.5*cm, 0.8*cm, footer_left)
        canvas.drawRightString(w - 1.5*cm, 0.8*cm, f"{doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.8*cm, bottomMargin=1.8*cm
    )

    # ── STILURI ──────────────────────────────────────────────
    styles = getSampleStyleSheet()
    s_title   = ParagraphStyle('ts_title',   fontSize=22, fontName=F_BOLD,
                                textColor=C_DARK, spaceAfter=6, leading=26)
    s_subtitle= ParagraphStyle('ts_sub',     fontSize=12, fontName=F_NORMAL,
                                textColor=C_GRAY, spaceAfter=4, leading=16)
    s_h1      = ParagraphStyle('ts_h1',      fontSize=14, fontName=F_BOLD,
                                textColor=C_DARK, spaceBefore=14, spaceAfter=6, leading=18)
    s_h2      = ParagraphStyle('ts_h2',      fontSize=11, fontName=F_BOLD,
                                textColor=C_DARK, spaceBefore=8, spaceAfter=4, leading=14)
    s_body    = ParagraphStyle('ts_body',    fontSize=9,  fontName=F_NORMAL,
                                textColor=colors.HexColor('#2C3E50'), leading=14, spaceAfter=4)
    s_small   = ParagraphStyle('ts_small',   fontSize=8,  fontName=F_NORMAL,
                                textColor=C_GRAY, leading=12, spaceAfter=3)
    s_disclaimer = ParagraphStyle('ts_disc', fontSize=8.5, fontName=F_NORMAL,
                                   textColor=colors.HexColor('#784212'), leading=13,
                                   backColor=colors.HexColor('#FFF8F0'),
                                   borderColor=colors.HexColor('#E67E22'),
                                   borderWidth=0, leftIndent=8, rightIndent=8,
                                   spaceBefore=6, spaceAfter=6)
    s_method  = ParagraphStyle('ts_method',  fontSize=8,  fontName=F_NORMAL,
                                textColor=colors.HexColor('#555555'), leading=13,
                                leftIndent=6, rightIndent=6, spaceAfter=4)

    story = []

    # ════════════════════════════════════════════════════════
    # PAG 1 — COPERTĂ
    # ════════════════════════════════════════════════════════
    story.append(Spacer(1, 2*cm))
    cover_title = "Diagnoza de Echipa" if lang == "Română" else "Team Diagnostic"
    story.append(Paragraph(cover_title, s_title))
    story.append(Paragraph("Team Scientist", s_subtitle))
    story.append(Spacer(1, 0.3*cm))

    # Info rând
    n_members = len(df)
    cover_info = f"{'Data' if lang=='Română' else 'Date'}: {date_str}  |  {'Membri analizati' if lang=='Română' else 'Members analysed'}: {n_members}"
    if team_name:
        cover_info = f"{'Echipa' if lang=='Română' else 'Team'}: {team_name}  |  " + cover_info
    story.append(Paragraph(cover_info, s_subtitle))
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=C_DARK))
    story.append(Spacer(1, 0.5*cm))

    # Disclaimer proeminent
    disc_text = (
        "⚠  Concluziile din acest raport sunt extrase din date si reprezinta indicatori de analiza, "
        "nu verdicte. Se recomanda discutii directe cu oamenii si eventual analize suplimentare inainte de orice decizie."
        if lang == "Română" else
        "⚠  The conclusions in this report are data-driven indicators, not verdicts. "
        "Direct conversations with team members and further analysis are recommended before any decision."
    )
    disc_table = Table([[Paragraph(disc_text, s_disclaimer)]], colWidths=['100%'])
    disc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFF8F0')),
        ('LEFTPADDING',  (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING',   (0,0), (-1,-1), 8),
        ('BOTTOMPADDING',(0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#E67E22')),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.HexColor('#FFF8F0')]),
    ]))
    story.append(disc_table)
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # PAG 2 — IMPACT FINANCIAR
    # ════════════════════════════════════════════════════════
    fin_title = "Impact Financiar Estimat" if lang == "Română" else "Estimated Financial Impact"
    story.append(Paragraph(fin_title, s_h1))

    sal_note = (f"Calculat la salariu mediu estimat de EUR {fi['salary_used']:,.0f}/luna."
                if lang == "Română" else
                f"Calculated at estimated average salary of EUR {fi['salary_used']:,.0f}/month.")
    story.append(Paragraph(sal_note, s_small))
    story.append(Spacer(1, 0.3*cm))

    total_txt = "Total pierderi estimate / an" if lang == "Română" else "Total estimated losses / year"
    total_val = f"EUR {fi['total_min']:,.0f} - EUR {fi['total_max']:,.0f}"
    fin_header = [[Paragraph(total_txt, s_small),
                   Paragraph(f"<b>{total_val}</b>", ParagraphStyle('fh', fontSize=14,
                   fontName=F_BOLD, textColor=C_RED, leading=18))]]
    fin_header_tbl = Table(fin_header, colWidths=[9*cm, 9*cm])
    fin_header_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR',  (0,0), (-1,-1), colors.white),
        ('LEFTPADDING',  (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING',   (0,0), (-1,-1), 10),
        ('BOTTOMPADDING',(0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(fin_header_tbl)
    story.append(Spacer(1, 0.3*cm))

    # 3 carduri financiare
    per_yr = "/an" if lang == "Română" else "/year"
    fin_rows = [
        ["🔥 Burnout", f"EUR {fi['burnout']:,.0f}{per_yr}",
         ("Angajatii epuizati lucreaza la 70-85% din capacitate. Restul se pierde in erori, lentoare si absenteism ascuns."
          if lang=="Română" else
          "Exhausted employees work at 70-85% capacity. The rest is lost in errors, slowdowns and hidden absenteeism.")],
        [f"✈️ {'Risc plecare' if lang=='Română' else 'Leaving risk'}",
         f"EUR {fi['leaving_min']:,.0f} - EUR {fi['leaving_max']:,.0f}",
         ("Inlocuirea unui angajat costa 6-9 luni de salariu — recrutare, onboarding si timp pana la productivitate deplina."
          if lang=="Română" else
          "Replacing an employee costs 6-9 months salary — recruitment, onboarding and ramp-up time.")],
        [f"🤐 {'Masca politicoasa' if lang=='Română' else 'Polite mask'}",
         f"EUR {fi['mask']:,.0f}{per_yr}",
         ("Oamenii care tac nu propun, nu semnaleaza probleme la timp si nu contribuie la solutii."
          if lang=="Română" else
          "People who stay silent don't propose, don't flag problems in time and don't contribute to solutions.")],
    ]
    for lbl, val, desc in fin_rows:
        row_data = [[Paragraph(f"<b>{lbl}</b>", s_body),
                     Paragraph(f"<b>{val}</b>", ParagraphStyle('fv', fontSize=11,
                     fontName=F_BOLD, textColor=C_ORANGE, leading=14)),
                     Paragraph(desc, s_small)]]
        t_fin = Table(row_data, colWidths=[4*cm, 4.5*cm, 9.5*cm])
        t_fin.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8F9FA')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#DEE2E6')),
            ('LEFTPADDING',  (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING',   (0,0), (-1,-1), 7),
            ('BOTTOMPADDING',(0,0), (-1,-1), 7),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t_fin)
        story.append(Spacer(1, 0.15*cm))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # PAG 3 — REZUMAT EXECUTIV & ACȚIUNI
    # ════════════════════════════════════════════════════════
    t_txt = TEXTS[lang]
    sum_title = "Rezumat Executiv si Actiuni Recomandate" if lang == "Română" else "Executive Summary & Recommended Actions"
    story.append(Paragraph(sum_title, s_h1))

    n_critical = int(((df['B_Score'] > 70) | (df['F_Score'] > 65)).sum())
    n_warning  = int(((df['B_Score'].between(50,70)) | (df['F_Score'].between(40,65))).sum())
    n_ok       = len(df) - n_critical - n_warning

    # Scoreboard 3 coloane
    sb_data = [[
        Paragraph(f"<b>{n_critical}</b>", ParagraphStyle('sc', fontSize=28, fontName=F_BOLD,
                   textColor=C_RED, alignment=TA_CENTER)),
        Paragraph(f"<b>{n_warning}</b>",  ParagraphStyle('sw', fontSize=28, fontName=F_BOLD,
                   textColor=C_ORANGE, alignment=TA_CENTER)),
        Paragraph(f"<b>{n_ok}</b>",       ParagraphStyle('sok', fontSize=28, fontName=F_BOLD,
                   textColor=C_GREEN, alignment=TA_CENTER)),
    ],[
        Paragraph("🔴 Interventie imediata" if lang=="Română" else "🔴 Immediate attention",
                  ParagraphStyle('sl', fontSize=8, fontName=F_NORMAL, textColor=C_RED, alignment=TA_CENTER)),
        Paragraph("🟡 De urmarit" if lang=="Română" else "🟡 To monitor",
                  ParagraphStyle('sl2', fontSize=8, fontName=F_NORMAL, textColor=C_ORANGE, alignment=TA_CENTER)),
        Paragraph("🟢 In parametri" if lang=="Română" else "🟢 Within range",
                  ParagraphStyle('sl3', fontSize=8, fontName=F_NORMAL, textColor=C_GREEN, alignment=TA_CENTER)),
    ]]
    sb_tbl = Table(sb_data, colWidths=[6*cm, 6*cm, 6*cm])
    sb_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#FDEDEC')),
        ('BACKGROUND', (1,0), (1,-1), colors.HexColor('#FEF9E7')),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#EAFAF1')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',   (0,0), (-1,-1), 10),
        ('BOTTOMPADDING',(0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#DEE2E6')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DEE2E6')),
    ]))
    story.append(sb_tbl)
    story.append(Spacer(1, 0.4*cm))

    # Insights individuale
    def pdf_level_color(level):
        return {
            "critical": colors.HexColor('#FDEDEC'),
            "warning":  colors.HexColor('#FEF9E7'),
            "ok":       colors.HexColor('#EAFAF1'),
            "info":     colors.HexColor('#EBF5FB'),
        }.get(level, colors.HexColor('#F4F6F7'))

    def pdf_level_border(level):
        return {
            "critical": C_RED,
            "warning":  C_ORANGE,
            "ok":       C_GREEN,
            "info":     colors.HexColor('#2471A3'),
        }.get(level, C_GRAY)

    def pdf_insight_block(text, level):
        bg  = pdf_level_color(level)
        brd = pdf_level_border(level)
        tbl = Table([[Paragraph(text, ParagraphStyle('pi', fontSize=8.5, fontName=F_NORMAL,
                     textColor=colors.HexColor('#2C3E50'), leading=13))]], colWidths=['100%'])
        tbl.setStyle(TableStyle([
            ('BACKGROUND',   (0,0), (-1,-1), bg),
            ('LEFTPADDING',  (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING',   (0,0), (-1,-1), 6),
            ('BOTTOMPADDING',(0,0), (-1,-1), 6),
            ('LINEBEFORE',   (0,0), (0,-1), 3, brd),
        ]))
        return tbl

    # Situații urgente
    urgent = df[(df['B_Score'] > 70) | (df['F_Score'] > 65)].copy()
    urgent['_max'] = urgent[['B_Score','F_Score']].max(axis=1)
    urgent = urgent.sort_values('_max', ascending=False)
    if not urgent.empty:
        story.append(Paragraph(f"⚠️ {t_txt['sec_urgent']}", s_h2))
        for _, row in urgent.iterrows():
            ins = generate_individual_insights(row, t_txt, salary)
            story.append(Paragraph(f"<b>{row['Nume']}</b> — Burnout: {row['B_Score']:.0f} | "
                         f"{'Risc Plecare' if lang=='Română' else 'Leaving Risk'}: {row['F_Score']:.0f} | "
                         f"Mask: {row['S_Raw']:.1f}", s_body))
            story.append(pdf_insight_block(f"🔥 {ins['burnout'][0]}", ins['burnout'][1]))
            story.append(pdf_insight_block(f"✈️ {ins['leaving'][0]}", ins['leaving'][1]))
            story.append(pdf_insight_block(f"🤐 {ins['mask'][0]}", ins['mask'][1]))
            story.append(Spacer(1, 0.2*cm))

    # De urmărit
    monitor = df[~((df['B_Score'] > 70) | (df['F_Score'] > 65)) &
                  ((df['B_Score'] > 50) | (df['F_Score'] > 40))].copy()
    if not monitor.empty:
        story.append(Paragraph(f"👁️ {t_txt['sec_monitor']}", s_h2))
        monitor['_max'] = monitor[['B_Score','F_Score']].max(axis=1)
        monitor = monitor.sort_values('_max', ascending=False)
        for _, row in monitor.iterrows():
            ins = generate_individual_insights(row, t_txt, salary)
            story.append(Paragraph(f"<b>{row['Nume']}</b> — Burnout: {row['B_Score']:.0f} | "
                         f"{'Risc Plecare' if lang=='Română' else 'Leaving Risk'}: {row['F_Score']:.0f}", s_body))
            story.append(pdf_insight_block(f"🔥 {ins['burnout'][0]}", ins['burnout'][1]))
            story.append(pdf_insight_block(f"✈️ {ins['leaving'][0]}", ins['leaving'][1]))
            story.append(Spacer(1, 0.15*cm))

    # Tipare
    patterns = detect_team_patterns(df, G, t_txt)
    if patterns:
        story.append(Paragraph(f"🕸️ {t_txt['sec_patterns']}", s_h2))
        for p in patterns:
            story.append(pdf_insight_block(f"<b>{p['title']}</b> — {p['text']}", p['level']))
            story.append(Spacer(1, 0.1*cm))

    # Acțiuni
    all_w1, all_w2, all_w3 = [], [], []
    for _, row in df.iterrows():
        ins = generate_individual_insights(row, t_txt, salary)
        all_w1.extend(ins["actions_w1"])
        all_w2.extend(ins["actions_w2"])
        all_w3.extend(ins["actions_w3"])
    hubs_df = df[df['ONA_InDegree'] >= 3].sort_values('ONA_InDegree', ascending=False)
    if not hubs_df.empty:
        all_w1.append(t_txt["action_hub"].format(name=hubs_df.iloc[0]['Nume']))
    for _, row in df[(df['ONA_Conn'] <= 1) & (df['S_Raw'] < 3)].iterrows():
        all_w3.append(t_txt["action_isolated"].format(name=row['Nume']))

    if any([all_w1, all_w2, all_w3]):
        story.append(Paragraph(f"✅ {t_txt['action_title']}", s_h2))
        if all_w1:
            story.append(Paragraph(f"<b>{t_txt['action_w1']}</b>", s_body))
            for a in all_w1[:3]:
                story.append(pdf_insight_block(a, "critical"))
        if all_w2:
            story.append(Paragraph(f"<b>{t_txt['action_w2']}</b>", s_body))
            for a in all_w2[:3]:
                story.append(pdf_insight_block(a, "warning"))
        if all_w3:
            story.append(Paragraph(f"<b>{t_txt['action_w3']}</b>", s_body))
            for a in all_w3[:3]:
                story.append(pdf_insight_block(a, "ok"))

    # Metodologie
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_GRAY))
    story.append(Spacer(1, 0.2*cm))
    method_title = "Despre metodologie" if lang == "Română" else "About the methodology"
    story.append(Paragraph(method_title, ParagraphStyle('mt', fontSize=9, fontName=F_BOLD,
                 textColor=C_GRAY, spaceAfter=3)))
    method_text = (
        "Indicatorii din aceasta diagnoza sunt construiti pe baza unor modele validate in cercetarea organizationala: "
        "Maslach & Leiter (burnout cronic), Karasek (stres ocupational), Edmondson (siguranta psihologica), "
        "Gallup & Google Project Aristotle (engagement si dinamica de echipa), Cross et al. (retele organizationale informale). "
        "Datele sunt introduse de manager si reflecta observatii directe — nu autopercepție subiectiva a angajatilor. "
        "Scorurile sunt indicatori de directie, nu masuratori clinice."
        if lang == "Română" else
        "The indicators in this diagnosis are built on models validated in organisational research: "
        "Maslach & Leiter (chronic burnout), Karasek (occupational stress), Edmondson (psychological safety), "
        "Gallup & Google Project Aristotle (engagement and team dynamics), Cross et al. (informal organisational networks). "
        "Data is entered by the manager and reflects direct observations — not subjective self-perception of employees. "
        "Scores are directional indicators, not clinical measurements."
    )
    story.append(Paragraph(method_text, s_method))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # HELPER: matplotlib bar chart → image bytes
    # ════════════════════════════════════════════════════════
    def make_bar_chart(names, scores, colors_list, xlabel, threshold_high, threshold_med,
                       color_high, color_med, color_ok, legend_high, legend_med, legend_ok):
        fig, ax = plt.subplots(figsize=(10, max(4, len(names)*0.45)))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        bars = ax.barh(names, scores, color=colors_list, edgecolor='white', height=0.6)
        ax.set_xlim(0, 115)
        ax.set_xlabel(xlabel, fontsize=9)
        ax.axvline(x=threshold_high, color=color_high, linestyle='--', linewidth=0.8, alpha=0.6)
        ax.axvline(x=threshold_med,  color=color_med,  linestyle='--', linewidth=0.8, alpha=0.5)
        for bar, score in zip(bars, scores):
            ax.text(score + 1.5, bar.get_y() + bar.get_height()/2,
                    f'{score:.1f}', va='center', fontsize=8)
        legend_patches = [
            mpatches.Patch(color=color_high, label=legend_high),
            mpatches.Patch(color=color_med,  label=legend_med),
            mpatches.Patch(color=color_ok,   label=legend_ok),
        ]
        ax.legend(handles=legend_patches, loc='lower right', fontsize=8, framealpha=0.8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(axis='y', labelsize=8)
        ax.tick_params(axis='x', labelsize=8)
        plt.tight_layout()
        img_buf = io.BytesIO()
        fig.savefig(img_buf, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        img_buf.seek(0)
        return img_buf

    # ════════════════════════════════════════════════════════
    # PAG 4 — STRES & BURNOUT
    # ════════════════════════════════════════════════════════
    burnout_title = "Stres si Burnout" if lang == "Română" else "Stress & Burnout"
    story.append(Paragraph(burnout_title, s_h1))

    legend_desc_b = (
        "Scor 0-100. Rosu (>70) = risc ridicat | Galben (50-70) = atentie | Verde (<50) = in parametri\n"
        "Angajatii epuizati lucreaza la 70-85% din capacitate. Restul se pierde in erori, lentoare si absenteism ascuns."
        if lang == "Română" else
        "Score 0-100. Red (>70) = elevated risk | Yellow (50-70) = warning | Green (<50) = within range\n"
        "Exhausted employees work at 70-85% capacity. The rest is lost in errors, slowdowns and hidden absenteeism."
    )
    story.append(Paragraph(legend_desc_b, s_small))
    story.append(Spacer(1, 0.2*cm))

    df_b = df.sort_values('B_Score', ascending=True)
    colors_b = ['#E74C3C' if s > 70 else '#F39C12' if s > 50 else '#27AE60' for s in df_b['B_Score']]
    b_img = make_bar_chart(
        df_b['Nume'].tolist(), df_b['B_Score'].tolist(), colors_b,
        "Burnout Score (0-100)", 70, 50,
        '#E74C3C', '#F39C12', '#27AE60',
        ">70 Risc ridicat" if lang=="Română" else ">70 Elevated risk",
        "50-70 Atentie" if lang=="Română" else "50-70 Warning",
        "<50 In parametri" if lang=="Română" else "<50 Within range"
    )
    chart_h = max(5*cm, len(df)*1.1*cm)
    story.append(Image(b_img, width=17*cm, height=min(chart_h, 16*cm)))
    story.append(Spacer(1, 0.2*cm))

    cost_b_txt = (f"Pierderi estimate burnout: EUR {fi['burnout']:,.0f}/an "
                  f"({fi['n_burnout_high']} angajat(i) risc ridicat, {fi['n_burnout_med']} atentie)"
                  if lang == "Română" else
                  f"Estimated burnout losses: EUR {fi['burnout']:,.0f}/year "
                  f"({fi['n_burnout_high']} employee(s) high risk, {fi['n_burnout_med']} warning)")
    story.append(Paragraph(cost_b_txt, s_small))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # PAG 5 — MASCA POLITICOASĂ
    # ════════════════════════════════════════════════════════
    mask_title = "Masca Politicoasa — Siguranta Psihologica" if lang == "Română" else "Polite Mask — Psychological Safety"
    story.append(Paragraph(mask_title, s_h1))

    mask_legend = (
        "Axa X: cat de des recunoaste greseli in fata echipei (1=deloc, 5=deschis). "
        "Axa Y: cat de des propune idei noi (1=rar, 5=frecvent). "
        "Marimea punctului: proportionala cu riscul de masca. "
        "Culoarea: intensitatea riscului (portocaliu inchis = risc ridicat).\n"
        "Cadrane: Stanga-sus = Creativ/Defensiv | Dreapta-sus = Autentic & Sigur | "
        "Stanga-jos = Tacere Critica | Dreapta-jos = Se simte sigur, e tacut(a)."
        if lang == "Română" else
        "X axis: how often they acknowledge mistakes (1=never, 5=openly). "
        "Y axis: how often they propose new ideas (1=rarely, 5=frequently). "
        "Dot size: proportional to mask risk. "
        "Color: risk intensity (dark orange = high risk).\n"
        "Quadrants: Top-left = Creative/Defensive | Top-right = Authentic & Safe | "
        "Bottom-left = Critical Silence | Bottom-right = Safe but Silent."
    )
    story.append(Paragraph(mask_legend, s_small))
    story.append(Spacer(1, 0.2*cm))

    # Scatter chart matplotlib
    fig_s, ax_s = plt.subplots(figsize=(9, 7))
    fig_s.patch.set_facecolor('white')
    ax_s.set_facecolor('white')
    sizes_s  = (df['S_Score'] / 10 + 5) * 20
    colors_s = df['S_Score'].values
    sc = ax_s.scatter(df['Erori_Asumate'], df['Idei_Noi'],
                      s=sizes_s, c=colors_s, cmap='Oranges',
                      vmin=0, vmax=100, alpha=0.85, edgecolors='white', linewidths=0.5)
    plt.colorbar(sc, ax=ax_s, label="Mask risk (%)", shrink=0.7)
    ax_s.axvline(x=3, color='gray', linestyle=':', linewidth=0.8, alpha=0.5)
    ax_s.axhline(y=3, color='gray', linestyle=':', linewidth=0.8, alpha=0.5)
    for _, row in df.iterrows():
        ax_s.annotate(row['Nume'], (row['Erori_Asumate'], row['Idei_Noi']),
                      fontsize=7, ha='center', va='bottom',
                      xytext=(0, 5), textcoords='offset points')
    # Etichete cadrane
    q_labels = (["Creativ/Defensiv","Autentic & Sigur","Tacere Critica","Se simte sigur, e tacut(a)"]
                 if lang=="Română" else
                 ["Creative/Defensive","Authentic & Safe","Critical Silence","Safe but Silent"])
    q_colors = ['#666','#2E8B57','#C0392B','#B8860B']
    q_pos    = [(1.5,4.6),(4.1,4.6),(1.5,1.2),(4.1,1.2)]
    for (x,y), lbl, col in zip(q_pos, q_labels, q_colors):
        ax_s.text(x, y, lbl, fontsize=7.5, color=col, ha='center',
                  fontstyle='italic', fontweight='bold')
    ax_s.set_xlim(1,5); ax_s.set_ylim(1,5)
    ax_s.set_xlabel("Asumare erori (1-5)" if lang=="Română" else "Error acknowledgment (1-5)", fontsize=9)
    ax_s.set_ylabel("Propunere idei (1-5)" if lang=="Română" else "Idea proposals (1-5)", fontsize=9)
    ax_s.spines['top'].set_visible(False)
    ax_s.spines['right'].set_visible(False)
    ax_s.tick_params(labelsize=8)
    plt.tight_layout()
    img_s = io.BytesIO()
    fig_s.savefig(img_s, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig_s)
    img_s.seek(0)
    story.append(Image(img_s, width=14*cm, height=11*cm))

    cost_m_txt = (f"Pierderi estimate masca politicoasa: EUR {fi['mask']:,.0f}/an ({fi['n_mask']} angajat(i) cu scor sub 3)"
                  if lang=="Română" else
                  f"Estimated polite mask losses: EUR {fi['mask']:,.0f}/year ({fi['n_mask']} employee(s) scoring below 3)")
    story.append(Paragraph(cost_m_txt, s_small))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # PAG 6 — RISC PLECARE
    # ════════════════════════════════════════════════════════
    leaving_title = "Risc de Plecare" if lang == "Română" else "Leaving Risk"
    story.append(Paragraph(leaving_title, s_h1))

    legend_desc_f = (
        "Scor 0-100. Rosu (>65) = risc ridicat | Galben (40-65) = monitorizare | Verde (<40) = in parametri\n"
        "Inlocuirea unui angajat costa 6-9 luni de salariu — recrutare, onboarding si timp pana la productivitate deplina."
        if lang == "Română" else
        "Score 0-100. Red (>65) = elevated risk | Yellow (40-65) = monitor | Green (<40) = within range\n"
        "Replacing an employee costs 6-9 months salary — recruitment, onboarding and ramp-up time."
    )
    story.append(Paragraph(legend_desc_f, s_small))
    story.append(Spacer(1, 0.2*cm))

    df_f = df.sort_values('F_Score', ascending=True)
    colors_f = ['#E74C3C' if s > 65 else '#F39C12' if s > 40 else '#27AE60' for s in df_f['F_Score']]
    f_img = make_bar_chart(
        df_f['Nume'].tolist(), df_f['F_Score'].tolist(), colors_f,
        "Leaving Risk Score (0-100)", 65, 40,
        '#E74C3C', '#F39C12', '#27AE60',
        ">65 Risc ridicat" if lang=="Română" else ">65 Elevated risk",
        "40-65 Monitorizare" if lang=="Română" else "40-65 Monitor",
        "<40 In parametri" if lang=="Română" else "<40 Within range"
    )
    story.append(Image(f_img, width=17*cm, height=min(chart_h, 16*cm)))
    story.append(Spacer(1, 0.2*cm))

    # Tabel risc ridicat
    high_risk = df_f[df_f['F_Score'] > 65][['Nume','F_Score','Ultima_Marire','Scor_Energie']].sort_values('F_Score', ascending=False)
    if not high_risk.empty and salary > 0:
        story.append(Paragraph("Cost estimat inlocuire — membri cu risc ridicat" if lang=="Română" else "Estimated replacement cost — high-risk members", s_h2))
        hr_header = [
            Paragraph("Cod" if lang=="Română" else "Code", s_small),
            Paragraph("Scor risc" if lang=="Română" else "Risk score", s_small),
            Paragraph("Ultima marire (luni)" if lang=="Română" else "Last raise (months)", s_small),
            Paragraph("Energie" if lang=="Română" else "Energy", s_small),
            Paragraph("Cost estimat" if lang=="Română" else "Est. cost", s_small),
        ]
        hr_rows = [hr_header]
        for _, row in high_risk.iterrows():
            hr_rows.append([
                Paragraph(str(row['Nume']), s_body),
                Paragraph(f"{row['F_Score']:.1f}", s_body),
                Paragraph(f"{int(row['Ultima_Marire'])}", s_body),
                Paragraph(f"{int(row['Scor_Energie'])}/5", s_body),
                Paragraph(f"EUR {salary*6:,.0f}-EUR {salary*9:,.0f}", s_body),
            ])
        hr_tbl = Table(hr_rows, colWidths=[4*cm, 2.5*cm, 3.5*cm, 2*cm, 5*cm])
        hr_tbl.setStyle(TableStyle([
            ('BACKGROUND',   (0,0), (-1,0), C_DARK),
            ('TEXTCOLOR',    (0,0), (-1,0), colors.white),
            ('BACKGROUND',   (0,1), (-1,-1), colors.HexColor('#FDEDEC')),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.HexColor('#FDEDEC'), colors.HexColor('#FEF5F5')]),
            ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#CCCCCC')),
            ('LEFTPADDING',  (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING',   (0,0), (-1,-1), 5),
            ('BOTTOMPADDING',(0,0), (-1,-1), 5),
            ('FONTSIZE', (0,0), (-1,-1), 8),
        ]))
        story.append(hr_tbl)

    cost_f_txt = (f"Pierderi estimate risc plecare: EUR {fi['leaving_min']:,.0f}-EUR {fi['leaving_max']:,.0f} ({fi['n_leaving']} angajat(i) cu risc ridicat)"
                  if lang=="Română" else
                  f"Estimated leaving risk losses: EUR {fi['leaving_min']:,.0f}-EUR {fi['leaving_max']:,.0f} ({fi['n_leaving']} employee(s) at high risk)")
    story.append(Paragraph(cost_f_txt, s_small))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # PAG 7 — REȚEAUA DE RELAȚII
    # ════════════════════════════════════════════════════════
    ona_title = "Reteaua Informala de Relatii" if lang == "Română" else "Informal Relationship Network"
    story.append(Paragraph(ona_title, s_h1))

    ona_legend = (
        "Dimensiunea nodului = cati colegi consulta / solicita acel membru al echipei (cu cat e mai mare, cu atat e mai consultat). "
        "Culoarea nodului = risc burnout (verde = scazut, rosu = ridicat). "
        "Sageata indica directia consultarii: de la cel care intreaba spre cel consultat.\n"
        "Noduri izolate (fara conexiuni sau cu putine) = posibil dezangajare sau excludere informala."
        if lang == "Română" else
        "Node size = how many colleagues consult / reach out to that team member (larger = more consulted). "
        "Node color = burnout risk (green = low, red = high). "
        "Arrow indicates consultation direction: from the person asking toward the person consulted.\n"
        "Isolated nodes (no or few connections) = possible disengagement or informal exclusion."
    )
    story.append(Paragraph(ona_legend, s_small))
    story.append(Spacer(1, 0.3*cm))

    # Graf matplotlib
    pos = nx.spring_layout(G, k=1.2, seed=42)
    fig_n, ax_n = plt.subplots(figsize=(11, 9))
    fig_n.patch.set_facecolor('white')
    ax_n.set_facecolor('white')

    nx_nodes = list(G.nodes())
    b_vals   = [G.nodes[n].get('B', 0) for n in nx_nodes]
    sizes_n  = [(G.in_degree(n)*300)+200 for n in nx_nodes]

    import matplotlib.cm as cm_mpl
    cmap  = plt.get_cmap('RdYlGn_r')
    norm  = plt.Normalize(vmin=0, vmax=100)
    node_colors = [cmap(norm(b)) for b in b_vals]

    # Muchii cu săgeți
    for e in G.edges():
        x0, y0 = pos[e[0]]
        x1, y1 = pos[e[1]]
        ax_n.annotate("", xy=(x1,y1), xytext=(x0,y0),
                      arrowprops=dict(arrowstyle="-|>", color='gray',
                                      lw=0.8, alpha=0.5, mutation_scale=12))

    sc_n = ax_n.scatter([pos[n][0] for n in nx_nodes],
                         [pos[n][1] for n in nx_nodes],
                         s=sizes_n, c=b_vals, cmap='RdYlGn_r',
                         vmin=0, vmax=100, alpha=0.9,
                         edgecolors='white', linewidths=1.5, zorder=3)
    plt.colorbar(sc_n, ax=ax_n, label="Burnout risk (0-100)", shrink=0.6)

    for n in nx_nodes:
        x, y = pos[n]
        ax_n.text(x, y - 0.08, n, fontsize=8, ha='center', va='top',
                  fontweight='bold', color='#1F3864')

    ax_n.set_xticks([]); ax_n.set_yticks([])
    ax_n.spines['top'].set_visible(False)
    ax_n.spines['right'].set_visible(False)
    ax_n.spines['left'].set_visible(False)
    ax_n.spines['bottom'].set_visible(False)

    # Legenda dimensiune noduri
    legend_size = [
        plt.scatter([],[], s=200, c='gray', alpha=0.6, label="0 colegi" if lang=="Română" else "0 colleagues"),
        plt.scatter([],[], s=500, c='gray', alpha=0.6, label="1 coleg" if lang=="Română" else "1 colleague"),
        plt.scatter([],[], s=800, c='gray', alpha=0.6, label="2+ colegi" if lang=="Română" else "2+ colleagues"),
    ]
    ax_n.legend(handles=legend_size, title="Consultat de:" if lang=="Română" else "Consulted by:",
                loc='lower left', fontsize=7, title_fontsize=7, framealpha=0.8)

    plt.tight_layout()
    img_n = io.BytesIO()
    fig_n.savefig(img_n, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig_n)
    img_n.seek(0)
    story.append(Image(img_n, width=16*cm, height=13*cm))

    # Identificare hubs și izolați
    hubs_pdf = df[df['ONA_InDegree'] >= 3].sort_values('ONA_InDegree', ascending=False)
    if not hubs_pdf.empty:
        hub_names = ", ".join([f"{r['Nume']} ({int(r['ONA_InDegree'])} colegi)" for _, r in hubs_pdf.iterrows()])
        hub_txt = (f"Persoane-cheie (hub-uri): {hub_names}"
                   if lang=="Română" else f"Key people (hubs): {hub_names}")
        story.append(Paragraph(hub_txt, s_small))

    isolated_pdf = df[df['ONA_Conn'] <= 1]
    if not isolated_pdf.empty:
        iso_names = ", ".join(isolated_pdf['Nume'].tolist())
        iso_txt = (f"Noduri izolate (putine conexiuni): {iso_names} — de inclus in decizii de echipa."
                   if lang=="Română" else
                   f"Isolated nodes (few connections): {iso_names} — include in team decisions.")
        story.append(Paragraph(iso_txt, s_small))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # PAG 8 — ANEXĂ: DATE INDIVIDUALE
    # ════════════════════════════════════════════════════════
    annex_title = "Anexa — Scoruri Individuale" if lang == "Română" else "Annex — Individual Scores"
    story.append(Paragraph(annex_title, s_h1))
    annex_desc = (
        "Tabel complet cu indicatorii calculati pentru fiecare membru al echipei. "
        "B = Burnout (0-100), F = Risc Plecare (0-100), Mask = Siguranta Psihologica (1-5), "
        "Hub = consultat de X colegi."
        if lang == "Română" else
        "Full table with calculated indicators for each team member. "
        "B = Burnout (0-100), F = Leaving Risk (0-100), Mask = Psychological Safety (1-5), "
        "Hub = consulted by X colleagues."
    )
    story.append(Paragraph(annex_desc, s_small))
    story.append(Spacer(1, 0.3*cm))

    ann_cols = ['Cod' if lang=='Română' else 'Code', 'B Score', 'F Score', 'Mask (1-5)',
                'Hub', 'Ore/sapt' if lang=='Română' else 'Hours/wk',
                'Zile conc.' if lang=='Română' else 'Vac. days', 'Energie' if lang=='Română' else 'Energy']
    ann_header = [Paragraph(c, ParagraphStyle('ah', fontSize=7.5, fontName=F_BOLD,
                 textColor=colors.white)) for c in ann_cols]
    ann_rows = [ann_header]
    df_ann = df.sort_values('B_Score', ascending=False)
    for _, row in df_ann.iterrows():
        b_color = colors.HexColor('#FDEDEC') if row['B_Score'] > 70 else \
                  colors.HexColor('#FEF9E7') if row['B_Score'] > 50 else \
                  colors.HexColor('#EAFAF1')
        ann_rows.append([
            Paragraph(str(row['Nume']), ParagraphStyle('ac', fontSize=8, fontName=F_NORMAL)),
            Paragraph(f"{row['B_Score']:.1f}", ParagraphStyle('ac', fontSize=8, fontName=F_BOLD,
                     textColor=C_RED if row['B_Score']>70 else C_ORANGE if row['B_Score']>50 else C_GREEN)),
            Paragraph(f"{row['F_Score']:.1f}", ParagraphStyle('ac', fontSize=8, fontName=F_BOLD,
                     textColor=C_RED if row['F_Score']>65 else C_ORANGE if row['F_Score']>40 else C_GREEN)),
            Paragraph(f"{row['S_Raw']:.1f}", ParagraphStyle('ac', fontSize=8, fontName=F_NORMAL,
                     textColor=C_RED if row['S_Raw']<3 else colors.HexColor('#2C3E50'))),
            Paragraph(str(int(row['ONA_InDegree'])),
                      ParagraphStyle('ac', fontSize=8, fontName=F_NORMAL,
                     textColor=C_ORANGE if row['ONA_InDegree']>=3 else colors.HexColor('#2C3E50'))),
            Paragraph(str(int(row['Ore_Saptamana'])), ParagraphStyle('ac', fontSize=8, fontName=F_NORMAL)),
            Paragraph(str(int(row['Zile_Concediu'])), ParagraphStyle('ac', fontSize=8, fontName=F_NORMAL)),
            Paragraph(f"{int(row['Scor_Energie'])}/5", ParagraphStyle('ac', fontSize=8, fontName=F_NORMAL)),
        ])
    ann_tbl = Table(ann_rows, colWidths=[4*cm, 1.8*cm, 1.8*cm, 2*cm, 1.5*cm, 2*cm, 2*cm, 2*cm])
    ann_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  C_DARK),
        ('TEXTCOLOR',     (0,0), (-1,0),  colors.white),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, colors.HexColor('#F8F9FA')]),
        ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#CCCCCC')),
        ('LEFTPADDING',   (0,0), (-1,-1), 5),
        ('RIGHTPADDING',  (0,0), (-1,-1), 5),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(ann_tbl)

    # CTA final
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_GRAY))
    story.append(Spacer(1, 0.3*cm))
    cta_txt = (
        "Pentru o analiza mai profunda sau programe de dezvoltare pentru echipa dvs., "
        "contactati-ma direct pe LinkedIn: linkedin.com/in/razvanghebaur"
        if lang == "Română" else
        "For a deeper analysis or development programmes for your team, "
        "contact me directly on LinkedIn: linkedin.com/in/razvanghebaur"
    )
    story.append(Paragraph(cta_txt, ParagraphStyle('cta', fontSize=9, fontName=F_NORMAL,
                 textColor=colors.HexColor('#2471A3'), leading=14)))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    buf.seek(0)
    return buf.read()


def render_pdf_button(df, G, fi, lang, salary, key_suffix=""):
    """Render the PDF download button — generates only when clicked."""
    st.markdown("---")

    # Câmpul de echipă/departament — shared prin session_state (același indiferent de tab)
    if 'pdf_team_name' not in st.session_state:
        st.session_state['pdf_team_name'] = ""

    label_input = (
        "Completează numele echipei / departamentului și firmei (opțional)"
        if lang == "Română" else
        "Enter team / department and company name (optional)"
    )
    placeholder_input = (
        "Ex: Echipa Vânzări — Compania X"
        if lang == "Română" else
        "E.g. Sales Team — Company X"
    )
    team_name = st.text_input(
        label_input,
        value=st.session_state['pdf_team_name'],
        key=f"team_name_input_{key_suffix}",
        placeholder=placeholder_input
    )
    st.session_state['pdf_team_name'] = team_name

    pdf_key = f"pdf_bytes_{key_suffix}"
    btn_label = "📄 Generează și descarcă raport PDF" if lang == "Română" else "📄 Generate & download PDF report"

    if st.button(btn_label, key=f"pdf_gen_{key_suffix}", use_container_width=True):
        try:
            with st.spinner("Se generează PDF..." if lang == "Română" else "Generating PDF..."):
                pdf_bytes = generate_pdf_report(df, G, fi, lang, salary, team_name)
            st.session_state[pdf_key] = pdf_bytes
        except Exception as e:
            st.error(f"Eroare la generarea PDF: {e}" if lang == "Română" else f"PDF generation error: {e}")
            st.session_state[pdf_key] = None

    if st.session_state.get(pdf_key):
        fname = f"TeamScientist_Diagnostic_{datetime.now().strftime('%Y%m%d')}.pdf"
        st.download_button(
            label="⬇️ Descarcă PDF" if lang == "Română" else "⬇️ Download PDF",
            data=st.session_state[pdf_key],
            file_name=fname,
            mime="application/pdf",
            use_container_width=True,
            key=f"pdf_dl_{key_suffix}"
        )


def render_landing_page(lang, template_bytes):
    if lang == "Română":
        st.markdown("""
<div style='max-width:780px;margin:0 auto;padding:2rem 0 0.5rem;'>
  <div style='font-size:12px;font-weight:500;color:#888;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:1.2rem;'>🔬 TeamScientist</div>
  <p style='font-size:17px;line-height:1.8;margin:0 0 1rem;'>
    Mă numesc <strong>Răzvan Ghebaur</strong> și de peste 20 de ani lucrez împreună cu manageri și antreprenori care vor să creeze și să mențină echipe eficiente și sănătoase relațional.
  </p>
  <p style='font-size:17px;line-height:1.8;margin:0 0 1rem;'>
    Vă invit să testați un instrument care vă arată concret ce funcționează bine în echipa dvs., dar și ce pierderi ascunse pot exista.
  </p>
  <p style='font-size:17px;line-height:1.8;margin:0 0 0.5rem;'><strong>Cum funcționează?</strong></p>
  <p style='font-size:17px;line-height:1.8;margin:0 0 1rem;'>
    Veți avea nevoie de 15–20 de minute să adunați câteva date anonimizate pe care în mod normal le aveți deja la îndemână. Apoi veți încărca tabelul în spațiul dedicat de mai jos.
  </p>
  <p style='font-size:17px;line-height:1.8;margin:0 0 0.5rem;'><strong>Ce veți primi în schimb?</strong></p>
  <p style='font-size:17px;line-height:1.8;margin:0 0 1rem;'>
    O diagnoză valoroasă și un set de acțiuni concrete de management pe care să le puneți în practică se vor afișa automat, imediat ce ați încărcat tabelul cu datele anonimizate.
  </p>
  <p style='font-size:17px;line-height:1.8;margin:0 0 0.75rem;'>
    Veți primi răspunsuri și sugestii acționabile la următoarele întrebări importante pentru orice manager interesat de propria echipă și de rezultatele ei:
  </p>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
<div style='max-width:780px;margin:0 auto;padding:2rem 0 0.5rem;'>
  <div style='font-size:12px;font-weight:500;color:#888;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:1.2rem;'>🔬 TeamScientist</div>
  <p style='font-size:17px;line-height:1.8;margin:0 0 1rem;'>
    My name is <strong>Răzvan Ghebaur</strong> and for over 20 years I have been working alongside managers and entrepreneurs who want to build and maintain efficient, relationally healthy teams.
  </p>
  <p style='font-size:17px;line-height:1.8;margin:0 0 1rem;'>
    I invite you to test an instrument that shows you concretely what is working well in your team — and what hidden losses may exist.
  </p>
  <p style='font-size:17px;line-height:1.8;margin:0 0 0.5rem;'><strong>How does it work?</strong></p>
  <p style='font-size:17px;line-height:1.8;margin:0 0 1rem;'>
    You will need 15–20 minutes to gather a few anonymised data points you already have at hand. Then you upload the table in the dedicated space below.
  </p>
  <p style='font-size:17px;line-height:1.8;margin:0 0 0.5rem;'><strong>What will you receive in return?</strong></p>
  <p style='font-size:17px;line-height:1.8;margin:0 0 1rem;'>
    A valuable diagnosis and a set of concrete management actions will appear automatically as soon as you upload the table with the anonymised data.
  </p>
  <p style='font-size:17px;line-height:1.8;margin:0 0 0.75rem;'>
    You will receive answers and actionable suggestions to the following questions — important for any manager who cares about their team and its results:
  </p>
</div>""", unsafe_allow_html=True)

    # ── CELE 4 CASETE ─────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if lang == "Română":
            st.markdown("<div style='background:#FCEBEB;border-radius:12px;padding:1.25rem;border:1px solid #F09595;height:100%;'><div style='font-size:22px;margin-bottom:10px;'>🔥</div><p style='font-size:14px;font-weight:600;color:#A32D2D;margin:0 0 8px;'>Cine prezintă stres ridicat și risc de burnout?</p><p style='font-size:13px;line-height:1.55;color:#791F1F;margin:0;'>Identifici cine lucrează peste limită și cine are energia în scădere — înainte ca problema să devină vizibilă.</p></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background:#FCEBEB;border-radius:12px;padding:1.25rem;border:1px solid #F09595;height:100%;'><div style='font-size:22px;margin-bottom:10px;'>🔥</div><p style='font-size:14px;font-weight:600;color:#A32D2D;margin:0 0 8px;'>Who shows elevated stress and burnout risk?</p><p style='font-size:13px;line-height:1.55;color:#791F1F;margin:0;'>Identify who is working beyond their limit and whose energy is declining — before it becomes a visible problem.</p></div>", unsafe_allow_html=True)
    with c2:
        if lang == "Română":
            st.markdown("<div style='background:#FAEEDA;border-radius:12px;padding:1.25rem;border:1px solid #FAC775;height:100%;'><div style='font-size:22px;margin-bottom:10px;'>✈️</div><p style='font-size:14px;font-weight:600;color:#854F0B;margin:0 0 8px;'>Cine se gândește la plecare?</p><p style='font-size:13px;line-height:1.55;color:#633806;margin:0;'>Afli cine are factori de risc și cât te-ar costa înlocuirea — cu cifre, nu cu presupuneri.</p></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background:#FAEEDA;border-radius:12px;padding:1.25rem;border:1px solid #FAC775;height:100%;'><div style='font-size:22px;margin-bottom:10px;'>✈️</div><p style='font-size:14px;font-weight:600;color:#854F0B;margin:0 0 8px;'>Who is thinking about leaving?</p><p style='font-size:13px;line-height:1.55;color:#633806;margin:0;'>Find out who has risk factors and what replacement would cost — with numbers, not assumptions.</p></div>", unsafe_allow_html=True)
    with c3:
        if lang == "Română":
            st.markdown("<div style='background:#E1F5EE;border-radius:12px;padding:1.25rem;border:1px solid #5DCAA5;height:100%;'><div style='font-size:22px;margin-bottom:10px;'>🕸️</div><p style='font-size:14px;font-weight:600;color:#0F6E56;margin:0 0 8px;'>Cum arată rețeaua informală de relații din echipa mea?</p><p style='font-size:13px;line-height:1.55;color:#085041;margin:0;'>Descoperi cine sunt persoanele-cheie, cine e izolat și unde există silozuri de colaborare.</p></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background:#E1F5EE;border-radius:12px;padding:1.25rem;border:1px solid #5DCAA5;height:100%;'><div style='font-size:22px;margin-bottom:10px;'>🕸️</div><p style='font-size:14px;font-weight:600;color:#0F6E56;margin:0 0 8px;'>What does my team's informal relationship network look like?</p><p style='font-size:13px;line-height:1.55;color:#085041;margin:0;'>Discover who the key people are, who is isolated, and where collaboration silos exist.</p></div>", unsafe_allow_html=True)
    with c4:
        if lang == "Română":
            st.markdown("<div style='background:#F3EEF9;border-radius:12px;padding:1.25rem;border:1px solid #C39BD3;height:100%;'><div style='font-size:22px;margin-bottom:10px;'>🤐</div><p style='font-size:14px;font-weight:600;color:#6C3483;margin:0 0 8px;'>Cine are o mască politicoasă exagerată?</p><p style='font-size:13px;line-height:1.55;color:#512E7F;margin:0;'>Afli cine din echipă se ferește să vină cu idei și să-și asume erori.</p></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background:#F3EEF9;border-radius:12px;padding:1.25rem;border:1px solid #C39BD3;height:100%;'><div style='font-size:22px;margin-bottom:10px;'>🤐</div><p style='font-size:14px;font-weight:600;color:#6C3483;margin:0 0 8px;'>Who is wearing an exaggerated polite mask?</p><p style='font-size:13px;line-height:1.55;color:#512E7F;margin:0;'>Find out who in the team avoids sharing ideas and owning mistakes.</p></div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

    # ── TARGET / CINE E PENTRU DVS ────────────────────────────
    if lang == "Română":
        st.markdown("""
<div style='max-width:780px;margin:0 auto 1.5rem;'>
  <p style='font-size:17px;line-height:1.8;margin:0 0 1rem;'>
    Dacă aveți în coordonare directă între <strong>8 și 20 de oameni</strong> — acest instrument este pentru dvs.
  </p>
  <p style='font-size:17px;line-height:1.8;margin:0;'>
    Dacă doriți să rămâneți la curent cu evoluția instrumentului sau vreți pur și simplu să oferiți sugestii și feedback, sunteți bineveniți să mă contactați direct pe <a href='https://linkedin.com/in/razvanghebaur' target='_blank' style='color:#2471A3;'>LinkedIn</a>.
  </p>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
<div style='max-width:780px;margin:0 auto 1.5rem;'>
  <p style='font-size:17px;line-height:1.8;margin:0 0 1rem;'>
    If you directly manage between <strong>8 and 20 people</strong> — this instrument is for you.
  </p>
  <p style='font-size:17px;line-height:1.8;margin:0;'>
    If you would like to stay informed about the instrument's evolution or simply share suggestions and feedback, you are welcome to contact me directly on <a href='https://linkedin.com/in/razvanghebaur' target='_blank' style='color:#2471A3;'>LinkedIn</a>.
  </p>
</div>""", unsafe_allow_html=True)

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
            f"<div><p style='font-size:13px;color:#888;margin:0;'>{'Pasul 1' if lang=='Română' else 'Step 1'}</p>"
            f"<p style='font-size:14px;font-weight:600;color:inherit;margin:0;'>{'Descarcă și completează' if lang=='Română' else 'Download and fill in'}</p></div></div>"
            f"<p style='font-size:13px;color:#888;margin:0 0 8px;'>{'~15 minute' if lang=='Română' else '~15 minutes'}</p>"
            f"<p style='font-size:15px;line-height:1.6;opacity:0.85;margin:0 0 1rem;'>{'Descarcă template-ul Excel și completează datele echipei tale urmând instrucțiunile din fișier. Datele sunt cele pe care le știi deja sau pe care le poți afla ușor.' if lang=='Română' else 'Download the Excel template and fill in your team data following the instructions in the file. The data is what you already know or can easily find out.'}"
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
            f"<div><p style='font-size:13px;color:#888;margin:0;'>{'Pasul 2' if lang=='Română' else 'Step 2'}</p>"
            f"<p style='font-size:14px;font-weight:600;color:inherit;margin:0;'>{'Încarcă XLS completat' if lang=='Română' else 'Upload completed XLS'}</p></div></div>"
            f"<p style='font-size:13px;color:#888;margin:0 0 8px;'>{'30 secunde' if lang=='Română' else '30 seconds'}</p>"
            f"<p style='font-size:15px;line-height:1.6;opacity:0.85;margin:0 0 1rem;'>{'Încarcă fișierul completat direct în aplicație. Diagnosticul se generează automat.' if lang=='Română' else 'Upload the completed file directly into the application. The diagnostic is generated automatically.'}"
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
            f"<div><p style='font-size:13px;color:#888;margin:0;'>{'Pasul 3' if lang=='Română' else 'Step 3'}</p>"
            f"<p style='font-size:14px;font-weight:600;color:inherit;margin:0;'>{'Explorează și descarcă diagnosticul' if lang=='Română' else 'Explore and download the diagnostic'}</p></div></div>"
            f"<p style='font-size:13px;color:#888;margin:0 0 8px;'>{'cât vrei' if lang=='Română' else 'as long as you want'}</p>"
            f"<p style='font-size:15px;line-height:1.6;opacity:0.85;margin:0;'>{'5 tab-uri cu vizualizări clare și recomandări concrete. La final, descarcă raportul PDF complet al diagnosticului.' if lang=='Română' else '5 tabs with clear visualizations and concrete recommendations. Download the full PDF diagnostic report when ready.'}"
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
            "👇 **Diagnosticul echipei dvs. este gata.** Explorați rezultatele în cele 5 tab-uri de mai jos. Începeți cu **Rezumat & Acțiuni** pentru o imagine de ansamblu, apoi aprofundați fiecare dimensiune."
            if lang == "Română" else
            "👇 **Your diagnostic is ready.** Explore the results in the 5 tabs below. Start with **Summary & Actions** for an overview, then dive into each dimension."
        )
        st.info(tab_guide)

        # TABS
        tab_labels = (
            ["📋 Rezumat & Acțiuni", "🔥 Stres & Burnout", "🤐 Masca Politicoasă", "✈️ Risc Plecare", "🕸️ Rețeaua de Relații"]
            if lang == "Română" else
            ["📋 Summary & Actions", "🔥 Stress & Burnout", "🤐 Polite Mask", "✈️ Leaving Risk", "🕸️ Relationship Network"]
        )
        tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_labels)

        # TAB 1: INSIGHTS
        with tab1:
            render_insights_tab(df, G, lang, salary, fi)
            render_pdf_button(df, G, fi, lang, salary, key_suffix="tab1")

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
            render_pdf_button(df, G, fi, lang, salary, key_suffix="tab2")

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
            render_pdf_button(df, G, fi, lang, salary, key_suffix="tab3")

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
            render_pdf_button(df, G, fi, lang, salary, key_suffix="tab4")

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
            render_pdf_button(df, G, fi, lang, salary, key_suffix="tab5")

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
