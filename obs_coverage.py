"""Validação temporal rover × base(s) e planejamento de processamento por segmento."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import math
import os
from typing import List, Optional, Tuple

from pyproj import Transformer

_ECEF_TO_GEO = Transformer.from_crs("epsg:4978", "epsg:4326", always_xy=True)


@dataclass
class ObsSpan:
    path: str
    t0: datetime
    t1: datetime
    lat: Optional[float] = None
    lon: Optional[float] = None
    alt: Optional[float] = None

    @property
    def basename(self) -> str:
        return os.path.basename(self.path)


@dataclass
class CoverageSegment:
    base_path: str
    ts: datetime
    te: datetime
    pos_output: str


@dataclass
class CoverageReport:
    rover: ObsSpan
    bases: List[ObsSpan]
    ok: bool
    segments: List[CoverageSegment] = field(default_factory=list)
    gaps: List[Tuple[datetime, datetime]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def alert_message(self) -> str:
        lines = [
            f"Rover: {self.rover.basename}",
            f"  Período: {format_periodo(self.rover.t0, self.rover.t1)}",
            "Bases:",
        ]
        for base in self.bases:
            lines.append(f"  • {base.basename}: {format_periodo(base.t0, base.t1)}")
        lines.append("")

        if self.errors:
            lines.append("Erros:")
            lines.extend(f"  • {e}" for e in self.errors)
        if self.gaps:
            lines.append("Trechos do rover SEM cobertura de base:")
            for g0, g1 in self.gaps:
                lines.append(f"  • {format_periodo(g0, g1)}")
        if self.warnings:
            lines.append("Avisos:")
            lines.extend(f"  • {w}" for w in self.warnings)
        if self.segments and len(self.segments) > 1:
            lines.append("Processamento por segmento:")
            for seg in self.segments:
                lines.append(
                    f"  • {format_periodo(seg.ts, seg.te)}  |  "
                    f"base: {os.path.basename(seg.base_path)}"
                )
        return "\n".join(lines)


def format_periodo(t0: datetime, t1: datetime) -> str:
    fmt = "%d/%m/%Y %H:%M:%S"
    return f"{t0.strftime(fmt)} → {t1.strftime(fmt)}"


def parse_obs_span(file_path: str) -> ObsSpan:
    lat, lon, alt, t0, t1 = None, None, None, None, None
    with open(file_path, "r", encoding="latin1") as f:
        for line in f:
            if "APPROX POSITION XYZ" in line:
                parts = list(map(float, line.strip().split()[0:3]))
                lon, lat, alt = _ECEF_TO_GEO.transform(*parts)
            elif "TIME OF FIRST OBS" in line:
                parts = line.strip().split()
                date_str = (
                    f"{parts[0]}-{parts[1]}-{parts[2]} "
                    f"{parts[3]}:{parts[4]}:{float(parts[5]):02.0f}"
                )
                t0 = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            elif "TIME OF LAST OBS" in line:
                parts = line.strip().split()
                date_str = (
                    f"{parts[0]}-{parts[1]}-{parts[2]} "
                    f"{parts[3]}:{parts[4]}:{float(parts[5]):02.0f}"
                )
                t1 = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            if lat is not None and lon is not None and alt is not None and t0 and t1:
                break

    if t0 is None or t1 is None:
        raise ValueError(f"Não foi possível ler o período de observação: {file_path}")

    return ObsSpan(path=file_path, t0=t0, t1=t1, lat=lat, lon=lon, alt=alt)


def parse_obs_info(file_path):
    """Compatível com a API anterior de ppk_drone.py."""
    span = parse_obs_span(file_path)
    return span.lat, span.lon, span.alt, span.t0, span.t1


def _haversine_m(lat1, lon1, lat2, lon2) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def validate_same_base_station(
    bases: List[ObsSpan],
    max_horiz_m: float = 0.5,
    max_vert_m: float = 1.0,
) -> List[str]:
    errors = []
    with_coords = [b for b in bases if b.lat is not None and b.lon is not None]
    if len(with_coords) < 2:
        return errors

    ref = with_coords[0]
    for base in with_coords[1:]:
        horiz = _haversine_m(ref.lat, ref.lon, base.lat, base.lon)
        vert = abs((base.alt or 0) - (ref.alt or 0))
        if horiz > max_horiz_m or vert > max_vert_m:
            errors.append(
                f"Base '{base.basename}' está a {horiz:.2f} m (H) / {vert:.2f} m (V) "
                f"de '{ref.basename}'. Mesclar ou processar juntas só é válido "
                f"para o mesmo marco físico."
            )
    return errors


def _merge_intervals(
    intervals: List[Tuple[datetime, datetime]],
) -> List[Tuple[datetime, datetime]]:
    if not intervals:
        return []
    sorted_iv = sorted(intervals, key=lambda x: x[0])
    merged = [sorted_iv[0]]
    for start, end in sorted_iv[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def _subtract_gaps(
    window: Tuple[datetime, datetime],
    covered: List[Tuple[datetime, datetime]],
) -> List[Tuple[datetime, datetime]]:
    w0, w1 = window
    if w0 >= w1:
        return []

    gaps = [(w0, w1)]
    for c0, c1 in covered:
        new_gaps = []
        for g0, g1 in gaps:
            if c1 <= g0 or c0 >= g1:
                new_gaps.append((g0, g1))
                continue
            if g0 < c0:
                new_gaps.append((g0, c0))
            if c1 < g1:
                new_gaps.append((c1, g1))
        gaps = new_gaps
    return [(g0, g1) for g0, g1 in gaps if g0 < g1]


def plan_coverage(
    rover: ObsSpan,
    bases: List[ObsSpan],
    output_pos: str,
) -> CoverageReport:
    report = CoverageReport(rover=rover, bases=bases, ok=True)

    if not bases:
        report.ok = False
        report.errors.append("Nenhum arquivo de base informado.")
        return report

    station_errors = validate_same_base_station(bases)
    report.errors.extend(station_errors)

    r0, r1 = rover.t0, rover.t1
    sorted_bases = sorted(bases, key=lambda b: b.t0)

    overlaps: List[Tuple[datetime, datetime]] = []
    segments: List[CoverageSegment] = []

    for i, base in enumerate(sorted_bases):
        seg_start = max(r0, base.t0)
        seg_end = min(r1, base.t1)
        if seg_start >= seg_end:
            report.warnings.append(
                f"Base '{base.basename}' ({format_periodo(base.t0, base.t1)}) "
                f"não sobrepõe o rover ({format_periodo(r0, r1)})."
            )
            continue

        overlaps.append((seg_start, seg_end))
        segments.append(
            CoverageSegment(
                base_path=base.path,
                ts=seg_start,
                te=seg_end,
                pos_output=f"{output_pos}.part{i:02d}",
            )
        )

    if not segments:
        report.ok = False
        report.errors.append(
            "Nenhuma base cobre o período do rover. Verifique os arquivos selecionados."
        )
        return report

    covered = _merge_intervals(overlaps)
    gaps = _subtract_gaps((r0, r1), covered)

    if gaps:
        report.ok = False
        report.gaps = gaps
        report.errors.append(
            "A base (ou o conjunto de bases) não cobre toda a observação do rover. "
            "Arquivo incorreto ou faltam segmentos de base."
        )

    for i in range(len(sorted_bases) - 1):
        b1, b2 = sorted_bases[i], sorted_bases[i + 1]
        if b1.t1 < b2.t0:
            gap_start = max(r0, b1.t1)
            gap_end = min(r1, b2.t0)
            if gap_start < gap_end:
                report.warnings.append(
                    f"Intervalo sem base entre '{b1.basename}' e '{b2.basename}': "
                    f"{format_periodo(gap_start, gap_end)}"
                )

    report.segments = segments
    return report


def format_rtklib_time(dt: datetime) -> str:
    return dt.strftime("%Y/%m/%d %H:%M:%S")
