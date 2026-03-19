import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import numpy as np

st.set_page_config(page_title="Team Scientist | Strategic Audit", layout="wide")

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

salary = st.sidebar.number_input(
    "Salariu mediu lunar estimat (€)" if st.session_state.lang == "Română"
    else "Estimated avg monthly salary (€)",
    value=3000, step=500,
    help="Folosit pentru estimarea costului de înlocuire."
    if st.session_state.lang == "Română"
    else "Used to estimate replacement cost in Leaving Risk."
)

# ── TRADUCERI UI ─────────────────────────────────────────────
UI = {
    "Română": {
        "title":   "🔬 Team Scientist | Diagnostic Strategic",
        "upload":  "Încarcă fișierul TeamScientist_Audit_Demo_v2.xlsx",
        "err_col": "❌ Lipsesc coloanele:",
        "b_title": "🔥 Burnout",
        "s_title": "🤐 Masca Politicoasă",
        "f_title": "✈️ Risc Plecare",
        "o_title": "🕸️ Rețeaua (ONA)",
        "i_title": "🧩 Insights",
        "b_desc":  "Scor 0–100. Peste 70 = Risc Critic | 50–70 = Atenție.",
        "b_legend":"Roșu = critic (>70) | Galben = atenție (50–70) | Verde = OK (<50)",
        "s_q1":    "Autentic & Sigur",
        "s_q2":    "Safe but Silent",
        "s_q3":    "Risc Cultural",
        "s_q4":    "Tăcere Critică",
        "s_desc":  "Axa X = Siguranță psihologică declarată | Axa Y = Comportamente observabile (erori + idei)",
        "f_desc":  "Scor 0–100. Peste 65 = Risc Mare | 40–65 = Monitorizare.",
        "f_cost":  "Înlocuirea unui angajat costă 6–12 luni de productivitate.",
        "o_desc":  "Dimensiunea nodului = câți colegi te consultă | Culoarea = risc burnout",
        "o_legend":"Nod mare + roșu = hub supraîncărcat (risc sistemic)",
    },
    "English": {
        "title":   "🔬 Team Scientist | Strategic Diagnostic",
        "upload":  "Upload TeamScientist_Audit_Demo_v2.xlsx",
        "err_col": "❌ Missing columns:",
        "b_title": "🔥 Burnout",
        "s_title": "🤐 Polite Mask",
        "f_title": "✈️ Flight Risk",
        "o_title": "🕸️ Network (ONA)",
        "i_title": "🧩 Insights",
        "b_desc":  "Score 0–100. Over 70 = Critical Risk | 50–70 = Warning.",
        "b_legend":"Red = critical (>70) | Yellow = warning (50–70) | Green = OK (<50)",
        "s_q1":    "Authentic & Safe",
        "s_q2":    "Safe but Silent",
        "s_q3":    "Cultural Risk",
        "s_q4":    "Critical Silence",
        "s_desc":  "X axis = declared psychological safety | Y axis = observable behaviors (errors + ideas)",
        "f_desc":  "Score 0–100. Over 65 = High Risk | 40–65 = Monitor.",
        "f_cost":  "Replacing one employee costs 6–12 months of productivity.",
        "o_desc":  "Node size = how many colleagues consult you | Color = burnout risk",
        "o_legend":"Large + red node = overloaded hub (systemic risk)",
    }
}

# ── COLOANE OBLIGATORII ──────────────────────────────────────
REQUIRED_COLUMNS = [
    'Nume', 'Ore_Saptamana', 'Presiune_Externa', 'Idei_Noi',
    'Erori_Asumate', 'Ultima_Marire', 'Scor_Energie',
    'Zile_Concediu', 'Sfat_De_La'
]

# ════════════════════════════════════════════════════════════
# FORMULE (formulas.py integrat)
# ════════════════════════════════════════════════════════════

def compute_indicators(df):
    df = df.copy()
    num_cols = [
        'Ore_Saptamana', 'Presiune_Externa', 'Idei_Noi', 'Erori_Asumate',
        'Vechime_Rol', 'Ultima_Marire', 'Scor_Energie', 'Zile_Concediu'
    ]
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
    df['Vechime_Rol']      = df['Vechime_Rol'].fillna(1) if 'Vechime_Rol' in df.columns else df.assign(Vechime_Rol=12)['Vechime_Rol']

    # BURNOUT
    S_hours    = ((df['Ore_Saptamana'] - 40) / 20 * 100).clip(0, 100)
    S_vacation = ((20 - df['Zile_Concediu']) / 20 * 100).clip(0, 100)
    S_energy   = ((5 - df['Scor_Energie']) / 4 * 100).clip(0, 100)
    S_pressure = ((df['Presiune_Externa'] - 1) / 4 * 100).clip(0, 100)

    df['B_Score'] = (
        0.30 * S_hours +
        0.20 * S_vacation +
        0.25 * S_energy +
        0.25 * S_pressure
    ).clip(0, 100).round(1)

    # POLITE MASK
    mask_raw      = (df['Erori_Asumate'] + df['Idei_Noi']) / 2
    df['S_Raw']   = mask_raw.round(2)
    df['S_Score'] = ((5 - mask_raw) / 4 * 100).clip(0, 100).round(1)
    df['S_Diss']  = df['S_Score']
    df['S_Size']  = (df['S_Score'] / 10 + 5).clip(5, 20)
    df['S_Contr'] = mask_raw

    # ONA
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

    # LEAVING RISK
    vec = df['Vechime_Rol'].clip(lower=1) if 'Vechime_Rol' in df.columns else pd.Series([12] * n)
    S_stagnation = (df['Ultima_Marire'] / vec * 100).clip(0, 100)
    S_wellbeing  = (((5 - df['Scor_Energie']) + (df['Presiune_Externa'] - 1)) / 8 * 100).clip(0, 100)

    df['F_Score'] = (
        0.40 * S_stagnation +
        0.40 * S_wellbeing +
        0.20 * S_ona
    ).clip(0, 100).round(1)

    return df, G


def burnout_label(score):
    if score > 70: return "🔴 Critic"
    if score > 50: return "🟡 Atenție"
    return "🟢 OK"

def leaving_label(score):
    if score > 65: return "🔴 Risc Mare"
    if score > 40: return "🟡 Monitorizare"
    return "🟢 Stabil"

def mask_label_raw(raw):
    if raw < 3:  return "🔴 Zonă Critică"
    if raw <= 4: return "🟡 Safe but Silent"
    return "🟢 Autentic & Sigur"


# ════════════════════════════════════════════════════════════
# INSIGHTS ENGINE (insights_engine.py integrat)
# ════════════════════════════════════════════════════════════

TEXTS = {
    "Română": {
        "exec_title":   "Rezumat executiv",
        "exec_all_ok":  "Echipa funcționează în parametri normali. Niciun risc critic identificat.",
        "exec_some_risk": "Au fost identificate {n_risk} situații care necesită atenție în 30 de zile.",
        "exec_critical": "{n_critical} angajat(ți) în zonă critică — intervenție imediată.",
        "sec_urgent":   "Urgențe — intervenție imediată",
        "sec_monitor":  "Monitorizare activă — 30 de zile",
        "sec_patterns": "Tipare la nivel de echipă",
        "sec_ok":       "Ce funcționează bine",
        "action_title": "Ce faci concret — această săptămână",
        "pattern_cultural_silence": "Problemă culturală de siguranță psihologică",
        "pattern_cultural_silence_desc": (
            "{pct}% din echipă are scor Polite Mask sub 3. "
            "Aceasta indică o problemă sistemică de cultură, nu individuală. "
            "Oamenii tac pentru că nu se simt în siguranță să greșească sau să propună. "
            "Intervenția necesară este la nivel de echipă, nu per angajat."
        ),
        "pattern_hub_risk": "Nod central supraîncărcat — risc sistemic",
        "pattern_hub_risk_desc": (
            "{name} este consultat de {n_conn} colegi și are simultan burnout ridicat ({b:.0f}) "
            "și risc de plecare ridicat ({f:.0f}). "
            "Dacă această persoană pleacă, fluxul informal de cunoaștere al echipei se întrerupe brusc. "
            "Acesta este cel mai costisitor scenariu de risc din audit."
        ),
        "pattern_isolation": "Izolare totală — deconectare dublă",
        "pattern_isolation_desc": (
            "{names} prezintă izolare în rețea combinată cu mască politicoasă. "
            "Nu cer ajutor și nu contribuie — semnal timpuriu de dezangajare silențioasă."
        ),
        "pattern_silent_stars": "Performeri tăcuți — potențial neexploatat",
        "pattern_silent_stars_desc": (
            "{names} au indicatori buni dar scor Polite Mask scăzut. "
            "O conversație directă despre ce îi oprește poate debloca contribuții valoroase."
        ),
        "pattern_ok": "Nucleu stabil",
        "pattern_ok_desc": (
            "{names} prezintă toți indicatorii în parametri normali. "
            "Reprezintă fundația stabilă a echipei."
        ),
        "burnout_critical": (
            "{name} se află în burnout avansat (scor {b:.0f}/100). "
            "Lucrează {ore}h/săptămână, {concediu} zi(e) concediu, energie {energie}/5. "
            "Fără intervenție în 1–2 săptămâni, riscul de colaps sau demisie este ridicat."
        ),
        "burnout_warning": (
            "{name} prezintă semne timpurii de burnout (scor {b:.0f}/100). "
            "Energie {energie}/5, {ore}h/săpt. — oboseală acumulată, necesită monitorizare."
        ),
        "burnout_ok": "{name} funcționează în parametri normali din perspectiva energiei și efortului.",
        "leaving_critical": (
            "{name} are risc de plecare ridicat (scor {f:.0f}/100). "
            "Ultima mărire: acum {marire} luni | Energie: {energie}/5 | "
            "Consultat de {conn} colegi. Cost estimat înlocuire: {cost}."
        ),
        "leaving_monitor": (
            "{name} prezintă factori de risc moderați (scor {f:.0f}/100). "
            "Stagnare financiară ({marire} luni) — conversație de carieră în 30 de zile."
        ),
        "leaving_ok": "{name} este stabil din perspectiva riscului de plecare.",
        "mask_critical": (
            "{name} tace activ (Polite Mask {mask:.1f}/5). "
            "Nu raportează erori și nu propune idei — se simte nesigur(ă). "
            "Prioritar: conversație de siguranță psihologică, nu de performanță."
        ),
        "mask_silent": (
            "{name} are potențial neexploatat (Polite Mask {mask:.1f}/5). "
            "Contribuție mai mare posibilă dacă mediul devine mai permisiv cu erorile."
        ),
        "mask_ok": "{name} contribuie autentic și se simte în siguranță să greșească și să propună.",
        "action_burnout_critical": (
            "Programează 1:1 cu {name} în 48h. Nu evaluare — ascultare. "
            "Întreabă ce ar face situația mai sustenabilă."
        ),
        "action_leaving_critical": (
            "Inițiază conversație de carieră cu {name}. "
            "Verifică dacă există spațiu pentru ajustare salarială sau de rol."
        ),
        "action_mask_critical": (
            "Cu {name}: înlocuiește feedback-ul de grup cu 1:1. "
            "Creează un moment explicit în care eroarea este normalizată public."
        ),
        "action_hub": (
            "Distribuie din responsabilitățile informale ale lui {name}. "
            "Identifică cine poate prelua 20% din cererile de sfat."
        ),
        "action_isolated": (
            "Include {name} explicit în cel puțin o decizie de echipă săptămâna aceasta."
        ),
        "replacement_cost": "~{min}–{max} (6–12 luni salariu + recrutare)",
    },
    "English": {
        "exec_title":   "Executive summary",
        "exec_all_ok":  "The team is operating within normal parameters. No critical risks identified.",
        "exec_some_risk": "{n_risk} situation(s) require attention in the next 30 days.",
        "exec_critical": "{n_critical} employee(s) in the critical zone — immediate action required.",
        "sec_urgent":   "Urgent — immediate action required",
        "sec_monitor":  "Active monitoring — 30 days",
        "sec_patterns": "Team-level patterns",
        "sec_ok":       "What's working well",
        "action_title": "What you do concretely — this week",
        "pattern_cultural_silence": "Cultural psychological safety issue",
        "pattern_cultural_silence_desc": (
            "{pct}% of the team scores below 3 on the Polite Mask indicator. "
            "This signals a systemic cultural issue, not an individual one. "
            "People are silent because it doesn't feel safe to make mistakes or propose ideas. "
            "The intervention must happen at team level, not person by person."
        ),
        "pattern_hub_risk": "Overloaded central hub — systemic risk",
        "pattern_hub_risk_desc": (
            "{name} is consulted by {n_conn} colleagues and simultaneously shows high burnout ({b:.0f}) "
            "and high leaving risk ({f:.0f}). "
            "If this person leaves, the team's informal knowledge flow breaks down abruptly. "
            "This is the most costly risk scenario in this audit."
        ),
        "pattern_isolation": "Total disconnection — dual isolation",
        "pattern_isolation_desc": (
            "{names} show network isolation combined with a polite mask. "
            "They don't ask for help and don't contribute — early signal of silent disengagement."
        ),
        "pattern_silent_stars": "Silent performers — untapped potential",
        "pattern_silent_stars_desc": (
            "{names} perform well but score low on Polite Mask. "
            "A direct conversation about what holds them back may unlock valuable contributions."
        ),
        "pattern_ok": "Stable core",
        "pattern_ok_desc": (
            "{names} show all indicators within normal parameters. "
            "They represent the stable foundation of the team."
        ),
        "burnout_critical": (
            "{name} is in advanced burnout (score {b:.0f}/100). "
            "Working {ore}h/week, {concediu} vacation day(s), energy {energie}/5. "
            "Without intervention in 1–2 weeks, collapse or sudden resignation risk is high."
        ),
        "burnout_warning": (
            "{name} shows early burnout signs (score {b:.0f}/100). "
            "Energy {energie}/5, {ore}h/week — accumulating fatigue, needs monitoring."
        ),
        "burnout_ok": "{name} is operating within normal parameters for energy and effort.",
        "leaving_critical": (
            "{name} has high leaving risk (score {f:.0f}/100). "
            "Last raise: {marire} months ago | Energy: {energie}/5 | "
            "Consulted by {conn} colleagues. Estimated replacement cost: {cost}."
        ),
        "leaving_monitor": (
            "{name} shows moderate risk factors (score {f:.0f}/100). "
            "Financial stagnation ({marire} months) — career conversation within 30 days."
        ),
        "leaving_ok": "{name} is stable from a leaving risk perspective.",
        "mask_critical": (
            "{name} is actively silent (Polite Mask {mask:.1f}/5). "
            "Doesn't report errors or propose ideas — feels unsafe. "
            "Priority: psychological safety conversation, not performance review."
        ),
        "mask_silent": (
            "{name} has untapped potential (Polite Mask {mask:.1f}/5). "
            "Greater contribution possible if the environment becomes more permissive with mistakes."
        ),
        "mask_ok": "{name} contributes authentically and feels safe to make mistakes and propose ideas.",
        "action_burnout_critical": (
            "Schedule a 1:1 with {name} within 48h. Not an evaluation — listening. "
            "Ask what would make the situation more sustainable."
        ),
        "action_leaving_critical": (
            "Initiate a career conversation with {name}. "
            "Check if there's room for a salary or role adjustment."
        ),
        "action_mask_critical": (
            "With {name}: replace group feedback with 1:1 conversations. "
            "Create an explicit moment where making mistakes is publicly normalized."
        ),
        "action_hub": (
            "Distribute some of {name}'s informal responsibilities. "
            "Identify who could take over 20% of the advice requests."
        ),
        "action_isolated": (
            "Include {name} explicitly in at least one team decision this week."
        ),
        "replacement_cost": "~{min}–{max} (6–12 months salary + recruitment)",
    }
}


def fmt_cost(salary_monthly, t):
    return t["replacement_cost"].format(
        min=f"€{salary_monthly * 6:,.0f}",
        max=f"€{salary_monthly * 12:,.0f}"
    )


def insight_card(text, level="info"):
    colors = {
        "critical": ("#FDEDEC", "#C0392B", "⚠", "#7B241C"),
        "warning":  ("#FEF9E7", "#E67E22", "◉", "#784212"),
        "ok":       ("#EAFAF1", "#1E8449", "✓", "#1D6A39"),
        "info":     ("#EBF5FB", "#2471A3", "→", "#1A5276"),
    }
    bg, border, icon, text_color = colors.get(level, colors["info"])
    st.markdown(
        f"<div style='background:{bg};border-left:3px solid {border};"
        f"border-radius:0 8px 8px 0;padding:12px 16px;margin:6px 0;"
        f"font-size:14px;line-height:1.6;color:{text_color}'>"
        f"<span style='color:{border};margin-right:8px'>{icon}</span>{text}</div>",
        unsafe_allow_html=True
    )


def action_card(text):
    st.markdown(
        f"<div style='background:#F4F6F7;border:1px solid #D5D8DC;"
        f"border-radius:8px;padding:12px 16px;margin:4px 0;"
        f"font-size:13px;line-height:1.6;color:#2C3E50'>"
        f"<span style='color:#E67E22;margin-right:8px;font-weight:600'>→</span>{text}</div>",
        unsafe_allow_html=True
    )


def section_header(title, color="#1C2833"):
    st.markdown(
        f"<div style='margin:24px 0 10px;padding:8px 14px;"
        f"background:{color}10;border-left:3px solid {color};"
        f"border-radius:0 6px 6px 0;font-weight:600;font-size:15px'>"
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
    cost     = fmt_cost(salary, t) if salary > 0 else "N/A"
    actions  = []

    if b > 70:
        bt, bl = t["burnout_critical"].format(name=name, b=b, ore=ore, concediu=concediu, energie=energie), "critical"
        actions.append(t["action_burnout_critical"].format(name=name))
    elif b > 50:
        bt, bl = t["burnout_warning"].format(name=name, b=b, ore=ore, energie=energie), "warning"
    else:
        bt, bl = t["burnout_ok"].format(name=name), "ok"

    if f > 65:
        ft, fl = t["leaving_critical"].format(name=name, f=f, marire=marire, energie=energie, conn=conn, cost=cost), "critical"
        actions.append(t["action_leaving_critical"].format(name=name))
    elif f > 40:
        ft, fl = t["leaving_monitor"].format(name=name, f=f, marire=marire), "warning"
    else:
        ft, fl = t["leaving_ok"].format(name=name), "ok"

    if mask < 3:
        mt, ml = t["mask_critical"].format(name=name, mask=mask), "critical"
        actions.append(t["action_mask_critical"].format(name=name))
    elif mask <= 4:
        mt, ml = t["mask_silent"].format(name=name, mask=mask), "warning"
    else:
        mt, ml = t["mask_ok"].format(name=name), "ok"

    return {
        "burnout": (bt, bl), "leaving": (ft, fl), "mask": (mt, ml),
        "actions": actions,
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


def render_insights_tab(df, G, lang, salary=3000):
    t = TEXTS[lang]

    n_critical = int(((df['B_Score'] > 70) | (df['F_Score'] > 65)).sum())
    n_warning  = int(((df['B_Score'].between(50, 70)) | (df['F_Score'].between(40, 65))).sum())
    n_risk     = n_critical + n_warning

    section_header(f"🔬 {t['exec_title']}", "#2E4057")
    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 Critice" if lang == "Română" else "🔴 Critical", n_critical)
    c2.metric("🟡 Monitorizare" if lang == "Română" else "🟡 Monitoring", n_warning)
    c3.metric("🟢 OK", len(df) - n_risk)

    if n_critical > 0:
        insight_card(t["exec_critical"].format(n_critical=n_critical), "critical")
    if n_warning > 0:
        insight_card(t["exec_some_risk"].format(n_risk=n_risk), "warning")
    if n_critical == 0 and n_warning == 0:
        insight_card(t["exec_all_ok"], "ok")

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
            with st.expander(
                f"{row['Nume']} — B: {row['B_Score']:.0f} | F: {row['F_Score']:.0f} | M: {row['S_Raw']:.1f}",
                expanded=True
            ):
                insight_card(f"🔥 {ins['burnout'][0]}", ins['burnout'][1])
                insight_card(f"✈️ {ins['leaving'][0]}", ins['leaving'][1])
                insight_card(f"🤐 {ins['mask'][0]}", ins['mask'][1])

    monitor = df[
        ~((df['B_Score'] > 70) | (df['F_Score'] > 65)) &
        ((df['B_Score'] > 50) | (df['F_Score'] > 40))
    ].copy()
    monitor['_max'] = monitor[['B_Score', 'F_Score']].max(axis=1)
    monitor = monitor.sort_values('_max', ascending=False)

    if not monitor.empty:
        section_header(f"👁️ {t['sec_monitor']}", "#E67E22")
        for _, row in monitor.iterrows():
            ins = generate_individual_insights(row, t, salary)
            with st.expander(
                f"{row['Nume']} — B: {row['B_Score']:.0f} | F: {row['F_Score']:.0f} | M: {row['S_Raw']:.1f}",
                expanded=False
            ):
                insight_card(f"🔥 {ins['burnout'][0]}", ins['burnout'][1])
                insight_card(f"✈️ {ins['leaving'][0]}", ins['leaving'][1])
                insight_card(f"🤐 {ins['mask'][0]}", ins['mask'][1])

    all_actions = []
    for _, row in df.iterrows():
        all_actions.extend(generate_individual_insights(row, t, salary)["actions"])

    hubs = df[df['ONA_InDegree'] >= 3].sort_values('ONA_InDegree', ascending=False)
    if not hubs.empty:
        all_actions.append(t["action_hub"].format(name=hubs.iloc[0]['Nume']))

    for _, row in df[(df['ONA_Conn'] <= 1) & (df['S_Raw'] < 3)].iterrows():
        all_actions.append(t["action_isolated"].format(name=row['Nume']))

    if all_actions:
        section_header(f"✅ {t['action_title']}", "#1E8449")
        for action in all_actions:
            action_card(action)

    stable = df[(df['B_Score'] < 40) & (df['F_Score'] < 35) & (df['S_Raw'] >= 3.5)]
    if not stable.empty:
        section_header(f"💚 {t['sec_ok']}", "#1E8449")
        insight_card(t["pattern_ok_desc"].format(names=", ".join(stable['Nume'].tolist())), "ok")


# ════════════════════════════════════════════════════════════
# APP PRINCIPAL
# ════════════════════════════════════════════════════════════

l = UI[st.session_state.lang]
st.title(l["title"])
uploaded_file = st.file_uploader(l["upload"], type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Detectare automată header (rândul 3 dacă există titlu și subtitlu)
        if df.columns[0] not in REQUIRED_COLUMNS and len(df) > 2:
            df = pd.read_excel(uploaded_file, header=2)
        df.columns = df.columns.str.strip()

        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            st.error(f"{l['err_col']} {', '.join(missing)}")
            st.stop()

        df, G = compute_indicators(df)

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            l["b_title"], l["s_title"], l["f_title"], l["o_title"], l["i_title"]
        ])

        # ── TAB 1: BURNOUT ──────────────────────────────────
        with tab1:
            st.caption(l["b_desc"])
            st.caption(l["b_legend"])
            df_b = df.sort_values('B_Score', ascending=True)
            colors_b = [
                '#E74C3C' if s > 70 else '#F39C12' if s > 50 else '#27AE60'
                for s in df_b['B_Score']
            ]
            fig_b = go.Figure(go.Bar(
                x=df_b['B_Score'], y=df_b['Nume'],
                orientation='h',
                marker_color=colors_b,
                text=df_b['B_Score'].round(1),
                textposition='outside'
            ))
            fig_b.update_layout(
                xaxis=dict(range=[0, 115], title="Burnout Score"),
                yaxis=dict(title=""),
                height=max(400, len(df) * 26),
                margin=dict(l=10, r=40, t=20, b=20)
            )
            st.plotly_chart(fig_b, use_container_width=True)

        # ── TAB 2: POLITE MASK ──────────────────────────────
        with tab2:
            st.caption(l["s_desc"])
            fig_s = px.scatter(
                df, x="Scor_Siguranta" if "Scor_Siguranta" in df.columns else "S_Raw",
                y="S_Contr",
                size="S_Size",
                color="S_Score",
                color_continuous_scale='Oranges',
                hover_name="Nume",
                hover_data={"S_Raw": ":.2f", "B_Score": ":.1f"}
            )
            x_mid = 3.5 if "Scor_Siguranta" in df.columns else 3.0
            fig_s.add_vline(x=x_mid, line_dash="dot", line_color="gray",
                            annotation_text=l["s_q2"] + " | " + l["s_q1"],
                            annotation_position="top")
            fig_s.add_hline(y=3.0, line_dash="dot", line_color="gray",
                            annotation_text=l["s_q4"] + " | " + l["s_q3"],
                            annotation_position="right")
            fig_s.update_layout(height=500, margin=dict(l=10, r=10, t=40, b=20))
            st.plotly_chart(fig_s, use_container_width=True)

        # ── TAB 3: LEAVING RISK ─────────────────────────────
        with tab3:
            st.caption(l["f_desc"])
            st.info(l["f_cost"])
            df_f = df.sort_values('F_Score', ascending=True)
            fig_f = px.bar(
                df_f, x="F_Score", y="Nume", orientation='h',
                color="F_Score",
                color_continuous_scale=[
                    [0, "#27AE60"], [0.4, "#F39C12"], [0.65, "#E74C3C"], [1, "#922B21"]
                ],
                text=df_f['F_Score'].round(1),
            )
            fig_f.update_traces(textposition='outside')
            fig_f.update_layout(
                xaxis=dict(range=[0, 115], title="Leaving Risk Score"),
                yaxis=dict(title=""),
                height=max(400, len(df) * 26),
                margin=dict(l=10, r=40, t=20, b=20),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_f, use_container_width=True)

        # ── TAB 4: ONA ──────────────────────────────────────
        with tab4:
            st.caption(l["o_desc"])
            st.caption(l["o_legend"])
            pos = nx.spring_layout(G, k=1.2, seed=42)
            fig_ona = go.Figure()

            for e in G.edges():
                x0, y0 = pos[e[0]]; x1, y1 = pos[e[1]]
                fig_ona.add_trace(go.Scatter(
                    x=[x0, (x0+x1)/2, x1], y=[y0, (y0+y1)/2, y1],
                    mode='lines+markers',
                    marker=dict(symbol="arrow", size=8, angleref="previous",
                                color="rgba(150,150,150,0.6)"),
                    line=dict(width=1, color='rgba(150,150,150,0.4)'),
                    hoverinfo='none', showlegend=False
                ))

            nx_nodes = list(G.nodes())
            b_vals = [G.nodes[n].get('B', 0) for n in nx_nodes]
            sizes  = [(G.in_degree(n) * 12) + 14 for n in nx_nodes]

            fig_ona.add_trace(go.Scatter(
                x=[pos[n][0] for n in nx_nodes],
                y=[pos[n][1] for n in nx_nodes],
                mode='markers+text',
                text=nx_nodes,
                textposition="bottom center",
                marker=dict(
                    size=sizes,
                    color=b_vals,
                    colorscale='Reds',
                    showscale=True,
                    colorbar=dict(title="Burnout"),
                    line=dict(width=1, color='white')
                ),
                hovertemplate="<b>%{text}</b><br>Burnout: %{marker.color:.0f}<extra></extra>",
                showlegend=False
            ))

            fig_ona.update_layout(
                showlegend=False,
                height=600,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig_ona, use_container_width=True)

        # ── TAB 5: INSIGHTS ─────────────────────────────────
        with tab5:
            render_insights_tab(df, G, st.session_state.lang, salary)

    except Exception as e:
        st.error(f"Eroare / Error: {e}")
        st.exception(e)
