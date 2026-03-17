import csv
import json
from pathlib import Path
import numpy as np

import matplotlib.pyplot as plt
from shapely.geometry import Point, shape

# --- TWOJE IMPORTY I STAŁE ---
DATA_DIR = Path(__file__).resolve().parent / "DATA"
GEOJSON_PATH = DATA_DIR / "wojewodztwa-min.geojson"
SCHOOLS_PATH = DATA_DIR / "szkoly_final.csv"
# NOWA ŚCIEŻKA DO POWIATÓW
POWIATY_PATH = DATA_DIR / "poland.municipalities.json" 
TARGET_VOIVODESHIP = "małopolskie"

# --- ISTNIEJĄCE FUNKCJE (BEZ ZMIAN) ---

def load_voivodeship_geometry(geojson_path: Path, voivodeship_name: str):
    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for feature in data["features"]:
        name = feature.get("properties", {}).get("nazwa", "")
        if name.lower() == voivodeship_name.lower():
            return shape(feature["geometry"])
    raise ValueError(f"Nie znaleziono województwa: {voivodeship_name}")

def load_school_rows(csv_path: Path):
    rows = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                x, y = float(row["x"]), float(row["y"])
                row["_x"], row["_y"] = x, y
                row["_point"] = Point(x, y)
                rows.append(row)
            except (TypeError, ValueError): continue
    return rows

def filter_points_inside_polygon(rows, polygon):
    inside = [r for r in rows if polygon.covers(r["_point"])]
    return inside, len(rows) - len(inside)

# --- NOWA FUNKCJA DO WCZYTYWANIA POWIATÓW ---

def load_powiaty_in_voivodeship(powiaty_path: Path, voivodeship_geom):
    """Wczytuje powiaty i zwraca tylko te, które leżą w granicach województwa."""
    with open(powiaty_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    powiaty_shapes = []
    for feature in data["features"]:
        poly = shape(feature["geometry"])
        # Sprawdzamy, czy powiat należy do Małopolski 
        # (na podstawie nazwy w properties lub przecięcia geometrii)
        # Używamy intersection, bo powiaty na granicach mogą minimalnie wystawać
        if voivodeship_geom.intersects(poly.centroid): 
            powiaty_shapes.append(poly)
            
    return powiaty_shapes

# --- ZMODYFIKOWANE RYSOWANIE ---

def draw_polygon(ax, geom, color="#1f4e79", fill_color="#9dc3e6", alpha=0.45, linewidth=1.7):
    if geom.geom_type == "MultiPolygon":
        for poly in geom.geoms:
            x, y = poly.exterior.xy
            ax.plot(x, y, color=color, linewidth=linewidth, zorder=2)
            ax.fill(x, y, color=fill_color, alpha=alpha, zorder=1)
    else:
        x, y = geom.exterior.xy
        ax.plot(x, y, color=color, linewidth=linewidth, zorder=2)
        ax.fill(x, y, color=fill_color, alpha=alpha, zorder=1)

def plot_małopolska_with_schools_and_powiaty(geom, school_rows, powiaty_shapes):
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # 1. Rysujemy tło (Województwo)
    draw_polygon(ax, geom)

    # 2. Rysujemy granice powiatów (cieńsze linie, bez wypełnienia)
    for p_geom in powiaty_shapes:
        if p_geom.geom_type == "MultiPolygon":
            for poly in p_geom.geoms:
                x, y = poly.exterior.xy
                ax.plot(x, y, color="#595959", linewidth=0.6, alpha=0.5, zorder=2)
        else:
            x, y = p_geom.exterior.xy
            ax.plot(x, y, color="#595959", linewidth=0.6, alpha=0.5, zorder=2)

    # 3. Szkoły
    xs = [row["_x"] for row in school_rows]
    ys = [row["_y"] for row in school_rows]
    ax.scatter(xs, ys, s=8, alpha=0.6, color="#c00000", label="szkoły", zorder=3)

    ax.set_title("Małopolskie: Powiaty + Istniejące szkoły")
    ax.set_aspect("equal")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend(loc="lower left")
    plt.tight_layout()
    plt.show()

def main():
    # Załaduj dane
    geom = load_voivodeship_geometry(GEOJSON_PATH, TARGET_VOIVODESHIP)
    all_school_rows = load_school_rows(SCHOOLS_PATH)
    school_rows_in_malopolska, outside_count = filter_points_inside_polygon(all_school_rows, geom)
    
    # NOWY KROK: Załaduj powiaty
    print("Filtrowanie powiatów dla województwa...")
    powiaty_in_malopolska = load_powiaty_in_voivodeship(POWIATY_PATH, geom)

    print(f"Załadowano geometrię: {TARGET_VOIVODESHIP}")
    print(f"Liczba powiatów w Małopolsce: {len(powiaty_in_malopolska)}")
    print(f"Szkoły wewnątrz granic: {len(school_rows_in_malopolska)}")

    # Wyświetl mapę
    plot_małopolska_with_schools_and_powiaty(geom, school_rows_in_malopolska, powiaty_in_malopolska)

if __name__ == "__main__":
    main()