import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import numpy as np

st.set_page_config(page_title="Team Scientist | Strategic Audit", layout="wide")

# --- UI & CSS (Smart Dark/Light Mode) ---
st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: rgba(128, 128, 128, 0.05);
        padding: 15px; border-radius: 10px; border: 1px solid rgba(128, 128, 128, 0.1); 
    }
    .stAlert { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIONARE LIMBĂ ---
if 'lang' not in st.session_state:
    st.session_state.lang = "Română"

def change_lang():
    st.session_state.lang = st.session_state.lang_select

st.sidebar.selectbox("Limbă / Language", ["Română", "English"], key="lang_select", on_change=change_lang)

# --- DICȚIONAR TEXTE ---
texts = {
    "Română": {
        "title": "🔬 Team Scientist | Diagnostic Strategic v2.0",
        "upload": "Încarcă fișierul Excel de audit (13 coloane)",
        "err_col": "❌ Lipsesc coloanele:",
        "b_title": "🔥 Burnout",
        "s_title": "🤐 Masca Politicoasă (Silence)",
        "f_title": "✈️ Risc Plecare (Flight)",
        "o_title": "🕸️ Rețeaua Echipei (ONA)",
        "i_title": "🧩 Insights Avansate",
        "data_table": "Vezi datele brute",
        "b_subtitle": "Clasamentul Riscului de Epuizare pe Angajat",
        "b_desc": "Scor 0-100. Zone: Roșu (>70 - Risc Critic), Portocaliu (50-70 - Atenție), Verde (<50 - Sănătos).",
        "b_summary": "⚠️ Atenție: {} angajați sunt în Zona Critică de burnout!",
        "s_subtitle": "Disonanța dintre Siguranța Declarată și Contribuția Reală",
        "s_desc": "<b>Cum citim graficul:</b> Axele arată Siguranța (X) și Contribuția (Y). Bulele mari și portocalii sunt în zona 'Măștii Politicoase': Ei spun că se simt în siguranță, dar tac și nu contribuie. Necesită reconectare autentică.",
        "o_subtitle": "Harta Influenței și a Dependențelor în Echipă",
        "o_desc": "Săgețile indică cine cere sfatul cui. Culoarea arată burnout-ul. Nodurile mari și roșii sunt piloni de expertiză la un pas de colaps.",
        "f_subtitle": "Probabilitatea de Demisie în Următoarele 3 Luni"
    },
    "English": {
        "title": "🔬 Team Scientist | Strategic Diagnostic v2.0",
        "upload": "Upload Audit Excel file (13 columns)",
        "err_col": "❌ Missing columns:",
        "b_title": "🔥 Burnout",
        "s_title": "🤐 Polite Mask (Silence)",
        "f_title": "✈️ Flight Risk",
        "o_title": "🕸️ Team Network (ONA)",
        "i_title": "🧩 Advanced Insights",
        "data_table": "View raw data",
        "b_subtitle": "Employee Burnout Risk Ranking",
        "b_desc": "Score 0-100. Zones: Red (>70 - Critical Risk), Orange (50-70 - Warning), Green (<50 - Healthy).",
        "b_summary": "⚠️ Warning: {} employees are in the Critical Burnout Zone!",
        "s_subtitle": "Dissonance Between Declared Safety and Real Contribution",
        "s_desc": "<b>How to read:</b> Axes show Safety (X) and Contribution (Y). Large orange bubbles are 'Polite Mask': They say they feel safe but stay silent and don't contribute. Needs authentic reconnection.",
        "o_subtitle": "Team Influence and Dependency Map",
        "o_desc": "Arrows indicate who seeks advice from whom. Color shows burnout. Large red nodes are expertise pillars close to collapse.",
        "f_subtitle": "Probability of Resignation in the Next 3 Months"
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
            # --- CALCUL PILONI ---
            # 1. Burnout
            df['B_Score'] = (df['Ore_Saptamana']/40 * 30) + ((6 - df['Scor_Energie']) * 10)
            df.loc[df['Mod_Lucru'].isin([1, 3]), 'B_Score'] *= 1.15
            df.loc[df['Presiune_Externa'] > 7, 'B_Score'] *= 1.20
            df['B_Score'] = df['B_Score'].clip(0, 100) # Limităm scorul
            
            # Definire zone burnout pentru colorare
            def color_burnout(score):
                if score > 70: return '#ff4b4b' # Rosu
                if score > 50: return '#ffa421' # Portocaliu
                return '#28a745' # Verde
            df['B_Color'] = df['B_Score'].apply(color_burnout)

            # 2. Silence
            df['S_Contributie'] = (df['Idei_Noi'] + df['Erori_Asumate']) / 2
            df['S_Dissonance'] = df['Scor_Siguranta'] - df['S_Contributie']
            # Marime bula bazata pe disonanta pozitiva (tace desi e safe)
            df['Size_Display'] = df['S_Dissonance'].apply(lambda x: max(x, 0) * 12 + 8)

            # 3. Flight
            df['F_Score'] = (df['Vechime_Rol'] * 2) + (df['Ultima_Marire'] * 1.5) + ((6 - df['Scor_Evolutie']) * 10)
            df['F_Score'] = df['F_Score'].clip(0, 100)

            # --- UI TABS ---
            tab1, tab2, tab3, tab4, tab5 = st.tabs([l["b_title"], l["s_title"], l["f_title"], l["o_title"], l["i_title"]])

            # --- TAB 1: BURNOUT (Clasament Clar) ---
            with tab1:
                st.subheader(l["b_subtitle"])
                st.caption(l["b_desc"])
                
                critical_count = len(df[df['B_Score'] > 70])
                if critical_count > 0:
                    st.error(l["b_summary"].format(critical_count))
                
                # Grafic cu bare rangate, colorat pe zone
                df_sorted_b = df.sort_values('B_Score', ascending=True) # Asc pentru ca managerul vrea rosul sus
                fig1 = go.Figure(go.Bar(
                    x=df_sorted_b['B_Score'],
                    y=df_sorted_b['Nume'],
                    orientation='h',
                    marker_color=df_sorted_b['B_Color'],
                    text=df_sorted_b['B_Score'].round(1),
                    textposition='outside'
                ))
                fig1.update_layout(xaxis=dict(title="Scor Burnout", range=[0, 110]), yaxis=dict(title=None), margin=dict(l=0, r=0, t=20, b=0), height=500)
                # Adaugam linii de demarcatie zone
                fig1.add_vline(x=70, line_width=2, line_dash="dash", line_color="#ff4b4b")
                fig1.add_vline(x=50, line_width=2, line_dash="dash", line_color="#ffa421")
                
                st.plotly_chart(fig1, use_container_width=True)

            # --- TAB 2: SILENCE (Explicat) ---
            with tab2:
                st.subheader(l["s_subtitle"])
                st.markdown(f"<div style='background-color: rgba(255, 164, 33, 0.1); padding: 15px; border-radius: 10px; border: 1px solid #ffa421;'>{l['s_desc']}</div>", unsafe_allow_html=True)
                st.write("")
                
                fig2 = px.scatter(df, x="Scor_Siguranta", y="S_Contributie", 
                                 size="Size_Display", color="S_Dissonance", 
                                 color_continuous_scale='Oranges', hover_name="Nume",
                                 labels={'Scor_Siguranta': 'Siguranță Declarată (X)', 'S_Contributie': 'Contribuție Reală (Y)'},
                                 hover_data={'Size_Display': False, 'S_Dissonance': True})
                
                # Adaugam linii de zona pentru claritate
                fig2.add_hline(y=4, line_width=1, line_dash="dot", line_color="#cccccc")
                fig2.add_vline(x=4, line_width=1, line_dash="dot", line_color="#cccccc")
                # Adaugam text annotations pe zone
                fig2.add_annotation(x=5, y=1, text="🤐 Masca<br>Politicoasă", showarrow=False, font=dict(color="#ffa421", size=14))
                fig2.add_annotation(x=5, y=8, text="✅ Zona<br>Sănătoasă", showarrow=False, font=dict(color="#28a745", size=14))

                st.plotly_chart(fig2, use_container_width=True)

            # --- TAB 3: FLIGHT (Rangate) ---
            with tab3:
                st.subheader(l["f_subtitle"])
                df_sorted_f = df.sort_values('F_Score', ascending=True)
                fig3 = px.bar(df_sorted_f, x="F_Score", y="Nume", orientation='h',
                             color="F_Score", color_continuous_scale='Reds',
                             text=df_sorted_f['F_Score'].round(1))
                fig3.update_layout(xaxis=dict(title="Probabilitate Plecare (0-100)", range=[0, 105]), yaxis=dict(title=None), margin=dict(l=0, r=0, t=20, b=0))
                st.plotly_chart(fig3, use_container_width=True)

            # --- TAB 4: ONA (Vectori și Săgeți CURBATE) ---
            with tab4:
                st.subheader(l["o_subtitle"])
                st.caption(l["o_desc"])
                
                # NetworkX DiGraph (Directed)
                G = nx.DiGraph()
                for _, row in df.iterrows():
                    node = str(row['Nume'])
                    G.add_node(node, B_Score=row['B_Score'])
                    advisors = str(row['Sfat_De_La']).split(',')
                    for adv in advisors:
                        adv = adv.strip()
                        if adv and adv in df['Nume'].values:
                            # Săgeata pleacă de la cel care cere -> la cel care oferă
                            G.add_edge(node, adv)

                # Layout smart
                pos = nx.spring_layout(G, k=0.8, seed=42)
                in_degrees = dict(G.in_degree())

                # Crearea graficului cu Plotly go.Figure (pentru control total)
                fig_net = go.Figure()

                # 1. Muchii (Linii curbate cu săgeți discrete)
                for edge in G.edges():
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    
                    # Calculăm un punct de curbură intermediar
                    dist = np.sqrt((x1-x0)**2 + (y1-y0)**2)
                    curve_strength = 0.15 # Ajustează curbura
                    
                    # Punct intermediar curbat
                    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
                    # Vector perpendicular
                    px_v, py_v = -(y1 - y0), (x1 - x0)
                    if dist > 0:
                        px_v, py_v = px_v / dist, py_v / dist # Normalizare
                    
                    cx, cy = mx + px_v * curve_strength * dist, my + py_v * curve_strength * dist
                    
                    # Generăm curba (Bezier simplu)
                    t = np.linspace(0, 1, 15)
                    curve_x = (1-t)**2 * x0 + 2*(1-t)*t * cx + t**2 * x1
                    curve_y = (1-t)**2 * y0 + 2*(1-t)*t * cy + t**2 * y1
                    
                    # Desenăm linia curbată
                    fig_net.add_trace(go.Scatter(
                        x=curve_x, y=curve_y,
                        mode='lines',
                        line=dict(width=1.5, color='rgba(200, 200, 200, 0.6)'),
                        hoverinfo='none',
                        showlegend=False
                    ))
                    
                    # Adăugăm un marker tip săgeată la capăt (aproape de țintă, nu chiar pe ea)
                    arrow_t = 0.85 # Poziția săgeții pe curbă (0.9 = 90% din drum)
                    ax = (1-arrow_t)**2 * x0 + 2*(1-arrow_t)*arrow_t * cx + arrow_t**2 * x1
                    ay = (1-arrow_t)**2 * y0 + 2*(1-arrow_t)*arrow_t * cy + arrow_t**2 * y1
                    
                    # Calculăm unghiul săgeții (tangenta la curbă)
                    dt = 0.01
                    tx_ahead = (1-(arrow_t+dt))**2 * x0 + 2*(1-(arrow_t+dt))*(arrow_t+dt) * cx + (arrow_t+dt)**2 * x1
                    ty_ahead = (1-(arrow_t+dt))**2 * y0 + 2*(1-(arrow_t+dt))*(arrow_t+dt) * cy + (arrow_t+dt)**2 * y1
                    
                    # Unghi în grade
                    angle = np.degrees(np.arctan2(ty_ahead - ay, tx_ahead - ax))

                    fig_net.add_trace(go.Scatter(
                        x=[ax], y=[ay],
                        mode='markers',
                        marker=dict(
                            symbol='arrow',
                            size=12,
                            color='rgba(180, 180, 180, 0.8)',
                            angle=angle-90, # Ajustare orientare marker
                            line=dict(width=0)
                        ),
                        hoverinfo='none',
                        showlegend=False
                    ))

                # 2. Noduri (Oamenii)
                node_x, node_y, node_text, node_color, node_size = [], [], [], [], []
                for node in G.nodes():
                    x, y = pos[node]
                    node_x.append(x)
                    node_y.append(y)
                    in_deg = in_degrees.get(node, 0)
                    b_score = G.nodes[node].get('B_Score', 0)
                    
                    node_text.append(f"<b>{node}</b><br>Solicitat de: {in_deg} colegi<br>Scor Burnout: {b_score:.1f}")
                    node_color.append(b_score)
                    node_size.append((in_deg * 8) + 20) # Bază mai mare pentru noduri

                fig_net.add_trace(go.Scatter(
                    x=node_x, y=node_y,
                    mode='markers+text',
                    text=[n for n in G.nodes()],
                    textposition="bottom center",
                    textfont=dict(size=11),
                    hoverinfo='text',
                    hovertext=node_text,
                    marker=dict(
                        showscale=True,
                        colorscale='Reds',
                        color=node_color,
                        size=node_size,
                        colorbar=dict(title="Nivel Burnout", thickness=15, x=1.02),
                        line=dict(width=2, color='#ffffff') # Contur alb pentru vizibilitate in Dark Mode
                    ),
                    showlegend=False
                ))

                # Layout final
                fig_net.update_layout(
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=0,l=0,r=0,t=0),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    height=700
                )
                
                st.plotly_chart(fig_net, use_container_width=True)

            # --- INSIGHTS EXPERT ---
            with tab5:
                st.subheader(l["i_title"])
                martyrs = df[(df['B_Score'] > 70) & (df['Presiune_Externa'] > 7)]
                talent_drain = df[(df['F_Score'] > 60) & (df['Idei_Noi'] > 7)]
                
                c1, c2 = st.columns(2)
                with c1:
                    st.metric(l["martyrs"], len(martyrs))
                    if len(martyrs) > 0: st.warning(f"<b>Nume:</b> {', '.join(martyrs['Nume'].tolist())}", unsafe_allow_html=True)
                with c2:
                    st.metric(l["talent"], len(talent_drain))
                    if len(talent_drain) > 0: st.error(f"<b>Nume:</b> {', '.join(talent_drain['Nume'].tolist())}", unsafe_allow_html=True)

            # --- DATA TABLE ---
            st.divider()
            with st.expander(f"📊 {l['data_table']}"):
                st.dataframe(df)

    except Exception as e:
        st.error(f"Eroare procesare: {e}")
