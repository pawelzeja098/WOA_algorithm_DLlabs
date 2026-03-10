# config.py — Konfiguracja projektu WOA: Lokalizacja placówki oświatowej

# ---------------------------------------------------------------------------
# Obszar geograficzny (siatka km × km)
# ---------------------------------------------------------------------------
AREA_SIZE = 100  # 100 km × 100 km

# ---------------------------------------------------------------------------
# Typ szkoły: 'kindergarten' | 'primary' | 'secondary'
# Wpływa na etykiety i domyślny zestaw wag
# ---------------------------------------------------------------------------
SCHOOL_TYPE = "primary"

# ---------------------------------------------------------------------------
# Parametry algorytmu wielorybiego (WOA)
# ---------------------------------------------------------------------------
WOA_PARAMS = {
    "n_agents": 30,       # Liczba wielorybów (rozmiar populacji)
    "max_iter": 100,      # Maksymalna liczba iteracji
    "b": 1.0,             # Stała kształtu spirali logarytmicznej
    "seed": 42,           # Ziarno losowości (None = losowy)
}

# ---------------------------------------------------------------------------
# Wagi kryteriów (suma = 1.0)
#   distance      – odległość do najbliższej szkoły        (im większa → wyższa potrzeba)
#   students      – liczba potencjalnych uczniów w gminie  (im więcej  → wyższa potrzeba)
#   occupancy     – obłożenie najbliższych szkół           (im wyższe  → wyższa potrzeba)
#   connectivity  – wskaźnik skomunikowania gminy          (odwrócony: gorsza sieć → wyższa potrzeba)
#   exam_results  – wyniki egzaminów                       (odwrócony: gorsze wyniki → wyższa potrzeba)
#   fertility     – współczynnik dzietności                (im wyższy  → wyższa potrzeba w przyszłości)
# ---------------------------------------------------------------------------
WEIGHTS = {
    "distance":      0.25,
    "students":      0.20,
    "occupancy":     0.20,
    "connectivity":  0.10,
    "exam_results":  0.10,
    "fertility":     0.15,
}

# Upewnij się, że wagi sumują się do 1
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "Wagi muszą sumować się do 1.0"

# ---------------------------------------------------------------------------
# Parametry generatora danych syntetycznych
# ---------------------------------------------------------------------------
DATA_PARAMS = {
    "n_municipalities": 50,   # Liczba gmin
    "n_existing_schools": 15, # Liczba istniejących szkół
    "seed": 42,
}

# ---------------------------------------------------------------------------
# Ustawienia wizualizacji
# ---------------------------------------------------------------------------
VISUALIZATION = {
    "enabled": True,
    "save_figures": True,         # Zapisz PNG do katalogu output/
    "show_plots": True,           # Wyświetl okna matplotlib
    "landscape_resolution": 40,  # Rozdzielczość siatki mapy fitness (↑ wolniej)
}
