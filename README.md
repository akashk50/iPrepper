# iPrepper

iPrepper is an interview-practice desktop application written by **Akash Khanna** for a data management class. The original Python/Tkinter application brings together a searchable question bank, speech transcription, facial-expression charts, AI feedback, and saved interview results. This repository preserves that class-project implementation and its authorship.

This is a class prototype, with exploratory scripts alongside the main application. It requires external services, local model files, and camera/microphone access; cloning alone does not produce a ready-to-run app. The previous README reported that the original service keys/accounts were disabled; their current status has not been tested.

## Architecture

| File | Responsibility |
| --- | --- |
| `Final_Project/main.py` | Main Tkinter UI, MongoDB question search, recording queues, Vosk transcription, DeepFace analysis, OpenAI feedback, DynamoDB result writes |
| `Final_Project/tableClass.py` | Analytics table, filtering, and result add/edit/delete operations |
| `Final_Project/config.py` | Environment configuration and paths; service clients are created only when requested |
| `Final_Project/mongoDB.py` | Question CSV loader (`loadMongo`), example query (`main`), legacy database-deletion helper (`deleteDB`) |
| `Final_Project/dynamoDB.py` | Standalone sample result writer, despite its historical `get_dynamodb_headers` function name |
| `Final_Project/audioVisual.py` | Earlier audiovisual/feedback prototype |
| `Final_Project/test1.py`, `ttkbootstrapTest.py` | UI experiments, not automated tests |
| `Final_Project/questions.csv`, `logo.ppm` | Original question bank and logo |
| `tests/` | Offline automated tests using mocks, with no service or device access |

Question flow: CSV → MongoDB `questions` collection → search/select question. Practice flow: microphone → Vosk transcript; webcam → DeepFace expression counts; question + transcript → OpenAI feedback; feedback + expression proportions → DynamoDB → analytics table. Facial-expression proportions are an experimental visualization, not an assessment of a person's abilities.

## Local setup

Use a virtual environment. Python 3.11 is a reasonable starting point given the original bytecode artifacts, but the full dependency combination has not been validated. The offline suite was verified on Python 3.14.3 without installing runtime dependencies. DeepFace/TensorFlow and native audio support may require a different Python version or additional platform packages.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

`requirements.txt` lists direct dependencies with compatibility ranges; it is not a tested lockfile. Tkinter comes from your Python/system installation, not pip. On macOS, install a Python build with Tk support and PortAudio before installing PyAudio. Check Tk independently with `python -m tkinter`. Install `requirements-prototypes.txt` only if you need the ttkbootstrap experiment. No runtime dependencies were installed as part of this cleanup.

Edit `.env` locally, then export it from the repository root (the application does not load it automatically):

```sh
set -a
source .env
set +a
```

Configure the following prerequisites yourself before launching; these instructions do not provision resources:

- **OpenAI:** set `OPENAI_API_KEY`. `OPENAI_MODEL` retains the original `gpt-3.5-turbo-0125` default; availability is unverified. Set a model compatible with the existing Chat Completions arguments if needed. Stopping a recording invokes the API and may incur charges.
- **AWS:** choose an existing local profile (`AWS_PROFILE`) or export `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`; temporary credentials also require `AWS_SESSION_TOKEN`. Boto3 uses its standard credential chain. Set `AWS_REGION` (default `us-east-1`) and `DYNAMODB_TABLE` (default `user_scores`). The table needs a **string partition key `dateSubmitted`**, with no sort key expected by this code. Its non-key fields are `Question`, `Feedback`, `Happy`, `Neutral`, and `Other Emotions`. The app scans at startup and writes/deletes through the UI. The sample DynamoDB script also writes a record when run.
- **MongoDB:** run your own instance and set `MONGODB_URI` and `MONGODB_DATABASE` (defaults: `mongodb://localhost:27017`, `dsci351-project`). The `questions` collection uses `Question`, numeric `Difficulty`, and `Category` fields, matching the bundled CSV.
- **Vosk:** separately obtain and unpack a compatible English model. Set `VOSK_MODEL_PATH` to that directory (absolute, or relative to the launch directory). The original project used `vosk-model-en-us-0.42-gigaspeech`; no model is bundled or downloaded by this cleanup.
- **Devices/models:** set `CAMERA_INDEX` to an integer if the default `0` is wrong (validated when opening a camera), grant camera/microphone access, and arrange DeepFace model weights. DeepFace may download weights on first use. The chart now uses a system font; Tk uses a fallback if Quicksand is unavailable. The included PPM logo and text play/stop controls replace references to missing PNG files.

To seed your configured MongoDB **once**, from the repository root:

```sh
(cd Final_Project && python -c 'from mongoDB import loadMongo; loadMongo()')
```

The original loader appends all CSV records; running it repeatedly creates duplicates. It is intentionally not run automatically. `deleteDB()` is a legacy destructive helper that drops databases; do not call it for setup.

Launch the main application from the repository root:

```sh
python Final_Project/main.py
```

Bundled asset paths resolve relative to the source file. Application/prototype modules still initialize windows/devices/clients at module scope, so do not import them as libraries or for test discovery.

## Offline verification

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q Final_Project tests
```

The tests use only the standard library and mocked SDK/Tk modules. They cover environment defaults/overrides, asset/model paths, missing OpenAI configuration, AWS client arguments, DynamoDB pagination, case-insensitive filtering, result add/edit/delete behavior, write-failure behavior, sample Decimal ratios, and MongoDB's import/loader behavior. They do not validate a real database schema, service authentication, model/API compatibility, UI rendering, audio/video, transcription, or facial-expression analysis.

## Scope and remaining limitations

This cleanup centralizes configuration, removes current source credential literals and tracked bytecode, makes paths portable, adds setup guidance, and adds offline regression tests. It preserves the original interview workflow and layout.

The larger follow-up would be separating UI state, recording/thread lifecycle, and service adapters. Known prototype limitations include blocking work in UI callbacks, Tk updates from a worker thread, recording state accumulated across sessions, incomplete transcript finalization, empty-expression handling, and edit-selection validation. Those need a coordinated refactor and interactive validation before claiming a reliable complete interview flow; they are outside this cleanup.

Keep `.env` and real credentials out of Git. Removing current source literals does **not** revoke credentials or erase them from Git history. No history rewrite, credential validation/rotation, deployment, or repository permission changes are part of this cleanup.
