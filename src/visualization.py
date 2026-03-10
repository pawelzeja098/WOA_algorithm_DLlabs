"""
src/visualization.py — Moduł wizualizacji wyników optymalizacji WOA.

Zawiera cztery wykresy:
  1. plot_feature_maps      — mapy 6 zmiennych wejściowych
  2. plot_fitness_landscape — mapa wskaźnika potrzeby + trajektoria WOA
  3. plot_convergence       — krzywa zbieżności WOA
  4. plot_criteria_analysis — słupkowy + radarowy rozkład wyników kryteriów
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
import pandas as pd
from typing import Sequence

# Własna mapa kolorów: zielony (niska potrzeba) → żółty → czerwony (wysoka potrzeba)
_NEED_CMAP = LinearSegmentedColormap.from_list(
    "need", ["#2ecc71", "#f1c40f", "#e67e22", "#e74c3c"]
)


# ---------------------------------------------------------------------------
# 1. Mapy zmiennych wejściowych
# ---------------------------------------------------------------------------

def plot_feature_maps(
    municipalities: pd.DataFrame,
    existing_schools: np.ndarray,
    save_path: str | None = None,
) -> plt.Figure:
    """
    Rysuje 6 podwykresów — po jednym dla każdej zmiennej wejściowej.
    """
    feature_cfg = [
        ("student_count",       "Liczba uczniów (kohorta roczna)",  "Blues"),
        ("school_occupancy",    "Obłożenie szkół [%]",               "Reds"),
        ("connectivity_index",  "Wskaźnik skomunikowania [0–1]",     "Greens"),
        ("exam_score",          "Wyniki egzaminów [0–100]",          "Purples"),
        ("fertility_rate",      "Współczynnik dzietności",           "YlOrBr"),
        ("dist_to_nearest_school", "Odległość do szkoły [km]",       "OrRd"),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(17, 11))
    axes = axes.flatten()

    for ax, (feat, title, cmap) in zip(axes, feature_cfg):
        if feat not in municipalities.columns:
            ax.set_visible(False)
            continue

        sc = ax.scatter(
            municipalities["x"], municipalities["y"],
            c=municipalities[feat], cmap=cmap,
            s=90, edgecolors="gray", linewidths=0.4, alpha=0.88,
            zorder=3,
        )
        if len(existing_schools) > 0:
            ax.scatter(
                existing_schools[:, 0], existing_schools[:, 1],
                c="black", s=55, marker="^", alpha=0.85, zorder=5,
                label="Istniejące szkoły",
            )

        cb = plt.colorbar(sc, ax=ax, shrink=0.82, pad=0.02)
        cb.ax.tick_params(labelsize=8)
        ax.set_title(title, fontsize=10, fontweight="bold", pad=6)
        ax.set_xlabel("X [km]", fontsize=8)
        ax.set_ylabel("Y [km]", fontsize=8)
        ax.grid(True, alpha=0.2, linewidth=0.5)
        ax.tick_params(labelsize=8)

    axes[0].legend(fontsize=8, loc="upper right")
    fig.suptitle(
        "Zmienne wejściowe modelu  (▲ = istniejące szkoły)",
        fontsize=14, fontweight="bold", y=1.01,
    )
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


# ---------------------------------------------------------------------------
# 2. Mapa wskaźnika potrzeby + trajektoria agentów WOA
# ---------------------------------------------------------------------------

def plot_fitness_landscape(
    problem,
    bounds: tuple[Sequence[float], Sequence[float]],
    resolution: int = 40,
    best_position: np.ndarray | None = None,
    history: list[np.ndarray] | None = None,
    municipalities: pd.DataFrame | None = None,
    existing_schools: np.ndarray | None = None,
    title: str = "WOA — Optymalizacja lokalizacji placówki oświatowej",
    save_path: str | None = None,
) -> plt.Figure:
    """
    Lewy panel  — mapa przestrzenna wskaźnika potrzeby + optymalna lokalizacja.
    Prawy panel — te same dane z trajektorią agentów WOA (ostatnie 5 iteracji).
    """
    lb, ub = bounds
    xs = np.linspace(lb[0], ub[0], resolution)
    ys = np.linspace(lb[1], ub[1], resolution)
    X, Y = np.meshgrid(xs, ys)
    Z = np.vectorize(lambda xi, yi: problem.evaluate([xi, yi]))(X, Y)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # ---------- panel lewy: mapa potrzeby ----------
    cf1 = ax1.contourf(X, Y, Z, levels=22, cmap=_NEED_CMAP, alpha=0.87)
    ax1.contour(X, Y, Z, levels=10, colors="white", alpha=0.18, linewidths=0.5)
    cb1 = plt.colorbar(cf1, ax=ax1, label="Wskaźnik potrzeby [0–1]", shrink=0.9)
    cb1.ax.tick_params(labelsize=9)

    if municipalities is not None:
        ax1.scatter(
            municipalities["x"], municipalities["y"],
            c="white", s=28, alpha=0.65, edgecolors="#555555", linewidths=0.4,
            label="Gminy", zorder=3,
        )
    if existing_schools is not None and len(existing_schools) > 0:
        ax1.scatter(
            existing_schools[:, 0], existing_schools[:, 1],
            c="#3498db", s=80, marker="^", edgecolors="#1a5276", linewidths=0.8,
            label="Istn. szkoły", zorder=5,
        )
    if best_position is not None:
        ax1.scatter(
            best_position[0], best_position[1],
            c="gold", s=320, marker="*", edgecolors="black", linewidths=1.6,
            label=f"Optymalna lok. WOA\n({best_position[0]:.1f}, {best_position[1]:.1f})",
            zorder=7,
        )

    ax1.set_xlim(lb[0], ub[0])
    ax1.set_ylim(lb[1], ub[1])
    ax1.set_xlabel("Współrzędna X [km]", fontsize=10)
    ax1.set_ylabel("Współrzędna Y [km]", fontsize=10)
    ax1.set_title("Mapa wskaźnika potrzeby", fontsize=11, fontweight="bold")
    ax1.legend(loc="upper right", fontsize=8, framealpha=0.85)

    # ---------- panel prawy: trajektoria agentów ----------
    cf2 = ax2.contourf(X, Y, Z, levels=22, cmap=_NEED_CMAP, alpha=0.87)
    plt.colorbar(cf2, ax=ax2, label="Wskaźnik potrzeby [0–1]", shrink=0.9).ax.tick_params(labelsize=9)

    if history:
        n_show = min(6, len(history))
        shown = history[:: max(1, len(history) // n_show)][-n_show:]
        alphas = np.linspace(0.12, 0.75, len(shown))
        sizes = np.linspace(8, 45, len(shown))
        for snap, alpha, sz in zip(shown, alphas, sizes):
            ax2.scatter(snap[:, 0], snap[:, 1], c="cyan", s=sz, alpha=alpha, zorder=3)

    if existing_schools is not None and len(existing_schools) > 0:
        ax2.scatter(
            existing_schools[:, 0], existing_schools[:, 1],
            c="#3498db", s=80, marker="^", edgecolors="#1a5276", linewidths=0.8,
            label="Istn. szkoły", zorder=5,
        )
    if best_position is not None:
        ax2.scatter(
            best_position[0], best_position[1],
            c="gold", s=320, marker="*", edgecolors="black", linewidths=1.6,
            label="Optymalna lok. WOA", zorder=7,
        )

    ax2.set_xlim(lb[0], ub[0])
    ax2.set_ylim(lb[1], ub[1])
    ax2.set_xlabel("Współrzędna X [km]", fontsize=10)
    ax2.set_ylabel("Współrzędna Y [km]", fontsize=10)
    ax2.set_title("Trajektoria agentów WOA", fontsize=11, fontweight="bold")
    ax2.legend(loc="upper right", fontsize=8, framealpha=0.85)

    fig.suptitle(title, fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


# ---------------------------------------------------------------------------
# 3. Krzywa zbieżności
# ---------------------------------------------------------------------------

def plot_convergence(
    convergence_curve: list[float],
    title: str = "Krzywa zbieżności algorytmu WOA",
    save_path: str | None = None,
) -> plt.Figure:
    """Wykres najlepszego wynik WOA w kolejnych iteracjach."""
    iters = np.arange(1, len(convergence_curve) + 1)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(iters, convergence_curve, color="#2980b9", linewidth=2.2, zorder=3)
    ax.fill_between(iters, convergence_curve, alpha=0.15, color="#2980b9")
    ax.scatter(
        [len(convergence_curve)], [convergence_curve[-1]],
        color="gold", s=100, zorder=4, edgecolors="black", linewidths=1.2,
        label=f"Ostateczny wynik: {convergence_curve[-1]:.5f}",
    )
    ax.set_xlabel("Iteracja", fontsize=11)
    ax.set_ylabel("Najlepszy wskaźnik potrzeby", fontsize=11)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlim(1, len(convergence_curve))
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.legend(fontsize=10)
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


# ---------------------------------------------------------------------------
# 4. Analiza kryteriów dla optymalnej lokalizacji
# ---------------------------------------------------------------------------

def plot_criteria_analysis(
    problem,
    best_position: np.ndarray,
    save_path: str | None = None,
) -> plt.Figure:
    """
    Lewy panel  — poziomy wykres słupkowy wyników cząstkowych.
    Prawy panel — wykres radarowy ważonych składowych.
    """
    breakdown = problem.breakdown(best_position)
    raw   = breakdown["raw_scores"]
    wgt   = breakdown["weighted_scores"]

    labels_long = [
        "Odległość od\nnajbliższej szkoły",
        "Liczba potencjalnych\nuczniów",
        "Obłożenie\nnajbliższych szkół",
        "Skomunikowanie\n(odwrócone)",
        "Wyniki egzaminów\n(odwrócone)",
        "Współczynnik\ndzietności",
    ]
    labels_short = ["Odległość", "Uczniowie", "Obłożenie", "Komunikacja", "Egzaminy", "Dzietność"]
    keys   = list(raw.keys())
    scores = [raw[k] for k in keys]
    wscores = [wgt[k] for k in keys]

    fig = plt.figure(figsize=(15, 6))
    gs  = gridspec.GridSpec(1, 2, figure=fig, wspace=0.38)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], projection="polar")

    # --- Słupkowy ---
    bar_colors = ["#e74c3c" if s > 0.6 else "#f39c12" if s > 0.4 else "#27ae60" for s in scores]
    bars = ax1.barh(labels_long, scores, color=bar_colors, edgecolor="white", height=0.58)
    ax1.set_xlim(0.0, 1.05)
    ax1.set_xlabel("Wynik składowy [0–1]", fontsize=10)
    ax1.set_title("Wyniki cząstkowe kryteriów\n(optymalna lokalizacja)", fontsize=11, fontweight="bold")
    ax1.axvline(0.5, color="gray", linestyle="--", alpha=0.45, linewidth=1)
    for bar, val, wval in zip(bars, scores, wscores):
        ax1.text(
            val + 0.02, bar.get_y() + bar.get_height() / 2,
            f"{val:.2f}  (w={wval:.3f})",
            va="center", fontsize=8.5, color="#2c3e50",
        )
    ax1.grid(True, axis="x", alpha=0.25, linestyle="--")
    ax1.tick_params(axis="y", labelsize=9)

    # --- Radarowy ---
    n = len(keys)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    vals_closed = wscores + [wscores[0]]
    angles_closed = np.append(angles, angles[0])

    ax2.plot(angles_closed, vals_closed, "o-", linewidth=2, color="#2980b9")
    ax2.fill(angles_closed, vals_closed, alpha=0.22, color="#2980b9")
    ax2.set_xticks(angles)
    ax2.set_xticklabels(labels_short, size=9)
    ax2.set_ylim(0, max(problem.weights.values()) * 1.15)
    ax2.set_title("Ważone składowe kryteriów\n(wykres radarowy)", fontsize=11, fontweight="bold", pad=22)
    ax2.grid(True, alpha=0.35)

    fig.suptitle(
        f"Analiza kryteriów — optymalna lokalizacja  "
        f"(X={best_position[0]:.2f} km, Y={best_position[1]:.2f} km)  |  "
        f"Łączny wskaźnik: {breakdown['total']:.4f}",
        fontsize=12, fontweight="bold", y=1.02,
    )
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig
