"""
Modul do wczytywania danych z E8 - gminy (aktualizacja 07.2025).csv
Przygotowuje dane wejsciowe do funkcji fitness algorytmu WOA.
"""

import csv
from pathlib import Path
from typing import Dict, Optional


def safe_float(value: str, default: float = 0.0) -> float:
    """Bezpieczna konwersja stringa do float."""
    if not value or value.strip() == "":
        return default
    try:
        # Zamien przecinek na kropke (polska notacja)
        return float(str(value).strip().replace(",", "."))
    except (ValueError, AttributeError):
        return default


def load_egzaminy_data(csv_path: Path) -> Dict[str, Dict]:
    """
    Wczytuje dane egzaminow z E8 - gminy (aktualizacja 07.2025).csv
    
    Obsługuje rozne kodowania (cp1250, utf-8-sig, utf-8, latin-1, iso-8859-2)
    bez zaleznoci external.
    
    Args:
        csv_path: sciezka do pliku E8 - gminy (aktualizacja 07.2025).csv
    
    Returns:
        slownik z danymi egzaminow po gminach
    """
    egzaminy = {}
    
    przedmioty = [
        "polski",
        "matematyka",
        "angielski",
        "francuski",
        "hiszpanski",
        "niemiecki",
        "rosyjski",
        "wloski"
    ]
    
    encodings_to_try = ['cp1250', 'utf-8-sig', 'utf-8', 'latin-1', 'iso-8859-2']
    
    for enc in encodings_to_try:
        try:
            egzaminy = {}  # Reset dla kazdego kodowania
            
            with open(csv_path, "r", encoding=enc, newline="") as f:
                reader = csv.reader(f, delimiter=";")

                # Wiersz 1: grupy przedmiotów, wiersz 2: właściwe nagłówki
                next(reader, None)
                next(reader, None)
                
                for row in reader:
                    if len(row) < 46:
                        continue

                    gmina = row[3].strip()
                    typ_gminy = row[4].strip()
                    powiat = row[2].strip()
                    wojewodztwo = row[1].strip()
                    
                    if not gmina:
                        continue
                    
                    gmina_key = f"{gmina} ({typ_gminy})" if typ_gminy else gmina
                    
                    egzaminy[gmina_key] = {
                        "gmina": gmina,
                        "typ_gminy": typ_gminy,
                        "powiat": powiat,
                        "wojewodztwo": wojewodztwo,
                        "przedmioty": {}
                    }
                    
                    kolumny_przedmiotow = {
                        "polski": (6, 7, 8, 9, 10),
                        "matematyka": (11, 12, 13, 14, 15),
                        "angielski": (16, 17, 18, 19, 20),
                        "francuski": (21, 22, 23, 24, 25),
                        "hiszpanski": (26, 27, 28, 29, 30),
                        "niemiecki": (31, 32, 33, 34, 35),
                        "rosyjski": (36, 37, 38, 39, 40),
                        "wloski": (41, 42, 43, 44, 45)
                    }
                    
                    for przedmiot, (idx_n, idx_s, idx_o, idx_m, idx_mod) in kolumny_przedmiotow.items():
                        przedmiot_data = {
                            "liczba_zdajacych": safe_float(row[idx_n] if idx_n < len(row) else "0"),
                            "srednia": safe_float(row[idx_s] if idx_s < len(row) else "0"),
                            "odchylenie_standardowe": safe_float(row[idx_o] if idx_o < len(row) else "0"),
                            "mediana": safe_float(row[idx_m] if idx_m < len(row) else "0"),
                            "modalna": safe_float(row[idx_mod] if idx_mod < len(row) else "0")
                        }
                        egzaminy[gmina_key]["przedmioty"][przedmiot] = przedmiot_data
            
            if egzaminy:
                print(f"Dane egzaminow wczytane z kodowaniem: {enc}")
                return egzaminy
                    
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            continue
    
    print("Nie udalo sie wczytac pliku egzaminow z zadnym kodowaniem")
    return {}


class EgzaminyDataAccessor:
    """
    Accessor do danych egzaminow po gminach.
    """
    
    def __init__(self, egzaminy_dict: Dict):
        """
        Parameters:
        - egzaminy_dict: slownik danych egzaminow (z load_egzaminy_data)
        """
        self.egzaminy = egzaminy_dict
    
    def get_egzaminy_for_gmina(self, gmina_name: str, typ_gminy: str = "") -> Optional[Dict]:
        """Zwraca dane egzaminow dla danej gminy."""
        if typ_gminy:
            key = f"{gmina_name} ({typ_gminy})"
            if key in self.egzaminy:
                return self.egzaminy[key]
        
        if gmina_name in self.egzaminy:
            return self.egzaminy[gmina_name]
        
        for key, data in self.egzaminy.items():
            if gmina_name.lower() in key.lower():
                return data
        
        return None
    
    def get_srednia_dla_wszystkich_przedmiotow(self, gmina_name: str) -> float:
        """Zwraca srednia wartosc ze wszystkich przedmiotow."""
        egzaminy_data = self.get_egzaminy_for_gmina(gmina_name)
        if not egzaminy_data or not egzaminy_data.get("przedmioty"):
            return 0.0
        
        przedmioty = egzaminy_data["przedmioty"]
        srednias = [p["srednia"] for p in przedmioty.values() if p["srednia"] > 0]
        
        return sum(srednias) / len(srednias) if srednias else 0.0
    
    def get_liczba_zdajacych_total(self, gmina_name: str) -> float:
        """Zwraca srednia liczbe zdajacych ze wszystkich przedmiotow."""
        egzaminy_data = self.get_egzaminy_for_gmina(gmina_name)
        if not egzaminy_data or not egzaminy_data.get("przedmioty"):
            return 0.0
        
        przedmioty = egzaminy_data["przedmioty"]
        liczby = [p["liczba_zdajacych"] for p in przedmioty.values() if p["liczba_zdajacych"] > 0]
        
        return sum(liczby) / len(liczby) if liczby else 0.0
    
    def get_srednie_odchylenie_standardowe(self, gmina_name: str) -> float:
        """Zwraca srednie odchylenie standardowe ze wszystkich przedmiotow."""
        egzaminy_data = self.get_egzaminy_for_gmina(gmina_name)
        if not egzaminy_data or not egzaminy_data.get("przedmioty"):
            return 0.0
        
        przedmioty = egzaminy_data["przedmioty"]
        odchylenia = [p["odchylenie_standardowe"] for p in przedmioty.values() if p["odchylenie_standardowe"] > 0]
        
        return sum(odchylenia) / len(odchylenia) if odchylenia else 0.0
    
    def get_wszystkie_dane_dla_gminy(self, gmina_name: str) -> Dict:
        """Zwraca WSZYSTKIE dostepne dane dla gminy - gotowe do uzytku w fitness_func."""
        egzaminy_data = self.get_egzaminy_for_gmina(gmina_name)
        
        if not egzaminy_data:
            return None
        
        return {
            "gmina_nazwa": egzaminy_data.get("gmina", ""),
            "typ_gminy": egzaminy_data.get("typ_gminy", ""),
            "powiat": egzaminy_data.get("powiat", ""),
            "wojewodztwo": egzaminy_data.get("wojewodztwo", ""),
            
            "srednia_wszystkich_przedmiotow": self.get_srednia_dla_wszystkich_przedmiotow(gmina_name),
            "liczba_zdajacych": self.get_liczba_zdajacych_total(gmina_name),
            "srednie_odchylenie_standardowe": self.get_srednie_odchylenie_standardowe(gmina_name),
            
            "przedmioty": egzaminy_data.get("przedmioty", {})
        }


if __name__ == "__main__":
    print("TEST: EgzaminyDataAccessor")
    print("=" * 60)
    
    data_dir = Path(__file__).resolve().parent / "DATA"
    egzamini_path = data_dir / "E8 - gminy (aktualizacja 07.2025).csv"
    
    print("\n1. Wczytywanie danych egzaminow...")
    egzaminy_data = load_egzaminy_data(egzamini_path)
    print(f"   Zaladowano {len(egzaminy_data)} gmin\n")
    
    print("2. Tworzenie accessor'a...")
    accessor = EgzaminyDataAccessor(egzaminy_data)
    print("   Accessor gotowy\n")
    
    if egzaminy_data:
        first_gmina_key = list(egzaminy_data.keys())[0]
        gmina_name = egzaminy_data[first_gmina_key]["gmina"]
        
        print(f"3. Test dostepu dla gminy: {first_gmina_key}")
        all_data = accessor.get_wszystkie_dane_dla_gminy(gmina_name)
        
        if all_data:
            print(f"   Srednia wynikow: {all_data['srednia_wszystkich_przedmiotow']:.2f}%")
            print(f"   Liczba zdajacych: {all_data['liczba_zdajacych']:.0f}")
            print(f"   Odchylenie standardowe: {all_data['srednie_odchylenie_standardowe']:.2f}%")
            print(f"   Przedmioty dostepne: {list(all_data['przedmioty'].keys())}")
    
    print("\n" + "=" * 60)
    print("TEST ZAKONCZONY POMYSLNIE\n")
