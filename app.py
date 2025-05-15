import os
import io
import xml.etree.ElementTree as ET
from flask import Flask, request, send_file, render_template_string
from datetime import datetime

ET.register_namespace('', "x-schema:CufSchema.xml")
ET.register_namespace('Ibis', "http://www.brinkgroep.nl/ibis/xml")

app = Flask(__name__)

# 📁 Map met XML-bestanden (bij deployment in GitHub)
XML_FOLDER = os.path.join(os.getcwd(), 'olaf_en_piet')

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        lengte = request.form.get('lengte')
        breedte = request.form.get('breedte')

        if not lengte or not breedte:
            return "Lengte en breedte zijn verplicht.", 400

        try:
            download_filename, xml_bytes = generate_cufxml(lengte, breedte)
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

def generate_cufxml(lengte, breedte):
    # Zoek nieuwste bestand in de map
    files = [f for f in os.listdir(XML_FOLDER) if f.endswith('.xml')]
    if not files:
        raise FileNotFoundError("Geen CUFXML-bestanden gevonden.")

    latest_file = max(
        [os.path.join(XML_FOLDER, f) for f in files],
        key=os.path.getctime
    )

    tree = ET.parse(latest_file)
    root = tree.getroot()

    ns = {'cuf': 'x-schema:CufSchema.xml'}

    for regel in root.findall('.//cuf:BEGROTINGSREGEL', ns):
        if regel.get('OMSCHRIJVING') == "Vuren Geschaafd 70*170 mm":
            lengte_f = float(lengte)
            breedte_f = float(breedte)
            totaal = lengte_f * breedte_f
            regel.set('HOEVEELHEID', f"{totaal:.5f}")
            regel.set('HOEVEELHEID_EENHEID', 'm1')
            break

    # Bestandnaam
    filename = f"CUFXML_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"

    # In-memory opslag (geen disk)
    xml_bytes_io = io.BytesIO()
    tree.write(xml_bytes_io, encoding='utf-8', xml_declaration=True)
    return filename, xml_bytes_io.getvalue()

