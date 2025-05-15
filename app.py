import os
import io
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template
from datetime import datetime

ET.register_namespace('', "x-schema:CufSchema.xml")
ET.register_namespace('Ibis', "http://www.brinkgroep.nl/ibis/xml")

app = Flask(__name__)

# Gebruik het CUFXML-bestand dat je meestuurt als basis
XML_BASISPAD = os.path.join(os.getcwd(), 'olaf_en_piet', 'CUFXML_20250513_155824.xml')

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        m2 = request.form.get('m2')

        if not m2:
            return "Oppervlakte (m²) is verplicht.", 400

        try:
            download_naam, bestand_in_geheugen = bewerk_cufxml(m2)
            return send_file(
                io.BytesIO(bestand_in_geheugen),
                mimetype='application/xml',
                as_attachment=True,
                download_name=download_naam
            )
        except Exception as e:
            return f"Fout bij genereren van CUFXML: {e}", 500

    return render_template("index.html")

def bewerk_cufxml(m2):
    if not os.path.exists(XML_BASISPAD):
        raise FileNotFoundError("CUFXML-basisbestand niet gevonden.")

    tree = ET.parse(XML_BASISPAD)
    root = tree.getroot()
    ns = {'cuf': 'x-schema:CufSchema.xml'}

    for regel in root.findall('.//cuf:BEGROTINGSREGEL', ns):
        if regel.get('OMSCHRIJVING') == "Vuren Geschaafd 70*170 mm":
            try:
                m2_float = float(m2)
                regel.set('HOEVEELHEID', f"{m2_float:.5f}")
                regel.set('HOEVEELHEID_EENHEID', 'm1')
            except ValueError:
                raise ValueError("m² moet een geldig getal zijn.")
            break

    bestandsnaam = f"CUFXML_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
    xml_stream = io.BytesIO()
    tree.write(xml_stream, encoding='utf-8', xml_declaration=True)
    return bestandsnaam, xml_stream.getvalue()

