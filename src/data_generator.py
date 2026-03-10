"""
src/data_generator.py — Generator syntetycznych danych gmin i szkół.

Generuje realistyczne dane przestrzenne uwzględniające korelację między
cechami a odległością od centrum obszaru (symulacja urban/rural gradient):

  - Obszary miejskie (bliżej centrum):
      · więcej uczniów, wyższe obłożenie szkół, lepsza sieć komunikacyjna,
        nieco wyższe wyniki egzaminów, niższy współczynnik dzietności.
  - Obszary wiejskie (dalej od centrum):
      · mniej uczniów, niższe obłożenie, słabsza komunikacja,
        nieco niższe wyniki egzaminów, wyższy współczynnik dzietności.

Istniejące szkoły rozmieszczone są koncentrycznie wokół centrum obszaru,
odzwierciedlając realia, w których centrum jest lepiej obsługiwane.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist


def generate_municipality_data(
    n_municipalities: int = 50,
    n_existing_schools: int = 15,
    area_size: float = 100.0,
    seed: int = 42,
) -> tuple[pd.DataFrame, np.ndarray]:
    """
    Generuje syntetyczne dane dla gmin i istniejących szkół.

    Parameters
    ----------
    n_municipalities : int
        Liczba gmin.
    n_existing_schools : int
        Liczba aktualnie istniejących szkół.
    area_size : float
        Wymiar kwadratowego obszaru geograficznego [km].
    seed : int
        Ziarno generatora losowego (odtwarzalność wyników).

    Returns
    -------
    municipalities : pd.DataFrame
        DataFrame z danymi gmin (kolumny opisane poniżej).
    existing_schools : np.ndarray, shape (n_existing_schools, 2)
        Macierz współrzędnych (x, y) istniejących szkół [km].

    Kolumny DataFrame:
        municipality_id     – identyfikator (GMN_000 … GMN_049)
        x, y                – współrzędne centroidu gminy [km]
        student_count       – szacunkowa roczna kohorta uczniów
        school_occupancy    – średnie obłożenie pobliskich szkół [%]
        connectivity_index  – wskaźnik dostępności komunikacyjnej [0–1]
        exam_score          – średni wynik egzaminów gminnych [0–100]
        fertility_rate      – współczynnik dzietności [dzieci/kobietę]
    """
    rng = np.random.default_rng(seed)

    # --- Rozmieszczenie gmin w klastrach przestrzennych ---
    n_clusters = 6
    cluster_centers = rng.uniform(0.1 * area_size, 0.9 * area_size, (n_clusters, 2))
    cluster_ids = rng.integers(0, n_clusters, size=n_municipalities)

    x = (cluster_centers[cluster_ids, 0] + rng.normal(0, 7, n_municipalities)).clip(1, area_size - 1)
    y = (cluster_centers[cluster_ids, 1] + rng.normal(0, 7, n_municipalities)).clip(1, area_size - 1)

    # --- Współczynnik „miejskości" oparty na odległości od centrum ---
    center = np.array([area_size / 2.0, area_size / 2.0])
    dist_to_center = np.hypot(x - center[0], y - center[1])
    urban = np.exp(-dist_to_center / (area_size * 0.28))  # zbliża się do 0 na obrzeżach

    # --- Generowanie zmiennych z realistyczną korelacją przestrzenną ---

    # 1. Liczba uczniów (100–2500): wyższa w miastach
    student_count = (
        300 + 2200 * urban + rng.normal(0, 180, n_municipalities)
    ).clip(100, 3000).astype(int)

    # 2. Obłożenie (55–125 %): wyższe w zatłoczonych miastach, niższe na wsi
    school_occupancy = (
        65 + 50 * urban + rng.normal(0, 8, n_municipalities)
    ).clip(50, 130)

    # 3. Wskaźnik skomunikowania (0.1–1.0): lepszy w miastach
    connectivity_index = (
        0.25 + 0.70 * urban + rng.normal(0, 0.07, n_municipalities)
    ).clip(0.05, 1.0)

    # 4. Wyniki egzaminów (35–95): nieznacznie wyższe w miastach
    exam_score = (
        55 + 32 * urban + rng.normal(0, 7, n_municipalities)
    ).clip(30, 100)

    # 5. Współczynnik dzietności (1.0–3.0): wyższy na wsi
    fertility_rate = (
        2.2 - 0.80 * urban + rng.normal(0, 0.12, n_municipalities)
    ).clip(1.0, 3.5)

    municipalities = pd.DataFrame(
        {
            "municipality_id":   [f"GMN_{i:03d}" for i in range(n_municipalities)],
            "x":                 np.round(x, 3),
            "y":                 np.round(y, 3),
            "student_count":     student_count,
            "school_occupancy":  np.round(school_occupancy, 2),
            "connectivity_index": np.round(connectivity_index, 4),
            "exam_score":        np.round(exam_score, 2),
            "fertility_rate":    np.round(fertility_rate, 3),
        }
    )

    # --- Istniejące szkoły koncentrycznie wokół centrum ---
    # ~70% szkół w pasie 0–35 km od centrum, ~30% rozproszone
    n_urban_schools = int(n_existing_schools * 0.70)
    n_rural_schools = n_existing_schools - n_urban_schools

    angle_u = rng.uniform(0, 2 * np.pi, n_urban_schools)
    r_u = rng.uniform(2, area_size * 0.35, n_urban_schools)
    sx_u = (center[0] + r_u * np.cos(angle_u)).clip(1, area_size - 1)
    sy_u = (center[1] + r_u * np.sin(angle_u)).clip(1, area_size - 1)

    sx_r = rng.uniform(1, area_size - 1, n_rural_schools)
    sy_r = rng.uniform(1, area_size - 1, n_rural_schools)

    school_x = np.concatenate([sx_u, sx_r])
    school_y = np.concatenate([sy_u, sy_r])
    existing_schools = np.column_stack([school_x, school_y])

    return municipalities, existing_schools


def add_distance_to_nearest_school(
    municipalities: pd.DataFrame,
    existing_schools: np.ndarray,
) -> pd.DataFrame:
    """
    Dodaje kolumnę 'dist_to_nearest_school' [km] do DataFrame gmin.

    Parameters
    ----------
    municipalities : pd.DataFrame
    existing_schools : np.ndarray, shape (K, 2)

    Returns
    -------
    pd.DataFrame z dodatkową kolumną.
    """
    df = municipalities.copy()
    if len(existing_schools) == 0:
        df["dist_to_nearest_school"] = 999.0
        return df

    muni_coords = df[["x", "y"]].values
    dist_matrix = cdist(muni_coords, existing_schools)
    df["dist_to_nearest_school"] = np.round(dist_matrix.min(axis=1), 3)
    return df
