# Empleo Argentina — series trimestrales de la EPH

Extracción y normalización de series de empleo y desempleo publicadas en el apéndice estadístico del Ministerio de Economía de la Nación.

> **Estado:** snapshot histórico en mantenimiento. La última actualización sustantiva identificada incorporó datos en 2023; el push de diciembre de 2024 agregó un archivo de tooling y no constituye una actualización de las series. La fuente y el pipeline no fueron revalidados en 2026.

## Qué contiene

El repositorio conserva:

- `Descargador de Datos Oficiales.ipynb`: notebook de descarga y extracción;
- `datos/apendice3a.xlsx`: copia de la fuente utilizada por el pipeline;
- `datos/42.3_EPH_PUNTUA.csv`: series de la EPH puntual;
- `datos/45.2_ECTDT.csv`: series trimestrales por aglomerado y región.

La fuente histórica configurada es:

```text
https://www.economia.gob.ar/download/infoeco/apendice3a.xlsx
```

## Uso recomendado

Para análisis reproducible, utilizar los CSV comprometidos y registrar el commit exacto:

```python
import pandas as pd

empleo = pd.read_csv(
    "datos/45.2_ECTDT.csv",
    parse_dates=[0],
    index_col=0,
)
print(empleo.tail())
```

Para reconstruir la extracción, abrir `Descargador de Datos Oficiales.ipynb` y revisar primero que:

- la URL continúe disponible;
- los nombres de las hojas no hayan cambiado;
- las claves de serie sigan representando los mismos indicadores;
- las dependencias `pandas`, `requests` y `openpyxl` sean compatibles.

## Verificación de frescura

[`DATA_STATUS.json`](DATA_STATUS.json) declara el corte del snapshot y separa una actualización de datos de un push cualquiera al repositorio.

```bash
python scripts/verify_snapshot.py
```

Este chequeo confirma que `datos/45.2_ECTDT.csv` sigue terminando en el período declarado. No descarga la fuente ni demuestra que el notebook todavía pueda ejecutarse. No se identificó automatización versionada dentro del repositorio.

## Autoridad y límites

Este repositorio posee el **snapshot procesado y la lógica histórica de extracción**. No es la publicación oficial ni garantiza que los valores reflejen la última edición del apéndice.

La serie presenta períodos con cambios de cobertura y valores faltantes. Las columnas codificadas deben interpretarse utilizando los metadatos de la fuente, no solamente su nombre interno.

## Próxima revisión útil

Una revisión de mantenimiento debería:

1. descargar la versión corriente de `apendice3a.xlsx`;
2. comparar hojas, códigos y cobertura con el snapshot;
3. ejecutar la extracción en un entorno limpio;
4. declarar la fecha máxima de cada output;
5. decidir si la actualización debe volver a automatizarse.

Hasta entonces, describir los archivos como datos históricos versionados.

## Posible cambio de nombre

`empleoARG` es reconocible pero poco explícito. `empleo-arg-series` o `argentina-employment-series` mejorarían la búsqueda; el cambio no es necesario para que el repositorio sea legible.
