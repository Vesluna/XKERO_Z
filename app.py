import os
import re
import shutil
import zipfile
import uuid
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
    "Guitars": {
        "Acoustic Guitar": ["acousticguitar", "acguitar", "steelstring", "nylonstring", "acousticgtr"],
        "Electric Guitar": ["electricguitar", "eguitar", "cleangtr", "distortedguitar", "overdrivegtr", "egtr", "leadgtr", "powerchord", "guitarelectric", "metalguitar", "sillyguitar"],
        "Bass Guitar": ["bassguitar", "electricbass", "pickedbass", "fingeredbass", "fretlessbass", "ebass", "slapbass", "bass", "subbass"],
        "Generic Guitar": ["guitar", "gtr", "guitarspacechord", "guitarspaceichord", "guitarspacevchord", "guitarvchord", "guitarslap", "stealthpilot guitar"],
    },
    "Strings": {
        "Violin": ["violin", "stradivarius", "fiddle", "violins", "violinpizzicato"],
        "Viola": ["viola", "violas"],
        "Cello": ["cello", "violoncello", "cellos", "pizzicato", "cellopizzicato"],
        "Double Bass": ["doublebass", "contrabass", "uprightbass", "standupbass"],
        "Harp": ["harp", "lyre", "celticharp"],
        "Banjo": ["banjo", "banjos"],
        "Mandolin": ["mandolin", "mandoline"],
        "Ukulele": ["ukulele", "uku", "uke"],
        "Generic Strings": ["strings", "stringensemble", "orchestralstrings", "staccatostrings", "pizzicato", "arco", "synthstrings", "string"],
    },
    "Woodwinds": {
        "Flute": ["flute", "piccolo", "panflute", "panpipes", "westernflute", "shakuhachi", "flutesound"],
        "Oboe": ["oboe", "englishhorn", "hautbois"],
        "Clarinet": ["clarinet", "bassclarinet"],
        "Bassoon": ["bassoon", "contrabassoon"],
        "Saxophone": ["saxophone", "sax", "altosax", "tenorsax", "barisax", "sopranosax"],
        "Recorder": ["recorder", "whistle", "tinwhistle", "lowwhistle", "ocarina"],
        "Generic Woodwinds": ["woodwind", "reed", "windinstrument", "woodwinds"],
    },
    "Brass": {
        "Trumpet": ["trumpet", "cornet", "flugelhorn", "piccolotrumpet", "tr", "trumpet"],
        "Trombone": ["trombone", "basstrombone", "valvetrombone", "trombone"],
        "Tuba": ["tuba", "sousaphone", "euphonium"],
        "French Horn": ["frenchhorn", "horn", "orchestralhorn", "horns"],
        "Generic Brass": ["brass", "brasssection", "brasshorns", "brassensemble", "hornsection", "stabs", "brassstab", "brasstone", "bigband"],
    },
    "Percussion & Drums": {
        "Kick Drum": ["kick", "bassdrum", "kickdrum", "bdrum", "subkick", "punch", "bd", "kick_orchestra_hit", "tom_kick"],
        "Snare Drum": ["snare", "snaredrum", "sdrum", "rimshot", "rim", "ghostnote", "sd", "snare_cymbal", "snare_drum"],
        "Hi-Hat": ["hihat", "hats", "openhat", "closedhat", "cymbalhat", "pedalhat", "hat", "hi_hat"],
        "Tom Tom": ["tom", "tomtom", "floortom", "racktom", "toms"],
        "Cymbals": ["cymbal", "crash", "ride", "splash", "chinacym", "gong", "cymbals", "reverse_cymbal", "low_cymbal"],
        "Clap & Snap": ["clap", "handclap", "snap", "fingersnap", "claps"],
        "Cowbell": ["cowbell", "woodblock", "agogobell", "jamblock"],
        "Timpani": ["timpani", "kettledrum", "timp"],
        "Latin Percussion": ["conga", "bongo", "timbale", "cajon", "djembe", "cuica", "clave", "bongohigh", "bongolow"],
        "Shakers & Toys": ["shaker", "cabasa", "maraca", "tambourine", "guiro", "triangleperc", "fingercym"],
        "Electronic Drums": ["808", "909", "707", "linndrum", "electronicperc", "synthdrum", "drummachine", "drum", "beat"],
    },
    "Chromatic & Mallets": {
        "Bells": ["bell", "bells", "glockenspiel", "tubularbells", "handbells", "carillon", "orchestralbells", "agogo", "jingle", "tubularbell", "bells", "crystal"],
        "Chimes": ["chime", "chimes", "windchimes", "barchimes"],
        "Marimba & Xylophone": ["marimba", "xylophone", "vibraphone", "balafon", "xylo", "vibes", "icyxylophone"],
        "Music Box": ["musicbox", "spieluhr", "lullaby"],
    },
    "Keyboards & Synths": {
        "Acoustic Piano": ["piano", "grandpiano", "uprightpiano", "pianoloop", "fortepiano", "keys"],
        "Electric Piano": ["electricpiano", "rhodes", "wurlitzer", "epiano", "clavinet", "dx7piano"],
        "Organ": ["organ", "hammond", "churchorgan", "pipeorgan", "b3organ", "reedorgan", "sacattoorgan"],
        "Harpsichord": ["harpsichord", "clavin", "cembalo"],
        "Accordion": ["accordion", "harmonica", "melodica", "concertina"],
        "Synth Leads": ["lead", "synthlead", "monolead", "sawlead", "squarelead", "glide", "rublead"],
        "Synth Pads": ["pad", "synthpad", "ambientpad", "stringpad", "atmosphere", "pads"],
        "Synth Plucks": ["pluck", "synthpluck", "staccatosynth", "plucks", "malletsynth"],
        "Synth Bass": ["synthbass", "subbass", "sub", "wobblebass", "acidbass", "303", "reese", "808bass", "donk", "spitsybass", "moonchargebass"],
        "Chiptune & Waves": ["chiptune", "nes", "gameboy", "squarewave", "sawwave", "trianglewave", "sinewave", "pulsewave", "noise", "2bit", "4bit", "8bit", "16bit", "waveform", "sid", "ym2612", "chipping", "rezsqr"],
        "Mellotron": ["mellotron", "stringsynth", "tronflute"],
        "Generic Synths": ["synth", "synthesizer", "syn", "square synth", "smooth synth", "main synth", "alarm synth", "big synth", "bass synth"],
    },
    "World & Traditional": {
        "Sitar & Tanpura": ["sitar", "tanpura", "tambura"],
        "Koto & Shamisen": ["koto", "shamisen", "guzheng"],
        "Oud & Lute": ["oud", "lute", "pipa", "bouzouki"],
        "Bagpipes": ["bagpipe", "bagpipes", "uilleann", "bagpipesound"],
        "Didgeridoo": ["didgeridoo", "didge"],
        "Kalimba": ["kalimba", "thumbpiano", "mbira"],
    },
    "Vocals": {
        "Choir": ["choir", "chorus", "gospelchoir", "vocalensemble", "chants", "gregorian"],
        "Vocal Loops": ["vocalloop", "acapella", "vocalphrase", "vocalhook", "vocalchop"],
        "Vocal FX": ["vocalfx", "chant", "adlib", "grunt", "shout", "vox", "beatbox", "breath", "ah", "heeyy", "ooh", "ugh", "laugh", "meow", "wooh", "angry", "amazed", "confused", "excited", "hi", "sad", "think", "bye", "shocked", "sleep", "disgust", "faint", "oldman", "duckquack"],
    },
    "Foley & Environment": {
        "Nature Elements": ["rain", "wind", "thunder", "water", "ocean", "birds", "fire", "stream", "halloween thunder", "windflying"],
        "Footsteps": ["footsteps", "walk", "run", "gravel", "concrete", "woodstep", "playersit", "boarddrop", "boardollie", "boardstop"],
        "Mechanical & Tech": ["glitch", "click", "button", "computer", "machine", "servo", "alarm", "beep", "carhorn", "truckengine", "truckhorn", "hydraulic", "levercompressed", "mechanical", "tech", "beepsound", "beeps", "beepsgps"],
        "Vinyl & LoFi": ["vinyl", "crackle", "cassette", "tapehiss", "lofi"],
        "General Noise": ["noise", "static", "hiss", "buzz", "hum"],
    },
    "Sound Design & FX": {
        "Cinematic FX": ["impact", "hit", "boom", "subdrop", "explosion", "subhit", "braam", "orchestrahit", "cinematicboom", "discimpact", "bombexplode"],
        "Transitions": ["riser", "rise", "fall", "downlifter", "sweep", "whoosh", "transition", "uplifter", "swoosh", "reverse"],
        "Textures": ["drone", "texture", "noisefloor", "ambientfx", "atmospherefx", "soundscape"],
        "Game FX": ["laser", "pew", "zap", "katana", "slash", "energy", "lunge", "rocket", "saber", "sword", "ping", "powerup", "gamefx", "pop", "incorrect", "correct", "victory", "death", "die", "ouch", "hurl", "kerplunk", "paint", "splat", "rubberband", "sentryshoot", "shortwhistle", "sticky"],
        "Horror FX": ["horror", "ghost", "scream", "scared", "nightmare", "thunder", "lightning", "evil", "woohh"],
        "Miscellaneous FX": ["boing", "chug", "ching", "thump", "splat", "clunk", "collide", "flashbulb", "glassbreak", "pageturn", "ringtone", "switch", "unsheath", "uuhhh"],
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

# List of keywords that MUST be matched as whole words to avoid false positives
# e.g., 'ui' should not match 'Guitar'
WHOLE_WORD_ONLY = ["ui", "tr", "bd", "ah", "he", "hi", "sd", "sn", "kd"]

def find_matching_instrument(name: str, strict_mode: bool = False):
    """Return (category, folder_name) for the best keyword match, or (None, None)."""
    # Clean the name: remove non-alphanumeric chars and convert to lowercase
    clean_name = re.sub(r'[^a-z0-9]', ' ', name.lower())
    clean_name_words = clean_name.split()
    
    # First pass: look for exact whole-word matches
    for keyword, category, folder_name in KEYWORD_LOOKUP:
        if keyword in clean_name_words:
            return category, folder_name
            
    # Second pass: look for substring matches if not in strict mode
    if not strict_mode:
        for keyword, category, folder_name in KEYWORD_LOOKUP:
            # Skip short keywords that must be whole words
            if keyword in WHOLE_WORD_ONLY:
                continue
            if keyword in name.lower():
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
                # If isolate_misc is false, uncategorized files go to the root of the processed folder
                dest_dir = target_path

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
# ROUTES
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    """Main tools menu landing page."""
    return render_template('index.html')

@app.route('/compiler')
def compiler_page():
    """Audio library compiler / sorter tool."""
    return render_template('sample-compiler.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle ZIP upload and start processing."""
    if 'file' not in request.files:
        return jsonify({"status": "error", "error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "error": "No selected file"}), 400
    
    if file and file.filename.endswith('.zip'):
        folder_id = str(uuid.uuid4())
        upload_path = os.path.join(UPLOAD_FOLDER, f"{folder_id}.zip")
        file.save(upload_path)
        
        extract_path = os.path.join(UPLOAD_FOLDER, folder_id)
        processed_path = os.path.join(OUTPUT_FOLDER, folder_id)
        os.makedirs(extract_path, exist_ok=True)
        os.makedirs(processed_path, exist_ok=True)
        
        try:
            with zipfile.ZipFile(upload_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            settings = {
                'nested_action': request.form.get('nested_action', 'extract'),
                'sort_sf2': request.form.get('sort_sf2') == 'true',
                'isolate_misc': request.form.get('isolate_misc') == 'true',
                'strict_mode': request.form.get('strict_mode') == 'true'
            }
            
            if settings['nested_action'] != 'ignore':
                extract_nested_zips(extract_path, settings['nested_action'])
            
            file_count = process_audio_library(extract_path, processed_path, settings)
            
            # Create a ZIP of the processed results
            result_zip = os.path.join(OUTPUT_FOLDER, f"{folder_id}_sorted.zip")
            with zipfile.ZipFile(result_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(processed_path):
                    for f in files:
                        abs_path = os.path.join(root, f)
                        rel_path = os.path.relpath(abs_path, processed_path)
                        zipf.write(abs_path, rel_path)
            
            return jsonify({
                "status": "success",
                "folder_id": folder_id,
                "file_count": file_count
            })
            
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 500
        finally:
            # Clean up extraction temp files
            if os.path.exists(extract_path):
                shutil.rmtree(extract_path)
            if os.path.exists(upload_path):
                os.remove(upload_path)
    
    return jsonify({"status": "error", "error": "Invalid file format"}), 400

@app.route('/download/<folder_id>')
def download_result(folder_id):
    """Download the sorted ZIP file."""
    zip_path = os.path.join(OUTPUT_FOLDER, f"{folder_id}_sorted.zip")
    if os.path.exists(zip_path):
        return send_file(zip_path, as_attachment=True, download_name="XKERO_Z_Sorted_Library.zip")
    return "File not found", 404

@app.route('/api/explore/<folder_id>')
def explore_folder(folder_id):
    """Return a JSON tree of the processed folder."""
    processed_path = os.path.join(OUTPUT_FOLDER, folder_id)
    if not os.path.exists(processed_path):
        return jsonify({"error": "Folder not found"}), 404
    
    def get_tree(path):
        tree = {}
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                tree[item] = get_tree(item_path)
            else:
                tree[item] = "file"
        return tree
    
    return jsonify({"tree": get_tree(processed_path)})

if __name__ == "__main__":
    print("XKERO_Z Tools Suite is starting...")
    print("Access the tools at: http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
