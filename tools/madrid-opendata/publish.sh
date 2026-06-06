#!/bin/bash
# Efficient standardized republish: rsync (skips unchanged raster/v3/tab), drop orphan parquet/, refresh surface+catalog, no-cache.
set -uo pipefail
ST="/tmp/od_catalog"; DST="gs://carto-portolan-madrid/madrid-opendata"   # e.g. /tmp/madrid_catalog  gs://carto-portolan-madrid/madrid-city
echo "[$DST] rsync data tree (uploads changed v2/catalog, skips unchanged)"
gcloud storage rsync -r "$ST/data" "$DST/data" 2>&1 | tail -2
echo "[$DST] remove orphan data/parquet/ (superseded by v2-as-GeoParquet)"
gcloud storage rm -r "$DST/data/parquet" 2>&1 | tail -1 || echo "  (no parquet/ to remove)"
echo "[$DST] upload catalog.json + versions.json (no-cache)"
for f in catalog.json versions.json; do
  [ -f "$ST/$f" ] && gcloud storage cp "$ST/$f" "$DST/$f" --content-type=application/json --cache-control=no-cache >/dev/null 2>&1 && echo "  $f"
done
echo "[$DST] upload IRC surface (no-cache)"
cd "$ST/_surface"; n=0
for f in *.json; do
  key=$(echo "$f" | sed 's/\.json$//; s/__/\//g')
  gcloud storage cp "$f" "$DST/$key" --content-type=application/json --cache-control=no-cache >/dev/null 2>&1 && n=$((n+1))
done
echo "  surface objects: $n"
echo "[$DST] no-cache on metadata + index"
gcloud storage objects update "$DST/data/**/metadata/*.json" --cache-control=no-cache >/dev/null 2>&1 || true
gcloud storage objects update "$DST/data/catalog/datasets/data/datasets.parquet" --cache-control=no-cache >/dev/null 2>&1 || true
echo "[$DST] done"
