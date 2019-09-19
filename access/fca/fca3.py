import pandas as pd
import numpy as np
try:
    import geopandas as gpd
except:
    pass
from .fca1 import weighted_catchment
from ..weights.weights import step_fn

def three_stage_fca(demand_df, supply_df, cost_df, max_cost,
                  demand_index = "geoid", demand_name   = "demand",
                  supply_index = "geoid",   supply_name   = "supply",
                  cost_origin = "origin", cost_dest = "dest", cost_name = "cost",
                  weight_fn = None, normalize = False):
    """
    Calculation of the floating catchment accessibility
      ratio, from DataFrames with precomputed distances.
    This is accomplished through a single call of the `access.weighted_catchment` method,
      to retrieve the patients using each provider.
    The ratio of providers per patient is then calculated at each care destination,
      and that ratio is weighted and summed at each corresponding demand site.
    The only difference weight respect to the 2SFCA method is that,
      in addition to a distance-dependent weight (`weight_fn`), 
      a preference weight $G$ is calculated.  That calculation
      uses the value $\beta$.
    See the original paper by: .

    Parameters
    ----------

    demand_df     : [pandas.DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html)
                    The origins dataframe, containing a location index and a total demand.
    demand_origin : str
                    is the name of the column of `demand` that holds the origin ID.
    demand_value  : str
                    is the name of the column of `demand` that holds the aggregate demand at a location.
    supply_df     : [pandas.DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html)
                    The origins dataframe, containing a location index and level of supply
    supply_df     : [pandas.DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html)
                    The origins dataframe, containing a location index and level of supply
    cost_df       : [pandas.DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html)
                    This dataframe contains a link between neighboring demand locations, and a cost between them.
    cost_origin   : str
                    The column name of the locations of users or consumers.
    cost_dest     : str
                    The column name of the supply or resource locations.
    cost_name     : str
                    The column name of the travel cost between origins and destinations
    weight_fn  : function
                 This fucntion will weight the value of resources/facilities,
                 as a function of the raw cost.
    max_cost   : float
                 This is the maximum cost to consider in the weighted sum;
                   note that it applies _along with_ the weight function.
    preference_weight_beta : float
                             Parameter scaling with the gaussian weights, 
                               used to generate preference weights.

    Returns
    -------
    access     : pandas.Series
                 A -- potentially-weighted -- three-stage access ratio.
    """
    
    #create preference weight 'G', which is the weight
    cost_df["W3"] = cost_df[cost_name].apply(weight_fn)
    W3sum_frame = cost_df[["origin", "W3"]].groupby('origin').sum().rename(columns = {"W3" : "W3sum"}).reset_index()
    cost_df = pd.merge(cost_df, W3sum_frame)
    cost_df["G"] = cost_df.W3 / cost_df.W3sum
    
    #get a series of total demand then calculate the supply to total demand ratio for each location
    total_demand_series = weighted_catchment(demand_df, cost_df, max_cost, 
                                          cost_source = cost_origin, cost_dest = cost_dest, cost_cost = cost_name,
                                          loc_loc = demand_index, loc_value = demand_name, 
                                          weight_fn = weight_fn, three_stage_weight = True)
    
    #create a temporary dataframe, temp, that holds the supply and aggregate demand at each location
    temp = supply_df.join(total_demand_series, how = 'right')
    
    #there may be NA values due to a shorter supply dataframe than the demand dataframe. 
    #in this case, replace any potential NA values(which correspond to supply locations with no supply) with 0.
    temp.fillna(0, inplace = True)
    
    #calculate the fractional ratio of supply to aggregate demand at each location, or Rl
    temp['Rl'] = temp[supply_name] / temp[demand_name]
        
    #separate the fractional ratio of supply to aggregate demand at each location, or Rl, into a new dataframe
    supply_to_total_demand_frame = pd.DataFrame(data = {'Rl':temp['Rl']})
    supply_to_total_demand_frame.index.name = 'geoid'
    
    #sum, into a series, the supply to total demand ratios for each location
    three_stage_fca_series = weighted_catchment(supply_to_total_demand_frame, cost_df.sort_index(), max_cost, 
                                          cost_source = cost_dest, cost_dest = cost_origin, cost_cost = cost_name,
                                          loc_loc = 'geoid', loc_value = "Rl", 
                                          weight_fn = weight_fn, three_stage_weight = True)
        
    #remove the preference weight G from the original costs dataframe
    cost_df.drop(columns = ["G", "W3", "W3sum"], inplace = True)
    
    return three_stage_fca_series

