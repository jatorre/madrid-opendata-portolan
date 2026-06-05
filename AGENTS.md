# AGENTS.md — guide for AI agents

This repo **is a Portolan catalog** of the City of Madrid open-data portal (datos.madrid.es), served as
static files on Google Cloud Storage. No server, no API keys. Endpoint = `public_base` in
`portolan.config.json`: `https://storage.googleapis.com/carto-portolan-madrid/madrid-opendata`.

## How to READ (no credentials)

- **ATTACH (DuckDB / Snowflake):** `ATTACH 'cat' (TYPE iceberg, ENDPOINT '<public_base>', AUTHORIZATION_TYPE 'none');`
  then `SELECT * FROM cat.<ns>.<table>;` — namespaces: `v2`/`v3` (vector), `tab` (non-spatial), `catalog`.
- **Discover:** `SELECT * FROM cat.catalog.datasets` — one STAC row per dataset, with `properties`
  (title, description, keywords, OSI `semantics`, `crs`, `materialized`, `data_status`) and `assets`.
  `materialized=true` rows have cloud-native data; `data_status` explains the rest (maintenance, etc.).
- **Scan a table:** `iceberg_scan('<public_base>/data/v3/<table>/metadata/v1.metadata.json')`.
- **Direct download:** GeoParquet/Parquet under `<public_base>/data/parquet/`.

CRS is **OGC:CRS84 (EPSG:4326)** throughout — geometry is WGS84 lon/lat; spatial ops need no transform.
Read each table's column `doc` and the dataset's `semantics` before composing a query.

## How to CONTRIBUTE / refresh

Re-run `tools/madrid-opendata/fetch_convert.py` → `build_opendata_catalog.py` → `publish.sh` (resumable;
picks up datasets that were under maintenance). Edit `portolan.config.json` / the tooling via PR. Data
bytes live on the bucket, never in git.

## Conventions

- Git holds the **definition**; the bucket holds **data** + generated artifacts. Never commit parquet.
- Source of truth for what exists = the CKAN catalog (`https://datos.madrid.es/api/3/action`) → `manifest.json`.
- This is an **open, public, anonymous** catalog. Query is the engine's native SQL — no custom query API.
