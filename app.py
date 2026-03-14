import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import numpy as np

st.set_page_config(page_title="Team Scientist | Strategic Audit", layout="wide")

# --- CSS Universal (Dark & Light Mode) ---
st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: rgba(128, 128, 128, 0.1);
        padding: 15px; border-radius: 10px; border: 1px solid rgba(128, 128, 128, 0.2); 
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px; background-color: rgba(128, 128, 128, 0.05); border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIONARE LIMBĂ ---
if 'lang' not in st.session_state:
    st.session_state.lang = "Română"

def change_lang():
    st.session_state.lang = st.session_state.lang_select

st.sidebar.selectbox("Limbă / Language", ["Română", "English"], key="lang_select", on_change=change_lang)

# --- DICȚIONAR TEXTE (ACUM COMPLET) ---
texts = {
    "Română": {
        "title": "🔬 Team Scientist | Diagnostic Strategic",
        "upload": "Încarcă fișierul Excel (13 coloane)",
        "err_col": "❌ Lipsesc coloanele:",
        "b_title": "🔥 Burnout",
        "s_title": "🤐 Masca Politicoasă",
        "f_title": "✈️ Risc Plecare",
        "o_title": "🕸️ Rețeaua (ONA)",
        "i_title": "🧩 Analiză Avansată",
        "data_table": "Vezi datele procesate detaliat",
        "b_subtitle": "Clasamentul Riscului de Burnout",
        "b_desc": "<b>Scor 0-100:</b> <span style='color:#ff4b4b'>Peste 70 (Risc Critic)</span> | <span style='color:#ffa421'>50-70 (Atenție)</span> | <span style='color:#28a745'>Sub 50 (Sănătos)</span>",
        "s_subtitle": "Disonanța dintre Siguranță și Contribuție",
        "s_desc": "<b>Cum citim:</b> Oamenii din zona portocalie spun că sunt 'OK', dar au încetat să mai aducă idei sau să raporteze erori. Este un semnal de deconectare psihologică.",
        "o_subtitle": "Harta Influenței: Cine se bazează pe cine?",
        "o_desc": "Săgeata indică direcția solicitării de ajutor. Nodurile mari și roșii sunt 'Hub-uri de expertiză' aflate la un pas de epuizare.",
        "f_subtitle": "Probabilitatea de demisie (următoarele 3 luni)",
        "martyrs": "Martiri Invizibili",
        "talent": "Risc Pierdere Talent"
    },
    "English": {
        "title": "🔬 Team Scientist | Strategic Diagnostic",
        "upload": "Upload Excel file (13 columns)",
        "err_col": "❌ Missing columns:",
        "b_title": "🔥 Burnout",
        "s_title": "🤐 Polite Mask",
        "f_title": "✈️ Flight Risk",
        "o_title": "🕸️ Network (ONA)",
        "i_title": "🧩 Advanced Insights",
        "data_table": "View detailed data",
        "b_subtitle": "Burnout Risk Ranking",
        "b_desc": "<b>Score 0-100:</b> <span style='color:#ff4b4b'>Above 70 (Critical)</span> | <span style='color:#ffa421'>50-70 (Warning)</span> | <span style='color:#28a745'>Below 50 (Healthy)</span>",
        "s_subtitle": "Dissonance: Safety vs Contribution",
        "s_desc": "<b>How to read:</b> People in the orange area say they are 'OK' but have stopped bringing ideas or reporting errors. This is a sign of psychological disconnect.",
        "o_subtitle": "Influence Map: Who relies on whom?",
        "o_desc": "The arrow indicates the direction of the help request. Large red nodes are 'Expertise Hubs' close to collapse.",
        "f_subtitle": "Resignation probability (next 3 months)",
        "martyrs": "Invisible Martyrs",
        "talent": "Talent Drain Risk"
    }
}

l = texts[st.session_state.lang]

st.title(l["title"])

REQUIRED_COLUMNS = [
    'Nume', 'Ore_Saptamana', 'Zile_Concediu', 'Idei_Noi', 'Erori_Asumate', 
    'Vechime_Rol', 'Ultima_Marire', 'Scor_Energie', 'Scor_Siguranta', 
    'Scor_Evolutie', 'Mod_Lucru', 'Presiune_Externa', 'Sfat_De_La'
]

uploaded_file = st.file_uploader(l["upload"], type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        
        if missing:
            st.error(f"{l['err_col']} {', '.join(missing)}")
        else:
            # --- CALCULE ---
            df['B_Score'] = ((df['Ore_Saptamana']/40 * 30) + ((6 - df['Scor_Energie']) * 10)).clip(0, 100)
            df.loc[df['Mod_Lucru'].isin([1, 3]), 'B_Score'] *= 1.15
            df.loc[df['Presiune_Externa'] > 7, 'B_Score'] *= 1.20
            df['B_Score'] = df['B_Score'].clip(0, 100)

            df['S_Contr'] = (df['Idei_Noi'] + df['Erori_Asumate']) / 2
            df['S_Diss'] = df['Scor_Siguranta'] - df['S_Contr']
            df['S_Size'] = df['S_Diss'].apply(lambda x: max(x, 0) * 12 + 10)

            df['F_Score'] = ((df['Vechime_Rol'] * 2) + (df['Ultima_Marire'] * 1.5) + ((6 - df['Scor_Evolutie']) * 10)).clip(0, 100)

            # --- TABS ---
            tab1, tab2, tab3, tab4, tab5 = st.tabs([l["b_title"], l["s_title"], l["f_title"], l["o_title"], l["i_title"]])

            with tab1:
                st.subheader(l["b_subtitle"])
                st.markdown(l["b_desc"], unsafe_allow_html=True)
                df_b = df.sort_values('B_Score', ascending=True)
                colors = ['#ff4b4b' if s > 70 else '#ffa421' if s > 50 else '#28a745' for s in df_b['B_Score']]
                fig1 = go.Figure(go.Bar(x=df_b['B_Score'], y=df_b['Nume'], orientation='h', marker_color=colors, text=df_b['B_Score'].round(1), textposition='outside'))
                fig1.update_layout(xaxis=dict(range=[0, 115]), height=500, margin=dict(l=0, r=0, t=20, b=0))
                st.plotly_chart(fig1, use_container_width=True)

            with tab2:
                st.subheader(l["s_subtitle"])
                st.info(l["s_desc"])
                fig2 = px.scatter(df, x="Scor_Siguranta", y="S_Contr", size="S_Size", color="S_Diss", color_continuous_scale='Oranges', hover_name="Nume")
                fig2.add_vline(x=4, line_dash="dot", line_color="gray")
                fig2.add_hline(y=4, line_dash="dot", line_color="gray")
                st.plotly_chart(fig2, use_container_width=True)

            with tab3:
                st.subheader(l["f_subtitle"])
                df_f = df.sort_values('F_Score', ascending=True)
                fig3 = px.bar(df_f, x="F_Score", y="Nume", orientation='h', color="F_Score", color_continuous_scale='Reds')
                st.plotly_chart(fig3, use_container_width=True)

            with tab4:
                st.subheader(l["o_subtitle"])
                st.caption(l["o_desc"])
                G = nx.DiGraph()
                for _, r in df.iterrows():
                    G.add_node(str(r['Nume']), B=r['B_Score'])
                    for a in str(r['Sfat_De_La']).split(','):
                        a = a.strip()
                        if a in df['Nume'].values: G.add_edge(str(r['Nume']), a)
                
                pos = nx.spring_layout(G, k=0.8, seed=42)
                fig_ona = go.Figure()
                for e in G.edges():
                    x0, y0 = pos[e[0]]; x1, y1 = pos[e[1]]
                    fig_ona.add_trace(go.Scatter(x=[x0, (x0+x1)/2, x1], y=[y0, (y0+y1)/2, y1], mode='lines+markers', marker=dict(symbol="arrow", size=10, angleref="previous"), line=dict(width=1, color='gray'), hoverinfo='none'))
                
                nx_nodes = G.nodes()
                fig_ona.add_trace(go.Scatter(x=[pos[n][0] for n in nx_nodes], y=[pos[n][1] for n in nx_nodes], mode='markers+text', text=list(nx_nodes), textposition="bottom center", marker=dict(size=[(dict(G.in_degree())[n]*8)+15 for n in nx_nodes], color=[G.nodes[n]['B'] for n in nx_nodes], colorscale='Reds', showscale=True)))
                fig_ona.update_layout(showlegend=False, xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), yaxis=dict(showgrid=False, zeroline=False, showticklabels=False), height=600)
                st.plotly_chart(fig_ona, use_container_width=True)

            with tab5:
                st.subheader(l["i_title"])
                martyrs = df[(df['B_Score'] > 70) & (df['Presiune_Externa'] > 7)]
                talent = df[(df['F_Score'] > 60) & (df['Idei_Noi'] > 7)]
                c1, c2 = st.columns(2)
                with c1:
                    st.metric(l["martyrs"], len(martyrs))
                    if not martyrs.empty: st.warning(f"⚠️ {', '.join(martyrs['Nume'].tolist())}")
                with c2:
                    st.metric(l["talent"], len(talent))
                    if not talent.empty: st.error(f"🚨 {', '.join(talent['Nume'].tolist())}")

            st.divider()
            with st.expander(l["data_table"]):
                st.dataframe(df)

    except Exception as e:
        st.error(f"Eroare procesare: {e}")
