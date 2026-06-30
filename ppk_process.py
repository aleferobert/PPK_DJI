"""
Módulo para processar arquivos .MRK e .POS e gerar CSV de resultados PPK.
Pode ser importado em outros scripts Python.
"""

import re
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from pyproj import Transformer

M3M_FILE_RE = re.compile(r"^(DJI_\d{14})_(\d{4})_", re.I)
P4M_JPG_RE = re.compile(r"^DJI_(\d{4})\.JPG$", re.I)
P4M_TIF_RE = re.compile(r"^DJI_(\d{4})\.TIF$", re.I)

M3M_SUFFIXES = ("_D.JPG", "_F.JPG", "_MS_G.TIF", "_MS_R.TIF", "_MS_RE.TIF", "_MS_NIR.TIF")
P4M_BAND_COUNT = 5


def gps_time_to_datetime(week, tow):
    """Converte semana GPS e tempo da semana (TOW) para datetime."""
    gps_epoch = datetime(1980, 1, 6)
    return gps_epoch + timedelta(weeks=week, seconds=float(tow))


def init_image_naming(image_dir):
    """
    Detecta o padrão de nomes e, no M3M, monta o mapa idx -> prefixo de data/hora.
    Uma única passagem em listdir, sem busca recursiva.
    """
    mode = "rgb"
    m3m_map = {}
    has_p4m_tif = False

    for fname in os.listdir(image_dir):
        m3m_match = M3M_FILE_RE.match(fname)
        if m3m_match:
            mode = "m3m"
            m3m_map[int(m3m_match.group(2))] = m3m_match.group(1)
            continue
        if P4M_TIF_RE.match(fname):
            has_p4m_tif = True

    if mode != "m3m" and has_p4m_tif:
        mode = "p4m"

    return mode, m3m_map


def resolve_capture_files(image_dir, idx, mode, m3m_map):
    """
    Monta os caminhos esperados para um disparo a partir do índice do MRK.
    Só verifica existência com os.path.isfile — sem glob nem busca recursiva.
    """
    paths = []

    if mode == "m3m":
        ts = m3m_map.get(idx)
        if not ts:
            return paths
        base = f"{ts}_{idx:04d}"
        for suffix in M3M_SUFFIXES:
            path = os.path.join(image_dir, f"{base}{suffix}")
            if os.path.isfile(path):
                paths.append(path.replace("\\", "/"))
        return paths

    if mode == "p4m":
        jpg = os.path.join(image_dir, f"DJI_{idx:04d}.JPG")
        if os.path.isfile(jpg):
            paths.append(jpg.replace("\\", "/"))
        for band in range(1, P4M_BAND_COUNT + 1):
            tif = os.path.join(image_dir, f"DJI_{idx + band:04d}.TIF")
            if os.path.isfile(tif):
                paths.append(tif.replace("\\", "/"))
        return paths

    jpg = os.path.join(image_dir, f"DJI_{idx:04d}.JPG")
    if os.path.isfile(jpg):
        paths.append(jpg.replace("\\", "/"))
    return paths


def parse_mrk_gps_time(mrk_path, image_dir):
    """
    Lê o .MRK e associa cada disparo às imagens do grupo (RGB + bandas).
    Para multiespectral, replica timestamp e atitude em cada arquivo do disparo.
    """
    mode, m3m_map = init_image_naming(image_dir)

    timestamps = []
    filenames = []
    pitches = []
    rolls = []
    yaws = []

    with open(mrk_path, "r", encoding="utf-8", errors="replace") as f:
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

                capture_files = resolve_capture_files(image_dir, idx, mode, m3m_map)
                for image_path in capture_files:
                    timestamps.append(dt)
                    filenames.append(image_path)
                    pitches.append(pitch)
                    rolls.append(roll)
                    yaws.append(yaw)
            except Exception:
                continue

    return pd.DataFrame({
        "filename": filenames,
        "timestamp": timestamps,
        "pitch": pitches,
        "roll": rolls,
        "yaw": yaws,
    })


def parse_pos_standard(pos_path):
    """
    Lê o arquivo .POS padrão RTKLIB e retorna DataFrame com timestamp, lat, lon, altura.
    """
    pos_data = []
    with open(pos_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("%") or line.strip() == "":
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
            except Exception:
                continue

    df = pd.DataFrame(pos_data, columns=["timestamp", "lat", "lon", "height"])
    return df.sort_values("timestamp")


def interpolate_positions_by_time(mrk_df, pos_df):
    """
    Interpola latitude, longitude e altura do .POS para os timestamps das imagens do .MRK.
    Converte ângulos de radianos para graus.
    """
    pos_df = pos_df.copy()
    pos_df.set_index("timestamp", inplace=True)
    mrk_df = mrk_df.sort_values("timestamp")

    timestamps_int = mrk_df["timestamp"].astype(np.int64)
    pos_index_int = pos_df.index.astype(np.int64)

    def interp(field):
        return np.interp(timestamps_int, pos_index_int, pos_df[field])

    return pd.DataFrame({
        "file_path": mrk_df["filename"],
        "latitude": interp("lat"),
        "longitude": interp("lon"),
        "height": interp("height"),
        "pitch": mrk_df["pitch"] * (180 / np.pi),
        "roll": mrk_df["roll"] * (180 / np.pi),
        "yaw": mrk_df["yaw"] * (180 / np.pi),
    })


def process_ppk(mrk_path, pos_path, output_dir, output_format, proj4_str=None):
    """
    Função principal para processar MRK e POS e gerar arquivo de saída.
    output_format: "dji_terra", "webodm" ou "pixel4d"
    """
    image_dir = os.path.dirname(mrk_path)
    mrk_df = parse_mrk_gps_time(mrk_path, image_dir)
    if mrk_df.empty:
        raise ValueError("Nenhuma imagem encontrada para os índices do arquivo .MRK.")

    pos_df = parse_pos_standard(pos_path)
    result_df = interpolate_positions_by_time(mrk_df, pos_df)

    if output_format == "dji_terra":
        output_file = os.path.join(output_dir, "POS_PPK.txt")
        result_df.to_csv(output_file, index=False)

    elif output_format == "pixel4d":
        output_file = os.path.join(output_dir, "geolocation.csv")
        pixel4d_df = pd.DataFrame({
            "Image name": [os.path.basename(path) for path in result_df["file_path"]],
            "latitude": result_df["latitude"],
            "longitude": result_df["longitude"],
            "altitude": result_df["height"],
        })
        pixel4d_df.to_csv(output_file, index=False)

    elif output_format == "webodm":
        if proj4_str is None:
            proj4_str = "+proj=utm +zone=20 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"

        transformer = Transformer.from_crs("epsg:4326", proj4_str, always_xy=True)
        xs, ys = transformer.transform(result_df["longitude"].values, result_df["latitude"].values)

        output_file = os.path.join(output_dir, "geo.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"{proj4_str}\n")
            names = [os.path.basename(path) for path in result_df["file_path"]]
            for name, x, y, z in zip(names, xs, ys, result_df["height"]):
                f.write(f"{name}\t{x}\t{y}\t{z:.2f}\n")

    else:
        raise ValueError("Formato de saída não suportado.")
