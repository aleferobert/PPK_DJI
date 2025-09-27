import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from pyproj import Transformer
import re
import os
import subprocess

def decimal_to_dms(coord, is_lat=True):
    sinal = -1 if coord < 0 else 1
    #direction = 'N' if is_lat and coord >= 0 else 'S' if is_lat else 'E' if coord >= 0 else 'W'              
    coord = abs(coord)
    degrees = int(coord) * sinal
    minutes = int((coord - int(coord)) * 60)
    seconds = (coord - int(coord) - minutes / 60) * 3600
    return degrees, minutes, seconds
    #return f"{degrees}°{minutes}'{seconds:.1f}\"{direction}"

# Função para converter GMS para graus decimais
def dms_to_decimal(gms_str):
    # Aceita formatos tipo -23°34'45.6", +23 34 45.6, ou -60 20 60
    gms_str = gms_str.strip().replace(',', '.')
    # Tenta separar por espaço
    parts = gms_str.split()
    if len(parts) == 3:
        graus, minutos, segundos = parts
        graus = float(graus)
        minutos = float(minutos)
        segundos = float(segundos)
        decimal = abs(graus) + minutos/60 + segundos/3600
        if graus < 0:
            decimal *= -1
        return decimal
    # Tenta regex para formatos com ° ' "
    match = re.match(r"([+-]?\d+)[°\s](\d+)[']?(\d+(?:\.\d+)?)[\"\s]?", gms_str)
    if match:
        graus, minutos, segundos = match.groups()
        decimal = abs(float(graus)) + float(minutos)/60 + float(segundos)/3600
        if float(graus) < 0:
            decimal *= -1
        return decimal
    raise ValueError("Formato GMS inválido. Use: grau minuto segundo, ex: -60 20 60")

# Função para ler informações do arquivo .OBS e extrair coordenadas e período
# Utiliza pyproj para converter coordenadas de ECEF para geodésicas (lat, lon, alt)
def parse_obs_info(file_path):
    lat, lon, alt, t0, t1 = None, None, None, None, None
    with open(file_path, 'r', encoding='latin1') as f:
        for line in f:
            if 'APPROX POSITION XYZ' in line:
                parts = list(map(float, line.strip().split()[0:3]))
                transformer = Transformer.from_crs("epsg:4978", "epsg:4326", always_xy=True)
                lon, lat, alt = transformer.transform(*parts)
            elif 'TIME OF FIRST OBS' in line:
                parts = line.strip().split()
                date_str = f"{parts[0]}-{parts[1]}-{parts[2]} {parts[3]}:{parts[4]}:{float(parts[5]):02.0f}"
                t0 = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            elif 'TIME OF LAST OBS' in line:
                parts = line.strip().split()
                date_str = f"{parts[0]}-{parts[1]}-{parts[2]} {parts[3]}:{parts[4]}:{float(parts[5]):02.0f}"
                t1 = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            if lat is not None and lon is not None and alt is not None and t0 and t1:
                break
    return lat, lon, alt, t0, t1

# Função para selecionar arquivo e preencher informações
def selecionar_arquivo(entry, label_info, tipo):
    
    filetypes = []
    if tipo == ".MRK":
        filetypes = [("Arquivo MRK", "*.MRK"),("Todos os arquivos", "*.*")]
    elif tipo == ".OBS - ROVER":
        filetypes = [("Arquivo OBS", "*.OBS;*.??O;*.??D"),("Todos os arquivos", "*.*")]
    elif tipo == ".OBS - BASE":
        filetypes = [("Arquivo OBS", "*.OBS;*.??O;*.??D"),("Todos os arquivos", "*.*")]
    elif tipo == ".NAV":
        filetypes = [("Arquivo NAV", "*.NAV;*.??N"),("Todos os arquivos", "*.*")]

    caminho = filedialog.askopenfilename(title=f"Selecionar arquivo {tipo}", filetypes=filetypes)
    if caminho:
        entry.delete(0, tk.END)
        entry.insert(0, caminho)
        if tipo in ['.OBS - ROVER', '.OBS - BASE']:
            try:
                #VERIFICA SE É HATANAKA E CONVERTE PARA RINEX
                if caminho.lower()[-4:].startswith('.') and caminho.lower().endswith('d'):
                    tempfile = os.path.splitext(caminho)[0] + os.path.splitext(caminho)[1].replace("d", "o")
                    comando = f'"{os.path.normpath(crx2rnx_path)}" -f "{os.path.normpath(caminho)}"'
                    try:
                        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
                        if resultado.returncode == 0:
                            caminho = tempfile
                            entry.delete(0, tk.END)
                            entry.insert(0, caminho)
                    except Exception as e:
                        messagebox.showerror("Erro", f"Erro ao converter CRX para RINEX:\n{e}")
                        return

                lat, lon, alt, t0, t1 = parse_obs_info(caminho)
                lat_dms =   "{}°{}'{:.1f}".format(*decimal_to_dms(lat, is_lat=True)) 
                lon_dms = "{}°{}'{:.1f}".format(*decimal_to_dms(lon, is_lat=False))  
                #lat_dms = decimal_to_dms(lat, is_lat=True)
                #lon_dms = decimal_to_dms(lon, is_lat=False)
                label_info.config(
                    text=f"↳ Coordenadas {tipo.split()[-1].lower()}: {lat_dms}, {lon_dms}\n↳ Período: {t0} → {t1}"
                )
                # Preencher campos GMS se for .OBS - BASE
                if tipo == '.OBS - BASE' and lat is not None and lon is not None:
                    # Converter decimal para GMS separado
                    lat_g, lat_m, lat_s = decimal_to_dms(lat, is_lat=True)
                    lon_g, lon_m, lon_s = decimal_to_dms(lon, is_lat=False)
                    entry_lat_gms.delete(0, tk.END)
                    entry_lat_gms.insert(0, f"{lat_g} {lat_m} {lat_s:.8f}")
                    entry_lon_gms.delete(0, tk.END)
                    entry_lon_gms.insert(0, f"{lon_g} {lon_m} {lon_s:.8f}")
                    # Altitude elipsoidal convertida
                    if alt is not None:
                        entry_alt_gms.delete(0, tk.END)
                        entry_alt_gms.insert(0, f"{alt:.2f}")
            except Exception as e:
                label_info.config(text=f"Erro ao ler {tipo}: {e}")


# Caminho do executável e config.conf (ajuste conforme seu ambiente)
# Caminho absoluto para o executável na mesma pasta do script
script_dir = os.path.dirname(os.path.abspath(__file__))
rnx2rtkp_path = os.path.join(script_dir, "rnx2rtkp.exe")
crx2rnx_path = os.path.join(script_dir, "crx2rnx.exe")
config_path = os.path.join(os.path.dirname(rnx2rtkp_path), "config.conf")

root = tk.Tk()
root.title("PPK-DRONE - Processamento PPK")

tk.Label(root, text="Selecionar .MRK").grid(row=0, column=0, sticky='w')
entry_mrk = tk.Entry(root, width=60)
entry_mrk.grid(row=0, column=1)
tk.Button(root, text="...", command=lambda: selecionar_arquivo(entry_mrk, tk.Label(), ".MRK")).grid(row=0, column=2)

tk.Label(root, text="Selecionar .OBS - ROVER").grid(row=1, column=0, sticky='w')
entry_obs_rover = tk.Entry(root, width=60)
entry_obs_rover.grid(row=1, column=1)
label_rover_info = tk.Label(root, text="", justify='left')
label_rover_info.grid(row=2, column=1, sticky='w')
tk.Button(root, text="...", command=lambda: selecionar_arquivo(entry_obs_rover, label_rover_info, ".OBS - ROVER")).grid(row=1, column=2)

tk.Label(root, text="Selecionar .OBS - BASE").grid(row=3, column=0, sticky='w')
entry_obs_base = tk.Entry(root, width=60)
entry_obs_base.grid(row=3, column=1)
label_base_info = tk.Label(root, text="", justify='left')
label_base_info.grid(row=4, column=1, sticky='w')
tk.Button(root, text="...", command=lambda: selecionar_arquivo(entry_obs_base, label_base_info, ".OBS - BASE")).grid(row=3, column=2)

tk.Label(root, text="Selecionar .NAV").grid(row=5, column=0, sticky='w')
entry_nav = tk.Entry(root, width=60)
entry_nav.grid(row=5, column=1)
tk.Button(root, text="...", command=lambda: selecionar_arquivo(entry_nav, tk.Label(), ".NAV")).grid(row=5, column=2)

# Campos opcionais para coordenada da base em GMS
frame_gms = tk.Frame(root)
frame_gms.grid(row=6, column=1, sticky='w', pady=(10,0))
tk.Label(frame_gms, text="Coordenada da base (opcional, GMS):").grid(row=0, column=0, columnspan=6, sticky='w')


# Latitude
entry_lat_gms = tk.Entry(frame_gms, width=10)
tk.Label(frame_gms, text="Lat GMS:").grid(row=1, column=0)
entry_lat_gms.grid(row=1, column=1)
# Longitude
entry_lon_gms = tk.Entry(frame_gms, width=10)
tk.Label(frame_gms, text="Lon GMS:").grid(row=1, column=2)
entry_lon_gms.grid(row=1, column=3)
# Altitude
entry_alt_gms = tk.Entry(frame_gms, width=10)
tk.Label(frame_gms, text="Alt (m):").grid(row=1, column=4)
entry_alt_gms.grid(row=1, column=5)

# Adicione logo após a criação do root:
saida_var = tk.StringVar(value="dji_terra")

frame_saida = tk.Frame(root)
frame_saida.grid(row=8, column=1, sticky='w')
tk.Label(frame_saida, text="Formato de saída:").grid(row=0, column=0, sticky='w')
tk.Radiobutton(frame_saida, text="DJI Terra (CSV)", variable=saida_var, value="dji_terra").grid(row=0, column=1)
tk.Radiobutton(frame_saida, text="WebODM (TXT)", variable=saida_var, value="webodm").grid(row=0, column=2)

# Importa o módulo de processamento PPK
import sys
sys.path.append(os.path.dirname(__file__))  # Garante que o módulo local seja encontrado
import ppk_process  # Importa as funções do módulo criado

def executar_script():
    if not all([entry_mrk.get(), entry_obs_rover.get(), entry_obs_base.get(), entry_nav.get()]):
        messagebox.showwarning("Atenção", "Todos os arquivos precisam ser preenchidos.")
        return
    # Se o campo GMS estiver preenchido, converte para decimal
    lat_gms = entry_lat_gms.get().strip()
    lon_gms = entry_lon_gms.get().strip()
    alt_gms = entry_alt_gms.get().strip()
    l_arg = ""
    if lat_gms and lon_gms:
        try:
            lat_dec = dms_to_decimal(lat_gms)
            lon_dec = dms_to_decimal(lon_gms)
            alt_dec = float(alt_gms) if alt_gms else 0.0
            l_arg = f" -l {lat_dec:.8f} {lon_dec:.8f} {alt_dec:.3f}"
            print(f"Coordenada base em decimal: lat={lat_dec}, lon={lon_dec}, alt={alt_dec}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao converter coordenada GMS: {e}")
            return
    # Monta comando RNX2RTKP com caminhos normalizados
    rover_obs = os.path.normpath(entry_obs_rover.get())
    base_obs = os.path.normpath(entry_obs_base.get())
    base_nav = os.path.normpath(entry_nav.get())
    saida_pos = os.path.normpath(os.path.join(os.path.dirname(entry_mrk.get()), "POS_PPK.pos"))
    comando = f'"{os.path.normpath(rnx2rtkp_path)}" -k "{os.path.normpath(config_path)}" "{rover_obs}" "{base_obs}" "{base_nav}" -o "{saida_pos}"{l_arg}'
    print(comando)
    try:
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
        if resultado.returncode == 0:
            

            try:
                mrk_path = entry_mrk.get()                
                output_dir = os.path.dirname(mrk_path)
                
                ppk_process.process_ppk(mrk_path, saida_pos, proj4_str=None, output_dir = output_dir, output_format=saida_var.get())
                
                # Salva os resultados no formato escolhido
                #ppk_process.save_results(result_df, output_dir, output_format=saida_var.get())

                messagebox.showinfo("Execução", f"Processamento concluído! Arquivo gerado: {saida_pos}")

            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao gerar arquivo de saída: {e}")

        else:
            messagebox.showerror("Erro", f"Erro ao executar RNX2RTKP:\n{resultado.stderr}")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao executar RNX2RTKP: {e}")

tk.Button(root, text="Executar script", command=executar_script, bg="lightgreen").grid(row=7, column=1, pady=10)

root.mainloop()
