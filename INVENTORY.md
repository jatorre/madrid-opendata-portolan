# datos.madrid.es → Portolan — import inventory (2026-06-05)

Source: **City of Madrid open-data portal** [datos.madrid.es](https://datos.madrid.es), **CKAN 2.9.11**
(API `https://datos.madrid.es/api/3/action`). Distinct from the geoportal/IDEAM (cartography/imagery);
this is operational/thematic open data. Imported autonomously into a cloud-native Portolan catalog.

## Catalog
- **Endpoint:** `https://storage.googleapis.com/carto-portolan-madrid/madrid-opendata` (anonymous `ATTACH`).
- **CRS:** `OGC:CRS84` (EPSG:4326 / WGS84) — open-data geo is GeoRSS/KML lat-long; SHP reprojected to 4326.
- **667 datasets** indexed in `catalog.datasets` (stac-geoparquet), all © Ayuntamiento de Madrid.

## Results
- **527 materialized layers** across the downloadable datasets:
  - **108 vector** (from SHP/GeoJSON/KML/KMZ/**GEO=GeoRSS**) → Iceberg **v2 + v3** + remote **GeoParquet** (EPSG:4326).
  - **419 tabular** (from CSV/XLSX/JSON) → Iceberg **`tab`** (`portolan:geospatial:false`) + remote Parquet.
- **137 metadata-only rows** (`materialized:false` + `data_status`): tabular_failed 51 (XLS/odd encodings),
  extract_failed 7, convert_failed 4, build_error 3 (empty GeoRSS), plus PDF/RDF-only, maintenance, 403/404.
- Each table carries full properties + **per-column `doc`** + **OSI semantics**; materialized rows carry the
  **STAC Iceberg** extension; the root `catalog.json` carries the **git-backed-catalog** extension.

## Themes (CKAN groups)
sociedad-bienestar 109 · transporte 109 · sector-publico 101 · medio-ambiente 78 · urbanismo 77 ·
cultura-ocio 33 · deporte 33 · salud 25 · seguridad 17 · comercio 14 · turismo 13 · educacion 12 · hacienda 12 …

## Query
```sql
ATTACH 'mad' (TYPE iceberg, ENDPOINT 'https://storage.googleapis.com/carto-portolan-madrid/madrid-opendata', AUTHORIZATION_TYPE 'none');
SELECT json_extract_string(properties,'$.data_status') st, count(*) FROM mad.catalog.datasets GROUP BY 1;
SELECT count(*) FROM mad.tab."<a-tabular-dataset-id>";
```

Reproduce/refresh (resumable): `tools/madrid-opendata/fetch_convert.py` → `build_opendata_catalog.py` → `publish.sh`.
