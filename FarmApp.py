import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# -------------------------------
# Page settings
# -------------------------------
st.set_page_config(page_title="Rice Polygon Viewer", layout="wide")

st.title("🌾 Rice Polygon Web App (FID / District Based)")

# -------------------------------
# Load Shapefile
# -------------------------------
@st.cache_data
def load_data():
    shp_path = Path("newRicecluster") / "newRice_cluster.shp"
    gdf = gpd.read_file(shp_path)
    gdf = gdf.to_crs(epsg=4326)   # for folium
    return gdf

gdf = load_data()

# # -------------------------------
# # Sidebar Inputs
# # -------------------------------
st.sidebar.header("🔍 Filter Options")

# District dropdown
districts = sorted(gdf["district"].unique())
district = st.sidebar.selectbox("Select District", districts)

# Filter by district
district_gdf = gdf[gdf["district"] == district]

# FID input
fid = st.sidebar.number_input(
    "Enter Farmer plot_code",
    min_value=int(district_gdf["plot_code"].min()),
    max_value=int(district_gdf["plot_code"].max()),
    step=1
)

# -------------------------------
# Filter Polygon
# -------------------------------
selected_poly = district_gdf[district_gdf["plot_code"] == fid]

if selected_poly.empty:
    st.warning("❌ No polygon found for this Farmer plot_code")
    st.stop()

# -------------------------------
# Area calculation (Acre)
# -------------------------------
selected_poly_utm = selected_poly.to_crs(epsg=32644)  # UTM zone India
area_acre = selected_poly_utm.geometry.area.iloc[0] * 0.000247105

# -------------------------------
# Show Attributes
# -------------------------------
st.subheader("📋 Polygon Details")

col1, col2 = st.columns(2)

# with col1:
#     st.write(selected_poly.drop(columns="geometry"))

with col1:
    st.metric("Polygon Area (Acre)", round(area_acre, 2))


def get_color(feature):
    cate = feature["properties"].get("Categry", "Mixed")
    if cate == "Basmati":
        return "green"
    elif cate == "Non basmati":
        return "orange"
    else:
        return "red"


# -------------------------------
# Map Visualization
# -------------------------------
st.subheader("🗺️ Polygon Map")

# Safe centroid
centroid = selected_poly.to_crs(epsg=32644).geometry.centroid.to_crs(epsg=4326).iloc[0]

m = folium.Map(
    location=[centroid.y, centroid.x],
    zoom_start=16,
    tiles=None
)

# Street map
folium.TileLayer(
    "OpenStreetMap",
    name="Street Map",
    control=True
).add_to(m)

# Satellite map
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri",
    name="Satellite",
    overlay=False,
    control=True
).add_to(m)

# Ensure area column exists
selected_poly["Area_acres"] = round(area_acre, 2)

# Polygon layer
folium.GeoJson(
    selected_poly,
    style_function=lambda feature: {
        "fillColor": get_color(feature),
        "color": "black",
        "weight": 2,
        "fillOpacity": 0.6,
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["plot_code", "district", "Categry", "Area_acres"],
        aliases=["Farmer plot_code", "District", "Category", "Area (Acre)"],
        localize=True
    )
).add_to(m)

folium.LayerControl().add_to(m)


# Legend
legend_html = """
<div style="
position: fixed;
bottom: 50px;
left: 50px;
width: 180px;
background-color: white;
border: 2px solid black;
z-index: 9999;
font-size: 14px;
padding: 10px;
">
<b>Rice Category</b><br><br>
<span style="color:green;">&#9632;</span> Basmati<br>
<span style="color:orange;">&#9632;</span> Non basmati<br>
<span style="color:red;">&#9632;</span> Mixed
</div>
"""

m.get_root().html.add_child(folium.Element(legend_html))

st_folium(m, width=1100, height=500)
