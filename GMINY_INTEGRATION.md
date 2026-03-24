# Integracja danych gminy z algorytmem WOA

## 📋 Problem
Jak załadować dane z `gminy_ready.csv` aby algorytm WOA miał dostęp do danych każdej gminy na podstawie proponowanej lokalizacji (x, y)?

## ✅ Rozwiązanie

System oparty na 3 komponentach:

### 1. **Załadowanie danych gminy** 
```python
gminy_data = load_gminy_data(GMINY_READY_PATH)
```
- Wczytuje CSV do słownika: `{ "nazwa_gminy": { dane } }`
- Konwertuje kolumny numeryczne (populacja, wydatki, itp.)

### 2. **Załadowanie geometrii gminy**
```python
gminy_geoms = load_gminy_geometries(POWIATY_PATH, geom)
```
- Wczytuje geometrie z `poland.municipalities.json`
- Zwraca listę: `[{ "geometry": Polygon, "name": str, "terc": str }, ...]`

### 3. **GminaDataAccessor** - główna klasa dostępu
```python
gmina_accessor = GminaDataAccessor(gminy_data, gminy_geoms)

# Użycie:
gmina_data = gmina_accessor.get_data_for_position(x=123.45, y=678.90)
```

**Co robi:**
- Na podstawie pozycji (x, y) znajduje, która gmina zawiera ten punkt
- Zwraca dane tej gminy z `gminy_ready.csv`
- zwraca `None` jeśli punkt jest poza wszystkimi gminami

## 🔄 Flow: Od pozycji do danych

```
Pozycja (x, y) z algorytmu WOA
    ↓
GminaDataAccessor.get_data_for_position(x, y)
    ↓
find_gmina_for_point() - sprawdza geometrie
    ↓
Zwraca: { "powiat": "...", "gmina": "...", "populacja": 25000, ... }
    ↓
Funkcja fitness używa tych danych do oceny pozycji
```

## 💻 Użycie w praktyce

### Opcja A: W funkcji fitness (REKOMENDOWANE)

```python
from load_shape import GminaDataAccessor, load_gminy_data, load_gminy_geometries

# Przygotowanie
gmina_accessor = GminaDataAccessor(gminy_data, gminy_geoms)

# Funkcja fitness
def fitness_func(position):
    x, y = position
    gmina_data = gmina_accessor.get_data_for_position(x, y)
    
    if gmina_data is None:
        return 0.0  # Punkt poza gminą
    
    # Użyj danych gminy do oceny
    score = gmina_data.get("suma_U19", 0) + gmina_data.get("przystanki", 0)
    return score

# Algorytm WOA
from src.woa import WhaleOptimizationAlgorithm
woa = WhaleOptimizationAlgorithm(fitness_func=fitness_func, ...)
```

### Opcja B: Poza funkcją fitness

```python
# Dla niestandardowych analiz
for position in positions:
    gmina_info = gmina_accessor.get_data_for_position(position[0], position[1])
    print(gmina_info)
```

## 📊 Dostępne dane w gminy_ready.csv

```python
gmina_data = {
    "gmina": "Nowy Wiśnicz",
    "powiat": "powiat bocheński",
    "powierzchnia": 82,           # km²
    "gestosc": 176.3,             # osób/km²
    "populacja": 14457,
    "0-4": 784,
    "5-9": 1011,
    "10-14": 955,
    "15-19": 922,
    "suma_U19": 3672,             # razem osoby poniżej 19 lat
    "wydatki": 52504807.6,        # budżet gminy
    "przystanki": 151             # liczba przystanków transportu publicznego
}
```

## 📍 Przykład metryki fitness

### Minimalizuj dystans do szkół z dostępem do transportu
```python
def fitness_func(position):
    gmina_data = gmina_accessor.get_data_for_position(position[0], position[1])
    if gmina_data is None:
        return 0.0
    
    # Prioritizuj gminy z dużą młodą populacją i dostępem do transportu
    score = (gmina_data["suma_U19"] * 0.7) + (gmina_data["przystanki"] * 0.3)
    return score
```

### Maksymalizuj dostęp dla słabych demograficznie gmin
```python
def fitness_func(position):
    gmina_data = gmina_accessor.get_data_for_position(position[0], position[1])
    if gmina_data is None:
        return 0.0
    
    # Preferuj gminy z mniejszą populacją (marginalizowane tereny)
    score = 1.0 / (1.0 + gmina_data["populacja"] / 5000)
    return score
```

## 🚀 Pełny przykład

Patrz plik: `example_woa_with_gminy.py`

Uruchamienie:
```bash
cd e:\Studia\WOA_algorithm_DLlabs
python example_woa_with_gminy.py
```

## 🔧 Debugowanie

**Sprawdzenie, czy gmina znaleziona:**
```python
# Test punktu
test_point = (123.45, 678.90)
gmina = gmina_accessor.get_data_for_position(test_point[0], test_point[1])

if gmina is None or gmina.get("data_not_found"):
    print(f"⚠️  Punkt {test_point} nie znaleziony w żadnej gminie!")
else:
    print(f"✓ Znaleziona gmina: {gmina['gmina']}")
```

**Sprawdzenie liczby załadowanych gmin:**
```python
print(f"Gminy w CSV: {len(gminy_data)}")
print(f"Geometrie gminy: {len(gminy_geoms)}")
# Powinny być zbliżone lub geometrii mogą być więcej
```

## ⚠️ Często spotykane problemy

### Problem: `gmina_accessor.get_data_for_position()` zwraca None
**Przyczyna:** Punkt (x, y) leży poza granicami Małopolski
**Rozwiązanie:** Sprawdź czy punkt jest wewnątrz `mask_polygon`

### Problem: Dane gminy znalezione ale `data_not_found: True`
**Przyczyna:** Nazwa gminy z geometrii nie pasuje do CSV
**Rozwiązanie:** Normalizuj nazwy gminy (usuwaj znaki diakrytyczne, spaces)

### Problem: Funkcja fitness zawsze zwraca 0
**Przyczyna:** Wszystkie pozycje WOA są poza gminami
**Rozwiązanie:** 
- Sprawdź czy `mask_polygon` jest prawidłowy
- Sprawdź czy initial population jest inicjalizowana poprawnie
- Debuguj z print() w funkcji fitness

## 📚 Powiązane funkcje w load_shape.py

| Funkcja | Opis |
|---------|------|
| `load_gminy_data()` | Wczytuje gminy_ready.csv |
| `load_gminy_geometries()` | Wczytuje geometrie z JSON |
| `find_gmina_for_point()` | Znajduje gminę dla punktu |
| `GminaDataAccessor` | Klasa dostępu do danych |

## 💡 Wskazówki

1. **Cachuj accessor** - stwórz raz na początku, nie na nowo w każdej iteracji
2. **Normalizuj metryki** - dziel duże liczby aby fitness mieści się w rozsądnym zakresie
3. **Testuj fitness** - przetestuj funkcję fitness z kilkoma punktami before running WOA
4. **Obsługuj None** - zawsze sprawdź czy `get_data_for_position()` zwrófćiła dane

---

**Autor:** Dokumentacja systemu WOA z danymi gminy  
**Data:** 2024  
**Status:** ✓ Przetestowano i gotowe do użytku
