import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
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

def converter_hatanaka_se_necessario(caminho):
    if caminho.lower()[-4:].startswith('.') and caminho.lower().endswith('d'):
        tempfile = os.path.splitext(caminho)[0] + os.path.splitext(caminho)[1].replace("d", "o")
        comando = f'"{os.path.normpath(crx2rnx_path)}" -f "{os.path.normpath(caminho)}"'
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
        if resultado.returncode != 0:
            raise RuntimeError(f"Erro ao converter CRX para RINEX:\n{resultado.stderr}")
        return tempfile
    return caminho


# Caminho do executável e config.conf (ajuste conforme seu ambiente)
# Caminho absoluto para o executável na mesma pasta do script
script_dir = os.path.dirname(os.path.abspath(__file__))
rnx2rtkp_path = os.path.join(script_dir, "rnx2rtkp.exe")
crx2rnx_path = os.path.join(script_dir, "crx2rnx.exe")
config_path = os.path.join(os.path.dirname(rnx2rtkp_path), "config.conf")

import sys
sys.path.append(script_dir)
import ppk_process
from reference_points import ReferencePointStore
from obs_coverage import parse_obs_info, parse_obs_span, plan_coverage
from ppk_runner import process_rover_with_bases
from mission_utils import discover_rover_for_mrk, discover_base_obs

ref_store = ReferencePointStore(os.path.join(script_dir, "ppk_drone.db"))
missions_data = []
bases_data = []

root = tk.Tk()
root.title("PPK-DRONE - Processamento PPK")
ref_var = tk.StringVar()

frame_missions = tk.LabelFrame(
    root, text="Rovers — adicione .MRK (o OBS é detectado na mesma pasta)", padx=5, pady=5
)
frame_missions.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=(6, 0))

cols = ("pasta", "mrk", "rover", "status")
tree_missions = ttk.Treeview(frame_missions, columns=cols, show="headings", height=4)
tree_missions.heading("pasta", text="Pasta")
tree_missions.heading("mrk", text="MRK")
tree_missions.heading("rover", text="Rover OBS")
tree_missions.heading("status", text="Status")
tree_missions.column("pasta", width=180)
tree_missions.column("mrk", width=140)
tree_missions.column("rover", width=140)
tree_missions.column("status", width=80)
tree_missions.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 4))

scroll_missions = ttk.Scrollbar(frame_missions, orient="vertical", command=tree_missions.yview)
tree_missions.configure(yscrollcommand=scroll_missions.set)
scroll_missions.grid(row=0, column=4, sticky="ns")

tk.Label(frame_missions, text="Saída consolidada:").grid(row=1, column=0, sticky="w")
entry_saida_consolidada = tk.Entry(frame_missions, width=58)
entry_saida_consolidada.grid(row=1, column=1, columnspan=2, sticky="w", padx=4)
tk.Button(
    frame_missions, text="...",
    command=lambda: _escolher_pasta_saida(),
).grid(row=1, column=3, sticky="w")

frame_bases = tk.LabelFrame(
    root, text="Bases — adicione OBS (NAV detectado na mesma pasta)", padx=5, pady=5
)
frame_bases.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=(6, 0))

cols_base = ("pasta", "obs", "nav")
tree_bases = ttk.Treeview(frame_bases, columns=cols_base, show="headings", height=3)
tree_bases.heading("pasta", text="Pasta")
tree_bases.heading("obs", text="Base OBS")
tree_bases.heading("nav", text="NAV")
tree_bases.column("pasta", width=160)
tree_bases.column("obs", width=200)
tree_bases.column("nav", width=200)
tree_bases.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 4))

scroll_bases = ttk.Scrollbar(frame_bases, orient="vertical", command=tree_bases.yview)
tree_bases.configure(yscrollcommand=scroll_bases.set)
scroll_bases.grid(row=0, column=4, sticky="ns")

label_cobertura = tk.Label(root, text="", justify="left", fg="darkorange")
label_cobertura.grid(row=2, column=1, sticky="w")

frame_gms = tk.Frame(root)
frame_gms.grid(row=3, column=1, sticky='w', pady=(10, 0))
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

saida_var = tk.StringVar(value="dji_terra")

frame_saida = tk.Frame(root)
frame_saida.grid(row=6, column=1, sticky='w')
tk.Label(frame_saida, text="Formato de saída:").grid(row=0, column=0, sticky='w')
tk.Radiobutton(frame_saida, text="DJI Terra (CSV)", variable=saida_var, value="dji_terra").grid(row=0, column=1)
tk.Radiobutton(frame_saida, text="WebODM (TXT)", variable=saida_var, value="webodm").grid(row=0, column=2)
tk.Radiobutton(frame_saida, text="Pixel4D (CSV)", variable=saida_var, value="pixel4d").grid(row=0, column=3)


def atualizar_lista_pontos():
    names = ref_store.list_names()
    combo_ref["values"] = names
    if names and ref_var.get() not in names:
        ref_var.set(names[0])
    elif not names:
        ref_var.set("")


def preencher_gms_da_base(obs_path):
    try:
        lat, lon, alt, _t0, _t1 = parse_obs_info(obs_path)
        if lat is None or lon is None:
            return
        lat_g, lat_m, lat_s = decimal_to_dms(lat, is_lat=True)
        lon_g, lon_m, lon_s = decimal_to_dms(lon, is_lat=False)
        entry_lat_gms.delete(0, tk.END)
        entry_lat_gms.insert(0, f"{lat_g} {lat_m} {lat_s:.8f}")
        entry_lon_gms.delete(0, tk.END)
        entry_lon_gms.insert(0, f"{lon_g} {lon_m} {lon_s:.8f}")
        if alt is not None:
            entry_alt_gms.delete(0, tk.END)
            entry_alt_gms.insert(0, f"{alt:.2f}")
    except Exception:
        pass


def carregar_ponto_base():
    name = ref_var.get().strip()
    if not name:
        messagebox.showwarning("Atenção", "Selecione um ponto de base.")
        return

    point = ref_store.get(name)
    if not point:
        messagebox.showerror("Erro", "Ponto não encontrado.")
        atualizar_lista_pontos()
        return

    entry_lat_gms.delete(0, tk.END)
    entry_lat_gms.insert(0, point["lat_gms"])
    entry_lon_gms.delete(0, tk.END)
    entry_lon_gms.insert(0, point["lon_gms"])
    entry_alt_gms.delete(0, tk.END)
    entry_alt_gms.insert(0, f"{point['alt']:.2f}")

    obs_path = point["obs_path"]
    if obs_path and os.path.isfile(obs_path):
        try:
            bases_data.clear()
            registrar_base_obs(obs_path, avisar=False)
        except Exception:
            preencher_gms_da_base(obs_path)
    else:
        preencher_gms_da_base(obs_path) if obs_path else None


def salvar_ponto_base():
    lat_gms = entry_lat_gms.get().strip()
    lon_gms = entry_lon_gms.get().strip()
    alt_gms = entry_alt_gms.get().strip()

    if not lat_gms or not lon_gms:
        messagebox.showwarning(
            "Atenção",
            "Preencha latitude e longitude GMS antes de salvar o ponto.",
        )
        return

    try:
        dms_to_decimal(lat_gms)
        dms_to_decimal(lon_gms)
        alt = float(alt_gms) if alt_gms else 0.0
    except Exception as e:
        messagebox.showerror("Erro", f"Coordenadas inválidas:\n{e}")
        return

    name = simpledialog.askstring(
        "Salvar ponto de base",
        "Nome do ponto:",
        parent=root,
    )
    if not name or not name.strip():
        return
    name = name.strip()

    if ref_store.get(name):
        if not messagebox.askyesno(
            "Substituir ponto",
            f"O ponto '{name}' já existe. Deseja substituir?",
        ):
            return

    obs_path = bases_data[0]["obs"] if bases_data else ""
    ref_store.save(name, lat_gms, lon_gms, alt, obs_path)
    ref_var.set(name)
    atualizar_lista_pontos()
    messagebox.showinfo("Salvo", f"Ponto '{name}' salvo com sucesso.")


def excluir_ponto_base():
    name = ref_var.get().strip()
    if not name:
        messagebox.showwarning("Atenção", "Selecione um ponto para excluir.")
        return
    if not messagebox.askyesno("Confirmar exclusão", f"Excluir o ponto '{name}'?"):
        return
    if ref_store.delete(name):
        ref_var.set("")
        atualizar_lista_pontos()
        messagebox.showinfo("Excluído", f"Ponto '{name}' removido.")
    else:
        messagebox.showerror("Erro", "Não foi possível excluir o ponto.")


frame_ref = tk.LabelFrame(root, text="Pontos de base salvos", padx=5, pady=5)
frame_ref.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=(8, 0))

tk.Label(frame_ref, text="Ponto:").grid(row=0, column=0, sticky="w")
combo_ref = ttk.Combobox(frame_ref, textvariable=ref_var, width=42, state="readonly")
combo_ref.grid(row=0, column=1, padx=5, sticky="w")
combo_ref.bind("<<ComboboxSelected>>", lambda _e: carregar_ponto_base())
tk.Button(frame_ref, text="Carregar", command=carregar_ponto_base, width=10).grid(row=0, column=2, padx=2)
tk.Button(frame_ref, text="Salvar atual", command=salvar_ponto_base, width=10).grid(row=0, column=3, padx=2)
tk.Button(frame_ref, text="Excluir", command=excluir_ponto_base, width=10).grid(row=0, column=4, padx=2)


def obter_caminhos_base():
    return [base["obs"] for base in bases_data]


def obter_nav():
    if not bases_data:
        return ""
    return bases_data[0]["nav"]


def atualizar_tree_bases():
    for item in tree_bases.get_children():
        tree_bases.delete(item)
    for base in bases_data:
        tree_bases.insert(
            "",
            tk.END,
            iid=base["obs"],
            values=(
                os.path.basename(base["folder"]),
                os.path.basename(base["obs"]),
                os.path.basename(base["nav"]),
            ),
        )


def _base_ja_existe(obs_path):
    obs_norm = os.path.normpath(obs_path)
    return any(b["obs"] == obs_norm for b in bases_data)


def registrar_base_obs(obs_path, avisar=True):
    if _base_ja_existe(obs_path):
        raise ValueError(f"Base já na lista:\n{os.path.basename(obs_path)}")

    obs_path = converter_hatanaka_se_necessario(obs_path)
    info = discover_base_obs(obs_path)
    parse_obs_span(info["obs"])

    if bases_data and bases_data[0]["nav"] != info["nav"]:
        if avisar:
            messagebox.showwarning(
                "NAV diferente",
                f"O NAV desta base ({os.path.basename(info['nav'])}) difere do "
                f"primeiro ({os.path.basename(bases_data[0]['nav'])}).\n"
                "Será usado o NAV da primeira base no processamento.",
            )

    bases_data.append(info)
    if len(bases_data) == 1:
        preencher_gms_da_base(info["obs"])
    atualizar_tree_bases()
    atualizar_status_cobertura()
    return info


def adicionar_base_obs():
    paths = filedialog.askopenfilenames(
        title="Selecionar arquivo(s) OBS de base",
        filetypes=[("Arquivo OBS", "*.OBS;*.??O;*.??D"), ("Todos os arquivos", "*.*")],
    )
    if not paths:
        return

    adicionados = 0
    problemas = []
    for path in paths:
        try:
            registrar_base_obs(path, avisar=False)
            adicionados += 1
        except Exception as e:
            problemas.append(f"{os.path.basename(path)}: {e}")

    if adicionados:
        msg = f"{adicionados} base(s) adicionada(s)."
        if problemas:
            msg += "\n\nNão adicionados:\n" + "\n".join(f"  • {p}" for p in problemas)
            messagebox.showwarning("Resultado", msg)
        elif adicionados > 1:
            messagebox.showinfo("Bases", msg)

    atualizar_status_cobertura()


def remover_base_selecionada():
    selecionados = tree_bases.selection()
    if not selecionados:
        messagebox.showwarning("Atenção", "Selecione uma base para remover.")
        return
    for iid in selecionados:
        bases_data[:] = [b for b in bases_data if b["obs"] != iid]
    atualizar_tree_bases()
    atualizar_status_cobertura()


def limpar_bases():
    if not bases_data:
        return
    if messagebox.askyesno("Confirmar", "Remover todas as bases da lista?"):
        bases_data.clear()
        atualizar_tree_bases()
        atualizar_status_cobertura()


tk.Button(frame_bases, text="Adicionar OBS…", command=adicionar_base_obs).grid(
    row=1, column=0, sticky="w", pady=(4, 0)
)
tk.Button(frame_bases, text="Remover", command=remover_base_selecionada).grid(
    row=1, column=1, sticky="w", padx=4, pady=(4, 0)
)
tk.Button(frame_bases, text="Limpar", command=limpar_bases).grid(
    row=1, column=2, sticky="w", pady=(4, 0)
)


def atualizar_status_cobertura():
    base_paths = obter_caminhos_base()
    if not missions_data or not base_paths:
        label_cobertura.config(text="", fg="darkorange")
        return

    try:
        bases = [parse_obs_span(path) for path in base_paths]
        problemas = []
        ok_count = 0

        for mission in missions_data:
            rover = parse_obs_span(mission["rover"])
            report = plan_coverage(rover, bases, "POS_PPK.pos")
            nome = os.path.basename(mission["mrk"])
            if report.ok and not report.warnings:
                ok_count += 1
            elif report.errors:
                problemas.append(f"{nome}: {report.errors[0]}")
            elif report.warnings:
                problemas.append(f"{nome}: {report.warnings[0]}")

        if problemas:
            label_cobertura.config(text=f"↳ {problemas[0]}", fg="red")
        elif ok_count == len(missions_data):
            label_cobertura.config(
                text=f"↳ Cobertura OK para {ok_count} rover(s)",
                fg="green",
            )
    except Exception as e:
        label_cobertura.config(text=f"↳ Erro ao verificar cobertura: {e}", fg="red")


def _escolher_pasta_saida():
    pasta = filedialog.askdirectory(title="Pasta para planilha consolidada")
    if pasta:
        entry_saida_consolidada.delete(0, tk.END)
        entry_saida_consolidada.insert(0, pasta)


def atualizar_tree_missions():
    for item in tree_missions.get_children():
        tree_missions.delete(item)
    for mission in missions_data:
        tree_missions.insert(
            "",
            tk.END,
            iid=mission["mrk"],
            values=(
                os.path.basename(mission["folder"]),
                os.path.basename(mission["mrk"]),
                os.path.basename(mission["rover"]),
                mission.get("status", "pendente"),
            ),
        )


def _definir_pasta_saida_padrao(folder):
    if not entry_saida_consolidada.get().strip():
        entry_saida_consolidada.insert(0, folder)


def _missao_ja_existe(mrk_path):
    mrk_norm = os.path.normpath(mrk_path)
    return any(m["mrk"] == mrk_norm for m in missions_data)


def registrar_missao_mrk(mrk_path, avisar=True):
    if _missao_ja_existe(mrk_path):
        raise ValueError(f"O .MRK já está na lista:\n{os.path.basename(mrk_path)}")

    info = discover_rover_for_mrk(mrk_path)
    info["rover"] = converter_hatanaka_se_necessario(info["rover"])
    info["status"] = "pendente"
    missions_data.append(info)
    _definir_pasta_saida_padrao(info["folder"])
    atualizar_tree_missions()
    atualizar_status_cobertura()

    if avisar and info.get("warning"):
        messagebox.showwarning("Atenção", info["warning"])
    return info


def adicionar_mrk_missao():
    paths = filedialog.askopenfilenames(
        title="Selecionar arquivo(s) .MRK",
        filetypes=[("Arquivo MRK", "*.MRK"), ("Todos os arquivos", "*.*")],
    )
    if not paths:
        return

    adicionados = 0
    problemas = []
    for path in paths:
        try:
            registrar_missao_mrk(path, avisar=False)
            adicionados += 1
        except Exception as e:
            problemas.append(f"{os.path.basename(path)}: {e}")

    if adicionados:
        msg = f"{adicionados} missão(ões) adicionada(s)."
        if problemas:
            msg += "\n\nNão adicionados:\n" + "\n".join(f"  • {p}" for p in problemas)
            messagebox.showwarning("Resultado", msg)
        elif adicionados > 1:
            messagebox.showinfo("Missões", msg)

    atualizar_status_cobertura()


def remover_missao_selecionada():
    selecionados = tree_missions.selection()
    if not selecionados:
        messagebox.showwarning("Atenção", "Selecione uma missão para remover.")
        return
    for iid in selecionados:
        missions_data[:] = [m for m in missions_data if m["mrk"] != iid]
    atualizar_tree_missions()
    atualizar_status_cobertura()


def limpar_missoes():
    if not missions_data:
        return
    if messagebox.askyesno("Confirmar", "Remover todas as missões da lista?"):
        missions_data.clear()
        atualizar_tree_missions()
        atualizar_status_cobertura()


tk.Button(frame_missions, text="Adicionar .MRK…", command=adicionar_mrk_missao).grid(
    row=2, column=0, sticky="w", pady=(4, 0)
)
tk.Button(frame_missions, text="Remover", command=remover_missao_selecionada).grid(
    row=2, column=1, sticky="w", padx=4, pady=(4, 0)
)
tk.Button(frame_missions, text="Limpar", command=limpar_missoes).grid(
    row=2, column=2, sticky="w", pady=(4, 0)
)


def validar_cobertura_lote(missions, base_paths, perguntar=True):
    """Valida cobertura de todas as missões; retorna False se o usuário cancelar."""
    bases = [parse_obs_span(path) for path in base_paths]
    linhas = []
    bloqueio = False

    for mission in missions:
        rover = parse_obs_span(mission["rover"])
        report = plan_coverage(rover, bases, "POS_PPK.pos")
        nome = os.path.basename(mission["mrk"])

        if any("marco físico" in e for e in report.errors):
            messagebox.showerror(
                "Bases incompatíveis",
                f"Missão '{nome}':\n{report.alert_message()}",
            )
            return False

        if not report.ok or report.warnings:
            bloqueio = bloqueio or not report.ok
            linhas.append(f"[{nome}]\n{report.alert_message()}")

    if not linhas:
        return True

    if not perguntar:
        return not bloqueio

    titulo = "Cobertura incompleta" if bloqueio else "Aviso de cobertura"
    texto = "\n\n".join(linhas) + "\n\nDeseja continuar mesmo assim?"
    return messagebox.askyesno(titulo, texto)


def obter_l_arg():
    lat_gms = entry_lat_gms.get().strip()
    lon_gms = entry_lon_gms.get().strip()
    alt_gms = entry_alt_gms.get().strip()
    if not lat_gms or not lon_gms:
        return ""
    lat_dec = dms_to_decimal(lat_gms)
    lon_dec = dms_to_decimal(lon_gms)
    alt_dec = float(alt_gms) if alt_gms else 0.0
    return f" -l {lat_dec:.8f} {lon_dec:.8f} {alt_dec:.3f}"


def executar_processamento(l_arg):
    if not missions_data:
        messagebox.showwarning("Atenção", "Adicione pelo menos um arquivo .MRK na lista de rovers.")
        return
    if not bases_data:
        messagebox.showwarning("Atenção", "Adicione pelo menos um arquivo OBS de base.")
        return

    base_paths = [os.path.normpath(p) for p in obter_caminhos_base()]
    base_nav = os.path.normpath(obter_nav())
    output_dir = entry_saida_consolidada.get().strip() or missions_data[0]["folder"]
    output_dir = os.path.normpath(output_dir)

    if not validar_cobertura_lote(missions_data, base_paths):
        return

    mrk_pos_pairs = []
    falhas = []
    segmentos_total = 0

    for mission in missions_data:
        mission["status"] = "processando…"
        atualizar_tree_missions()
        root.update_idletasks()

        pasta = mission["folder"]
        mrk_path = mission["mrk"]
        rover_obs = mission["rover"]
        saida_pos = os.path.normpath(os.path.join(pasta, "POS_PPK.pos"))

        try:
            report = process_rover_with_bases(
                rnx2rtkp_path,
                config_path,
                rover_obs,
                base_paths,
                base_nav,
                saida_pos,
                l_arg=l_arg,
            )
            if report.errors:
                mission["status"] = "erro"
                falhas.append(f"{os.path.basename(mrk_path)}: {report.errors[0]}")
                continue

            segmentos_total += len(report.segments)
            ppk_process.process_ppk(
                mrk_path,
                saida_pos,
                proj4_str=None,
                output_dir=pasta,
                output_format=saida_var.get(),
            )
            mrk_pos_pairs.append((mrk_path, saida_pos))
            mission["status"] = "OK"
        except Exception as e:
            mission["status"] = "erro"
            falhas.append(f"{os.path.basename(mrk_path)}: {e}")

    atualizar_tree_missions()

    if not mrk_pos_pairs:
        messagebox.showerror("Erro", "Nenhuma missão processada com sucesso.\n\n" + "\n".join(falhas))
        return

    try:
        ppk_process.process_combined_missions(
            mrk_pos_pairs, output_dir, saida_var.get(), proj4_str=None
        )
        arquivo = os.path.join(
            output_dir, ppk_process.consolidated_output_basename(saida_var.get())
        )
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao gerar planilha consolidada:\n{e}")
        return

    msg = (
        f"Processadas {len(mrk_pos_pairs)} de {len(missions_data)} missão(ões).\n"
        f"Planilha consolidada:\n{arquivo}"
    )
    if segmentos_total > len(mrk_pos_pairs):
        msg += f"\n({segmentos_total} segmentos de base no total)"
    if falhas:
        msg += "\n\nFalhas:\n" + "\n".join(f"  • {f}" for f in falhas)
    messagebox.showinfo("Execução", msg)


def executar_script():
    try:
        l_arg = obter_l_arg()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao converter coordenada GMS: {e}")
        return

    try:
        executar_processamento(l_arg)
    except Exception as e:
        messagebox.showerror("Erro", f"Falha no processamento PPK:\n{e}")


tk.Button(root, text="Executar script", command=executar_script, bg="lightgreen").grid(row=5, column=1, pady=10)

atualizar_lista_pontos()
root.mainloop()
