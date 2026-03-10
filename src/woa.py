"""
src/woa.py — Implementacja algorytmu wielorybiego (Whale Optimization Algorithm)

Źródło:
    Mirjalili, S., & Lewis, A. (2016).
    The Whale Optimization Algorithm.
    Advances in Engineering Software, 95, 51–67.
    https://doi.org/10.1016/j.advengsoft.2016.01.008

Algorytm naśladuje zachowania łowieckie humbaków (Megaptera novaeangliae):
  - Atak bąbelkowy ze zwężającym się okrążaniem   (eksplo­ita­cja)
  - Atak bąbelkowy ze spiralą logarytmiczną        (eksplo­ita­cja)
  - Losowe przeszukiwanie                          (eksplo­ra­cja)
"""

from __future__ import annotations

import numpy as np
from typing import Callable, Sequence


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
        n_agents: int = 30,
        max_iter: int = 100,
        b: float = 1.0,
        seed: int | None = None,
    ) -> None:
        self.fitness_func = fitness_func
        self.lb = np.array(lb, dtype=float)
        self.ub = np.array(ub, dtype=float)
        self.n_agents = n_agents
        self.max_iter = max_iter
        self.b = b
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
        """Losowa inicjalizacja pozycji wielorybów w granicach przestrzeni."""
        return self._rng.uniform(self.lb, self.ub, size=(self.n_agents, self.dim))

    def _clip(self, positions: np.ndarray) -> np.ndarray:
        """Obcinanie pozycji do dozwolonych granic."""
        return np.clip(positions, self.lb, self.ub)

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
            a = 2.0 - 2.0 * t / self.max_iter   # 2 → 0

            new_positions = positions.copy()

            for i in range(self.n_agents):
                r1 = self._rng.random()
                r2 = self._rng.random()
                A = 2.0 * a * r1 - a   # współczynnik ruchu
                C = 2.0 * r2           # współczynnik odległości
                p = self._rng.random()
                l = self._rng.uniform(-1.0, 1.0)  # parametr spirali

                if p < 0.5:
                    if abs(A) < 1.0:
                        # ---- Eksploatacja: zwężające się okrążanie ----
                        D = np.abs(C * self.best_position - positions[i])
                        new_positions[i] = self.best_position - A * D
                    else:
                        # ---- Eksploracja: losowe przeszukiwanie ----
                        rand_idx = self._rng.integers(0, self.n_agents)
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

            positions = self._clip(new_positions)
            scores = self._evaluate_population(positions)

            # Aktualizacja najlepszego rozwiązania
            iter_best_idx = int(np.argmax(scores))
            if scores[iter_best_idx] > self.best_score:
                self.best_score = float(scores[iter_best_idx])
                self.best_position = positions[iter_best_idx].copy()

            self.convergence_curve.append(self.best_score)
            self.history.append(positions.copy())

            if verbose and (t + 1) % 10 == 0:
                print(
                    f"  Iteracja {t + 1:>4}/{self.max_iter} | "
                    f"Wynik: {self.best_score:.6f} | "
                    f"Pozycja: ({self.best_position[0]:.2f}, {self.best_position[1]:.2f})"
                )

        return self.best_position, self.best_score
