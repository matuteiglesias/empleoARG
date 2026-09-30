from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict

from .model import Geography, Indicator


def norm(text: object) -> str:
    value = "" if text is None else str(text)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower().replace("º", "o").replace("°", "o")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


GEOGRAPHIES: tuple[Geography, ...] = (
    Geography("total_31", "total_31_agglomerates", "Total 31 aglomerados urbanos", ("total 31 aglomerados urbanos", "total 31 aglomerados", "31 aglomerados urbanos", "total")),
    Geography("region", "gran_buenos_aires", "Gran Buenos Aires", ("gran buenos aires", "region gran buenos aires", "gba")),
    Geography("region", "cuyo", "Cuyo", ("cuyo", "region cuyo")),
    Geography("region", "noreste", "Noreste", ("noreste", "noreste argentino", "nea", "region noreste")),
    Geography("region", "noroeste", "Noroeste", ("noroeste", "noroeste argentino", "noa", "region noroeste")),
    Geography("region", "pampeana", "Pampeana", ("pampeana", "region pampeana")),
    Geography("region", "patagonia", "Patagonia", ("patagonia", "patagonica", "region patagonia")),
    Geography("agglomerate", "gran_la_plata", "Gran La Plata", ("gran la plata",), "02"),
    Geography("agglomerate", "bahia_blanca_cerri", "Bahía Blanca-Cerri", ("bahia blanca cerri", "bahia blanca - cerri"), "03"),
    Geography("agglomerate", "gran_rosario", "Gran Rosario", ("gran rosario",), "04"),
    Geography("agglomerate", "gran_santa_fe", "Gran Santa Fe", ("gran santa fe",), "05"),
    Geography("agglomerate", "gran_parana", "Gran Paraná", ("gran parana",), "06"),
    Geography("agglomerate", "posadas", "Posadas", ("posadas",), "07"),
    Geography("agglomerate", "gran_resistencia", "Gran Resistencia", ("gran resistencia",), "08"),
    Geography("agglomerate", "comodoro_rivadavia_rada_tilly", "Comodoro Rivadavia-Rada Tilly", ("comodoro rivadavia rada tilly", "comodoro rivadavia - rada tilly"), "09"),
    Geography("agglomerate", "gran_mendoza", "Gran Mendoza", ("gran mendoza",), "10"),
    Geography("agglomerate", "corrientes", "Corrientes", ("corrientes",), "12"),
    Geography("agglomerate", "gran_cordoba", "Gran Córdoba", ("gran cordoba",), "13"),
    Geography("agglomerate", "concordia", "Concordia", ("concordia",), "14"),
    Geography("agglomerate", "formosa", "Formosa", ("formosa",), "15"),
    Geography("agglomerate", "neuquen_plottier", "Neuquén-Plottier", ("neuquen plottier", "neuquen - plottier"), "17"),
    Geography("agglomerate", "santiago_del_estero_la_banda", "Santiago del Estero-La Banda", ("santiago del estero la banda", "santiago del estero - la banda"), "18"),
    Geography("agglomerate", "jujuy_palpala", "Jujuy-Palpalá", ("jujuy palpala", "jujuy - palpala"), "19"),
    Geography("agglomerate", "rio_gallegos", "Río Gallegos", ("rio gallegos",), "20"),
    Geography("agglomerate", "gran_catamarca", "Gran Catamarca", ("gran catamarca",), "22"),
    Geography("agglomerate", "salta", "Salta", ("salta",), "23"),
    Geography("agglomerate", "la_rioja", "La Rioja", ("la rioja",), "25"),
    Geography("agglomerate", "gran_san_luis", "Gran San Luis", ("gran san luis", "san luis el chorrillo", "san luis - el chorrillo"), "26"),
    Geography("agglomerate", "gran_san_juan", "Gran San Juan", ("gran san juan",), "27"),
    Geography("agglomerate", "gran_tucuman_tafi_viejo", "Gran Tucumán-Tafí Viejo", ("gran tucuman tafi viejo", "gran tucuman - tafi viejo"), "29"),
    Geography("agglomerate", "santa_rosa_toay", "Santa Rosa-Toay", ("santa rosa toay", "santa rosa - toay"), "30"),
    Geography("agglomerate", "ushuaia_rio_grande", "Ushuaia-Río Grande", ("ushuaia rio grande", "ushuaia - rio grande"), "31"),
    Geography("agglomerate", "caba", "Ciudad Autónoma de Buenos Aires", ("ciudad autonoma de buenos aires", "caba", "ciudad de buenos aires"), "32"),
    Geography("agglomerate", "partidos_del_gba", "Partidos del GBA", ("partidos del gba", "partidos del gran buenos aires", "conurbano bonaerense"), "33"),
    Geography("agglomerate", "mar_del_plata", "Mar del Plata", ("mar del plata", "mar del plata batán", "mar del plata batan"), "34"),
    Geography("agglomerate", "rio_cuarto", "Río Cuarto", ("rio cuarto",), "36"),
    Geography("agglomerate", "san_nicolas_villa_constitucion", "San Nicolás-Villa Constitución", ("san nicolas villa constitucion", "san nicolas - villa constitucion"), "38"),
    Geography("agglomerate", "rawson_trelew", "Rawson-Trelew", ("rawson trelew", "rawson - trelew"), "91"),
)

INDICATORS: tuple[Indicator, ...] = (
    Indicator("activity_rate", "Tasa de actividad", ("tasa de actividad", "actividad"), "percent", "poblacion economicamente activa", "poblacion total eph"),
    Indicator("employment_rate", "Tasa de empleo", ("tasa de empleo", "empleo"), "percent", "poblacion ocupada", "poblacion total eph"),
    Indicator("unemployment_rate", "Tasa de desocupación", ("tasa de desocupacion", "tasa de desempleo", "desocupacion", "desempleo"), "percent", "poblacion desocupada", "poblacion economicamente activa"),
    Indicator("subemployment_rate", "Tasa de subocupación", ("tasa de subocupacion", "tasa de subempleo", "subocupacion", "subempleo"), "percent", "poblacion subocupada", "poblacion economicamente activa"),
    Indicator("employed_job_seekers_rate", "Ocupados demandantes de empleo", ("ocupados demandantes de empleo", "ocupados demandantes"), "percent", "poblacion ocupada demandante de empleo", "poblacion economicamente activa"),
    Indicator("demanding_subemployment_rate", "Subocupación demandante", ("subocupacion demandante", "subocupados demandantes"), "percent", "poblacion subocupada demandante", "poblacion economicamente activa"),
    Indicator("non_demanding_subemployment_rate", "Subocupación no demandante", ("subocupacion no demandante", "subocupados no demandantes"), "percent", "poblacion subocupada no demandante", "poblacion economicamente activa"),
)

GEO_BY_ID = {g.geography_id: g for g in GEOGRAPHIES}
INDICATOR_BY_ID = {i.indicator_id: i for i in INDICATORS}

_GEO_ALIAS = {norm(alias): g for g in GEOGRAPHIES for alias in (g.geography_label, *g.aliases)}
_IND_ALIAS = {norm(alias): i for i in INDICATORS for alias in (i.indicator_label, *i.aliases)}

CORE_INDICATORS = ("activity_rate", "employment_rate", "unemployment_rate", "subemployment_rate")
REQUIRED_GEOGRAPHIES = ("total_31_agglomerates", "gran_buenos_aires", "cuyo", "noreste", "noroeste", "pampeana", "patagonia")


def match_geography(value: object) -> Geography | None:
    key = norm(value)
    if not key:
        return None
    if key in _GEO_ALIAS:
        return _GEO_ALIAS[key]
    # Exact repo-owned source code may appear separately from a label; never map bare
    # arbitrary numbers to geographies here.
    return None


def match_indicator(value: object) -> Indicator | None:
    key = norm(value)
    if not key:
        return None
    if key in _IND_ALIAS:
        return _IND_ALIAS[key]
    # Human tables often wrap labels in footnote text. Only accept a unique contained
    # alias with enough semantic specificity.
    matches = {ind for alias, ind in _IND_ALIAS.items() if len(alias) >= 10 and alias in key}
    return next(iter(matches)) if len(matches) == 1 else None


def geography_registry_json() -> list[dict]:
    return [asdict(g) for g in GEOGRAPHIES]


def indicator_registry_json() -> list[dict]:
    return [asdict(i) for i in INDICATORS]
