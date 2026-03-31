"""
PRZYKŁAD: Jak użyć danych gminy w algorytmie WOA

Pokazuje:
1. Załadowanie danych i geometrii gminy
2. Stworzenie funkcji fitness, która ma dostęp do danych gminy
3. Uruchomienie WOA z dostępem do danych gminy dla każdej pozycji
"""

from pathlib import Path
import numpy as np
from shapely.geometry import Point
from scipy.spatial.distance import cdist

# Importuj z load_shape
from load_shape import (
    load_voivodeship_geometry, 
    load_gminy_data,
    load_gminy_geometries,
    load_school_rows,
    filter_points_inside_polygon,
    GminaDataAccessor,
    GEOJSON_PATH, 
    POWIATY_PATH, 
    GMINY_READY_PATH,
    SCHOOLS_PATH,
    TARGET_VOIVODESHIP
)

# Importuj z load_egzaminy
from load_egzaminy import load_egzaminy_data, EgzaminyDataAccessor

# Importuj WOA
from src.woa import WhaleOptimizationAlgorithm


def create_fitness_func_with_gminy_data(gmina_accessor: GminaDataAccessor, egzaminy_accessor: EgzaminyDataAccessor, school_rows: list = None):
    """
    Fabryka do tworzenia funkcji fitness z dostępem do WSZYSTKICH danych.
    
    Dostępne dane:
    1. Demograficzne (gmina_data): suma_U19, populacja, gestosc, przystanki, wydatki, powierzchnia
    2. Edukacyjne (egzaminy_data): srednia_wynikow, liczba_zdajacych, nierownos, szczegóły po przedmiotach
    
    Parameter:
    - gmina_accessor: dostęp do danych demograficznych
    - egzaminy_accessor: dostęp do danych edukacyjnych
    - school_rows: lista istniejących szkół
    
    Returns:
        Funkcja fitness_func(position) -> float
    """
    
    # Zlicz szkoły w każdej gminie
    schools_per_gmina = {}
    if school_rows:
        for school in school_rows:
            x, y = school["_x"], school["_y"]
            gmina_info = gmina_accessor.get_data_for_position(x, y)
            if gmina_info:
                gmina_name = gmina_info.get("gmina", gmina_info.get("name"))
                schools_per_gmina[gmina_name] = schools_per_gmina.get(gmina_name, 0) + 1

    # Przygotuj punkty istniejacych szkol do szybkiego liczenia odleglosci
    if school_rows:
        school_points = np.array(
            [[s["_x"], s["_y"]] for s in school_rows if "_x" in s and "_y" in s],
            dtype=float,
        )
    else:
        school_points = np.empty((0, 2), dtype=float)
    
    def fitness_func(position: np.ndarray) -> float:
        x, y = position[0], position[1]
        

        gmina_data = gmina_accessor.get_data_for_position(x, y)
        if gmina_data is None or gmina_data.get("data_not_found"):
            return 0.0
        
        if school_points.shape[0] > 0:
            dxy = school_points - np.array([x, y], dtype=float)
            min_dist_to_school = float(np.sqrt(np.min(np.sum(dxy * dxy, axis=1))))
        else:
            min_dist_to_school = 0.0

        suma_u19 = gmina_data.get("suma_U19", 0)
        przystanki = gmina_data.get("przystanki", 0)
        
        # Gładkie skalowanie bez twardego obcinania redukuje duże płaskie plateau funkcji celu.
        U19_SCALE = 4500.0
        PRZYSTANKI_SCALE = 80.0
        DIST_SCALE = 0.045

        # Wartości rosną do 1 asymptotycznie, ale nadal różnicują „dobre” obszary.
        norm_u19 = 1.0 - np.exp(-float(suma_u19) / U19_SCALE)
        norm_przystanki = 1.0 - np.exp(-float(przystanki) / PRZYSTANKI_SCALE)
        norm_dist = 1.0 - np.exp(-float(min_dist_to_school) / DIST_SCALE)
    
        WAGA_DYSTANS = 0.60
        WAGA_DZIECI = 0.20           
        WAGA_KOMUNIKACJA = 0.20     
        
        score = (
            (norm_dist * WAGA_DYSTANS) +
            (norm_u19 * WAGA_DZIECI) + 
            (norm_przystanki * WAGA_KOMUNIKACJA)
        )
        
        return float(score)
    
    return fitness_func


def main():
    print("=" * 70)
    print("ALGORYTM WOA Z DOSTĘPEM DO DANYCH GMINY + DYSTANS OD SZKÓŁ")
    print("=" * 70)
    
    # === KROK 1: Załaduj geometrię województwa ===
    print("\n[1/7] Wczytywanie geometrii województwa...")
    geom = load_voivodeship_geometry(GEOJSON_PATH, TARGET_VOIVODESHIP)
    print(f"✓ Załadowano: {TARGET_VOIVODESHIP}")
    
    # === KROK 2: Załaduj istniejące szkoły ===
    print("[2/7] Wczytywanie istniejących szkół...")
    all_school_rows = load_school_rows(SCHOOLS_PATH)
    school_rows_in_region, outside_count = filter_points_inside_polygon(all_school_rows, geom)
    print(f"✓ Załadowano {len(school_rows_in_region)} szkół w regionie")
    
    # === KROK 3: Załaduj dane gminy ===
    print("[3/7] Wczytywanie danych gminy...")
    gminy_data = load_gminy_data(GMINY_READY_PATH)
    print(f"✓ Załadowano {len(gminy_data)} rekordów gminy")
    
    # === KROK 4: Załaduj geometrie gminy ===
    print("[4/7] Wczytywanie geometrii gminy...")
    gminy_geoms = load_gminy_geometries(POWIATY_PATH, geom)
    print(f"✓ Załadowano {len(gminy_geoms)} geometrii gminy")
    
    # === KROK 5: Utwórz accessor ===
    print("[5/8] Tworzenie accessor'a danych demograficznych...")
    gmina_accessor = GminaDataAccessor(gminy_data, gminy_geoms)
    print("✓ Accessor demograficzny gotowy")
    
    # === KROK 6: Załaduj dane edukacyjne (E8) ===
    print("[6/8] Wczytywanie danych edukacyjnych (E8 - gminy)...")
    from pathlib import Path
    DATA_DIR = Path(__file__).resolve().parent / "DATA"
    egzamini_path = DATA_DIR / "E8 - gminy (aktualizacja 07.2025).csv"
    egzaminy_data = load_egzaminy_data(egzamini_path)
    print(f"✓ Załadowano {len(egzaminy_data)} rekordów edukacyjnych")
    
    # === KROK 7: Utwórz accessor do danych edukacyjnych ===
    print("[7/8] Tworzenie accessor'a danych edukacyjnych...")
    egzaminy_accessor = EgzaminyDataAccessor(egzaminy_data)
    print("✓ Accessor edukacyjny gotowy")
    
    # === KROK 8: Stwórz funkcję fitness ===
    print("[8/8] Tworzenie funkcji fitness...")
    fitness_func = create_fitness_func_with_gminy_data(gmina_accessor, egzaminy_accessor, school_rows_in_region)
    print("✓ Funkcja fitness gotowa (z dostępem do WSZYSTKICH danych)\n")
    
    # Pobierz granice bounding box
    bounds = geom.bounds  # (minx, miny, maxx, maxy)
    lb = [bounds[0], bounds[1]]  # Lower bound
    ub = [bounds[2], bounds[3]]  # Upper bound
    
    # Utwórz i uruchom WOA
    woa = WhaleOptimizationAlgorithm(
        fitness_func=fitness_func,
        lb=lb,
        ub=ub,
        mask_polygon=geom,
        n_agents=40,          # Większa populacja = lepsze pokrycie przestrzeni
        max_iter=120,         # Więcej iteracji na eksplorację i dopracowanie
        b=1.0,
        forced_exploration_prob=0.25,
        a_decay_power=2.0,
        seed=42
    )
    
    best_position, best_score = woa.optimize(verbose=True)
    
    # === WYNIKI ===
    print("\n" + "=" * 70)
    print("WYNIKI OPTYMALIZACJI")
    print("=" * 70)
    print(f"Najlepsza pozycja (x, y): ({best_position[0]:.4f}, {best_position[1]:.4f})")
    print(f"Wynik fitness: {best_score:.6f}")
    
    # Pobierz dane gminy dla najlepszej pozycji
    best_gmina_data = gmina_accessor.get_data_for_position(best_position[0], best_position[1])
    if best_gmina_data and not best_gmina_data.get("data_not_found"):
        print(f"\nGmina optymalna: {best_gmina_data.get('gmina', 'N/A')}")
        print(f"  - Powiat: {best_gmina_data.get('powiat', 'N/A')}")
        print(f"  - Populacja: {best_gmina_data.get('populacja', 'N/A')}")
        print(f"  - Suma U19: {best_gmina_data.get('suma_U19', 'N/A')}")
        print(f"  - Przystanki: {best_gmina_data.get('przystanki', 'N/A')}")
        print(f"  - Gęstość: {best_gmina_data.get('gestosc', 'N/A')} osób/km²")
        
        # Dystans do najbliższej szkoły
        best_point = Point(best_position[0], best_position[1])
        min_dist_to_school = min([
            np.sqrt((best_position[0] - s["_x"]) ** 2 + (best_position[1] - s["_y"]) ** 2)
            for s in school_rows_in_region
        ]) if school_rows_in_region else -1
        
        print(f"  - Dystans do najbliższej szkoły: {min_dist_to_school:.3f}°")
    
    print("\nOptymalizacja zakonczona")
    
    return woa, best_position, best_score


if __name__ == "__main__":
    woa, best_pos, best_score = main()
