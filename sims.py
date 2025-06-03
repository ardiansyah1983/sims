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
import os
import glob
from pathlib import Path

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
    .error-box {
        background-color: #FFEBEE;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #F44336;
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
    .file-info {
        background-color: #F3E5F5;
        padding: 0.8rem;
        border-radius: 5px;
        border-left: 4px solid #9C27B0;
        margin-bottom: 0.5rem;
    }
    .auto-load-info {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #4CAF50;
        margin-bottom: 1rem;
    }
    .filter-section {
        background-color: #F5F5F5;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #E0E0E0;
    }
    .filter-row {
        margin-bottom: 0.8rem;
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

# Function to create data directory if it doesn't exist
def ensure_data_directory():
    """Create data directory if it doesn't exist"""
    data_dir = Path("data")
    if not data_dir.exists():
        data_dir.mkdir(exist_ok=True)
    return data_dir

# Function to scan and load CSV files from data directory
@st.cache_data
def scan_data_directory():
    """Scan data directory for CSV files and return file information"""
    data_dir = ensure_data_directory()
    csv_files = list(data_dir.glob("*.csv"))
    
    file_info = []
    for file_path in csv_files:
        try:
            # Get file stats
            stat = file_path.stat()
            size_mb = stat.st_size / (1024 * 1024)
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            # Try to read first few rows to get column info
            try:
                sample_df = pd.read_csv(file_path, nrows=5)
                num_columns = len(sample_df.columns)
                columns = list(sample_df.columns)
            except Exception as e:
                num_columns = "Error"
                columns = []
            
            # Count total rows (approximate for large files)
            try:
                total_rows = sum(1 for line in open(file_path)) - 1  # -1 for header
            except:
                total_rows = "Unknown"
            
            file_info.append({
                'filename': file_path.name,
                'path': str(file_path),
                'size_mb': size_mb,
                'modified': modified_time,
                'rows': total_rows,
                'columns': num_columns,
                'column_names': columns
            })
        except Exception as e:
            st.error(f"Error reading file {file_path.name}: {str(e)}")
    
    return file_info

# Function to load CSV file from data directory
@st.cache_data
def load_csv_from_data_dir(file_path):
    """Load CSV file from data directory with error handling"""
    try:
        df = pd.read_csv(file_path)
        return df, None
    except Exception as e:
        return None, str(e)

# Function to auto-detect and load the best CSV file
def auto_load_best_csv():
    """Automatically load the most suitable CSV file from data directory"""
    file_info = scan_data_directory()
    
    if not file_info:
        return None, "Tidak ada file CSV ditemukan di folder 'data'"
    
    # Sort by modification time (most recent first) and then by completeness
    def score_file(file):
        score = 0
        # More recent files get higher score
        days_old = (datetime.now() - file['modified']).days
        score += max(0, 100 - days_old)  # Recent files get up to 100 points
        
        # Files with more columns (likely more complete) get higher score
        if isinstance(file['columns'], int):
            score += file['columns'] * 2
        
        # Files with reasonable size get higher score
        if isinstance(file['size_mb'], float):
            if 0.1 < file['size_mb'] < 100:  # Sweet spot for CSV files
                score += 50
        
        return score
    
    # Sort files by score
    sorted_files = sorted(file_info, key=score_file, reverse=True)
    best_file = sorted_files[0]
    
    # Load the best file
    df, error = load_csv_from_data_dir(best_file['path'])
    
    if df is not None:
        return df, f"Auto-loaded: {best_file['filename']}"
    else:
        return None, f"Error loading {best_file['filename']}: {error}"

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
        try:
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
        except ImportError:
            st.warning("scikit-learn tidak tersedia. Menggunakan random sampling.")
            return df.sample(max_markers, random_state=42)
    
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

# Function to apply filters to dataframe
def apply_filters(df, city_filter, service_filter, client_filter=None, freq_range=None):
    """Apply multiple filters to the dataframe"""
    filtered_df = df.copy()
    
    # Apply city filter
    if city_filter != "All":
        filtered_df = filtered_df[filtered_df['CITY'] == city_filter]
    
    # Apply service filter
    if service_filter != "All":
        filtered_df = filtered_df[filtered_df['SERVICE'] == service_filter]
    
    # Apply client filter if provided
    if client_filter and client_filter != "All":
        filtered_df = filtered_df[filtered_df['CLNT_NAME'] == client_filter]
    
    # Apply frequency range filter if provided
    if freq_range and 'FREQ_MHZ' in df.columns:
        filtered_df = filtered_df[
            (filtered_df['FREQ_MHZ'] >= freq_range[0]) & 
            (filtered_df['FREQ_MHZ'] <= freq_range[1])
        ]
    
    return filtered_df

# Initialize session state for storing uploaded data
if 'data' not in st.session_state:
    st.session_state.data = None
if 'data_source' not in st.session_state:
    st.session_state.data_source = None
if 'available_files' not in st.session_state:
    st.session_state.available_files = []

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
            st.session_state.data_source = f"Manual Upload: {uploaded_file.name}"
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

# Function to process CSV file from data directory
def process_csv_from_data_dir(file_path):
    try:
        # Read CSV into pandas DataFrame
        df = pd.read_csv(file_path)
        
        # Validate the data
        is_valid, message = validate_csv_data(df)
        
        if is_valid:
            # Store the data in session state
            st.session_state.data = df
            st.session_state.data_source = f"Auto-loaded: {Path(file_path).name}"
            
            if isinstance(message, list):
                st.session_state.upload_warnings = message
                st.session_state.upload_message = f"Data berhasil dimuat dari folder data!"
                st.session_state.upload_status = "success"
            else:
                st.session_state.upload_message = f"Data berhasil dimuat dari folder data!"
                st.session_state.upload_status = "success"
                st.session_state.upload_warnings = []
            return True
        else:
            st.session_state.upload_message = f"Error validasi data: {message}"
            st.session_state.upload_status = "error"
            st.session_state.upload_warnings = []
            return False
            
    except Exception as e:
        st.session_state.upload_message = f"Error memproses file: {str(e)}"
        st.session_state.upload_status = "error"
        st.session_state.upload_warnings = []
        return False

# Sidebar for app navigation and settings
with st.sidebar:
    st.image("https://via.placeholder.com/250x80/1E88E5/FFFFFF?text=SIMS", width=250)
    
    st.markdown("### Menu Navigasi")
    app_mode = st.radio(
        "Pilih Mode Aplikasi:",
        ["📊 Dashboard", "🗂️ Data Manager", "📁 File Browser", "📝 Tentang Aplikasi"]
    )
    
    # Auto-load section
    st.markdown("---")
    st.markdown("### 🤖 Auto-Load Data")
    
    # Scan for available files
    file_info = scan_data_directory()
    st.session_state.available_files = file_info
    
    if file_info:
        st.success(f"Ditemukan {len(file_info)} file CSV di folder 'data'")
        
        # Auto-load button
        if st.button("🚀 Auto-Load Data Terbaik", help="Memuat file CSV terbaik secara otomatis"):
            with st.spinner('Memuat data...'):
                df, message = auto_load_best_csv()
                if df is not None:
                    st.session_state.data = df
                    st.session_state.data_source = message
                    st.session_state.upload_status = "success"
                    st.session_state.upload_message = message
                    st.session_state.upload_warnings = []
                    st.success("Data berhasil dimuat!")
                    st.rerun()
                else:
                    st.error(message)
        
        # Manual file selection
        if len(file_info) > 1:
            st.markdown("**Atau pilih file manual:**")
            file_names = [f"{f['filename']} ({f['size_mb']:.1f}MB)" for f in file_info]
            selected_idx = st.selectbox("Pilih file:", range(len(file_names)), format_func=lambda x: file_names[x])
            
            if st.button("📂 Load File Terpilih"):
                selected_file = file_info[selected_idx]
                with st.spinner(f'Memuat {selected_file["filename"]}...'):
                    if process_csv_from_data_dir(selected_file['path']):
                        st.success(f"Data dari {selected_file['filename']} berhasil dimuat!")
                        st.rerun()
    else:
        st.info("Tidak ada file CSV di folder 'data'. Silakan upload manual atau tambahkan file ke folder 'data'.")
    
    # Current data info
    if st.session_state.data is not None:
        st.markdown("---")
        st.markdown("### 📈 Data Saat Ini")
        st.markdown(f"**Sumber:** {st.session_state.data_source}")
        st.markdown(f"**Jumlah Baris:** {len(st.session_state.data):,}")
        
        # Clear data button
        if st.button("🗑️ Hapus Data", help="Hapus data yang sedang dimuat"):
            st.session_state.data = None
            st.session_state.data_source = None
            st.session_state.upload_status = None
            st.session_state.upload_message = ""
            st.session_state.upload_warnings = []
            st.success("Data berhasil dihapus!")
            st.rerun()
    
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
    max_markers = st.slider("Jumlah maksimum marker pada peta:", 1000, 20000, 10000, 1000)
    
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
    st.markdown(f"<div style='text-align: center; color: #888;'>Versi 3.1.0<br>Last updated: {datetime.now().strftime('%d %b %Y')}</div>", unsafe_allow_html=True)

# Main content area based on selected mode
if app_mode == "📁 File Browser":
    # File Browser page
    st.markdown('<p class="sub-header">📁 File Browser - Data Directory</p>', unsafe_allow_html=True)
    
    # Refresh button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()
    
    # Display available files
    file_info = st.session_state.available_files
    
    if file_info:
        st.markdown(f"### 📂 Ditemukan {len(file_info)} file CSV di folder 'data'")
        
        for i, file in enumerate(file_info):
            with st.expander(f"📄 {file['filename']} ({file['size_mb']:.1f} MB)"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Informasi File:**")
                    st.write(f"📅 **Dimodifikasi:** {file['modified'].strftime('%d %b %Y, %H:%M')}")
                    st.write(f"📊 **Jumlah Baris:** {file['rows']:,}" if isinstance(file['rows'], int) else f"📊 **Jumlah Baris:** {file['rows']}")
                    st.write(f"📋 **Jumlah Kolom:** {file['columns']}" if isinstance(file['columns'], int) else f"📋 **Jumlah Kolom:** {file['columns']}")
                
                with col2:
                    if file['column_names']:
                        st.markdown("**Kolom yang Tersedia:**")
                        for col in file['column_names'][:10]:  # Show first 10 columns
                            st.write(f"• {col}")
                        if len(file['column_names']) > 10:
                            st.write(f"• ... dan {len(file['column_names']) - 10} kolom lainnya")
                
                # Action buttons
                btn_col1, btn_col2, btn_col3 = st.columns(3)
                
                with btn_col1:
                    if st.button(f"📖 Preview", key=f"preview_{i}"):
                        try:
                            preview_df = pd.read_csv(file['path'], nrows=10)
                            st.markdown("**Preview 10 baris pertama:**")
                            st.dataframe(preview_df, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error preview: {str(e)}")
                
                with btn_col2:
                    if st.button(f"📊 Load Data", key=f"load_{i}"):
                        with st.spinner(f'Memuat {file["filename"]}...'):
                            if process_csv_from_data_dir(file['path']):
                                st.success(f"Data dari {file['filename']} berhasil dimuat!")
                                st.rerun()
                            else:
                                st.error("Gagal memuat data")
                
                with btn_col3:
                    # Download button
                    with open(file['path'], 'rb') as f:
                        st.download_button(
                            label="💾 Download",
                            data=f.read(),
                            file_name=file['filename'],
                            mime='text/csv',
                            key=f"download_{i}"
                        )
    else:
        st.markdown("""
        <div class="warning-box">
            <h3>Folder 'data' Kosong</h3>
            <p>Tidak ada file CSV yang ditemukan di folder 'data'.</p>
            <p>Untuk menggunakan fitur auto-load:</p>
            <ol>
                <li>Buat folder bernama 'data' di direktori aplikasi</li>
                <li>Letakkan file CSV Anda di dalam folder tersebut</li>
                <li>Klik tombol 'Refresh' di atas</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        # Instructions for creating data folder
        st.markdown("### 📋 Panduan Setup Folder Data")
        st.code("""
# Struktur folder yang direkomendasikan:
your_app_directory/
├── app.py (file aplikasi utama)
├── data/
│   ├── frequency_data_2024.csv
│   ├── frequency_data_2025.csv
│   └── backup_data.csv
└── komdigi.png (logo)
        """)

elif app_mode == "🗂️ Data Manager":
    # Data Manager page - combines upload and data management
    st.markdown('<p class="sub-header">🗂️ Data Manager</p>', unsafe_allow_html=True)
    
    # Create tabs for different data management functions
    data_tab1, data_tab2, data_tab3 = st.tabs(["📤 Upload Manual", "📁 Auto-Load Status", "🔍 Data Analysis"])
    
    with data_tab1:
        st.markdown("### 📤 Upload Data Manual")
        
        # Upload container with styling
        st.markdown('<div class="upload-container">', unsafe_allow_html=True)
        
        # File uploader
        uploaded_file = st.file_uploader("Pilih file CSV untuk diunggah", type=["csv"])
        
        if uploaded_file is not None and uploaded_file != st.session_state.uploaded_file:
            st.session_state.uploaded_file = uploaded_file
            with st.spinner('Memproses file...'):
                process_uploaded_file(uploaded_file)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Display upload status messages
        if st.session_state.upload_status == "success":
            st.success(st.session_state.upload_message)
            
            # Display warnings if any
            if st.session_state.upload_warnings:
                for warning in st.session_state.upload_warnings:
                    st.warning(warning)
        
        elif st.session_state.upload_status == "error":
            st.error(st.session_state.upload_message)
        
        # Instructions
        with st.expander("📋 Panduan Upload Data"):
            st.markdown("""
            #### Format Data yang Diperlukan
            
            **Kolom Wajib:**
            - `CITY` - Kota lokasi pemancar
            - `CLNT_NAME` - Nama klien/pengguna frekuensi
            - `STN_NAME` - Nama stasiun/pemancar
            - `SERVICE` - Kategori layanan (Broadcasting, Mobile, Satellite, dll)
            - `SUBSERVICE` - Sub kategori layanan (FM Radio, 4G LTE, 5G, dll)
            - `SID_LONG` - Koordinat longitude (bujur) lokasi
            - `SID_LAT` - Koordinat latitude (lintang) lokasi
            
            **Kolom Opsional:**
            - `FREQ_MHZ` - Frekuensi dalam MHz
            - `BW_MHZ` - Bandwidth dalam MHz
            - `DATE` - Tanggal registrasi/pembaruan data
            - `TX_POWER` - Daya pancar dalam Watt
            - `ANTENNA_HEIGHT` - Tinggi antena dalam meter
            - `POLARIZATION` - Polarisasi antena
            """)
    
    with data_tab2:
        st.markdown("### 📁 Status Auto-Load")
        
        if st.session_state.data is not None:
            st.markdown(f"""
            <div class="auto-load-info">
                <h4>✅ Data Aktif</h4>
                <p><strong>Sumber:</strong> {st.session_state.data_source}</p>
                <p><strong>Jumlah Baris:</strong> {len(st.session_state.data):,}</p>
                <p><strong>Jumlah Kolom:</strong> {len(st.session_state.data.columns)}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show data preview
            st.markdown("#### Preview Data")
            st.dataframe(st.session_state.data.head(), use_container_width=True)
            
            # Data info
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Baris", f"{len(st.session_state.data):,}")
            with col2:
                st.metric("Kota Unik", f"{st.session_state.data['CITY'].nunique():,}")
            with col3:
                st.metric("Klien Unik", f"{st.session_state.data['CLNT_NAME'].nunique():,}")
            with col4:
                st.metric("Layanan Unik", f"{st.session_state.data['SERVICE'].nunique():,}")
        
        else:
            st.markdown("""
            <div class="warning-box">
                <h4>⚠️ Tidak Ada Data Aktif</h4>
                <p>Belum ada data yang dimuat. Gunakan salah satu metode berikut:</p>
                <ul>
                    <li>Upload file manual di tab "Upload Manual"</li>
                    <li>Gunakan tombol "Auto-Load" di sidebar</li>
                    <li>Pilih file dari "File Browser"</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Available files in data directory
        st.markdown("#### 📂 File Tersedia di Folder Data")
        
        if st.session_state.available_files:
            for file in st.session_state.available_files:
                st.markdown(f"""
                <div class="file-info">
                    <strong>{file['filename']}</strong> ({file['size_mb']:.1f} MB)<br>
                    <small>📅 {file['modified'].strftime('%d %b %Y, %H:%M')} | 📊 {file['rows']} baris | 📋 {file['columns']} kolom</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Tidak ada file CSV di folder 'data'")
    
    with data_tab3:
        if st.session_state.data is not None:
            st.markdown("### 🔍 Analisis Data")
            
            df = st.session_state.data
            
            # Data quality analysis
            st.markdown("#### 📊 Kualitas Data")
            
            qual_col1, qual_col2 = st.columns(2)
            
            with qual_col1:
                # Missing data analysis
                missing_data = df.isnull().sum()
                missing_pct = (missing_data / len(df)) * 100
                
                missing_df = pd.DataFrame({
                    'Kolom': missing_data.index,
                    'Missing Count': missing_data.values,
                    'Missing %': missing_pct.values
                }).sort_values('Missing %', ascending=False)
                
                st.markdown("**Data yang Hilang:**")
                st.dataframe(missing_df, use_container_width=True)
            
            with qual_col2:
                # Data types
                dtype_df = pd.DataFrame({
                    'Kolom': df.dtypes.index,
                    'Tipe Data': df.dtypes.values.astype(str)
                })
                
                st.markdown("**Tipe Data:**")
                st.dataframe(dtype_df, use_container_width=True)
            
            # Coordinate validation
            st.markdown("#### 🗺️ Validasi Koordinat")
            
            coord_issues = []
            
            # Check for invalid coordinates
            invalid_lat = df[(df['SID_LAT'] < -90) | (df['SID_LAT'] > 90)]
            invalid_long = df[(df['SID_LONG'] < -180) | (df['SID_LONG'] > 180)]
            
            if not invalid_lat.empty:
                coord_issues.append(f"⚠️ {len(invalid_lat)} baris dengan latitude tidak valid")
            
            if not invalid_long.empty:
                coord_issues.append(f"⚠️ {len(invalid_long)} baris dengan longitude tidak valid")
            
            # Check for suspicious coordinates (e.g., 0,0)
            suspicious_coords = df[(df['SID_LAT'] == 0) & (df['SID_LONG'] == 0)]
            if not suspicious_coords.empty:
                coord_issues.append(f"⚠️ {len(suspicious_coords)} baris dengan koordinat (0,0) - mungkin data kosong")
            
            # Check coordinate precision
            lat_precision = df['SID_LAT'].apply(lambda x: len(str(x).split('.')[-1]) if '.' in str(x) else 0)
            long_precision = df['SID_LONG'].apply(lambda x: len(str(x).split('.')[-1]) if '.' in str(x) else 0)
            
            if lat_precision.mean() < 4 or long_precision.mean() < 4:
                coord_issues.append("⚠️ Presisi koordinat rendah (kurang dari 4 digit desimal)")
            
            if coord_issues:
                for issue in coord_issues:
                    st.warning(issue)
            else:
                st.success("✅ Semua koordinat valid")
            
            # Frequency analysis (if available)
            if 'FREQ_MHZ' in df.columns:
                st.markdown("#### 📡 Analisis Frekuensi")
                
                freq_col1, freq_col2 = st.columns(2)
                
                with freq_col1:
                    freq_stats = df['FREQ_MHZ'].describe()
                    st.markdown("**Statistik Frekuensi:**")
                    st.dataframe(freq_stats, use_container_width=True)
                
                with freq_col2:
                    # Frequency bands distribution
                    df['FREQ_BAND'] = df['FREQ_MHZ'].apply(get_frequency_band)
                    band_counts = df['FREQ_BAND'].value_counts()
                    
                    st.markdown("**Distribusi Band Frekuensi:**")
                    st.dataframe(band_counts, use_container_width=True)
        else:
            st.info("Muat data terlebih dahulu untuk melakukan analisis")

elif app_mode == "📊 Dashboard":
    # Dashboard display - check if data exists
    if st.session_state.data is not None:
        st.markdown('<p class="sub-header">📊 Dashboard Informasi Frekuensi</p>', unsafe_allow_html=True)
        
        # Get dataframe from session state
        df = st.session_state.data
        
        # Show data source info
        st.markdown(f"""
        <div class="auto-load-info">
            <strong>📊 Data Sumber:</strong> {st.session_state.data_source}
        </div>
        """, unsafe_allow_html=True)
        
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
            
            # Enhanced Filter Section
            st.markdown('<div class="filter-section">', unsafe_allow_html=True)
            st.markdown("#### 🔍 Filter Data")
            
            # Filter row 1: Map type and display mode
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                map_type = st.selectbox(
                    "🗺️ Jenis Peta:",
                    ["OpenStreetMap", "Esri Satellite", "CartoDB Dark"],
                    key="dash_map_type"
                )
            
            with filter_col2:
                display_mode = st.selectbox(
                    "👁️ Mode Tampilan:",
                    ["Markers + Heatmap", "Markers", "Heatmap"],
                    key="dash_display_mode"
                )
            
            # Filter row 2: City, Service, and Client filters
            filter_col3, filter_col4, filter_col5 = st.columns(3)
            
            with filter_col3:
                # City filter - Enhanced with search and count
                dash_cities = ["All"] + sorted(df['CITY'].unique().tolist())
                city_counts = df['CITY'].value_counts()
                
                # Format city options with counts
                city_options = ["All (Semua Kota)"]
                for city in dash_cities[1:]:  # Skip "All"
                    count = city_counts.get(city, 0)
                    city_options.append(f"{city} ({count:,} lokasi)")
                
                selected_city_idx = st.selectbox(
                    "🏙️ Filter Kota:",
                    range(len(city_options)),
                    format_func=lambda x: city_options[x],
                    key="dash_city"
                )
                
                # Get actual city name
                if selected_city_idx == 0:
                    dash_city = "All"
                else:
                    dash_city = dash_cities[selected_city_idx]
            
            with filter_col4:
                # Service filter with counts
                dash_services = ["All"] + sorted(df['SERVICE'].unique().tolist())
                service_counts = df['SERVICE'].value_counts()
                
                service_options = ["All (Semua Layanan)"]
                for service in dash_services[1:]:
                    count = service_counts.get(service, 0)
                    service_options.append(f"{service} ({count:,} lokasi)")
                
                selected_service_idx = st.selectbox(
                    "📡 Filter Layanan:",
                    range(len(service_options)),
                    format_func=lambda x: service_options[x],
                    key="dash_service"
                )
                
                if selected_service_idx == 0:
                    dash_service = "All"
                else:
                    dash_service = dash_services[selected_service_idx]
            
            with filter_col5:
                # Client filter (optional, only if many clients)
                if df['CLNT_NAME'].nunique() <= 50:  # Show client filter only if reasonable number
                    dash_clients = ["All"] + sorted(df['CLNT_NAME'].unique().tolist())
                    client_counts = df['CLNT_NAME'].value_counts()
                    
                    client_options = ["All (Semua Klien)"]
                    for client in dash_clients[1:]:
                        count = client_counts.get(client, 0)
                        client_options.append(f"{client} ({count:,} lokasi)")
                    
                    selected_client_idx = st.selectbox(
                        "🏢 Filter Klien:",
                        range(len(client_options)),
                        format_func=lambda x: client_options[x],
                        key="dash_client"
                    )
                    
                    if selected_client_idx == 0:
                        dash_client = "All"
                    else:
                        dash_client = dash_clients[selected_client_idx]
                else:
                    dash_client = "All"
                    st.info(f"Filter klien disembunyikan ({df['CLNT_NAME'].nunique():,} klien unik)")
            
            # Frequency filter (if frequency data available)
            if 'FREQ_MHZ' in df.columns:
                st.markdown("#### 📊 Filter Frekuensi")
                freq_col1, freq_col2 = st.columns(2)
                
                with freq_col1:
                    min_freq = float(df['FREQ_MHZ'].min())
                    max_freq = float(df['FREQ_MHZ'].max())
                    freq_range = st.slider(
                        "🔊 Rentang Frekuensi (MHz):",
                        min_value=min_freq,
                        max_value=max_freq,
                        value=(min_freq, max_freq),
                        key="dash_freq_range"
                    )
                
                with freq_col2:
                    # Frequency band filter
                    freq_bands = ["All"] + sorted(df['FREQ_MHZ'].apply(get_frequency_band).unique().tolist())
                    selected_band = st.selectbox(
                        "📈 Filter Band Frekuensi:",
                        freq_bands,
                        key="dash_freq_band"
                    )
            else:
                freq_range = None
                selected_band = "All"
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Apply all filters
            filtered_data = apply_filters(df, dash_city, dash_service, dash_client, freq_range)
            
            # Apply frequency band filter if available
            if 'FREQ_MHZ' in df.columns and selected_band != "All":
                filtered_data = filtered_data[filtered_data['FREQ_MHZ'].apply(get_frequency_band) == selected_band]
            
            # Show filter results
            st.markdown(f"""
            <div class="info-box">
                📍 <strong>Data Terfilter:</strong> {len(filtered_data):,} dari {len(df):,} lokasi 
                ({(len(filtered_data)/len(df)*100):.1f}%)
            </div>
            """, unsafe_allow_html=True)
            
            if len(filtered_data) == 0:
                st.warning("⚠️ Tidak ada data yang sesuai dengan filter. Silakan sesuaikan kriteria filter.")
            else:
                # Optimize data for map display
                if len(filtered_data) > max_markers:
                    dash_map_data = optimize_map_data(filtered_data, max_markers, sampling_method)
                    st.info(f"Dataset terfilter terlalu besar ({len(filtered_data):,} data). Menampilkan sampel {len(dash_map_data):,} titik untuk performa optimal.")
                else:
                    dash_map_data = filtered_data
                
                # Define map center
                avg_lat = dash_map_data['SID_LAT'].mean()
                avg_long = dash_map_data['SID_LONG'].mean()
                
                # Create base map
                if map_type == "OpenStreetMap":
                    m = folium.Map(location=[avg_lat, avg_long], zoom_start=6, tiles="OpenStreetMap")
                elif map_type == "Esri Satellite":
                    m = folium.Map(location=[avg_lat, avg_long], zoom_start=6, 
                                  tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                                  attr="Esri")
                elif map_type == "CartoDB Dark":
                    m = folium.Map(location=[avg_lat, avg_long], zoom_start=6, tiles="CartoDB dark_matter")
                
                # Add plugins
                MiniMap().add_to(m)
                LocateControl().add_to(m)
                Fullscreen().add_to(m)
                MousePosition().add_to(m)
                
                # Add markers
                if display_mode in ["Markers", "Markers + Heatmap"]:
                    marker_cluster = MarkerCluster().add_to(m)
                    
                    for _, row in dash_map_data.iterrows():
                        service_info = get_service_icon(row['SERVICE'])
                        icon_color = service_info['color']
                        
                        # Create popup
                        popup_content = create_popup_content(row)
                        popup = folium.Popup(folium.Html(popup_content, script=True), max_width=350)
                        
                        # Add marker to cluster
                        folium.Marker(
                            location=[row['SID_LAT'], row['SID_LONG']],
                            popup=popup,
                            icon=folium.Icon(color='blue', icon='info-sign'),
                            tooltip=f"{row['STN_NAME']} - {row['SERVICE']}"
                        ).add_to(marker_cluster)
                
                # Add heatmap
                if display_mode in ["Heatmap", "Markers + Heatmap"]:
                    heat_data = [[row['SID_LAT'], row['SID_LONG']] for _, row in dash_map_data.iterrows()]
                    HeatMap(heat_data, radius=15, blur=10).add_to(m)
                
                # Add legend for services
                if display_mode in ["Markers", "Markers + Heatmap"]:
                    legend_html = """
                    <div style="position: fixed; bottom: 50px; right: 50px; z-index: 1000; background-color: white; 
                                padding: 10px; border: 2px solid grey; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                        <p style="text-align: center; font-weight: bold; margin-bottom: 10px;">Legenda Layanan</p>
                    """
                    
                    # Add legend items based on unique services in the filtered data
                    for service in sorted(dash_map_data['SERVICE'].unique()):
                        service_info = get_service_icon(service)
                        count = len(dash_map_data[dash_map_data['SERVICE'] == service])
                        legend_html += f"""
                        <div style="display: flex; align-items: center; margin-bottom: 5px;">
                            <div style="width: 20px; height: 20px; border-radius: 50%; background-color: {service_info['color']}; margin-right: 8px;"></div>
                            <span style="font-size: 12px;">{service} ({count})</span>
                        </div>
                        """
                    
                    legend_html += """
                    </div>
                    """
                    
                    # Add legend as HTML
                    m.get_root().html.add_child(folium.Element(legend_html))
                
                # Display map
                st.markdown("#### 🗺️ Peta Interaktif")
                folium_static(m, width=1000, height=600)
                
                # Show additional statistics
                st.markdown("#### 📊 Statistik Data Terfilter")
                stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                
                with stat_col1:
                    st.metric("📍 Total Lokasi", f"{len(filtered_data):,}")
                
                with stat_col2:
                    st.metric("🏙️ Jumlah Kota", f"{filtered_data['CITY'].nunique():,}")
                
                with stat_col3:
                    st.metric("📡 Jenis Layanan", f"{filtered_data['SERVICE'].nunique():,}")
                
                with stat_col4:
                    st.metric("🏢 Jumlah Klien", f"{filtered_data['CLNT_NAME'].nunique():,}")
                
                # Export filtered data
                if st.button("📥 Export Data Terfilter", key="export_filtered"):
                    csv = filtered_data.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()
                    href = f'<a href="data:file/csv;base64,{b64}" download="filtered_frequency_data.csv">Download CSV</a>'
                    st.markdown(href, unsafe_allow_html=True)
        
        with dash_tab2:
            st.markdown("### 📊 Statistik Layanan Frekuensi")
            
            # Service distribution
            service_counts = df['SERVICE'].value_counts().reset_index()
            service_counts.columns = ['SERVICE', 'COUNT']
            
            fig = px.bar(
                service_counts,
                x='SERVICE',
                y='COUNT',
                color='SERVICE',
                title='Distribusi Jenis Layanan',
                labels={'SERVICE': 'Jenis Layanan', 'COUNT': 'Jumlah'}
            )
            
            fig.update_layout(xaxis_title='Jenis Layanan', yaxis_title='Jumlah')
            st.plotly_chart(fig, use_container_width=True)
            
            # Check if frequency data exists for additional analysis
            if 'FREQ_MHZ' in df.columns:
                # Frequency analysis by service
                freq_col1, freq_col2 = st.columns(2)
                
                with freq_col1:
                    # Box plot of frequency by service
                    fig_box = px.box(
                        df,
                        x='SERVICE',
                        y='FREQ_MHZ',
                        color='SERVICE',
                        title='Distribusi Frekuensi per Layanan',
                        labels={'SERVICE': 'Jenis Layanan', 'FREQ_MHZ': 'Frekuensi (MHz)'}
                    )
                    fig_box.update_layout(xaxis_title='Jenis Layanan', yaxis_title='Frekuensi (MHz)')
                    st.plotly_chart(fig_box, use_container_width=True)
                
                with freq_col2:
                    # Average frequency per service
                    avg_freq_service = df.groupby('SERVICE')['FREQ_MHZ'].mean().reset_index()
                    avg_freq_service.columns = ['SERVICE', 'AVG_FREQ']
                    avg_freq_service = avg_freq_service.sort_values('AVG_FREQ')
                    
                    fig_avg = px.bar(
                        avg_freq_service,
                        y='SERVICE',
                        x='AVG_FREQ',
                        color='SERVICE',
                        title='Rata-rata Frekuensi per Layanan',
                        labels={'SERVICE': 'Jenis Layanan', 'AVG_FREQ': 'Rata-rata Frekuensi (MHz)'},
                        orientation='h'
                    )
                    fig_avg.update_layout(yaxis_title='Jenis Layanan', xaxis_title='Rata-rata Frekuensi (MHz)')
                    st.plotly_chart(fig_avg, use_container_width=True)
            
            # Subservice distribution
            subservice_counts = df['SUBSERVICE'].value_counts().reset_index()
            subservice_counts.columns = ['SUBSERVICE', 'COUNT']
            
            if len(subservice_counts) > 15:
                subservice_counts = subservice_counts.head(15)
                title = 'Distribusi Sub-layanan (Top 15)'
            else:
                title = 'Distribusi Sub-layanan'
            
            fig2 = px.bar(
                subservice_counts,
                y='SUBSERVICE',
                x='COUNT',
                color='COUNT',
                title=title,
                labels={'SUBSERVICE': 'Sub-layanan', 'COUNT': 'Jumlah'},
                orientation='h',
                color_continuous_scale='Viridis'
            )
            
            fig2.update_layout(yaxis_title='Sub-layanan', xaxis_title='Jumlah', yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig2, use_container_width=True)
        
        with dash_tab3:
            st.markdown("### 🏙️ Distribusi Kota")
            
            city_counts = df['CITY'].value_counts().reset_index()
            city_counts.columns = ['CITY', 'COUNT']
            
            if len(city_counts) > 20:
                city_counts = city_counts.head(20)
                title = 'Top 20 Kota berdasarkan Jumlah Pemancar'
            else:
                title = 'Kota berdasarkan Jumlah Pemancar'
            
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
            
            fig.update_layout(yaxis_title='Kota', xaxis_title='Jumlah Pemancar', yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Create cross-tab analysis between cities and services
            if df['CITY'].nunique() <= 20:  # Only show if reasonable number of cities
                st.markdown("#### 🔥 Heatmap Layanan per Kota")
                
                # Create cross-tabulation
                city_service_cross = pd.crosstab(df['CITY'], df['SERVICE'])
                
                # Create heatmap
                fig_heatmap = px.imshow(
                    city_service_cross,
                    labels=dict(x="Jenis Layanan", y="Kota", color="Jumlah Pemancar"),
                    title="Distribusi Layanan per Kota",
                    aspect="auto",
                    color_continuous_scale='YlOrRd'
                )
                
                fig_heatmap.update_layout(
                    xaxis_title='Jenis Layanan', 
                    yaxis_title='Kota',
                    height=400
                )
                
                st.plotly_chart(fig_heatmap, use_container_width=True)
            
            # City statistics summary
            st.markdown("#### 📈 Statistik Kota")
            
            city_stats = df.groupby('CITY').agg({
                'STN_NAME': 'count',
                'SERVICE': 'nunique',
                'CLNT_NAME': 'nunique'
            }).rename(columns={
                'STN_NAME': 'Total_Pemancar',
                'SERVICE': 'Jenis_Layanan',
                'CLNT_NAME': 'Jumlah_Klien'
            }).sort_values('Total_Pemancar', ascending=False)
            
            # Add frequency stats if available
            if 'FREQ_MHZ' in df.columns:
                freq_stats = df.groupby('CITY')['FREQ_MHZ'].agg(['mean', 'min', 'max']).round(2)
                freq_stats.columns = ['Rata_Freq_MHz', 'Min_Freq_MHz', 'Max_Freq_MHz']
                city_stats = pd.concat([city_stats, freq_stats], axis=1)
            
            st.dataframe(city_stats.head(20), use_container_width=True)
    else:
        # No data available
        st.markdown('<p class="sub-header">📊 Dashboard Informasi Frekuensi</p>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="warning-box">
            <h3>Data Belum Tersedia</h3>
            <p>Belum ada data frekuensi yang diunggah untuk ditampilkan di dashboard.</p>
            <p>Gunakan salah satu opsi berikut:</p>
            <ul>
                <li>Klik tombol "🚀 Auto-Load Data Terbaik" di sidebar</li>
                <li>Beralih ke tab "🗂️ Data Manager" untuk upload manual</li>
                <li>Gunakan "📁 File Browser" untuk memilih file</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

elif app_mode == "📝 Tentang Aplikasi":
    # About the application
    st.markdown('<p class="sub-header">🌟 Tentang Aplikasi</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <h3>Sistem Informasi Manajemen Frekuensi v3.1</h3>
    <p>Aplikasi ini dirancang untuk mempermudah pengelolaan dan visualisasi data frekuensi radio beserta lokasi penggunanya. 
    Versi 3.1 memiliki fitur enhanced filtering termasuk filter kota yang komprehensif pada peta distribusi frekuensi.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Fitur Baru v3.1")
        st.markdown("""
        - **🏙️ Enhanced City Filter**: Filter kota dengan hitungan lokasi real-time
        - **📊 Multi-Filter Dashboard**: Filter berdasarkan kota, layanan, klien, dan frekuensi
        - **🔍 Smart Filter Interface**: Interface filter yang lebih intuitif dengan info statistik
        - **📈 Advanced Statistics**: Statistik detail per kota dengan analisis cross-tab
        - **🗺️ Interactive Legend**: Legend dinamis yang menunjukkan jumlah lokasi per layanan
        - **📥 Export Filtered Data**: Export data hasil filter langsung dari dashboard
        """)
    
    with col2:
        st.markdown("### 🔑 Fitur Utama")
        st.markdown("""
        - **🤖 Auto-Load Data**: Membaca file CSV otomatis dari folder 'data'
        - **📁 File Browser**: Jelajahi dan kelola file di folder data
        - **🗂️ Data Manager**: Manajemen data terpusat dengan analisis kualitas
        - **Peta Multi-Layer**: Visualisasi dengan berbagai jenis peta
        - **Filter Data Dinamis**: Filter berdasarkan berbagai kriteria
        - **Clustering Otomatis**: Optimasi tampilan untuk dataset besar
        - **Heat Map**: Visualisasi kepadatan penggunaan frekuensi
        - **Analitik Frekuensi**: Grafik dan statistik komprehensif
        """)
    
    st.markdown("### 📋 Setup Folder Data")
    st.markdown("""
    Untuk menggunakan fitur auto-load, buat struktur folder sebagai berikut:
    """)
    
    st.code("""
your_app_directory/
├── app.py (file aplikasi utama)
├── data/                    # Folder untuk file CSV
│   ├── frequency_data_2024.csv
│   ├── frequency_data_2025.csv
│   ├── backup_data.csv
│   └── monthly_report.csv
├── komdigi.png (opsional)
└── requirements.txt
    """)
    
    st.markdown("### 🚀 Cara Menggunakan Enhanced Filter")
    
    with st.expander("📖 Panduan Penggunaan Filter Baru"):
        st.markdown("""
        #### 1. Filter Kota (Enhanced)
        - **Tampilan Otomatis**: Setiap opsi kota menampilkan jumlah lokasi dalam kurung
        - **Pencarian Cepat**: Gunakan dropdown yang dapat dicari untuk kota dengan banyak pilihan
        - **Statistik Real-time**: Melihat jumlah lokasi yang tersedia per kota
        
        #### 2. Filter Multi-Kriteria
        - **Kombinasi Filter**: Gabungkan filter kota, layanan, dan klien sekaligus
        - **Filter Frekuensi**: Gunakan slider untuk rentang frekuensi atau pilih band tertentu
        - **Preview Hasil**: Lihat jumlah data terfilter sebelum tampil di peta
        
        #### 3. Visualisasi Interaktif
        - **Legend Dinamis**: Legend menampilkan jumlah lokasi per jenis layanan
        - **Export Data**: Ekspor hasil filter langsung dalam format CSV
        - **Statistik Detail**: Lihat breakdown statistik dari data yang terfilter
        
        #### 4. Tips Optimasi Performa
        - **Dataset Besar**: Sistem otomatis mengoptimasi tampilan untuk dataset >10,000 titik
        - **Sampling Method**: Pilih metode sampling di sidebar untuk performa terbaik
        - **Filter Bertahap**: Gunakan filter bertahap untuk mempersempit data sebelum visualisasi
        """)
    
    st.markdown("### 📊 Format Data yang Didukung")
    
    with st.expander("📄 Spesifikasi File CSV"):
        st.markdown("""
        #### Kolom Wajib:
        - `CITY` - Nama kota lokasi pemancar
        - `CLNT_NAME` - Nama klien/pengguna frekuensi  
        - `STN_NAME` - Nama stasiun/pemancar
        - `SERVICE` - Kategori layanan (Broadcasting, Mobile, Satellite, dll)
        - `SUBSERVICE` - Sub kategori layanan (FM Radio, 4G LTE, 5G, dll)
        - `SID_LAT` - Koordinat latitude (lintang) dalam format desimal
        - `SID_LONG` - Koordinat longitude (bujur) dalam format desimal
        
        #### Kolom Opsional:
        - `FREQ_MHZ` - Frekuensi dalam MHz (untuk analisis spektrum)
        - `BW_MHZ` - Bandwidth dalam MHz
        - `DATE` - Tanggal registrasi/pembaruan data
        - `TX_POWER` - Daya pancar dalam Watt
        - `ANTENNA_HEIGHT` - Tinggi antena dalam meter
        - `POLARIZATION` - Polarisasi antena (H/V/Circular)
        
        #### Contoh Data Valid:
        ```csv
        CITY,CLNT_NAME,STN_NAME,SERVICE,SUBSERVICE,SID_LAT,SID_LONG,FREQ_MHZ
        Jakarta,PT Telkom,Jakarta Tower,Broadcasting,FM Radio,-6.2088,106.8456,98.5
        Surabaya,PT XL,Surabaya BTS,Mobile,4G LTE,-7.2575,112.7520,1800.0
        ```
        """)

# Sample data generator for testing
if st.sidebar.button("🧪 Generate Sample Data", help="Buat data contoh untuk testing"):
    sample_data = {
        'CITY': ['Jakarta', 'Surabaya', 'Bandung', 'Medan', 'Makassar'] * 20,
        'CLNT_NAME': ['PT Telkom', 'PT XL', 'PT Indosat', 'PT Smartfren', 'PT Tri'] * 20,
        'STN_NAME': [f'Station_{i}' for i in range(100)],
        'SERVICE': ['Broadcasting', 'Mobile', 'Cellular', 'Satellite', 'Radio'] * 20,
        'SUBSERVICE': ['FM Radio', '4G LTE', '5G', 'Satellite Internet', 'AM Radio'] * 20,
        'SID_LAT': np.random.uniform(-10, 5, 100),
        'SID_LONG': np.random.uniform(95, 140, 100),
        'FREQ_MHZ': np.random.uniform(50, 3000, 100)
    }
    
    sample_df = pd.DataFrame(sample_data)
    st.session_state.data = sample_df
    st.session_state.data_source = "Generated Sample Data"
    st.session_state.upload_status = "success"
    st.session_state.upload_message = "Sample data generated successfully!"
    st.success("Sample data berhasil dibuat! Refresh halaman untuk melihat data.")

# Add footer
st.markdown("---")
st.markdown("""
<div class="footer">
    <p><strong>Sistem Informasi Manajemen Frekuensi v3.1</strong> © 2025</p>
    <p>Dikembangkan dengan ❤️ untuk pengelolaan spektrum frekuensi yang lebih baik</p>
    <p>✨ <strong>New v3.1:</strong> Enhanced City Filter | Multi-Criteria Filtering | Advanced Statistics | Export Filtered Data</p>
</div>
""", unsafe_allow_html=True)