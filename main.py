"""
Write one shapefile per SCIAN class from an INEGI DENUE state download.

Inputs:
  CLASSES_CSV  one column headed scian_class_id, one 6-digit SCIAN class code per row
  DENUE_ZIP    a state's shapefile zip from https://www.inegi.org.mx/contenidos/masiva/denue/
               e.g. denue_14_shp.zip, used as downloaded

Output: output/<zip name>/scian_<class>/scian_<class>.shp, one folder per class,
ready for ArcGIS Pro.
"""

import argparse
import csv
import re
import shutil
import sys
import zipfile
from pathlib import Path

import geopandas as gpd

ID_COLUMN = "scian_class_id"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def read_classes(path):
    """
    Class codes from a one-column CSV headed scian_class_id; exits listing every invalid line.
    """
    if not path.exists():
        sys.exit(f"error: {path} not found")
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = [(n, row) for n, row in enumerate(csv.reader(f), 1) if row]
    if not rows or rows[0][1] != [ID_COLUMN]:
        found = ",".join(rows[0][1]) if rows else "an empty file"
        sys.exit(f"error: {path} line 1 must be exactly '{ID_COLUMN}', found '{found}'")

    classes, errors = [], []
    for n, row in rows[1:]:
        if len(row) != 1:
            errors.append(f"line {n}: {len(row)} columns, only '{ID_COLUMN}' is allowed")
        elif not re.fullmatch(r"\d{6}", row[0]):
            errors.append(f"line {n}: '{row[0]}' is not a 6-digit SCIAN class code")
        elif row[0] in classes:
            errors.append(f"line {n}: {row[0]} is repeated")
        else:
            classes.append(row[0])
    if errors:
        sys.exit(f"error: invalid {path}\n  " + "\n  ".join(errors))
    if not classes:
        sys.exit(f"error: {path} has no class codes")
    return set(classes)


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
    parser.add_argument("classes_csv", type=Path, help=f"CSV with a single {ID_COLUMN} column")
    parser.add_argument("denue_zip", type=Path, help="INEGI DENUE state shapefile zip, e.g. denue_14_shp.zip")
    args = parser.parse_args()

    classes = read_classes(args.classes_csv)
    denue = read_denue(args.denue_zip, classes)
    out = OUTPUT_DIR / args.denue_zip.stem
    groups = dict(tuple(denue.groupby("codigo_act")))

    # Start from an empty folder so dropped classes don't linger.
    shutil.rmtree(out, ignore_errors=True)

    for class_id, group in groups.items():
        name = f"scian_{class_id}"
        (out / name).mkdir(parents=True)
        group.to_file(out / name / f"{name}.shp", encoding="utf-8")
        print(f"{class_id}  {len(group):>5}  {name}/")

    print(f"\n{len(groups)} shapefiles, {len(denue)} establishments -> {out}/")
    missing = sorted(classes - set(groups))
    if missing:
        print(f"classes with no establishments in this zip (no folder written): {', '.join(missing)}")


if __name__ == "__main__":
    main()
