import pandas as pd

df1 = pd.read_excel('data/Rides/ESTACIONES DBIZI COORDENADAS.xlsx')
# print(df1.head(10))

df2 = pd.read_csv('data/Rides/estaciones.csv')
# print(df2.head(10))

df3 = pd.read_csv('data/Rides/stations_ed.csv')
# print(df3.head(10))

df4 = pd.read_csv('data/Rides/Stations_new.csv')
print(df3.head(80))