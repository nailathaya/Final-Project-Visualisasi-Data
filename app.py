import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import json

st.set_page_config(
    page_title="Dashboard Aksi Iklim 2025-2050",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 100%;
        }
        h1 { font-family: 'Helvetica Neue', sans-serif; font-size: 2.2rem; margin-bottom: 0; color: #003366; }
        h2 { font-family: 'Helvetica Neue', sans-serif; font-size: 1.5rem; margin-top: 0; color: #2E86AB; }
        h3 { font-size: 1.1rem; color: #444; margin-bottom: 5px; }
        p, div { font-family: 'Segoe UI', sans-serif; font-size: 0.9rem; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    base_path = "/Users/HilalAbyan/Final-Project-Visualisasi-Data/Data Visualisation Competition 2025/"
    path_level1 = f"{base_path}/data/level_1/Level_1.parquet"
    path_level3 = f"{base_path}/data/level_3/level3_road_cong.parquet"
    path_lookups = f"{base_path}/lookups/lookups.parquet"
    path_shape = f"{base_path}shapefile/small_areas_british_grid.parquet"
    
    l1 = pd.read_parquet(path_level1)
    l3 = pd.read_parquet(path_level3)
    look = pd.read_parquet(path_lookups)
    gdf = gpd.read_parquet(path_shape)
    
    return l1, l3, look, gdf

try:
    level_1, df, look, gdf = load_data()
    years = [str(y) for y in range(2025, 2051)]
except Exception as e:
    st.error(f"Gagal memuat data. Pastikan path file benar. Error: {e}")
    st.stop()

for y in years:
    if y in df.columns:
        df[y] = pd.to_numeric(df[y], errors='coerce').fillna(0)

cong_series = df[df['co-benefit_type'] == 'congestion'][years].sum()
safe_series = df[df['co-benefit_type'] == 'road_safety'][years].sum()

df_line = pd.DataFrame({
    'Year': years,
    'Congestion': cong_series.values,
    'Road Safety': safe_series.values
})
df_line['Cumulative_Congestion'] = df_line['Congestion'].cumsum()
df_line['Cumulative_Safety'] = df_line['Road Safety'].cumsum()

totals = df.groupby('co-benefit_type')['sum'].sum().abs()
total_cong = totals['congestion']
total_safe = totals['road_safety']

mortality_data = df[df['damage_pathway'] == 'reduced_mortality'][years].sum()

df['total_value'] = df[years].sum(axis=1)
grouped_area = df.groupby(['small_area', 'co-benefit_type'])['total_value'].sum().unstack().reset_index()
if 'congestion' not in grouped_area.columns: grouped_area['congestion'] = 0
if 'road_safety' not in grouped_area.columns: grouped_area['road_safety'] = 0

df['sum'] = pd.to_numeric(df['sum'], errors='coerce')
pathways_data = df.groupby(['damage_pathway', 'damage_type'])['sum'].sum().abs().reset_index()
pathways_data.columns = ['Damage Pathway', 'Type', 'Total Value']

pathway_labels = {
    'time_saved': 'Time Saved',
    'reduced_mortality': 'Reduced Mortality',
    'society': 'Society'
}
pathways_data['Pathway Label'] = pathways_data['Damage Pathway'].map(pathway_labels)

agg_l3 = df.groupby('small_area')['total_value'].sum().reset_index()
map_df = gdf.merge(agg_l3, on='small_area', how='left')

c_head1, c_head2 = st.columns([3, 1])
with c_head1:
    st.markdown("<h1>AKSI IKLIM: Dampak Multidimensional terhadap Efisiensi Waktu dan Keselamatan Jiwa</h1>", unsafe_allow_html=True)
    st.markdown("**Intervensi transportasi berkelanjutan merupakan bentuk investasi sosial-ekonomi jangka panjang.** Dashboard ini menyajikan analisis dampak kebijakan kota hijau terhadap peningkatan efisiensi sistem transportasi dan keselamatan masyarakat pada periode 2025–2050.")

with c_head2:
    st.markdown("""
    <div style="text-align: right; color: gray;">
        <b>Dashboard Pemantauan Dampak Kebijakan</b><br>
        Fokus Analisis: Efisiensi Sistem dan Keselamatan Publik<br>
        <i>Pembaruan Terakhir: Desember 2024</i>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

left_panel, right_panel = st.columns([3, 1.3])

with left_panel:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Manfaat Ekonomi Kumulatif Jangka Panjang")
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=df_line['Year'], y=df_line['Cumulative_Congestion'], name='Penghematan Kemacetan',
                                    line=dict(color='#2E86AB', width=3)))
        fig_line.add_trace(go.Scatter(x=df_line['Year'], y=df_line['Cumulative_Safety'], name='Manfaat Keselamatan',
                                    line=dict(color='#2ca02c', width=3)))
        
        fig_line.update_layout(
            title="<b>Investasi Jangka Panjang dengan Manfaat Ekonomi Berkelanjutan</b>",
            xaxis_title="Tahun", yaxis_title="Nilai Ekonomi Akumulatif (£)",
            margin=dict(l=0, r=0, t=30, b=0), height=275,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.6,
            ), template="plotly_white"
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with col2:
        st.markdown("### Dominasi Efisiensi Waktu")
        labels = ['Pengurangan Kemacetan', 'Peningkatan Keselamatan']
        values = [total_cong, total_safe]
        colors = ['#2E86AB', '#E94F37']
        
        fig_donut = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.6, marker_colors=colors)])
        fig_donut.update_layout(
            title="<b>Proporsi Kontribusi Manfaat Ekonomi</b>",
            margin=dict(l=20, r=20, t=30, b=0), height=250,
            annotations=[dict(text='<b>Total <br>Manfaat</b>', x=0.5, y=0.5, font_size=14, showarrow=False)],
            showlegend=True, legend=dict(orientation="h", y=-0.1)
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    col3, col4 = st.columns([1, 2])

    with col3:
        st.markdown("### Periode Manfaat")
        key_years = ['2025', '2030', '2035', '2040']
        key_vals = [mortality_data.get(y, 0) for y in key_years]
        
        max_val_pic = max(key_vals) if max(key_vals) > 0 else 1
        norms = [int((v/max_val_pic)*8) for v in key_vals]
        
        fig_pic = go.Figure()
        for i, (yr, val, n) in enumerate(zip(key_years, key_vals, norms)):
            icons = "👤" * max(1, n)
            fig_pic.add_trace(go.Bar(
                y=[yr], x=[val], orientation='h',
                text=f"{icons} {val:.1f} Jiwa", textposition='auto',
                marker_color=['#a8ddb5', '#7bccc4', '#43a2ca', '#0868ac'][i]
            ))
        
        fig_pic.update_layout(
            title="<b>Periode Kritis (2025–2035)</b>",
            xaxis_visible=False, yaxis=dict(title="Tahun", type='category'),
            margin=dict(l=0, r=0, t=30, b=0), height=220, showlegend=False, template="plotly_white"
        )
        st.plotly_chart(fig_pic, use_container_width=True)

    with col4:
        st.markdown("### Tren Dampak Kebijakan terhadap Keselamatan Jiwa")
        fig_mix = go.Figure()
        fig_mix.add_trace(go.Bar(
            x=years, y=mortality_data.values,
            name='Nyawa Terselamatkan', marker_color='#E94F37', opacity=0.6
        ))
        fig_mix.add_trace(go.Scatter(
            x=years, y=mortality_data.values,
            name='Trend', line=dict(color='#c0392b', width=4, shape='spline')
        ))
        
        peak_year = mortality_data.idxmax()
        peak_val = mortality_data.max()

        fig_mix.update_layout(
            title=f"<b>Puncak Efektivitas Intervensi: Tahun {peak_year}</b>",
            yaxis_title="Jumlah Jiwa / Tahun",
            margin=dict(l=0, r=0, t=30, b=0), height=220, showlegend=False, template="plotly_white"
        )
        st.plotly_chart(fig_mix, use_container_width=True)

    col5, col6 = st.columns(2)

    with col5:
        st.markdown("### Sinergi Manfaat")
        fig_scat = px.scatter(grouped_area, x='road_safety', y='congestion', 
                            labels={'road_safety': 'Safety Benefit (£)', 'congestion': 'Congestion Benefit (£)'},
                            title="<b>Jalan Lancar Menghasilkan Jalan Aman</b>",
                            trendline="ols", trendline_color_override="darkblue")
        fig_scat.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=200, template="plotly_white")
        st.plotly_chart(fig_scat, use_container_width=True)

    with col6:
        st.markdown("### Rincian Jalur Dampak Kebijakan")
        fig_polar = px.bar_polar(
            pathways_data, 
            r="Total Value", 
            theta="Pathway Label", 
            color="Type",
            color_discrete_map={'health': '#E94F37', 'non-health': '#2E86AB', 'health benefits': '#E94F37'},
            template="plotly_white",
            title="<b>Sumber Keuntungan</b>"
        )
        
        fig_polar.update_layout(
            height=250,
            margin=dict(l=30, r=30, t=30, b=0),
            legend=dict(orientation="h", y=-0.2),
            polar=dict(
                radialaxis=dict(visible=True, showticklabels=False),
                angularaxis=dict(direction="clockwise")
            )
        )
        st.plotly_chart(fig_polar, use_container_width=True)

with right_panel:
    st.markdown("### Distribusi Geografis Dampak Kebijakan di Wilayah Britania Raya")
    
    if not map_df.empty:        
        fig_map = px.choropleth_mapbox(
            map_df,
            geojson=map_df.geometry,
            locations=map_df.index,
            color='total_value',
            color_continuous_scale='Bluered',
            range_color=[map_df['total_value'].min(), map_df['total_value'].max()],
            mapbox_style="carto-positron",
            zoom=4.8, 
            center={"lat": 54.0, "lon": -2.5},
            opacity=0.7,
            labels={'total_value': 'Benefit (£)'}
        )
        
        fig_map.update_layout(
            height=850, 
            margin=dict(l=0, r=0, t=0, b=0),
            coloraxis_showscale=True,
            coloraxis_colorbar=dict(
                title="Total Benefit",
                title_font=dict(color="black", size=14),
                tickfont=dict(color="black", size=12),
                thicknessmode="pixels", thickness=15,
                lenmode="fraction", len=0.7,
                yanchor="top", y=1,
                xanchor="left", x=0
            )
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("Data spasial tidak tersedia.")

st.markdown("---")
st.markdown("""
<div style="text-align: center; font-size: 0.9rem; color: #555;">
    <b>Kesimpulan:</b> Penerapan kebijakan transportasi berkelanjutan berkontribusi signifikan terhadap peningkatan kualitas hidup masyarakat melalui efisiensi sistem dan perlindungan keselamatan jiwa. 
    <br><i>Sumber Data: Analisis Proyeksi Transportasi Periode 2025–2050.</i>
</div>
""", unsafe_allow_html=True)