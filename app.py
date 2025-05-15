import os
import io
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file
from datetime import datetime

# Register namespaces
ET.register_namespace('', "x-schema:CufSchema.xml")
ET.register_namespace('Ibis', "http://www.brinkgroep.nl/ibis/xml")

app = Flask(__name__)

# 📌 Specifiek bestand dat altijd bewerkt wordt
XML_FILE_PATH = os.path.join(os.getcwd(), 'olaf_en_piet', 'CUFXML_20250513_155824.xml')

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        lengte = request.form.get('lengte')
        breedte = request.form.get('breedte')

        if not lengte or not breedte:
            return "Lengte en breedte zijn verplicht.", 400

        try:
            download_filename, xml_bytes = bewerk_cufxml(lengte, breedte)
            return send_file(
                io.BytesIO(xml_bytes),
                mimetype='application/xml',
                as_attachment=True,
                download_name=download_filename
            )
        except Exception as e:
            return f"Fout bij genereren van CUFXML: {e}", 500

    return '''
    <!DOCTYPE html>
    <html>
    <head><title>CUFXML Bewerken</title></head>
    <body>
        <h1>Voer lengte en breedte in</h1>
        <form method="POST">
            Lengte: <input name="lengte" required><br><br>
            Breedte: <input name="breedte" required><br><br>
            <button type="submit">Download CUFXML</button>
        </form>
    </body>
    </html>
    '''

def bewerk_cufxml(lengte, breedte):
    if not os.path.exists(XML_FILE_PATH):
        raise FileNotFoundError("CUFXML-bestand niet gevonden.")

    tree = ET.parse(XML_FILE_PATH)
    root = tree.getroot()

    ns = {'cuf': 'x-schema:CufSchema.xml'}

    for regel in root.findall('.//cuf:BEGROTINGSREGEL', ns):
        if regel.get('OMSCHRIJVING') == "Vuren Geschaafd 70*170 mm":
            try:
                lengte_f = float(lengte)
                breedte_f = float(breedte)
                totaal = lengte_f * breedte_f
                regel.set('HOEVEELHEID', f"{totaal:.5f}")
                regel.set('HOEVEELHEID_EENHEID', 'm1')
            except ValueError:
                raise ValueError("Lengte en breedte moeten numeriek zijn.")
            break

    # Downloadnaam dynamisch
    filename = f"CUFXML_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"

    # Opslaan in-memory (geen disk!)
    xml_io = io.BytesIO()
    tree.write(xml_io, encoding='utf-8', xml_declaration=True)
    return filename, xml_io.getvalue()

