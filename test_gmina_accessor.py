"""
SZYBKI TEST - Sprawdzenie czy GminaDataAccessor działa prawidłowo
"""

from pathlib import Path
from load_shape import (
    load_voivodeship_geometry,
    load_gminy_data,
    load_gminy_geometries,
    GminaDataAccessor,
    GEOJSON_PATH,
    POWIATY_PATH,
    GMINY_READY_PATH,
    TARGET_VOIVODESHIP
)

print("TEST: GminaDataAccessor")
print("=" * 60)

# Załaduj dane
print("\n1. Wczytywanie danych...")
geom = load_voivodeship_geometry(GEOJSON_PATH, TARGET_VOIVODESHIP)
gminy_data = load_gminy_data(GMINY_READY_PATH)
gminy_geoms = load_gminy_geometries(POWIATY_PATH, geom)

print(f"   ✓ Załadowano {len(gminy_data)} gminy")
print(f"   ✓ Załadowano {len(gminy_geoms)} geometrii")

# Utwórz accessor
print("\n2. Tworzenie GminaDataAccessor...")
accessor = GminaDataAccessor(gminy_data, gminy_geoms)
print("   ✓ Accessor utworzony")

# Test: Pobierz dane dla gminy z pliku CSV
print("\n3. Test dostepu do danych...")
if gminy_data:
    first_gmina_name = list(gminy_data.keys())[0]
    first_gmina = gminy_data[first_gmina_name]
    print(f"   Przykładowa gmina z CSV: {first_gmina_name}")
    print(f"   - Powiat: {first_gmina.get('powiat')}")
    print(f"   - Populacja: {first_gmina.get('populacja')}")
    print(f"   - Suma U19: {first_gmina.get('suma_U19')}")

# Test: Find gmina z geometrii
print("\n4. Test geolokalizacji dla punktu...")
if gminy_geoms:
    # Weź centroid pierwszej gminy
    first_geom = gminy_geoms[0]
    test_x, test_y = first_geom["geometry"].centroid.x, first_geom["geometry"].centroid.y
    print(f"   Testowanie punktu: ({test_x:.2f}, {test_y:.2f})")
    
    # Spróbuj pobrać dane
    result = accessor.get_data_for_position(test_x, test_y)
    if result:
        print(f"   ✓ Znaleziona gmina: {result.get('gmina', result.get('name', 'N/A'))}")
        print(f"   ✓ Powiat: {result.get('powiat', 'N/A')}")
        print(f"   ✓ Dane dostępne: {not result.get('data_not_found', False)}")
    else:
        print(f"   Nie znaleziono gminy dla tego punktu")

print("\n" + "=" * 60)
print("TEST ZAKONCZONY POMYSLNIE\n")
