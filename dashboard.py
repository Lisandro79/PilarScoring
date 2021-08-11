import json
import pickle
from os import path

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import numpy as np
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output

data_dir = './data/'
general_election = pd.read_csv(path.join(data_dir, 'generales.csv'))
general_election_2017 = pd.read_csv(path.join(data_dir, 'generales_2017.csv'))
paso_election = pd.read_csv(path.join(data_dir, 'paso.csv'))
volatility = pd.read_csv(path.join(data_dir, 'volatility.csv'))

with open(path.join(data_dir, 'parties.pkl'), 'rb') as open_file:
    parties = pickle.load(open_file)

with open(path.join(data_dir, 'parties_2017.pkl'), 'rb') as open_file:
    parties_2017 = pickle.load(open_file)

with open(path.join(data_dir, 'counties.pkl'), 'rb') as open_file:
    localidades = pickle.load(open_file)

with open(path.join(data_dir, 'features.pkl'), 'rb') as open_file:
    features = pickle.load(open_file)

data_loc = './geographical_data/buenos_aires.geojson'
with open(data_loc) as open_file:
    geojson = json.load(open_file)

election_type = ['2019', '2019-paso', '2017']

year_partidos_centro = {'2019': ['CONSENSO FEDERAL', 'FRENTE NOS', 'CONSENSO FEDERAL + FRENTE NOS'],
                        '2019-paso': ['CONSENSO FEDERAL', 'FRENTE NOS', 'CONSENSO FEDERAL + FRENTE NOS'],
                        '2017': ['1PAIS', 'FRENTE JUSTICIALISTA', 'SUMEMOS PILAR',
                                 '1PAIS + FRENTE JUSTICIALISTA', '1PAIS + SUMEMOS PILAR',
                                 'FRENTE JUSTICIALISTA + SUMEMOS PILAR',
                                 '1PAIS + FRENTE JUSTICIALISTA + SUMEMOS PILAR']}

data_loc = './geographical_data/Localidades_BuenosAires.geojson'
with open(data_loc) as open_file:
    geo_loc = json.load(open_file)
    lower_localidades = [loc.lower() for loc in localidades]
    geo_localidad = pd.DataFrame(columns=['localidad', 'lat', 'lon'])
    for idx, localidad in enumerate(geo_loc['features']):
        if localidad['properties']['nombre'].lower() in lower_localidades:
            coordinates = localidad['geometry']['coordinates']
            name = localidad['properties']['nombre']
            geo_localidad.loc[idx] = [name, coordinates[0][1], coordinates[0][0]]

colors = {
    'background': '#222',
    'text': '#fff'
}

council = 'PILAR'

# Dashboard
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE])
app.title = 'Dashboard Nous'
server = app.server

# Layout
app.layout = dbc.Container(
    [
        html.H1(children=f"Municipio: {council}"),

        # Section 1
        html.H2(children="Resultados Generales"),

        dbc.Row(dcc.Slider(id='slider-year',
                           value=2019, min=2019, max=2019, step=4,
                           marks={2019: '2019'})
                ),

        dbc.Row([dbc.Col(dcc.Graph(id='pie_chart'), width=5),
                 dbc.Col(dcc.Graph(id='votos_localidad'), width=5)]
                ),

        dbc.Row([dbc.Col(dcc.Graph(id='pie_chart_2017'), width=5),
                 dbc.Col(dcc.Graph(id='votos_localidad_2017'), width=5)]
                ),



        html.H2(children=f"Votos Centro"),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Row(
                        [
                            html.Div([
                                dcc.Dropdown(id='dropdown-votos-centro',
                                             options=[{'label': i, 'value': i} for i in election_type],
                                             value=election_type[0]
                                             ),
                                dcc.Dropdown(id='dropdown-partidos-centro',
                                             options=[{'label': i, 'value': i} for i in year_partidos_centro['2019']],
                                             value='CONSENSO FEDERAL + FRENTE NOS'),
                                html.Div(id='votos-centro-table')
                            ], style={"width": "100%"}
                            )
                        ]
                    ), width=10,
                ),

                dbc.Col(
                    dcc.Graph(id='googleMap'), width=10,
                )
            ]
        ),

        html.H4(children=f"Seleccione el número de mesas"),
        dcc.Slider(id='map-slider', min=1, max=700, step=1, value=200,
                   marks={i: f'{i}' for i in range(0, 700, 50)}),
        html.H4(children=f"Top mesas seleccionadas: "),
        html.Div(id='map-slider-value', style={'whiteSpace': 'pre-line'}),
        html.H4(children=f"Total Votantes: "),
        html.Div(id='total_voters', style={'whiteSpace': 'pre-line'}),

        html.Br(),
        html.Br(),
        html.H4(children=f"Elecciones 2017"),
        dcc.Graph(id='fig_2017'),

        # Section 2a: Resultados generales de Pilar, mesa por mesa
        html.H2(
            [
                "Resultados mesa por mesa de la elección general.",
                html.Br()
            ]
        ),
        html.P(
            ["El primer gráfico muestra la relación entre los votos de cada partido en las mesas electoraes. "
             "Los menus con los nombres de los partidos sirven para comparar resultados. Seleccione los partidos"
             " políticos que desea comparar",
             html.Br(),
             "El coeficiente de correlación de Pearson indica la asociación entre los votos recibidos por "
             "un partido y otro: a) r = 1 significa una perfecta asociación lineal (por cada 1% de aumento de "
             "los votos del partido A, el partido B aumenta 1%) , b) r = 0 significa que no existe asociación y "
             "c) r = -1 indica una asociación inversa (por cada 1% de aumento de los votos del partido A, "
             "el partido B disminuye 1%).",
             html.Br()
             ]
        ),

        dbc.Row(
            [
                dbc.Col(dcc.Dropdown(id='dropdown-scatter1',
                                     options=[{'label': i, 'value': i} for i in parties],
                                     value=parties[0]
                                     ), width=4),

                dbc.Col(dcc.Dropdown(id='dropdown-scatter2',
                                     options=[{'label': i, 'value': i} for i in parties],
                                     value=parties[1]
                                     ), width=4)
            ]
        ),

        dcc.Graph(id='scatter'),

        # Section 2b
        html.H3([html.Br(), "Proporción de votos por cada mesa"]),
        html.P(
            ["La mayoría de los votantes se dividen en dos partidos: el Frente "
             "de todos y Juntoso por el Cambio. El aumento de votantes de uno de estos partidos disminuye el "
             "la cantidad de votantes del otro. "
             "El filtro permite ordenar las mesas por voto para cada cada partido.",
             html.Br()
             ]
        ),

        dcc.Dropdown(id='dropdown-hbar',
                     options=[{'label': i, 'value': i} for i in parties],
                     value=parties[0]
                     ),
        dcc.Graph(id='hbar'),

        # Section 3: Resultados desagregados por Localidad, Mesa por Mesa
        html.H1(
            children=[html.Br(),
                      "Resultados Paso vs Elección General. "
                      ]
        ),
        html.P(
            children=[
                "En esta sección analizamos las diferencias en los votos, mesa por mesa entre las elecciones paso y "
                "las elecciones generales. A diferencia de los gráficos anteriores, esta sección permite "
                "filtrar los resultados electorales por cada localidad de Pilar. ",
                html.Br(),
                html.Br(),
                "Los resultados que presentamos a continuación muestran la diferencia en la proporción de votos"
                "recibidos desde las paso hasta las elecciones generales. Juntos por el cambio muestra un "
                "significativo aumento de la proporción de votantes de las paso a la elección general. ",
                html.Br(),
                "Eje vertical: proporción de votos desde las paso a la elección general "
                "para Juntos por el Cambio (valores positivos indican un aumento en la proporción de votos).",
                html.Br(),
                "Eje horizontal: proporción de votos para los demás partidos. ",
                html.Br(),
                "Seleccione el filtro para ver la correlación entre el aumento de votos para Juntos por el cambio "
                "y los resultados de los demas partidos.",
                html.Br()]
        ),

        dbc.Row(
            [
                dbc.Col(dcc.Dropdown(id='dropdown_county_volatility',
                                     options=[{'label': i, 'value': i} for i in localidades],
                                     value=localidades[0]
                                     ), width=4),
                dbc.Col(dcc.Dropdown(id='dropdown_county_parties',
                                     options=[{'label': i, 'value': i} for i in parties],
                                     value=parties[0]
                                     ), width=4),
            ]
        ),
        dcc.Graph(id='fig_volatility'),
        html.Div(id='first-table'),
        html.Div(id='second-table'),

        # Section 3: Resultados desagregados por Localidad, Mesa por Mesa
        html.H1(
            children=[html.Br(),
                      "Principales características demográficas de los votantes de cada partido. "
                      ]
        ),
        html.P(
            children=["Analizamos las caracteristicas socio-demograficas de los votantes de cada partido, "
                      "en cada una de las mesas de las principales localidaded de Pilar.",
                      html.Br(),
                      "El filtro permite seleccionar la proporción de votantes masculinos (pmale), la proporción de "
                      "votantes femeninos (pfemail), la proporción de votos por franja etaea (e.g., 18-25)y la "
                      "proporción de votos por franja etarea y género (e.g., 18-25_m, todos los votantes masculinos "
                      "entre 18 y 25 años, o 18-25_f, todos los votantes femeninos de entre 18 y 25 años. ",
                      html.Br(),
                      ]
        ),

        html.Div(id='third-table'),
        dbc.Row(
            [
                dbc.Col(dcc.Dropdown(id='dropdown-localidad',
                                     options=[{'label': i, 'value': i} for i in localidades],
                                     value=localidades[0]
                                     ), width=4),
                dbc.Col(dcc.Dropdown(id='dropdown-localidad-partidos',
                                     options=[{'label': i, 'value': i} for i in parties],
                                     value=parties[0]
                                     ), width=4),
                dbc.Col(dcc.Dropdown(id='dropdown-localidad-features',
                                     options=[{'label': i, 'value': i} for i in features],
                                     value=features[1]
                                     ), width=4)
            ]
        ),
        dcc.Graph(id='scatter-localidad', className='card'),

        # Hidden div inside the app that stores the intermediate value
        html.Div(id='intermediate-election', style={'display': 'none'}),
        html.Div(id='intermediate-paso', style={'display': 'none'}),
        html.Div(id='intermediate-election-2017', style={'display': 'none'}),
        html.Div(id='intermediate-volatility', style={'display': 'none'}),
        html.Div(id='intermediate-parties', style={'display': 'none'}),

    ], fluid=True
)


@app.callback([Output('dropdown-partidos-centro', 'options'),
               Output('dropdown-partidos-centro', 'value')],
              Input('dropdown-votos-centro', 'value'))
def update_dropdown(year):
    options = [{'label': i, 'value': i} for i in year_partidos_centro[year]]
    if year == '2019' or year == '2019-paso':
        value = options[2]['value']
    elif year == '2017':
        value = options[6]['value']
    return options, value


@app.callback(
    [Output('intermediate-election', 'children'),
     Output('intermediate-paso', 'children'),
     Output('intermediate-election-2017', 'children'),
     Output('intermediate-volatility', 'children'),
     Output('intermediate-parties', 'children'),
     Output('pie_chart', 'figure'),
     Output('pie_chart_2017', 'figure'),
     Output('dropdown-localidad', 'options'),
     Output('dropdown-localidad-partidos', 'options'),
     Output('dropdown-localidad-features', 'options'),
     Output('dropdown_county_volatility', 'options'),
     Output('dropdown_county_parties', 'options'),
     Output('dropdown-localidad', 'value'),
     Output('dropdown-localidad-partidos', 'value'),
     Output('dropdown-localidad-features', 'value'),
     Output('dropdown_county_volatility', 'value'),
     Output('dropdown_county_parties', 'value'),
     Output('dropdown-scatter1', 'options'),
     Output('dropdown-scatter2', 'options'),
     Output('dropdown-scatter1', 'value'),
     Output('dropdown-scatter2', 'value'),
     Output('dropdown-hbar', 'value'),
     Output('dropdown-hbar', 'options')],
    Input('slider-year', 'value')
)
def update_dataframe(selected_year):
    formatted_localidades = [{'label': i, 'value': i} for i in localidades]
    form_feats = [{'label': i, 'value': i} for i in features]
    formatted_features = [feature for feature in form_feats if feature['label'] != 'school']

    results = pd.DataFrame(general_election[parties].mean(axis=0).reset_index())

    results.columns = ['Partidos Politicos', 'Porcentage Votos']
    results.sort_values(by=['Porcentage Votos'], ascending=False, inplace=True)
    results.reset_index(drop=True, inplace=True)

    fig_pie = px.pie(results, values='Porcentage Votos', names='Partidos Politicos')
    fig_pie.update_layout()

    results_2017 = pd.DataFrame(general_election_2017[parties_2017].mean(axis=0).reset_index())
    results_2017.columns = ['Partidos Politicos', 'Porcentage Votos']
    results_2017.sort_values(by=['Porcentage Votos'], ascending=False, inplace=True)
    results_2017.reset_index(drop=True, inplace=True)

    fig_pie_2017 = px.pie(results_2017, values='Porcentage Votos', names='Partidos Politicos')
    fig_pie_2017.update_layout()

    formatted_political_parties = [{'label': i, 'value': i} for i in parties]

    return general_election.to_json(date_format='iso', orient='split'), \
           paso_election.to_json(date_format='iso', orient='split'), \
           general_election_2017.to_json(date_format='iso', orient='split'), \
           volatility.to_json(date_format='iso', orient='split'), \
           json.dumps(parties), \
           fig_pie, \
           fig_pie_2017, \
           formatted_localidades, \
           formatted_political_parties, \
           formatted_features, \
           formatted_localidades, \
           formatted_political_parties, \
           localidades[0], \
           parties[1], \
           features[1], \
           localidades[0], \
           parties[1], \
           formatted_political_parties, \
           formatted_political_parties, \
           parties[1], \
           parties[3], \
           parties[1], \
           formatted_political_parties


@app.callback([Output('votos-centro-table', 'children'),
               Output('googleMap', 'figure'),
               Output('votos_localidad', 'figure'),
               Output('votos_localidad_2017', 'figure'),
               Output('fig_2017', 'figure'),
               Output('map-slider-value', 'children'),
               Output('total_voters', 'children')],
              [Input('intermediate-election', 'children'),
               Input('intermediate-paso', 'children'),
               Input('intermediate-election-2017', 'children'),
               Input('intermediate-parties', 'children'),
               Input('dropdown-votos-centro', 'value'),
               Input('dropdown-partidos-centro', 'value'),
               Input('map-slider', 'value')])
def update_votos_centro(serialized_data,
                        serialized_paso,
                        serialized_data_2017,
                        serialized_political_parties,
                        dropdown_votos_centro,
                        dropdown_partidos_centro,
                        number_booths):
    election_2019 = pd.read_json(serialized_data, orient='split')
    paso_2019 = pd.read_json(serialized_paso, orient='split')
    election_2017 = pd.read_json(serialized_data_2017, orient='split')
    political_parties = json.loads(serialized_political_parties)
    results = pd.DataFrame(election_2019[political_parties].mean(axis=0).reset_index())

    results.columns = ['Partidos Politicos', 'Porcentage Votos']
    results.sort_values(by=['Porcentage Votos'], ascending=False, inplace=True)
    results.reset_index(drop=True, inplace=True)

    # Sum of votes by localidad
    votes_localidad = election_2019.groupby(['localidad']).sum().reset_index()
    votes_localidad = votes_localidad[['localidad', 'CONSENSO FEDERAL cant', 'FRENTE NOS cant']]
    votes_localidad.columns = ['localidad', 'CONSENSO FEDERAL', 'FRENTE NOS']
    number_booths_localidad = election_2019.groupby(['localidad']).count().reset_index()
    number_booths_localidad = number_booths_localidad[['localidad', 'mesa']]

    votes_localidad_2017 = election_2017.groupby(['localidad']).sum().reset_index()
    votes_localidad_2017 = votes_localidad_2017[['localidad', '1PAIS cant', 'FRENTE JUSTICIALISTA cant',
                                                 'SUMEMOS PILAR cant']]
    votes_localidad_2017.columns = ['localidad', '1PAIS', 'FRENTE JUSTICIALISTA', 'SUMEMOS PILAR']

    if dropdown_votos_centro == '2019':
        center_parties = ['CONSENSO FEDERAL', 'FRENTE NOS']
        if dropdown_partidos_centro == 'CONSENSO FEDERAL + FRENTE NOS':
            sum_cols = pd.DataFrame(election_2019[center_parties[0]] + election_2019[center_parties[1]])
            sum_cols_cant = pd.DataFrame(election_2019[center_parties[0] + ' cant'] +
                                         election_2019[center_parties[1] + ' cant'])
        elif dropdown_partidos_centro == 'CONSENSO FEDERAL':
            sum_cols = pd.DataFrame(election_2019[center_parties[0]])
            sum_cols_cant = pd.DataFrame(election_2019[center_parties[0] + ' cant'])
        elif dropdown_partidos_centro == 'FRENTE NOS':
            sum_cols = pd.DataFrame(election_2019[center_parties[1]])
            sum_cols_cant = pd.DataFrame(election_2019[center_parties[1] + ' cant'])

        data = pd.concat([election_2019[['mesa', 'school', 'localidad']], sum_cols, sum_cols_cant],
                         axis=1, ignore_index=True)
        columns = ['Mesa', 'Escuela', 'Localidad', 'Porcentaje Votos', 'Cantidad Votos']

    elif dropdown_votos_centro == '2019-paso':
        center_parties = ['CONSENSO FEDERAL', 'FRENTE NOS']
        if dropdown_partidos_centro == 'CONSENSO FEDERAL + FRENTE NOS':
            sum_cols_cant = pd.DataFrame(election_2019[center_parties[0] + ' cant'] +
                                         election_2019[center_parties[1] + ' cant'])
            sum_cols_paso = pd.DataFrame(paso_2019[center_parties[0]] + paso_2019[center_parties[1]])
        elif dropdown_partidos_centro == 'CONSENSO FEDERAL':
            sum_cols_cant = pd.DataFrame(election_2019[center_parties[0] + ' cant'])
            sum_cols_paso = pd.DataFrame(paso_2019[center_parties[0]])
        elif dropdown_partidos_centro == 'FRENTE NOS':
            sum_cols_cant = pd.DataFrame(election_2019[center_parties[1] + ' cant'])
            sum_cols_paso = pd.DataFrame(paso_2019[center_parties[1]])

        data = pd.concat([paso_2019[['mesa', 'school', 'localidad']], sum_cols_paso, sum_cols_cant],
                         axis=1, ignore_index=True)
        columns = ['Mesa', 'Escuela', 'Localidad', 'Porcentaje Votos', 'Cantidad Votos']

    elif dropdown_votos_centro == '2017':
        center_parties = ['1PAIS', 'FRENTE JUSTICIALISTA', 'SUMEMOS PILAR']
        if dropdown_partidos_centro == '1PAIS + FRENTE JUSTICIALISTA + SUMEMOS PILAR':
            sum_cols = pd.DataFrame(election_2017[center_parties[0]] +
                                    election_2017[center_parties[1]] +
                                    election_2017[center_parties[2]])
            sum_cols_cant = pd.DataFrame(election_2017[center_parties[0] + ' cant'] +
                                         election_2017[center_parties[1] + ' cant'] +
                                         election_2017[center_parties[2] + ' cant'])
        elif dropdown_partidos_centro == '1PAIS + FRENTE JUSTICIALISTA':
            sum_cols = pd.DataFrame(election_2017[center_parties[0]] +
                                    election_2017[center_parties[1]])
            sum_cols_cant = pd.DataFrame(election_2017[center_parties[0] + ' cant'] +
                                         election_2017[center_parties[1] + ' cant'])
        elif dropdown_partidos_centro == '1PAIS + SUMEMOS PILAR':
            sum_cols = pd.DataFrame(election_2017[center_parties[0]] +
                                    election_2017[center_parties[2]])
            sum_cols_cant = pd.DataFrame(election_2017[center_parties[0] + ' cant'] +
                                         election_2017[center_parties[2] + ' cant'])
        elif dropdown_partidos_centro == 'FRENTE JUSTICIALISTA + SUMEMOS PILAR':
            sum_cols = pd.DataFrame(election_2017[center_parties[1]] +
                                    election_2017[center_parties[2]])
            sum_cols_cant = pd.DataFrame(election_2017[center_parties[1] + ' cant'] +
                                         election_2017[center_parties[2] + ' cant'])
        elif dropdown_partidos_centro == '1PAIS':
            sum_cols = pd.DataFrame(election_2017[center_parties[0]])
            sum_cols_cant = pd.DataFrame(election_2017[center_parties[0] + ' cant'])
        elif dropdown_partidos_centro == 'FRENTE JUSTICIALISTA':
            sum_cols = pd.DataFrame(election_2017[center_parties[1]])
            sum_cols_cant = pd.DataFrame(election_2017[center_parties[1] + ' cant'])
        elif dropdown_partidos_centro == 'SUMEMOS PILAR':
            sum_cols = pd.DataFrame(election_2017[center_parties[2]])
            sum_cols_cant = pd.DataFrame(election_2017[center_parties[2] + ' cant'])

        data = pd.concat([election_2017[['mesa', 'school', 'localidad']], sum_cols, sum_cols_cant],
                         axis=1, ignore_index=True)
        columns = ['Mesa', 'Escuela', 'Localidad', 'Porcentaje Votos', 'Cantidad Votos']

    data.columns = columns
    data['Porcentaje Votos'] = pd.Series([round(val * 100, 2) for val in data['Porcentaje Votos']],
                                         index=data.index)
    data = data.sort_values(['Porcentaje Votos'], ascending=False)

    # format data to plot on map
    data_filt = data.iloc[0:number_booths]
    total_electors = data_filt['Cantidad Votos'].sum()
    # print(total_electors)
    data_map = data_filt['Localidad'].value_counts(normalize=True).reset_index()
    data_map['Localidad'] = data_map['Localidad'] * 100
    data_map.columns = ['localidad', 'Porcentaje Mesas']

    df = geo_localidad.copy(deep=True)

    data_map = data_map.merge(df, how='inner', on='localidad')
    assert round(data_map['Porcentaje Mesas'].sum()) == 100

    table_data = data.to_dict('records')

    table = html.Div([
        dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in columns],
            data=table_data,
            page_size=8,
            sort_action='native',
            style_cell={'width': '250px',
                        'height': '60px',
                        'textAlign': 'center'}
        )
    ])

    map_fig = px.scatter_mapbox(data_map,
                                lat="lat",
                                lon="lon",
                                color="Porcentaje Mesas",
                                size="Porcentaje Mesas",
                                hover_data=['Porcentaje Mesas'],
                                hover_name="Porcentaje Mesas",
                                color_continuous_scale=px.colors.sequential.Turbo,
                                size_max=20,
                                zoom=10)
    votes_fig = px.bar(votes_localidad,
                       x='localidad',
                       y=['CONSENSO FEDERAL', 'FRENTE NOS'])

    votes_fig_2017 = px.bar(votes_localidad_2017,
                            x='localidad',
                            y=['1PAIS', 'FRENTE JUSTICIALISTA', 'SUMEMOS PILAR'])


    map_fig.update_layout(mapbox_style="open-street-map")

    cols_cant = [party + ' cant' for party in parties_2017]
    results = general_election_2017[cols_cant].sum().reset_index()
    results.columns = ['partidos', 'resultados']
    fig_2017 = px.bar(results, x='partidos', y='resultados')

    return table, map_fig, votes_fig, votes_fig_2017, fig_2017, number_booths, total_electors


@app.callback(Output('fig_volatility', 'figure'),
              [Input('intermediate-election', 'children'),
               Input('intermediate-parties', 'children'),
               Input('intermediate-volatility', 'children'),
               Input('dropdown_county_volatility', 'value'),
               Input('dropdown_county_parties', 'value')])
def update_volatility_chart(serialized_data,
                            serialized_political_parties,
                            serialized_volatility,
                            dropdown_county_volatility,
                            dropdown_volatility_political_party):
    # general_election = pd.read_json(serialized_data, orient='split')
    political_parties = json.loads(serialized_political_parties)
    election_volatility = pd.read_json(serialized_volatility, orient='split')
    volatility_filtered_by_county = election_volatility.loc[general_election['localidad'] == dropdown_county_volatility]
    fig_volatility = px.scatter(volatility_filtered_by_county,
                                x=dropdown_volatility_political_party,
                                y=political_parties[3],
                                hover_data=['mesa'],
                                color_discrete_sequence=['rgba(230, 0, 0, 0.9)'])
    fig_volatility.update_traces(marker=dict(size=10))

    return fig_volatility


@app.callback(
    Output('second-table', 'children'),
    Input('fig_volatility', 'hoverData'))
def display_second_table(hover_data):
    if hover_data is not None:
        mesa = hover_data['points'][0]['customdata'][0]
        cols_table = ['pmale', 'pfemale', '18-25', '25-35', '35-45', '45-55', '55-65', '65-75', '>75']
        data = general_election.loc[general_election.mesa == mesa, cols_table]
        for col in cols_table:
            data[col] = pd.Series(["{0:.2f}%".format(val) for val in data[col]], index=data.index)
        data = data.to_dict('records')
        table = html.Div([
            dcc.Markdown('''***Caracteristicas demograficas de la mesa***'''),
            dash_table.DataTable(
                id='table',
                columns=[{"name": i, "id": i} for i in cols_table],
                data=data,
                style_cell={'width': '300px',
                            'height': '60px',
                            'textAlign': 'center'}
            )
        ])
        return table


@app.callback(
    Output('first-table', 'children'),
    Input('fig_volatility', 'hoverData'))
def display_first_table(hover_data):
    if hover_data is not None:
        cols_table = ['Elección',
                      'mesa',
                      'FRENTE DE TODOS',
                      'JUNTOS POR EL CAMBIO',
                      'CONSENSO FEDERAL',
                      'FRENTE DE IZQUIERDA Y DE TRABAJADORES - UNIDAD',
                      'FRENTE NOS',
                      ]

        mesa = hover_data['points'][0]['customdata'][0]

        aux1 = general_election.loc[general_election.mesa == mesa].copy()
        aux1.loc[:, 'Elección'] = 'General'
        aux1 = aux1[cols_table]

        aux2 = paso_election.loc[paso_election.mesa == mesa].copy()
        aux2.loc[:, 'Elección'] = 'Paso'
        aux2 = aux2[cols_table]

        data = pd.concat([aux1, aux2])
        for col in cols_table[2:]:
            data[col] = pd.Series(["{0:.2f}%".format(val * 100) for val in data[col]], index=data.index)

        data = data.to_dict('records')
        table = html.Div([
            dcc.Markdown('''***Resultados de la elección***'''),
            dash_table.DataTable(
                id='table',
                columns=[{"name": i, "id": i} for i in cols_table],
                data=data,
                style_cell={'width': '300px',
                            'height': '60px',
                            'textAlign': 'center'}
            )
        ])

        return table


@app.callback(
    [Output('scatter', 'figure'),
     Output('hbar', 'figure'),
     Output('scatter-localidad', 'figure'),
     Output('third-table', 'children')],
    [Input('intermediate-election', 'children'),
     Input('intermediate-parties', 'children'),
     Input('dropdown-localidad', 'value'),
     Input('dropdown-localidad-partidos', 'value'),
     Input('dropdown-localidad-features', 'value'),
     Input('dropdown-scatter1', 'value'),
     Input('dropdown-scatter2', 'value'),
     Input('dropdown-hbar', 'value')]
)
def update_charts(serialized_data,
                  serialized_political_parties,
                  dropdown_localidad,
                  dropdown_localidad_partido,
                  dropdown_localidad_feature,
                  dropdown1,
                  dropdown2,
                  dropdown):
    election_2019 = pd.read_json(serialized_data, orient='split')
    political_parties = json.loads(serialized_political_parties)
    results = pd.DataFrame(election_2019[political_parties].mean(axis=0).reset_index())
    results.columns = ['Partidos Politicos', 'Porcentage Votos']
    results.sort_values(by=['Porcentage Votos'], ascending=False, inplace=True)
    results.reset_index(drop=True, inplace=True)

    pearson_r = election_2019[dropdown1].corr(election_2019[dropdown2])
    pearson_r = '{:,.2f}'.format(pearson_r)
    # try:
    fig_scatter = px.scatter(election_2019,
                             x=dropdown1,
                             y=dropdown2,
                             hover_data=['mesa'],
                             color=dropdown2,
                             title=f"Pearson's R: {pearson_r}")
    fig_scatter.update_layout(plot_bgcolor=colors['background'],
                              paper_bgcolor=colors['background'],
                              font_color=colors['text']
                              )

    # Voting Booths, horizontal bar plot
    sorted_by_winner = election_2019.sort_values(by=[dropdown])
    fig_bar = px.bar(sorted_by_winner,
                     x=political_parties,
                     y=np.arange(0, len(election_2019)),
                     orientation='h',
                     barmode="stack",
                     opacity=1,
                     hover_data=["mesa"],
                     labels={'value': "Porcentage Votos", 'y': '', 'variable': 'Partidos Politicos'},
                     color_discrete_sequence=["red", "blue", "yellow", "green", "magenta", "goldenrod"],
                     height=750,
                     width=1500)
    fig_bar.update_layout(plot_bgcolor=colors['background'],
                          paper_bgcolor=colors['background'],
                          font_color=colors['text']
                          )

    filtered_by_county = election_2019.loc[election_2019['localidad'] == dropdown_localidad]
    pearson_r = filtered_by_county[dropdown_localidad_feature] \
        .corr(filtered_by_county[dropdown_localidad_partido])
    pearson_r = '{:,.2f}'.format(pearson_r)
    fig_scatter_localidad = px.scatter(filtered_by_county,
                                       x=dropdown_localidad_feature,
                                       y=dropdown_localidad_partido,
                                       hover_data=['mesa'],
                                       color=dropdown2,
                                       title=f"Pearson's R: {pearson_r}")
    fig_scatter_localidad.update_layout(plot_bgcolor=colors['background'],
                                        paper_bgcolor=colors['background'],
                                        font_color=colors['text']
                                        )
    cols_features = ['pmale', 'pfemale', '18-25', '25-35', '35-45', '45-55', '55-65', '65-75', '>75']
    pearsons = {feature: '{:,.2f}'.format(filtered_by_county[feature]
                                          .corr(filtered_by_county[dropdown_localidad_partido]))
                for feature in cols_features}

    table = html.Div([
        dcc.Markdown('''***Características demograficas y resultados electorales***'''),
        dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in cols_features],
            data=[pearsons],
            style_cell={'width': '300px',
                        'height': '60px',
                        'textAlign': 'center'}
        )
    ])

    return fig_scatter, fig_bar, fig_scatter_localidad, table


if __name__ == "__main__":
    app.run_server(debug=True)

# ToDo
#  Mostrar numero total de votantes en el mapa (hover).
#  Add absolute number of votos centro per localidad (more precise to search people)
#  Add data from elections_2017 -> Add absolute number of votos centro
#  Add cumulative subplot to show the majority of voting booths in each location.


# import plotly.graph_objects as go
#
# googleMap = go.Figure(px.choropleth_mapbox(
#     px.choropleth_mapbox(dat,
#                          geojson=geojson,
#                          locations="Municipios",
#                          featureidkey="properties.nombre",
#                          center={"lat": LOC_PILAR[0], "lon": LOC_PILAR[1]},
#                          mapbox_style='carto-positron',
#                          zoom=11,
#                          opacity=0.2)))  # color="Votes",)  # here you set all attributes needed for a Choroplethmapbox
# googleMap.add_scattermapbox(lat=[-34.45866],
#                             lon=[-58.9142],
#                             mode='markers+text',
#                             text='Test',  #a list of strings, one  for each geographical position  (lon, lat)
#                             below='',
#                             marker_size=12,
#                             marker_color='rgb(235, 0, 100)')

# googleMap.update_layout((title_text ='Your plot title', title_x =0.5,
#                         mapbox = dict(center= dict(lat=52.370216, lon=4.895168),  #change to the center of your map
#                                           accesstoken= "your-mapbox-access-token",
#                                           zoom=6, #change this value correspondingly, for your map
#                                           style="light"  # set your prefered mapbox style
#                                           ))


# Map
# LOC_PILAR = [-34.45866, -58.9142]  # LOC_BsAs = [-35.828117, -59.811962]
# counties = {features['properties']['nombre']: random.randint(0, 300) for features in geojson['features']}
# dat = pd.DataFrame(list(counties.items()), columns=['Municipios', 'Votes'])
# dat = dat.loc[dat.Municipios.str.upper() == council]

# googleMap = px.choropleth_mapbox(dat,
#                                  geojson=geojson,
#                                  locations="Municipios",
#                                  featureidkey="properties.nombre",
#                                  center={"lat": LOC_PILAR[0], "lon": LOC_PILAR[1]},
#                                  mapbox_style="carto-positron",
#                                  zoom=11,
#                                  opacity=0.2)  # color="Votes",
