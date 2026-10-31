"""
Write one shapefile per SCIAN class from an INEGI DENUE state download, grouped by ReflexIA sector.

Inputs:
  CLASSES_CSV  columns scian_class_id, scian_class_name and reflexia_sector,
               one row per class and sector
  DENUE_ZIP    a state's shapefile zip from https://www.inegi.org.mx/contenidos/masiva/denue/
               e.g. denue_14_shp.zip, used as downloaded

Output: output/<zip name>/<sector>/<class> <class name>/scian_<class>.shp, one folder per sector
holding one folder per class, ready for ArcGIS Pro.
"""

import argparse
import csv
import re
import shutil
import sys
import zipfile
from pathlib import Path

import geopandas as gpd

COLUMNS = ["scian_class_id", "scian_class_name", "reflexia_sector"]
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def read_classes(path):
    """
    (class_id, name, sector) rows from the classes CSV; exits listing every invalid line.

    A class may appear in several sectors, but only once in each.
    """
    if not path.exists():
        sys.exit(f"error: {path} not found")
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = [(n, row) for n, row in enumerate(csv.reader(f), 1) if row]
    if not rows or rows[0][1] != COLUMNS:
        found = ",".join(rows[0][1]) if rows else "an empty file"
        sys.exit(f"error: {path} line 1 must be exactly '{','.join(COLUMNS)}', found '{found}'")

    classes, errors, seen = [], [], set()
    for n, row in rows[1:]:
        if len(row) != len(COLUMNS):
            errors.append(f"line {n}: {len(row)} columns, expected {len(COLUMNS)}")
            continue
        class_id, name, sector = row
        if not re.fullmatch(r"\d{6}", class_id):
            errors.append(f"line {n}: '{class_id}' is not a 6-digit SCIAN class code")
        elif not name or not sector:
            errors.append(f"line {n}: {class_id} needs a class name and a sector")
        elif re.search(r'[\\/:*?"<>|]', name + sector):
            errors.append(f"line {n}: {class_id} name and sector can't contain any of \\ / : * ? \" < > |")
        elif (class_id, sector) in seen:
            errors.append(f"line {n}: {class_id} is repeated in sector '{sector}'")
        else:
            seen.add((class_id, sector))
            classes.append((class_id, name, sector))
    if errors:
        sys.exit(f"error: invalid {path}\n  " + "\n  ".join(errors))
    if not classes:
        sys.exit(f"error: {path} has no class codes")
    return classes


def read_denue(zip_path, classes):
    """
    Establishments of the given classes from a DENUE zip.
    """
    if not zipfile.is_zipfile(zip_path):
        sys.exit(f"error: {zip_path} is missing or not a zip file")
    with zipfile.ZipFile(zip_path) as z:
        shps = [n for n in z.namelist() if n.lower().endswith(".shp")]
    if len(shps) != 1:
        sys.exit(f"error: {zip_path} should contain one .shp, found {len(shps)}; "
                 "is it a DENUE shapefile download (denue_XX_shp.zip)?")
    source = f"zip://{zip_path}!{shps[0]}"

    in_list = ",".join(f"'{c}'" for c in sorted(classes))
    denue = gpd.read_file(source, where=f"codigo_act IN ({in_list})")
    # INEGI's .prj is a custom WGS84 definition; use the standard one so ArcGIS recognizes it.
    return denue.set_crs(4326, allow_override=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("classes_csv", type=Path, help=f"CSV with columns: {', '.join(COLUMNS)}")
    parser.add_argument("denue_zip", type=Path, help="INEGI DENUE state shapefile zip, e.g. denue_14_shp.zip")
    args = parser.parse_args()

    classes = read_classes(args.classes_csv)
    class_ids = {class_id for class_id, _, _ in classes}
    denue = read_denue(args.denue_zip, class_ids)
    out = OUTPUT_DIR / args.denue_zip.stem
    groups = dict(tuple(denue.groupby("codigo_act")))

    # Start from an empty folder so dropped classes don't linger.
    shutil.rmtree(out, ignore_errors=True)

    # One write per CSV row, so a class listed in two sectors lands in both.
    written = 0
    for class_id, name, sector in classes:
        if class_id not in groups:
            continue
        group = groups[class_id]
        folder = out / sector / f"{class_id} {name}"
        folder.mkdir(parents=True)
        group.to_file(folder / f"scian_{class_id}.shp", encoding="utf-8")
        written += 1
        print(f"{class_id}  {len(group):>5}  {sector}/{folder.name}/")

    print(f"\n{written} shapefiles, {len(denue)} establishments -> {out}/")
    missing = sorted(class_ids - set(groups))
    if missing:
        print(f"classes with no establishments in this zip (no folder written): {', '.join(missing)}")


if __name__ == "__main__":
    main()
