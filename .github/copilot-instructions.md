# Copilot Instructions for this Repository

## Prerequisites

- Real-Time Distribution infrastructure must already be configured and running (ADS/ADH with TRCC route active; README states 3.2.1+).
- RCC access is required at the infrastructure layer (TRCC username/password/hosts are configured on ADH side, see `infra_config/rmds_trcc.cnf`), not passed to `trcc_posting.py`.
- Python environment is required for local runs (`console_python/requirements.txt`).
- `websocket-client` support is required for the sample protocol flow (pinned in requirements).
- Jupyter runtime is required only for notebook workflows (`notebook_python/requirements_notebook.txt`).

## Dependency files and expectations

- `console_python/requirements.txt` is the runtime dependency set for the console sample. It pins:
  - `websocket-client` (WebSocket connection and callbacks)
  - `requests` + `urllib3` + `certifi` + `charset-normalizer` + `idna` (HTTP/TLS stack dependencies)
- `notebook_python/requirements_notebook.txt` is a separate, larger notebook environment lockfile including JupyterLab/Jupyter Server/IPython plus the same networking dependencies used by the console flow.
- Keep console and notebook dependency changes in their respective files; do not merge notebook-only packages into the console requirements.

## Build, run, test, and lint commands

### Console app (primary example)

Run from `console_python`:

```bash
pip install -r requirements.txt
python trcc_posting.py --hostname <ADS_HOST> --port <WS_PORT> --item <CONTRIBUTION_RIC> --service <TRCC_SERVICE>
```

Example values used in this repo are recorded in `run.txt`.

### Docker flow (console app)

Run from `console_python`:

```bash
docker build -t esdk_ws_rcc_python .
docker run esdk_ws_rcc_python --hostname <ADS_HOST> --port <WS_PORT> --item <CONTRIBUTION_RIC> --service <TRCC_SERVICE>
```

### Notebook flow

Run from `notebook_python`:

```bash
pip install -r requirements_notebook.txt
jupyter notebook trcc_posting_notebook.ipynb
```

### Tests and linting

There is no automated test suite or lint configuration in this repository (`pytest`/`unittest`, `ruff`/`flake8`/`pylint` are not configured).

For a single-scenario verification, run one `trcc_posting.py` session against a reachable ADS endpoint and confirm Login Refresh followed by Post Ack output in the console.

## High-level architecture

- `console_python/trcc_posting.py` is the main RCC contribution sample. It is an event-driven `websocket-client` app that:
  1. Connects to ADS at `ws://<hostname>:<port>/WebSocket` with subprotocol `tr_json2`.
  2. Sends a Login message (`Domain: Login`, `ID: 1`) from `on_open`.
  3. On Login Refresh, sends an off-stream OMM Post (`Domain: MarketPrice`, `Type: Post`, `Ack: true`) targeting the contribution item/service.
  4. Handles server `Ping` by sending `Pong`.
  5. Continues periodic posts (every ~3 seconds) with incremented field values.
- `console_python/market_price.py` is a related consumer/request example (Market Price request after login), useful as a simpler WebSocket reference.
- `infra_config/rmds_trcc.cnf` contains example ADH/TRCC route settings. RCC tunnel credentials and host routing are configured at infra level there, not in the Python app.
- `notebook_python/trcc_posting_notebook.ipynb` mirrors the posting workflow for notebook-based usage.

## Key codebase conventions

- Preserve WebSocket JSON field names/casing exactly as written (`Domain`, `Type`, `Ack`, `PostID`, `PostUserInfo`, etc.) because they map to protocol semantics.
- Login stream identity is intentionally fixed (`login_id = 1`) and reused by post messages (`ID: login_id`) for off-stream posting via the login stream.
- Post construction keeps both top-level `Key` and nested `Message.Key` aligned to the same `item` and `service`.
- `PostUserInfo.UserID` is derived from `app_id` and must be numeric (`int(app_id)`).
- CLI parsing uses `getopt` long options only (`--hostname`, `--port`, `--app_id`, `--user`, `--position`, `--item`, `--service`); keep this style when extending arguments.
- Runtime behavior is based on mutable module-level state (`post_id`, field values, `next_post_time`) rather than class encapsulation; maintain consistency with that pattern unless intentionally refactoring.
