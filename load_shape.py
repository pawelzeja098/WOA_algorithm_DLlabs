import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
from shapely.geometry import Point, shape

DATA_DIR = Path(__file__).resolve().parent / "DATA"
GEOJSON_PATH = DATA_DIR / "wojewodztwa-min.geojson"
SCHOOLS_PATH = DATA_DIR / "szkoly_final.csv"
TARGET_VOIVODESHIP = "małopolskie"


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

        if not reader.fieldnames or "x" not in reader.fieldnames or "y" not in reader.fieldnames:
            raise ValueError("Plik CSV musi zawierać kolumny: x oraz y")

        for row in reader:
            try:
                x = float(row["x"])
                y = float(row["y"])
            except (TypeError, ValueError):
                continue

            row["_x"] = x
            row["_y"] = y
            row["_point"] = Point(x, y)
            rows.append(row)

    return rows


def filter_points_inside_polygon(rows, polygon):
    inside = []
    outside_count = 0

    for row in rows:
        if polygon.covers(row["_point"]):
            inside.append(row)
        else:
            outside_count += 1

    return inside, outside_count


def draw_polygon(ax, geom):
    if geom.geom_type == "MultiPolygon":
        for poly in geom.geoms:
            x, y = poly.exterior.xy
            ax.plot(x, y, color="#1f4e79", linewidth=1.7, zorder=2)
            ax.fill(x, y, color="#9dc3e6", alpha=0.45, zorder=1)
    else:
        x, y = geom.exterior.xy
        ax.plot(x, y, color="#1f4e79", linewidth=1.7, zorder=2)
        ax.fill(x, y, color="#9dc3e6", alpha=0.45, zorder=1)


def plot_małopolska_with_schools(geom, school_rows):
    fig, ax = plt.subplots(figsize=(9, 9))
    draw_polygon(ax, geom)

    xs = [row["_x"] for row in school_rows]
    ys = [row["_y"] for row in school_rows]
    ax.scatter(xs, ys, s=10, alpha=0.7, color="#c00000", label="szkoły", zorder=3)

    ax.set_title("Małopolskie + szkoły")
    ax.set_xlabel("Długość geograficzna ")
    ax.set_ylabel("Szerokość geograficzna")
    ax.set_aspect("equal")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(loc="lower left")
    plt.tight_layout()
    plt.show()


def main():
    geom = load_voivodeship_geometry(GEOJSON_PATH, TARGET_VOIVODESHIP)
    all_school_rows = load_school_rows(SCHOOLS_PATH)
    school_rows_in_malopolska, outside_count = filter_points_inside_polygon(all_school_rows, geom)

    print(f"Załadowano geometrię: {TARGET_VOIVODESHIP}")
    print(f"Wczytane szkoły: {len(all_school_rows)}")
    print(f"Szkoły wewnątrz granic: {len(school_rows_in_malopolska)}")
    print(f"Punkty poza granicą: {outside_count}")

    plot_małopolska_with_schools(geom, school_rows_in_malopolska)


if __name__ == "__main__":
    main()