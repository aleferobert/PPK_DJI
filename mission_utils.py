"""Associação .MRK → rover OBS na mesma pasta."""

import os
import re

OBS_EXT_RE = re.compile(r"\.((?:\d{2}[OD])|OBS)$", re.I)
NAV_EXT_RE = re.compile(r"\.((?:\d{2}N)|NAV)$", re.I)


def is_obs_file(filename: str) -> bool:
    return bool(OBS_EXT_RE.search(filename)) and not NAV_EXT_RE.search(filename)


def is_nav_file(filename: str) -> bool:
    return bool(NAV_EXT_RE.search(filename))


def discover_nav_for_obs(obs_path: str) -> str:
    """Localiza o arquivo NAV (.NAV / .??N) na mesma pasta do OBS."""
    obs_path = os.path.normpath(obs_path)
    folder = os.path.dirname(obs_path)
    basename = os.path.basename(obs_path)
    stem, ext = os.path.splitext(basename)

    if len(ext) == 4 and ext[1:3].isdigit() and ext[-1].upper() in ("O", "D"):
        nav_candidate = os.path.join(folder, stem + ext[:-1] + "n")
        if os.path.isfile(nav_candidate):
            return nav_candidate
        nav_candidate = os.path.join(folder, stem + ext[:-1] + "N")
        if os.path.isfile(nav_candidate):
            return nav_candidate

    nav_files = sorted(
        os.path.join(folder, name)
        for name in os.listdir(folder)
        if is_nav_file(name)
    )
    if not nav_files:
        raise ValueError(f"Nenhum arquivo NAV na pasta:\n{folder}")

    if len(nav_files) > 1:
        for nav in nav_files:
            if os.path.splitext(nav)[0] == stem:
                return nav

    return nav_files[0]


def discover_base_obs(obs_path: str) -> dict:
    """Registra base OBS e NAV associado na mesma pasta."""
    obs_path = os.path.normpath(obs_path)
    if not is_obs_file(os.path.basename(obs_path)):
        raise ValueError("Selecione um arquivo OBS de base (.OBS / .??O / .??D)")

    nav_path = discover_nav_for_obs(obs_path)
    return {
        "folder": os.path.dirname(obs_path),
        "obs": obs_path,
        "nav": nav_path,
    }


def discover_rover_for_mrk(mrk_path: str) -> dict:
    """
    A partir de um .MRK, localiza o rover OBS na mesma pasta (sem busca recursiva).
    """
    mrk_path = os.path.normpath(mrk_path)
    if not os.path.isfile(mrk_path):
        raise ValueError(f"Arquivo .MRK não encontrado:\n{mrk_path}")
    if not mrk_path.upper().endswith(".MRK"):
        raise ValueError("Selecione um arquivo .MRK")

    folder = os.path.dirname(mrk_path)
    obs_files = sorted(
        os.path.join(folder, name)
        for name in os.listdir(folder)
        if is_obs_file(name)
    )
    if not obs_files:
        raise ValueError(
            f"Nenhum arquivo OBS do rover na pasta do .MRK:\n{folder}"
        )

    rover_path = obs_files[0]
    warning = None
    if len(obs_files) > 1:
        warning = (
            f"Vários OBS em '{os.path.basename(folder)}'; "
            f"usando {os.path.basename(rover_path)}"
        )

    return {
        "folder": folder,
        "mrk": mrk_path,
        "rover": rover_path,
        "warning": warning,
    }
