import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
from folium.plugins import Search
from folium.plugins import MarkerCluster, HeatMap, MiniMap, Draw, LocateControl, Fullscreen, MousePosition
from folium import FeatureGroup, GeoJson, TopoJson
from folium.plugins import MarkerCluster
import io
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import base64
from branca.element import Figure, MacroElement
from jinja2 import Template
import json
from datetime import datetime


# Set page title and layout
st.set_page_config(page_title="Sistem Informasi Manajemen Frekuensi", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 1px 1px 2px #ccc;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #0277BD;
        margin-top: 1rem;
        border-bottom: 1px solid #f0f0f0;
        padding-bottom: 0.5rem;
    }
    .info-box {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #1E88E5;
        margin-bottom: 1rem;
    }
    .warning-box {
        background-color: #FFF8E1;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #FFC107;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #4CAF50;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        text-align: center;
    }
    .legend-item {
        display: flex;
        align-items: center;
        margin-bottom: 5px;
    }
    .legend-color {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        margin-right: 10px;
    }
    .footer {
        text-align: center;
        margin-top: 3rem;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 5px;
    }
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* Make the tabs more visible */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 4px 4px 0 0;
    }
    /* Improve filter section appearance */
    .filter-container {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    /* Style upload widget */
    .upload-container {
        background-color: #f1f8ff;
        padding: 20px;
        border-radius: 5px;
        border: 1px dashed #1E88E5;
        margin-bottom: 20px;
    }
    /* Progress indicator */
    .stProgress > div > div > div > div {
        background-color: #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# Header with custom styling
st.markdown('<p class="main-header">📡 Sistem Informasi Manajemen Frekuensi</p>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem;">Aplikasi untuk mengelola dan memvisualisasikan data frekuensi beserta lokasi pengguna</p>', unsafe_allow_html=True)

# Function to create custom icon based on service type
def get_service_icon(service):
    """Return custom icon based on service type with improved mapping"""
    icon_map = {
        'Broadcasting': {'icon': 'tower-broadcast', 'color': '#E53935'},  # Red
        'Mobile': {'icon': 'signal', 'color': '#43A047'},                # Green
        'Cellular': {'icon': 'tower-cell', 'color': '#1E88E5'},          # Blue
        'Satellite': {'icon': 'satellite-dish', 'color': '#8E24AA'},     # Purple
        'Microwave': {'icon': 'wifi', 'color': '#FB8C00'},               # Orange
        'Radio': {'icon': 'radio', 'color': '#FFB300'},                  # Amber
        'TV': {'icon': 'tv', 'color': '#546E7A'},                        # Blue Grey
        'Amateur': {'icon': 'walkie-talkie', 'color': '#6D4C41'},        # Brown
        'Maritime': {'icon': 'ship', 'color': '#00ACC1'},                # Cyan
        'Aviation': {'icon': 'plane', 'color': '#7CB342'},               # Light Green
        'Fixed': {'icon': 'broadcast-tower', 'color': '#5E35B1'},        # Deep Purple
        'Radar': {'icon': 'satellite', 'color': '#F4511E'}               # Deep Orange
    }
    
    # Default to signal icon if service not in map
    if service in icon_map:
        return icon_map[service]
    else:
        return {'icon': 'signal', 'color': '#757575'}  # Grey

# Function to convert frequency to band
def get_frequency_band(freq):
    """Identify frequency band based on MHz value"""
    if pd.isna(freq):
        return "Unknown"
    
    if freq < 30:
        return "HF (3-30 MHz)"
    elif freq < 300:
        return "VHF (30-300 MHz)"
    elif freq < 3000:
        return "UHF (300-3000 MHz)"
    elif freq < 30000:
        return "SHF (3-30 GHz)"
    elif freq < 300000:
        return "EHF (30-300 GHz)"
    else:
        return "THF (>300 GHz)"

# Function to create a beautified popup with antenna icon
def create_popup_content(row):
    """Create enhanced HTML popup with antenna icon and improved styling"""
    
    # Build additional fields if they exist in the dataframe
    additional_fields = ""
    
    # Check for frequency info and determine band
    freq_band = ""
    if 'FREQ_MHZ' in row and not pd.isna(row['FREQ_MHZ']):
        band = get_frequency_band(row['FREQ_MHZ'])
        freq_band = f"""
        <tr>
            <td style="padding: 5px; font-weight: bold;"><i class="fa fa-broadcast-tower"></i> Frekuensi:</td>
            <td style="padding: 5px;">{row['FREQ_MHZ']} MHz <span class="band-tag" style="background-color: #E1F5FE; padding: 2px 5px; border-radius: 3px; font-size: 0.8em; margin-left: 5px;">{band}</span></td>
        </tr>
        """
        additional_fields += freq_band
    
    # Check for bandwidth info
    if 'BW_MHZ' in row and not pd.isna(row['BW_MHZ']):
        additional_fields += f"""
        <tr>
            <td style="padding: 5px; font-weight: bold;"><i class="fa fa-arrows-alt-h"></i> Bandwidth:</td>
            <td style="padding: 5px;">{row['BW_MHZ']} MHz</td>
        </tr>
        """
    
    # Add date information if available
    if 'DATE' in row and not pd.isna(row['DATE']):
        try:
            date_str = pd.to_datetime(row['DATE']).strftime('%d %b %Y')
            additional_fields += f"""
            <tr>
                <td style="padding: 5px; font-weight: bold;"><i class="fa fa-calendar-alt"></i> Tanggal:</td>
                <td style="padding: 5px;">{date_str}</td>
            </tr>
            """
        except:
            pass
    
    # Service icon
    service_info = get_service_icon(row['SERVICE'])
    icon_name = service_info['icon']
    icon_color = service_info['color']
    
    # Create a beautified popup with antenna icon
    popup_html = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; min-width: 300px; max-width: 350px; border-radius: 5px;">
        <div style="background-color: {icon_color}; color: white; padding: 10px; border-radius: 5px 5px 0 0; display: flex; align-items: center;">
            <div style="background-color: rgba(255,255,255,0.2); width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 10px;">
                <i class="fa fa-{icon_name}" style="font-size: 20px;"></i>
            </div>
            <div>
                <div style="font-size: 1.2em; font-weight: bold;">{row['STN_NAME']}</div>
                <div style="font-size: 0.9em; opacity: 0.9;">{row['SERVICE']} · {row['SUBSERVICE']}</div>
            </div>
        </div>
        <div style="padding: 15px; background-color: white; border-radius: 0 0 5px 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 5px; font-weight: bold;"><i class="fa fa-building"></i> Klien:</td>
                    <td style="padding: 5px;">{row['CLNT_NAME']}</td>
                </tr>
                <tr>
                    <td style="padding: 5px; font-weight: bold;"><i class="fa fa-map-marker-alt"></i> Kota:</td>
                    <td style="padding: 5px;">{row['CITY']}</td>
                </tr>
                {additional_fields}
                <tr>
                    <td style="padding: 5px; font-weight: bold;"><i class="fa fa-location-arrow"></i> Koordinat:</td>
                    <td style="padding: 5px;">
                        <span style="font-family: monospace;">{row['SID_LAT']:.6f}, {row['SID_LONG']:.6f}</span>
                        <a href="https://www.google.com/maps/search/?api=1&query={row['SID_LAT']},{row['SID_LONG']}" target="_blank" style="margin-left: 5px; color: #1E88E5;">
                            <i class="fa fa-external-link-alt"></i>
                        </a>
                    </td>
                </tr>
            </table>
        </div>
    </div>
    """
    return popup_html

# Function to validate uploaded CSV data
def validate_csv_data(df):
    """Validate the uploaded CSV data to ensure it has the required columns"""
    required_columns = ['CITY', 'CLNT_NAME', 'STN_NAME', 'SERVICE', 'SUBSERVICE', 'SID_LAT', 'SID_LONG']
    optional_columns = ['FREQ_MHZ', 'BW_MHZ', 'DATE', 'TX_POWER', 'ANTENNA_HEIGHT', 'POLARIZATION']
    
    # Check for required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        return False, f"Kolom yang diperlukan tidak ditemukan: {', '.join(missing_columns)}"
    
    # Check coordinate data
    if df['SID_LAT'].isnull().any() or df['SID_LONG'].isnull().any():
        return False, "Beberapa baris memiliki koordinat latitude/longitude yang kosong."
    
    # Check if latitude is within valid range (-90 to 90)
    if (df['SID_LAT'] < -90).any() or (df['SID_LAT'] > 90).any():
        return False, "Beberapa nilai latitude berada di luar kisaran yang valid (-90 hingga 90)."
    
    # Check if longitude is within valid range (-180 to 180)
    if (df['SID_LONG'] < -180).any() or (df['SID_LONG'] > 180).any():
        return False, "Beberapa nilai longitude berada di luar kisaran yang valid (-180 hingga 180)."
    
    # Add warning for optional columns
    warnings = []
    missing_optional = [col for col in optional_columns if col not in df.columns]
    if missing_optional:
        warnings.append(f"Kolom opsional tidak ditemukan: {', '.join(missing_optional)}")
    
    return True, warnings

# Function to optimize map performance for large datasets
def optimize_map_data(df, max_markers, sampling_method="random"):
    """Optimize the dataframe for map display to handle large datasets"""
    if len(df) <= max_markers:
        return df
    
    if sampling_method == "random":
        # Simple random sampling
        return df.sample(max_markers, random_state=42)
    
    elif sampling_method == "cluster":
        # K-means clustering to get representative points
        # This is a simplified implementation - for real applications, 
        # consider using scikit-learn for more advanced clustering
        from sklearn.cluster import KMeans
        
        # Extract coordinates for clustering
        coords = df[['SID_LAT', 'SID_LONG']].values
        
        # Determine number of clusters (max_markers or less)
        n_clusters = min(max_markers, len(df))
        
        # Apply K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df['cluster'] = kmeans.fit_predict(coords)
        
        # Select one representative point from each cluster
        result = df.groupby('cluster').apply(lambda x: x.sample(1)).reset_index(drop=True)
        return result
    
    elif sampling_method == "grid":
        # Grid-based sampling (divide area into grid cells and take samples from each)
        # Create grid cells based on lat/long
        lat_bins = pd.cut(df['SID_LAT'], bins=int(np.sqrt(max_markers)))
        long_bins = pd.cut(df['SID_LONG'], bins=int(np.sqrt(max_markers)))
        
        df['grid_cell'] = list(zip(lat_bins, long_bins))
        
        # Take samples from each grid cell
        result = df.groupby('grid_cell', observed=False).apply(
            lambda x: x.sample(min(1, len(x)), random_state=42)
        ).reset_index(drop=True)
        
        # If we still have too many points, do random sampling
        if len(result) > max_markers:
            result = result.sample(max_markers, random_state=42)
            
        return result
    
    else:
        # Default to random sampling
        return df.sample(max_markers, random_state=42)

# Initialize session state for storing uploaded data
if 'data' not in st.session_state:
    st.session_state.data = None

# Initialize session state for file uploader
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'upload_status' not in st.session_state:
    st.session_state.upload_status = None
if 'upload_message' not in st.session_state:
    st.session_state.upload_message = ""
if 'upload_warnings' not in st.session_state:
    st.session_state.upload_warnings = []

# Function to process uploaded CSV file
def process_uploaded_file(uploaded_file):
    try:
        # Read CSV into pandas DataFrame
        df = pd.read_csv(uploaded_file)
        
        # Validate the data
        is_valid, message = validate_csv_data(df)
        
        if is_valid:
            # If it's a list of warnings (valid=True), store warnings
            if isinstance(message, list):
                st.session_state.upload_warnings = message
                st.session_state.upload_message = "Data berhasil diunggah!"
                st.session_state.upload_status = "success"
            else:
                st.session_state.upload_message = message
                st.session_state.upload_status = "success"
                st.session_state.upload_warnings = []
                
            # Store the data in session state
            st.session_state.data = df
            return True
        else:
            # If not valid, set error message
            st.session_state.upload_message = message
            st.session_state.upload_status = "error"
            st.session_state.upload_warnings = []
            return False
            
    except Exception as e:
        # Handle exceptions during file processing
        st.session_state.upload_message = f"Error memproses file: {str(e)}"
        st.session_state.upload_status = "error"
        st.session_state.upload_warnings = []
        return False

# Sidebar for app navigation and settings
with st.sidebar:
    st.image("komdigi.png", width=250)  # Replace with a frequency management logo
    
    st.markdown("### Menu Navigasi")
    app_mode = st.radio(
        "Pilih Mode Aplikasi:",
        ["📊 Dashboard", "🗂️ Upload & Analisis", "📝 Tentang Aplikasi"]
    )
    
    if app_mode == "📊 Dashboard":
        st.info("Mode dashboard menampilkan visualisasi interaktif data frekuensi.")
    
    if app_mode == "🗂️ Upload & Analisis":
        st.info("Upload data CSV untuk analisis dan visualisasi.")
    
    if app_mode == "📝 Tentang Aplikasi":
        st.info("Informasi tentang aplikasi dan panduan penggunaan.")
        
    st.markdown("---")
    
    # Advanced Settings
    st.markdown("### Pengaturan Lanjutan")
    
    # Map Settings
    st.markdown("#### Pengaturan Peta")
    default_map_style = st.selectbox(
        "Gaya peta default:",
        ["OpenStreetMap", "Esri Satellite", "CartoDB Dark"]
    )
    
    # Performance Settings
    st.markdown("#### Pengaturan Performa")
    # Increase max_markers to 20000 to handle larger datasets
    max_markers = st.slider("Jumlah maksimum marker pada peta:", 1000, 20000, 5000, 1000)
    
    sampling_method = st.selectbox(
        "Metode sampling untuk dataset besar:",
        ["random", "cluster", "grid"],
        help="Metode untuk memilih subset data yang representatif jika jumlah baris melebihi jumlah maksimum marker"
    )
    
    # Display Settings
    st.markdown("#### Tampilan")
    theme_mode = st.radio("Mode tampilan:", ["Light", "Dark"], horizontal=True)
    
    # Date and version info
    st.markdown("---")
    st.markdown(f"<div style='text-align: center; color: #888;'>Versi 2.2.0<br>Last updated: {datetime.now().strftime('%d %b %Y')}</div>", unsafe_allow_html=True)

# Main content area based on selected mode
if app_mode == "🗂️ Upload & Analisis":
    # Upload and Analysis page
    st.markdown('<p class="sub-header">📤 Upload Data Frekuensi</p>', unsafe_allow_html=True)
    
    # Upload container with styling
    st.markdown('<div class="upload-container">', unsafe_allow_html=True)
    
    # File uploader
    uploaded_file = st.file_uploader("Pilih file CSV untuk diunggah", type=["csv"])
    
    if uploaded_file is not None and uploaded_file != st.session_state.uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        with st.spinner('Memproses file...'):
            process_uploaded_file(uploaded_file)
    
    # Display upload status messages
    if st.session_state.upload_status == "success":
        st.success(st.session_state.upload_message)
        
        # Display warnings if any
        if st.session_state.upload_warnings:
            for warning in st.session_state.upload_warnings:
                st.warning(warning)
        
        # Display data summary
        if st.session_state.data is not None:
            df = st.session_state.data
            
            # Data summary container
            st.markdown("### 📊 Ringkasan Data")
            
            # Display metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Jumlah Baris", f"{len(df):,}")
            with col2:
                st.metric("Jumlah Kota", f"{df['CITY'].nunique():,}")
            with col3:
                st.metric("Jumlah Klien", f"{df['CLNT_NAME'].nunique():,}")
            with col4:
                st.metric("Jumlah Layanan", f"{df['SERVICE'].nunique():,}")
            
            # Display preview of the data
            st.markdown("### 🔍 Preview Data")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Data filtering options
            st.markdown('<p class="sub-header">🔍 Filter Data</p>', unsafe_allow_html=True)
            
            # Filter container
            st.markdown('<div class="filter-container">', unsafe_allow_html=True)
            
            # Filter columns
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            with filter_col1:
                # Filter by city
                cities = ["All"] + sorted(df['CITY'].unique().tolist())
                selected_city = st.selectbox("Filter berdasarkan Kota:", cities)
            
            with filter_col2:
                # Filter by service
                services = ["All"] + sorted(df['SERVICE'].unique().tolist())
                selected_service = st.selectbox("Filter berdasarkan Layanan:", services)
            
            with filter_col3:
                # Filter by client
                clients = ["All"] + sorted(df['CLNT_NAME'].unique().tolist())
                selected_client = st.selectbox("Filter berdasarkan Klien:", clients)
            
            # Additional filters if frequency data exists
            if 'FREQ_MHZ' in df.columns:
                freq_col1, freq_col2 = st.columns(2)
                
                with freq_col1:
                    # Frequency range filter
                    min_freq = float(df['FREQ_MHZ'].min())
                    max_freq = float(df['FREQ_MHZ'].max())
                    freq_range = st.slider(
                        "Rentang Frekuensi (MHz):",
                        min_value=min_freq,
                        max_value=max_freq,
                        value=(min_freq, max_freq)
                    )
                
                with freq_col2:
                    # Frequency band filter
                    bands = ["All"] + sorted(df['FREQ_MHZ'].apply(get_frequency_band).unique().tolist())
                    selected_band = st.selectbox("Filter berdasarkan Band:", bands)
            
            # Apply filters to create filtered dataframe
            filtered_df = df.copy()
            
            # Apply city filter
            if selected_city != "All":
                filtered_df = filtered_df[filtered_df['CITY'] == selected_city]
            
            # Apply service filter
            if selected_service != "All":
                filtered_df = filtered_df[filtered_df['SERVICE'] == selected_service]
            
            # Apply client filter
            if selected_client != "All":
                filtered_df = filtered_df[filtered_df['CLNT_NAME'] == selected_client]
            
            # Apply frequency filter if exists
            if 'FREQ_MHZ' in df.columns:
                # Apply frequency range filter
                filtered_df = filtered_df[
                    (filtered_df['FREQ_MHZ'] >= freq_range[0]) & 
                    (filtered_df['FREQ_MHZ'] <= freq_range[1])
                ]
                
                # Apply band filter
                if selected_band != "All":
                    filtered_df = filtered_df[filtered_df['FREQ_MHZ'].apply(get_frequency_band) == selected_band]
            
            st.markdown('</div>', unsafe_allow_html=True)  # Close filter container
            
            # Show filtered data info
            st.markdown(f"<div class='info-box'>Menampilkan {len(filtered_df):,} dari {len(df):,} data ({(len(filtered_df)/len(df)*100):.1f}%)</div>", unsafe_allow_html=True)
            
            # Export options
            export_col1, export_col2 = st.columns(2)
            
            with export_col1:
                # Create download button for filtered CSV
                csv = filtered_df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="filtered_frequency_data.csv" class="btn" style="background-color:#1E88E5; color:white; padding:0.5rem 1rem; border-radius:5px; text-decoration:none; display:inline-block; text-align:center;">📥 Download Data Terfilter (CSV)</a>'
                st.markdown(href, unsafe_allow_html=True)
            
            with export_col2:
                # Show filtered data
                if st.button("Tampilkan Data Terfilter", key="show_filtered"):
                    st.dataframe(filtered_df, use_container_width=True)
            
            # Data Visualization Section
            st.markdown('<p class="sub-header">📊 Visualisasi Data</p>', unsafe_allow_html=True)
            
            # Visualization Tabs
            viz_tab1, viz_tab2, viz_tab3 = st.tabs(["📍 Visualisasi Peta", "📊 Grafik Distribusi", "📈 Analisis Frekuensi"])
            
            with viz_tab1:
                st.markdown("### 🗺️ Peta Sebaran Lokasi Frekuensi")
                
                # Map settings
                map_col1, map_col2 = st.columns(2)
                
                with map_col1:
                    # Map type selection
                    map_type = st.selectbox(
                        "Pilih Jenis Peta:",
                        ["OpenStreetMap", "Esri Satellite", "CartoDB Dark", "Stamen Terrain"]
                    )
                
                with map_col2:
                    # Display mode
                    display_mode = st.selectbox(
                        "Mode Tampilan:",
                        ["Markers", "Heatmap", "Markers + Heatmap"]
                    )
                
                # Create map
                if len(filtered_df) > 0:
                    # Optimize data if needed based on performance settings
                    if len(filtered_df) > max_markers:
                        map_data = optimize_map_data(filtered_df, max_markers, sampling_method)
                        st.warning(f"Dataset terfilter terlalu besar ({len(filtered_df):,} baris). Menampilkan sampel {len(map_data):,} titik untuk performa yang lebih baik.")
                    else:
                        map_data = filtered_df
                    
                    # Define map center (average of coordinates)
                    avg_lat = map_data['SID_LAT'].mean()
                    avg_long = map_data['SID_LONG'].mean()
                    
                    # Create base map
                    if map_type == "OpenStreetMap":
                        m = folium.Map(location=[avg_lat, avg_long], zoom_start=6, tiles="OpenStreetMap")
                    elif map_type == "Esri Satellite":
                        m = folium.Map(location=[avg_lat, avg_long], zoom_start=6, tiles="Esri Satellite")
                    elif map_type == "CartoDB Dark":
                        m = folium.Map(location=[avg_lat, avg_long], zoom_start=6, tiles="CartoDB dark_matter")
                    elif map_type == "Stamen Terrain":
                        m = folium.Map(location=[avg_lat, avg_long], zoom_start=6, tiles="Stamen Terrain")
                    
                    # Add plugins
                    MiniMap().add_to(m)
                    Draw(export=True).add_to(m)
                    LocateControl().add_to(m)
                    Fullscreen().add_to(m)
                    MousePosition().add_to(m)
                    
                    # Add search plugin
                    # Search(
                    #    layer=None,
                    #    geom_type="Point",
                    #    placeholder="Search location...",
                    #    collapsed=True,
                    #    search_zoom=12
                    # ).add_to(m)
                    
                    # Tambahkan ini sebagai pengganti plugin Search
                    search_query = st.text_input("Cari lokasi:", "")
                    if search_query:
                        st.write(f"Mencari: {search_query}")
                        # Tampilkan filter data berdasarkan pencarian
                        filtered_results = df[df['CITY'].str.contains(search_query, case=False) | 
                        df['STN_NAME'].str.contains(search_query, case=False)]
                        if not filtered_results.empty:
                            st.dataframe(filtered_results)
                        else:
                            st.info("Tidak ditemukan hasil yang cocok")
                    
                    
                    # Create marker cluster for markers
                    if display_mode in ["Markers", "Markers + Heatmap"]:
                        marker_cluster = MarkerCluster().add_to(m)
                        
                        # Add markers with popups
                        for _, row in map_data.iterrows():
                            service_info = get_service_icon(row['SERVICE'])
                            icon_color = service_info['color']
                            
                            # Create custom icon
                            icon = folium.Icon(
                                icon=service_info['icon'],
                                prefix='fa',
                                color='white',
                                icon_color=icon_color
                            )
                            
                            # Create popup
                            popup_content = create_popup_content(row)
                            popup = folium.Popup(folium.Html(popup_content, script=True), max_width=350)
                            
                            # Add marker to cluster
                            folium.Marker(
                                location=[row['SID_LAT'], row['SID_LONG']],
                                popup=popup,
                                icon=icon,
                                tooltip=f"{row['STN_NAME']} - {row['SERVICE']}"
                            ).add_to(marker_cluster)
                    
                    # Add heatmap
                    if display_mode in ["Heatmap", "Markers + Heatmap"]:
                        # Extract coordinates for heatmap
                        heat_data = [[row['SID_LAT'], row['SID_LONG']] for _, row in map_data.iterrows()]
                        
                        # Add heat map to the map
                        HeatMap(heat_data, radius=15, blur=10, gradient={0.4: 'blue', 0.65: 'lime', 0.8: 'yellow', 1: 'red'}).add_to(m)
                    
                    # Add legend
                    legend_html = """
                    <div style="position: fixed; bottom: 50px; right: 50px; z-index: 1000; background-color: white; 
                                padding: 10px; border: 2px solid grey; border-radius: 5px;">
                        <p style="text-align: center; font-weight: bold; margin-bottom: 10px;">Legenda Layanan</p>
                    """
                    
                    # Add legend items based on unique services in the filtered_df
                    for service in sorted(map_data['SERVICE'].unique()):
                        service_info = get_service_icon(service)
                        legend_html += f"""
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: {service_info['color']};"></div>
                            <div>{service}</div>
                        </div>
                        """
                    
                    legend_html += """
                    </div>
                    """
                    
                    # Add legend as HTML
                    m.get_root().html.add_child(folium.Element(legend_html))
                    
                    # Display map
                    st.markdown("#### Interactive Map")
                    folium_static(m, width=1000, height=600)
                    
                    # Show stats about the map
                    st.markdown(f"<div class='info-box'>Menampilkan {len(map_data):,} titik lokasi dari {len(filtered_df):,} data terfilter.</div>", unsafe_allow_html=True)
                else:
                    st.warning("Tidak ada data untuk ditampilkan. Silakan sesuaikan filter.")
            
            with viz_tab2:
                st.markdown("### 📊 Grafik Distribusi")
                
                if len(filtered_df) > 0:
                    # Create distribution charts
                    dist_tab1, dist_tab2, dist_tab3 = st.tabs(["Distribusi Layanan", "Distribusi Kota", "Distribusi Klien"])
                    
                    with dist_tab1:
                        # Service distribution
                        service_counts = filtered_df['SERVICE'].value_counts().reset_index()
                        service_counts.columns = ['SERVICE', 'COUNT']
                        
                        # Create bar chart
                        fig = px.bar(
                            service_counts, 
                            x='SERVICE', 
                            y='COUNT',
                            color='SERVICE',
                            title='Distribusi Layanan',
                            labels={'SERVICE': 'Jenis Layanan', 'COUNT': 'Jumlah'},
                            color_discrete_sequence=px.colors.qualitative.Bold
                        )
                        
                        # Update layout
                        fig.update_layout(xaxis_title='Jenis Layanan', yaxis_title='Jumlah')
                        
                        # Show plot
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Show percentages as pie chart
                        pie_fig = px.pie(
                            service_counts, 
                            values='COUNT', 
                            names='SERVICE', 
                            title='Persentase Jenis Layanan',
                            color_discrete_sequence=px.colors.qualitative.Bold
                        )
                        
                        # Update layout
                        pie_fig.update_layout(margin=dict(t=40, b=40, l=40, r=40))
                        pie_fig.update_traces(textposition='inside', textinfo='percent+label', textfont_size=12)
                        
                        # Show plot
                        st.plotly_chart(pie_fig, use_container_width=True)
                    
                    with dist_tab2:
                        # City distribution (top 15)
                        city_counts = filtered_df['CITY'].value_counts().reset_index()
                        city_counts.columns = ['CITY', 'COUNT']
                        
                        # Limit to top 15 cities for readability
                        if len(city_counts) > 15:
                            city_counts = city_counts.head(15)
                            title = 'Distribusi Kota (Top 15)'
                        else:
                            title = 'Distribusi Kota'
                        
                        # Create horizontal bar chart
                        fig = px.bar(
                            city_counts, 
                            y='CITY', 
                            x='COUNT',
                            color='COUNT',
                            title=title,
                            labels={'CITY': 'Kota', 'COUNT': 'Jumlah'},
                            orientation='h',
                            color_continuous_scale='Blues'
                        )
                        
                        # Update layout
                        fig.update_layout(yaxis_title='Kota', xaxis_title='Jumlah', yaxis={'categoryorder':'total ascending'})
                        
                        # Show plot
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with dist_tab3:
                        # Client distribution (top 15)
                        client_counts = filtered_df['CLNT_NAME'].value_counts().reset_index()
                        client_counts.columns = ['CLNT_NAME', 'COUNT']
                        
                        # Limit to top 15 clients for readability
                        if len(client_counts) > 15:
                            client_counts = client_counts.head(15)
                            title = 'Distribusi Klien (Top 15)'
                        else:
                            title = 'Distribusi Klien'
                        
                        # Create horizontal bar chart
                        fig = px.bar(
                            client_counts, 
                            y='CLNT_NAME', 
                            x='COUNT',
                            color='COUNT',
                            title=title,
                            labels={'CLNT_NAME': 'Klien', 'COUNT': 'Jumlah'},
                            orientation='h',
                            color_continuous_scale='Greens'
                        )
                        
                        # Update layout
                        fig.update_layout(yaxis_title='Klien', xaxis_title='Jumlah', yaxis={'categoryorder':'total ascending'})
                        
                        # Show plot
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Tidak ada data untuk ditampilkan. Silakan sesuaikan filter.")
            
            with viz_tab3:
                st.markdown("### 📈 Analisis Frekuensi")
                
                if 'FREQ_MHZ' in filtered_df.columns and len(filtered_df) > 0:
                    # Frequency analysis
                    freq_tab1, freq_tab2, freq_tab3 = st.tabs(["Distribusi Frekuensi", "Frekuensi per Layanan", "Visualisasi 3D"])
                    
                    with freq_tab1:
                        # Create histogram of frequencies
                        fig = px.histogram(
                            filtered_df,
                            x='FREQ_MHZ',
                            nbins=50,
                            title='Distribusi Frekuensi',
                            labels={'FREQ_MHZ': 'Frekuensi (MHz)'},
                            color_discrete_sequence=['#1E88E5']
                        )
                        
                        # Update layout
                        fig.update_layout(xaxis_title='Frekuensi (MHz)', yaxis_title='Jumlah')
                        
                        # Show plot
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Add band distribution
                        filtered_df['FREQ_BAND'] = filtered_df['FREQ_MHZ'].apply(get_frequency_band)
                        band_counts = filtered_df['FREQ_BAND'].value_counts().reset_index()
                        band_counts.columns = ['FREQ_BAND', 'COUNT']
                        
                        # Create band distribution chart
                        band_fig = px.bar(
                            band_counts,
                            x='FREQ_BAND',
                            y='COUNT',
                            color='FREQ_BAND',
                            title='Distribusi Band Frekuensi',
                            labels={'FREQ_BAND': 'Band Frekuensi', 'COUNT': 'Jumlah'}
                        )
                        
                        # Update layout
                        band_fig.update_layout(xaxis_title='Band Frekuensi', yaxis_title='Jumlah')
                        
                        # Show plot
                        st.plotly_chart(band_fig, use_container_width=True)
                    
                    with freq_tab2:
                        # Box plot of frequency by service
                        fig = px.box(
                            filtered_df,
                            x='SERVICE',
                            y='FREQ_MHZ',
                            color='SERVICE',
                            title='Distribusi Frekuensi per Layanan',
                            labels={'SERVICE': 'Jenis Layanan', 'FREQ_MHZ': 'Frekuensi (MHz)'}
                        )
                        
                        # Update layout
                        fig.update_layout(xaxis_title='Jenis Layanan', yaxis_title='Frekuensi (MHz)')
                        
                        # Show plot
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Calculate average frequency per service
                        avg_freq = filtered_df.groupby('SERVICE')['FREQ_MHZ'].mean().reset_index()
                        avg_freq.columns = ['SERVICE', 'AVG_FREQ']
                        avg_freq = avg_freq.sort_values('AVG_FREQ')
                        
                        # Create bar chart of average frequencies
                        avg_fig = px.bar(
                            avg_freq,
                            y='SERVICE',
                            x='AVG_FREQ',
                            color='SERVICE',
                            title='Rata-rata Frekuensi per Layanan',
                            labels={'SERVICE': 'Jenis Layanan', 'AVG_FREQ': 'Rata-rata Frekuensi (MHz)'},
                            orientation='h'
                        )
                        
                        # Update layout
                        avg_fig.update_layout(yaxis_title='Jenis Layanan', xaxis_title='Rata-rata Frekuensi (MHz)')
                        
                        # Show plot
                        st.plotly_chart(avg_fig, use_container_width=True)
                    
                    with freq_tab3:
                        # 3D scatter plot of locations and frequencies
                        fig = px.scatter_3d(
                            filtered_df,
                            x='SID_LONG',
                            y='SID_LAT',
                            z='FREQ_MHZ',
                            color='SERVICE',
                            title='Visualisasi 3D Lokasi dan Frekuensi',
                            labels={
                                'SID_LONG': 'Longitude',
                                'SID_LAT': 'Latitude',
                                'FREQ_MHZ': 'Frekuensi (MHz)',
                                'SERVICE': 'Jenis Layanan'
                            }
                        )
                        
                        # Update layout
                        fig.update_layout(margin=dict(l=0, r=0, b=0, t=30))
                        
                        # Show plot
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Data frekuensi tidak tersedia atau tidak ada data untuk ditampilkan. Silakan sesuaikan filter.")
    else:
        # Display guide on how to upload
        st.info("Belum ada data yang diunggah. Silakan unggah file CSV dengan data frekuensi.")
        
        # Instructions
        st.markdown("""
        #### Panduan Upload Data
        
        1. Siapkan file CSV dengan kolom-kolom yang diperlukan:
           - `CITY` - Kota lokasi pemancar
           - `CLNT_NAME` - Nama klien/pengguna frekuensi
           - `STN_NAME` - Nama stasiun/pemancar
           - `SERVICE` - Kategori layanan (Broadcasting, Mobile, Satellite, dll)
           - `SUBSERVICE` - Sub kategori layanan (FM Radio, 4G LTE, 5G, dll)
           - `SID_LONG` - Koordinat longitude (bujur) lokasi
           - `SID_LAT` - Koordinat latitude (lintang) lokasi
           
        2. Kolom opsional yang dapat ditambahkan:
           - `FREQ_MHZ` - Frekuensi dalam MHz
           - `BW_MHZ` - Bandwidth dalam MHz
           - `DATE` - Tanggal registrasi/pembaruan data
           - `TX_POWER` - Daya pancar dalam Watt
           - `ANTENNA_HEIGHT` - Tinggi antena dalam meter
           - `POLARIZATION` - Polarisasi antena
           
        3. Klik tombol "Browse files" di atas untuk memilih file CSV dari perangkat Anda.
        
        4. Setelah file diunggah, sistem akan melakukan validasi dan menampilkan data jika valid.
        """)
        
        # Sample CSV template
        st.markdown("#### Contoh Template CSV")
        
        sample_csv = """CITY,CLNT_NAME,STN_NAME,SERVICE,SUBSERVICE,SID_LAT,SID_LONG,FREQ_MHZ,BW_MHZ
Jakarta,PT Telkom,Jakarta Tower,Broadcasting,FM Radio,-6.2088,106.8456,98.5,0.2
Surabaya,PT Media Networks,Surabaya Station,Mobile,4G LTE,-7.2575,112.7520,1800.0,20.0
Bandung,PT Broadcast Indonesia,Bandung Relay,Cellular,5G,-6.9175,107.6191,2600.0,40.0
Medan,PT Radio Sentosa,Medan Transmitter,Broadcasting,TV,3.5952,98.6722,205.0,0.1
Makassar,PT Telkom,Makassar Tower,Satellite,Internet,-5.1477,119.4144,14000.0,36.0
Semarang,PT Radio Indonesia,Semarang Station,Radio,AM Radio,-6.9932,110.4203,540.0,0.01"""
        
        st.code(sample_csv, language="csv")
        
        # Download button for template
        st.download_button(
            label="⬇️ Download Template CSV",
            data=sample_csv,
            file_name='frequency_data_template.csv',
            mime='text/csv',
        )
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close upload container
    
elif app_mode == "📊 Dashboard":
    # Dashboard display - check if data exists
    if st.session_state.data is not None:
        st.markdown('<p class="sub-header">📊 Dashboard Informasi Frekuensi</p>', unsafe_allow_html=True)
        
        # Get dataframe from session state
        df = st.session_state.data
        
        # Dashboard metrics
        st.markdown("### 📌 Ringkasan")
        
        # Display metrics in columns
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Data", f"{len(df):,}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Jumlah Kota", f"{df['CITY'].nunique():,}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Jumlah Klien", f"{df['CLNT_NAME'].nunique():,}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Jenis Layanan", f"{df['SERVICE'].nunique():,}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col5:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            if 'FREQ_MHZ' in df.columns:
                avg_freq = df['FREQ_MHZ'].mean()
                if avg_freq >= 1000:
                    freq_display = f"{avg_freq/1000:.2f} GHz"
                else:
                    freq_display = f"{avg_freq:.2f} MHz"
                st.metric("Rata-rata Frekuensi", freq_display)
            else:
                st.metric("Sub Layanan", f"{df['SUBSERVICE'].nunique():,}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Create dashboard tabs
        dash_tab1, dash_tab2, dash_tab3 = st.tabs(["🌍 Peta Utama", "📊 Statistik Layanan", "🏙️ Distribusi Kota"])
        
        with dash_tab1:
            st.markdown("### 🗺️ Peta Distribusi Frekuensi")
            
            # Map settings in smaller columns
            map_col1, map_col2, map_col3 = st.columns(3)
            
            with map_col1:
                # Map type selection
                map_type = st.selectbox(
                    "Jenis Peta:",
                    ["OpenStreetMap", "Esri Satellite", "CartoDB Dark"],
                    key="dash_map_type"
                )
            
            with map_col2:
                # Service filter for map
                dash_services = ["All"] + sorted(df['SERVICE'].unique().tolist())
                dash_service = st.selectbox("Filter Layanan:", dash_services, key="dash_service")
            
            with map_col3:
                # Display mode
                display_mode = st.selectbox(
                    "Mode Tampilan:",
                    ["Markers + Heatmap", "Markers", "Heatmap"],
                    key="dash_display_mode"
                )
            
            # Filter data based on selection
            if dash_service != "All":
                dash_map_data = df[df['SERVICE'] == dash_service].copy()
            else:
                dash_map_data = df.copy()
            
            # Optimize data for map display
            if len(dash_map_data) > max_markers:
                dash_map_data = optimize_map_data(dash_map_data, max_markers, sampling_method)
                st.info(f"Dataset terlalu besar ({len(df):,} data). Menampilkan sampel {len(dash_map_data):,} titik untuk performa optimal.")
            
            # Define map center
            avg_lat = dash_map_data['SID_LAT'].mean()
            avg_long = dash_map_data['SID_LONG'].mean()
            
            # Create base map
            if map_type == "OpenStreetMap":
                m = folium.Map(location=[avg_lat, avg_long], zoom_start=5, tiles="OpenStreetMap")
            elif map_type == "Esri Satellite":
                m = folium.Map(location=[avg_lat, avg_long], zoom_start=5, tiles="Esri Satellite")
            elif map_type == "CartoDB Dark":
                m = folium.Map(location=[avg_lat, avg_long], zoom_start=5, tiles="CartoDB dark_matter")
            
            # Add plugins
            MiniMap().add_to(m)
            Draw(export=True).add_to(m)
            LocateControl().add_to(m)
            Fullscreen().add_to(m)
            MousePosition().add_to(m)
            
            # Create feature group for search functionality
            feature_group = folium.FeatureGroup(name="Locations")
            feature_group.add_to(m)
            
            # Add search plugin with the feature group
            Search(
                layer=feature_group,
                geom_type="Point",
                placeholder="Cari lokasi...",
                collapsed=True,
                search_zoom=12
            ).add_to(m)
            
            # Add markers
            if display_mode in ["Markers", "Markers + Heatmap"]:
                marker_cluster = MarkerCluster().add_to(m)
                
                # Add markers with popups
                for _, row in dash_map_data.iterrows():
                    service_info = get_service_icon(row['SERVICE'])
                    icon_color = service_info['color']
                    
                    # Create custom icon
                    icon = folium.Icon(
                        icon=service_info['icon'],
                        prefix='fa',
                        color='white',
                        icon_color=icon_color
                    )
                    
                    # Create popup
                    popup_content = create_popup_content(row)
                    popup = folium.Popup(folium.Html(popup_content, script=True), max_width=350)
                    
                    # Add marker to cluster
                    folium.Marker(
                        location=[row['SID_LAT'], row['SID_LONG']],
                        popup=popup,
                        icon=icon,
                        tooltip=f"{row['STN_NAME']} - {row['SERVICE']}"
                    ).add_to(marker_cluster)
            
            # Add heatmap
            if display_mode in ["Heatmap", "Markers + Heatmap"]:
                # Extract coordinates for heatmap
                heat_data = [[row['SID_LAT'], row['SID_LONG']] for _, row in dash_map_data.iterrows()]
                
                # Add heat map to the map
                HeatMap(heat_data, radius=15, blur=10, gradient={0.4: 'blue', 0.65: 'lime', 0.8: 'yellow', 1: 'red'}).add_to(m)
            
            # Add legend
            legend_html = """
            <div style="position: fixed; bottom: 50px; right: 50px; z-index: 1000; background-color: white; 
                        padding: 10px; border: 2px solid grey; border-radius: 5px;">
                <p style="text-align: center; font-weight: bold; margin-bottom: 10px;">Legenda Layanan</p>
            """
            
            # Add legend items based on unique services
            for service in sorted(dash_map_data['SERVICE'].unique()):
                service_info = get_service_icon(service)
                legend_html += f"""
                <div class="legend-item">
                    <div class="legend-color" style="background-color: {service_info['color']};"></div>
                    <div>{service}</div>
                </div>
                """
            
            legend_html += """
            </div>
            """
            
            # Add legend as HTML
            m.get_root().html.add_child(folium.Element(legend_html))
            
            # Display map
            folium_static(m, width=1000, height=550)
        
        with dash_tab2:
            st.markdown("### 📊 Statistik Layanan Frekuensi")
            
            # Create service statistics
            service_counts = df['SERVICE'].value_counts().reset_index()
            service_counts.columns = ['SERVICE', 'COUNT']
            
            # Create bar chart
            fig = px.bar(
                service_counts,
                x='SERVICE',
                y='COUNT',
                color='SERVICE',
                title='Distribusi Jenis Layanan',
                labels={'SERVICE': 'Jenis Layanan', 'COUNT': 'Jumlah'}
            )
            
            # Update layout
            fig.update_layout(xaxis_title='Jenis Layanan', yaxis_title='Jumlah')
            
            # Show plot
            st.plotly_chart(fig, use_container_width=True)
            
            # Check if frequency data exists
            if 'FREQ_MHZ' in df.columns:
                # Subservice by frequency
                subservice_freq = df.groupby(['SERVICE', 'SUBSERVICE'])['FREQ_MHZ'].mean().reset_index()
                
                # Create grouped bar chart
                fig2 = px.bar(
                    subservice_freq,
                    x='SERVICE',
                    y='FREQ_MHZ',
                    color='SUBSERVICE',
                    title='Rata-rata Frekuensi per Subservice',
                    labels={'SERVICE': 'Jenis Layanan', 'FREQ_MHZ': 'Rata-rata Frekuensi (MHz)', 'SUBSERVICE': 'Sub-layanan'}
                )
                
                # Update layout
                fig2.update_layout(xaxis_title='Jenis Layanan', yaxis_title='Rata-rata Frekuensi (MHz)')
                
                # Show plot
                st.plotly_chart(fig2, use_container_width=True)
            
            # Subservice distribution
            subservice_counts = df['SUBSERVICE'].value_counts().reset_index()
            subservice_counts.columns = ['SUBSERVICE', 'COUNT']
            
            # Limit to top 15 subservices for readability
            if len(subservice_counts) > 15:
                subservice_counts = subservice_counts.head(15)
                title = 'Distribusi Sub-layanan (Top 15)'
            else:
                title = 'Distribusi Sub-layanan'
            
            # Create horizontal bar chart
            fig3 = px.bar(
                subservice_counts,
                y='SUBSERVICE',
                x='COUNT',
                color='COUNT',
                title=title,
                labels={'SUBSERVICE': 'Sub-layanan', 'COUNT': 'Jumlah'},
                orientation='h',
                color_continuous_scale='Viridis'
            )
            
            # Update layout
            fig3.update_layout(yaxis_title='Sub-layanan', xaxis_title='Jumlah', yaxis={'categoryorder':'total ascending'})
            
            # Show plot
            st.plotly_chart(fig3, use_container_width=True)
        
        with dash_tab3:
            st.markdown("### 🏙️ Distribusi Kota")
            
            # Create city statistics
            city_counts = df['CITY'].value_counts().reset_index()
            city_counts.columns = ['CITY', 'COUNT']
            
            # Limit to top 20 cities
            if len(city_counts) > 20:
                city_counts = city_counts.head(20)
                title = 'Top 20 Kota berdasarkan Jumlah Pemancar'
            else:
                title = 'Kota berdasarkan Jumlah Pemancar'
            
            # Create horizontal bar chart
            fig = px.bar(
                city_counts,
                y='CITY',
                x='COUNT',
                color='COUNT',
                title=title,
                labels={'CITY': 'Kota', 'COUNT': 'Jumlah Pemancar'},
                orientation='h',
                color_continuous_scale='Blues'
            )
            
            # Update layout
            fig.update_layout(yaxis_title='Kota', xaxis_title='Jumlah Pemancar', yaxis={'categoryorder':'total ascending'})
            
            # Show plot
            st.plotly_chart(fig, use_container_width=True)
            
            # Distribution of services per city (heatmap)
            city_service = pd.crosstab(df['CITY'], df['SERVICE'])
            
            # Limit to top 15 cities by total
            if len(city_service) > 15:
                city_totals = city_service.sum(axis=1)
                top_cities = city_totals.nlargest(15).index
                city_service = city_service.loc[top_cities]
                title = 'Distribusi Layanan per Kota (Top 15 Kota)'
            else:
                title = 'Distribusi Layanan per Kota'
            
            # Create heatmap
            fig2 = px.imshow(
                city_service,
                labels=dict(x="Jenis Layanan", y="Kota", color="Jumlah Pemancar"),
                title=title,
                aspect="auto",
                color_continuous_scale='YlGnBu'
            )
            
            # Update layout
            fig2.update_layout(xaxis_title='Jenis Layanan', yaxis_title='Kota')
            
            # Show plot
            st.plotly_chart(fig2, use_container_width=True)
            
            # Create map of stations by city
            st.markdown("#### Peta Distribusi Pemancar per Kota")
            
            # Create map with city markers
            city_data = df.groupby('CITY').agg({
                'SID_LAT': 'mean',
                'SID_LONG': 'mean',
                'STN_NAME': 'count'
            }).reset_index()
            
            # Rename columns
            city_data.rename(columns={'STN_NAME': 'COUNT'}, inplace=True)
            
            # Create map
            city_map = folium.Map(location=[city_data['SID_LAT'].mean(), city_data['SID_LONG'].mean()], zoom_start=5, tiles="OpenStreetMap")
            
            # Add city markers with scaled sizes
            for _, row in city_data.iterrows():
                # Scale marker size based on count (min 10, max 40)
                marker_size = min(40, max(10, int(10 * np.log10(row['COUNT']))))
                
                # Create popup content
                popup_content = f"""
                <div style="font-family: 'Segoe UI', sans-serif; min-width: 200px; max-width: 300px;">
                    <h3 style="margin-bottom: 10px;">{row['CITY']}</h3>
                    <p><b>Jumlah Pemancar:</b> {row['COUNT']:,}</p>
                    <p><b>Koordinat:</b> {row['SID_LAT']:.6f}, {row['SID_LONG']:.6f}</p>
                </div>
                """
                
                # Create popup
                popup = folium.Popup(folium.Html(popup_content, script=True), max_width=300)
                
                # Add circle marker
                folium.CircleMarker(
                    location=[row['SID_LAT'], row['SID_LONG']],
                    radius=marker_size,
                    popup=popup,
                    color='#3186cc',
                    fill=True,
                    fill_color='#3186cc',
                    fill_opacity=0.7,
                    tooltip=f"{row['CITY']} ({row['COUNT']} pemancar)"
                ).add_to(city_map)
            
            # Add plugins
            MiniMap().add_to(city_map)
            
            # Display map
            folium_static(city_map, width=1000, height=500)
    else:
        # No data available - show dashboard placeholder
        st.markdown('<p class="sub-header">📊 Dashboard Informasi Frekuensi</p>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="warning-box">
            <h3>Data Belum Tersedia</h3>
            <p>Belum ada data frekuensi yang diunggah untuk ditampilkan di dashboard.</p>
            <p>Silakan beralih ke tab "🗂️ Upload & Analisis" untuk mengunggah data CSV.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show sample dashboard
        st.markdown("### 🖼️ Preview Dashboard")
        st.image("komdigi.png", width=250, caption="Contoh tampilan dashboard dengan data frekuensi")
        
        # Quick instructions
        st.markdown("""
        <div class="info-box">
            <h3>Cara Menggunakan Dashboard</h3>
            <ol>
                <li>Unggah file CSV data frekuensi di tab "🗂️ Upload & Analisis"</li>
                <li>Pastikan file memiliki kolom yang diperlukan (CITY, CLNT_NAME, STN_NAME, SERVICE, SUBSERVICE, SID_LAT, SID_LONG)</li>
                <li>Setelah berhasil diunggah, kembali ke tab "📊 Dashboard" untuk melihat visualisasi data</li>
                <li>Gunakan filter yang tersedia untuk memfokuskan analisis pada data tertentu</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

elif app_mode == "📝 Tentang Aplikasi":
    # About the application
    st.markdown('<p class="sub-header">🌟 Tentang Aplikasi</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <h3>Sistem Informasi Manajemen Frekuensi</h3>
    <p>Aplikasi ini dirancang untuk mempermudah pengelolaan dan visualisasi data frekuensi radio beserta lokasi penggunanya. Aplikasi ini membantu regulator, operator, dan pihak terkait untuk menganalisis penggunaan spektrum frekuensi di berbagai wilayah secara efektif.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Manfaat Aplikasi")
        st.markdown("""
        - **Visualisasi Interaktif**: Tampilkan data frekuensi pada peta interaktif multi-layer
        - **Analisis Mendalam**: Identifikasi pola penggunaan spektrum dan potensi interferensi
        - **Kemudahan Monitoring**: Pantau penggunaan spektrum berdasarkan wilayah dan layanan
        - **Pelaporan Fleksibel**: Hasilkan laporan dan ekspor data untuk analisis lebih lanjut
        - **Perencanaan Spektrum**: Dukung pengambilan keputusan alokasi spektrum yang efisien
        """)
    
    with col2:
        st.markdown("### 🔑 Fitur Utama")
        st.markdown("""
        - **Peta Multi-Layer**: Visualisasi menggunakan beragam jenis peta, termasuk satelit
        - **Filter Data Dinamis**: Filter berdasarkan lokasi, layanan, frekuensi, dan klien
        - **Clustering Otomatis**: Kelompokkan marker untuk tampilan yang lebih bersih
        - **Heat Map**: Visualisasi kepadatan penggunaan frekuensi
        - **Analitik Frekuensi**: Grafik dan statistik distribusi penggunaan spektrum
        - **Pencarian & Navigasi**: Temukan lokasi spesifik dengan mudah
        - **Ekspor Data**: Unduh data terfilter untuk analisis lanjutan
        - **Dukungan Dataset Besar**: Mampu menangani dan memvisualisasikan hingga 20,000+ titik data
        """)
    
    st.markdown('<p class="sub-header">📋 Panduan Penggunaan</p>', unsafe_allow_html=True)
    
    # User guide with tabs for different sections
    panduan_tab1, panduan_tab2, panduan_tab3 = st.tabs(["📤 Upload Data", "🗺️ Penggunaan Peta", "📊 Analisis Data"])
    
    with panduan_tab1:
        st.markdown("### Upload Data Frekuensi")
        st.markdown("""
        1. **Format Data**: Gunakan file CSV dengan kolom wajib berikut:
           - `CITY` - Kota lokasi pemancar
           - `CLNT_NAME` - Nama klien/pengguna frekuensi
           - `STN_NAME` - Nama stasiun/pemancar
           - `SERVICE` - Kategori layanan (Broadcasting, Mobile, Satellite, dll)
           - `SUBSERVICE` - Sub kategori layanan (FM Radio, 4G LTE, 5G, dll)
           - `SID_LONG` - Koordinat longitude (bujur) lokasi
           - `SID_LAT` - Koordinat latitude (lintang) lokasi
           
        2. **Kolom Opsional** yang memperkaya analisis:
           - `FREQ_MHZ` - Frekuensi dalam MHz
           - `BW_MHZ` - Bandwidth dalam MHz
           - `DATE` - Tanggal registrasi/pembaruan data
           - `TX_POWER` - Daya pancar dalam Watt
           - `ANTENNA_HEIGHT` - Tinggi antena dalam meter
           - `POLARIZATION` - Polarisasi antena
           
        3. **Proses Upload**:
           - Klik tombol "Browse files" di panel Upload
           - Pilih file CSV dari perangkat Anda
           - Sistem akan memvalidasi struktur dan isi data
           - Jika ada kolom yang tidak valid, sistem akan memberi peringatan
           
        4. **Penanganan Dataset Besar**:
           - Aplikasi ini mendukung dataset hingga 20,000+ baris
           - Untuk dataset sangat besar, sistem menggunakan metode sampling untuk mengoptimalkan tampilan
           - Anda dapat memilih metode sampling di panel Pengaturan Performa
           - Data asli tetap utuh untuk analisis, hanya tampilan peta yang dioptimasi
           
        > 💡 **Tip**: Pastikan koordinat dalam format desimal (misal: -6.2088, 106.8456) dan kisaran yang valid (Latitude: -90 hingga 90, Longitude: -180 hingga 180)
        """)
        
        # Sample CSV template
        st.markdown("#### Contoh Template CSV")
        
        sample_csv = """CITY,CLNT_NAME,STN_NAME,SERVICE,SUBSERVICE,SID_LAT,SID_LONG,FREQ_MHZ,BW_MHZ
Jakarta,PT Telkom,Jakarta Tower,Broadcasting,FM Radio,-6.2088,106.8456,98.5,0.2
Surabaya,PT Media Networks,Surabaya Station,Mobile,4G LTE,-7.2575,112.7520,1800.0,20.0
Bandung,PT Broadcast Indonesia,Bandung Relay,Cellular,5G,-6.9175,107.6191,2600.0,40.0
Medan,PT Radio Sentosa,Medan Transmitter,Broadcasting,TV,3.5952,98.6722,205.0,0.1
Makassar,PT Telkom,Makassar Tower,Satellite,Internet,-5.1477,119.4144,14000.0,36.0
Semarang,PT Radio Indonesia,Semarang Station,Radio,AM Radio,-6.9932,110.4203,540.0,0.01"""
        
        st.code(sample_csv, language="csv")
        
        # Download button for template
        st.download_button(
            label="Download Template CSV",
            data=sample_csv,
            file_name='frequency_data_template.csv',
            mime='text/csv',
        )
    
    with panduan_tab2:
        st.markdown("### Menggunakan Peta Interaktif")
        st.markdown("""
        #### Fitur-fitur Peta:
        
        1. **Jenis Peta**:
           - **OpenStreetMap**: Peta dasar dengan tampilan jalan dan bangunan
           - **Esri Satellite**: Peta satelit dengan resolusi tinggi
           - **CartoDB Dark**: Peta gelap untuk kontras marker yang lebih baik
           - **Hybrid Map**: Kombinasi peta satelit dengan label jalan
        
        2. **Marker & Icon**:
           - Setiap marker mewakili lokasi stasiun/pemancar frekuensi
           - Warna dan ikon marker bervariasi berdasarkan jenis layanan
           - Klik marker untuk melihat informasi detail dalam popup
        
        3. **Layer & Filter**:
           - **Layer Service**: Filter marker berdasarkan jenis layanan (Broadcasting, Mobile, dll)
           - **Layer Frekuensi**: Filter marker berdasarkan rentang frekuensi (HF, VHF, UHF, dll)
           - **Heatmap**: Tampilkan peta panas kepadatan penggunaan frekuensi
           - **Cluster**: Kelompokkan marker yang berdekatan (berguna untuk data banyak)
        
        4. **Navigasi Peta**:
           - **Zoom**: Gunakan tombol +/- atau scroll mouse untuk zoom in/out
           - **Pan**: Klik dan tahan untuk menggeser peta
           - **Kotak Pencarian**: Cari lokasi spesifik dengan memasukkan nama
           - **Minimap**: Tampilan konteks area yang sedang dilihat
        
        5. **Alat Tambahan**:
           - **Ruler**: Ukur jarak antar titik
           - **Drawing**: Gambar area untuk analisis
           - **Full Screen**: Tampilkan peta dalam layar penuh
           - **Koordinat**: Lihat posisi koordinat kursor
        
        6. **Penanganan Data Besar**:
           - Untuk dataset besar (>5000 titik), sistem menggunakan clustering otomatis
           - Anda dapat memilih metode sampling untuk mengoptimalkan performa:
             - **Random**: Memilih titik secara acak (cepat, tetapi mungkin tidak representatif)
             - **Cluster**: Menggunakan K-means clustering untuk memilih titik yang representatif
             - **Grid**: Membagi area menjadi grid dan mengambil sampel dari setiap sel
        
        > 💡 **Tip**: Untuk analisis interferensi, gunakan fitur "buffer" dengan mengaktifkan tombol lingkaran pada alat drawing, kemudian atur radius sesuai kebutuhan
        """)
        
        # Map legend and examples
        st.markdown("#### Contoh Tampilan Peta & Legenda")
        st.image("https://i.imgur.com/LMPFZLK.png", caption="Contoh tampilan peta dengan marker lokasi frekuensi")
    
    with panduan_tab3:
        st.markdown("### Analisis & Visualisasi Data")
        st.markdown("""
        #### Jenis Visualisasi:
        
        1. **Dashboard Ringkasan**:
           - Statistik jumlah total data, kota, klien, dll
           - Grafik distribusi layanan
           - Pie chart persentase jenis layanan
        
        2. **Visualisasi Koordinat**:
           - Peta interaktif dengan marker lokasi
           - Heatmap kepadatan lokasi
           - Scatter plot distribusi koordinat
        
        3. **Analisis Frekuensi**:
           - Histogram distribusi frekuensi
           - Grafik pita frekuensi per layanan
           - Visualisasi 3D koordinat dan frekuensi
        
        4. **Distribusi Geografis**:
           - Bar chart jumlah pengguna per kota
           - Heatmap layanan per kota
           - Choropleth map kepadatan frekuensi per wilayah
        
        #### Tips Analisis Data:
        
        - **Analisis Interferensi**: Gunakan filter frekuensi dan radius untuk mengidentifikasi potensi interferensi antar pemancar
        - **Perencanaan Spektrum**: Analisis kepadatan penggunaan frekuensi untuk menemukan pita frekuensi yang masih tersedia
        - **Optimasi Jaringan**: Identifikasi area dengan cakupan rendah atau tinggi untuk optimasi jaringan
        - **Kepatuhan Regulasi**: Verifikasi apakah penggunaan frekuensi sesuai dengan alokasi yang diizinkan
        - **Dataset Besar**: Untuk analisis dataset >10,000 baris, gunakan fitur filter untuk memfokuskan pada subset data yang relevan
        """)
    
    # System requirements and technical info
    st.markdown('<p class="sub-header">🔧 Informasi Teknis</p>', unsafe_allow_html=True)
    
    tech_col1, tech_col2 = st.columns(2)
    
    with tech_col1:
        st.markdown("### Persyaratan Sistem")
        st.markdown("""
        - **Browser**: Chrome, Firefox, Safari, atau Edge versi terbaru
        - **Koneksi Internet**: Diperlukan untuk mengakses peta dan menampilkan data
        - **Perangkat**: Dapat diakses dari desktop, laptop, atau tablet
        - **Penyimpanan**: Minimal 4GB RAM untuk data berukuran besar
        - **Performa Optimal**: Untuk dataset >10,000 baris, disarankan menggunakan komputer dengan spesifikasi yang memadai
        """)
    
    with tech_col2:
        st.markdown("### Teknologi yang Digunakan")
        st.markdown("""
        - **Framework**: Streamlit untuk antarmuka web interaktif
        - **Visualisasi**: Folium, Plotly, dan Matplotlib
        - **Analisis Data**: Pandas dan NumPy
        - **Kartografi**: OpenStreetMap, Mapbox, ESRI, CartoDB
        - **UI/UX**: HTML/CSS dengan font-awesome icons
        - **Optimasi**: K-means clustering dan sampling grid untuk penanganan dataset besar
        """)
    
    # Credits and footer
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        <p><strong>Sistem Informasi Manajemen Frekuensi</strong> © 2025</p>
        <p>Dikembangkan dengan ❤️ untuk pengelolaan spektrum frekuensi yang lebih baik</p>
    </div>
    """, unsafe_allow_html=True)

# Add a footer with version info
st.markdown("""
<div style="text-align: center; margin-top: 3rem; padding: 1rem; color: #888;">
    <p>Sistem Informasi Manajemen Frekuensi v2.2.0</p>
    <p>© 2025 All Rights Reserved | Loka Monitor SFR Kendari</p>
</div>
""", unsafe_allow_html=True)