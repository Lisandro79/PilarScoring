from data_source import DataSource
import pandas as pd
import pickle
import json
import numpy as np


def process_booth_demographics_2017():

    padron = pd.read_csv('./dataset/Padron_Pilar_2017.csv', low_memory=False)
    padron.columns = ['DNI', 'Clase', 'Apellidos', 'Nombres', 'Domicilio', 'Tipo DNI', 'Distrito',
                  'Circuito', 'Mesa', 'Escuela', 'Direccion']
    pad = padron.copy(deep=True)
    pad['Localidad'] = ''
    circuits_councils = {'768': 'Pilar',
                         '769': 'Manzanares',
                         '770': 'Derqui',
                         '770A': 'La Lonja',
                         '771': 'Del Viso',
                         '772': 'Villa Rosa'
                         }

    # Assign Localidad
    circuits = pad.Circuito.unique()
    for circuit in circuits:
        idxs = pad.Circuito == circuit
        pad.loc[idxs, 'Localidad'] = circuits_councils[circuit]

    # Compute age from the year of birth
    # replace the '0' with the closest class
    pad.loc[pad.Clase.isnull(), 'Clase'] = 0
    zero_clase = pad.index[pad['Clase'] == 0].tolist()
    nonzeros = pad[pad.Clase != 0].index

    indexes = []
    for anchor in zero_clase:
        dists = anchor - nonzeros
        nhops = min(dists, key=abs)
        pad.loc[anchor, 'Clase'] = pad.Clase.iloc[anchor - nhops]
    #     indexes.append(anchor - nhops)
    # pad.loc[zero_clase, 'Clase'] = pad.Clase.iloc[indexes]

    election_year = 2017
    pad['edad'] = election_year - pad.Clase
    pad['edad_bin'] = pd.cut(pad['edad'], [16, 25, 35, 45, 55, 65, 75, 100],
                             labels=['18-25', '25-35', '35-45', '45-55', '55-65', '65-75', '75'])
    pad.dropna(axis=0, inplace=True)

    new_cols = ['Localidad', 'Mesa', 'school',
                '18-25', '25-35', '35-45', '45-55', '55-65', '65-75', '>75',
                ]

    localidades = pad.Localidad.unique()
    dataset = pd.DataFrame(columns=new_cols)
    i = 0
    for localidad in localidades:
        local = pad.loc[pad['Localidad'] == localidad]
        local.reset_index(inplace=True)

        # Compute Gender and age for each voting booth
        mesas = local.groupby('Mesa')

        for mesa, group in mesas:
            school = local.loc[local.Mesa == mesa]['Escuela'].unique()
            school = school[0]
            age = group['edad_bin'].value_counts(normalize=True) * 100

            dataset.loc[i] = [localidad, mesa, school, age['18-25'], age['25-35'], age['35-45'], age['45-55'],
                              age['55-65'], age['65-75'], age['75']
                              ]
            i += 1

    dataset.to_csv('./dataset/demographics_mesa_2017.csv', index=False)


def process_booth_demographics_2019():

    padron = pd.read_csv('./dataset/Padron_Pilar_2019.csv')
    padron.columns = ['DNI', 'Clase', 'Apellidos', 'Nombres', 'Dirección', 'Tipo DNI', 'Circuito', 'Mesa',
                      'Sexo', 'Escuela', 'Localidad']
    pad = padron.copy(deep=True)

    # Compute age from the year of birth
    # replace the '0' with the closest class
    zero_clase = pad.index[pad['Clase'] == 0].tolist()
    nonzeros = pad[pad.Clase != 0].index

    for anchor in zero_clase:
        dists = anchor - nonzeros
        nhops = min(dists, key=abs)
        pad.Clase.iloc[anchor] = pad.Clase.iloc[anchor - nhops]

    election_year = 2019
    pad['edad'] = election_year - pad.Clase
    pad['edad_bin'] = pd.cut(pad['edad'], [16, 25, 35, 45, 55, 65, 75, 100],
                             labels=['18-25', '25-35', '35-45', '45-55', '55-65', '65-75', '75'])

    # 'pVotos', 'Localidad', 'Mesa', 'pMale', 'pFemale', '18-25', '25-35', '35-45', '45-55', '55-65', '65-75', '>75'
    new_cols = ['Localidad', 'Mesa', 'school', 'pMale', 'pFemale',
                '18-25', '25-35', '35-45', '45-55', '55-65', '65-75', '>75',
                '18-25_m', '25-35_m', '35-45_m', '45-55_m', '55-65_m', '65-75_m', '>75_m',
                '18-25_f', '25-35_f', '35-45_f', '45-55_f', '55-65_f', '65-75_f', '>75_f'
                ]

    localidades = pad.Localidad.unique()
    dataset = pd.DataFrame(columns=new_cols)
    i = 0
    for localidad in localidades:
        loc = pad.loc[pad['Localidad'] == localidad]
        loc.reset_index(inplace=True)

        # Compute Gender and age for each voting booth
        mesas = loc.groupby('Mesa')
        # symbols['Mesa'].get_group(692)

        for mesa, group in mesas:
            school = loc.loc[loc.Mesa == mesa]['Escuela'].unique()
            school = school[0]
            gen = group['Sexo'].value_counts(normalize=True) * 100
            age = group['edad_bin'].value_counts(normalize=True) * 100

            female = group.loc[group['Sexo'] == 'F']
            male = group.loc[group['Sexo'] == 'M']
            age_f = female['edad_bin'].value_counts(normalize=True) * 100
            age_m = male['edad_bin'].value_counts(normalize=True) * 100

            dataset.loc[i] = [
                localidad, mesa, school, gen.M, gen.F,
                age['18-25'], age['25-35'], age['35-45'], age['45-55'], age['55-65'], age['65-75'], age['75'],
                age_f['18-25'], age_f['25-35'], age_f['35-45'], age_f['45-55'], age_f['55-65'], age_f['65-75'], age_f['75'],
                age_m['18-25'], age_m['25-35'], age_m['35-45'], age_m['45-55'], age_m['55-65'], age_m['65-75'], age_m['75']
            ]
            i += 1

    dataset.to_csv('./dataset/demographics_mesa_2019.csv', index=False)


process_booth_demographics_2017()

# 2017
council = 'PILAR'
ds = DataSource()
data, _, _, parties = ds.select_council(year=2017, election_type='municipales', council=council)
data.to_csv('./data/generales_2017.csv')
with open('./data/parties_2017.pkl', "wb") as open_file:
    pickle.dump(parties, open_file)

# Select initial Municipio and voting booths, Filter valid votes
council = 'PILAR'
ds = DataSource()
data, data_paso, volatility, parties = ds.select_council(year=2019,
                                                         election_type='municipales',
                                                         council=council)
localidades = ds.electoral_roll.localidad.unique()
features = ds.electoral_roll.columns[2:]

# Save to disk
data.to_csv('./data/generales.csv')
data_paso.to_csv('./data/paso.csv')
volatility.to_csv('./data/volatility.csv')

with open('./data/parties.pkl', "wb") as open_file:
    pickle.dump(parties, open_file)

with open('./data/counties.pkl', "wb") as open_file:
    pickle.dump(localidades, open_file)

with open('./data/features.pkl', "wb") as open_file:
    pickle.dump(features, open_file)




