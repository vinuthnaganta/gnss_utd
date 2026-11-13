import pandas as pd
from pathlib import Path

filename = "gnss_files/gnss_log_2026_11_04_12_13_10.txt"

CONSTELLATIONS = {0: "UNKNOWN", 1: "GPS", 2: "SBAS", 3: "GLONASS",
                  4: "QZSS", 5: "BEIDOU", 6: "GALILEO", 7: "IRNSS"}

BANDS = {
    ("GPS", 1575): "L1", ("GPS", 1227): "L2", ("GPS", 1176): "L5",
    ("GALILEO", 1575): "E1", ("GALILEO", 1176): "E5a", ("GALILEO", 1207): "E5b",
    ("BEIDOU", 1575): "B1C", ("BEIDOU", 1561): "B1I", ("BEIDOU", 1176): "B2a",
    ("BEIDOU", 1207): "B2I", ("BEIDOU", 1268): "B3I",
    ("QZSS", 1575): "L1", ("QZSS", 1227): "L2", ("QZSS", 1176): "L5",
    ("SBAS", 1575): "L1", ("SBAS", 1176): "L5",
    ("IRNSS", 1176): "L5",
}

def band_name(constellation, freq_hz):
    if pd.isna(freq_hz):
        return None
    mhz = freq_hz / 1e6
    if constellation == "GLONASS":
        return "G1" if mhz > 1590 else "G2"
    return BANDS.get((constellation, round(mhz)), f"{mhz:.2f} MHz")

fix_cols, status_cols = None, None
last_fix_ms, epoch = None, -1
rows = []

with open(filename, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        if line.startswith("#"):
            parts = [p.strip() for p in line.lstrip("# ").split(",")]
            if len(parts) > 2:
                if parts[0] == "Fix":
                    fix_cols = parts[1:]
                elif parts[0] == "Status":
                    status_cols = parts[1:]
            continue

        parts = line.split(",")

        if parts[0] == "Fix":
            epoch += 1
            fix = dict(zip(fix_cols, parts[1:]))
            last_fix_ms = pd.to_numeric(fix.get("UnixTimeMillis"), errors="coerce")

        elif parts[0] == "Status":
            rec = dict(zip(status_cols, parts[1:]))
            rec["epoch_id"] = epoch
            rec["fix_time_ms"] = last_fix_ms
            rows.append(rec)

df = pd.DataFrame(rows)

num_cols = ["UnixTimeMillis", "SignalCount", "SignalIndex", "ConstellationType",
            "Svid", "CarrierFrequencyHz", "Cn0DbHz", "AzimuthDegrees",
            "ElevationDegrees"]
for c in num_cols:
    df[c] = pd.to_numeric(df[c], errors="coerce")

time_ms = df["UnixTimeMillis"].fillna(df["fix_time_ms"])

out = pd.DataFrame({
    "epoch_id": df["epoch_id"],
    "utc_time": pd.to_datetime(time_ms, unit="ms", utc=True),
    "Constellation": df["ConstellationType"].map(CONSTELLATIONS),
    "Svid": df["Svid"],
    "CarrierFrequencyHz": df["CarrierFrequencyHz"] / 1e6,
    "Cn0DbHz": df["Cn0DbHz"],
    "AzimuthDegrees": df["AzimuthDegrees"],
    "ElevationDegrees": df["ElevationDegrees"]
})
out["band"] = [band_name(c, f * 1e6) for c, f in zip(out["Constellation"], out["CarrierFrequencyHz"])]

out = out[["epoch_id", "utc_time", "Constellation", "Svid", "band",
           "CarrierFrequencyHz", "Cn0DbHz", "AzimuthDegrees", "ElevationDegrees"]]

Path("results").mkdir(exist_ok=True)
out.to_csv("results/gnss_signals_calm_day_phase_0.csv", index=False)