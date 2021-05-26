import plotly.express as px
import pandas as pd
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from data_source import DataSource
import json
import random
import dash_bootstrap_components as dbc


ds = DataSource()
council = 'PILAR'
data, data_paso, volatility, parties = ds.select_council(year=2019,
                                                         election_type='municipales',
                                                         council=council)
localidades = ds.electoral_roll.localidad.unique()
features = ds.electoral_roll.columns[2:]

colors = {
    'background': '#222',
    'text': '#fff'
}

# Dashboard
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE])
app.title = 'Dashboard Nous'

# Map
LOC_PILAR = [-34.45866, -58.9142]  # LOC_BsAs = [-35.828117, -59.811962]
geojson = ds.get_geo_polygons()
counties = {features['properties']['nombre']: random.randint(0, 300) for features in geojson['features']}
dat = pd.DataFrame(list(counties.items()), columns=['Municipios', 'Votes'])
dat = dat.loc[dat.Municipios.str.upper() == council]
fig_map = px.choropleth_mapbox(dat,
                               geojson=geojson,
                               locations="Municipios",
                               featureidkey="properties.nombre",
                               center={"lat": LOC_PILAR[0], "lon": LOC_PILAR[1]},
                               mapbox_style="carto-positron",
                               zoom=11,
                               opacity=0.2)  # color="Votes",

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

        dbc.Row(
            [
                dbc.Col(dcc.Graph(id='pie_chart'), width=6),
                dbc.Col(dcc.Graph(figure=fig_map), width=6),
            ]
        ),

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
                      "Resultados de las elecciones paso versus resultados de la elección general. "
                      ]
        ),
        html.P(
            children=["En esta sección analizamos las diferencias en los votos, mesa por mesa entre las elecciones paso y "
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
                                     value=features[0]
                                     ), width=4)
            ]
        ),
        dcc.Graph(id='scatter-localidad', className='card'),

        # Hidden div inside the app that stores the intermediate value
        html.Div(id='intermediate-data', style={'display': 'none'}),
        html.Div(id='intermediate-volatility', style={'display': 'none'}),
        html.Div(id='intermediate-parties', style={'display': 'none'}),

    ], fluid=True
)


@app.callback(
    [Output('intermediate-data', 'children'),
     Output('intermediate-volatility', 'children'),
     Output('intermediate-parties', 'children'),
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
    general_election, _, volatility, political_parties = ds.select_council(year=selected_year,
                                                                           election_type='municipales',
                                                                           council=council)
    formatted_localidades = [{'label': i, 'value': i} for i in ds.electoral_roll.localidad.unique()]
    formatted_features = [{'label': i, 'value': i} for i in ds.electoral_roll.columns[2:]]
    formatted_political_parties = [{'label': i, 'value': i} for i in political_parties]

    return general_election.to_json(date_format='iso', orient='split'), \
           volatility.to_json(date_format='iso', orient='split'), \
           json.dumps(political_parties), \
           formatted_localidades, \
           formatted_political_parties, \
           formatted_features, \
           formatted_localidades, \
           formatted_political_parties, \
           localidades[0], \
           political_parties[1], \
           features[0], \
           localidades[0], \
           political_parties[1], \
           formatted_political_parties, \
           formatted_political_parties, \
           political_parties[1], \
           political_parties[3], \
           political_parties[1], \
           formatted_political_parties


@app.callback(Output('fig_volatility', 'figure'),
              [Input('intermediate-data', 'children'),
               Input('intermediate-parties', 'children'),
               Input('intermediate-volatility', 'children'),
               Input('dropdown_county_volatility', 'value'),
               Input('dropdown_county_parties', 'value')])
def update_volatility_chart(serialized_data,
                            serialized_political_parties,
                            serialized_volatility,
                            dropdown_county_volatility,
                            dropdown_volatility_political_party):
    general_election = pd.read_json(serialized_data, orient='split')
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
    [Output('pie_chart', 'figure'),
     Output('scatter', 'figure'),
     Output('hbar', 'figure'),
     Output('scatter-localidad', 'figure')],  #
    [Input('intermediate-data', 'children'),
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
    general_election = pd.read_json(serialized_data, orient='split')
    political_parties = json.loads(serialized_political_parties)
    results = pd.DataFrame(general_election[political_parties].mean(axis=0).reset_index())
    results.columns = ['Partidos Politicos', 'Porcentage Votos']
    results.sort_values(by=['Porcentage Votos'], ascending=False, inplace=True)
    results.reset_index(drop=True, inplace=True)

    fig_pie = px.pie(results, values='Porcentage Votos', names='Partidos Politicos')
    fig_pie.update_layout()

    pearson_r = general_election[dropdown1].corr(general_election[dropdown2])
    fig_scatter = px.scatter(general_election,
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
    sorted_by_winner = general_election.sort_values(by=[dropdown])
    fig_bar = px.bar(sorted_by_winner,
                     x=political_parties,
                     y=np.arange(0, len(general_election)),
                     orientation='h',
                     barmode="stack",
                     opacity=1,
                     hover_data=["mesa"],
                     labels={'value': "Porcentage Votos", 'y': '', 'variable': 'Partidos Politicos'},
                     color_discrete_sequence=["red", "blue", "yellow", "green", "magenta", "goldenrod"],
                     height=450)
    fig_bar.update_layout(plot_bgcolor=colors['background'],
                          paper_bgcolor=colors['background'],
                          font_color=colors['text']
                          )

    filtered_by_county = general_election.loc[general_election['localidad'] == dropdown_localidad]
    pearson_r = filtered_by_county[dropdown_localidad_feature] \
        .corr(filtered_by_county[dropdown_localidad_partido])
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

    return fig_pie, fig_scatter, fig_bar, fig_scatter_localidad


if __name__ == "__main__":
    app.run_server(debug=True)