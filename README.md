# DENUE shapefiles by activity class

Splits a state's [DENUE](https://www.inegi.org.mx/app/mapa/denue/) download from INEGI into one
shapefile per SCIAN activity class (*clase de actividad económica*), grouped into one folder per
ReflexIA strategic sector and ready to add as layers in ArcGIS Pro. Only the classes you list are
extracted; each shapefile holds one point per establishment, of every size.

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

- Three columns, with the header `scian_class_id,scian_class_name,reflexia_sector` on the first line.
- One class per line: its 6-digit SCIAN code (codes can be looked up in INEGI's
  [SCIAN classifier](https://www.inegi.org.mx/app/scian/)), its name, and its ReflexIA sector.
- The name and sector are required, and they become folder names, so they can't contain
  `\ / : * ? " < > |`. Names with commas need quotes.
- A code can appear under several sectors, but only once in each. UTF-8 encoding.

```csv
scian_class_id,scian_class_name,reflexia_sector
311110,Elaboración de alimentos balanceados para animales,Agroalimentario
334519,"Fabricación de otros instrumentos de medición, control, navegación, y equipo médico electrónico",Electrónica y semiconductores
334519,"Fabricación de otros instrumentos de medición, control, navegación, y equipo médico electrónico",Farmacéutica y servicios de salud
```

If the CSV breaks any rule, the script stops without writing anything and lists each problem with
its line number.

## Usage

```bash
source .venv/bin/activate
python main.py input/scian_class_ids.csv input/denue_09_shp.zip
```

The script prints how many establishments each class has and lists any class with none in the state;
those classes get no folder, and a sector with no establishments gets none either.

## Output

One folder per sector in `output/<zip name>/`, holding one folder per class, named with its SCIAN
code and name. Each class folder holds that class's shapefile, named after its SCIAN code:

```
output/denue_09_shp/
  Agroalimentario/
    311110 Elaboración de alimentos balanceados para animales/
      scian_311110.shp
      scian_311110.shx
      scian_311110.dbf
      scian_311110.prj
      scian_311110.cpg
  Turismo/
    ...
```

A class listed under several sectors is written to each of them, so its establishments appear in
each sector's folder; the total the script prints counts them once.

Each run replaces the previous output for that zip.

Class names make these paths long, up to about 220 characters from the project folder. Windows
usually limits paths to 259 characters, so keep the project in a short path there.

A shapefile is several files with the same name; keep them together:

| File | Contents |
|---|---|
| `.shp`, `.shx`, `.dbf` | points, index and attributes (all required) |
| `.prj` | coordinate system: WGS 84 (EPSG:4326) |
| `.cpg` | text encoding (UTF-8), so accents display correctly |

To use them in ArcGIS Pro, add the `output/<zip name>/` folder as a folder connection in the Catalog pane,
then drag the shapefiles onto a map. The class name of each layer is in its folder name, and DENUE's
own wording of it is in the `nombre_act` field.

The attributes are DENUE's original fields (in Spanish), including `codigo_act` and `nombre_act`
(class), `nom_estab` (name), `per_ocu` (size by employees), address fields, `municipio`,
`latitud`/`longitud` and `fecha_alta`. Their full descriptions are in
`diccionario_de_datos/denue_diccionario_de_datos.csv` inside the zip.

## Data source

DENUE data is published by [INEGI](https://www.inegi.org.mx/) under the
[Términos de Libre Uso de la Información del INEGI](https://www.inegi.org.mx/inegi/terminos.html).
