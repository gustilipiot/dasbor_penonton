import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIG PAGE ---
st.set_page_config(
    page_title="Dashboard Rekapitulasi Penonton Bioskop KGPD",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Dashboard Rekapitulasi Penonton Bioskop KGPD")
st.markdown("Monitoring Performa Penonton, Time Series, serta Ranking Bioskop (Top & Bottom 10 Penonton & OR).")

# --- SIDEBAR: UPLOAD FILE ---
st.sidebar.header("📁 Upload File Excel")
uploaded_file = st.sidebar.file_uploader("Pilih file REKAPITULASI PENONTON KGPD 20261008.xlsx", type=["xlsx", "xls"])

# Fungsi pencari nama sheet yang fleksibel
def find_sheet(xls_obj, target_keywords):
    for sheet in xls_obj.sheet_names:
        clean_sheet = sheet.strip().lower()
        for kw in target_keywords:
            if kw.lower() in clean_sheet:
                return sheet
    return None

if uploaded_file is not None:
    xls = pd.ExcelFile(uploaded_file)
    
    # ---------------------------------------------------------
    # 1. SUMMARY TOTAL PENONTON (8 OKTOBER 2026)
    # ---------------------------------------------------------
    st.subheader("📌 Summary Jumlah Penonton (8 Oktober 2026)")
    
    summary_data = {
        "XXI": 47143,
        "IMAX": 6770,
        "CGV": 14668,
        "CINEPOLIS": 8821,
        "BIOSKOP LOCAL": 9107
    }
    grand_total = 90875

    # Metrics Row
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("GRAND TOTAL", f"{grand_total:,}")
    m2.metric("XXI", f"{summary_data['XXI']:,}")
    m3.metric("IMAX", f"{summary_data['IMAX']:,}")
    m4.metric("CGV", f"{summary_data['CGV']:,}")
    m5.metric("CINEPOLIS", f"{summary_data['CINEPOLIS']:,}")
    m6.metric("BIOSKOP LOCAL", f"{summary_data['BIOSKOP LOCAL']:,}")

    col_sum1, col_sum2 = st.columns([6, 4])
    
    df_summary = pd.DataFrame([
        {"Bioskop": "XXI", "Penonton": 47143},
        {"Bioskop": "IMAX", "Penonton": 6770},
        {"Bioskop": "CGV", "Penonton": 14668},
        {"Bioskop": "CINEPOLIS", "Penonton": 8821},
        {"Bioskop": "BIOSKOP LOCAL", "Penonton": 9107},
    ])
    
    with col_sum1:
        fig_bar_sum = px.bar(
            df_summary.sort_values(by="Penonton", ascending=True),
            x="Penonton",
            y="Bioskop",
            orientation="h",
            text_auto=",",
            title="Jumlah Penonton 8 Oktober 2026 per Jaringan",
            color="Penonton",
            color_continuous_scale="Reds"
        )
        fig_bar_sum.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig_bar_sum, use_container_width=True)
        
    with col_sum2:
        fig_pie_sum = px.pie(
            df_summary,
            values="Penonton",
            names="Bioskop",
            hole=0.4,
            title="Pangsa Pasar (Market Share %)",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_pie_sum.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie_sum.update_layout(height=380, showlegend=False)
        st.plotly_chart(fig_pie_sum, use_container_width=True)

    st.markdown("---")

    # ---------------------------------------------------------
    # 2. TIME SERIES CHART
    # ---------------------------------------------------------
    st.subheader("📈 Time Series Tren Jumlah Penonton Harian")
    
    # Cari sheet TOTAL secara aman
    sheet_total_name = find_sheet(xls, ['total'])
    if sheet_total_name:
        df_total_sheet = pd.read_excel(xls, sheet_name=sheet_total_name)
    else:
        df_total_sheet = pd.read_excel(xls, sheet_name=0)

    date_cols = [c for c in df_total_sheet.columns if 'OKTOBER' in str(c) or 'NOVEMBER' in str(c) or 'EARLY' in str(c)]
    
    df_ts_raw = df_total_sheet.iloc[0:27][['CINEMA'] + date_cols].copy()
    df_ts_raw['CINEMA'] = df_ts_raw['CINEMA'].astype(str).str.strip()
    
    df_ts_melt = df_ts_raw.melt(id_vars=['CINEMA'], var_name='Tanggal', value_name='Penonton')
    df_ts_melt['Penonton'] = pd.to_numeric(df_ts_melt['Penonton'], errors='coerce').fillna(0)
    df_ts_grouped = df_ts_melt[df_ts_melt['Penonton'] > 0]
    
    if not df_ts_grouped.empty:
        fig_ts = px.line(
            df_ts_grouped,
            x='Tanggal',
            y='Penonton',
            color='CINEMA',
            markers=True,
            title="Tren Penonton Harian per Jaringan Bioskop"
        )
        fig_ts.update_layout(height=420, xaxis_title="Tanggal", yaxis_title="Jumlah Penonton")
        st.plotly_chart(fig_ts, use_container_width=True)
    else:
        st.info("Data time series harian belum terisi penuh pada file rekap saat ini (Menampilkan data awal 8 Oktober 2026).")

    st.markdown("---")

    # Helper Function untuk Extract Data Bioskop secara aman
    def get_cinema_data(target_keywords, col_name_idx, col_aud_idx, col_or_idx=None, start_row=1):
        target_sheet = find_sheet(xls, target_keywords)
        if not target_sheet:
            return pd.DataFrame(columns=['Bioskop', 'Penonton', 'OR', 'OR_Pct'])
            
        df_s = pd.read_excel(xls, sheet_name=target_sheet)
        df_clean = df_s.iloc[start_row:].copy()
        cols = [df_s.columns[col_name_idx], df_s.columns[col_aud_idx]]
        if col_or_idx is not None:
            cols.append(df_s.columns[col_or_idx])
        
        df_clean = df_clean[cols].dropna(how='all')
        df_clean.columns = ['Bioskop', 'Penonton', 'OR'] if col_or_idx is not None else ['Bioskop', 'Penonton']
        df_clean['Bioskop'] = df_clean['Bioskop'].astype(str).str.strip()
        df_clean = df_clean[~df_clean['Bioskop'].str.upper().isin(['NAN', 'TOTAL', 'TOTAL IMAX', 'JUMLAH'])]
        df_clean['Penonton'] = pd.to_numeric(df_clean['Penonton'], errors='coerce').fillna(0)
        
        if col_or_idx is not None:
            df_clean['OR'] = pd.to_numeric(df_clean['OR'], errors='coerce').fillna(0)
            df_clean['OR_Pct'] = df_clean['OR'] * 100
        else:
            df_clean['OR'] = 0
            df_clean['OR_Pct'] = 0
            
        return df_clean

    df_xxi = get_cinema_data(['xxi'], 1, 6, 7, start_row=1)
    df_imax = get_cinema_data(['imax'], 1, 4, 5, start_row=1)
    df_cgv = get_cinema_data(['cgv'], 1, 6, None, start_row=1)
    df_cine = get_cinema_data(['cinepolis'], 2, 5, None, start_row=2)

    # ---------------------------------------------------------
    # 3. TOP 10 & BOTTOM 10 PENONTON
    # ---------------------------------------------------------
    st.subheader("📊 Ranking Bioskop Berdasarkan Jumlah Penonton")
    
    tab_top_aud, tab_bot_aud = st.tabs(["🏆 Top 10 Penonton Tertinggi", "🔻 Top 10 Penonton Terendah"])

    with tab_top_aud:
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            fig_xxi = px.bar(df_xxi.sort_values('Penonton', ascending=False).head(10).sort_values('Penonton'), x='Penonton', y='Bioskop', orientation='h', text_auto=',', title="Top 10 XXI - Penonton Tertinggi", color_discrete_sequence=['#1f77b4'])
            st.plotly_chart(fig_xxi, use_container_width=True)
            
            fig_cgv = px.bar(df_cgv.sort_values('Penonton', ascending=False).head(10).sort_values('Penonton'), x='Penonton', y='Bioskop', orientation='h', text_auto=',', title="Top 10 CGV - Penonton Tertinggi", color_discrete_sequence=['#2ca02c'])
            st.plotly_chart(fig_cgv, use_container_width=True)

        with col_t2:
            fig_imax = px.bar(df_imax.sort_values('Penonton', ascending=False).head(10).sort_values('Penonton'), x='Penonton', y='Bioskop', orientation='h', text_auto=',', title="Top 10 IMAX - Penonton Tertinggi", color_discrete_sequence=['#ff7f0e'])
            st.plotly_chart(fig_imax, use_container_width=True)
            
            fig_cine = px.bar(df_cine.sort_values('Penonton', ascending=False).head(10).sort_values('Penonton'), x='Penonton', y='Bioskop', orientation='h', text_auto=',', title="Top 10 CINEPOLIS - Penonton Tertinggi", color_discrete_sequence=['#d62728'])
            st.plotly_chart(fig_cine, use_container_width=True)

    with tab_bot_aud:
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            df_xxi_bot = df_xxi[df_xxi['Penonton'] > 0].sort_values('Penonton', ascending=True).head(10).sort_values('Penonton', ascending=False)
            fig_xxi_bot = px.bar(df_xxi_bot, x='Penonton', y='Bioskop', orientation='h', text_auto=',', title="Top 10 XXI - Penonton Terendah (>0)", color_discrete_sequence=['#aec7e8'])
            st.plotly_chart(fig_xxi_bot, use_container_width=True)
            
            df_cgv_bot = df_cgv[df_cgv['Penonton'] > 0].sort_values('Penonton', ascending=True).head(10).sort_values('Penonton', ascending=False)
            fig_cgv_bot = px.bar(df_cgv_bot, x='Penonton', y='Bioskop', orientation='h', text_auto=',', title="Top 10 CGV - Penonton Terendah (>0)", color_discrete_sequence=['#98df8a'])
            st.plotly_chart(fig_cgv_bot, use_container_width=True)

        with col_b2:
            df_imax_bot = df_imax[df_imax['Penonton'] > 0].sort_values('Penonton', ascending=True).head(10).sort_values('Penonton', ascending=False)
            fig_imax_bot = px.bar(df_imax_bot, x='Penonton', y='Bioskop', orientation='h', text_auto=',', title="Top 10 IMAX - Penonton Terendah (>0)", color_discrete_sequence=['#ffbb78'])
            st.plotly_chart(fig_imax_bot, use_container_width=True)
            
            df_cine_bot = df_cine[df_cine['Penonton'] > 0].sort_values('Penonton', ascending=True).head(10).sort_values('Penonton', ascending=False)
            fig_cine_bot = px.bar(df_cine_bot, x='Penonton', y='Bioskop', orientation='h', text_auto=',', title="Top 10 CINEPOLIS - Penonton Terendah (>0)", color_discrete_sequence=['#ff9896'])
            st.plotly_chart(fig_cine_bot, use_container_width=True)

    st.markdown("---")

    # ---------------------------------------------------------
    # 4. TOP 10 & BOTTOM 10 OCCUPANCY RATE (OR)
    # ---------------------------------------------------------
    st.subheader("🔥 Ranking Bioskop Berdasarkan Occupancy Rate (OR)")
    
    tab_top_or, tab_bot_or = st.tabs(["🏆 Top 10 OR Tertinggi", "🔻 Top 10 OR Terendah"])

    with tab_top_or:
        col_or1, col_or2 = st.columns(2)
        with col_or1:
            df_xxi_top_or = df_xxi.sort_values('OR', ascending=False).head(10).sort_values('OR')
            fig_xxi_or = px.bar(
                df_xxi_top_or, x='OR_Pct', y='Bioskop', orientation='h', 
                text=df_xxi_top_or['OR_Pct'].map('{:.1f}%'.format),
                title="Top 10 XXI - OR Tertinggi (%)", color_discrete_sequence=['#17becf']
            )
            st.plotly_chart(fig_xxi_or, use_container_width=True)

        with col_or2:
            df_imax_top_or = df_imax.sort_values('OR', ascending=False).head(10).sort_values('OR')
            fig_imax_or = px.bar(
                df_imax_top_or, x='OR_Pct', y='Bioskop', orientation='h', 
                text=df_imax_top_or['OR_Pct'].map('{:.1f}%'.format),
                title="Top 10 IMAX - OR Tertinggi (%)", color_discrete_sequence=['#9467bd']
            )
            st.plotly_chart(fig_imax_or, use_container_width=True)

    with tab_bot_or:
        col_bor1, col_bor2 = st.columns(2)
        with col_bor1:
            df_xxi_bot_or = df_xxi[df_xxi['OR'] > 0].sort_values('OR', ascending=True).head(10).sort_values('OR', ascending=False)
            fig_xxi_bot_or = px.bar(
                df_xxi_bot_or, x='OR_Pct', y='Bioskop', orientation='h', 
                text=df_xxi_bot_or['OR_Pct'].map('{:.1f}%'.format),
                title="Top 10 XXI - OR Terendah (>0%)", color_discrete_sequence=['#9edae5']
            )
            st.plotly_chart(fig_xxi_bot_or, use_container_width=True)

        with col_bor2:
            df_imax_bot_or = df_imax[df_imax['OR'] > 0].sort_values('OR', ascending=True).head(10).sort_values('OR', ascending=False)
            fig_imax_bot_or = px.bar(
                df_imax_bot_or, x='OR_Pct', y='Bioskop', orientation='h', 
                text=df_imax_bot_or['OR_Pct'].map('{:.1f}%'.format),
                title="Top 10 IMAX - OR Terendah (>0%)", color_discrete_sequence=['#c5b0d5']
            )
            st.plotly_chart(fig_imax_bot_or, use_container_width=True)

else:
    st.info("👋 Silakan unggah file Excel **REKAPITULASI PENONTON KGPD 20261008.xlsx** pada sidebar di sebelah kiri.")