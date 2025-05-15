import os
import io
import xml.etree.ElementTree as ET
from flask import Flask, request, render_template
from datetime import datetime
import pyodbc

ET.register_namespace('', "x-schema:CufSchema.xml")
ET.register_namespace('Ibis', "http://www.brinkgroep.nl/ibis/xml")

app = Flask(__name__)

XML_BASISPAD = os.path.join(os.getcwd(), 'olaf_en_piet', 'CUFXML_20250513_155824.xml')

# 🔧 Jouw databaseverbinding (PAS AAN met jouw gegevens)
conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=tcp:JOUWSERVER.database.windows.net,1433;"
    "Database=JOUW_DATABASE;"
    "Uid=JOUWGEBRUIKER;"
    "Pwd=JOUWWACHTWOORD;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        m2 = request.form.get('m2')

        if not m2:
            return "Oppervlakte (m²) is verplicht.", 400

        try:
            bestand_naam, xml_tekst = genereer_cufxml(m2)
            sla_op_in_sql(bestand_naam, xml_tekst)
            return f"✅ CUFXML-bestand <strong>{bestand_naam}</strong> is opgeslagen in de database."
        except Exception as e:
            return f"❌ Fout bij genereren of opslaan: {e}", 500

    return render_template("index.html")

def genereer_cufxml(m2):
    if not os.path.exists(XML_BASISPAD):
        raise FileNotFoundError("CUFXML-basisbestand niet gevonden.")

    tree = ET.parse(XML_BASISPAD)
    root = tree.getroot()
    ns = {'cuf': 'x-schema:CufSchema.xml'}

    for regel in root.findall('.//cuf:BEGROTINGSREGEL', ns):
        if regel.get('OMSCHRIJVING') == "Vuren Geschaafd 70*170 mm":
            regel.set('HOEVEELHEID', f"{float(m2):.5f}")
            regel.set('HOEVEELHEID_EENHEID', 'm1')
            break

    bestandsnaam = f"CUFXML_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
    xml_io = io.BytesIO()
    tree.write(xml_io, encoding='utf-8', xml_declaration=True)
    return bestandsnaam, xml_io.getvalue().decode('utf-8')

def sla_op_in_sql(bestandsnaam, xml_string):
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO CUFXML_Bestanden (naam, inhoud) 
            VALUES (?, ?)
        """, bestandsnaam, xml_string)
        conn.commit()

