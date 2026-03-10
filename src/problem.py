"""
src/problem.py — Definicja problemu optymalizacyjnego dla WOA.

Funkcja celu ocenia, jak bardzo potrzebna jest nowa placówka oświatowa
w danym miejscu (x, y) obszaru geograficznego.

Kryteria (6 zmiennych):
  1. Odległość do najbliższej szkoły       — większa → wyższa potrzeba
  2. Liczba potencjalnych uczniów w gminie — więcej  → wyższa potrzeba
  3. Obłożenie najbliższych szkół          — wyższe  → wyższa potrzeba
  4. Współczynnik skomunikowania gminy     — odwrócony: gorszy → wyższa potrzeba
  5. Wyniki egzaminów                      — odwrócony: gorsze → wyższa potrzeba
  6. Współczynnik dzietności               — wyższy  → wyższa potrzeba

Interpolacja cech w przestrzeni ciągłej:
  Dla danego punktu (x, y) wartości cech interpolowane są z danych
  gminnych metodą ważoną odwrotnością odległości (IDW).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from typing import Sequence


class SchoolPlacementProblem:
    """
    Funkcja celu do optymalizacji lokalizacji placówki oświatowej za pomocą WOA.

    Parameters
    ----------
    municipalities_data : pd.DataFrame
        Dane gmin z kolumnami: x, y, student_count, school_occupancy,
        connectivity_index, exam_score, fertility_rate.
    existing_schools : np.ndarray, shape (K, 2)
        Współrzędne (x, y) istniejących szkół.
    school_type : str
        Typ placówki: 'kindergarten' | 'primary' | 'secondary'.
    weights : dict | None
        Słownik wag dla każdego kryterium. Jeśli None, używane są wagi domyślne.
    max_distance_km : float
        Maksymalna odległość od szkoły traktowana jako „pełna potrzeba" (km).
    n_neighbors : int
        Liczba sąsiednich gmin użytych do interpolacji IDW.
    """

    SCHOOL_TYPE_LABELS = {
        "kindergarten": "Przedszkole",
        "primary": "Szkoła podstawowa",
        "secondary": "Liceum / szkoła średnia",
    }

    DEFAULT_WEIGHTS = {
        "distance":      0.25,
        "students":      0.20,
        "occupancy":     0.20,
        "connectivity":  0.10,
        "exam_results":  0.10,
        "fertility":     0.15,
    }

    def __init__(
        self,
        municipalities_data: pd.DataFrame,
        existing_schools: np.ndarray,
        school_type: str = "primary",
        weights: dict | None = None,
        max_distance_km: float = 50.0,
        n_neighbors: int = 5,
    ) -> None:
        self.data = municipalities_data.reset_index(drop=True)
        self.existing_schools = np.asarray(existing_schools, dtype=float)
        self.school_type = school_type
        self.weights = weights if weights is not None else self.DEFAULT_WEIGHTS.copy()
        self.max_distance_km = max_distance_km
        self.n_neighbors = n_neighbors

        self._muni_coords = self.data[["x", "y"]].values.astype(float)
        self._feature_stats: dict[str, tuple[float, float]] = {}
        self._precompute_normalization()

    # ------------------------------------------------------------------
    # Normalizacja
    # ------------------------------------------------------------------

    def _precompute_normalization(self) -> None:
        for col in ("student_count", "school_occupancy", "connectivity_index",
                    "exam_score", "fertility_rate"):
            lo = float(self.data[col].min())
            hi = float(self.data[col].max())
            self._feature_stats[col] = (lo, hi)

    def _normalize(self, value: float, feature: str) -> float:
        lo, hi = self._feature_stats[feature]
        if hi <= lo:
            return 0.5
        return float(np.clip((value - lo) / (hi - lo), 0.0, 1.0))

    # ------------------------------------------------------------------
    # Interpolacja IDW
    # ------------------------------------------------------------------

    def _idw(self, position: np.ndarray, feature: str) -> float:
        """
        Interpolacja wartości cechy w punkcie 'position'
        metodą ważoną odwrotnością kwadratu odległości (IDW).
        """
        pos = position.reshape(1, 2)
        dists = cdist(pos, self._muni_coords)[0]

        k = min(self.n_neighbors, len(dists))
        nn_idx = np.argsort(dists)[:k]
        nn_dists = dists[nn_idx]

        # Punkt pokrywa się z centrum gminy — zwróć wartość bezpośrednio
        if nn_dists[0] < 1e-9:
            return float(self.data.at[nn_idx[0], feature])

        w = 1.0 / (nn_dists ** 2)
        vals = self.data[feature].values[nn_idx]
        return float(np.dot(w, vals) / w.sum())

    # ------------------------------------------------------------------
    # Składowe oceny
    # ------------------------------------------------------------------

    def _score_distance(self, position: np.ndarray) -> float:
        """Odległość do najbliższej istniejącej szkoły (znormalizowana)."""
        if len(self.existing_schools) == 0:
            return 1.0
        dists = cdist(position.reshape(1, 2), self.existing_schools)[0]
        return float(np.clip(dists.min() / self.max_distance_km, 0.0, 1.0))

    def _score_students(self, position: np.ndarray) -> float:
        val = self._idw(position, "student_count")
        return self._normalize(val, "student_count")

    def _score_occupancy(self, position: np.ndarray) -> float:
        val = self._idw(position, "school_occupancy")
        return self._normalize(val, "school_occupancy")

    def _score_connectivity(self, position: np.ndarray) -> float:
        """Odwrócony wskaźnik skomunikowania — słabsza sieć = wyższa potrzeba."""
        val = self._idw(position, "connectivity_index")
        return 1.0 - self._normalize(val, "connectivity_index")

    def _score_exam(self, position: np.ndarray) -> float:
        """Odwrócone wyniki egzaminów — gorsze wyniki = wyższa potrzeba."""
        val = self._idw(position, "exam_score")
        return 1.0 - self._normalize(val, "exam_score")

    def _score_fertility(self, position: np.ndarray) -> float:
        val = self._idw(position, "fertility_rate")
        return self._normalize(val, "fertility_rate")

    # ------------------------------------------------------------------
    # Publiczna funkcja celu
    # ------------------------------------------------------------------

    def evaluate(self, position: Sequence[float]) -> float:
        """
        Oblicza ważoną sumę wskaźników potrzeby dla lokalizacji (x, y).

        Returns
        -------
        float
            Wynik w zakresie [0, 1].  1 = najwyższa potrzeba budowy szkoły.
        """
        pos = np.asarray(position, dtype=float)

        s_dist  = self._score_distance(pos)
        s_std   = self._score_students(pos)
        s_occ   = self._score_occupancy(pos)
        s_conn  = self._score_connectivity(pos)
        s_exam  = self._score_exam(pos)
        s_fert  = self._score_fertility(pos)

        score = (
            self.weights["distance"]     * s_dist
            + self.weights["students"]   * s_std
            + self.weights["occupancy"]  * s_occ
            + self.weights["connectivity"] * s_conn
            + self.weights["exam_results"] * s_exam
            + self.weights["fertility"]  * s_fert
        )
        return float(score)

    def __call__(self, position: Sequence[float]) -> float:
        return self.evaluate(position)

    # ------------------------------------------------------------------
    # Szczegółowa analiza punktu (do raportowania)
    # ------------------------------------------------------------------

    def breakdown(self, position: Sequence[float]) -> dict:
        """
        Zwraca słownik z indywidualnymi wynikami każdego kryterium
        dla podanej lokalizacji.
        """
        pos = np.asarray(position, dtype=float)
        scores = {
            "distance":     self._score_distance(pos),
            "students":     self._score_students(pos),
            "occupancy":    self._score_occupancy(pos),
            "connectivity": self._score_connectivity(pos),
            "exam_results": self._score_exam(pos),
            "fertility":    self._score_fertility(pos),
        }
        weighted = {k: v * self.weights[k] for k, v in scores.items()}
        return {
            "raw_scores":      scores,
            "weighted_scores": weighted,
            "total":           sum(weighted.values()),
        }
