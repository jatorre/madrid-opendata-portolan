# 🇪🇸 Madrid Open Data — Portolan catalog

🌐 **[Explorar el catálogo (visor web) →](https://storage.googleapis.com/carto-portolan-madrid/madrid-opendata/web/index.html)**

A **Portolan** cloud-native spatial-data catalog of the **City of Madrid open-data portal**
([datos.madrid.es](https://datos.madrid.es), CKAN 2.9.11), published as a static **Apache Iceberg REST
catalog + stac-geoparquet index** on Google Cloud Storage — readable with no server, no credentials.

Sibling of [`madrid-city-portolan`](https://github.com/jatorre/madrid-city-portolan) (the geoportal/IDEAM
cartography). This repo is the **open-data** portal: mostly thematic **tabular** data + point/area
**geospatial** layers. Both federate under the same publisher (Ayuntamiento de Madrid) on the same bucket.

**Catalog endpoint (Iceberg REST):** `https://storage.googleapis.com/carto-portolan-madrid/madrid-opendata`
**CRS:** `OGC:CRS84` (EPSG:4326 / WGS84) — open-data geo is GeoRSS/KML lat-long.

## Read it — no credentials, no server

```sql
INSTALL iceberg;LOAD iceberg;INSTALL httpfs;LOAD httpfs;INSTALL spatial;LOAD spatial;
ATTACH 'mad' (TYPE iceberg,
  ENDPOINT 'https://storage.googleapis.com/carto-portolan-madrid/madrid-opendata',
  AUTHORIZATION_TYPE 'none');
SHOW ALL TABLES;                                    -- v2.* / v3.* (vector) , tab.* (non-spatial) , catalog.datasets
SELECT id, json_extract_string(properties,'$.data_status') FROM mad.catalog.datasets;
```

Four equivalent reads (all the same files on the bucket): `ATTACH` (Iceberg REST), `iceberg_scan(<metadata.json>)`,
the `catalog.datasets` stac-geoparquet index, or direct GeoParquet/Parquet download under `data/`.

## What's in it

Every dataset from datos.madrid.es is catalogued in `catalog.datasets` (STAC item per row, with OSI
`semantics`, `materialized`, `data_status`). Data is materialized where downloadable:

- **Vector** (SHP / GeoJSON / KML / KMZ / GEO=GeoRSS) → Iceberg **v2** (WKB) + **v3** (native geometry) +
  remote **GeoParquet**, reprojected to EPSG:4326.
- **Tabular** (CSV / XLSX / JSON) → Iceberg **`tab`** table (`portolan:geospatial:false`) + remote Parquet.
- Non-downloadable (PDF/RDF only) → metadata-only row with a `source` link.

## Rebuild (resumable)

```bash
python3 tools/madrid-opendata/fetch_convert.py          # CKAN download + convert -> /tmp/od_data + ledger
<iceberg-geo-testbed venv>/bin/python tools/madrid-opendata/build_opendata_catalog.py
bash tools/madrid-opendata/publish.sh                   # -> gs://carto-portolan-madrid/madrid-opendata
```

`manifest.json` = all datasets harvested from the CKAN API. Git tracks the **definition**; data bytes live
on the bucket (see `.gitignore`). Data © Ayuntamiento de Madrid, reuse under the datos.gob.es legal notice.
