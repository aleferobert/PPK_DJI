"""
Módulo para processar arquivos .MRK e .POS e gerar CSV de resultados PPK.
Pode ser importado em outros scripts Python.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import glob
import os
from pyproj import Transformer
from PIL import Image

def gps_time_to_datetime(week, tow):
    """
    Converte semana GPS e tempo da semana (TOW) para datetime.
    """
    gps_epoch = datetime(1980, 1, 6)
    return gps_epoch + timedelta(weeks=week, seconds=float(tow))

def parse_mrk_gps_time(mrk_path, image_dir):
    """
    Lê o arquivo .MRK e associa cada registro à imagem correspondente,
    extraindo timestamp e ângulos de atitude.
    """
    timestamps = []
    filenames = []
    pitches = []
    rolls = []
    yaws = []

    all_images = sorted(glob.glob(os.path.join(image_dir, "*.JPG")))
    image_map = {f"DJI_{i+1:04d}": path.replace("\\", "/") for i, path in enumerate(all_images)}

    with open(mrk_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            try:
                idx = int(parts[0])
                tow = float(parts[1])
                week = int(parts[2].strip("[]"))
                dt = gps_time_to_datetime(week, tow)

                imu_str = parts[-2]
                imu_parts = imu_str.strip().split(",")
                yaw = float(imu_parts[0])
                pitch = float(imu_parts[1])
                roll = float(imu_parts[2])

                image_key = f"DJI_{idx:04d}"
                image_path = image_map.get(image_key)
                if image_path:
                    timestamps.append(dt)
                    filenames.append(image_path)
                    pitches.append(pitch)
                    rolls.append(roll)
                    yaws.append(yaw)
            except Exception:
                continue

    return pd.DataFrame({
        'filename': filenames,
        'timestamp': timestamps,
        'pitch': pitches,
        'roll': rolls,
        'yaw': yaws
    })

def parse_pos_standard(pos_path):
    """
    Lê o arquivo .POS padrão RTKLIB e retorna DataFrame com timestamp, lat, lon, altura.
    """
    pos_data = []
    with open(pos_path, 'r') as f:
        for line in f:
            if line.startswith('%') or line.strip() == "":
                continue
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            try:
                date_str = parts[0]
                time_str = parts[1]
                dt = datetime.strptime(f"{date_str} {time_str}", "%Y/%m/%d %H:%M:%S.%f")
                lat = float(parts[2])
                lon = float(parts[3])
                height = float(parts[4])
                pos_data.append((dt, lat, lon, height))
            except:
                continue

    df = pd.DataFrame(pos_data, columns=['timestamp', 'lat', 'lon', 'height'])
    return df.sort_values('timestamp')

def interpolate_positions_by_time(mrk_df, pos_df):
    """
    Interpola latitude, longitude e altura do .POS para os timestamps das imagens do .MRK.
    Converte ângulos de radianos para graus.
    """
    pos_df.set_index('timestamp', inplace=True)
    mrk_df = mrk_df.sort_values('timestamp')

    timestamps_int = mrk_df['timestamp'].astype(np.int64)
    pos_index_int = pos_df.index.astype(np.int64)

    def interp(field):
        return np.interp(timestamps_int, pos_index_int, pos_df[field])

    result = pd.DataFrame({
        'file_path': mrk_df['filename'],
        'latitude': interp('lat'),
        'longitude': interp('lon'),
        'height': interp('height'),
        'pitch': mrk_df['pitch'] * (180 / np.pi),  # rad → graus
        'roll': mrk_df['roll'] * (180 / np.pi),
        'yaw': mrk_df['yaw'] * (180 / np.pi)
    })

    return result

def process_ppk(mrk_path, pos_path, output_dir, output_format, proj4_str=None):
    """
    Função principal para processar MRK e POS e retornar DataFrame final.
    output_format: "csv" (DJI Terra) ou "webodm"
    proj4_str: string proj4 para projeção (ex: '+proj=utm +zone=20 ...')
    """
    image_dir = os.path.dirname(mrk_path)
    mrk_df = parse_mrk_gps_time(mrk_path, image_dir)
    pos_df = parse_pos_standard(pos_path)
    result_df = interpolate_positions_by_time(mrk_df, pos_df)

    if output_format == "dji_terra":
        output_file = os.path.join(output_dir, "POS_PPK.txt")
        result_df.to_csv(output_file, index=False)

    elif output_format == "webodm":
        # Projeta para UTM (ou outro sistema), se proj4_str fornecido
        if proj4_str is None:
            proj4_str = "+proj=utm +zone=20 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"

        
        transformer = Transformer.from_crs("epsg:4326", proj4_str, always_xy=True)
        xs, ys = transformer.transform(result_df['longitude'].values, result_df['latitude'].values)

        result_df = pd.DataFrame({
            'image_name': [os.path.basename(f) for f in result_df['file_path']],
            'geo_x': xs,
            'geo_y': ys,
            'geo_z': result_df['height']
        })
        
        output_file = os.path.join(output_dir, "geo.txt")
        
        with open(output_file, "w") as f:
            f.write(f"{proj4_str}\n")
            for _, row in result_df.iterrows():
                f.write(f"{row['image_name']}\t{row['geo_x']}\t{row['geo_y']}\t{row['geo_z']:.2f}\n")



        '''transformer = Transformer.from_crs("epsg:4326", proj4_str, always_xy=True)
        xs, ys = transformer.transform(result_df['longitude'].values, result_df['latitude'].values)
        im_xs = []
        im_ys = []
        for file_path in result_df['file_path']:
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
                    im_xs.append(width // 2)
                    im_ys.append(height // 2)
            except Exception:
                im_xs.append(0)
                im_ys.append(0)
        result_df = pd.DataFrame({
            'geo_x': xs,
            'geo_y': ys,
            'geo_z': result_df['height'],
            'im_x': im_xs,
            'im_y': im_ys,
            'image_name': [os.path.basename(f) for f in result_df['file_path']]
        })
        result_df.attrs['proj4'] = proj4_str

        output_file = os.path.join(output_dir, "geo.txt")
        with open(output_file, "w") as f:
            f.write(f"{proj4_str}\n")
            for _, row in result_df.iterrows():
                f.write(f"{row['geo_x']}\t{row['geo_y']}\t{row['geo_z']:.3f}\t{row['im_x']}\t{row['im_y']}\t{row['image_name']}\n")
        '''
    else:
        raise ValueError("Formato de saída não suportado.")
