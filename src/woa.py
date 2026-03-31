"""
Algorytm naśladuje zachowania łowieckie humbaków :
  - Atak bąbelkowy ze zwężającym się okrążaniem   
  - Atak bąbelkowy ze spiralą logarytmiczną     
  - Losowe przeszukiwanie                          
"""

from __future__ import annotations

import numpy as np
from typing import Callable, Sequence
from shapely.geometry import Point, Polygon, MultiPolygon


class WhaleOptimizationAlgorithm:
    """
    Algorytm wielorybiej optymalizacji (WOA) — maksymalizacja funkcji celu.

    Parameters
    ----------
    fitness_func : callable
        Funkcja celu f(position) → float.  Wyższy wynik = lepsze rozwiązanie.
    lb : Sequence[float]
        Dolne granice przestrzeni poszukiwań dla każdego wymiaru.
    ub : Sequence[float]
        Górne granice przestrzeni poszukiwań dla każdego wymiaru.
    n_agents : int
        Liczba wielorybów (rozmiar populacji).
    max_iter : int
        Maksymalna liczba iteracji.
    b : float
        Stała kształtu spirali logarytmicznej.
    seed : int | None
        Ziarno generatora liczb pseudolosowych (None = losowy).
    """

    def __init__(
        self,
        fitness_func: Callable[[np.ndarray], float],
        lb: Sequence[float],
        ub: Sequence[float],
        mask_polygon: Polygon | MultiPolygon | None = None,
        n_agents: int = 30,
        max_iter: int = 100,
        b: float = 1.0,
        forced_exploration_prob: float = 0.15,
        a_decay_power: float = 2.0,
        seed: int | None = None,
    ) -> None:
        self.fitness_func = fitness_func
        self.lb = np.array(lb, dtype=float)
        self.ub = np.array(ub, dtype=float)
        self.mask_polygon = mask_polygon #Kształt obszaru poszukiwań - granice województwa
        self.n_agents = n_agents
        self.max_iter = max_iter
        self.b = b
        self.forced_exploration_prob = float(np.clip(forced_exploration_prob, 0.0, 1.0))
        self.a_decay_power = max(0.1, float(a_decay_power))
        self.dim = len(lb)
        self._rng = np.random.default_rng(seed)

        # Wyniki optymalizacji (wypełniane przez optimize())
        self.best_position: np.ndarray | None = None
        self.best_score: float = -np.inf
        self.convergence_curve: list[float] = []
        self.history: list[np.ndarray] = []  # pozycje agentów w każdej iteracji

    # ------------------------------------------------------------------
    # Metody prywatne
    # ------------------------------------------------------------------

    def _init_population(self) -> np.ndarray:
        """Inicjalizacja: losuje punkty tak długo, aż znajdą się wewnątrz poligonu."""
        positions = np.zeros((self.n_agents, self.dim))
        
        for i in range(self.n_agents):
            valid = False
            while not valid:
                p = self._rng.uniform(self.lb, self.ub)
                # Jeśli mamy maskę, sprawdź czy punkt jest wewnątrz
                if self.mask_polygon is not None:
                    if self.mask_polygon.covers(Point(p[0], p[1])):
                        positions[i] = p
                        valid = True
                else:
                    positions[i] = p
                    valid = True
        return positions

    def _random_point_in_mask(self, fallback: np.ndarray) -> np.ndarray:
        """Losuje punkt wewnątrz maski; po kilku próbach zwraca fallback."""
        if self.mask_polygon is None:
            return self._rng.uniform(self.lb, self.ub)

        for _ in range(50):
            candidate = self._rng.uniform(self.lb, self.ub)
            if self.mask_polygon.covers(Point(candidate[0], candidate[1])):
                return candidate
        return fallback

    def _clip(self, positions: np.ndarray, old_positions: np.ndarray) -> np.ndarray:
        """
        Jeśli wieloryb wypłynie poza województwo,
        próbujemy losowo wrócić do wnętrza maski zamiast zamrażać pozycję.
        """
        new_positions = np.clip(positions, self.lb, self.ub)
        
        if self.mask_polygon is not None:
            for i in range(len(new_positions)):
                point = Point(new_positions[i][0], new_positions[i][1])
                if not self.mask_polygon.covers(point):
                    # Zamiast cofać do starej pozycji (stagnacja), losujemy punkt z maski.
                    new_positions[i] = self._random_point_in_mask(old_positions[i])
                    
        return new_positions

    def _evaluate_population(self, positions: np.ndarray) -> np.ndarray:
        """Wyznaczanie wartości funkcji celu dla całej populacji."""
        return np.array([self.fitness_func(p) for p in positions])

    # ------------------------------------------------------------------
    # Główna pętla optymalizacji
    # ------------------------------------------------------------------

    def optimize(self, verbose: bool = True) -> tuple[np.ndarray, float]:
        """
        Uruchamia algorytm WOA.

        Parameters
        ----------
        verbose : bool
            Czy wypisywać postęp co 10 iteracji.

        Returns
        -------
        best_position : np.ndarray
            Najlepsza znaleziona pozycja (optymalna lokalizacja szkoły).
        best_score : float
            Wartość funkcji celu w najlepszej pozycji.
        """
        positions = self._init_population()
        scores = self._evaluate_population(positions)

        best_idx = int(np.argmax(scores))
        self.best_position = positions[best_idx].copy()
        self.best_score = float(scores[best_idx])

        if verbose:
            print(f"  Inicjalizacja — najlepszy wynik: {self.best_score:.6f}")

        for t in range(self.max_iter):
            # Liniowy spadek parametru sterującego eksploracja/eksploatacja
            progress = t / max(1, self.max_iter - 1)
            a = 2.0 * (1.0 - progress ** self.a_decay_power)

            new_positions = positions.copy()

            for i in range(self.n_agents):
                r1 = self._rng.random()
                r2 = self._rng.random()
                A = 2.0 * a * r1 - a   # współczynnik ruchu
                C = 2.0 * r2           # współczynnik odległości
                p = self._rng.random()
                l = self._rng.uniform(-1.0, 1.0)  # parametr spirali
                force_explore = self._rng.random() < self.forced_exploration_prob * (1.0 - progress)

                if force_explore:
                    rand_idx = int(self._rng.integers(0, self.n_agents - 1))
                    if rand_idx >= i:
                        rand_idx += 1
                    X_rand = positions[rand_idx]
                    D = np.abs(C * X_rand - positions[i])
                    new_positions[i] = X_rand - A * D
                elif p < 0.5:
                    if abs(A) < 1.0:
                        # ---- Eksploatacja: zwężające się okrążanie ----
                        D = np.abs(C * self.best_position - positions[i])
                        new_positions[i] = self.best_position - A * D
                    else:
                        # ---- Eksploracja: losowe przeszukiwanie ----
                        rand_idx = int(self._rng.integers(0, self.n_agents - 1))
                        if rand_idx >= i:
                            rand_idx += 1
                        X_rand = positions[rand_idx]
                        D = np.abs(C * X_rand - positions[i])
                        new_positions[i] = X_rand - A * D
                else:
                    # ---- Eksploatacja: spirala logarytmiczna ----
                    D_star = np.abs(self.best_position - positions[i])
                    new_positions[i] = (
                        D_star * np.exp(self.b * l) * np.cos(2.0 * np.pi * l)
                        + self.best_position
                    )

            positions = self._clip(new_positions, positions)
            scores = self._evaluate_population(positions)

            # Aktualizacja najlepszego rozwiązania
            iter_best_idx = int(np.argmax(scores))
            iter_best_score = float(scores[iter_best_idx])
            iter_best_position = positions[iter_best_idx]
            if scores[iter_best_idx] > self.best_score:
                self.best_score = float(scores[iter_best_idx])
                self.best_position = positions[iter_best_idx].copy()

            spread = float(np.mean(np.std(positions, axis=0)))

            self.convergence_curve.append(self.best_score)
            self.history.append(positions.copy())

            if verbose:
                print(
                    f"  Iteracja {t + 1:>4}/{self.max_iter} | "
                    f"BestGlobal: {self.best_score:.6f} | "
                    f"BestIter: {iter_best_score:.6f} | "
                    f"Spread: {spread:.4f} | "
                    f"Pozycja globalna: ({self.best_position[0]:.4f}, {self.best_position[1]:.4f}) | "
                    f"Pozycja iteracji: ({iter_best_position[0]:.4f}, {iter_best_position[1]:.4f})"
                )

        return self.best_position, self.best_score
