import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Logically Human | Audit", layout="wide")

# --- GESTIONARE LIMBĂ ---
if 'lang' not in st.session_state:
    st.session_state.lang = "Română"

def change_lang():
    st.session_state.lang = st.session_state.lang_select

st.sidebar.selectbox("Limbă / Language", ["Română", "English"], key="lang_select", on_change=change_lang)

texts = {
    "Română": {
        "title": "🧠 Logically Human | Diagnostic Strategic",
        "upload": "Încarcă Excel-ul cu cele 9 coloane standard",
        "btn": "Generează Raport de Risc",
        "b_title": "🔥 Risc Burnout",
        "s_title": "🤐 Masca Politicoasă (Silence)",
        "f_title": "✈️ Risc Plecare (Flight)",
        "insight_title": "💡 Actionable Insights (Piloni)",
        "b_desc": "Epuizare detectată. Recuperarea este sub nivelul de efort.",
        "s_desc": "Disonanță: Angajatul spune că e bine, dar nu mai contribuie/nu mai raportează erori.",
        "f_desc": "Plafonare detectată. Lipsă de creștere și deconectare de viitor.",
        "safe": "Stabilitate / Sănătate"
    },
    "English": {
        "title": "🧠 Logically Human | Strategic Diagnostic",
        "upload": "Upload Excel with the 9 standard columns",
        "btn": "Generate Risk Report",
        "b_title": "🔥 Burnout Risk",
        "s_title": "🤐 Polite Mask (Silence)",
        "f_title": "✈️ Flight Risk",
        "insight_title": "💡 Actionable Insights (Pillars)",
        "b_desc": "Exhaustion detected. Recovery is below effort level.",
        "s_desc": "Dissonance: Employee says they're fine, but stops contributing/reporting errors.",
        "f_desc": "Stagnation detected. Lack of growth and future disconnect.",
        "safe": "Stability / Healthy"
    }
}

l = texts[st.session_state.lang]

st.title(l["title"])

# --- UPLOAD ---
uploaded_file = st.file_uploader(l["upload"], type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    if st.button(l["btn"]):
        # --- LOGICA DE CALCUL ---
        df['Burnout_Flag'] = (df['Ore_Saptamana'] > 45) & (df['Zile_Concediu'] < 5) & (df['Scor_Energie'] < 3)
        df['Silence_Flag'] = (df['Scor_Siguranta'] >= 4) & ((df['Idei_Noi'] <= 2) | (df['Erori_Asumate'] <= 2))
        df['Flight_Flag'] = (df['Vechime_Rol'] > 18) & (df['Ultima_Marire'] > 12) & (df['Scor_Evolutie'] < 3)
        
        def get_status(row):
            if row['Burnout_Flag']: return l["b_title"]
            if row['Silence_Flag']: return l["s_title"]
            if row['Flight_Flag']: return l["f_title"]
            return l["safe"]
        
        df['Status'] = df.apply(get_status, axis=1)
        
        col1, col2, col3 = st.columns(3)
        col1.metric(l["b_title"], df['Burnout_Flag'].sum())
        col2.metric(l["s_title"], df['Silence_Flag'].sum())
        col3.metric(l["f_title"], df['Flight_Flag'].sum())
        
        st.divider()
        c1, c2 = st.columns([1, 1])
        with c1:
            fig = px.pie(df, names='Status', hole=0.4, color='Status',
                         color_discrete_map={l["b_title"]: "#ff4b4b", l["s_title"]: "#ffa421", l["f_title"]: "#3d3d3d", l["safe"]: "#28a745"})
            st.plotly_chart(fig, use_container_width=True)
            
        with c2:
            st.subheader(l["insight_title"])
            if df['Burnout_Flag'].any(): st.warning(f"**{l['b_title']}:** {l['b_desc']}")
            if df['Silence_Flag'].any(): 
                st.error(f"**{l['s_title']}:** {l['s_desc']}")
                st.info("💡 Sfat: Organizează o sesiune de 'Greșeala Săptămânii'. Sparge gheața.")
            if df['Flight_Flag'].any(): st.warning(f"**{l['f_title']}:** {l['f_desc']}")

        st.divider()
        with st.expander("Vezi tabelul procesat detaliat"):
            st.dataframe(df)
