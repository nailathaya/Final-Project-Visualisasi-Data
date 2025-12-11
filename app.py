import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import folium
from streamlit_folium import st_folium
import json
import plotly.express as px
from shapely.geometry import mapping

BASE = "/content/drive/MyDrive/Data Visualisation Competition 2025"  
PATH_LEVEL1 = f"{BASE}/data/level_1/Level_1.xlsx"
PATH_LEVEL3 = f"{BASE}/data/level_3/Level_3.xlsx"
PATH_LOOKUPS = f"{BASE}/lookups/lookups.xlsx"
PATH_SHAPE = f"{BASE}/shapefile/small_areas_british_grid.shp"

st.set_page_config(layout="wide", page_title="Co-Benefits Visualisation", initial_sidebar_state="expanded")

@st.cache_data
def load_level1(path=PATH_LEVEL1):
    return pd.read_excel(path)

@st.cache_data
def load_level3(path=PATH_LEVEL3):
    return pd.read_excel(path)

@st.cache_data
def load_lookups(path=PATH_LOOKUPS):
    return pd.read_excel(path)

@st.cache_data
def load_shapefile(path=PATH_SHAPE):
    return gpd.read_file(path)

# Safe year columns detection (int or numeric-strings)
def detect_year_cols(df, start=2025, end=2050):
    cols = []
    for c in df.columns:
        try:
            if isinstance(c, int):
                y = c
            else:
                s = str(c).strip()
                if s.isdigit():
                    y = int(s)
                else:
                    continue
            if start <= y <= end:
                cols.append(c)
        except Exception:
            continue
    # sort by numeric year value
    cols_sorted = sorted(cols, key=lambda x: int(str(x)))
    return cols_sorted

st.sidebar.title("Data & Settings")
st.sidebar.write("Memuat data — tunggu sebentar...")

level_1 = load_level1()
level_3 = load_level3()
lookups = load_lookups()
gdf = load_shapefile()

st.sidebar.success("Data loaded")

st.sidebar.header("Visual settings")
map_mode = st.sidebar.selectbox("Map mode", ["Total (level_1)", "Per year (level_3)"])
year_cols = detect_year_cols(level_3)
selected_year = None
if map_mode == "Per year (level_3)":
    if year_cols:
        # convert to int labels for slider
        years_int = [int(str(y)) for y in year_cols]
        selected_year = st.sidebar.select_slider("Select year for map", options=years_int, value=years_int[0])
    else:
        st.sidebar.error("No year columns detected in level_3")

show_pop_bubbles = st.sidebar.checkbox("Show population bubbles (map)", value=True)
bubble_max_radius = st.sidebar.slider("Bubble max radius", min_value=1, max_value=50, value=8)

# scatter settings
st.sidebar.markdown("---")
st.sidebar.write("Scatter settings")
region_col = st.sidebar.selectbox("Region column for coloring (lookups)", options=["local_authority", "nation"], index=0)

# line chart settings
st.sidebar.markdown("---")
st.sidebar.write("Line chart settings")
line_smooth = st.sidebar.checkbox("Apply 3-yr rolling mean (line chart)", value=False)

# prepare choropleth base (level_1)
level_1_copy = level_1.copy()
if 'road_safety' in level_1_copy.columns and 'congestion' in level_1_copy.columns:
    level_1_copy['total_benefit'] = level_1_copy['road_safety'] + level_1_copy['congestion']
else:
    level_1_copy['total_benefit'] = level_1_copy.get('sum', 0)  # fallback

# Merge shapefile with level_1 data for mapping by default
gdf_merged_base = gdf.merge(level_1_copy[['small_area', 'total_benefit', 'road_safety', 'congestion']],
                            on='small_area', how='left')

# Prepare lookup merge for scatter
lookups_small = lookups.copy()
# ensure population numeric
if 'population' in lookups_small.columns:
    lookups_small['population'] = pd.to_numeric(lookups_small['population'], errors='coerce')
else:
    lookups_small['population'] = np.nan

scatter_df = level_1_copy[['small_area', 'road_safety', 'congestion']].merge(
    lookups_small[['small_area', 'population', region_col]], on='small_area', how='left'
).dropna(subset=['population'])

# Prepare line chart aggregates from level_3
year_columns = detect_year_cols(level_3)
# Filter pathways
cong_df = level_3[
    (level_3['co-benefit_type'] == 'congestion') &
    (level_3['damage_pathway'].str.lower() == 'time_saved')
] if 'damage_pathway' in level_3.columns else level_3[level_3['co-benefit_type'] == 'congestion']

rs_df = level_3[
    (level_3['co-benefit_type'] == 'road_safety') &
    (level_3['damage_pathway'].str.lower().isin(['reduced_mortality', 'society']))
] if 'damage_pathway' in level_3.columns else level_3[level_3['co-benefit_type'] == 'road_safety']

# if lowercase mismatch, attempt case-insensitive fallback
if cong_df.shape[0] == 0 and 'damage_pathway' in level_3.columns:
    cong_df = level_3[
        (level_3['co-benefit_type'] == 'congestion') &
        (level_3['damage_pathway'].str.lower().str.replace(" ", "_") == 'time_saved')
    ]

if rs_df.shape[0] == 0 and 'damage_pathway' in level_3.columns:
    rs_df = level_3[
        (level_3['co-benefit_type'] == 'road_safety') &
        (level_3['damage_pathway'].str.lower().isin(['reduced_mortality', 'society']))
    ]

# Sum across small areas
if year_columns:
    cong_yearly = cong_df[year_columns].sum(numeric_only=True)
    rs_yearly = rs_df[year_columns].sum(numeric_only=True)
    # ensure ordering and convert index to ints for plotting
    years_plot = [int(str(x)) for x in cong_yearly.index]
else:
    cong_yearly = pd.Series(dtype=float)
    rs_yearly = pd.Series(dtype=float)
    years_plot = []

st.title("Co-Benefits Visualisation — Road Safety & Congestion")
st.markdown("Interaktif: peta choropleth, scatter hubungan, dan tren 2025–2050. Sesuaikan di sidebar.")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Choropleth Map — Where Climate Action Saves Time & Lives")

    if map_mode == "Total (level_1)":
        # Create folium map centered on UK
        m = folium.Map(location=[54.0, -2.0], zoom_start=5, tiles="cartodbpositron")
        # convert GeoDataFrame to GeoJSON
        gjson = json.loads(gdf_merged_base.to_json())

        # create choropleth
        folium.Choropleth(
            geo_data=gjson,
            name="Total co-benefit",
            data=gdf_merged_base,
            columns=["small_area", "total_benefit"],
            key_on="feature.properties.small_area",
            fill_color="YlGnBu",
            nan_fill_color="white",
            fill_opacity=0.8,
            line_opacity=0.1,
            legend_name="Total benefit (road_safety + congestion)"
        ).add_to(m)

        # optional population bubbles
        if show_pop_bubbles and 'population' in lookups_small.columns:
            # attach centroids for bubbles (req
