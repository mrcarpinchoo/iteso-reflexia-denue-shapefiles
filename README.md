# DENUE shapefiles by activity class

Splits a state's [DENUE](https://www.inegi.org.mx/app/mapa/denue/) download from INEGI into one
shapefile per SCIAN activity class (*clase de actividad económica*), ready to add as layers in
ArcGIS Pro. Only the classes you list are extracted; each shapefile holds one point per establishment,
of every size.

Developed for ReflexIA's observatory as part of PAP 4J10A, a professional practicum program at ITESO.

## Setup

Requires Python 3.10 or later (tested with 3.12).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

In later sessions, run `source .venv/bin/activate` again before using the script.

## Inputs

You provide two files. Putting them in an `input/` folder is a suggestion, not a requirement
(it's ignored by git):

```bash
mkdir -p input
```

**1. A state's DENUE zip**, downloaded from <https://www.inegi.org.mx/contenidos/masiva/denue/>
and used as is (don't unzip it). The files are named `denue_<code>_shp.zip`, where `<code>` is the
state's two-digit INEGI code, e.g.:

```bash
curl -L -o input/denue_09_shp.zip https://www.inegi.org.mx/contenidos/masiva/denue/denue_09_shp.zip
```

**2. A CSV with the classes to extract**, e.g. `input/scian_class_ids.csv`, which you create in
this exact format:

- One column only, with the header `scian_class_id` on the first line.
- One 6-digit SCIAN class code per line (codes can be looked up in INEGI's
  [SCIAN classifier](https://www.inegi.org.mx/app/scian/)).
- Each code only once. UTF-8 encoding.

```csv
scian_class_id
325412
334410
541510
```

If the CSV breaks any rule, the script stops without writing anything and lists each problem with
its line number.

## Usage

```bash
source .venv/bin/activate
python main.py input/scian_class_ids.csv input/denue_09_shp.zip
```

The script prints how many establishments each class has and lists any class with none in the state;
those classes get no folder.

## Output

One folder per class in `output/<zip name>/`, each holding that class's shapefile, named after its
SCIAN code:

```
output/denue_09_shp/
  scian_325412/
    scian_325412.shp
    scian_325412.shx
    scian_325412.dbf
    scian_325412.prj
    scian_325412.cpg
  scian_334410/
    ...
```

Each run replaces the previous output for that zip.

A shapefile is several files with the same name; keep them together:

| File | Contents |
|---|---|
| `.shp`, `.shx`, `.dbf` | points, index and attributes (all required) |
| `.prj` | coordinate system: WGS 84 (EPSG:4326) |
| `.cpg` | text encoding (UTF-8), so accents display correctly |

To use them in ArcGIS Pro, add the `output/<zip name>/` folder as a folder connection in the Catalog pane,
then drag the shapefiles onto a map. The class name of each layer is in its `nombre_act` field.

The attributes are DENUE's original fields (in Spanish), including `codigo_act` and `nombre_act`
(class), `nom_estab` (name), `per_ocu` (size by employees), address fields, `municipio`,
`latitud`/`longitud` and `fecha_alta`. Their full descriptions are in
`diccionario_de_datos/denue_diccionario_de_datos.csv` inside the zip.

## Data source

DENUE data is published by [INEGI](https://www.inegi.org.mx/) under the
[Términos de Libre Uso de la Información del INEGI](https://www.inegi.org.mx/inegi/terminos.html).
