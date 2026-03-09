import streamlit as st
import pandas as pd

# Setări pagină
st.set_page_config(page_title="Logically Human Audit", layout="wide")

st.title("🧠 Logically Human | Team Diagnostic")
st.sidebar.header("Configurare")
limba = st.sidebar.selectbox("Limbă", ["Română", "English"])

# Mesaje în funcție de limbă
text = {
    "Română": {"msg": "Încarcă datele echipei", "btn": "Analizează", "res": "Rezultate Audit"},
    "English": {"msg": "Upload team data", "btn": "Analyze", "res": "Audit Results"}
}

# 1. Upload Fișier
file = st.file_uploader(text[limba]["msg"], type=["xlsx"])

if file:
    df = pd.read_excel(file)
    
    if st.button(text[limba]["btn"]):
        st.subheader(text[limba]["res"])
        
        # 2. Calcule Logice
        # Identificăm persoanele cu risc
        burnout_risk = df[(df['Ore_Saptamana'] > 45) & (df['Zile_Concediu_Luate'] < 5)]
        flight_risk = df[(df['Vechime_Rol_Luni'] > 18) & (df['Scor_Crestere'] < 3)]
        
        # 3. Afișare Dashboard
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Risc Burnout (Cazuri)", len(burnout_risk))
            if len(burnout_risk) > 0:
                st.error("⚠️ Echipa se 'arde'. Ai oameni care trag tare fără recuperare.")
                st.write(burnout_risk[['ID_Angajat', 'Ore_Saptamana']])

        with col2:
            st.metric("Risc Plecare (Cazuri)", len(flight_risk))
            if len(flight_risk) > 0:
                st.warning("⚠️ Atenție la plafonare. Oamenii aceștia nu mai văd viitorul aici.")
                st.write(flight_risk[['ID_Angajat', 'Vechime_Rol_Luni']])

        # 4. Pastila de Psihologie
        st.divider()
        st.info("**Reflecție Logically Human:** Datele arată *ce* se întâmplă. Întreabă-te *de ce* ai permis ca ID-ul cel mai ocupat să nu aibă nicio zi de concediu? Este despre performanță sau despre frica lui/ei de a nu fi indispensabil?")
