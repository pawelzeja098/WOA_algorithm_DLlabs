# 📊 Dane dostępne do funkcji celu - Kompleksowy przewodnik

## 🎯 Strefa dla opracowywania funkcji fitness

Ta dokumentacja pokazuje **WSZYSTKIE dostępne dane** które możesz użyć w funkcji celu (`fitness_func`).
Każda wartość jest przygotowana i gotowa do użytku.

---

## 📦 Dostępne źródła danych

### 1. **Dane demograficzne gminy** (z `gminy_ready.csv`)
```python
gmina_data = {
    "gmina": "Tarnów",
    "powiat": "Tarnów",
    "powierzchnia": 82.0,           # km²
    "gestosc": 176.3,               # osób/km²
    "populacja": 101599.0,          # całkowita populacja
    "0-4": 784,                     # liczba dzieci w każdej grupie wiekowej
    "5-9": 1011,
    "10-14": 955,
    "15-19": 922,
    "suma_U19": 17277.0,            # ⭐ SUMA DZIECI PONIŻEJ 19 LAT
    "wydatki": 52504807.6,          # budżet gminy (zł)
    "przystanki": 376.0             # liczba przystanków transportu publicznego
}
```

### 2. **Dane edukacyjne gminy** (z `E8 - gminy (aktualizacja 07.2025).csv`)
```python
egzaminy_data = {
    # Zagregowane metryki
    "srednia_wszystkich_przedmiotow": 65.5,  # średnia z wszystkich przedmiotów (%)
    "liczba_zdajacych": 380.0,               # średnia liczba zdających (wszystkie przedmioty)
    "srednie_odchylenie_standardowe": 18.5,  # średnie odchylenie (wskaźnik nierówności)
    
    # Szczegółowe dane po przedmiotach (dla każdego: polski, matematyka, angielski, ...)
    "przedmioty": {
        "polski": {
            "liczba_zdajacych": 350,
            "srednia": 65.2,                 # wynik średni (%)
            "odchylenie_standardowe": 16.8,
            "mediana": 68.5,                 # wynik środkowy
            "modalna": 70.0                  # najczęstszy wynik
        },
        "matematyka": {
            "liczba_zdajacych": 350,
            "srednia": 52.1,
            "odchylenie_standardowe": 28.3,
            "mediana": 40.0,
            "modalna": 20.0
        },
        "angielski": {
            "liczba_zdajacych": 340,
            "srednia": 72.5,
            "odchylenie_standardowe": 24.1,
            "mediana": 85.0,
            "modalna": 96.0
        },
        # ... pozostałe przedmioty: francuski, hiszpanski, niemiecki, rosyjski, wloski
    }
}
```

---

## 🔗 Jak dane trafiają do `fitness_func`

```python
def fitness_func(position: np.ndarray) -> float:
    """
    position = [x, y]  - współrzędne geograficzne
    """
    x, y = position[0], position[1]
    
    # ===== DANE DEMOGRAFICZNE =====
    gmina_data = gmina_accessor.get_data_for_position(x, y)
    # gmina_data zawiera wszystko z gminy_ready.csv
    
    # ===== DANE EDUKACYJNE =====
    egzaminy_data = egzaminy_accessor.get_wszystkie_dane_dla_gminy(gmina_data["gmina"])
    # egzaminy_data zawiera wszystko z E8 - gminy
    
    # ===== TWOJA FUNKCJA CELU =====
    # Teraz masz dostęp do WSZYSTKICH danych i możesz je kombinować jak chcesz!
    score = ...  # ← TUTAJ TY DEFINIUJESZ LOGIKĘ
    
    return float(score)
```

---

## 📋 Lista WSZYSTKICH dostępnych wartości

### Przed przedmiotu (każdy ma te same pola):
| Pole | Typ | Opis |
|------|-----|------|
| `liczba_zdajacych` | int | Ilu uczniów brało egzamin z danego przedmiotu |
| `srednia` | float | Średnia % wynik (0-100) |
| `odchylenie_standardowe` | float | Rozproszenie wyników - wskaźnik **nierówności** |
| `mediana` | float | Wynik środkowy - połowa ponieżej, połowa powyżej (%) |
| `modalna` | float | Najczęstszy wynik (%) |

### Zagregowane metryki:
| Pole | Typ | Opis | Przydatność |
|------|-----|--------|-------------|
| `suma_U19` | float | Liczba dzieci 0-19 lat | Rozmiar populacji szkolnej |
| `liczba_zdajacych` | float | Ilu uczniów ma dostęp do edukacji | Dostęp do szkoły |
| `srednia_wszystkich_przedmiotow` | float | Średnia jakość edukacji | Poziom edukacji |
| `srednie_odchylenie_standardowe` | float | Średnia nierówność wyników | Potrzeba wsparcia |
| `przystanki` | float | Dostęp do transportu | Dojazd do szkoły |
| `populacja` | float | Całkowita populacja gminy | Zaludnienie |
| `gestosc` | float | osób/km² | Urbanizacja |
| `wydatki` | float | Budżet gminy (zł) | Potencjał finansowy |

---

## 💡 Przykłady kombinacji metryk

### **Przykład 1: Deficyt edukacyjny**
```python
deficyt = suma_u19 / (liczba_zdajacych + 1)
# Wysoki = mało uczniów na dziecko = duży deficyt edukacyjny
```

### **Przykład 2: Nierówności szkolne**
```python
nierownosc = srednie_odchylenie_standardowe
# Wysokie = uczniowie mają bardzo różne wyniki = potrzeba wsparcia
```

### **Przykład 3: Słabi uczniowie**
```python
unia_slabych = (mediana - srednia) / srednia  # dla każdego przedmiotu
# Negatywna = mediana poniżej średniej = połowa uczniów słaba
```

### **Przykład 4: Dostęp do transportu dla uczniów**
```python
transport_per_capita = przystanki / suma_u19
# Wysoki = dobre połączenia komunikacyjne dla dzieci
```

### **Przykład 5: Potencjał inwestycji**
```python
potencjal = (wydatki / populacja) * (suma_u19 / populacja)
# Budżet gminy * udział dzieci = potencjał do wydania na edukację
```

### **Przykład 6: Kombinacja wszystkich metryk**
```python
# Szkoła gdzie NAPRAWDĘ jest potrzebna
score = (
    0.3 * (suma_u19 / (liczba_zdajacych + 1)) +              # deficyt
    0.2 * srednie_odchylenie_standardowe +                   # nierówności
    0.2 * (1.0 / (srednia_wszystkich_przedmiotow + 1)) +     # słabe wyniki
    0.15 * (przystanki / suma_u19) +                         # transport
    0.15 * max(0, mediana - srednia) / 100                   # słabi uczniowie
)
```

---

## 🎓 Przedmioty dostępne w pliku E8

| Przedmiot | Klucz w słowniku |
|-----------|------------------|
| Polski | `"polski"` |
| Matematyka | `"matematyka"` |
| Język angielski | `"angielski"` |
| Język francuski | `"francuski"` |
| Język hiszpański | `"hiszpanski"` |
| Język niemiecki | `"niemiecki"` |
| Język rosyjski | `"rosyjski"` |
| Język włoski | `"wloski"` |

---

## 🔧 Jak używać w kodzie

```python
# W funkcji fitness
def fitness_func(position):
    x, y = position
    
    # Pobierz dane
    gmina_data = gmina_accessor.get_data_for_position(x, y)
    if gmina_data is None:
        return 0.0
    
    egzaminy_data = egzaminy_accessor.get_wszystkie_dane_dla_gminy(gmina_data["gmina"])
    if egzaminy_data is None:
        return 0.0
    
    # Dostęp do każdej wartości
    suma_u19 = gmina_data["suma_U19"]
    liczba_zdajacych = egzaminy_data["liczba_zdajacych"]
    srednia = egzaminy_data["srednia_wszystkich_przedmiotow"]
    nierownos = egzaminy_data["srednie_odchylenie_standardowe"]
    przystanki = gmina_data["przystanki"]
    
    # Dostęp do szczegółów przedmiotu
    polski_srednia = egzaminy_data["przedmioty"]["polski"]["srednia"]
    matematyka_mediana = egzaminy_data["przedmioty"]["matematyka"]["mediana"]
    
    # Twoja metryka
    score = ...
    return float(score)
```

---

## ✅ Checklist dla funkcji celu

Zanim zaczniesz pisać `fitness_func`, przygotuj plan:

- [ ] **Cel**: Co chcę optymalizować? (dostęp, jakość, równość, itd.)
- [ ] **Dane**: Które kolumny będę używać?
- [ ] **Wagi**: Jakie będą proporcje między metrykami?
- [ ] **Normalizacja**: Jak przeskalować wartości aby się nie dominowały?
- [ ] **Testy**: Jakie gminy powinny mieć najwyższy score?

---

## 📌 Ważne!

1. **Zawsze sprawdzaj `None`** - jeśli dane dla gminy się nie znalazły
2. **Unikaj dzielenia przez 0** - dodaj `+ 1` do mianownika
3. **Normalizuj wartości** - duża liczba może zdominować małą
4. **Testuj logicę** - wypisz wartości dla kilku gmin zanim puszczysz WOA

---

## 🚀 Gotowy szablon

```python
def fitness_func(position: np.ndarray) -> float:
    x, y = position[0], position[1]
    
    # Pobierz dane
    gmina_data = gmina_accessor.get_data_for_position(x, y)
    if gmina_data is None:
        return 0.0
    
    egzaminy_data = egzaminy_accessor.get_wszystkie_dane_dla_gminy(gmina_data["gmina"])
    if egzaminy_data is None:
        return 0.0
    
    # =================================
    # TUTAJ DEFINIUJESZ SWOJĄ LOGIKĘ
    # =================================
    
    # Przykład: szkoła gdzie jest potrzeba
    score = (
        gmina_data["suma_U19"] / (egzaminy_data["liczba_zdajacych"] + 1) +
        egzaminy_data["srednie_odchylenie_standardowe"] / 10
    )
    
    # =================================
    
    return float(score)
```

---

**Status:** ✅ Wszystkie dane przygotowane i gotowe do użytku!
