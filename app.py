import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Logically Human | Premium Audit", layout="wide")

# --- CSS pentru un look mai premium ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧠 Logically Human | Diagnostic Strategic v1.5")

# --- Verificare Coloane Necesare ---
REQUIRED_COLUMNS = [
    'Nume', 'Ore_Saptamana', 'Zile_Concediu', 'Idei_Noi', 'Erori_Asumate', 
    'Vechime_Rol', 'Ultima_Marire', 'Scor_Energie', 'Scor_Siguranta', 
    'Scor_Evolutie', 'Mod_Lucru', 'Presiune_Externa'
]

uploaded_file = st.file_uploader("Încarcă fișierul Excel actualizat", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        
        # Verificăm dacă toate coloanele există
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        
        if missing:
            st.error(f"❌ Fișierul tău nu conține coloanele: {', '.join(missing)}")
            st.info("Asigură-te că folosești tabelul nou cu 12 coloane.")
        else:
            # --- CALCUL ---
            # 1. Burnout Score
            df['B_Score'] = (df['Ore_Saptamana']/40 * 30) + ((6 - df['Scor_Energie']) * 10)
            df.loc[df['Mod_Lucru'].isin([1, 3]), 'B_Score'] *= 1.15
            df.loc[df['Presiune_Externa'] > 7, 'B_Score'] *= 1.20
            
            # 2. Silence Score
            df['S_Dissonance'] = df['Scor_Siguranta'] - ((df['Idei_Noi'] + df['Erori_Asumate']) / 2)
            
            # 3. Flight Risk
            df['F_Score'] = (df['Vechime_Rol'] * 2) + (df['Ultima_Marire'] * 1.5) + ((6 - df['Scor_Evolutie']) * 10)

            # --- VIZUALIZARE ---
            tab1, tab2, tab3, tab4 = st.tabs(["🔥 Burnout", "🤐 Silence", "✈️ Flight Risk", "🧩 Insights Expert"])

            with tab1:
                st.subheader("Distribuția Riscului de Burnout")
                fig1 = px.histogram(df, x="B_Score", color_discrete_sequence=['#ff4b4b'], labels={'B_Score': 'Scor Burnout'})
                st.plotly_chart(fig1, use_container_width=True)

            with tab2:
                st.subheader("Analiza Siguranță vs. Contribuție")
                fig2 = px.scatter(df, x="Scor_Siguranta", y="Idei_Noi", size="S_Dissonance", 
                                 color="S_Dissonance", color_continuous_scale='Oranges', hover_name="Nume")
                st.plotly_chart(fig2, use_container_width=True)

            with tab3:
                st.subheader("Top Flight Risk")
                fig3 = px.bar(df.sort_values('F_Score', ascending=False), x="Nume", y="F_Score", color="F_Score", color_continuous_scale='Reds')
                st.plotly_chart(fig3, use_container_width=True)

            with tab4:
                st.subheader("🧩 Cross-Pillar Interpretations")
                martyrs = df[(df['B_Score'] > 70) & (df['Presiune_Externa'] > 7)]
                talent_drain = df[(df['F_Score'] > 60) & (df['Idei_Noi'] > 7)]
                
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Martiri Invizibili", len(martyrs))
                    if len(martyrs) > 0: st.warning("Atenție: Oameni cu presiune externă uriașă și burnout. Risc de colaps personal.")
                with c2:
                    st.metric("Top Talents at Risk", len(talent_drain))
                    if len(talent_drain) > 0: st.error("Atenție: Oamenii cei mai creativi sunt gata să plece!")

            st.divider()
            st.caption("⚠️ Notă: Acestea sunt interpretări algoritmice. Necesită validare prin dialog direct.")

    except Exception as e:
        st.error(f"A apărut o eroare la procesare: {e}")
