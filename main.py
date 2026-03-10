"""
main.py — Główny skrypt projektu WOA: lokalizacja placówki oświatowej.

Uruchomienie:
    python main.py

Wyniki:
    output/municipalities.csv   — dane syntetycznych gmin
    output/woa_results.csv      — optymalna lokalizacja i wyniki WOA
    output/feature_maps.png     — mapy zmiennych wejściowych
    output/fitness_landscape.png — mapa wskaźnika potrzeby + trajektoria WOA
    output/convergence.png      — krzywa zbieżności
    output/criteria_analysis.png — analiza kryteriów dla optymalnej lokalizacji
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Upewnij się, że katalog projektu jest w ścieżce importów
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    AREA_SIZE, SCHOOL_TYPE, WOA_PARAMS, WEIGHTS, DATA_PARAMS, VISUALIZATION,
)
from src.data_generator import generate_municipality_data, add_distance_to_nearest_school
from src.problem import SchoolPlacementProblem
from src.woa import WhaleOptimizationAlgorithm
from src.visualization import (
    plot_feature_maps,
    plot_fitness_landscape,
    plot_convergence,
    plot_criteria_analysis,
)


def _sep(char: str = "=", width: int = 64) -> str:
    return char * width


def main() -> None:
    print(_sep())
    print("  WOA — System wspomagania decyzji o lokalizacji")
    school_label = SchoolPlacementProblem.SCHOOL_TYPE_LABELS.get(SCHOOL_TYPE, SCHOOL_TYPE)
    print(f"  Typ placówki: {school_label}")
    print(_sep())

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # ------------------------------------------------------------------ #
    # KROK 1: Generowanie danych syntetycznych                            #
    # ------------------------------------------------------------------ #
    print("\n[1/4] Generowanie danych syntetycznych …")
    municipalities, existing_schools = generate_municipality_data(
        n_municipalities=DATA_PARAMS["n_municipalities"],
        n_existing_schools=DATA_PARAMS["n_existing_schools"],
        area_size=AREA_SIZE,
        seed=DATA_PARAMS["seed"],
    )
    municipalities = add_distance_to_nearest_school(municipalities, existing_schools)
    municipalities.to_csv(output_dir / "municipalities.csv", index=False)

    print(f"  Gminy:              {len(municipalities)}")
    print(f"  Istniejące szkoły:  {len(existing_schools)}")
    print(f"  Zapisano → output/municipalities.csv")
    print()
    print("  Statystyki danych:")
    summary_cols = [
        "student_count", "school_occupancy", "connectivity_index",
        "exam_score", "fertility_rate", "dist_to_nearest_school",
    ]
    print(municipalities[summary_cols].describe().round(2).to_string(index=True))

    # ------------------------------------------------------------------ #
    # KROK 2: Konfiguracja problemu optymalizacyjnego                     #
    # ------------------------------------------------------------------ #
    print(f"\n[2/4] Konfiguracja problemu ({school_label}) …")
    problem = SchoolPlacementProblem(
        municipalities_data=municipalities,
        existing_schools=existing_schools,
        school_type=SCHOOL_TYPE,
        weights=WEIGHTS,
    )

    lb = [0.0, 0.0]
    ub = [AREA_SIZE, AREA_SIZE]
    print(f"  Przestrzeń poszukiwań: {lb} — {ub} [km]")
    print("  Wagi kryteriów:")
    for k, v in WEIGHTS.items():
        print(f"    {k:<20s}: {v:.2f}")

    # ------------------------------------------------------------------ #
    # KROK 3: Optymalizacja WOA                                           #
    # ------------------------------------------------------------------ #
    print(f"\n[3/4] Optymalizacja WOA …")
    print(f"  Agenty: {WOA_PARAMS['n_agents']}  |  Iteracje: {WOA_PARAMS['max_iter']}  |  b={WOA_PARAMS['b']}")
    print(_sep("-"))

    woa = WhaleOptimizationAlgorithm(
        fitness_func=problem,
        lb=lb,
        ub=ub,
        n_agents=WOA_PARAMS["n_agents"],
        max_iter=WOA_PARAMS["max_iter"],
        b=WOA_PARAMS["b"],
        seed=WOA_PARAMS.get("seed"),
    )

    best_pos, best_score = woa.optimize(verbose=True)

    print(_sep("-"))
    print(f"\n  ★ Optymalna lokalizacja:  X = {best_pos[0]:.3f} km,  Y = {best_pos[1]:.3f} km")
    print(f"  ★ Wskaźnik potrzeby:      {best_score:.6f}")

    # Najbliższa gmina
    from scipy.spatial.distance import cdist as _cdist
    muni_coords = municipalities[["x", "y"]].values
    dists = _cdist([best_pos], muni_coords)[0]
    nearest = municipalities.iloc[int(np.argmin(dists))]
    print(f"\n  Najbliższa gmina: {nearest['municipality_id']}  "
          f"(odl. {dists.min():.2f} km)")

    # Szczegółowa analiza kryteriów
    brkdwn = problem.breakdown(best_pos)
    print("\n  Rozkład składowych dla optymalnej lokalizacji:")
    for k in brkdwn["raw_scores"]:
        rs = brkdwn["raw_scores"][k]
        ws = brkdwn["weighted_scores"][k]
        print(f"    {k:<20s}  wynik={rs:.4f}  ważony={ws:.4f}")

    # Zapis wyników
    results_df = pd.DataFrame([{
        "school_type":          SCHOOL_TYPE,
        "school_type_label":    school_label,
        "optimal_x_km":         round(float(best_pos[0]), 4),
        "optimal_y_km":         round(float(best_pos[1]), 4),
        "need_score":           round(float(best_score), 6),
        "nearest_municipality": nearest["municipality_id"],
        "dist_to_nearest_muni_km": round(float(dists.min()), 3),
        "n_agents":             WOA_PARAMS["n_agents"],
        "n_iterations":         WOA_PARAMS["max_iter"],
        **{f"w_{k}": v for k, v in WEIGHTS.items()},
    }])
    results_df.to_csv(output_dir / "woa_results.csv", index=False)
    print(f"\n  Wyniki zapisano → output/woa_results.csv")

    # ------------------------------------------------------------------ #
    # KROK 4: Wizualizacje                                                #
    # ------------------------------------------------------------------ #
    if not VISUALIZATION["enabled"]:
        print("\n[4/4] Wizualizacja wyłączona w config.py.")
    else:
        import matplotlib.pyplot as plt

        save = VISUALIZATION.get("save_figures", True)
        show = VISUALIZATION.get("show_plots", True)
        res  = VISUALIZATION.get("landscape_resolution", 40)

        print(f"\n[4/4] Generowanie wizualizacji (rozdzielczość siatki: {res}×{res}) …")

        print("  - Mapy zmiennych wejściowych …")
        fig1 = plot_feature_maps(
            municipalities, existing_schools,
            save_path=str(output_dir / "feature_maps.png") if save else None,
        )

        print("  - Mapa wskaźnika potrzeby + trajektoria WOA …")
        fig2 = plot_fitness_landscape(
            problem=problem,
            bounds=(lb, ub),
            resolution=res,
            best_position=best_pos,
            history=woa.history,
            municipalities=municipalities,
            existing_schools=existing_schools,
            title=f"WOA — Optymalna lokalizacja: {school_label}",
            save_path=str(output_dir / "fitness_landscape.png") if save else None,
        )

        print("  - Krzywa zbieżności …")
        fig3 = plot_convergence(
            woa.convergence_curve,
            save_path=str(output_dir / "convergence.png") if save else None,
        )

        print("  - Analiza kryteriów …")
        fig4 = plot_criteria_analysis(
            problem, best_pos,
            save_path=str(output_dir / "criteria_analysis.png") if save else None,
        )

        if save:
            print(f"\n  Wykresy zapisano w katalogu: output/")

        if show:
            plt.show()
        else:
            plt.close("all")

    print("\n" + _sep())
    print("  Optymalizacja zakończona pomyślnie.")
    print(_sep())


if __name__ == "__main__":
    main()
