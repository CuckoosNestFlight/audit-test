# --- (În interiorul 'if uploaded_file:') ---
try:
    df = pd.read_excel(uploaded_file)
    
    # 1. PROTECȚIE: Curățare date (Manager-Proof)
    num_cols = ['Ore_Saptamana', 'Zile_Concediu', 'Idei_Noi', 'Erori_Asumate', 
                'Vechime_Rol', 'Ultima_Marire', 'Scor_Energie', 'Scor_Siguranta', 
                'Scor_Evolutie', 'Mod_Lucru', 'Presiune_Externa']
    
    for col in num_cols:
        if col in df.columns:
            # Transformă orice eroare de scriere în număr, erorile devin 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 2. VALIDARE: Verificăm dacă sunt scoruri "exotice" (ex: peste 10)
    if (df['Scor_Siguranta'] > 10).any():
        st.sidebar.error("❗ Date suspecte: Scoruri > 10 detectate la 'Siguranță'.")

    # 3. CALCUL ONA (Pre-calculăm conectivitatea pentru tab-ul 5)
    G_temp = nx.DiGraph()
    for _, r in df.iterrows():
        nume = str(r['Nume'])
        advisors = [a.strip() for a in str(r['Sfat_De_La']).split(',') if a.strip() in df['Nume'].values]
        for a in advisors: G_temp.add_edge(nume, a)
    
    # Conectivitate = Câți oameni cauți + Câți te caută
    df['ONA_Conn'] = df['Nume'].apply(lambda x: G_temp.in_degree(x) + G_temp.out_degree(x) if x in G_temp else 0)

    # ... restul calculelor tale ...

    # 4. INSIGHT NOU în TAB 5: Izolarea
    isolated_mask = df[(df['S_Diss'] > 2.5) & (df['ONA_Conn'] <= 1)]
    
    with tab5:
        if not isolated_mask.empty:
            st.error(f"⚠️ **Deconectare Totală (Izolare + Mască):** {', '.join(isolated_mask['Nume'].tolist())}")
            st.caption("Acești oameni declară că sunt OK, dar nu mai au nicio interacțiune de suport în rețea. Risc maxim de demisie silențioasă.")

except Exception as e:
    st.error(f"Fișierul are o problemă de formatare: {e}")
