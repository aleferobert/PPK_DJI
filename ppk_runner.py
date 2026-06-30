"""Execução do rnx2rtkp por segmento temporal e junção dos .pos resultantes."""

import os
import subprocess

from obs_coverage import (
    CoverageReport,
    format_rtklib_time,
    parse_obs_span,
    plan_coverage,
)
from ppk_process import merge_pos_files


def run_rnx2rtkp(
    rnx2rtkp_path: str,
    config_path: str,
    rover_obs: str,
    base_obs: str,
    nav_path: str,
    output_pos: str,
    l_arg: str = "",
    ts=None,
    te=None,
) -> subprocess.CompletedProcess:
    ts_arg = f' -ts {format_rtklib_time(ts)}' if ts else ""
    te_arg = f' -te {format_rtklib_time(te)}' if te else ""
    comando = (
        f'"{os.path.normpath(rnx2rtkp_path)}" -k "{os.path.normpath(config_path)}"'
        f'{ts_arg}{te_arg} '
        f'"{os.path.normpath(rover_obs)}" "{os.path.normpath(base_obs)}" '
        f'"{os.path.normpath(nav_path)}" -o "{os.path.normpath(output_pos)}"{l_arg}'
    )
    print(comando)
    return subprocess.run(comando, shell=True, capture_output=True, text=True)


def process_rover_with_bases(
    rnx2rtkp_path: str,
    config_path: str,
    rover_obs: str,
    base_obs_paths: list[str],
    nav_path: str,
    output_pos: str,
    l_arg: str = "",
) -> CoverageReport:
    rover = parse_obs_span(rover_obs)
    bases = [parse_obs_span(path) for path in base_obs_paths]
    report = plan_coverage(rover, bases, output_pos)

    if not report.segments:
        return report

    partial_files: list[str] = []
    try:
        for seg in report.segments:
            result = run_rnx2rtkp(
                rnx2rtkp_path,
                config_path,
                rover_obs,
                seg.base_path,
                nav_path,
                seg.pos_output,
                l_arg=l_arg,
                ts=seg.ts,
                te=seg.te,
            )
            if result.returncode != 0:
                report.ok = False
                report.errors.append(
                    f"rnx2rtkp falhou no segmento {seg.ts} → {seg.te} "
                    f"({os.path.basename(seg.base_path)}):\n{result.stderr}"
                )
                return report
            partial_files.append(seg.pos_output)

        if len(partial_files) == 1:
            if os.path.isfile(output_pos):
                os.remove(output_pos)
            os.replace(partial_files[0], output_pos)
        else:
            merge_pos_files(partial_files, output_pos)
    finally:
        for path in partial_files:
            if os.path.isfile(path) and path != output_pos:
                try:
                    os.remove(path)
                except OSError:
                    pass

    return report
