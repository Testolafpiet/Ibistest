import os
import time
from flask import Flask, request
import xml.etree.ElementTree as ET
from datetime import datetime

# Register namespaces voor CUFXML
ET.register_namespace('', "x-schema:CufSchema.xml")
ET.register_namespace('Ibis', "http://www.brinkgroep.nl/ibis/xml")

app = Flask(__name__)

# 📂 Map in het project (Azure-compatibel)
WATCH_FOLDER = os.path.join(os.getcwd(), 'olaf_en_piet')

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        lengte = request.form.get('lengte')
        breedte = request.form.get('breedte')

        if not lengte or not breedte:
            return "Lengte en breedte zijn verplicht.", 400

        try:
            file_path = update_cufxml(lengte, breedte)
            return f"CUFXML-bestand aangepast en opgeslagen als:<br><br>{file_path}"
        except Exception as e:
            return f"Fout bij aanmaken van CUFXML: {e}", 500

    return '''
    <!DOCTYPE html>
    <html>
    <head><title>CUFXML Bewerken</title></head>
    <body>
        <h1>Voer lengte en breedte in</h1>
        <form method="POST">
            Lengte: <input name="lengte" required><br><br>
            Breedte: <input name="breedte" required><br><br>
            <button type="submit">Verwerk CUFXML</button>
        </form>
    </body>
    </html>
    '''

def update_cufxml(lengte, breedte):
    # Zoek nieuwste XML-bestand in map
    files = [f for f in os.listdir(WATCH_FOLDER) if f.endswith('.xml')]
    if not files:
        raise FileNotFoundError("Geen XML-bestanden gevonden in de map.")

    latest_file = max(
        [os.path.join(WATCH_FOLDER, f) for f in files],
        key=os.path.getctime
    )

    print(f"[INFO] Bewerkt bestand: {latest_file}")
    tree = ET.parse(latest_file)
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
                raise ValueError("Lengte en breedte moeten getallen zijn.")
            break

    output_filename = f"CUFXML_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
    output_path = os.path.join(WATCH_FOLDER, output_filename)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    return output_filename
