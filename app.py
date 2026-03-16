import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import numpy as np

st.set_page_config(page_title="Team Scientist | Strategic Audit", layout="wide")

# --- CSS (Design Curat) ---
st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: rgba(128, 128, 128, 0.1);
        padding: 15px; border-radius: 10px; border: 1px solid rgba(128, 128, 128, 0.2); 
    }
    </style>
    """, unsafe_allow_html=True)

if 'lang' not in st.session_state: st.session_state.lang = "Română"
def change_lang(): st.session_state.lang = st.session_state.lang_select
st.sidebar.selectbox("Limbă / Language", ["Română", "English"], key="lang_select", on_change=change_lang)

# --- TRADUCERI ---
texts = {
    "Română": {
        "title": "🔬 Team Scientist | Diagnostic Strategic",
        "upload": "Încarcă fișierul TeamScientist_Audit_Final.xlsx",
        "err_col": "❌ Lipsesc coloanele:",
        "b_title": "🔥 Burnout", "s_title": "🤐 Masca Politicoasă", "f_title": "✈️ Risc Plecare", "o_title": "🕸️ Rețeaua (ONA)", "i_title": "🧩 Insights",
        "b_desc": "Scor 0-100. Peste 70 = Risc Critic | 50-70 = Atenție.",
        "iso_alert": "⚠️ Deconectare Totală (Izolare + Mască)",
        "ai_alert": "🤖 Oportunitate AI: Burnout ridicat, dar utilizare AI scăzută.",
        "martyrs": "Martiri Invizibili", "talent": "Risc Pierdere Talent"
    },
    "English": {
        "title": "🔬 Team Scientist | Strategic Diagnostic",
        "upload": "Upload TeamScientist_Audit_Final.xlsx",
        "err_col": "❌ Missing columns:",
        "b_title": "🔥 Burnout", "s_title": "🤐 Polite Mask", "f_title": "✈️ Flight Risk", "o_title": "🕸️ Network (ONA)", "i_title": "🧩 Insights",
        "b_desc": "Score 0-100. Over 70 = Critical | 50-70 = Warning.",
        "iso_alert": "⚠️ Total Disconnect (Isolation + Mask)",
        "ai_alert": "🤖 AI Opportunity: High Burnout, low AI usage.",
        "martyrs": "Invisible Martyrs", "talent": "Talent Drain Risk"
    }
}
l = texts[st.session_state.lang]

# --- COLOANE ---
REQUIRED_COLUMNS = ['Nume', 'Mod_Lucru', 'Ore_Saptamana', 'Presiune_Externa', 'Idei_Noi', 'Erori_Asumate', 'Vechime_Rol', 'Ultima_Marire', 'Scor_Energie', 'Scor_Siguranta', 'Scor_Evolutie', 'Sfat_De_La', 'AI_Usage']

st.title(l["title"])
uploaded_file = st.file_uploader(l["upload"], type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        # 1. Manager-Proofing & Cleaning
        num_cols = ['Ore_Saptamana', 'Presiune_Externa', 'Idei_Noi', 'Erori_Asumate', 'Vechime_Rol', 'Ultima_Marire', 'Scor_Energie', 'Scor_Siguranta', 'Scor_Evolutie', 'AI_Usage']
        for col in num_cols:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 2. Calcule recalibrate (pentru scale de 1-5)
        df['B_Score'] = ((df['Ore_Saptamana']/40 * 30) + ((6 - df['Scor_Energie']) * 12)).clip(0, 100)
        df.loc[df['Mod_Lucru'].isin([1, 3]), 'B_Score'] *= 1.10
        df.loc[df['Presiune_Externa'] > 4, 'B_Score'] *= 1.15
        df['B_Score'] = df['B_Score'].clip(0,100)

        df['S_Contr'] = (df['Idei_Noi'] + df['Erori_Asumate']) / 2
        df['S_Diss'] = df['Scor_Siguranta'] - df['S_Contr']
        df['S_Size'] = df['S_Diss'].apply(lambda x: max(x, 0) * 12 + 10)

        df['F_Score'] = ((df['Vechime_Rol'] * 0.5) + (df['Ultima_Marire'] * 0.5) + ((6 - df['Scor_Evolutie']) * 15)).clip(0, 100)

        # 3. ONA Pre-calcul
        G = nx.DiGraph()
        for _, r in df.iterrows():
            n = str(r['Nume'])
            G.add_node(n, B=r['B_Score'])
            advisors = [a.strip() for a in str(r['Sfat_De_La']).split(',') if a.strip() in df['Nume'].values]
            for a in advisors: G.add_edge(n, a)
        df['ONA_Conn'] = df['Nume'].apply(lambda x: G.in_degree(x) + G.out_degree(x) if x in G else 0)

        # --- UI ---
        tab1, tab2, tab3, tab4, tab5 = st.tabs([l["b_title"], l["s_title"], l["f_title"], l["o_title"], l["i_title"]])

        with tab1: # BURNOUT
            df_b = df.sort_values('B_Score', ascending=True)
            colors = ['#ff4b4b' if s > 70 else '#ffa421' if s > 50 else '#28a745' for s in df_b['B_Score']]
            st.plotly_chart(go.Figure(go.Bar(x=df_b['B_Score'], y=df_b['Nume'], orientation='h', marker_color=colors, text=df_b['B_Score'].round(1), textposition='outside')).update_layout(xaxis=dict(range=[0, 115]), height=500), use_container_width=True)

        with tab2: # SILENCE
            fig2 = px.scatter(df, x="Scor_Siguranta", y="S_Contr", size="S_Size", color="S_Diss", color_continuous_scale='Oranges', hover_name="Nume")
            fig2.add_vline(x=3.5, line_dash="dot", line_color="gray"); fig2.add_hline(y=3.5, line_dash="dot", line_color="gray")
            st.plotly_chart(fig2, use_container_width=True)

        with tab3: # FLIGHT
            st.plotly_chart(px.bar(df.sort_values('F_Score', ascending=True), x="F_Score", y="Nume", orientation='h', color="F_Score", color_continuous_scale='Reds'), use_container_width=True)

        with tab4: # ONA
            pos = nx.spring_layout(G, k=0.8, seed=42)
            fig_ona = go.Figure()
            for e in G.edges():
                x0, y0 = pos[e[0]]; x1, y1 = pos[e[1]]
                fig_ona.add_trace(go.Scatter(x=[x0, (x0+x1)/2, x1], y=[y0, (y0+y1)/2, y1], mode='lines+markers', marker=dict(symbol="arrow", size=10, angleref="previous"), line=dict(width=1, color='gray'), hoverinfo='none'))
            nx_nodes = list(G.nodes())
            fig_ona.add_trace(go.Scatter(x=[pos[n][0] for n in nx_nodes], y=[pos[n][1] for n in nx_nodes], mode='markers+text', text=nx_nodes, textposition="bottom center", marker=dict(size=[(G.in_degree(n)*10)+15 for n in nx_nodes], color=[G.nodes[n]['B'] for n in nx_nodes], colorscale='Reds', showscale=True)))
            fig_ona.update_layout(showlegend=False, xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), yaxis=dict(showgrid=False, zeroline=False, showticklabels=False), height=600)
            st.plotly_chart(fig_ona, use_container_width=True)

        with tab5: # INSIGHTS (AI INTEGRATED)
            martyrs = df[(df['B_Score'] > 70) & (df['Presiune_Externa'] > 3)]
            talent = df[(df['F_Score'] > 60) & (df['Idei_Noi'] > 3)]
            isolated = df[(df['S_Diss'] > 2.5) & (df['ONA_Conn'] <= 1)]
            ai_opp = df[(df['B_Score'] > 60) & (df['AI_Usage'] < 3)]
            
            c1, c2 = st.columns(2)
            with c1:
                st.metric(l["martyrs"], len(martyrs))
                if not martyrs.empty: st.warning(f"⚠️ {', '.join(martyrs['Nume'].tolist())}")
            with c2:
                st.metric(l["talent"], len(talent))
                if not talent.empty: st.error(f"🚨 {', '.join(talent['Nume'].tolist())}")
            
            if not isolated.empty: st.error(f"{l['iso_alert']}: {', '.join(isolated['Nume'].tolist())}")
            if not ai_opp.empty: st.info(f"{l['ai_alert']} -> **{', '.join(ai_opp['Nume'].tolist())}**")

    except Exception as e:
        st.error(f"Eroare: {e}")
