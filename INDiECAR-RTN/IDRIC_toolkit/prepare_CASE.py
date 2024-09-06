"""
Prepares a case study for the solver
"""

import os
import json
import pandas as pd
import geopandas as gpd
import tkinter as tk
import numpy as np
from tkinter import filedialog
from scipy.spatial import distance


def select_pathCase():
    """"""
    root = tk.Tk()
    #root.withdraw()
    msg="Select the folder where for the new case study"

    return filedialog.askdirectory(title=msg)


def make_NewCase(CaseName):
    """"""
    pathCASE = select_pathCase()
    path = f"{pathCASE}/{CaseName}/input/"
    if not os.path.exists(path):
        os.makedirs(path)
    return f"{pathCASE}/{CaseName}/"


def create_GriddedDistanceCSV(pathCASE, CaseName):
    """creates"""
    # load Data into GeoDataframe
    df = pd.read_csv(f"{pathCASE}input/grid_cells.csv")
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude))
    gdf.set_geometry("geometry", crs=4326, inplace=True)
    gdf.to_crs(crs=23028, inplace=True)
    # write out 2D coordinates
    coords = [(g.x, g.y) for g in gdf.geometry]
    # compute distance pairs
    dist = pd.DataFrame(distance.cdist(coords, coords))
    # scale metre to km
    dist /= 1000
    dist.rename(columns={i: i+1 for i in dist.columns}, inplace=True)
    dist.index += 1
    dist.to_csv(f"{pathCASE}input/Gridded_Linear_Distances.csv")


def write_RunInfo(pathCASE, RunName, d):
    """"""
    with open(f"{pathCASE}{RunName}.json", "w", encoding='utf-8') as outfile:
        json.dump(d, outfile, ensure_ascii=False, indent=4)

def load_ComponentModels(filePath):
    return pd.read_excel(f"{filePath}COMPONENT_MODELS.xlsx")

def write_csvData(pathCASE, data, param, additonalKeys=[], separator='\n'):
    cols = [c for c in data.columns if param in c]
    res = []
    for col in cols:
        key = ['J', *additonalKeys, col]
        dfwrk = data[key].copy()
        dfwrk.rename(columns={col: col.split(separator)[0]}, inplace=True)
        if len(col.split(separator)) > 1:
            if param == 'INV_COEFF' or param == 'PROCESS_COEFF':
                dfwrk.insert(1, "M", col.split(separator)[-1])
            elif param == 'RESOURCE_CONV_RATE':
                dfwrk.insert(1, "R", col.split(separator)[-1])
            else:
                dfwrk.insert(1, "MODE", col.split(separator)[-1])
        dfwrk.dropna(axis=0, inplace=True)
        res.append(dfwrk)
    pd.concat(res).to_csv(f"{pathCASE}{col.split(separator)[0]}.csv", index=False)

def make_geo_dataframe(df):
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Latitude, df.Longitude))
    gdf = gdf.set_crs('epsg:4326', inplace = True)
    return gdf

def currency_EUR_to_GBP(data_EUR):
    exchange_rate = 1.13	#https://www.finanzen.net/  Jan24th2023
    data_GBP = data_EUR / exchange_rate
    return data_GBP

def find_value_in_dataframe_w_two_cond(df, search_column_name1, search_column_name2, search_name1, search_name2, result_column_name):
    "This function looks up a value in another column"
    df_filtered = df.loc[(df[search_column_name1] == search_name1) & (df[search_column_name2] == search_name2)]
    try:
        result = float(df_filtered[result_column_name])
    except:
        try:
            result = str(df_filtered[result_column_name].item())
        except:
            try:
                result = int(df_filtered[result_column_name])
            except: 
                result = 0
    return result

def prepare_transport_data(filePath, filePath_transport):

    #import results from transport model
    gdf_cement =  pd.read_csv(f"{filePath_transport}Cement_plants_w_costs.csv",delimiter=';')
    gdf_cement = make_geo_dataframe(gdf_cement)

    #make dataframe and only keep transport costs
    gdf_transport_costs = gdf_cement[['VID', 'Capacity', 'geometry','Cost olivine transport', 'Cost biomass transport','Cost clay transport']].copy()
    gdf_transport_costs.rename(columns={'VID':'OID','Cost olivine transport': 'OLIVINE', 'Cost biomass transport': 'BIOMASS','Cost clay transport': 'CLAY'}, inplace= True)

    #make another dataframe and only keep transport emissions
    gdf_transport_emissions = gdf_cement[['VID','Transport_emissions_olivine','Transport_emissions_biomass','Transport_emissions_clay']].copy()
    gdf_transport_emissions.rename(columns={'VID':'OID','Transport_emissions_olivine': 'OLIVINE', 'Transport_emissions_biomass': 'BIOMASS','Transport_emissions_clay': 'CLAY'}, inplace= True)
    #melt emission dataframe:
    gdf_transport_emissions = gdf_transport_emissions.melt(['OID'], var_name = 'RESOURCE', value_name = 'TRANSPORT_EMISS')

    #import grid_cells
    df_grid_points = pd.read_csv( f"{filePath}grid_cells.csv", delimiter= ',')
    df_grid_points_short = df_grid_points[['OID','Grid_id']].copy()

    #merge two dataFrames and add indicator column
    all_df = pd.merge(gdf_transport_costs, df_grid_points_short, on=['OID'], how='right', indicator='exists')
    #print(all_df)

    #add column to show if each row in first DataFrame exists in second
    all_df['exists'] = np.where(all_df.exists == 'both', True, False)
    all_df_filtered = all_df[all_df['exists']==True].copy()
    all_df_filtered.drop(columns={'Capacity','geometry','exists'}, inplace= True)

    print(all_df_filtered)
    #Change currency to kGBP:
    resources = ['OLIVINE', 'BIOMASS','CLAY']
    for resource in resources:
        all_df_filtered[resource] = all_df_filtered.apply(lambda x: currency_EUR_to_GBP(x[resource]), axis=1) # transform into GBP
        all_df_filtered[resource] = all_df_filtered.apply(lambda x: (x[resource]/1000), axis=1) #transform into kt
    
    #if empty cells exist, replace them with 0
    all_df_filtered.fillna(0, inplace=True)

    #melt dataframe to be used in IDRIC
    all_df_filtered = all_df_filtered.melt(['OID','Grid_id'], var_name = 'RESOURCE', value_name = 'TRANSPORT_COEFF')

    #Add TRANSPORT EMISSIONS in tCO2 eq / tonne of material:
    all_df_filtered ["TRANSPORT_EMISS"] = all_df_filtered.apply(lambda x: find_value_in_dataframe_w_two_cond(gdf_transport_emissions, 'OID', 'RESOURCE', x['OID'], x['RESOURCE'], 'TRANSPORT_EMISS'), axis=1, result_type='expand')

    #Change emissions from kg/tonne to tonne /tonne:
    all_df_filtered ["TRANSPORT_EMISS"] /= 1000

    ##if no transport is used, replace NAN with 0
    all_df_filtered.fillna(0, inplace = True)

    #Export CSV file in input folder:
    all_df_filtered.to_csv(f"{filePath}TRANSPORT_COEFF.csv",sep=',', index=False)
    return

def fetch_GridData():
    #pathCASE = getPath_IDRICCases(CaseName)
    # load the sites from the DATA folder
    #pathDATA = getPath_toolkitData()
    #<load data csv>
    #<load OID csv in case folder>
    #<merge data>
    #<write csv file in case directory>
    pass