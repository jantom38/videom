import pandas as pd

# plik obsługujący ładowanie danych z bazy

def load_description(item_no):
    df = pd.read_excel("dane_z_nav.xlsx", sheet_name="Indeksy")

    foreign = df[df["Item No_"] == item_no]
    if foreign.empty:
        return "nie znaleziono indeksu w bazie"
    foreign = foreign["Assortment Card No_"].values[0]

    df = pd.read_excel("dane_z_nav.xlsx", sheet_name="Opisy")
    wynik = df[df["Assortment Card No_"] == foreign]

    if wynik.empty:
        return "nie znaleziono opisu w bazie"

    opis = " ".join(wynik["Opis Indeksu"].astype(str).dropna())
    return opis

def load_materials(Item_no):
    df = pd.read_excel("dane_z_nav.xlsx", sheet_name="Indeksy")

    foreign = df[df["Item No_"]==Item_no]
    if foreign.empty:
        return "nie znaleziono indeksu w bazie"
    foreign=foreign["Assortment Card No_"].values[0]

    df = pd.read_excel("dane_z_nav.xlsx", sheet_name="Materialy")

    wynik = df[df["Assortment Card No_"]==foreign]

    if wynik.empty:
        return "nie znaleziono materiału w bazie"

    opis = " ".join(wynik["Material"].astype(str).dropna())
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

# This block will only run when you execute `data_load.py` directly
if __name__ == '__main__':
    print("--- Testing data_load.py ---")
