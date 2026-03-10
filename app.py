import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx

st.set_page_config(page_title="Logically Human | Premium Audit", layout="wide")

# --- UI & CSS ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIONARE LIMBĂ ---
if 'lang' not in st.session_state:
    st.session_state.lang = "Română"

def change_lang():
    st.session_state.lang = st.session_state.lang_select

st.sidebar.selectbox("Limbă / Language", ["Română", "English"], key="lang_select", on_change=change_lang)

texts = {
    "Română": {
        "title": "🧠 Logically Human | Diagnostic Strategic",
        "upload": "Încarcă fișierul Excel (13 coloane, inclusiv 'Sfat_De_La')",
        "err_col": "❌ Lipsesc coloanele:",
        "b_title": "🔥 Burnout",
        "s_title": "🤐 Masca Politicoasă (Silence)",
        "f_title": "✈️ Risc Plecare (Flight)",
        "o_title": "🕸️ Rețeaua Echipei (ONA)",
        "i_title": "🧩 Analiză Avansată",
        "data_table": "Vezi datele procesate detaliat",
        "martyrs": "Martiri Invizibili",
        "talent": "Talent Drain Risk"
    },
    "English": {
        "title": "🧠 Logically Human | Strategic Diagnostic",
        "upload": "Upload Excel file (13 columns, incl. 'Sfat_De_La')",
        "err_col": "❌ Missing columns:",
        "b_title": "🔥 Burnout",
        "s_title": "🤐 Polite Mask (Silence)",
        "f_title": "✈️ Flight Risk",
        "o_title": "🕸️ Team Network (ONA)",
        "i_title": "🧩 Advanced Insights",
        "data_table": "View detailed processed data",
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
            # --- CALCUL PILONI CLASICI ---
            df['B_Score'] = (df['Ore_Saptamana']/40 * 30) + ((6 - df['Scor_Energie']) * 10)
            df.loc[df['Mod_Lucru'].isin([1, 3]), 'B_Score'] *= 1.15
            df.loc[df['Presiune_Externa'] > 7, 'B_Score'] *= 1.20
            
            df['S_Dissonance'] = df['Scor_Siguranta'] - ((df['Idei_Noi'] + df['Erori_Asumate']) / 2)
            df['Size_Display'] = df['S_Dissonance'].apply(lambda x: max(x, 0) * 10 + 5)
            
            df['F_Score'] = (df['Vechime_Rol'] * 2) + (df['Ultima_Marire'] * 1.5) + ((6 - df['Scor_Evolutie']) * 10)

            # --- UI TABS ---
            tab1, tab2, tab3, tab4, tab5 = st.tabs([l["b_title"], l["s_title"], l["f_title"], l["o_title"], l["i_title"]])

            with tab1:
                fig1 = px.histogram(df, x="B_Score", color_discrete_sequence=['#ff4b4b'])
                st.plotly_chart(fig1, use_container_width=True)

            with tab2:
                fig2 = px.scatter(df, x="Scor_Siguranta", y="Idei_Noi", size="Size_Display", color="S_Dissonance", color_continuous_scale='Oranges', hover_name="Nume", hover_data={'Size_Display': False})
                st.plotly_chart(fig2, use_container_width=True)

            with tab3:
                fig3 = px.bar(df.sort_values('F_Score', ascending=False), x="Nume", y="F_Score", color="F_Score", color_continuous_scale='Reds')
                st.plotly_chart(fig3, use_container_width=True)

            # --- NOU: ONA NETWORK GRAPH ---
            with tab4:
                st.subheader("Harta Influenței (Cine se bazează pe cine)")
                
                # Creăm rețeaua cu NetworkX
                G = nx.DiGraph()
                for _, row in df.iterrows():
                    node = str(row['Nume'])
                    G.add_node(node, B_Score=row['B_Score'])
                    advisors = str(row['Sfat_De_La']).split(',')
                    for adv in advisors:
                        adv = adv.strip()
                        if adv and adv in df['Nume'].values:
                            # Săgeata pleacă de la cel care cere sfatul către "Hub"
                            G.add_edge(node, adv)

                # Calculăm câte cereri primește fiecare (In-Degree)
                in_degrees = dict(G.in_degree())
                pos = nx.spring_layout(G, k=0.5, seed=42)

                # Desenăm muchiile (liniile)
                edge_x = []
                edge_y = []
                for edge in G.edges():
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])

                edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=1, color='#cccccc'), hoverinfo='none', mode='lines')

                # Desenăm nodurile (oamenii)
                node_x = []
                node_y = []
                node_text = []
                node_color = []
                node_size = []

                for node in G.nodes():
                    x, y = pos[node]
                    node_x.append(x)
                    node_y.append(y)
                    in_deg = in_degrees.get(node, 0)
                    b_score = G.nodes[node].get('B_Score', 0)
                    
                    node_text.append(f"<b>{node}</b><br>Căutat de: {in_deg} colegi<br>Scor Burnout: {b_score:.1f}")
                    node_color.append(b_score)
                    # Mărimea depinde de câți oameni se duc la el după sfat (minim 10px)
                    node_size.append((in_deg * 8) + 15)

                node_trace = go.Scatter(
                    x=node_x, y=node_y, mode='markers+text', text=[n for n in G.nodes()],
                    textposition="bottom center", hoverinfo='text', hovertext=node_text,
                    marker=dict(showscale=True, colorscale='Reds', color=node_color, size=node_size, colorbar=dict(title="Nivel Burnout"), line_width=2))

                fig_net = go.Figure(data=[edge_trace, node_trace],
                                    layout=go.Layout(showlegend=False, hovermode='closest', margin=dict(b=0,l=0,r=0,t=0),
                                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
                
                st.plotly_chart(fig_net, use_container_width=True)
                st.info("💡 **Ghid vizual:** Mărimea cercului indică de câți oameni e căutat pentru sfaturi. Culoarea roșie indică riscul lui de epuizare. Caută nodurile mari și roșii: aceia sunt pilonii tăi gata să cedeze.")

            # --- INSIGHTS ---
            with tab5:
                martyrs = df[(df['B_Score'] > 70) & (df['Presiune_Externa'] > 7)]
                talent_drain = df[(df['F_Score'] > 60) & (df['Idei_Noi'] > 7)]
                
                c1, c2 = st.columns(2)
                with c1:
                    st.metric(l["martyrs"], len(martyrs))
                    if len(martyrs) > 0: st.warning(f"{', '.join(martyrs['Nume'].tolist())}")
                with c2:
                    st.metric(l["talent"], len(talent_drain))
                    if len(talent_drain) > 0: st.error(f"{', '.join(talent_drain['Nume'].tolist())}")

            # --- DATA TABLE ---
            st.divider()
            with st.expander(f"📊 {l['data_table']}"):
                st.dataframe(df)

    except Exception as e:
        st.error(f"Eroare: {e}")
