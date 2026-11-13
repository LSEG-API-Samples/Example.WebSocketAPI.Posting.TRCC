# Copilot Instructions for this Repository

## Prerequisites

- Real-Time Distribution infrastructure must already be configured and running: ADS/ADH with an active TRCC route and contribution service (README states version 3.2.1+).
- RCC access is also required at the infrastructure layer; TRCC credentials and host routing are configured on ADH, not passed to the Python app (see `infra_config/rmds_trcc.cnf` for an example).

## Project context

- This repository demonstrates RCC contribution through a WebSocket connection to Real-Time Distribution (ADS/ADH).
- RCC credentials and route configuration belong to the infrastructure, not the Python CLI. `infra_config/rmds_trcc.cnf` is an example template, not a complete deployable configuration.
- See [README.md](../README.md) for protocol background and sample messages. Verify commands and paths against the current source; some README examples are legacy.

## Dependencies and environments

- Keep console and notebook dependencies separate in `console_python/requirements.txt` and `notebook_python/requirements_notebook.txt`.
- `websocket-client` provides the `websocket` import used by both flows. JupyterLab does not install this package on the notebook's behalf.
- The console requirements currently also include `requests`, which the sample scripts do not import. Check actual imports and usage before adding or retaining direct dependencies; pip resolves transitive dependencies, so do not pin them individually without a reason.
- Install the relevant requirements file from its directory. Start the notebook with `jupyter lab trcc_posting_notebook.ipynb` from `notebook_python`.

## Run and validate

Console, from `console_python`:

```bash
pip install -r requirements.txt
python trcc_posting.py --hostname <ADS_HOST> --port <WS_PORT> --item <CONTRIBUTION_RIC> --service <TRCC_SERVICE>
```

Docker, from `console_python`:

```bash
docker build -t esdk_ws_rcc_python .
docker run esdk_ws_rcc_python --hostname <ADS_HOST> --port <WS_PORT> --item <CONTRIBUTION_RIC> --service <TRCC_SERVICE>
```

Notebook, from `notebook_python`:

```bash
pip install -r requirements_notebook.txt
jupyter lab trcc_posting_notebook.ipynb
```

- There is no configured automated test or lint suite. For local checks, run `python -m py_compile trcc_posting.py market_price.py` from `console_python` and `python trcc_posting.py --help` with dependencies installed.
- End-to-end verification requires a reachable ADS/TRCC setup. The console prints inbound messages, including any Ack; it has no dedicated Ack assertion or automated integration test.
- `run.txt` contains environment-specific sample connection values; do not treat them as portable defaults.

## Architecture and conventions

- `console_python/trcc_posting.py` is the main contributor; `console_python/market_price.py` is a consumer/request example. The notebook flow in `notebook_python/trcc_posting_notebook.ipynb` sends one post and closes; it is not the console's repeating loop.
- The console uses `websocket-client` with subprotocol `tr_json2`, connects to `ws://<hostname>:<port>/WebSocket`, sends Login (`Domain: Login`, `ID: 1`) on open, and sends an off-stream MarketPrice Post on Login Refresh. It replies to server `Ping` with `Pong`.
- The console sends its first post immediately on Login Refresh. Later posts are driven by a loop that sleeps about 10 seconds before checking a 3-second deadline, so do not describe the effective repeat interval as exactly 3 seconds.
- Preserve protocol JSON field names/casing (`Domain`, `Type`, `Ack`, `PostID`, `PostUserInfo`, etc.). Keep top-level `Key` and nested `Message.Key` aligned to the same item and service.
- The login stream ID is fixed at `1` and reused for the outer off-stream post ID; `PostUserInfo.UserID` is `int(app_id)`.
- CLI options use `getopt` long options. The posting CLI accepts `--hostname`, `--port`, `--app_id`, `--user`, `--position`, `--item`, and `--service`; check the specific script before assuming another example has the same options.
- The contributor keeps runtime state in module-level variables such as `post_id`, field values, and `next_post_time`. Follow this pattern for narrow changes; refactor only when the task calls for it.
