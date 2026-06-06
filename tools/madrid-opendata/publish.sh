#!/bin/bash
# Publish to GCS in the v3 + standalone-GeoParquet model. Uses cp (NOT rsync: rsync's size-only
# compare is unsafe for Iceberg metadata). Overwrites v3/parquet/catalog/tab; leaves unchanged raster.
set -uo pipefail
ST="/tmp/od_catalog"; DST="gs://carto-portolan-madrid/madrid-opendata"
for d in v3 tab catalog parquet raster; do
  [ -d "$ST/data/$d" ] && gcloud storage cp --recursive "$ST/data/$d" "$DST/data/" 2>&1 | tail -1
done
for f in catalog.json versions.json; do
  [ -f "$ST/$f" ] && gcloud storage cp "$ST/$f" "$DST/$f" --content-type=application/json --cache-control=no-cache >/dev/null 2>&1 && echo "  $f"
done
cd "$ST/_surface"; for f in *.json; do key=$(echo "$f"|sed 's/\.json$//; s/__/\//g'); gcloud storage cp "$f" "$DST/$key" --content-type=application/json --cache-control=no-cache >/dev/null 2>&1; done
gcloud storage objects update "$DST/data/**/metadata/*.json" --cache-control=no-cache >/dev/null 2>&1 || true
gcloud storage objects update "$DST/data/catalog/datasets/data/datasets.parquet" --cache-control=no-cache >/dev/null 2>&1 || true
echo "published $DST"
