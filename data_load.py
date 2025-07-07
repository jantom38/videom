import pandas as pd


def load_description(item_no):
    df = pd.read_excel("dane_z_nav.xlsx", sheet_name="Indeksy")

    foreign = df[df["Item No_"] == item_no]
    # foreign=foreign["Assortment Card No_"]
    foreign = foreign["Assortment Card No_"].values[0]
    print(foreign)


    df = pd.read_excel("dane_z_nav.xlsx", sheet_name="Opisy")
    wynik = df[df["Assortment Card No_"] == foreign]

    # Jeśli nie znaleziono wyników, zwróć pusty string
    if wynik.empty:
        return "nie znaleziono opisu w bazie"

    # Połącz wszystkie wartości kolumny "Opis Indeksu" w jeden string, oddzielając spacjami
    opis = " ".join(wynik["Opis Indeksu"].astype(str))  # .astype(str) na wypadek wartości nie-tekstowych
    return opis

def load_materials(Item_no):
    df = pd.read_excel("dane_z_nav.xlsx", sheet_name="Indeksy")

    foreign = df[df["Item No_"]==Item_no]
    #foreign=foreign["Assortment Card No_"]
    foreign=foreign["Assortment Card No_"].values[0]
    print(foreign)

    df = pd.read_excel("dane_z_nav.xlsx", sheet_name="Materialy")

    wynik = df[df["Assortment Card No_"]==foreign]

    # Jeśli nie znaleziono wyników, zwróć pusty string
    if wynik.empty:
        return "nie znaleziono opisu w bazie"

    # Połącz wszystkie wartości kolumny "Opis Indeksu" w jeden string, oddzielając spacjami
    opis = " ".join(wynik["Material"].astype(str))  # .astype(str) na wypadek wartości nie-tekstowych
    return opis


def load_names(Item_no):
    df = pd.read_excel("dane_z_nav.xlsx", sheet_name="Indeksy")
    wynik = df[df["Item No_"] == Item_no]

    if wynik.empty:
        return {"PL": "Nie znaleziono produktu", "EN": "Product not found"}

    opis_pl = " ".join(wynik["DescriptionPL"].astype(str).dropna())
    opis_en = " ".join(wynik["DescriptionENU"].astype(str).dropna())

    return {
        "PL": opis_pl if opis_pl else "Brak opisu polskiego",
        "EN": opis_en if opis_en else "Brak opisu angielskiego"
    }

print(load_description("10004"))
