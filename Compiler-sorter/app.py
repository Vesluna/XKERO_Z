import os
import re
import shutil
import zipfile
from pathlib import Path
from flask import Flask, render_template, request, send_file, jsonify, send_from_directory

app = Flask(__name__)
app.secret_key = "xkero_z_secure_token_2026"

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'processed'
SAMPLE_WORKSPACE = os.path.join('static', 'custom_samples')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(SAMPLE_WORKSPACE, exist_ok=True)

# ---------------------------------------------------------------------------
# INSTRUMENT TAXONOMY
# Used by the Compiler-Sorter to classify audio files into folders.
# ---------------------------------------------------------------------------
INSTRUMENT_TAXONOMY = {
    "Strings": {
        "Acoustic Guitar": ["acousticguitar", "acguitar", "steelstring", "nylonstring", "acousticgtr"],
        "Electric Guitar": ["electricguitar", "eguitar", "cleangtr", "distortedguitar", "overdrivegtr", "egtr", "leadgtr"],
        "Bass Guitar": ["bassguitar", "electricbass", "pickedbass", "fingeredbass", "fretlessbass", "ebass", "slapbass"],
        "Violin": ["violin", "stradivarius", "fiddle", "violins"],
        "Viola": ["viola", "violas"],
        "Cello": ["cello", "violoncello", "cellos"],
        "Double Bass": ["doublebass", "contrabass", "uprightbass", "standupbass"],
        "Harp": ["harp", "lyre"],
        "Banjo": ["banjo", "banjos"],
        "Mandolin": ["mandolin", "mandoline"],
        "Ukulele": ["ukulele", "uku", "uke"],
        "Generic Strings": ["strings", "stringensemble", "orchestralstrings", "staccatostrings", "pizzicato", "arco", "synthstrings"],
    },
    "Woodwinds": {
        "Flute": ["flute", "piccolo", "panflute", "panpipes", "westernflute", "shakuhachi"],
        "Oboe": ["oboe", "englishhorn", "hautbois"],
        "Clarinet": ["clarinet", "bassclarinet"],
        "Bassoon": ["bassoon", "contrabassoon"],
        "Saxophone": ["saxophone", "sax", "altosax", "tenorsax", "barisax", "sopranosax"],
        "Recorder": ["recorder", "whistle", "tinwhistle", "lowwhistle", "ocarina"],
        "Generic Woodwinds": ["woodwind", "reed", "windinstrument", "woodwinds"],
    },
    "Brass": {
        "Trumpet": ["trumpet", "cornet", "flugelhorn", "piccolotrumpet"],
        "Trombone": ["trombone", "basstrombone", "valvetrombone"],
        "Tuba": ["tuba", "sousaphone", "euphonium"],
        "French Horn": ["frenchhorn", "horn", "orchestralhorn", "horns"],
        "Generic Brass": ["brass", "brasssection", "brasshorns", "brassensemble", "hornsection", "stabs"],
    },
    "Percussion & Drums": {
        "Kick Drum": ["kick", "bassdrum", "kickdrum", "bdrum", "subkick", "punch"],
        "Snare Drum": ["snare", "snaredrum", "sdrum", "rimshot", "rim", "ghostnote"],
        "Hi-Hat": ["hihat", "hats", "openhat", "closedhat", "cymbalhat", "pedalhat"],
        "Tom Tom": ["tom", "tomtom", "floortom", "racktom", "toms"],
        "Cymbals": ["cymbal", "crash", "ride", "splash", "chinacym", "gong", "cymbals"],
        "Clap & Snap": ["clap", "handclap", "snap", "fingersnap", "claps"],
        "Cowbell": ["cowbell", "woodblock", "agogobell", "jamblock"],
        "Timpani": ["timpani", "kettledrum", "timp"],
        "Latin Percussion": ["conga", "bongo", "timbale", "cajon", "djembe", "cuica", "clave"],
        "Shakers & Toys": ["shaker", "cabasa", "maraca", "tambourine", "guiro", "triangleperc"],
        "Electronic Drums": ["808", "909", "707", "linndrum", "electronicperc", "synthdrum", "drummachine"],
    },
    "Chromatic & Mallets": {
        "Bells": ["bell", "bells", "glockenspiel", "tubularbells", "handbells", "carillon", "orchestralbells", "agogo", "jingle"],
        "Chimes": ["chime", "chimes", "windchimes", "barchimes"],
        "Marimba & Xylophone": ["marimba", "xylophone", "vibraphone", "balafon", "xylo", "vibes"],
        "Music Box": ["musicbox", "spieluhr", "lullaby"],
    },
    "Keyboards & Synths": {
        "Acoustic Piano": ["piano", "grandpiano", "uprightpiano", "pianoloop", "fortepiano", "keys"],
        "Electric Piano": ["electricpiano", "rhodes", "wurlitzer", "epiano", "clavinet", "dx7piano"],
        "Organ": ["organ", "hammond", "churchorgan", "pipeorgan", "b3organ", "reedorgan"],
        "Harpsichord": ["harpsichord", "clavin", "cembalo"],
        "Accordion": ["accordion", "harmonica", "melodica", "concertina"],
        "Synth Leads": ["lead", "synthlead", "monolead", "sawlead", "squarelead", "glide"],
        "Synth Pads": ["pad", "synthpad", "ambientpad", "stringpad", "atmosphere", "pads"],
        "Synth Plucks": ["pluck", "synthpluck", "staccatosynth", "plucks", "malletsynth"],
        "Synth Bass": ["synthbass", "subbass", "sub", "wobblebass", "acidbass", "303", "reese", "808bass", "donk"],
        "Chiptune & Waves": ["chiptune", "nes", "gameboy", "squarewave", "sawwave", "trianglewave", "sinewave", "pulsewave", "noise", "2bit", "4bit", "8bit", "16bit", "waveform", "sid", "ym2612", "chipping"],
        "Mellotron": ["mellotron", "stringsynth", "tronflute"],
    },
    "World & Traditional": {
        "Sitar & Tanpura": ["sitar", "tanpura", "tambura"],
        "Koto & Shamisen": ["koto", "shamisen", "guzheng"],
        "Oud & Lute": ["oud", "lute", "pipa", "bouzouki"],
        "Bagpipes": ["bagpipe", "bagpipes", "uilleann"],
        "Didgeridoo": ["didgeridoo", "didge"],
        "Kalimba": ["kalimba", "thumbpiano", "mbira"],
    },
    "Vocals": {
        "Choir": ["choir", "chorus", "gospelchoir", "vocalensemble", "chants", "gregorian"],
        "Vocal Loops": ["vocalloop", "acapella", "vocalphrase", "vocalhook", "vocalchop"],
        "Vocal FX": ["vocalfx", "chant", "adlib", "grunt", "shout", "vox", "beatbox", "breath"],
    },
    "Foley & Environment": {
        "Nature Elements": ["rain", "wind", "thunder", "water", "ocean", "birds", "fire", "stream"],
        "Footsteps": ["footsteps", "walk", "run", "gravel", "concrete"],
        "Mechanical & Tech": ["glitch", "click", "ui", "button", "computer", "machine", "servo"],
        "Vinyl & LoFi": ["vinyl", "crackle", "cassette", "tapehiss", "lofi"],
    },
    "Sound Design & FX": {
        "Cinematic FX": ["impact", "hit", "boom", "subdrop", "explosion", "subhit", "braam"],
        "Transitions": ["riser", "rise", "fall", "downlifter", "sweep", "whoosh", "transition", "uplifter", "swoosh"],
        "Textures": ["drone", "texture", "noisefloor", "ambientfx", "atmospherefx", "soundscape"],
    },
}

# Build a flat keyword lookup list sorted by keyword length (longest first)
# to ensure more specific matches take priority.
KEYWORD_LOOKUP = []
for _category, _folders in INSTRUMENT_TAXONOMY.items():
    for _folder_name, _keywords in _folders.items():
        for _kw in _keywords:
            KEYWORD_LOOKUP.append((_kw.lower(), _category, _folder_name))
KEYWORD_LOOKUP.sort(key=lambda x: len(x[0]), reverse=True)


def find_matching_instrument(name: str, strict_mode: bool = False):
    """Return (category, folder_name) for the best keyword match, or (None, None)."""
    if strict_mode:
        clean_name = re.sub(r'[^a-z0-9\s]', ' ', name.lower())
        words = set(clean_name.split())
    else:
        clean_name = re.sub(r'[^a-z0-9]', '', name.lower())

    for keyword, category, folder_name in KEYWORD_LOOKUP:
        if strict_mode:
            if keyword in words or keyword in clean_name:
                return category, folder_name
        else:
            if keyword in clean_name:
                return category, folder_name
    return None, None


def extract_nested_zips(directory: str, action: str):
    """Recursively handle nested zip files inside an extracted directory."""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.zip'):
                zip_path = os.path.join(root, file)
                if action == "delete":
                    try:
                        os.remove(zip_path)
                    except OSError:
                        pass
                elif action == "sort":
                    extract_dir = os.path.join(root, file[:-4] + '_nested_extracted')
                    os.makedirs(extract_dir, exist_ok=True)
                    try:
                        with zipfile.ZipFile(zip_path, 'r') as inner_ref:
                            inner_ref.extractall(extract_dir)
                    except (zipfile.BadZipFile, OSError):
                        pass
                    try:
                        os.remove(zip_path)
                    except OSError:
                        pass
                    extract_nested_zips(extract_dir, action)


def process_audio_library(extract_path: str, target_path: str, settings: dict) -> int:
    """Walk extracted files, classify them, and copy to sorted output directory."""
    all_files = []
    for root, _, files in os.walk(extract_path):
        for file in files:
            all_files.append(os.path.join(root, file))

    processed_count = 0
    for file_path in all_files:
        path_obj = Path(file_path)
        file_name = path_obj.name
        ext = path_obj.suffix.lower()

        # Handle nested zips that were left in place (ignore mode)
        if ext == '.zip' and settings['nested_action'] == 'ignore':
            dest_dir = os.path.join(target_path, "Uncategorized_Zips")
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(file_path, os.path.join(dest_dir, file_name))
            continue

        # SF2 soundfonts — optionally alphabetize
        if ext == '.sf2':
            if settings['sort_sf2']:
                first_char = file_name[0].upper()
                if not first_char.isalpha():
                    first_char = '#'
                dest_dir = os.path.join(target_path, "SF2 Files", first_char)
            else:
                dest_dir = os.path.join(target_path, "SF2 Files")
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(file_path, os.path.join(dest_dir, file_name))
            processed_count += 1
            continue

        # Audio files — classify by filename then by parent folder name
        if ext in ['.wav', '.mp3', '.flac', '.aiff', '.ogg']:
            category, folder_name = find_matching_instrument(file_name, settings['strict_mode'])
            if not folder_name:
                category, folder_name = find_matching_instrument(
                    path_obj.parent.name, settings['strict_mode']
                )

            if category and folder_name:
                dest_dir = os.path.join(target_path, category, folder_name)
            elif settings['isolate_misc']:
                dest_dir = os.path.join(target_path, "Miscellaneous")
            else:
                dest_dir = os.path.join(target_path, "Uncategorized")

            os.makedirs(dest_dir, exist_ok=True)
            # Avoid overwriting files with identical names from different folders
            dest_file = os.path.join(dest_dir, file_name)
            if os.path.exists(dest_file):
                stem = path_obj.stem
                suffix = path_obj.suffix
                counter = 1
                while os.path.exists(dest_file):
                    dest_file = os.path.join(dest_dir, f"{stem}_{counter}{suffix}")
                    counter += 1
            shutil.copy2(file_path, dest_file)
            processed_count += 1

    return processed_count


# ---------------------------------------------------------------------------
# ROUTES — Navigation
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    """Main UltraBox companion page."""
    return render_template('ultrabox.html')


@app.route('/compiler')
def compiler_page():
    """Audio library compiler / sorter tool."""
    return render_template('index.html')


# ---------------------------------------------------------------------------
# ROUTE — Sample Import Pipeline (for the UltraBox companion page)
# ---------------------------------------------------------------------------

@app.route('/api/import-samples', methods=['POST'])
def import_samples():
    """
    Accept a sorted ZIP from the compiler, extract audio files (not SF2),
    and make them available to the companion sequencer via static URLs.
    Returns a JSON manifest of all imported samples.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file received."}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "Empty filename."}), 400

    try:
        temp_zip = os.path.join(UPLOAD_FOLDER, "temp_import.zip")
        file.save(temp_zip)

        if not zipfile.is_zipfile(temp_zip):
            return jsonify({"error": "File is not a valid ZIP archive."}), 400

        # Wipe previous custom sample workspace
        if os.path.exists(SAMPLE_WORKSPACE):
            shutil.rmtree(SAMPLE_WORKSPACE)
        os.makedirs(SAMPLE_WORKSPACE, exist_ok=True)

        imported_manifest: dict = {}
        audio_exts = {'.wav', '.mp3', '.flac', '.aiff', '.ogg'}

        with zipfile.ZipFile(temp_zip, 'r') as archive:
            for member in archive.namelist():
                # Skip macOS metadata entries and directories
                if member.startswith('__MACOSX') or member.endswith('/'):
                    continue

                filename = os.path.basename(member)
                if not filename:
                    continue

                ext = os.path.splitext(filename)[1].lower()
                if ext not in audio_exts:
                    continue

                # Preserve category/instrument hierarchy from sorted ZIP structure
                parts = Path(member).parts
                category = parts[0] if len(parts) > 1 else "Unsorted"
                instrument = parts[1] if len(parts) > 2 else "Default"

                target_dir = os.path.join(SAMPLE_WORKSPACE, category, instrument)
                os.makedirs(target_dir, exist_ok=True)

                target_path = os.path.join(target_dir, filename)
                # Handle name collisions
                if os.path.exists(target_path):
                    stem, sfx = os.path.splitext(filename)
                    c = 1
                    while os.path.exists(target_path):
                        target_path = os.path.join(target_dir, f"{stem}_{c}{sfx}")
                        c += 1

                with archive.open(member) as src, open(target_path, 'wb') as dst:
                    shutil.copyfileobj(src, dst)

                web_path = f"/static/custom_samples/{category}/{instrument}/{os.path.basename(target_path)}"
                imported_manifest.setdefault(category, {}).setdefault(instrument, []).append({
                    "name": os.path.basename(target_path),
                    "url": web_path,
                })

        try:
            os.remove(temp_zip)
        except OSError:
            pass

        return jsonify({
            "status": "success",
            "msg": f"Imported {sum(len(v) for cat in imported_manifest.values() for v in cat.values())} audio files. SF2 files were skipped.",
            "manifest": imported_manifest,
        }), 200

    except Exception as exc:
        return jsonify({"error": f"Import failed: {exc}"}), 500


# ---------------------------------------------------------------------------
# ROUTES — Compiler API
# ---------------------------------------------------------------------------

@app.route('/upload', methods=['POST'])
def upload_file():
    """Receive a ZIP, sort its audio files, and return a download link."""
    settings = {
        'strict_mode': request.form.get('strict_mode') == 'on',
        'sort_sf2': request.form.get('sort_sf2') == 'on',
        'isolate_misc': request.form.get('isolate_misc') == 'on',
        'nested_action': request.form.get('nested_action', ''),
        'ignore_warnings': request.form.get('ignore_warnings') == 'true',
    }

    if 'file' not in request.files:
        return jsonify({"error": "No file attached.", "critical": True}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "No file selected.", "critical": True}), 400

    try:
        filename = os.path.basename(file.filename)
        base_name = filename.rsplit('.', 1)[0]

        zip_path = os.path.join(UPLOAD_FOLDER, filename)
        extract_dir = os.path.join(UPLOAD_FOLDER, f"ext_{base_name}")
        sort_dir = os.path.join(OUTPUT_FOLDER, f"sort_{base_name}")
        output_zip_base = os.path.join(OUTPUT_FOLDER, f"Sorted_{base_name}")

        file.save(zip_path)

        if not zipfile.is_zipfile(zip_path):
            os.remove(zip_path)
            return jsonify({"error": "Uploaded file is not a valid ZIP archive.", "critical": True}), 400

        # Check for nested zips and warn if no action has been chosen yet
        if not settings['nested_action']:
            with zipfile.ZipFile(zip_path, 'r') as scan_ref:
                nested_zips = [f for f in scan_ref.namelist() if f.lower().endswith('.zip')]
                if nested_zips and not settings['ignore_warnings']:
                    return jsonify({
                        "status": "nested_warning",
                        "msg": (
                            f"Found {len(nested_zips)} nested ZIP file(s) inside the archive. "
                            "Choose an action: Sort (extract & classify), Delete (remove them), "
                            "or Ignore (copy as-is)."
                        ),
                    }), 200
                elif nested_zips:
                    settings['nested_action'] = 'ignore'

        # Extract main archive
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Handle nested zips
        if settings['nested_action'] in ('delete', 'sort'):
            extract_nested_zips(extract_dir, settings['nested_action'])

        # Sort files
        if os.path.exists(sort_dir):
            shutil.rmtree(sort_dir)
        processed_count = process_audio_library(extract_dir, sort_dir, settings)

        # Clean up extraction temp
        shutil.rmtree(extract_dir, ignore_errors=True)

        if processed_count == 0 and not settings['ignore_warnings']:
            shutil.rmtree(sort_dir, ignore_errors=True)
            return jsonify({
                "status": "soft_error",
                "msg": "No recognizable audio or SF2 files were found in the archive. Force continue anyway?",
            }), 200

        # Package sorted output
        shutil.make_archive(output_zip_base, 'zip', sort_dir)
        os.remove(zip_path)

        return jsonify({
            "status": "success",
            "download_url": f"/download/Sorted_{base_name}.zip",
            "browse_id": f"sort_{base_name}",
            "processed_count": processed_count,
        }), 200

    except Exception as exc:
        return jsonify({"error": f"Compiler error: {exc}", "critical": True}), 500


@app.route('/download/<filename>')
def download_file(filename):
    """Serve a processed ZIP for download."""
    safe_name = os.path.basename(filename)
    file_path = os.path.join(OUTPUT_FOLDER, safe_name)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found."}), 404
    return send_file(file_path, as_attachment=True)


@app.route('/api/explore/<browse_id>')
def explore_folder(browse_id):
    """Return a JSON tree of the sorted output folder for the file explorer."""
    safe_id = os.path.basename(browse_id)
    target_dir = os.path.join(OUTPUT_FOLDER, safe_id)
    if not os.path.exists(target_dir):
        return jsonify({"error": "Folder not found."}), 404

    def build_tree(path: str) -> dict:
        node = {"name": os.path.basename(path), "children": []}
        try:
            items = sorted(os.listdir(path))
        except OSError:
            return node
        for item in items:
            full = os.path.join(path, item)
            if os.path.isdir(full):
                node["children"].append(build_tree(full))
            else:
                rel = os.path.relpath(full, OUTPUT_FOLDER).replace('\\', '/')
                node["children"].append({"name": item, "type": "file", "path": rel})
        return node

    return jsonify(build_tree(target_dir))


@app.route('/play/<path:filepath>')
def play_audio(filepath):
    """Stream an audio file from the processed output folder."""
    # Prevent path traversal
    safe_path = os.path.normpath(filepath).lstrip('/')
    return send_from_directory(OUTPUT_FOLDER, safe_path)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
