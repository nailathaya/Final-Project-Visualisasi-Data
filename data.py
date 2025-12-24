import os
import pandas as pd
import geopandas as gpd
import shutil

def buat_struktur_dan_konversi(path_sumber, path_output):
    # 1. Definisi Struktur Folder Target
    root_name = "Data Visualisation Competition 2025"
    base_path = os.path.join(path_output, root_name)
    
    structure = [
        "data/level_1",
        "data/level_2",
        "data/level_3",
        "lookups",
        "shapefile"
    ]

    for folder in structure:
        os.makedirs(os.path.join(base_path, folder), exist_ok=True)

    print("--- Memulai Proses Konversi ---")

    # Helper function untuk konversi ke Parquet
    def to_parquet(src_file, dest_folder):
        filename = os.path.basename(src_file)
        name_only = os.path.splitext(filename)[0]
        target_path = os.path.join(base_path, dest_folder, f"{name_only}.parquet")
        
        if filename.endswith('.csv'):
            df = pd.read_csv(src_file)
            df.to_parquet(target_path)
            print(f"[OK] CSV -> Parquet: {filename}")
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(src_file)
            df.to_parquet(target_path)
            print(f"[OK] Excel -> Parquet: {filename}")

    # Helper function untuk GeoParquet (Shapefile)
    def shp_to_geoparquet(src_shp, dest_folder):
        filename = os.path.basename(src_shp)
        name_only = os.path.splitext(filename)[0]
        target_path = os.path.join(base_path, dest_folder, f"{name_only}.parquet")
        
        gdf = gpd.read_file(src_shp)
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)
        gdf['geometry'] = gdf['geometry'].simplify(0.001)
        gdf.to_parquet(target_path)
        print(f"[OK] SHP -> GeoParquet: {filename}")

    to_parquet(f"{path_sumber}/data/level_1/Level_1.xlsx", "data/level_1")
    to_parquet(f"{path_sumber}/data/level_3/level3_road_cong.csv", "data/level_3")
    to_parquet(f"{path_sumber}/lookups/lookups.xlsx", "lookups")
    shp_to_geoparquet(f"{path_sumber}/shapefile/small_areas_british_grid.shp", "shapefile")
    shutil.copy(f"{path_sumber}/README.txt", base_path)

    print("\n--- Membuat file ZIP ---")
    zip_file_path = shutil.make_archive(base_path, 'zip', base_path)
    print(f"Selesai! File ZIP tersimpan di: {zip_file_path}")

folder_asal = "/Users/HilalAbyan/Final-Project-Visualisasi-Data/Data Visualisation Competition 2025" 
folder_hasil = "output_final" 

buat_struktur_dan_konversi(folder_asal, folder_hasil)