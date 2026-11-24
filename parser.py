import csv
from datetime import datetime, timezone
from pathlib import Path


INPUT_ROOT = Path("gnss_files")
OUTPUT_ROOT = Path("results")

CONSTELLATIONS = {
    0: "UNKNOWN",
    1: "GPS",
    2: "SBAS",
    3: "GLONASS",
    4: "QZSS",
    5: "BEIDOU",
    6: "GALILEO",
    7: "IRNSS",
}

BANDS = {
    ("GPS", 1575): "L1",
    ("GPS", 1227): "L2",
    ("GPS", 1176): "L5",
    ("GALILEO", 1575): "E1",
    ("GALILEO", 1176): "E5a",
    ("GALILEO", 1207): "E5b",
    ("QZSS", 1575): "L1",
    ("QZSS", 1227): "L2",
    ("QZSS", 1176): "L5",
    ("SBAS", 1575): "L1",
    ("SBAS", 1176): "L5",
    ("BEIDOU", 1575): "B1C",
    ("BEIDOU", 1561): "B1I",
    ("BEIDOU", 1176): "B2a",
    ("BEIDOU", 1207): "B2I",
    ("BEIDOU", 1268): "B3I",
    ("IRNSS", 1176): "L5",
}


def numeric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def integer(value):
    number = numeric(value)
    if number is None:
        return ""
    return int(number) if number.is_integer() else number


def band_name(constellation, frequency_hz):
    if frequency_hz is None:
        return None

    mhz = frequency_hz / 1_000_000
    if constellation == "GLONASS":
        return "G1" if mhz > 1590 else "G2"

    return BANDS.get((constellation, round(mhz)), f"{mhz:.2f} MHz")


def parse_text_file(path):
    fix_columns = None
    status_columns = None
    last_fix_ms = None
    epoch_id = -1
    records = []

    with path.open("r", encoding="utf-8") as log_file:
        for raw_line in log_file:
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("#"):
                parts = [part.strip() for part in line.lstrip("# ").split(",")]
                if len(parts) > 2:
                    if parts[0] == "Fix":
                        fix_columns = parts[1:]
                    elif parts[0] == "Status":
                        status_columns = parts[1:]
                continue

            parts = line.split(",")
            if parts[0] == "Fix":
                epoch_id += 1
                if fix_columns:
                    fix = dict(zip(fix_columns, parts[1:]))
                    fix_ms = numeric(fix.get("UnixTimeMillis"))
                    if fix_ms is not None:
                        last_fix_ms = fix_ms

            elif parts[0] == "Status" and status_columns:
                status = dict(zip(status_columns, parts[1:]))
                status_ms = numeric(status.get("UnixTimeMillis"))
                records.append(
                    {
                        "epoch_id": epoch_id,
                        "status_ms": status_ms,
                        "fix_ms": last_fix_ms,
                        **status,
                    }
                )

    if not records:
        return []

    relative_path = path.relative_to(INPUT_ROOT)
    folder_parts = relative_path.parts[:-1]
    table = []

    for record in records:
        constellation_type = numeric(record.get("ConstellationType"))
        constellation_id = int(constellation_type) if constellation_type is not None else None
        constellation = CONSTELLATIONS.get(constellation_id, "UNKNOWN")
        frequency_hz = numeric(record.get("CarrierFrequencyHz"))
        time_ms = record["status_ms"] if record["status_ms"] is not None else record["fix_ms"]

        utc_time = ""
        if time_ms is not None:
            utc_time = (
                datetime.fromtimestamp(time_ms / 1000, tz=timezone.utc)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z")
            )

        table.append(
            {
                "epoch_id": record["epoch_id"],
                "utc_time": utc_time,
                "phase": folder_parts[0] if len(folder_parts) > 0 else "",
                "folder_scenario": folder_parts[1] if len(folder_parts) > 1 else "",
                "folder_detail": folder_parts[2] if len(folder_parts) > 2 else "",
                "constellation": constellation,
                "satellite_id": integer(record.get("Svid")),
                "frequency_band": band_name(constellation, frequency_hz),
                "carrier_frequency_mhz": frequency_hz / 1_000_000 if frequency_hz is not None else "",
                "cn0_db_hz": numeric(record.get("Cn0DbHz")),
                "azimuth_degrees": numeric(record.get("AzimuthDegrees")),
                "elevation_degrees": numeric(record.get("ElevationDegrees")),
                "source_file": relative_path.as_posix(),
            }
        )

    table.sort(
        key=lambda row: (
            row["utc_time"],
            row["constellation"],
            row["satellite_id"] if row["satellite_id"] is not None else float("inf"),
            row["frequency_band"] or "",
        )
    )
    return table


COLUMNS = [
        "epoch_id",
        "utc_time",
        "phase",
        "folder_scenario",
        "folder_detail",
        "constellation",
        "satellite_id",
        "frequency_band",
        "carrier_frequency_mhz",
        "cn0_db_hz",
        "azimuth_degrees",
        "elevation_degrees",
        "source_file",
]


def main():
    if not INPUT_ROOT.exists():
        raise FileNotFoundError(f"Input folder not found: {INPUT_ROOT}")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    combined_rows = []

    log_files = sorted(
        (path for path in INPUT_ROOT.rglob("*") if path.is_file() and path.suffix.lower() == ".txt"),
        key=lambda path: path.as_posix(),
    )

    for log_path in log_files:
        table = parse_text_file(log_path)
        if not table:
            continue

        relative_path = log_path.relative_to(INPUT_ROOT)
        output_path = OUTPUT_ROOT / relative_path.with_suffix(".csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(table)
        combined_rows.extend(table)

    if combined_rows:
        combined_rows.sort(
            key=lambda row: (
                row["phase"],
                row["folder_scenario"],
                row["folder_detail"],
                row["utc_time"],
                row["constellation"],
                row["satellite_id"] if row["satellite_id"] is not None else float("inf"),
                row["frequency_band"] or "",
            )
        )
        with (OUTPUT_ROOT / "gnss_signals.csv").open(
            "w", encoding="utf-8", newline=""
        ) as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(combined_rows)

    print(f"Parsed {len(log_files)} text files.")
    print(f"Saved {len(combined_rows)} rows across mirrored CSV folders.")


if __name__ == "__main__":
    main()
