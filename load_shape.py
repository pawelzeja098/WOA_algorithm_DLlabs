import json
from shapely.geometry import shape
import matplotlib.pyplot as plt

# Wczytujemy plik z wszystkimi województwami
with open('data/wojewodztwa-min.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)


malopolska_data = None
for feature in data['features']:
   
    if feature['properties'].get('nazwa') == 'małopolskie':
        malopolska_data = feature
        break

if malopolska_data:
    # Zamieniamy na obiekt geograficzny (Polygon lub MultiPolygon)
    wojewodztwo_shape = shape(malopolska_data['geometry'])
    print("Pomyślnie załadowano Małopolskę!")
else:
    print("Nie znaleziono województwa o takiej nazwie.")

def plot_voivodeship(geom):
    fig, ax = plt.subplots(figsize=(8, 8))
    
   
    if geom.geom_type == 'MultiPolygon':
        for poly in geom.geoms:
            x, y = poly.exterior.xy
            ax.plot(x, y, color='#6699cc', alpha=0.7, linewidth=3, solid_capstyle='round', zorder=2)
            ax.fill(x, y, color='#6699cc', alpha=0.3)
    else:
        
        x, y = geom.exterior.xy
        ax.plot(x, y, color='#6699cc', alpha=0.7, linewidth=3, solid_capstyle='round', zorder=2)
        ax.fill(x, y, color='#6699cc', alpha=0.3)

    ax.set_title("Podgląd załadowanego województwa: Małopolskie")
    ax.set_aspect('equal')
    plt.xlabel("Długość geograficzna (Longitude)")
    plt.ylabel("Szerokość geograficzna (Latitude)")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.show()


plot_voivodeship(wojewodztwo_shape)