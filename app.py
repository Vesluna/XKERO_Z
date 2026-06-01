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
    # Clean the name and split into words for more precise matching
    clean_name_words = re.findall(r'\b[a-z0-9]+\b', name.lower())
    
    for keyword, category, folder_name in KEYWORD_LOOKUP:
        # Check if the keyword exists as a whole word in the cleaned name's word list
        if keyword in clean_name_words:
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
    """Main tools menu landing page."""
    return render_template('index.html')

@app.route('/compiler')
def compiler_page():
    """Audio library compiler / sorter tool."""
    return render_template('sample-compiler.html')




# ---------------------------------------------------------------------------
