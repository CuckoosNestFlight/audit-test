import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Logically Human | Premium Audit", layout="wide")

# --- UI & Branding ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🧠 Logically Human | Diagnostic Strategic v1.5")
st.caption("Analiză predictivă bazată pe psihologie computațională și corelații de context.")

# --- Upload ---
uploaded_file = st.file_uploader("Încarcă fișierul de date (Excel)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # --- MOTORUL DE CALCUL (LOGICALLY HUMAN ENGINE) ---
    # 1. Calcul Burnout Score (0-100)
    df['B_Score'] = (df['Ore_Saptamana']/40 * 30) + ((6 - df['Scor_Energie']) * 10)
    df.loc[df['Mod_Lucru'].isin([1, 3]), 'B_Score'] *= 1.15 # Penalizare Office/Remote
    df.loc[df['Presiune_Externa'] > 7, 'B_Score'] *= 1.20 # Penalizare Presiune Externa
    
    # 2. Calcul Silence (Dissonance)
    df['S_Dissonance'] = df['Scor_Siguranta'] - ((df['Idei_Noi'] + df['Erori_Asumate']) / 2)
    
    # 3. Calcul Flight Risk
    df['F_Score'] = (df['Vechime_Rol'] * 2) + (df['Ultima_Marire'] * 1.5) + ((6 - df['Scor_Evolutie']) * 10)

    # --- DASHBOARD ---
    tab1, tab2, tab3, tab4 = st.tabs(["🔥 Burnout", "🤐 Silence", "✈️ Flight Risk", "🧩 Cross-Pillar Insights"])

    with tab1:
        st.subheader("Distribuția Riscului de Burnout")
        fig1 = px.histogram(df, x="B_Score", nbins=10, color_discrete_sequence=['#ff4b4b'], 
                           labels={'B_Score': 'Scor Burnout (0-100)'})
        st.plotly_chart(fig1, use_container_width=True)
        st.info("Analiză: Scorurile peste 70 indică risc iminent de colaps de performanță.")

    with tab2:
        st.subheader("Matricea Siguranță vs. Contribuție")
        fig2 = px.scatter(df, x="Scor_Siguranta", y="Idei_Noi", size="S_Dissonance", 
                         color="S_Dissonance", color_continuous_scale='Oranges',
                         hover_name="Nume" if "Nume" in df.columns else None)
        st.plotly_chart(fig2, use_container_width=True)
        st.write("Bulele mari și deschise la culoare reprezintă 'Masca Politicoasă'.")

    with tab3:
        st.subheader("Flight Risk vs. Evoluție Percepută")
        fig3 = px.bar(df, x="Nume" if "Nume" in df.columns else df.index, y="F_Score",
                     color="Scor_Evolutie", color_continuous_scale='Greys')
        st.plotly_chart(fig3, use_container_width=True)

    with tab4:
        st.subheader("🧩 Diagnostice de Context (Interpretări Expert)")
        
        # Intersectii Logice
        martyrs = df[(df['B_Score'] > 70) & (df['Presiune_Externa'] > 7)]
        talent_drain = df[(df['F_Score'] > 60) & (df['Idei_Noi'] > 7)]
        remote_mask = df[(df['Mod_Lucru'] == 3) & (df['S_Dissonance'] > 2)]

        c1, c2, c3 = st.columns(3)
        with c1:
            st.error(f"**Martiri Invizibili: {len(martyrs)}**")
            st.caption("Oameni cu burnout sever potențat de viața personală. Necesită flexibilitate imediată.")
        with c2:
            st.warning(f"**Talent Drain: {len(talent_drain)}**")
            st.caption("Cei mai creativi oameni sunt gata să plece. Risc major de pierdere de know-how.")
        with c3:
            st.info(f"**Izolare Digitală: {len(remote_mask)}**")
            st.caption("Angajați remote care au încetat să mai fie sinceri. Necesită reconectare 1-la-1.")

    # --- Disclaimer & CTA ---
    st.divider()
    st.warning("⚠️ **NOTĂ METODOLOGICĂ:** Aceste rezultate sunt interpretări algoritmice bazate pe datele furnizate. Ele reprezintă indicatori de probabilitate și nu sentințe. Este necesară validarea acestor concluzii prin dialog direct și analiză calitativă înainte de a lua decizii de management.")
    
    st.markdown("""
        ### 🚀 Vrei să treci la nivelul următor?
        Putem corela aceste date cu obiectivele tale de business pentru un plan de intervenție personalizat.
        - **Contact:** [Numele Tau / Email]
        - **Servicii:** Workshop-uri de Data-Sensemaking, Coaching pentru Lideri, Strategii de Retenție.
    """)
