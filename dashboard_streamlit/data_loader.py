"""Carga y validación de reportes integrales para el dashboard V2."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


REQUIRED_TABLES = {
    "episodios": {"algoritmo", "semilla", "recompensa_acumulada", "recursos_usados"},
    "resumen_algoritmos": {"algoritmo", "recompensa_acumulada_mean"},
    "clasificaciones_propuestas": {
        "algoritmo", "tipo_clasificacion", "accion", "accion_nombre", "n", "porcentaje"
    },
    "clasificaciones_ejecutadas": {
        "algoritmo", "tipo_clasificacion", "accion", "accion_nombre", "n", "porcentaje"
    },
    "estabilidad_semillas": {"algoritmo"},
    "metricas_subgrupos": {
        "algoritmo", "semilla", "dimension", "subgrupo", "cobertura", "intensidad_media"
    },
    "brechas_equidad": {"algoritmo", "semilla", "dimension"},
}

OPTIONAL_TABLES = {
    "detalle",
    "sensibilidad_episodios",
    "sensibilidad_resumen",
    # Notebook 10: cumplimiento de la Definición del PIDA.
    "criterios_pida",
    "rendimiento_ic",
    "robustez_escenarios",
    "brechas_subgrupos_pida",
    "verificacion_diccionario",
}

ALLOWED_RISK_CATEGORIES = {"bajo", "medio", "alto"}
ALLOWED_ACTIONS = {0, 1, 2, 3}


class DashboardDataError(ValueError):
    """Error legible para datos faltantes, incompatibles o no auditables."""


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception as exc:
        raise DashboardDataError(f"No fue posible leer {path.name}: {exc}") from exc


def _validate_columns(name: str, frame: pd.DataFrame, expected: set[str]) -> None:
    missing = sorted(expected - set(frame.columns))
    if missing:
        raise DashboardDataError(
            f"La tabla {name}.csv no contiene las columnas requeridas: {', '.join(missing)}"
        )


def _validate_actions(tables: dict[str, pd.DataFrame]) -> None:
    for name in ("clasificaciones_propuestas", "clasificaciones_ejecutadas"):
        actions = set(pd.to_numeric(tables[name]["accion"], errors="coerce").dropna().astype(int))
        unexpected = actions - ALLOWED_ACTIONS
        if unexpected:
            raise DashboardDataError(
                f"{name}.csv contiene acciones no admitidas: {sorted(unexpected)}"
            )


def _validate_risk_categories(tables: dict[str, pd.DataFrame]) -> None:
    groups = tables["metricas_subgrupos"]
    risk = groups.loc[groups["dimension"] == "categoria_riesgo", "subgrupo"].dropna()
    unexpected = set(risk.astype(str)) - ALLOWED_RISK_CATEGORIES
    if unexpected:
        raise DashboardDataError(
            "Se detectaron categorías de riesgo fuera del acuerdo bajo/medio/alto: "
            + ", ".join(sorted(unexpected))
        )


def _validate_manifest(directory: Path, manifest: pd.DataFrame) -> None:
    _validate_columns("manifest", manifest, {"tabla", "archivo", "filas"})
    for row in manifest.itertuples(index=False):
        filename = str(row.archivo)
        if Path(filename).name != filename:
            raise DashboardDataError("El manifiesto contiene una ruta de archivo no segura.")
        path = directory / filename
        if not path.is_file():
            raise DashboardDataError(f"El manifiesto referencia un archivo inexistente: {filename}")
        actual = len(_read_csv(path))
        if actual != int(row.filas):
            raise DashboardDataError(
                f"El manifiesto declara {row.filas} filas para {filename}, pero se encontraron {actual}."
            )


def report_fingerprint(directory: str | Path, manifest: pd.DataFrame | None = None) -> str:
    """Devuelve una huella corta reproducible del conjunto de CSV disponible."""
    directory = Path(directory)
    if manifest is not None and not manifest.empty:
        filenames = sorted(manifest["archivo"].astype(str).tolist())
    else:
        filenames = sorted(path.name for path in directory.glob("*.csv"))
    digest = hashlib.sha256()
    for filename in filenames:
        path = directory / filename
        if path.is_file():
            digest.update(filename.encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def load_integral_report(directory: str | Path) -> dict[str, pd.DataFrame | str]:
    """Carga el reporte V2, valida esquema, manifiesto, acciones y niveles de riesgo."""
    directory = Path(directory).expanduser().resolve()
    if not directory.is_dir():
        raise DashboardDataError(f"No existe el directorio de resultados: {directory}")

    tables: dict[str, pd.DataFrame | str] = {}
    missing_files = []
    for name, expected in REQUIRED_TABLES.items():
        path = directory / f"{name}.csv"
        if not path.is_file():
            missing_files.append(path.name)
            continue
        frame = _read_csv(path)
        _validate_columns(name, frame, expected)
        tables[name] = frame
    if missing_files:
        raise DashboardDataError(
            "Faltan tablas V2 requeridas: " + ", ".join(sorted(missing_files))
        )

    for name in OPTIONAL_TABLES:
        path = directory / f"{name}.csv"
        if path.is_file():
            tables[name] = _read_csv(path)

    manifest_path = directory / "manifest.csv"
    manifest = _read_csv(manifest_path) if manifest_path.is_file() else pd.DataFrame()
    if not manifest.empty:
        _validate_manifest(directory, manifest)
    tables["manifest"] = manifest

    typed_tables = {k: v for k, v in tables.items() if isinstance(v, pd.DataFrame)}
    _validate_actions(typed_tables)
    _validate_risk_categories(typed_tables)
    tables["fingerprint"] = report_fingerprint(directory, manifest if not manifest.empty else None)
    return tables


def filter_algorithms(frame: pd.DataFrame, algorithms: list[str]) -> pd.DataFrame:
    """Aplica un filtro homogéneo sin modificar la tabla original."""
    if "algoritmo" not in frame.columns or not algorithms:
        return frame.iloc[0:0].copy()
    return frame.loc[frame["algoritmo"].isin(algorithms)].copy()
