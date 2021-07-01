import json
import pandas as pd
from time import perf_counter


class DataSource:
    def __init__(self):
        self.invalid_codes = ['9001', '9002', '9003', '9004', '9005', '9005', '9006', '9010', '9020']
        self.political_parties, self.political_party_paso = self.load_political_parties()
        self.elections, self.paso = self.load_election_results()
        self.councils = self.load_councils()
        self.electoral_roll = self.load_electoral_roll()

    @staticmethod
    def load_political_parties():
        political_party = pd.read_csv('./dataset/codigo_votos_09_19.csv', low_memory=False)
        columns = ['anio', 'codigo_voto', 'nombre_partido']
        political_party.columns = columns

        political_party_paso = pd.read_csv('./dataset/paso_2019/codigo_votos.csv',
                                           sep=';',
                                           low_memory=False)
        columns = ['id_eleccion', 'eleccion', 'codigo_voto', 'nombre_partido', 'id_lista', 'lista']
        political_party_paso.columns = columns
        political_party_paso.insert(0, 'anio', 2019)
        political_party_paso = political_party_paso.drop(['id_eleccion', 'eleccion', 'id_lista', 'lista'], axis=1) \
            .sort_values(by=['codigo_voto']).drop_duplicates(subset=['codigo_voto'])

        return political_party, political_party_paso

    @staticmethod
    def load_election_results():
        elections = pd.read_csv('./dataset/resultados_electorales_09_19.csv', low_memory=False)
        elections.columns = ['year', 'cargo', 'provincia', 'id_municipio', 'circuito', 'mesa', 'codigo_voto',
                             'cant_votos']

        paso = pd.read_csv('./dataset/paso_2019/resultados_electorales.csv', sep=';', low_memory=False)
        paso.columns = ['id_provincia', 'id_municipio', 'circuito', 'mesa', 'id_eleccion', 'codigo_voto',
                        'id_lista', 'cant_votos']
        paso.insert(0, 'year', 2019)
        paso.insert(1, 'cargo', 'municipales')

        return elections, paso

    @staticmethod
    def load_councils(dataset='./dataset/municipios_aglo.csv'):
        councils = pd.read_csv(dataset, low_memory=False, encoding='ISO-8859-1')
        councils.columns = ['id_municipio', 'provincia', 'id_aglomerado', 'municipio']
        return councils

    @staticmethod
    def load_electoral_roll(dataset='./dataset/demographics_mesa_2019.csv'):
        electoral_roll = pd.read_csv(dataset)
        electoral_roll.columns = electoral_roll.columns.str.lower()
        return electoral_roll

    def select_council(self, year=2019, election_type='municipales', council='PILAR'):
        id_council = self.get_council_id(council)
        df = self.elections.loc[(self.elections['cargo'] == election_type) &
                                (self.elections['id_municipio'] == id_council) &
                                (self.elections['year'] == year) &
                                (~self.elections['codigo_voto'].isin(self.invalid_codes))]
        df = df.drop(['provincia', 'id_municipio', 'circuito'], axis=1)
        df.insert(4, 'nombre_partido', '')
        df.insert(5, 'prop_votos', '')

        parties = self.get_council_parties(2019, vote_ids=df.codigo_voto.unique())

        for code in df.codigo_voto.unique():
            party = self.political_parties.loc[(self.political_parties['codigo_voto'] == code) &
                                               (self.political_parties['anio'] == year)]['nombre_partido'].values
            df.loc[df.codigo_voto == code, 'nombre_partido'] = party[0]

        for mesa in df.mesa.unique():
            total_mesa = df.loc[df.mesa == mesa, 'cant_votos'].sum()
            df.loc[df.mesa == mesa, 'prop_votos'] = df.loc[df.mesa == mesa, 'cant_votos'] / total_mesa

        df['mesa'] = pd.to_numeric(df['mesa'], downcast='integer')
        df = df.sort_values(by=['mesa', 'nombre_partido'])

        # Format Paso
        ps = self.paso.loc[(self.paso['id_municipio'] == id_council) &
                           ~(self.paso['codigo_voto'].isin(self.invalid_codes))]
        ps = ps.drop(['id_provincia', 'id_municipio', 'circuito', 'id_eleccion', 'id_lista'], axis=1)

        # TODO: check why there is one missing voting booth
        # Voting Booth 671 is missing in the Paso election. I will discard it here, we need to further check this
        common_voting_booths = list(set(df.mesa.unique()).intersection(ps.mesa.unique()))
        ps = ps.loc[ps['mesa'].isin(common_voting_booths)]
        df = df.loc[df['mesa'].isin(common_voting_booths)]

        for code in ps.codigo_voto.unique():
            party = self.political_party_paso.loc[self.political_party_paso['codigo_voto'] == code]['nombre_partido'] \
                .values
            ps.loc[ps.codigo_voto == code, 'nombre_partido'] = party[0]

        # Calculate proportion of votes for each party
        # Return only those political parties that reached the general election
        paso = pd.DataFrame()
        for mesa in ps.mesa.unique():
            total_mesa = ps.loc[ps.mesa == mesa, 'cant_votos'].sum()
            ps.loc[ps.mesa == mesa, 'prop_votos'] = ps.loc[ps.mesa == mesa, 'cant_votos'] / total_mesa

            # sum proportions and cant_votos for each unique party
            aggregation_functions = {'year': 'first', 'cargo': 'first', 'mesa': 'first', 'codigo_voto': 'first',
                                     'nombre_partido': 'first', 'prop_votos': 'sum', 'cant_votos': 'sum'}
            df_new = ps.loc[ps.mesa == mesa]
            df_new = df_new.groupby(ps['nombre_partido'], as_index=False).aggregate(aggregation_functions)

            # filter parties that did not qualify to the general election
            paso = paso.append(df_new.loc[df_new.nombre_partido.isin(parties)])

        paso = paso.sort_values(by=['mesa', 'nombre_partido'])

        # Compute volatility from Paso to General election
        paso = paso.reset_index(drop=True)
        df = df.reset_index(drop=True)

        general_election = df.pivot(index='mesa', columns='nombre_partido', values='prop_votos')
        paso_election = paso.pivot(index='mesa', columns='nombre_partido', values='prop_votos')

        general_election_cant_votos = df.pivot(index='mesa', columns='nombre_partido', values='cant_votos')
        paso_election_cant_votos = paso.pivot(index='mesa', columns='nombre_partido', values='cant_votos')

        # modify column names to avoid conflicts
        new_cols = [col + ' cant' for col in general_election_cant_votos.columns]
        general_election_cant_votos.columns = new_cols

        new_cols = [col + ' cant' for col in paso_election_cant_votos.columns]
        paso_election_cant_votos.columns = new_cols

        volatility = general_election - paso_election
        volatility.insert(0, 'mesa', df['mesa'].unique())
        general_election.insert(0, 'mesa', df['mesa'].unique())
        general_election_cant_votos.insert(0, 'mesa', df['mesa'].unique())
        paso_election.insert(0, 'mesa', paso['mesa'].unique())
        paso_election_cant_votos.insert(0, 'mesa', paso['mesa'].unique())

        general_election.index.name = None
        general_election_cant_votos.index.name = None
        paso_election.index.name = None
        paso_election_cant_votos.index.name = None
        volatility.index.name = None

        general_election = pd.merge(general_election, general_election_cant_votos, on='mesa')
        general_election = pd.merge(general_election, self.electoral_roll, on='mesa')

        paso_election = pd.merge(paso_election, paso_election_cant_votos, on='mesa')
        paso_election = pd.merge(paso_election, self.electoral_roll, on='mesa')
        volatility = pd.merge(volatility, self.electoral_roll, on='mesa')

        return general_election, paso_election, volatility, parties

        # time4 = perf_counter()
        # print(f"Select Council {selected_year}, Took {time2 - time1} seconds")
        # print(f"Transpose table took {time3-time2}")
        # print(f"Serialization Took {time4 - time3}")

    def get_council_parties(self, year, vote_ids):
        parties_names = [self.get_party_name(year, vote_id) for vote_id in vote_ids]
        return parties_names

    def get_party_name(self, year, vote_id):
        result = self.political_parties[(self.political_parties['codigo_voto'] == vote_id) &
                                        (self.political_parties['anio'] == year)]['nombre_partido'].values
        if not result:
            print("Partido not found")
            return 'None'
        else:
            return result[0]

    def get_council_id(self, council):
        result = self.councils[self.councils['municipio'] == council]['id_municipio'].values
        if not result:
            print("Municipio not found")
            return None
        else:
            return result[0]

    @staticmethod
    def get_geo_polygons(data_loc='./geographical_data/buenos_aires.geojson'):
        with open(data_loc) as f:
            geojson = json.load(f)
        return geojson
