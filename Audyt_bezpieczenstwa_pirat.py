
import json
import sys


KRYTYCZNY = "KRYTYCZNY"
WYSOKI = "WYSOKI"
SREDNI = "SREDNI"


def wczytaj_konfiguracje(sciezka_pliku):
    with open(sciezka_pliku, "r", encoding="utf-8") as plik:
        return json.load(plik)


def sprawdz_magazyny_plikow(config, problemy):
    for magazyn in config.get("magazyny_plikow", []):
        nazwa = magazyn["nazwa"]

        if magazyn.get("publiczny_dostep") is True:
            problemy.append({
                "priorytet": KRYTYCZNY,
                "obszar": "Magazyn plików",
                "opis": f"Magazyn '{nazwa}' jest publicznie dostępny.",
                "rekomendacja": "Wyłączyć publiczny dostęp, ograniczyć go do roli aplikacji."
            })

        if magazyn.get("szyfrowanie") is False:
            problemy.append({
                "priorytet": WYSOKI,
                "obszar": "Magazyn plików",
                "opis": f"Magazyn '{nazwa}' nie ma włączonego szyfrowania.",
                "rekomendacja": "Włączyć szyfrowanie w spoczynku."
            })


def sprawdz_role_iam(config, problemy):
    for rola in config.get("role_iam", []):
        nazwa = rola["nazwa"]
        akcje = rola.get("akcje", [])
        zasoby = rola.get("zasoby", [])

        if "*" in akcje and "*" in zasoby:
            problemy.append({
                "priorytet": KRYTYCZNY,
                "obszar": "IAM",
                "opis": f"Rola '{nazwa}' ma nieograniczone uprawnienia.",
                "rekomendacja": "Ograniczyć rolę do konkretnych akcji i zasobów (least privilege)."
            })
        elif "*" in akcje:
            problemy.append({
                "priorytet": WYSOKI,
                "obszar": "IAM",
                "opis": f"Rola '{nazwa}' ma dostęp do wszystkich akcji.",
                "rekomendacja": "Sprecyzować listę dozwolonych akcji."
            })


def sprawdz_mfa_administratorow(config, problemy):
    for konto in config.get("konta_administracyjne", []):
        login = konto["login"]

        if konto.get("mfa_wlaczone") is False:
            problemy.append({
                "priorytet": KRYTYCZNY,
                "obszar": "Uwierzytelnianie",
                "opis": f"Konto administracyjne '{login}' nie ma włączonego MFA.",
                "rekomendacja": "Wymusić MFA dla wszystkich kont z dostępem do panelu administracyjnego."
            })


def sprawdz_bazy_danych(config, problemy):
    for baza in config.get("bazy_danych", []):
        nazwa = baza["nazwa"]

        if baza.get("szyfrowanie_w_spoczynku") is False:
            problemy.append({
                "priorytet": WYSOKI,
                "obszar": "Baza danych",
                "opis": f"Baza '{nazwa}' nie ma włączonego szyfrowania w spoczynku.",
                "rekomendacja": "Włączyć szyfrowanie (envelope encryption)."
            })

        if baza.get("publicznie_dostepna") is True:
            problemy.append({
                "priorytet": KRYTYCZNY,
                "obszar": "Baza danych",
                "opis": f"Baza '{nazwa}' jest dostępna publicznie.",
                "rekomendacja": "Ograniczyć dostęp wyłącznie do serwerów aplikacyjnych."
            })


def sprawdz_segmentacje_sieci(config, problemy):
    polaczenia = config.get("polaczenia_sieciowe", {})

    if polaczenia.get("panel_admin_dostepny_z_internetu") is True:
        problemy.append({
            "priorytet": WYSOKI,
            "obszar": "Segmentacja sieci",
            "opis": "Panel administracyjny jest dostępny z internetu.",
            "rekomendacja": "Ograniczyć dostęp do VPN lub konkretnych adresów IP."
        })

    if polaczenia.get("tls_wymuszony") is False:
        problemy.append({
            "priorytet": KRYTYCZNY,
            "obszar": "Szyfrowanie",
            "opis": "TLS nie jest wymuszony dla komunikacji sieciowej.",
            "rekomendacja": "Wymusić TLS/HTTPS dla całej komunikacji."
        })


def uruchom_audyt(sciezka_pliku):
    config = wczytaj_konfiguracje(sciezka_pliku)
    problemy = []

    sprawdz_magazyny_plikow(config, problemy)
    sprawdz_role_iam(config, problemy)
    sprawdz_mfa_administratorow(config, problemy)
    sprawdz_bazy_danych(config, problemy)
    sprawdz_segmentacje_sieci(config, problemy)

    return config, problemy


def wypisz_raport(config, problemy):
    print("=" * 70)
    print(f"RAPORT AUDYTU BEZPIECZEŃSTWA - {config.get('nazwa_firmy', '?')}")
    print("=" * 70)
    print()

    if not problemy:
        print("Nie wykryto żadnych problemów. Konfiguracja zgodna z zasadami.")
        return

    kolejnosc_priorytetow = [KRYTYCZNY, WYSOKI, SREDNI]
    liczba_wedlug_priorytetu = {p: 0 for p in kolejnosc_priorytetow}

    for problem in problemy:
        liczba_wedlug_priorytetu[problem["priorytet"]] += 1

    print("Podsumowanie:")
    for priorytet in kolejnosc_priorytetow:
        print(f"  {priorytet}: {liczba_wedlug_priorytetu[priorytet]}")
    print()

    print("Szczegóły:")
    print("-" * 70)

    for priorytet in kolejnosc_priorytetow:
        problemy_danego_priorytetu = [p for p in problemy if p["priorytet"] == priorytet]
        for problem in problemy_danego_priorytetu:
            print(f"[{problem['priorytet']}] {problem['obszar']}")
            print(f"  Problem:        {problem['opis']}")
            print(f"  Rekomendacja:   {problem['rekomendacja']}")
            print()


if __name__ == "__main__":
    sciezka = sys.argv[1] if len(sys.argv) > 1 else "pirat_config.json"

    try:
        config, problemy = uruchom_audyt(sciezka)
        wypisz_raport(config, problemy)
    except FileNotFoundError:
        print(f"Nie znaleziono pliku konfiguracyjnego: {sciezka}")
    except json.JSONDecodeError:
        print(f"Plik {sciezka} nie jest prawidłowym plikiem JSON.")
