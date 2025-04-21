import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster, HeatMap
import io
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import base64

# Set page title and layout
st.set_page_config(page_title="Sistem Informasi Manajemen Frekuensi", layout="wide")

# Header dengan styling
st.markdown("""
# 📡 Sistem Informasi Manajemen Frekuensi
Aplikasi untuk mengelola dan memvisualisasikan data frekuensi beserta lokasi pengguna
""")

# Function to create custom icon based on service type
def get_service_icon(service):
    """Return custom icon HTML based on service type"""
    icon_map = {
        'Broadcasting': 'tower-broadcast',
        'Mobile': 'signal',
        'Cellular': 'tower-cell',
        'Satellite': 'satellite-dish',
        'Microwave': 'wifi',
        'Radio': 'radio',
        'TV': 'tv',
        'Amateur': 'walkie-talkie',
        'Maritime': 'ship',
        'Aviation': 'plane'
    }
    
    # Default to signal icon if service not in map
    icon_name = icon_map.get(service, 'signal')
    
    return icon_name

# Upload file section
st.subheader("Upload Data Frekuensi")
uploaded_file = st.file_uploader("Pilih file CSV data frekuensi", type=["csv"])

# Main processing
if uploaded_file is not None:
    # Read the CSV file
    try:
        df = pd.read_csv(uploaded_file)
        
        # Display success message and basic info
        st.success("✅ File berhasil diupload!")
        
        # Informasi ringkasan data
        st.write(f"📊 Jumlah data: {len(df)} baris")
        
        # Check if required columns exist
        required_columns = ['CITY', 'CLNT_NAME', 'STN_NAME', 'SERVICE', 'SUBSERVICE', 'SID_LONG', 'SID_LAT']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        # Cek apakah kolom CITY itu sebenarnya CIRY (typo umum)
        if 'CITY' not in df.columns and 'CIRY' in df.columns:
            df = df.rename(columns={'CIRY': 'CITY'})
            st.info("ℹ️ Kolom 'CIRY' diubah menjadi 'CITY'")
            if 'CITY' in missing_columns:
                missing_columns.remove('CITY')
        
        if missing_columns:
            st.error(f"❌ File tidak memiliki kolom yang diperlukan: {', '.join(missing_columns)}")
            st.stop()
        
        # Konversi koordinat ke numerik dan bersihkan nilai yang tidak valid
        df['SID_LAT'] = pd.to_numeric(df['SID_LAT'], errors='coerce')
        df['SID_LONG'] = pd.to_numeric(df['SID_LONG'], errors='coerce')
        
        # Validasi koordinat (latitude: -90 to 90, longitude: -180 to 180)
        invalid_coords = ((df['SID_LAT'] < -90) | (df['SID_LAT'] > 90) | 
                          (df['SID_LONG'] < -180) | (df['SID_LONG'] > 180))
        
        if invalid_coords.any():
            st.warning(f"⚠️ {invalid_coords.sum()} data memiliki koordinat yang tidak valid dan akan diabaikan pada visualisasi peta.")
            # Set invalid coordinates to NaN
            df.loc[invalid_coords, ['SID_LAT', 'SID_LONG']] = np.nan
        
        # Show data preview in expandable section
        with st.expander("Preview Data"):
            st.dataframe(df.head(10), use_container_width=True)
        
        # Create dashboard layout with tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard & Filter", "🗺️ Peta Lokasi", "📈 Visualisasi Data", "📋 Tabel Data Lengkap"])
        
        with tab1:
            # Create two columns for the layout
            st.subheader("Dashboard Manajemen Frekuensi")
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown("### 🔍 Filter Data")
                
                # Filter for column CITY
                cities = ['Semua'] + sorted(df['CITY'].unique().tolist())
                selected_city = st.selectbox('Pilih Kota:', cities)
                
                # Filter for column CLNT_NAME
                clients = ['Semua'] + sorted(df['CLNT_NAME'].unique().tolist())
                selected_client = st.selectbox('Pilih Klien:', clients)
                
                # Filter for column STN_NAME
                stations = ['Semua'] + sorted(df['STN_NAME'].unique().tolist())
                selected_station = st.selectbox('Pilih Stasiun:', stations)
                
                # Filter for column SERVICE
                services = ['Semua'] + sorted(df['SERVICE'].unique().tolist())
                selected_service = st.selectbox('Pilih Layanan:', services)
                
                # Filter for column SUBSERVICE
                subservices = ['Semua'] + sorted(df['SUBSERVICE'].unique().tolist())
                selected_subservice = st.selectbox('Pilih Sub-Layanan:', subservices)
            
            # Apply filters to the dataframe
            filtered_df = df.copy()
            
            if selected_city != 'Semua':
                filtered_df = filtered_df[filtered_df['CITY'] == selected_city]
            
            if selected_client != 'Semua':
                filtered_df = filtered_df[filtered_df['CLNT_NAME'] == selected_client]
            
            if selected_station != 'Semua':
                filtered_df = filtered_df[filtered_df['STN_NAME'] == selected_station]
            
            if selected_service != 'Semua':
                filtered_df = filtered_df[filtered_df['SERVICE'] == selected_service]
            
            if selected_subservice != 'Semua':
                filtered_df = filtered_df[filtered_df['SUBSERVICE'] == selected_subservice]
            
            with col2:
                # Menampilkan metrik dan statistik ringkasan
                st.markdown("### 📈 Ringkasan Data")
                
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                
                with metric_col1:
                    st.metric("Total Data", len(filtered_df))
                
                with metric_col2:
                    st.metric("Jumlah Kota", filtered_df['CITY'].nunique())
                
                with metric_col3:
                    st.metric("Jumlah Klien", filtered_df['CLNT_NAME'].nunique())
                
                # Menampilkan distribusi layanan
                st.markdown("#### Distribusi Layanan")
                service_counts = filtered_df['SERVICE'].value_counts()
                st.bar_chart(service_counts)
                
                # Pie Chart untuk distribusi layanan
                fig = px.pie(
                    filtered_df, 
                    names='SERVICE', 
                    title='Distribusi Layanan (Pie Chart)',
                    hole=0.3,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Export filtered data button
            if not filtered_df.empty:
                st.markdown("### 💾 Ekspor Data")
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="Download Data Terfilter",
                    data=csv,
                    file_name='frequency_management_data.csv',
                    mime='text/csv',
                )
        
        with tab2:
            st.subheader("🗺️ Peta Lokasi Pengguna Frekuensi")
            
            # Opsi tampilan peta
            map_options_col1, map_options_col2 = st.columns(2)
            
            with map_options_col1:
                map_style = st.radio(
                    "Pilih Gaya Peta:",
                    ["OpenStreetMap", "Mapbox Streets", "Mapbox Satellite"],
                    horizontal=True
                )
                
                use_cluster = st.checkbox("Gunakan clustering untuk marker", value=True)
            
            with map_options_col2:
                show_heatmap = st.checkbox("Tampilkan heatmap", value=False)
                if 'FREQ_MHZ' in filtered_df.columns:
                    color_by = st.selectbox(
                        "Warna marker berdasarkan:",
                        ['SERVICE', 'FREQ_MHZ', 'SUBSERVICE']
                    )
                else:
                    color_by = st.selectbox(
                        "Warna marker berdasarkan:",
                        ['SERVICE', 'SUBSERVICE']
                    )
            
            # Map visualization using folium
            if not filtered_df.empty:
                # Memastikan koordinat tidak mengandung nilai NaN dan dikonversi ke numerik
                map_df = filtered_df.copy()
                map_df = map_df.dropna(subset=['SID_LONG', 'SID_LAT'])
                
                if not map_df.empty:
                    # Determine map center (default: Indonesia)
                    default_lat = -2.5489  # Center of Indonesia (approximate)
                    default_long = 118.0149  # Center of Indonesia (approximate)
                    
                    if len(map_df) > 0:
                        center_lat = map_df['SID_LAT'].mean()
                        center_long = map_df['SID_LONG'].mean()
                        
                        # Validate calculated center
                        if not (np.isnan(center_lat) or np.isnan(center_long)):
                            default_lat = center_lat
                            default_long = center_long
                    
                    # Create a folium map with appropriate tiles
                    if map_style == "OpenStreetMap":
                        m = folium.Map(location=[default_lat, default_long], 
                                        zoom_start=6, 
                                        tiles="OpenStreetMap")
                    elif map_style == "Mapbox Streets":
                        m = folium.Map(location=[default_lat, default_long], 
                                        zoom_start=6, 
                                        tiles='https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoiZXhhbXBsZXRva2VuIiwiYSI6ImNrbzB4b3d1YjAwcTAyb3FteHlxNDJkbGgifQ.1JXgEnfRuGAph4ZxGq9Sxg',
                                        attr='Mapbox')
                    elif map_style == "Mapbox Satellite":
                        m = folium.Map(location=[default_lat, default_long], 
                                        zoom_start=6, 
                                        tiles='https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoiZXhhbXBsZXRva2VuIiwiYSI6ImNrbzB4b3d1YjAwcTAyb3FteHlxNDJkbGgifQ.1JXgEnfRuGAph4ZxGq9Sxg',
                                        attr='Mapbox')
                    
                    # Add alternative tile layers
                    folium.TileLayer(
                        tiles="OpenStreetMap",
                        name="OpenStreetMap",
                    ).add_to(m)
                    
                    folium.TileLayer(
                        tiles='https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoiZXhhbXBsZXRva2VuIiwiYSI6ImNrbzB4b3d1YjAwcTAyb3FteHlxNDJkbGgifQ.1JXgEnfRuGAph4ZxGq9Sxg',
                        attr='Mapbox',
                        name='Mapbox Streets',
                    ).add_to(m)
                    
                    folium.TileLayer(
                        tiles='https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoiZXhhbXBsZXRva2VuIiwiYSI6ImNrbzB4b3d1YjAwcTAyb3FteHlxNDJkbGgifQ.1JXgEnfRuGAph4ZxGq9Sxg',
                        attr='Mapbox',
                        name='Mapbox Satellite',
                    ).add_to(m)
                    
                    # Add layer control to switch between base maps
                    folium.LayerControl().add_to(m)
                    
                    # Determine if we should use clustering
                    if use_cluster:
                        marker_cluster = MarkerCluster().add_to(m)
                    
                    # Add heatmap if requested
                    if show_heatmap and len(map_df) > 0:
                        heat_data = [[row['SID_LAT'], row['SID_LONG']] for _, row in map_df.iterrows()]
                        HeatMap(heat_data, radius=15).add_to(m)
                    
                    # Create color map based on selected column
                    color_column_values = map_df[color_by].unique()
                    color_map = {
                        value: '#%02x%02x%02x' % (
                            int(np.random.random() * 156) + 100,
                            int(np.random.random() * 156) + 100,
                            int(np.random.random() * 156) + 100
                        ) for value in color_column_values
                    }
                    
                    # Add markers for each point
                    for idx, row in map_df.iterrows():
                        # Build additional fields if they exist in the dataframe
                        additional_fields = ""
                        
                        # Check for frequency info
                        if 'FREQ_MHZ' in row and not pd.isna(row['FREQ_MHZ']):
                            additional_fields += f"""
                            <tr>
                                <td style="padding: 3px; font-weight: bold;">Frekuensi:</td>
                                <td style="padding: 3px;">{row['FREQ_MHZ']} MHz</td>
                            </tr>
                            """
                        
                        # Check for bandwidth info
                        if 'BW_MHZ' in row and not pd.isna(row['BW_MHZ']):
                            additional_fields += f"""
                            <tr>
                                <td style="padding: 3px; font-weight: bold;">Bandwidth:</td>
                                <td style="padding: 3px;">{row['BW_MHZ']} MHz</td>
                            </tr>
                            """
                            
                        # Create a popup with information
                        popup_text = f"""
                        <div style="font-family: Arial; min-width: 220px;">
                            <h4 style="margin-bottom: 10px;">{row['STN_NAME']}</h4>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 3px; font-weight: bold;">Klien:</td>
                                    <td style="padding: 3px;">{row['CLNT_NAME']}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 3px; font-weight: bold;">Layanan:</td>
                                    <td style="padding: 3px;">{row['SERVICE']}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 3px; font-weight: bold;">Sub-Layanan:</td>
                                    <td style="padding: 3px;">{row['SUBSERVICE']}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 3px; font-weight: bold;">Kota:</td>
                                    <td style="padding: 3px;">{row['CITY']}</td>
                                </tr>
                                {additional_fields}
                                <tr>
                                    <td style="padding: 3px; font-weight: bold;">Koordinat:</td>
                                    <td style="padding: 3px;">{row['SID_LAT']:.6f}, {row['SID_LONG']:.6f}</td>
                                </tr>
                            </table>
                        </div>
                        """
                        popup = folium.Popup(popup_text, max_width=300)
                        
                        # Get color based on selected column
                        color = color_map.get(row[color_by], 'blue') 
                        
                        # Get appropriate icon based on service
                        icon_name = get_service_icon(row['SERVICE'])
                        
                        # Determine target for the marker (cluster or map)
                        target = marker_cluster if use_cluster else m
                        
                        # Create and add custom icon marker
                        icon = folium.Icon(color=color, icon=icon_name, prefix='fa')
                        marker = folium.Marker(
                            location=[row['SID_LAT'], row['SID_LONG']],
                            popup=popup,
                            tooltip=f"{row['STN_NAME']} ({row['SERVICE']})",
                            icon=icon
                        )
                        marker.add_to(target)
                    
                    # Display the map
                    st.markdown("#### Lokasi Pengguna Frekuensi")
                    folium_static(m, width=1500, height=600)
                    
                    # Tampilkan legenda warna dan icon untuk layanan
                    st.markdown("#### Legenda Layanan")
                    
                    # Create legend based on selected color column
                    legend_html = "<div style='display: flex; flex-wrap: wrap; gap: 15px;'>"
                    
                    # Get unique values from the selected column
                    legend_items = map_df[color_by].unique().tolist()
                    
                    for item in sorted(legend_items):
                        color = color_map.get(item, 'blue')
                        # If color_by is SERVICE, use service icon; otherwise use circle
                        if color_by == 'SERVICE':
                            icon_name = get_service_icon(item)
                            legend_html += f"""
                            <div style="display: flex; align-items: center; border: 1px solid #ddd; border-radius: 5px; padding: 5px;">
                                <div style="width: 24px; height: 24px; background-color: {color}; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 10px;">
                                    <i class="fa fa-{icon_name}" style="color: white; font-size: 12px;"></i>
                                </div>
                                <div>{item}</div>
                            </div>
                            """
                        else:
                            legend_html += f"""
                            <div style="display: flex; align-items: center; border: 1px solid #ddd; border-radius: 5px; padding: 5px;">
                                <div style="width: 24px; height: 24px; background-color: {color}; border-radius: 50%; margin-right: 10px;"></div>
                                <div>{item}</div>
                            </div>
                            """
                    legend_html += "</div>"
                    
                    st.markdown(
                        f"""
                        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
                        {legend_html}
                        """, 
                        unsafe_allow_html=True
                    )
                    
                    # Tampilkan statistik koordinat
                    st.markdown("#### Statistik Koordinat")
                    stat_col1, stat_col2, stat_col3 = st.columns(3)
                    
                    with stat_col1:
                        st.metric("Jumlah Koordinat", len(map_df))
                    
                    with stat_col2:
                        st.metric("Kota dengan Koordinat Terbanyak", 
                                 map_df['CITY'].value_counts().index[0] if not map_df.empty else "N/A")
                    
                    with stat_col3:
                        st.metric("Layanan Terbanyak", 
                                 map_df['SERVICE'].value_counts().index[0] if not map_df.empty else "N/A")
                else:
                    st.warning("⚠️ Tidak ada data koordinat yang valid untuk ditampilkan pada peta.")
                    st.info("Pastikan data memiliki nilai latitude (SID_LAT) dan longitude (SID_LONG) yang valid.")
            else:
                st.warning("⚠️ Tidak ada data yang memenuhi filter untuk ditampilkan pada peta.")
        
        with tab3:
            st.subheader("📈 Visualisasi Data")
            
            # Check if there's data to visualize
            if not filtered_df.empty:
                # Create multiple visualizations in this tab
                viz_col1, viz_col2 = st.columns(2)
                
                with viz_col1:
                    st.markdown("### 🥧 Distribusi Layanan dan Sub-Layanan")
                    
                    # Pie chart for service distribution
                    service_counts = filtered_df['SERVICE'].value_counts()
                    fig_pie = px.pie(
                        values=service_counts.values,
                        names=service_counts.index,
                        title="Distribusi Layanan",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)
                    
                    # Pie chart for subservice distribution
                    subservice_counts = filtered_df['SUBSERVICE'].value_counts().head(10)  # Top 10 subservices
                    fig_sub_pie = px.pie(
                        values=subservice_counts.values,
                        names=subservice_counts.index,
                        title="Top 10 Sub-Layanan",
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig_sub_pie.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_sub_pie, use_container_width=True)
                
                with viz_col2:
                    st.markdown("### 📊 Distribusi Frekuensi per Kota")
                    
                    # Bar chart for city distribution
                    city_counts = filtered_df['CITY'].value_counts().head(10)  # Top 10 cities
                    fig_bar = px.bar(
                        x=city_counts.index,
                        y=city_counts.values,
                        title="Top 10 Kota dengan Pengguna Frekuensi Terbanyak",
                        labels={'x': 'Kota', 'y': 'Jumlah'},
                        color=city_counts.values,
                        color_continuous_scale='Viridis'
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                    
                    # Create a scatter plot of coordinates
                    if 'SID_LAT' in filtered_df.columns and 'SID_LONG' in filtered_df.columns:
                        # Convert to numeric and drop NaN values
                        scatter_df = filtered_df.copy()
                        scatter_df = scatter_df.dropna(subset=['SID_LAT', 'SID_LONG'])
                        
                        if not scatter_df.empty:
                            st.markdown("### 🌐 Scatter Plot Koordinat Lokasi")
                            
                            fig_scatter = px.scatter(
                                scatter_df,
                                x='SID_LONG',
                                y='SID_LAT',
                                color='SERVICE',
                                hover_name='STN_NAME',
                                hover_data=['CITY', 'CLNT_NAME', 'SUBSERVICE'],
                                title="Distribusi Lokasi Pengguna Frekuensi",
                                labels={'SID_LONG': 'Longitude', 'SID_LAT': 'Latitude', 'SERVICE': 'Layanan'},
                                color_discrete_sequence=px.colors.qualitative.Bold
                            )
                            fig_scatter.update_layout(
                                xaxis_title='Longitude',
                                yaxis_title='Latitude',
                            )
                            st.plotly_chart(fig_scatter, use_container_width=True)
                
                # Horizontal divider
                st.markdown("---")
                
                # Add heatmap of service by city
                st.markdown("### 🔥 Heatmap Layanan per Kota")
                
                # Create crosstab of CITY vs SERVICE
                service_by_city = pd.crosstab(filtered_df['CITY'], filtered_df['SERVICE'])
                
                # Limit to top 10 cities for better visualization
                top_cities = filtered_df['CITY'].value_counts().head(10).index.tolist()
                limited_crosstab = service_by_city.loc[service_by_city.index.isin(top_cities)]
                
                # Create heatmap
                fig_heatmap = px.imshow(
                    limited_crosstab,
                    labels=dict(x="Layanan", y="Kota", color="Jumlah"),
                    x=limited_crosstab.columns,
                    y=limited_crosstab.index,
                    color_continuous_scale="Viridis",
                    aspect="auto"
                )
                fig_heatmap.update_layout(
                    title="Heatmap Distribusi Layanan di Top 10 Kota",
                    xaxis_title="Layanan",
                    yaxis_title="Kota",
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
                
                # Visualisasi tambahan: Peta koordinat berwarna
                st.markdown("### 🌍 Peta Koordinat Berwarna")
                
                # Check if we have coordinate data
                coord_df = filtered_df.dropna(subset=['SID_LAT', 'SID_LONG'])
                
                if not coord_df.empty:
                    # Create a map figure using plotly
                    fig_map = px.scatter_mapbox(
                        coord_df,
                        lat='SID_LAT',
                        lon='SID_LONG',
                        color='SERVICE',
                        hover_name='STN_NAME',
                        hover_data=['CITY', 'CLNT_NAME', 'SUBSERVICE'],
                        zoom=4,
                        height=600,
                        title="Peta Distribusi Layanan Frekuensi",
                        color_discrete_sequence=px.colors.qualitative.Bold
                    )
                    
                    fig_map.update_layout(
                        mapbox_style="open-street-map",
                        margin={"r":0, "t":40, "l":0, "b":0}
                    )
                    
                    st.plotly_chart(fig_map, use_container_width=True)
                else:
                    st.warning("⚠️ Tidak ada data koordinat valid untuk divisualisasikan.")
                
                # Add time trend analysis (if applicable/date column exists)
                if 'DATE' in filtered_df.columns:
                    st.markdown("### 📅 Analisis Tren Waktu")
                    
                    # Convert to datetime
                    filtered_df['DATE'] = pd.to_datetime(filtered_df['DATE'], errors='coerce')
                    
                    # Group by date and count
                    time_trend = filtered_df.groupby(filtered_df['DATE'].dt.date).size().reset_index(name='count')
                    
                    # Plot time trend
                    fig_time = px.line(
                        time_trend,
                        x='DATE',
                        y='count',
                        title='Tren Jumlah Penambahan Data Frekuensi per Waktu',
                        labels={'DATE': 'Tanggal', 'count': 'Jumlah Data'}
                    )
                    st.plotly_chart(fig_time, use_container_width=True)
            else:
                st.warning("⚠️ Tidak ada data yang memenuhi filter untuk divisualisasikan.")
        
        with tab4:
            # Display filtered data in a table
            st.subheader("📋 Data Sistem Informasi Manajemen Frekuensi")
            
            # Opsi pencarian
            search_term = st.text_input("🔍 Cari data:", "")
            
            display_df = filtered_df
            
            # Apply search if provided
            if search_term:
                # Convert all columns to string for searching
                search_df = filtered_df.astype(str)
                # Create mask where any column contains the search term
            
            # Apply search if provided
                if search_term:
                    # Convert all columns to string for searching
                    search_df = filtered_df.astype(str)
                    # Create mask where any column contains the search term
                    mask = pd.DataFrame(False, index=search_df.index, columns=['match'])
                    for col in search_df.columns:
                        mask['match'] |= search_df[col].str.contains(search_term, case=False, na=False)
                    display_df = filtered_df[mask['match']]
                    
                    st.write(f"Ditemukan {len(display_df)} data yang mengandung '{search_term}'")
                
                # Tambahkan opsi untuk menampilkan jumlah baris tertentu
                num_rows = st.slider("Jumlah baris yang ditampilkan:", min_value=10, max_value=100, value=25, step=5)
                
                # Tambahkan opsi pengurutan data
                if not display_df.empty:
                    sort_columns = ['CITY', 'CLNT_NAME', 'STN_NAME', 'SERVICE', 'SUBSERVICE']
                    
                    # Tambahkan kolom frekuensi jika ada
                    if 'FREQ_MHZ' in display_df.columns:
                        sort_columns.append('FREQ_MHZ')
                    
                    sort_by = st.selectbox("Urutkan berdasarkan:", sort_columns)
                    sort_order = st.radio("Urutan:", ["Ascending", "Descending"], horizontal=True)
                    
                    # Terapkan pengurutan
                    ascending = True if sort_order == "Ascending" else False
                    display_df = display_df.sort_values(by=sort_by, ascending=ascending)
                
                # Display the filtered, searched, and sorted data
                st.dataframe(display_df.head(num_rows), use_container_width=True)
                
                # Tambahkan opsi untuk mengunduh data yang ditampilkan
                if not display_df.empty:
                    st.download_button(
                        label="Download Data Tabel",
                        data=display_df.to_csv(index=False),
                        file_name='data_frekuensi_tabel.csv',
                        mime='text/csv',
                    )
                
                # Tambahkan informasi tentang koordinat yang valid/tidak valid
                valid_coords = display_df.dropna(subset=['SID_LAT', 'SID_LONG'])
                if len(valid_coords) < len(display_df):
                    st.warning(f"⚠️ {len(display_df) - len(valid_coords)} dari {len(display_df)} baris tidak memiliki koordinat yang valid.")
                
    except Exception as e:
        st.error(f"❌ Error saat memproses file: {e}")
        st.write("Pastikan format file CSV valid dan memiliki kolom yang diperlukan.")
else:
    # Display instructions when no file is uploaded
    st.info("""
    ### 📌 Instruksi Penggunaan:
    1. Upload file CSV yang memiliki kolom: 
       - CITY (atau CIRY) - Kota lokasi frekuensi
       - CLNT_NAME - Nama klien/pengguna frekuensi
       - STN_NAME - Nama stasiun
       - SERVICE - Jenis layanan frekuensi
       - SUBSERVICE - Sub kategori layanan
       - SID_LONG - Koordinat longitude lokasi
       - SID_LAT - Koordinat latitude lokasi
       - FREQ_MHZ - Frekuensi dalam MHz (opsional)
       - BW_MHZ - Bandwidth dalam MHz (opsional)
    2. Gunakan filter untuk menyaring data
    3. Lihat visualisasi peta lokasi pengguna frekuensi
    4. Analisis data dengan berbagai grafik di tab visualisasi
    5. Ekspor data hasil filter untuk analisis lebih lanjut
    """)
    
    # Menampilkan contoh format data
    st.markdown("### 📝 Contoh Format Data CSV")
    example_data = {
        'CITY': ['Jakarta', 'Surabaya', 'Bandung', 'Medan', 'Makassar', 'Semarang'],
        'CLNT_NAME': ['PT Telkom', 'PT Media Networks', 'PT Broadcast Indonesia', 'PT Radio Sentosa', 'PT Telkom', 'PT Radio Indonesia'],
        'STN_NAME': ['Jakarta Tower', 'Surabaya Station', 'Bandung Relay', 'Medan Transmitter', 'Makassar Tower', 'Semarang Station'],
        'SERVICE': ['Broadcasting', 'Mobile', 'Cellular', 'Broadcasting', 'Satellite', 'Radio'],
        'SUBSERVICE': ['FM Radio', '4G LTE', '5G', 'TV', 'Internet', 'AM Radio'],
        'SID_LONG': [106.8456, 112.7520, 107.6191, 98.6722, 119.4144, 110.4203],
        'SID_LAT': [-6.2088, -7.2575, -6.9175, 3.5952, -5.1477, -6.9932],
        'FREQ_MHZ': [98.5, 1800.0, 2600.0, 205.0, 14000.0, 540.0],
        'BW_MHZ': [0.2, 20.0, 40.0, 0.1, 36.0, 0.01]
    }
    example_df = pd.DataFrame(example_data)
    st.dataframe(example_df, use_container_width=True)

    # Tambahkan panduan penggunaan peta
    st.markdown("### 🗺️ Panduan Penggunaan Peta")
    st.markdown("""
    #### Cara Menggunakan Peta:
    1. **Marker dan Icon**: Setiap titik pada peta mewakili lokasi pemancar/pengguna frekuensi dengan warna dan ikon yang berbeda berdasarkan jenis layanannya.
    2. **Popup Informasi**: Klik pada marker untuk melihat informasi detail tentang titik tersebut.
    3. **Clustering**: Aktifkan clustering untuk mengelompokkan marker yang berdekatan, berguna untuk data dalam jumlah besar.
    4. **Heatmap**: Aktifkan heatmap untuk melihat kepadatan penyebaran frekuensi dalam bentuk warna.
    5. **Jenis Peta**: Pilih jenis peta yang nyaman bagi Anda (OpenStreetMap, Mapbox Streets, atau Mapbox Satellite).
    
    #### Contoh Tampilan Peta Koordinat Frekuensi:
    """)
    
    # Tambahkan gambar contoh peta (bisa diganti dengan gambar yang lebih sesuai)
    st.image("https://i.imgur.com/LMPFZLK.png", caption="Contoh tampilan peta dengan marker koordinat frekuensi")

# Tambahkan komponen interaktif 3D
# Ditampilkan hanya jika file telah diupload dan memiliki koordinat yang valid
if 'df' in locals() and not df.empty:
    with st.expander("📊 Visualisasi 3D Koordinat Frekuensi"):
        st.markdown("### Visualisasi 3D Distribusi Koordinat Frekuensi")
        
        # Filter data untuk visualisasi 3D (hanya ambil data dengan koordinat valid)
        df_3d = df.dropna(subset=['SID_LAT', 'SID_LONG'])
        
        if not df_3d.empty and len(df_3d) >= 3:  # Pastikan ada cukup data untuk visualisasi 3D
            # Tambahkan kolom frekuensi jika tidak ada
            if 'FREQ_MHZ' not in df_3d.columns:
                df_3d['FREQ_MHZ'] = 100  # Nilai default
            
            # Normalisasi koordinat untuk visualisasi yang lebih baik
            x_min, x_max = df_3d['SID_LONG'].min(), df_3d['SID_LONG'].max()
            y_min, y_max = df_3d['SID_LAT'].min(), df_3d['SID_LAT'].max()
            
            # Buat visualisasi 3D dengan Plotly
            fig_3d = go.Figure(data=[go.Scatter3d(
                x=df_3d['SID_LONG'],
                y=df_3d['SID_LAT'],
                z=df_3d['FREQ_MHZ'],
                mode='markers',
                marker=dict(
                    size=5,
                    color=df_3d['FREQ_MHZ'],
                    colorscale='Viridis',
                    opacity=0.8,
                    colorbar=dict(title="Frekuensi (MHz)")
                ),
                text=df_3d['STN_NAME'],
                hoverinfo='text+x+y+z',
                hovertemplate='<b>%{text}</b><br>Long: %{x:.6f}<br>Lat: %{y:.6f}<br>Frekuensi: %{z} MHz',
            )])
            
            fig_3d.update_layout(
                title='Distribusi 3D Koordinat dan Frekuensi',
                scene=dict(
                    xaxis_title='Longitude',
                    yaxis_title='Latitude',
                    zaxis_title='Frekuensi (MHz)',
                    aspectmode='data'
                ),
                margin=dict(l=0, r=0, b=0, t=30),
                height=600
            )
            
            st.plotly_chart(fig_3d, use_container_width=True)
            
            st.markdown("""
            **Catatan**: 
            - Sumbu X menunjukkan Longitude (Bujur)
            - Sumbu Y menunjukkan Latitude (Lintang)
            - Sumbu Z menunjukkan Frekuensi dalam MHz
            - Warna titik menggambarkan nilai frekuensi
            """)
        else:
            st.warning("⚠️ Tidak cukup data dengan koordinat valid untuk visualisasi 3D.")

# Tambahkan pemeriksaan validitas koordinat
def validate_coordinates(df):
    """Memeriksa dan membersihkan data koordinat"""
    if 'SID_LAT' in df.columns and 'SID_LONG' in df.columns:
        # Konversi ke numerik
        df['SID_LAT'] = pd.to_numeric(df['SID_LAT'], errors='coerce')
        df['SID_LONG'] = pd.to_numeric(df['SID_LONG'], errors='coerce')
        
        # Validasi rentang koordinat
        invalid_lat = (df['SID_LAT'] < -90) | (df['SID_LAT'] > 90)
        invalid_long = (df['SID_LONG'] < -180) | (df['SID_LONG'] > 180)
        invalid_coords = invalid_lat | invalid_long
        
        if invalid_coords.any():
            st.warning(f"⚠️ {invalid_coords.sum()} baris memiliki koordinat yang tidak valid. Koordinat ini akan diabaikan pada tampilan peta.")
            
            # Set invalid values to NaN
            df.loc[invalid_coords, ['SID_LAT', 'SID_LONG']] = np.nan
    
    return df

# Footer
st.markdown("---")
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center;">
    <div>Sistem Informasi Manajemen Frekuensi © 2025</div>
    <div>Dikembangkan dengan ❤️ untuk pengelolaan spektrum frekuensi</div>
</div>
""", unsafe_allow_html=True)

# Tambahkan panduan penggunaan aplikasi dalam collapsed section
with st.expander("ℹ️ Panduan Lengkap Penggunaan Aplikasi"):
    st.markdown("""
    ## Panduan Penggunaan Aplikasi Sistem Informasi Manajemen Frekuensi
    
    ### 1. Upload Data
    - Format file harus CSV dengan pemisah koma
    - Pastikan file memiliki kolom wajib: CITY, CLNT_NAME, STN_NAME, SERVICE, SUBSERVICE, SID_LONG, SID_LAT
    - Kolom opsional: FREQ_MHZ (frekuensi dalam MHz), BW_MHZ (bandwidth dalam MHz)
    
    ### 2. Filter dan Analisis Data
    - Gunakan panel filter untuk menyaring data berdasarkan berbagai kriteria
    - Lihat ringkasan data dan statistik pada dashboard
    - Ekspor data hasil filter sebagai CSV untuk analisis lanjutan
    
    ### 3. Visualisasi Peta
    - Pilih jenis tampilan peta (OpenStreetMap, Mapbox Streets, Mapbox Satellite)
    - Aktifkan/nonaktifkan clustering untuk pengelompokan marker
    - Tampilkan heatmap untuk melihat kepadatan lokasi
    - Klik pada marker untuk melihat informasi detail
    
    ### 4. Visualisasi Grafik
    - Analisis distribusi layanan dengan pie chart dan bar chart
    - Lihat penyebaran koordinat dengan scatter plot
    - Analisis hubungan antar layanan dan kota dengan heatmap
    - Jelajahi visualisasi 3D untuk analisis spasial
    
    ### 5. Tabel Data
    - Pencarian data dengan kata kunci
    - Sorting/pengurutan data berdasarkan kolom tertentu
    - Pengaturan jumlah baris yang ditampilkan
    - Ekspor data tabel sebagai CSV
    
    ### Tips Penggunaan:
    - Pastikan koordinat (latitude/longitude) valid untuk tampilan peta yang akurat
    - Gunakan filter untuk fokus pada data yang relevan
    - Kombinasikan analisis peta dan grafik untuk pemahaman yang komprehensif
    - Ekspor data untuk analisis lebih lanjut dengan perangkat lunak lain
    """)