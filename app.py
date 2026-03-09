import streamlit as st
import pandas as pd
import plotly.express as px # Librarie pentru grafice "sexy"

st.set_page_config(page_title="Logically Human Audit", layout="wide")

# --- LOGICA DE LIMBĂ ---
if 'lang' not in st.session_state:
    st.session_state.lang = "Română"

def change_lang():
    if st.session_state.lang_select == "English":
        st.session_state.lang = "English"
    else:
        st.session_state.lang = "Română"

st.sidebar.selectbox("Limbă / Language", ["Română", "English"], key="lang_select", on_change=change_lang)

texts = {
    "Română": {
        "t": "🧠 Logically Human | Diagnostic Echipă",
        "up": "Încarcă Excel-ul (Anonim)",
        "ana": "Analizează Datele",
        "brn": "Risc Burnout",
        "flg": "Risc Plecare",
        "safe": "Zonă Sigură",
        "desc": "Distribuția Riscurilor în Echipă"
    },
    "English": {
        "t": "🧠 Logically Human | Team Diagnostic",
        "up": "Upload Excel (Anonymous)",
        "ana": "Analyze Data",
        "brn": "Burnout Risk",
        "flg": "Flight Risk",
        "safe": "Safe Zone",
        "desc": "Team Risk Distribution"
    }
}

l = texts[st.session_state.lang]

st.title(l["t"])

# --- GESTIONARE DATE (SESSION STATE) ---
if 'df' not in st.session_state:
    st.session_state.df = None

uploaded_file = st.file_uploader(l["up"], type=["xlsx"])

if uploaded_file:
    st.session_state.df = pd.read_excel(uploaded_file)

if st.session_state.df is not None:
    df = st.session_state.df
    
    if st.button(l["ana"]):
        # Calcule
        df['Burnout'] = (df['Ore_Saptamana'] > 45) & (df['Zile_Concediu_Luate'] < 5)
        df['Flight'] = (df['Vechime_Rol_Luni'] > 18) & (df['Scor_Crestere'] < 3)
        
        # Clasificare pentru grafic
        def classify(row):
            if row['Burnout']: return l["brn"]
            if row['Flight']: return l["flg"]
            return l["safe"]
        
        df['Status'] = df.apply(classify, axis=1)
        
        # --- DASHBOARD ---
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write(f"### {l['desc']}")
            fig = px.pie(df, names='Status', color='Status', 
                         color_discrete_map={l["brn"]:'#ff4b4b', l["flg"]:'#ffa421', l["safe"]:'#28a745'})
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.metric(l["brn"], len(df[df['Burnout']]))
            st.metric(l["flg"], len(df[df['Flight']]))
            
        st.divider()
        st.write("### 🔑 Actionable Insights")
        st.info("Sfat: Când un membru al echipei apare în zona portocalie (Risc Plecare), nu oferi bani imediat. Oferă-i vizibilitate asupra impactului muncii lui.")
