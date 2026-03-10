# WOA — System wspomagania decyzji o lokalizacji placówki oświatowej

> Projekt wykorzystuje **Whale Optimization Algorithm (WOA)** do wskazania
> optymalnego miejsca budowy przedszkola, szkoły podstawowej lub liceum
> na podstawie sześciu kryteriów przestrzenno-demograficznych.

---

## Spis treści

1. [Opis problemu](#opis-problemu)
2. [Algorytm WOA](#algorytm-woa)
3. [Zmienne wejściowe i kryteria](#zmienne-wejściowe-i-kryteria)
4. [Struktura projektu](#struktura-projektu)
5. [Instalacja](#instalacja)
6. [Uruchomienie](#uruchomienie)
7. [Konfiguracja](#konfiguracja)
8. [Opis modułów](#opis-modułów)
9. [Wyniki i wizualizacje](#wyniki-i-wizualizacje)

---

## Opis problemu

Celem systemu jest wspomaganie decyzji dotyczących **optymalnej lokalizacji
nowej placówki oświatowej** (przedszkole / szkoła podstawowa / liceum)
na zadanym obszarze geograficznym.

Dla każdego kandydującego miejsca w przestrzeni 2D obliczany jest
**złożony wskaźnik potrzeby** — ważona suma sześciu kryteriów.
Algorytm WOA przeszukuje przestrzeń i maksymalizuje ten wskaźnik.

---

## Algorytm WOA

**Whale Optimization Algorithm** (Mirjalili & Lewis, 2016) naśladuje
zachowania łowieckie humbaków (*Megaptera novaeangliae*):

| Faza | Mechanizm | Efekt |
|------|-----------|-------|
| Eksploracja | Losowe przeszukiwanie (|A| ≥ 1) | Globalne rojenie |
| Eksploatacja | Zwężające się okrążanie (|A| < 1) | Lokalne zagęszczenie |
| Eksploatacja | Spirala logarytmiczna (p ≥ 0.5) | Precyzyjne dążenie |

Parametr `a` maleje liniowo od 2 do 0, balansując eksplorację i eksploatację.

**Aktualizacja pozycji wieloryba `i` w iteracji `t`:**

$$
\vec{X}(t+1) = \begin{cases}
\vec{X}^*(t) - A \cdot D & \text{zwężające okrążanie} \\
\vec{X}_{rand} - A \cdot D & \text{losowe przeszukiwanie} \\
D' \cdot e^{bl} \cdot \cos(2\pi l) + \vec{X}^*(t) & \text{spirala}
\end{cases}
$$

gdzie $D = |C \cdot \vec{X}^* - \vec{X}|$, $A = 2ar_1 - a$, $C = 2r_2$,
$l \in [-1, 1]$, $b$ — stała kształtu spirali.

---

## Zmienne wejściowe i kryteria

| # | Zmienna | Kierunek wpływu | Waga domyślna |
|---|---------|-----------------|---------------|
| 1 | **Odległość do najbliższej szkoły** | ↑ większa → wyższa potrzeba | 0.25 |
| 2 | **Liczba potencjalnych uczniów w gminie** | ↑ więcej → wyższa potrzeba | 0.20 |
| 3 | **Obłożenie najbliższych szkół** | ↑ wyższe → wyższa potrzeba | 0.20 |
| 4 | **Współczynnik skomunikowania gminy** | ↓ gorszy → wyższa potrzeba *(odwrócony)* | 0.10 |
| 5 | **Wyniki egzaminów** | ↓ gorsze → wyższa potrzeba *(odwrócony)* | 0.10 |
| 6 | **Współczynnik dzietności** | ↑ wyższy → wyższa potrzeba | 0.15 |

Wartości cech w przestrzeni ciągłej są interpolowane z danych gmin
metodą **IDW** (ważona odwrotność kwadratu odległości).

---

## Struktura projektu

```
WOA_algorithm_DLlabs/
├── main.py                   # Główny skrypt uruchomieniowy
├── config.py                 # Konfiguracja (wagi, params WOA, typ szkoły)
├── requirements.txt          # Zależności Python
├── README.md
├── src/
│   ├── __init__.py
│   ├── woa.py                # Implementacja algorytmu WOA
│   ├── problem.py            # Funkcja celu (wskaźnik potrzeby)
│   ├── data_generator.py     # Generator syntetycznych danych gmin
│   └── visualization.py     # Wizualizacje (matplotlib)
└── output/                   # (tworzony automatycznie)
    ├── municipalities.csv    # Dane gmin
    ├── woa_results.csv       # Wyniki optymalizacji
    ├── feature_maps.png      # Mapy 6 zmiennych
    ├── fitness_landscape.png # Mapa wskaźnika + trajektoria WOA
    ├── convergence.png       # Krzywa zbieżności
    └── criteria_analysis.png # Analiza kryteriów (słupkowy + radarowy)
```

---

## Instalacja

```bash
# Sklonuj repozytorium / otwórz folder projektu w terminalu
cd WOA_algorithm_DLlabs

# (Opcjonalnie) utwórz środowisko wirtualne
python -m venv .venv
.venv\Scripts\activate        # Windows
# lub: source .venv/bin/activate  (Linux/macOS)

# Zainstaluj zależności
pip install -r requirements.txt
```

### Wymagania

| Biblioteka | Wersja min. | Zastosowanie |
|------------|-------------|--------------|
| numpy | 1.24 | operacje macierzowe, WOA |
| pandas | 2.0 | dane gmin, eksport CSV |
| scipy | 1.10 | interpolacja IDW, macierze odległości |
| matplotlib | 3.7 | wszystkie wykresy |

---

## Uruchomienie

```bash
python main.py
```

Program wykona 4 kroki:

1. **Generowanie danych** — 50 syntetycznych gmin + 15 istniejących szkół
2. **Konfiguracja problemu** — funkcja celu z wagami z `config.py`
3. **Optymalizacja WOA** — 30 wielorybów × 100 iteracji
4. **Wizualizacje** — 4 wykresy zapisane w `output/`

Przykładowe wyjście:
```
================================================================
  WOA — System wspomagania decyzji o lokalizacji
  Typ placówki: Szkoła podstawowa
================================================================
...
  ★ Optymalna lokalizacja:  X = 72.148 km,  Y = 18.563 km
  ★ Wskaźnik potrzeby:      0.736421
```

---

## Konfiguracja

Wszystkie parametry projektu znajdują się w pliku [`config.py`](config.py):

### Typ placówki

```python
SCHOOL_TYPE = "primary"   # "kindergarten" | "primary" | "secondary"
```

### Parametry WOA

```python
WOA_PARAMS = {
    "n_agents": 30,    # Rozmiar populacji
    "max_iter": 100,   # Liczba iteracji
    "b": 1.0,          # Stała spirali logarytmicznej
    "seed": 42,        # Reprodukowalność
}
```

### Wagi kryteriów

```python
WEIGHTS = {
    "distance":      0.25,   # Odległość do szkoły
    "students":      0.20,   # Liczba uczniów
    "occupancy":     0.20,   # Obłożenie szkół
    "connectivity":  0.10,   # Skomunikowanie (odwrócone)
    "exam_results":  0.10,   # Wyniki egzaminów (odwrócone)
    "fertility":     0.15,   # Dzietność
}
```

Wagi muszą sumować się do `1.0` (jest automatyczna walidacja).

---

## Opis modułów

### `src/woa.py` — `WhaleOptimizationAlgorithm`

Klasa implementuje pełny algorytm WOA z maksymalizacją funkcji celu.

| Atrybut | Opis |
|---------|------|
| `best_position` | Optymalna pozycja (x, y) po zakończeniu |
| `best_score` | Wartość funkcji celu w najlepszym punkcie |
| `convergence_curve` | Lista najlepszych wyników w każdej iteracji |
| `history` | Pozycje wszystkich agentów w każdej iteracji |

### `src/problem.py` — `SchoolPlacementProblem`

Funkcja celu — oblicza ważony wskaźnik potrzeby dla punktu (x, y).

- Interpolacja IDW wartości cech z najbliższych gmin
- Normalizacja min-max wszystkich składowych do [0, 1]
- Metoda `breakdown(position)` zwraca szczegółowy rozkład składowych

### `src/data_generator.py`

Generator syntetyczny odzwierciedlający gradient miejski-wiejski:
- Gminy miejskie: więcej uczniów, wyższe obłożenie, lepsza komunikacja
- Gminy wiejskie: wyższa dzietność, niższe obłożenie, słabsza komunikacja

### `src/visualization.py`

| Funkcja | Opis |
|---------|------|
| `plot_feature_maps` | 6 map rozłożenia zmiennych wejściowych |
| `plot_fitness_landscape` | Mapa fitness + trajektoria agentów WOA |
| `plot_convergence` | Krzywa zbieżności algorytmu |
| `plot_criteria_analysis` | Słupkowy + radarowy wykres kryteriów |

---

## Wyniki i wizualizacje

| Plik | Zawartość |
|------|-----------|
| `output/municipalities.csv` | Dane wszystkich gmin |
| `output/woa_results.csv` | Optymalna lokalizacja, wynik, metadane |
| `output/feature_maps.png` | 6 map przestrzennych zmiennych |
| `output/fitness_landscape.png` | Mapa wskaźnika potrzeby + trajektoria WOA |
| `output/convergence.png` | Zbieżność algorytmu po iteracjach |
| `output/criteria_analysis.png` | Rozkład kryteriów dla optymalnej lok. |

---

## Źródło algorytmu

> Mirjalili, S., & Lewis, A. (2016).
> *The Whale Optimization Algorithm.*
> Advances in Engineering Software, 95, 51–67.
> https://doi.org/10.1016/j.advengsoft.2016.01.008
