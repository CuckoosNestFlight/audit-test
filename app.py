# ============================================================
# TEAMSCIENTIST — INSIGHTS ENGINE
# Versiune: 1.0 | Martie 2026
# ============================================================
# Modul independent. Importează în app.py astfel:
#   from insights_engine import render_insights_tab
#   with tab5:
#       render_insights_tab(df, G, lang)
# ============================================================

import streamlit as st
import pandas as pd

# ── TEXTE BILINGVE ───────────────────────────────────────────

TEXTS = {
    "Română": {
        # Rezumat executiv
        "exec_title": "Rezumat executiv",
        "exec_all_ok": "Echipa funcționează în parametri normali. Niciun risc critic identificat în acest ciclu de audit.",
        "exec_some_risk": "Au fost identificate {n_risk} situații care necesită atenție în următoarele 30 de zile.",
        "exec_critical": "{n_critical} angajat(ți) se află în zonă critică și necesită intervenție imediată.",

        # Secțiuni
        "sec_urgent": "Urgențe — intervenție imediată",
        "sec_monitor": "Monitorizare activă — 30 de zile",
        "sec_patterns": "Tipare la nivel de echipă",
        "sec_ok": "Ce funcționează bine",
        "sec_actions": "Acțiuni recomandate",

        # Tipare echipă
        "pattern_cultural_silence": "Problemă culturală de siguranță psihologică",
        "pattern_cultural_silence_desc": (
            "{pct}% din echipă are scor Polite Mask sub 3. "
            "Aceasta indică o problemă sistemică de cultură, nu individuală. "
            "Oamenii tac pentru că nu se simt în siguranță să greșească sau să propună, "
            "indiferent de cine sunt. Intervenția necesară este la nivel de echipă, nu per angajat."
        ),
        "pattern_hub_risk": "Nod central supraîncărcat — risc sistemic",
        "pattern_hub_risk_desc": (
            "{name} este consultat de {n_conn} colegi și are simultan burnout ridicat ({b:.0f}) "
            "și risc de plecare ridicat ({f:.0f}). "
            "Dacă această persoană pleacă sau se prăbușește, "
            "fluxul informal de cunoaștere al echipei se întrerupe brusc. "
            "Acesta este cel mai costisitor scenariu de risc din audit."
        ),
        "pattern_isolation": "Izolare totală — deconectare dublă",
        "pattern_isolation_desc": (
            "{names} prezintă izolare în rețea (nicio conexiune de sfat) "
            "combinată cu mască politicoasă (scor siguranță < 3). "
            "Aceștia nu cer ajutor și nu contribuie — un semnal timpuriu "
            "de dezangajare silențioasă sau de plecare iminentă."
        ),
        "pattern_silent_stars": "Performeri tăcuți — potențial neexploatat",
        "pattern_silent_stars_desc": (
            "{names} au rezultate bune (burnout OK, risc plecare redus) "
            "dar scor Polite Mask scăzut. Contribuie mai puțin decât ar putea. "
            "O conversație directă despre ce îi oprește poate debloca "
            "contribuții valoroase fără niciun cost suplimentar."
        ),
        "pattern_ok": "Nucleu stabil",
        "pattern_ok_desc": (
            "{names} prezintă toți indicatorii în parametri normali. "
            "Aceștia reprezintă fundația stabilă a echipei. "
            "Menținerea condițiilor lor actuale este la fel de importantă "
            "ca rezolvarea problemelor identificate."
        ),

        # Template-uri individuale — Burnout
        "burnout_critical": (
            "{name} se află în burnout avansat (scor {b:.0f}/100). "
            "Lucrează {ore}h/săptămână, are {concediu} zi(e) concediu efectuate "
            "și un nivel de energie de {energie}/5. "
            "Fără intervenție în următoarele 1–2 săptămâni, "
            "riscul de colaps sau demisie spontană este ridicat."
        ),
        "burnout_warning": (
            "{name} prezintă semne timpurii de burnout (scor {b:.0f}/100). "
            "Nivelul de energie ({energie}/5) și orele lucrate ({ore}h/săpt.) "
            "indică o acumulare de oboseală care necesită monitorizare."
        ),
        "burnout_ok": (
            "{name} funcționează în parametri normali din perspectiva energiei și efortului."
        ),

        # Template-uri individuale — Leaving Risk
        "leaving_critical": (
            "{name} are un risc de plecare ridicat (scor {f:.0f}/100). "
            "Ultima mărire salarială a fost acum {marire} luni, "
            "energia este la {energie}/5, "
            "și este consultat(ă) de {conn} colegi — "
            "ceea ce îl/o face vizibil(ă) și atractiv(ă) pe piața muncii. "
            "Costul estimat de înlocuire: {cost}."
        ),
        "leaving_monitor": (
            "{name} prezintă factori de risc de plecare moderați (scor {f:.0f}/100). "
            "Stagnarea financiară ({marire} luni de la ultima mărire) "
            "combinată cu presiunea actuală merită o conversație de carieră în 30 de zile."
        ),
        "leaving_ok": (
            "{name} prezintă stabilitate din perspectiva riscului de plecare."
        ),

        # Template-uri individuale — Polite Mask
        "mask_critical": (
            "{name} tace activ (Polite Mask {mask:.1f}/5). "
            "Nu raportează erori și nu propune idei noi — "
            "un semnal că se simte nesigur(ă) în echipă sau în relație cu managerul. "
            "O conversație de siguranță psihologică, nu de performanță, este prioritară."
        ),
        "mask_silent": (
            "{name} are potențial neexploatat (Polite Mask {mask:.1f}/5). "
            "Există margine de contribuție mai mare dacă mediul devine mai permisiv cu erorile."
        ),
        "mask_ok": (
            "{name} contribuie autentic și se simte în siguranță să greșească și să propună."
        ),

        # Acțiuni recomandate
        "action_title": "Ce faci concret — această săptămână",
        "action_burnout_critical": "Programează o întâlnire 1:1 cu {name} în 48h. Nu evaluare — ascultare. Întreabă ce ar face situația mai sustenabilă.",
        "action_leaving_critical": "Inițiază o conversație de carieră cu {name}. Verifică dacă există spațiu pentru o ajustare salarială sau de rol înainte ca decizia să fie luată.",
        "action_mask_critical": "Cu {name}: înlocuiește feedback-ul de grup cu conversații 1:1. Creează un moment explicit în care eroarea este normalizată public.",
        "action_hub": "Distribuie din responsabilitățile informale ale lui {name}. Identifică cine ar putea prelua 20% din cererile de sfat.",
        "action_isolated": "Include {name} explicit în cel puțin o decizie de echipă această săptămână. Izolarea se adâncește în absența invitațiilor directe.",

        # Cost înlocuire
        "replacement_cost": "~{min}–{max} (6–12 luni salariu + recrutare)",
        "replacement_note": "Estimare bazată pe salariu mediu lunar de {sal} × factor înlocuire 6–12.",

        # Mesaje positive
        "no_critical": "Nicio urgență critică identificată în acest ciclu.",
        "stable_team": "Echipa prezintă o stabilitate generală bună.",

        # Sidebar
        "salary_input": "Salariu mediu lunar estimat (€)",
        "salary_help": "Folosit pentru estimarea costului de înlocuire în Leaving Risk.",
    },

    "English": {
        "exec_title": "Executive summary",
        "exec_all_ok": "The team is operating within normal parameters. No critical risks identified in this audit cycle.",
        "exec_some_risk": "{n_risk} situation(s) require attention in the next 30 days.",
        "exec_critical": "{n_critical} employee(s) are in the critical zone and require immediate action.",

        "sec_urgent": "Urgent — immediate action required",
        "sec_monitor": "Active monitoring — 30 days",
        "sec_patterns": "Team-level patterns",
        "sec_ok": "What's working well",
        "sec_actions": "Recommended actions",

        "pattern_cultural_silence": "Cultural psychological safety issue",
        "pattern_cultural_silence_desc": (
            "{pct}% of the team scores below 3 on the Polite Mask indicator. "
            "This signals a systemic cultural issue, not an individual one. "
            "People are staying silent because it doesn't feel safe to make mistakes or propose ideas — "
            "regardless of who they are. The intervention must happen at team level, not person by person."
        ),
        "pattern_hub_risk": "Overloaded central hub — systemic risk",
        "pattern_hub_risk_desc": (
            "{name} is consulted by {n_conn} colleagues and simultaneously shows high burnout ({b:.0f}) "
            "and high leaving risk ({f:.0f}). "
            "If this person leaves or collapses, "
            "the team's informal knowledge flow breaks down abruptly. "
            "This is the most costly risk scenario in this audit."
        ),
        "pattern_isolation": "Total disconnection — dual isolation",
        "pattern_isolation_desc": (
            "{names} show network isolation (no advice connections) "
            "combined with a polite mask (safety score < 3). "
            "They don't ask for help and don't contribute — an early signal "
            "of silent disengagement or imminent departure."
        ),
        "pattern_silent_stars": "Silent performers — untapped potential",
        "pattern_silent_stars_desc": (
            "{names} perform well (burnout OK, low leaving risk) "
            "but score low on Polite Mask. They contribute less than they could. "
            "A direct conversation about what holds them back may unlock "
            "valuable contributions at no additional cost."
        ),
        "pattern_ok": "Stable core",
        "pattern_ok_desc": (
            "{names} show all indicators within normal parameters. "
            "They represent the stable foundation of the team. "
            "Maintaining their current conditions is just as important "
            "as solving the identified problems."
        ),

        "burnout_critical": (
            "{name} is in advanced burnout (score {b:.0f}/100). "
            "Working {ore}h/week, with {concediu} vacation day(s) taken "
            "and an energy level of {energie}/5. "
            "Without intervention in the next 1–2 weeks, "
            "the risk of collapse or sudden resignation is high."
        ),
        "burnout_warning": (
            "{name} shows early burnout signs (score {b:.0f}/100). "
            "Energy level ({energie}/5) and hours worked ({ore}h/week) "
            "indicate accumulating fatigue that needs monitoring."
        ),
        "burnout_ok": (
            "{name} is operating within normal parameters for energy and effort."
        ),

        "leaving_critical": (
            "{name} has a high leaving risk (score {f:.0f}/100). "
            "Last salary raise was {marire} months ago, "
            "energy is at {energie}/5, "
            "and {conn} colleagues consult them — "
            "making them visible and attractive on the job market. "
            "Estimated replacement cost: {cost}."
        ),
        "leaving_monitor": (
            "{name} shows moderate leaving risk factors (score {f:.0f}/100). "
            "Financial stagnation ({marire} months since last raise) "
            "combined with current pressure warrants a career conversation within 30 days."
        ),
        "leaving_ok": (
            "{name} is stable from a leaving risk perspective."
        ),

        "mask_critical": (
            "{name} is actively silent (Polite Mask {mask:.1f}/5). "
            "They don't report errors and don't propose new ideas — "
            "a signal they feel unsafe within the team or with their manager. "
            "A psychological safety conversation — not a performance review — is the priority."
        ),
        "mask_silent": (
            "{name} has untapped potential (Polite Mask {mask:.1f}/5). "
            "There is room for greater contribution if the environment becomes more permissive with mistakes."
        ),
        "mask_ok": (
            "{name} contributes authentically and feels safe to make mistakes and propose ideas."
        ),

        "action_title": "What you do concretely — this week",
        "action_burnout_critical": "Schedule a 1:1 with {name} within 48h. Not an evaluation — listening. Ask what would make the situation more sustainable.",
        "action_leaving_critical": "Initiate a career conversation with {name}. Check if there's room for a salary or role adjustment before the decision is made.",
        "action_mask_critical": "With {name}: replace group feedback with 1:1 conversations. Create an explicit moment where making mistakes is publicly normalized.",
        "action_hub": "Distribute some of {name}'s informal responsibilities. Identify who could take over 20% of the advice requests.",
        "action_isolated": "Include {name} explicitly in at least one team decision this week. Isolation deepens in the absence of direct invitations.",

        "replacement_cost": "~{min}–{max} (6–12 months salary + recruitment)",
        "replacement_note": "Estimate based on avg monthly salary of {sal} × replacement factor 6–12.",

        "no_critical": "No critical urgencies identified in this cycle.",
        "stable_team": "The team shows overall good stability.",

        "salary_input": "Estimated avg monthly salary (€)",
        "salary_help": "Used to estimate replacement cost in Leaving Risk.",
    }
}


# ── HELPERS ──────────────────────────────────────────────────

def fmt_cost(salary_monthly: int, t: dict) -> str:
    """Estimează costul de înlocuire pe baza salariului lunar."""
    low  = salary_monthly * 6
    high = salary_monthly * 12
    return t["replacement_cost"].format(
        min=f"€{low:,.0f}",
        max=f"€{high:,.0f}"
    )


def section_header(title: str, color: str = "#1C2833"):
    st.markdown(
        f"<div style='margin:24px 0 10px;padding:8px 14px;"
        f"background:{color}10;border-left:3px solid {color};"
        f"border-radius:0 6px 6px 0;font-weight:600;font-size:15px'>"
        f"{title}</div>",
        unsafe_allow_html=True
    )


def insight_card(text: str, level: str = "info"):
    """level: critical | warning | ok | info"""
    colors = {
        "critical": ("#FDEDEC", "#C0392B", "⚠"),
        "warning":  ("#FEF9E7", "#E67E22", "◉"),
        "ok":       ("#EAFAF1", "#1E8449", "✓"),
        "info":     ("#EBF5FB", "#2471A3", "→"),
    }
    bg, border, icon = colors.get(level, colors["info"])
    st.markdown(
        f"<div style='background:{bg};border-left:3px solid {border};"
        f"border-radius:0 8px 8px 0;padding:12px 16px;margin:6px 0;"
        f"font-size:14px;line-height:1.6'>"
        f"<span style='color:{border};margin-right:8px'>{icon}</span>{text}</div>",
        unsafe_allow_html=True
    )


def action_card(text: str):
    st.markdown(
        f"<div style='background:#F4F6F7;border:1px solid #D5D8DC;"
        f"border-radius:8px;padding:12px 16px;margin:4px 0;"
        f"font-size:13px;line-height:1.6'>"
        f"<span style='color:#E67E22;margin-right:8px;font-weight:600'>→</span>{text}</div>",
        unsafe_allow_html=True
    )


# ── MOTORUL DE INSIGHTS ───────────────────────────────────────

def generate_individual_insights(row: pd.Series, t: dict, salary: int) -> dict:
    """
    Generează textele psihologice pentru un angajat individual.
    Returnează dict cu cheile: burnout, leaving, mask, actions
    """
    name    = str(row['Nume'])
    b       = float(row['B_Score'])
    f       = float(row['F_Score'])
    mask    = float(row['S_Raw'])
    ore     = int(row.get('Ore_Saptamana', 40))
    energie = int(row.get('Scor_Energie', 3))
    concediu= int(row.get('Zile_Concediu', 0))
    marire  = int(row.get('Ultima_Marire', 24))
    conn    = int(row.get('ONA_InDegree', 0))

    cost = fmt_cost(salary, t) if salary > 0 else "N/A (adaugă salariu mediu în sidebar)"
    actions = []

    # Burnout text
    if b > 70:
        burnout_text  = t["burnout_critical"].format(
            name=name, b=b, ore=ore, concediu=concediu, energie=energie)
        burnout_level = "critical"
        actions.append(t["action_burnout_critical"].format(name=name))
    elif b > 50:
        burnout_text  = t["burnout_warning"].format(
            name=name, b=b, ore=ore, energie=energie)
        burnout_level = "warning"
    else:
        burnout_text  = t["burnout_ok"].format(name=name)
        burnout_level = "ok"

    # Leaving text
    if f > 65:
        leaving_text  = t["leaving_critical"].format(
            name=name, f=f, marire=marire, energie=energie, conn=conn, cost=cost)
        leaving_level = "critical"
        actions.append(t["action_leaving_critical"].format(name=name))
    elif f > 40:
        leaving_text  = t["leaving_monitor"].format(
            name=name, f=f, marire=marire)
        leaving_level = "warning"
    else:
        leaving_text  = t["leaving_ok"].format(name=name)
        leaving_level = "ok"

    # Mask text
    if mask < 3:
        mask_text  = t["mask_critical"].format(name=name, mask=mask)
        mask_level = "critical"
        actions.append(t["action_mask_critical"].format(name=name))
    elif mask <= 4:
        mask_text  = t["mask_silent"].format(name=name, mask=mask)
        mask_level = "warning"
    else:
        mask_text  = t["mask_ok"].format(name=name)
        mask_level = "ok"

    return {
        "burnout":  (burnout_text,  burnout_level),
        "leaving":  (leaving_text,  leaving_level),
        "mask":     (mask_text,     mask_level),
        "actions":  actions,
        "is_critical": b > 70 or f > 65,
        "is_warning":  (50 < b <= 70) or (40 < f <= 65),
    }


def detect_team_patterns(df: pd.DataFrame, G, t: dict) -> list:
    """
    Detectează tipare la nivel de echipă.
    Returnează o listă de dict-uri {title, text, level}
    """
    patterns = []
    n = len(df)

    # 1. Cultural silence
    silent_pct = (df['S_Raw'] < 3).sum() / n * 100
    if silent_pct >= 50:
        patterns.append({
            "title": t["pattern_cultural_silence"],
            "text":  t["pattern_cultural_silence_desc"].format(pct=int(silent_pct)),
            "level": "critical"
        })
    elif silent_pct >= 30:
        patterns.append({
            "title": t["pattern_cultural_silence"],
            "text":  t["pattern_cultural_silence_desc"].format(pct=int(silent_pct)),
            "level": "warning"
        })

    # 2. Hub overload
    if G is not None:
        nodes = list(G.nodes())
        hub_candidates = df[df['ONA_InDegree'] >= 3].copy()
        for _, row in hub_candidates.iterrows():
            if row['B_Score'] > 60 and row['F_Score'] > 50:
                patterns.append({
                    "title": t["pattern_hub_risk"],
                    "text":  t["pattern_hub_risk_desc"].format(
                        name=row['Nume'],
                        n_conn=int(row['ONA_InDegree']),
                        b=row['B_Score'],
                        f=row['F_Score']
                    ),
                    "level": "critical"
                })

    # 3. Dual isolation
    isolated = df[(df['ONA_Conn'] <= 1) & (df['S_Raw'] < 3)]
    if not isolated.empty:
        names = ", ".join(isolated['Nume'].tolist())
        patterns.append({
            "title": t["pattern_isolation"],
            "text":  t["pattern_isolation_desc"].format(names=names),
            "level": "warning"
        })

    # 4. Silent stars
    silent_stars = df[(df['B_Score'] < 50) & (df['F_Score'] < 40) & (df['S_Raw'] < 3)]
    if not silent_stars.empty:
        names = ", ".join(silent_stars['Nume'].tolist())
        patterns.append({
            "title": t["pattern_silent_stars"],
            "text":  t["pattern_silent_stars_desc"].format(names=names),
            "level": "info"
        })

    # 5. Stable core
    stable = df[(df['B_Score'] < 40) & (df['F_Score'] < 35) & (df['S_Raw'] >= 3.5)]
    if not stable.empty:
        names = ", ".join(stable['Nume'].tolist())
        patterns.append({
            "title": t["pattern_ok"],
            "text":  t["pattern_ok_desc"].format(names=names),
            "level": "ok"
        })

    return patterns


# ── RENDER PRINCIPAL ─────────────────────────────────────────

def render_insights_tab(df: pd.DataFrame, G, lang: str, salary: int = 3000):
    """
    Funcția principală. Apeleaz-o în tab5 din app.py.

    Parametri:
        df      — DataFrame cu scorurile calculate (după compute_indicators)
        G       — graful NetworkX generat de compute_indicators
        lang    — "Română" sau "English"
        salary  — salariu mediu lunar estimat al echipei (€), default 3000
    """
    t = TEXTS[lang]

    # ── REZUMAT EXECUTIV ──────────────────────────────────────
    n_critical = int(((df['B_Score'] > 70) | (df['F_Score'] > 65)).sum())
    n_warning  = int(((df['B_Score'].between(50, 70)) | (df['F_Score'].between(40, 65))).sum())
    n_risk     = n_critical + n_warning

    section_header(f"🔬 {t['exec_title']}", "#2E4057")

    col1, col2, col3 = st.columns(3)
    col1.metric("🔴 Critice", n_critical)
    col2.metric("🟡 Monitorizare", n_warning)
    col3.metric("🟢 OK", len(df) - n_risk)

    if n_critical > 0:
        insight_card(t["exec_critical"].format(n_critical=n_critical), "critical")
    if n_warning > 0:
        insight_card(t["exec_some_risk"].format(n_risk=n_risk), "warning")
    if n_critical == 0 and n_warning == 0:
        insight_card(t["exec_all_ok"], "ok")

    # ── TIPARE ECHIPĂ ─────────────────────────────────────────
    patterns = detect_team_patterns(df, G, t)
    if patterns:
        section_header(f"🕸️ {t['sec_patterns']}", "#8E44AD")
        for p in patterns:
            with st.expander(p["title"], expanded=(p["level"] == "critical")):
                insight_card(p["text"], p["level"])

    # ── URGENȚE INDIVIDUALE ───────────────────────────────────
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
                bt, bl = ins["burnout"]
                ft, fl = ins["leaving"]
                mt, ml = ins["mask"]
                insight_card(f"🔥 {bt}", bl)
                insight_card(f"✈️ {ft}", fl)
                insight_card(f"🤐 {mt}", ml)

    # ── MONITORIZARE ─────────────────────────────────────────
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
                bt, bl = ins["burnout"]
                ft, fl = ins["leaving"]
                mt, ml = ins["mask"]
                insight_card(f"🔥 {bt}", bl)
                insight_card(f"✈️ {ft}", fl)
                insight_card(f"🤐 {mt}", ml)

    # ── ACȚIUNI RECOMANDATE ───────────────────────────────────
    all_actions = []
    for _, row in df.iterrows():
        ins = generate_individual_insights(row, t, salary)
        all_actions.extend(ins["actions"])

    # Hub action
    hubs = df[df['ONA_InDegree'] >= 3].sort_values('ONA_InDegree', ascending=False)
    if not hubs.empty:
        all_actions.append(t["action_hub"].format(name=hubs.iloc[0]['Nume']))

    # Isolated action
    isolated = df[(df['ONA_Conn'] <= 1) & (df['S_Raw'] < 3)]
    for _, row in isolated.iterrows():
        all_actions.append(t["action_isolated"].format(name=row['Nume']))

    if all_actions:
        section_header(f"✅ {t['action_title']}", "#1E8449")
        for action in all_actions:
            action_card(action)

    # ── CE FUNCȚIONEAZĂ BINE ──────────────────────────────────
    stable = df[(df['B_Score'] < 40) & (df['F_Score'] < 35) & (df['S_Raw'] >= 3.5)]
    if not stable.empty:
        section_header(f"💚 {t['sec_ok']}", "#1E8449")
        names = ", ".join(stable['Nume'].tolist())
        insight_card(
            t["pattern_ok_desc"].format(names=names),
            "ok"
        )
