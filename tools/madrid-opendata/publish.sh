#!/bin/bash
# Publish the staged Madrid catalog to GCS (data tree + remote parquet/rasters + IRC surface).
set -euo pipefail
DST="gs://carto-portolan-madrid/madrid-opendata"
ST="/tmp/od_catalog"

echo "=== upload data tree (v2/v3/tab/catalog/parquet/raster) ==="
gcloud storage cp --recursive "$ST/data" "$DST/" 2>&1 | tail -2

echo "=== upload top-level catalog.json + versions.json (no-cache: mutable discovery docs) ==="
for f in catalog.json versions.json; do
  [ -f "$ST/$f" ] && gcloud storage cp "$ST/$f" "$DST/$f" --content-type=application/json --cache-control=no-cache >/dev/null 2>&1 && echo "  $f"
done

echo "=== upload IRC REST surface (extension-less keys, application/json, no-cache) ==="
cd "$ST/_surface"
n=0
for f in *.json; do
  key=$(echo "$f" | sed 's/\.json$//; s/__/\//g')
  gcloud storage cp "$f" "$DST/$key" --content-type=application/json --cache-control=no-cache >/dev/null 2>&1 && n=$((n+1))
done
echo "uploaded $n surface objects"

# Mutable Iceberg metadata + the stac-geoparquet index get no-cache so in-place overwrites
# propagate immediately (GCS default for public objects is public,max-age=3600 -> stale reads).
echo "=== set no-cache on Iceberg metadata + index (overwrite-consistency) ==="
gcloud storage objects update "$DST/data/**/metadata/*.json" --cache-control=no-cache >/dev/null 2>&1 || true
gcloud storage objects update "$DST/data/catalog/datasets/data/datasets.parquet" --cache-control=no-cache >/dev/null 2>&1 || true

echo "=== verify endpoint ==="
BASE="https://storage.googleapis.com/carto-portolan-madrid/madrid-opendata"
for u in "v1/config" "v1/sdi/namespaces" "data/catalog/datasets/metadata/v1.metadata.json"; do
  printf "%-50s %s\n" "$u" "$(curl -sS -m 15 -o /dev/null -w '%{http_code}' "$BASE/$u")"
done
