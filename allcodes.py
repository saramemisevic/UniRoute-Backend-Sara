import os

# Sada koristimo tačno ime fajla koji će sadržavati sve tvoje spojene kodove
ime_glavnog_fajla = "all_codes.txt"

# Ovdje govorimo programu koje tačno fascikle (foldere) ne smije ni da pogleda, a kamoli da uđe u njih!
# Ovo je onaj zaštitni mehanizam koji smo maloprije detaljno objašnjavali.
folderi_koje_ignorisemo = ['venv', '__pycache__', 'init-db']

with open(ime_glavnog_fajla, 'w', encoding='utf-8') as glavni_fajl:

    # Program počinje svoju šetnju po tvom projektu
    for trenutni_folder, podfolderi, fajlovi in os.walk('.'):

        # Ovdje radimo jednu jako pametnu stvar: naređujemo programu da odmah izbaci sa svog spiska foldere koje smo gore naveli da ih ignoriše.
        # Na taj način, on fizički neće ni pokušati da kroči u venv ili __pycache__.
        podfolderi[:] = [d for d in podfolderi if d not in folderi_koje_ignorisemo]

        # Sada, za svaki pojedinačni fajl koji program pronađe u sigurnim, dozvoljenim folderima:
        for ime_fajla in fajlovi:

            # Sigurnosno pravilo da ne kopira samog sebe niti naš konačni tekstualni fajl
            if ime_fajla != ime_glavnog_fajla and ime_fajla != "allcodes.py":

                # Gledajući tvoju sliku, naložila sam programu da skuplja Python fajlove (.py), zatim tvoje baze/geopodatke (.geojson) i tvoje Docker konfiguracije (.yml)
                if ime_fajla.endswith('.py') or ime_fajla.endswith('.geojson') or ime_fajla.endswith('.yml'):

                    putanja_do_fajla = os.path.join(trenutni_folder, ime_fajla)

                    # Ispisivanje onog našeg lijepog i preglednog zaglavlja
                    glavni_fajl.write("\n\n") 
                    glavni_fajl.write("=========================================================================\n")
                    glavni_fajl.write(f"SADRŽAJ FAJLA: {putanja_do_fajla}\n")
                    glavni_fajl.write("=========================================================================\n\n")

                    try:
                        with open(putanja_do_fajla, 'r', encoding='utf-8') as kod_fajl:
                            tekst_koda = kod_fajl.read() 
                            glavni_fajl.write(tekst_koda)
                            
                    except Exception as greska:
                        glavni_fajl.write(f"Nažalost, došlo je do greške pri čitanju ovog fajla. Opis greške: {greska}\n")

print("Završeno! Svi tvoji kodovi (bez nepotrebnog smeća iz venv-a) su sada spojeni u fajl 'all_codes.txt'.")