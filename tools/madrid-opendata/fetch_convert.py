#!/usr/bin/env python3
"""Resumable download+convert for datos.madrid.es (CKAN) open data.
Vector (SHP/GeoJSON/KML/KMZ/GEO=GeoRSS) -> GeoParquet reprojected to EPSG:4326 (ogr2ogr).
Tabular (CSV/XLSX/XLS/JSON) -> parquet (DuckDB). Writes /tmp/od_state.json (crash-safe, skip-if-done)."""
import json, os, re, subprocess, shutil, glob
from pathlib import Path
MAN=json.load(open('/tmp/od_manifest.json'))
SP=Path('/tmp/od_state.json'); STATE=json.load(open(SP)) if SP.exists() else {}
DATA=Path('/tmp/od_data'); (DATA/'vector').mkdir(parents=True,exist_ok=True); (DATA/'tab').mkdir(parents=True,exist_ok=True)
WORK=Path('/tmp/od_work'); WORK.mkdir(exist_ok=True)
def save(): SP.write_text(json.dumps(STATE,ensure_ascii=False,indent=1))
def run(c,**k): return subprocess.run(c,capture_output=True,text=True,**k)
def dl(url,dest,t=150):
    r=run(['curl','-sSL','-m',str(t),'-o',str(dest),'-w','%{http_code} %{url_effective}',url])
    o=r.stdout.strip(); code=o.split()[0] if o else '000'; final=o.split(' ',1)[1] if ' ' in o else ''
    if 'mantenimiento' in final or 'ServicioNoDisponible' in final: return 'maintenance'
    if not dest.exists() or dest.stat().st_size<64: return 'failed'
    return 'ok' if code in('200','0') else f'http_{code}'
def bbox4326(parq):
    q=(f"INSTALL spatial;LOAD spatial;SET geometry_always_xy=true;"
       f"SELECT min(ST_XMin(geom)),min(ST_YMin(geom)),max(ST_XMax(geom)),max(ST_YMax(geom)) FROM read_parquet('{parq}')")
    r=run(['duckdb','-csv','-noheader','-c',q])
    try:
        v=[float(x) for x in r.stdout.strip().splitlines()[0].split(',')]
        return v if all(abs(x)<=180.001 for x in v[:1]+v[2:]) and v==v else None
    except Exception: return None
def rows_of(parq):
    r=run(['duckdb','-csv','-noheader','-c',f"SELECT count(*) FROM read_parquet('{parq}')"])
    try: return int(r.stdout.strip().splitlines()[-1])
    except Exception: return None
def ogr_to_4326(src, out):
    run(['ogr2ogr','-f','Parquet','-t_srs','EPSG:4326','-nlt','PROMOTE_TO_MULTI',
         '-lco','GEOMETRY_ENCODING=WKB','-lco','COMPRESSION=ZSTD',str(out),str(src)])
    return out if out.exists() and out.stat().st_size>0 else None

def process(ds):
    did=ds['id']
    if STATE.get(did,{}).get('status')=='done': return
    kind=ds['kind']; url=ds.get('res_url'); fmt=(ds.get('res_format') or '').upper()
    layers=[]; status='metadata_only'; err=None
    try:
        if kind=='vector' and url:
            ext={'GEO':'xml','GEOJSON':'geojson','KML':'kml','KMZ':'kmz','SHP':'zip'}.get(fmt,'dat')
            arc=WORK/f"{did}.{ext}"; st=dl(url,arc)
            if st!='ok': status=st
            else:
                src=arc
                if fmt=='SHP':
                    ex=WORK/did
                    if ex.exists(): shutil.rmtree(ex)
                    ex.mkdir()
                    if run(['unzip','-oq',str(arc),'-d',str(ex)]).returncode==0:
                        shps=glob.glob(str(ex/'**'/'*.shp'),recursive=True)
                        src=shps[0] if shps else None
                    else: src=None
                if src is None: status='extract_failed'
                else:
                    out=DATA/'vector'/f"{did}.parquet"
                    if ogr_to_4326(src,out):
                        layers.append(dict(collection=did,kind='vector',file=str(out),rows=rows_of(out),bbox=bbox4326(out),layer=ds['title']))
                        status='done'
                    else: status='convert_failed'
        elif kind=='tabular' and url:
            ext={'CSV':'csv','XLSX':'xlsx','XLS':'xls','JSON':'json'}.get(fmt,'csv')
            arc=WORK/f"{did}.{ext}"; st=dl(url,arc)
            if st!='ok': status=st
            else:
                out=DATA/'tab'/f"{did}.parquet"
                if fmt=='CSV':
                    run(['duckdb','-c',f"COPY (SELECT * FROM read_csv_auto('{arc}',sample_size=-1,ignore_errors=true,all_varchar=true)) TO '{out}' (FORMAT parquet)"])
                elif fmt in('XLSX',):
                    run(['duckdb','-c',f"INSTALL excel;LOAD excel;COPY (SELECT * FROM read_xlsx('{arc}',all_varchar=true)) TO '{out}' (FORMAT parquet)"])
                elif fmt=='JSON':
                    run(['duckdb','-c',f"COPY (SELECT * FROM read_json_auto('{arc}')) TO '{out}' (FORMAT parquet)"])
                else:  # XLS old format — try excel, else skip
                    run(['duckdb','-c',f"INSTALL excel;LOAD excel;COPY (SELECT * FROM read_xlsx('{arc}')) TO '{out}' (FORMAT parquet)"])
                if out.exists() and out.stat().st_size>0:
                    layers.append(dict(collection=did,kind='tabular',file=str(out),rows=rows_of(out),bbox=None,layer=ds['title'])); status='done'
                else: status='tabular_failed'
        else:
            status='metadata_only'
    except Exception as e:
        status='error'; err=str(e)[:300]
    STATE[did]=dict(status=status,kind=kind,groups=ds['groups'],layers=layers,error=err); save()

def main():
    todo=[d for d in MAN if d.get('res_url')]
    print(f"processing {len(todo)} datasets with a resource ({len(MAN)} total)")
    for i,ds in enumerate(todo,1):
        process(ds)
        if i%50==0: print(f"  {i}/{len(todo)}")
    import collections
    print("STATUS:",dict(collections.Counter(v['status'] for v in STATE.values())))
    print("materialized layers:",sum(len(v['layers']) for v in STATE.values()))
if __name__=='__main__': main()
