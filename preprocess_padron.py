from data_source import DataSource
import pandas as pd
import pickle


def process_booth_demographics():

    padron = pd.read_excel('./dataset/Padron_Pilar_2019.xlsx', engine='openpyxl')
    padron = padron.loc[3:, :]
    padron.columns = ['DNI', 'Clase', 'Apellidos', 'Nombres', 'Dirección', 'Tipo DNI', 'Circuito', 'Mesa',
                      'Sexo', 'ESCUELA', 'LOCALIDAD']
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
    new_cols = ['Localidad', 'Mesa', 'pMale', 'pFemale',
                '18-25', '25-35', '35-45', '45-55', '55-65', '65-75', '>75',
                '18-25_m', '25-35_m', '35-45_m', '45-55_m', '55-65_m', '65-75_m', '>75_m',
                '18-25_f', '25-35_f', '35-45_f', '45-55_f', '55-65_f', '65-75_f', '>75_f'
                ]

    localidades = pad.LOCALIDAD.unique()
    dataset = pd.DataFrame(columns=new_cols)
    i = 0
    for localidad in localidades:
        loc = pad.loc[pad['LOCALIDAD'] == localidad]
        loc.reset_index(inplace=True)

        # Compute Gender and age for each voting booth
        mesas = loc.groupby('Mesa')
        # symbols['Mesa'].get_group(692)

        for mesa, group in mesas:
            gen = group['Sexo'].value_counts(normalize=True) * 100
            age = group['edad_bin'].value_counts(normalize=True) * 100

            female = group.loc[group['Sexo'] == 'F']
            male = group.loc[group['Sexo'] == 'M']
            age_f = female['edad_bin'].value_counts(normalize=True) * 100
            age_m = male['edad_bin'].value_counts(normalize=True) * 100

            dataset.loc[i] = [
                localidad, mesa, gen.M, gen.F,
                age['18-25'], age['25-35'], age['35-45'], age['45-55'], age['55-65'], age['65-75'], age['75'],
                age_f['18-25'], age_f['25-35'], age_f['35-45'], age_f['45-55'], age_f['55-65'], age_f['65-75'], age_f['75'],
                age_m['18-25'], age_m['25-35'], age_m['35-45'], age_m['45-55'], age_m['55-65'], age_m['65-75'], age_m['75']
            ]
            i += 1

    dataset.to_csv('./dataset/demographics_mesa_2019.csv', index=False)


# # Election 2017
# # Select initial Municipio and voting booths, Filter valid votes
# ds = DataSource()
council = 'PILAR'
# data, data_paso, volatility, parties = ds.select_council(year=2017,
#                                                          election_type='municipales',
#                                                          council=council)
# localidades = ds.electoral_roll.localidad.unique()
# features = ds.electoral_roll.columns[2:]

# process_booth_demographics()

# Select initial Municipio and voting booths, Filter valid votes
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


