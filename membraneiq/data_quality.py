from __future__ import annotations

from dataclasses import dataclass, asdict
import pandas as pd


@dataclass
class ColumnQuality:
    column: str
    missing_pct: float
    numeric_pct: float
    constant: bool
    suspicious: bool


@dataclass
class DataQualityReport:
    rows: int
    duplicate_rows: int
    columns: list[ColumnQuality]
    score: float
    warnings: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def assess_dataframe(df: pd.DataFrame) -> DataQualityReport:
    warnings: list[str] = []
    columns: list[ColumnQuality] = []

    if len(df) == 0:
        return DataQualityReport(0, 0, [], 0.0, ["Dataset contains no rows"])

    duplicate_rows = int(df.duplicated().sum())
    if duplicate_rows:
        warnings.append(f"{duplicate_rows} duplicate rows detected")

    penalties = 0.0
    for name in df.columns:
        series = df[name]
        missing_pct = float(series.isna().mean() * 100)
        numeric = pd.to_numeric(series, errors="coerce")
        numeric_pct = float(numeric.notna().mean() * 100)
        constant = series.dropna().nunique() <= 1
        suspicious = missing_pct > 20 or (numeric_pct >= 80 and constant)
        if missing_pct > 20:
            warnings.append(f"{name}: {missing_pct:.1f}% missing")
            penalties += min(20.0, missing_pct * 0.2)
        if numeric_pct >= 80 and constant:
            warnings.append(f"{name}: numeric signal is constant/stuck")
            penalties += 8.0
        columns.append(
            ColumnQuality(
                column=str(name),
                missing_pct=round(missing_pct, 1),
                numeric_pct=round(numeric_pct, 1),
                constant=constant,
                suspicious=suspicious,
            )
        )

    if duplicate_rows:
        penalties += min(10.0, 100.0 * duplicate_rows / len(df))
    score = max(0.0, 100.0 - penalties)
    return DataQualityReport(
        rows=len(df),
        duplicate_rows=duplicate_rows,
        columns=columns,
        score=round(score, 1),
        warnings=warnings,
    )
