
import streamlit as st
from pdf2image import convert_from_bytes
from PIL import Image
import pytesseract
import pandas as pd
import re
import io

# Funktionen
def extract_data_last_kwh_only(text):
    ident = ""
    address = ""
    for line in text.splitlines():
        match = re.match(r'^\s*(\d{8})([, ]+.+)?$', line)
        if match:
            ident = match.group(1)
            address = match.group(2).strip(" ,") if match.group(2) else ""
            break

    kwh_matches = re.findall(r'([\d.,]+)\s*kWh', text)
    verbrauch_kwh = float(kwh_matches[-1].replace('.', '').replace(',', '.')) if kwh_matches else 0.0

    netto_match = re.findall(r'Nettobetrag\s+([\d.,]+)', text)
    nettobetrag = float(netto_match[0].replace('.', '').replace(',', '.')) if netto_match else 0.0

    preis_kwh = round(nettobetrag / verbrauch_kwh, 4) if verbrauch_kwh else 0.0

    return {
        "Identifikator": ident,
        "Objektadresse": address,
        "Verbrauch (kWh)": round(verbrauch_kwh, 1),
        "Nettobetrag (€)": round(nettobetrag, 2),
        "Preis pro kWh (€)": preis_kwh
    }

def process_pdf(file):
    images = convert_from_bytes(file.read())
    results = []
    for img in images:
        text = pytesseract.image_to_string(img, lang='eng')
        results.append(extract_data_last_kwh_only(text))
    return pd.DataFrame(results)

# Streamlit UI
st.set_page_config(page_title="Stromabrechnungs-Auswertung", layout="centered")
st.title("📄 Stromabrechnungs-Auswertung")

uploaded_file = st.file_uploader("PDF hochladen", type=["pdf"])

if uploaded_file:
    with st.spinner("Analysiere PDF ..."):
        df = process_pdf(uploaded_file)
        st.success("Analyse abgeschlossen!")
        st.dataframe(df)

        # Excel-Export
        excel_data = io.BytesIO()
        df.to_excel(excel_data, index=False, engine='openpyxl')
        excel_data.seek(0)
        st.download_button(
            label="📥 Excel-Datei herunterladen",
            data=excel_data,
            file_name="stromabrechnung_auswertung.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
