import pathlib
import streamlit as st
import pandas as pd
import numpy as np

# ladybug-charts uses deprecated pandas freq aliases (eg. "H") removed in pandas 2.2+.
# Patch pd.date_range so old aliases are silently mapped to their new names.
_orig_date_range = pd.date_range
_freq_alias_map = {'H': 'h', 'T': 'min', 'S': 's', 'L': 'ms', 'U': 'us', 'N': 'ns',
                   'M': 'ME', 'Q': 'QE', 'A': 'YE', 'Y': 'YE'}
def _patched_date_range(*args, **kwargs):
    if 'freq' in kwargs and isinstance(kwargs['freq'], str):
        kwargs['freq'] = _freq_alias_map.get(kwargs['freq'], kwargs['freq'])
    return _orig_date_range(*args, **kwargs)
pd.date_range = _patched_date_range

# applymap was removed in pandas 2.2+ (renamed to map)
if not hasattr(pd.DataFrame, 'applymap'):
    pd.DataFrame.applymap = pd.DataFrame.map

from ladybug.epw import EPW

from helper import colorsets, get_fields, field_label, get_hourly_data_figure, \
    get_bar_chart_figure, get_hourly_line_chart_figure, get_figure_config,\
    get_hourly_diurnal_average_chart_figure, get_daily_chart_figure, get_sunpath_figure,\
    get_degree_days_figure, get_windrose_figure, get_psy_chart_figure, \
    get_diurnal_average_chart_figure

st.set_page_config(
    page_title='ECO Consultor · Reporte Climático', layout='wide',
    page_icon='assets/branding/logo_eco.png'
)

st.sidebar.image('assets/branding/logo_eco.png', use_container_width=True)

# El manual de marca de ECO Consultor usa "Gotham" (tipografía de pago, no disponible
# en Google Fonts) y "Dosis" para descripciones. Aplicamos Dosis a los encabezados,
# que sí se puede incrustar libremente.
st.markdown(
    '''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Dosis:wght@400;600;700&display=swap');
    h1, h2, h3 { font-family: 'Dosis', sans-serif !important; }
    </style>
    ''',
    unsafe_allow_html=True
)


def main():

    ####################################################################################
    # Panel de control
    ####################################################################################
    with st.sidebar:

        # Un diccionario con el nombre de cada variable del EPW y su número de campo
        fields = get_fields()

        # archivo epw #####################################################################
        with st.expander('Cargar archivo EPW'):
            epw_data = st.file_uploader('', type='epw')
            if epw_data:
                epw_file = pathlib.Path(f'./data/{epw_data.name}')
                epw_file.parent.mkdir(parents=True, exist_ok=True)
                epw_file.write_bytes(epw_data.read())
            else:
                epw_file = './assets/sample.epw'

            global_epw = EPW(epw_file)

        # Paleta de colores global ##############################################################
        with st.expander('Paleta de colores global'):
            global_colorset = st.selectbox('', list(colorsets.keys()))

        st.markdown('---')

        # gráfico de promedio diurno #########################################################
        with st.expander('Gráfico de promedio diurno'):
            diurnal_average_chart_switch = st.checkbox(
                'Invertir colores', value=False, key='diurnal_average_chart_switch',
                help='Invierte el orden de la paleta de colores')

        # Datos horarios ##################################################################
        with st.expander('Datos horarios'):
            hourly_selected = st.selectbox(
                'Selecciona una variable ambiental', options=fields.keys(),
                format_func=field_label, key='hourly_data')
            hourly_data = global_epw.get_data_by_field(fields[hourly_selected])
            hourly_data_conditional_statement = st.text_input(
                'Aplicar declaración condicional')
            hourly_data_min = st.text_input('Mínimo')
            hourly_data_max = st.text_input('Máximo')

            hourly_data_st_month = st.number_input(
                'Mes inicial', min_value=1, max_value=12, value=1, key='hourly_data_st_month')
            hourly_data_end_month = st.number_input(
                'Mes final', min_value=1, max_value=12, value=12, key='hourly_data_end_month')

            hourly_data_st_day = st.number_input(
                'Día inicial', min_value=1, max_value=31, value=1, key='hourly_data_st_day')
            hourly_data_end_day = st.number_input(
                'Día final', min_value=1, max_value=31, value=31, key='hourly_data_end_day')

            hourly_data_st_hour = st.number_input(
                'Hora inicial', min_value=0, max_value=23, value=0, key='hourly_data_st_hour')
            hourly_data_end_hour = st.number_input(
                'Hora final', min_value=0, max_value=23, value=23, key='hourly_data_end_hour')

        # Gráfico de barras ####################################################################
        with st.expander('Gráfico de barras'):

            bar_chart_selection = []
            for var in fields.keys():
                if var == 'Dry Bulb Temperature' or var == 'Relative Humidity':
                    bar_chart_selection.append(st.checkbox(field_label(var), value=True))
                else:
                    bar_chart_selection.append(st.checkbox(field_label(var), value=False))

            bar_chart_data_type = st.selectbox('', ('Promedio mensual', 'Total mensual',
                                                    'Promedio diario',
                                                    'Total diario'), key=0)
            bar_chart_switch = st.checkbox(
                'Invertir colores', value=False, key='bar_chart_switch',
                help='Invierte el orden de la paleta de colores')
            bar_chart_stack = st.checkbox('Apilar', value=False, key='bar_chart_stacked')

        # Gráfico de línea horaria ############################################################
        with st.expander('Gráfico de línea horaria'):

            hourly_line_chart_selected = st.selectbox(
                'Selecciona una variable ambiental', options=fields.keys(), index=2,
                format_func=field_label, key='line_chart')
            hourly_line_chart_data = global_epw.get_data_by_field(
                fields[hourly_line_chart_selected])

            hourly_line_chart_switch = st.checkbox('Invertir colores', key='line_chart_switch',
                                                   help='Invierte el orden de la paleta de colores')

        # Gráfico de promedio diurno (datos horarios) ##########################################
        with st.expander('Promedio diurno a partir de datos horarios'):

            diurnal_average_chart_hourly_selected = st.selectbox(
                'Selecciona una variable ambiental', options=fields.keys(), index=8,
                format_func=field_label, key='hourly_diurnal_average_chart')
            diurnal_average_chart_hourly_data = global_epw.get_data_by_field(
                fields[diurnal_average_chart_hourly_selected])

            diurnal_average_chart_hourly_switch = st.checkbox(
                'Invertir colores', key='hourly_diurnal_average_chart_switch',
                help='Invierte el orden de la paleta de colores')

        # Gráfico diario ###################################################################
        with st.expander('Gráfico diario'):

            daily_chart_selected = st.selectbox(
                'Selecciona una variable ambiental', options=fields.keys(), index=16,
                format_func=field_label, key='daily_chart')
            daily_chart_data = global_epw.get_data_by_field(
                fields[daily_chart_selected])

            daily_chart_switch = st.checkbox('Invertir colores', key='daily_chart_switch',
                                             help='Invierte el orden de la paleta de colores')

        # Recorrido solar #######################################################################
        with st.expander('Recorrido solar'):

            sunpath_radio = st.radio(
                'Método del recorrido solar',
                ['desde la ubicación del EPW', 'con datos del EPW'],
                index=0, key='sunpath_visualization_method'
            )

            if sunpath_radio == 'desde la ubicación del EPW':
                sunpath_switch = st.checkbox('Invertir colores', key='sunpath_switch',
                                             help='Invierte el orden de la paleta de colores')
                sunpath_data = None

            else:
                sunpath_selected = st.selectbox(
                    'Selecciona una variable ambiental', options=fields.keys(),
                    format_func=field_label, key='sunpath')
                sunpath_data = global_epw.get_data_by_field(fields[sunpath_selected])
                sunpath_switch = None

        # Grados-día ###################################################################
        with st.expander('Grados-día'):

            degree_days_stack = st.checkbox('Apilar')

            degree_days_heat_base = st.number_input('Temperatura base de calefacción',
                                                    value=18)

            degree_days_switch = st.checkbox('Invertir colores', key='degree_switch',
                                             help='Invierte el orden de la paleta de colores')

            degree_days_cool_base = st.number_input('Temperatura base de enfriamiento',
                                                    value=23)

        # Rosa de vientos ######################################################################
        with st.expander('Rosa de vientos'):

            windrose_st_month = st.number_input(
                'Mes inicial', min_value=1, max_value=12, value=1, key='windrose_st_month')
            windrose_end_month = st.number_input(
                'Mes final', min_value=1, max_value=12, value=12, key='windrose_end_month')

            windrose_st_day = st.number_input(
                'Día inicial', min_value=1, max_value=31, value=1, key='windrose_st_day')
            windrose_end_day = st.number_input(
                'Día final', min_value=1, max_value=31, value=31, key='windrose_end_day')

            windrose_st_hour = st.number_input(
                'Hora inicial', min_value=0, max_value=23, value=0, key='windrose_st_hour')
            windrose_end_hour = st.number_input(
                'Hora final', min_value=0, max_value=23, value=23, key='windrose_end_hour')

        # Carta psicrométrica ############################################################
        with st.expander('Carta psicrométrica'):

            psy_load_data = st.checkbox('Cargar datos', key='psychrometric')
            if psy_load_data:
                psy_selected = st.selectbox(
                    'Selecciona una variable ambiental',
                    options=fields.keys(), format_func=field_label, key='psychrometric'
                )
                psy_data = global_epw.get_data_by_field(fields[psy_selected])
            else:
                psy_data = None

            psy_draw_polygons = st.checkbox(
                'Dibujar polígonos de confort', key='psychrometric_polygon'
            )
            psy_strategy_options = ['Confort', 'Enfriamiento evaporativo',
                                    'Masa + ventilación nocturna', 'Uso de ventiladores',
                                    'Captura de calor interno', 'Calefacción solar pasiva', 'Todas']
            psy_selected_strategy = st.selectbox(
                'Selecciona una estrategia pasiva',
                options=psy_strategy_options, key='psychrometric_passive_strategy'
            )

    ####################################################################################
    # Página principal
    ####################################################################################
    with st.container():
        st.title('ECO Consultor — Visualizador de Datos Climáticos')

        st.markdown('Bienvenido a la aplicación de visualización de datos climáticos de ECO'
                    ' Consultor. Carga un archivo EPW de tu sistema para visualizarlo. Por'
                    ' defecto, la aplicación carga el archivo EPW de Boston, EE. UU.')
        st.markdown('🖱️ Pasa el mouse sobre cada gráfico para ver los valores.')

        st.info(
            body='Esta aplicación fue desarrollada por **ECO Consultor** para visualizar y '
            'analizar archivos climáticos EPW como apoyo a nuestros estudios de eficiencia '
            'energética y confort térmico en edificaciones.\n\nEstá construida sobre la '
            'librería de código abierto `ladybug-charts`. Puedes ver el código fuente '
            '[aquí](https://github.com/Sogo2012/weather-report).'
        )

        st.header(f'{global_epw.location.city}, {global_epw.location.country}')

        # imagen y mapa ################################################################
        st.text(
            f'Latitud: {global_epw.location.latitude}, Longitud: {global_epw.location.longitude},'
            f' Zona horaria: {global_epw.location.time_zone}, fuente: {global_epw.location.source}')

        with st.expander('Cargar imagen desde el equipo'):
            local_image = st.file_uploader(
                'Selecciona una imagen', type=['png', 'jpg', 'jpeg'])

        if local_image:
            st.image(local_image)

        location = pd.DataFrame(
            [np.array([global_epw.location.latitude,
                        global_epw.location.longitude], dtype=np.float64)],
            columns=['latitude', 'longitude']
        )
        st.map(location, use_container_width=True)

        # Gráfico de promedio diurno a partir de datos horarios ########################################
        with st.container():
            st.header('Gráfico de promedio diurno')
            st.markdown(
                'Un gráfico que muestra cómo luce un día promedio en este clima, mes a mes.')

            diurnal_average_chart_figure = get_diurnal_average_chart_figure(
                global_epw, global_colorset, diurnal_average_chart_switch)

            st.plotly_chart(diurnal_average_chart_figure, use_container_width=True,
                            config=get_figure_config(
                                f'Grafico_promedio_diurno_{global_epw.location.city}'))

        # Datos horarios ##################################################################
        with st.container():
            st.header('Visualizar datos horarios')
            st.markdown(
                'Selecciona una variable ambiental del archivo EPW para visualizarla.'
                ' Por defecto, se usa la temperatura de bulbo seco.'
                ' Puedes usar la declaración condicional para filtrar los datos.'
                ' Por ejemplo, para ver la temperatura de bulbo seco por encima de 10, puedes'
                ' usar la declaración condicional "a>10" sin comillas.'
                ' Para ver la temperatura de bulbo seco entre -5 y 10 puedes usar la'
                ' declaración condicional "a>-5 and a<10" sin comillas.'
                ' También puedes usar los campos de mínimo y máximo para personalizar los'
                ' límites de los datos que estás visualizando y de la leyenda. Por defecto,'
                ' el gráfico usa los valores mínimo y máximo de los datos para definir los'
                ' límites.')

            hourly_data_figure = get_hourly_data_figure(
                hourly_data, global_colorset, hourly_data_conditional_statement,
                hourly_data_min, hourly_data_max, hourly_data_st_month, hourly_data_st_day,
                hourly_data_st_hour, hourly_data_end_month, hourly_data_end_day,
                hourly_data_end_hour)

            if isinstance(hourly_data_figure, str):
                st.error(hourly_data_figure)
            else:
                st.plotly_chart(hourly_data_figure, use_container_width=True,
                                config=get_figure_config(field_label(str(hourly_data.header.data_type))))

        # Gráfico de barras ####################################################################
        with st.container():
            st.header('Gráfico de barras')
            st.markdown(
                'Selecciona una o más variables ambientales del archivo EPW para'
                ' visualizarlas lado a lado en un gráfico de barras mensual o diario. Por'
                ' defecto, están seleccionadas "temperatura de bulbo seco" y "humedad'
                ' relativa".')

            bar_chart_figure = get_bar_chart_figure(
                fields, global_epw, bar_chart_selection, bar_chart_data_type,
                bar_chart_switch, bar_chart_stack, global_colorset)

            st.plotly_chart(bar_chart_figure, use_container_width=True,
                            config=get_figure_config(f'{bar_chart_data_type}'))

        # Gráfico de línea horaria ############################################################
        with st.container():
            st.header('Gráfico de línea horaria')
            st.markdown(
                'Selecciona una variable ambiental del archivo EPW para visualizarla en un'
                ' gráfico de línea. Por defecto, se usa la humedad relativa.')

            hourly_line_chart_figure = get_hourly_line_chart_figure(
                hourly_line_chart_data, hourly_line_chart_switch, global_colorset)

            st.plotly_chart(hourly_line_chart_figure, use_container_width=True,
                            config=get_figure_config(field_label(hourly_line_chart_selected)))

        # Gráfico de promedio diurno a partir de datos horarios ########################################
        with st.container():
            st.header('Gráfico de promedio diurno (datos horarios)')
            st.markdown(
                'Selecciona una variable ambiental del archivo EPW para visualizarla en un'
                ' gráfico de promedio diurno. Por defecto, se usa la radiación normal'
                ' directa.')

            per_hour_line_chart_figure = get_hourly_diurnal_average_chart_figure(
                diurnal_average_chart_hourly_data, diurnal_average_chart_hourly_switch,
                global_colorset)

            st.plotly_chart(per_hour_line_chart_figure, use_container_width=True,
                            config=get_figure_config(
                                field_label(diurnal_average_chart_hourly_data.header.data_type.name)))

        # Gráfico diario ###################################################################
        with st.container():

            st.header('Gráfico diario')
            st.markdown(
                'Selecciona una variable ambiental del archivo EPW para visualizarla en un'
                ' gráfico diario. Este gráfico muestra los valores promedio de cada día. Por'
                ' defecto, se usa la cobertura total de nubes.')

            daily_chart_figure = get_daily_chart_figure(
                daily_chart_data, daily_chart_switch, global_colorset)

            st.plotly_chart(daily_chart_figure, use_container_width=True,
                            config=get_figure_config(
                                field_label(daily_chart_data.header.data_type.name)))

        # Recorrido solar #######################################################################
        with st.container():

            st.header('Recorrido solar')
            st.markdown('Genera un recorrido solar (sunpath) a partir de la ubicación del'
                        ' EPW. Adicionalmente, puedes cargar una de las variables'
                        ' ambientales del archivo EPW sobre el recorrido solar.'
                        )

            sunpath_figure = get_sunpath_figure(
                sunpath_radio, global_colorset, global_epw, sunpath_switch, sunpath_data)

            st.plotly_chart(sunpath_figure, use_container_width=True,
                            config=get_figure_config(
                                f'Recorrido_solar_{global_epw.location.city}'))

        # Grados-día ###################################################################
        with st.container():

            st.header('Grados-Día')
            st.markdown('Calcula los grados-día de calefacción y enfriamiento.'
                        ' Tradicionalmente, los grados-día se definen como la diferencia'
                        ' entre una temperatura base y la temperatura ambiente promedio,'
                        ' multiplicada por la cantidad de días en que existe esa diferencia.'
                        ' Por defecto, las temperaturas base de calefacción y enfriamiento'
                        ' están configuradas en 18°C y 23°C respectivamente.'
                        ' Esto significa que se asume que por debajo de la temperatura base'
                        ' de calefacción se activará la calefacción, y por encima de la'
                        ' temperatura base de enfriamiento se activará el enfriamiento.')

            degree_days_figure, hourly_heat, hourly_cool = get_degree_days_figure(
                global_epw.dry_bulb_temperature, degree_days_heat_base,
                degree_days_cool_base, degree_days_stack, degree_days_switch,
                global_colorset)

            st.plotly_chart(degree_days_figure, use_container_width=True,
                            config=get_figure_config(
                                f'Grados_dia_{global_epw.location.city}'))
            st.text(
                f'Los grados-día de enfriamiento totales son {round(hourly_cool.total)}'
                f' y los grados-día de calefacción totales son {round(hourly_heat.total)}.')

        # Rosa de vientos ######################################################################
        with st.container():
            st.header('Rosa de vientos')
            st.markdown('Genera un diagrama de rosa de vientos.')

            windrose_figure = get_windrose_figure(
                windrose_st_month, windrose_st_day, windrose_st_hour, windrose_end_month,
                windrose_end_day, windrose_end_hour, global_epw, global_colorset)

            st.plotly_chart(windrose_figure, use_container_width=True,
                            config=get_figure_config(
                                f'Rosa_de_vientos_{global_epw.location.city}'))

        # Carta psicrométrica ###########################################################
        with st.container():
            st.header('Carta Psicrométrica')
            st.markdown(
                'Genera una carta psicrométrica con la temperatura de bulbo seco y la'
                ' humedad relativa del archivo climático. Puedes cargar una de las'
                ' variables ambientales del EPW sobre la carta psicrométrica.'
                ' Adicionalmente, puedes agregar polígonos de confort seleccionando una de'
                ' las estrategias pasivas. Por defecto, la carta psicrométrica muestra las'
                ' horas del año en que ocurre cierta combinación de temperatura de bulbo'
                ' seco y humedad relativa.')

            psy_chart_figure = get_psy_chart_figure(
                global_epw, global_colorset, psy_selected_strategy, psy_load_data,
                psy_draw_polygons, psy_data)

            st.plotly_chart(psy_chart_figure, use_container_width=True,
                            config=get_figure_config(
                                f'Carta_psicrometrica_{global_epw.location.city}'))


if __name__ == '__main__':
    main()
