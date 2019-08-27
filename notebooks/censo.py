import geopandas as gpd
import pandas as pd
import requests
from bs4 import BeautifulSoup

def cargar_tabla(soup):
    df_data = {
        'radio_cens': [],
        'tipo_vivienda': [],
        'casos': []
    }
    rows = soup.find('table').find_all('tr')
    rows_with_data = [r.text.replace('\n', ' ').strip() for r in rows][13:-5]
    resumen = rows_with_data[-10:]
    data_por_radio_censal = rows_with_data[:-13]

    radio_censal = None
    for r in data_por_radio_censal:
        if not len(r):
            continue
        cells = [i for i in r.split('  ') if len(i)]
        key = cells[0]
        if 'AREA #' in key:
            radio_censal = int(r.replace('AREA # ', '').split(' ')[0])
            continue
        elif key == 'Tabla vacía':
            df_data['radio_cens'].append(radio_censal)
            df_data['tipo_vivienda'].append('Total')
            df_data['casos'].append(0)

        elif len(cells) > 1:
            resultados = cells[1].strip().split(' ')
            try:
                casos = int(resultados[0])
            except ValueError:
                continue
            df_data['radio_cens'].append(radio_censal)
            df_data['tipo_vivienda'].append(key)
            df_data['casos'].append(casos)
        else:
            continue
    df = pd.DataFrame(columns=df_data.keys(), data=df_data)

    for rc in df.radio_cens.unique():
        resultados = df.loc[df.radio_cens == rc]
        for tv in df.tipo_vivienda.unique():
            if tv in resultados.tipo_vivienda.unique():
                continue
            df_data['radio_cens'].append(rc)
            df_data['tipo_vivienda'].append(tv)
            df_data['casos'].append(0)

    df = pd.DataFrame(columns=df_data.keys(), data=df_data)
    return df.pivot_table('casos', ['radio_cens'], 'tipo_vivienda')

def bajar_datos_del_censo(query):
    url_request = 'https://redatam.indec.gob.ar/argbin/RpWebEngine.exe/Frequency'
    params = {
        'MAIN': 'WebServerMain.inl',
        'BASE': 'CPV2010B',
        'CODIGO': 'xxUsuarioxx',
        'ITEM': 'FREQHOG',
        'MODE': 'RUN',
        'TITLE': '',

        'VARIABLE': 'HOGAR.HV01',
        'AREABREAK': 'RADIO',
        'SELECT': 'Sels\Prov82.sel',
        'INLINESELECTION': '',
        'SEL_FILTER': '',
        'FILTER': query,
        'FORMAT': 'HTML',
        'SUBMIT': 'Ejecutar',
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r_1 = requests.get(url_request, params=params, headers=headers)
    html = BeautifulSoup(r_1.text, 'html.parser')
    url_data = html.find('iframe').attrs['src']
    html_data = BeautifulSoup(requests.get(url_data).text,
                              'html.parser')
    return html_data

def cargar_mapa(path):
    shape = gpd.read_file(path)
    shape.crs = {'init': 'epsg:27700'}
    shape.to_crs(epsg=4326)
    return shape

