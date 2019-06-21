import os
import geopandas as gpd



FIPScodes = ['01','02', '04', '05', '06', '08', '09','10', '11', '12', '13', '15', '16','17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30' ,'31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '44', '45', '46', '47', '48', '49', '50', '51', '53', '54', '55', '56']
try:
        os.makedirs('maps')
except:
        print('Maps folder already exists')
for code in FIPScodes:
    stateMap = gpd.read_file('simpleGeojson\\' + code + '.geojson')
    print('Working on: ' + code)
    for row in stateMap['county'].unique():
        stateMap[stateMap['county'] == row].to_file('maps\\' + code + row + '.geojson',driver='GeoJSON') 
