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
GMINY_READY_PATH = DATA_DIR / "gminy_ready.csv"
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

# --- NOWE FUNKCJE DO OBSŁUGI DANYCH GMINY ---

def load_gminy_data(csv_path: Path):
    """Wczytuje dane gminy z gminy_ready.csv do słownika."""
    gminy_data = {}
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:  # utf-8-sig usuwa BOM
        reader = csv.DictReader(f)
        for row in reader:
            gmina_name = row.get("gmina", "").strip()
            if gmina_name:
                # Normalizuj kluczy do float gdzie potrzeba
                for key in ["powierzchnia", "gestosc", "populacja", "suma_U19", "wydatki", "przystanki"]:
                    if key in row:
                        try:
                            row[key] = float(row[key])
                        except (ValueError, TypeError):
                            pass
                gminy_data[gmina_name] = row
    return gminy_data

def load_gminy_geometries(powiaty_path: Path, voivodeship_geom):
    """
    Wczytuje geometrie gminy z poland.municipalities.json.
    Zwraca listę tupli (geometry, name, terc) dla gminy w województwie.
    """
    with open(powiaty_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    gminy_geoms = []
    for feature in data["features"]:
        poly = shape(feature["geometry"])
        props = feature.get("properties", {})
        name = props.get("name", "")
        terc = props.get("terc", "")
        
        # Sprawdzamy, czy gmina należy do województwa
        if voivodeship_geom.intersects(poly.centroid):
            gminy_geoms.append({
                "geometry": poly,
                "name": name,
                "terc": terc
            })
    
    return gminy_geoms

def find_gmina_for_point(point: Point, gminy_geoms: list):
    """
    Znajduje, która gmina zawiera dany punkt.
    Zwraca słownik z informacjami gminy lub None.
    """
    for gmina_info in gminy_geoms:
        if gmina_info["geometry"].contains(point):
            return gmina_info
    return None

class GminaDataAccessor:
    """
    Klasa do wygodnego dostępu do danych gminy na podstawie pozycji (x, y).
    Używana przez funkcję fitness algorytmu WOA.
    """
    def __init__(self, gmini_data_dict: dict, gminy_geometries: list):
        """
        Parameters:
        - gmini_data_dict: słownik danych gminy (klucz: nazwa gminy)
        - gminy_geometries: lista geometrii gminy
        """
        self.gminy_data = gmini_data_dict
        self.gminy_geoms = gminy_geometries
        # Utwórz indeks znormalizowanych nazw dla szybszego wyszukiwania
        self._normalized_index = self._build_normalized_index(gmini_data_dict)
    
    def _build_normalized_index(self, gminy_data_dict: dict):
        """
        Buduje indeks zmapowujący znormalizowane nazwy na oryginalne.
        Obsługuje warianty: "Racławice", "gmina Racławice", "Racławice (gmina)", itd.
        """
        index = {}
        for name, data in gminy_data_dict.items():
            # Normalizuj: usuń "gmina" prefix, "(gmina)" suffix, itp.
            normalized = name.strip()
            if normalized.startswith("gmina "):
                normalized = normalized[6:].strip()
            if normalized.endswith(" (gmina)"):
                normalized = normalized[:-8].strip()
            if normalized.endswith("(gmina)"):
                normalized = normalized[:-7].strip()
            
            index[normalized] = name
        return index
    
    def _find_gmina_name_variant(self, geom_name: str):
        """
        Szuka nazwy gminy w CSV odpowiadającej nazwie z geometrii.
        Zwraca oryginalną nazwę z CSV lub None.
        """
        # Znormalizuj wyszukiwaną nazwę
        normalized = geom_name.strip()
        if normalized.startswith("gmina "):
            normalized = normalized[6:].strip()
        
        # Dokładne dopasowanie
        if normalized in self._normalized_index:
            return self._normalized_index[normalized]
        
        # Fuzzy matching: wyszukaj zawierającą
        lower_normalized = normalized.lower()
        for norm_name, original_name in self._normalized_index.items():
            if lower_normalized in norm_name.lower() or norm_name.lower() in lower_normalized:
                return original_name
        
        return None
    
    def get_data_for_position(self, x: float, y: float):
        """
        Zwraca dane gminy dla danej pozycji (x, y).
        Jeśli punkt nie leży w żadnej gminie, zwraca None.
        
        Returns:
            dict: dane gminy z gminy_ready.csv lub None
        """
        point = Point(x, y)
        gmina_info = find_gmina_for_point(point, self.gminy_geoms)
        
        if gmina_info is None:
            return None
        
        # Szukaj danych po nazwie gminy
        gmina_name = gmina_info["name"]
        
        # Spróbuj znaleźć z normalizacją nazw
        csv_name = self._find_gmina_name_variant(gmina_name)
        
        if csv_name and csv_name in self.gminy_data:
            return self.gminy_data[csv_name]
        
        # Jeśli nie znaleźliśmy danych w CSV, zwróć None
        # (oznacza że gmina nie ma danych w gminy_ready.csv)
        return None


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
    
    # NOWY KROK: Załaduj dane i geometrie gminy
    print("Wczytywanie danych gminy...")
    gminy_data = load_gminy_data(GMINY_READY_PATH)
    gminy_geoms = load_gminy_geometries(POWIATY_PATH, geom)
    
    # Utwórz accessor do danych gminy
    gmina_accessor = GminaDataAccessor(gminy_data, gminy_geoms)

    print(f"Załadowano geometrię: {TARGET_VOIVODESHIP}")
    print(f"Liczba powiatów w Małopolsce: {len(powiaty_in_malopolska)}")
    print(f"Liczba gminy: {len(gminy_geoms)}")
    print(f"Rekordy danych gminy: {len(gminy_data)}")
    print(f"Szkoły wewnątrz granic: {len(school_rows_in_malopolska)}")

    # PRZYKŁAD: Użyj accessor'a do pobrania danych dla konkretnej pozycji
    if school_rows_in_malopolska:
        first_school = school_rows_in_malopolska[0]
        x_test, y_test = first_school["_x"], first_school["_y"]
        gmina_data_for_school = gmina_accessor.get_data_for_position(x_test, y_test)
        print(f"\nDane gminy dla pozycji ({x_test:.2f}, {y_test:.2f}):")
        print(gmina_data_for_school)

    # Wyświetl mapę
    plot_małopolska_with_schools_and_powiaty(geom, school_rows_in_malopolska, powiaty_in_malopolska)
    
    # WAŻNE: Zwróć accessor, aby był dostępny dla WOA
    return gmina_accessor

if __name__ == "__main__":
    main()