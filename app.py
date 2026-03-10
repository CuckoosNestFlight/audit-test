import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Logically Human | Premium Audit", layout="wide")

st.title("🧠 Logically Human | Diagnostic Strategic v1.5")

REQUIRED_COLUMNS = [
    'Nume', 'Ore_Saptamana', 'Zile_Concediu', 'Idei_Noi', 'Erori_Asumate', 
    'Vechime_Rol', 'Ultima_Marire', 'Scor_Energie', 'Scor_Siguranta', 
    'Scor_Evolutie', 'Mod_Lucru', 'Presiune_Externa'
]

uploaded_file = st.file_uploader("Încarcă fișierul Excel", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        
        if missing:
            st.error(f"❌ Lipsesc coloanele: {', '.join(missing)}")
        else:
            # --- CALCUL PILONI ---
            # 1. Burnout
            df['B_Score'] = (df['Ore_Saptamana']/40 * 30) + ((6 - df['Scor_Energie']) * 10)
            df.loc[df['Mod_Lucru'].isin([1, 3]), 'B_Score'] *= 1.15
            df.loc[df['Presiune_Externa'] > 7, 'B_Score'] *= 1.20
            
            # 2. Silence (Dissonance)
            df['S_Dissonance'] = df['Scor_Siguranta'] - ((df['Idei_Noi'] + df['Erori_Asumate']) / 2)
            # Cream o coloana pentru marimea bulei (doar valori pozitive, minim 5 pentru vizibilitate)
            df['Size_Display'] = df['S_Dissonance'].apply(lambda x: max(x, 0) * 10 + 5)
            
            # 3. Flight Risk
            df['F_Score'] = (df['Vechime_Rol'] * 2) + (df['Ultima_Marire'] * 1.5) + ((6 - df['Scor_Evolutie']) * 10)

            # --- UI ---
            tab1, tab2, tab3, tab4 = st.tabs(["🔥 Burnout", "🤐 Silence", "✈️ Flight Risk", "🧩 Insights Expert"])

            with tab1:
                st.subheader("Distribuția Riscului de Burnout")
                fig1 = px.histogram(df, x="B_Score", color_discrete_sequence=['#ff4b4b'])
                st.plotly_chart(fig1, use_container_width=True)

            with tab2:
                st.subheader("Analiza Siguranță vs. Contribuție")
                # Aici am schimbat 'size' cu 'Size_Display'
                fig2 = px.scatter(df, x="Scor_Siguranta", y="Idei_Noi", 
                                 size="Size_Display", 
                                 color="S_Dissonance", 
                                 color_continuous_scale='Oranges', 
                                 hover_name="Nume",
                                 hover_data={'Size_Display': False, 'S_Dissonance': True})
                st.plotly_chart(fig2, use_container_width=True)
                st.info("Bulele mari portocalii = 'Masca Politicoasă' (Disonanță ridicată).")

            with tab3:
                st.subheader("Top Flight Risk")
                fig3 = px.bar(df.sort_values('F_Score', ascending=False), x="Nume", y="F_Score", color="F_Score", color_continuous_scale='Reds')
                st.plotly_chart(fig3, use_container_width=True)

            with tab4:
                st.subheader("🧩 Interpretări Cross-Pillar")
                martyrs = df[(df['B_Score'] > 70) & (df['Presiune_Externa'] > 7)]
                talent_drain = df[(df['F_Score'] > 60) & (df['Idei_Noi'] > 7)]
                
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Martiri Invizibili", len(martyrs))
                    if len(martyrs) > 0: st.warning(f"Detectați: {', '.join(martyrs['Nume'].tolist())}")
                with c2:
                    st.metric("Top Talents at Risk", len(talent_drain))
                    if len(talent_drain) > 0: st.error(f"Risc de plecare pentru: {', '.join(talent_drain['Nume'].tolist())}")

            st.divider()
            st.markdown("### 📞 Contact & Next Level\nPentru o diagnoză detaliată și workshop-uri de intervenție, contactați-mă la **[Email-ul Tau]**.")

    except Exception as e:
        st.error(f"Eroare neprevăzută: {e}")
