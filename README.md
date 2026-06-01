# XKERO_Z — UltraBox Companion & Sample Compiler

A two-part toolkit for working with [UltraBox](https://ultraabox.github.io/), the open-source chiptune tracker and sampler built on BeepBox.

---

## What is UltraBox?

[UltraBox](https://ultraabox.github.io/) is a browser-based music tracker that combines features from many BeepBox mods into one package. It supports:

- Piano-roll based note editing
- Built-in chiptune synthesis (chip waves, FM, harmonics, spectrum, noise)
- **Custom sampling** — import your own `.wav`/`.mp3`/`.flac` sounds via public CORS-friendly URLs
- SF2 soundfont support (via the Sample Extractor utility)
- Advanced effects: reverb, panning, EQ filters, envelopes, unisons
- Up to 60 pitch channels, 60 noise channels, 60 mod channels
- Tempo range 1–500 BPM, up to 1024 bars

All song data is encoded in the URL — no account or server needed.

---

## Project Structure

```
XKERO_Z/
├── Compiler-sorter/        # Flask web app (run locally)
│   ├── app.py              # Backend — sorting logic + API routes
│   ├── requirements.txt    # Python dependencies
│   ├── templates/
│   │   ├── ultrabox.html   # UltraBox Companion page (/)
│   │   └── index.html      # Sample Compiler page (/compiler)
│   ├── static/
│   │   └── custom_samples/ # Auto-created; holds imported samples
│   ├── uploads/            # Auto-created; temporary upload storage
│   └── processed/          # Auto-created; sorted output ZIPs
├── .github/
│   └── workflows/
│       └── static.yml      # GitHub Pages deployment workflow
├── .gitignore
└── README.md
```

---

## Running Locally

### Requirements

- Python 3.9 or newer

### Setup

```bash
cd Compiler-sorter
pip install -r requirements.txt
python app.py
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.

---

## Tools

### 1. UltraBox Companion (`/`)

The main page embeds the live UltraBox editor in an iframe so you can compose music without leaving the app. It also provides:

- **Sample URL Manager** — Build a list of public sample URLs and generate a UltraBox link that pre-loads them. Supports export/import of your URL list as JSON. URLs are persisted in `localStorage`.
- **Import Sorted Pack** — Upload a ZIP produced by the Sample Compiler to preview and play back your sorted audio files directly in the browser.

### 2. Sample Compiler (`/compiler`)

Upload any ZIP archive containing audio files (`.wav`, `.mp3`, `.flac`, `.aiff`, `.ogg`) and SF2 soundfonts. The compiler:

1. Scans every filename and parent folder name for instrument keywords.
2. Sorts files into a structured folder hierarchy (e.g. `Percussion & Drums / Kick Drum / kick_01.wav`).
3. Alphabetizes SF2 files optionally.
4. Handles nested ZIP files (extract & sort, delete, or ignore).
5. Returns a downloadable sorted ZIP and an in-browser folder explorer with audio preview.

#### Compiler Settings

| Setting | Description |
|---|---|
| Strict Pattern Matching | Matches keywords as whole words only (reduces false positives) |
| Ignore Warnings & Soft Errors | Skip nested-ZIP and empty-archive warnings automatically |
| Alphabetize SF2 Soundfonts | Sort SF2 files into A–Z sub-folders |
| Isolate Unrecognized Files | Move unclassified audio to a `Miscellaneous` folder instead of `Uncategorized` |

---

## Adding Custom Samples to UltraBox

UltraBox does not host files itself. To use custom samples:

1. Upload your audio file to a CORS-friendly host such as [File Garden](https://filegarden.com/) or [Catbox](https://catbox.moe/).
2. Copy the direct file URL (must end in `.wav`, `.mp3`, etc.).
3. In UltraBox, open **Edit → Add Custom Samples…** and paste the URL.
4. Alternatively, use the **Sample URL Manager** tab in this app to build and save a list of URLs, then open UltraBox with all samples pre-loaded in one click.

---

## GitHub Pages

The repository includes a GitHub Actions workflow (`.github/workflows/static.yml`) that deploys a static landing page to GitHub Pages. The Flask app itself requires a Python server and cannot run on GitHub Pages directly — use the local setup above for full functionality.

---

## Instrument Taxonomy

The compiler recognises the following top-level categories:

- Strings (Acoustic Guitar, Electric Guitar, Bass Guitar, Violin, Viola, Cello, Double Bass, Harp, Banjo, Mandolin, Ukulele, Generic Strings)
- Woodwinds (Flute, Oboe, Clarinet, Bassoon, Saxophone, Recorder, Generic Woodwinds)
- Brass (Trumpet, Trombone, Tuba, French Horn, Generic Brass)
- Percussion & Drums (Kick Drum, Snare Drum, Hi-Hat, Tom Tom, Cymbals, Clap & Snap, Cowbell, Timpani, Latin Percussion, Shakers & Toys, Electronic Drums)
- Chromatic & Mallets (Bells, Chimes, Marimba & Xylophone, Music Box)
- Keyboards & Synths (Acoustic Piano, Electric Piano, Organ, Harpsichord, Accordion, Synth Leads, Synth Pads, Synth Plucks, Synth Bass, Chiptune & Waves, Mellotron)
- World & Traditional (Sitar & Tanpura, Koto & Shamisen, Oud & Lute, Bagpipes, Didgeridoo, Kalimba)
- Vocals (Choir, Vocal Loops, Vocal FX)
- Foley & Environment (Nature Elements, Footsteps, Mechanical & Tech, Vinyl & LoFi)
- Sound Design & FX (Cinematic FX, Transitions, Textures)

---

## Credits

- [UltraBox](https://ultraabox.github.io/) by Neptendo, choptop84, Slarmoo, ThinkAndWander, LeoV and contributors — MIT License
- [BeepBox](https://www.beepbox.co/) by John Nesky — MIT License
- XKERO_Z Companion & Compiler — 2026
