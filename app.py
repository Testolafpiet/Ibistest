import os
import subprocess
import time
from flask import Flask, render_template, request
import xml.etree.ElementTree as ET
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread
from datetime import datetime

ET.register_namespace('', "x-schema:CufSchema.xml")
ET.register_namespace('Ibis', "http://www.brinkgroep.nl/ibis/xml")

app = Flask(__name__)

# Constants
INPUT_FILE = 'CUF_bewerkt_20250507_135254.xml'
WATCH_FOLDER = r'C:\Users\Pim Mooten\Bouwbedrijf Leiden\Alle projecten - General\Olaf en Piet'
IBIS_EXECUTABLE = r'C:\Program Files\Ibis\Ibis Calculeren voor Bouw\IbisCalculeren.exe'

def start_ibis(file_path):
    if not os.path.exists(IBIS_EXECUTABLE):
        print(f"[FOUT] Ibis niet gevonden: {IBIS_EXECUTABLE}")
        return
    if not os.path.exists(file_path):
        print(f"[FOUT] CUFXML-bestand niet gevonden: {file_path}")
        return
    try:
        print(f"[INFO] Start IBIS...")
        subprocess.Popen([IBIS_EXECUTABLE])
        time.sleep(5)
        print(f"[INFO] Open bestand in IBIS: {file_path}")
        time.sleep(1)
        subprocess.Popen(f'"{IBIS_EXECUTABLE}" "{file_path}"')
    except Exception as e:
        print(f"[FOUT] Starten van IBIS mislukt: {e}")

class CUFXMLWatcher(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith('.xml'):
            return
        print(f"[DETECT] Nieuw bestand: {event.src_path}")
        start_ibis(event.src_path)

def monitor_folder():
    observer = Observer()
    handler = CUFXMLWatcher()
    observer.schedule(handler, path=WATCH_FOLDER, recursive=False)
    observer.start()
    print("[WATCHING] Mapmonitor gestart...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        lengte = request.form.get('lengte')
        breedte = request.form.get('breedte')

        if not lengte or not breedte:
            return "Lengte en breedte zijn verplicht.", 400

        try:
            file_path = update_cufxml(lengte, breedte)
            return f"CUFXML-bestand aangemaakt en opgeslagen in de map: {file_path}"
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
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"CUFXML-bronbestand niet gevonden: {INPUT_FILE}")

    print(f"[INFO] Verwerk CUFXML met lengte={lengte}, breedte={breedte}")
    tree = ET.parse(INPUT_FILE)
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
                print(f"[UPDATE] HOEVEELHEID aangepast naar {totaal:.5f}")
            except ValueError:
                raise ValueError("Lengte en breedte moeten getallen zijn.")
            break

    output_filename = f"CUFXML_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
    output_path = os.path.join(WATCH_FOLDER, output_filename)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"[UPDATED] CUFXML opgeslagen als: {output_path}")
    return output_path

if __name__ == '__main__':
    Thread(target=monitor_folder).start()
    app.run(debug=True, host='127.0.0.1', port=3030)
