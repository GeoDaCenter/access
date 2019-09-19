import pandas as pd
import numpy as np
try:
    import geopandas as gpd
except:
    pass
import warnings

def weighted_catchment(loc_df, cost_df, max_cost, cost_source = "origin", cost_dest = "dest", cost_cost = "cost", 
                       loc_loc = "geoid",loc_value = None, weight_fn = None, three_stage_weight = False):
    """
    Calculation of the floating catchment (buffered) accessibility
    sum, from DataFrames with computed distances.
    This catchment may be either a simple buffer -- with cost 
      below a single threshold -- or an additional weight may be applied
      as a function of the access cost.
 
    Parameters
    ----------

    loc_df         : [pandas.DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html)
                 should contain at _least_ a list of the locations (`df_dest`) at which facilities are located.
    loc_loc    : str
                 is the the name of the df column that holds the facility locations.
    loc_value   : str
                 If this value is `None`, a count will be used in place of a weight.
                 Use this, for instance, to count restaurants, instead of total doctors in a practice.
    cost_df    : [pandas.DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html)
                 This dataframe contains the precomputed costs from an origin/index location to destinations.
    cost_source : str
                 The name of the column name of the index locations -- this is what will be grouped.
    cost_dest  : str
                 The name of the column name of the destination locations.
                 This is what will be _in_ each group.
    cost_cost  : str
                 This is is the name of the cost column.
    weight_fn  : function
                 This fucntion will weight the value of resources/facilities,
                 as a function of the raw cost.
    max_cost   : float
                 This is the maximum cost to consider in the weighted sum;
                   note that it applies _along with_ the weight function.

    Returns
    -------
    resources  : pandas.Series
                 A -- potentially weighted -- sum of resources, facilities, or consumers.
    """
    #merge the loc dataframe and cost dataframe together
    temp = pd.merge(cost_df, loc_df, left_on = cost_source, right_on = loc_loc)
     
    #apply a weight function if inputted -- either enhanced two stage or three stage
    if weight_fn:
        if not three_stage_weight:
            weights_column = temp[cost_cost].apply(weight_fn)
            new_loc_value_column = temp[loc_value]*weights_column
            temp = temp.drop([loc_value], axis = 1)
            temp[loc_value] = new_loc_value_column
        else:
            new_loc_value_column = temp[loc_value]*temp.W3*temp.G
            temp = temp.drop([loc_value], axis = 1)
            temp[loc_value] = new_loc_value_column
    #constrain by max cost 
    temp = temp[temp[cost_cost] < max_cost]
   
    #return either the count or the summation of the values of the desired weighted catchment
    if loc_value is None:
        return temp.groupby([cost_dest])[cost_source].count()
    else:
        return temp.groupby([cost_dest])[loc_value].sum()

def fca_ratio(demand_df, supply_df, demand_cost_df, supply_cost_df, max_cost,
              demand_index = 'geoid', demand_name = "demand",
              supply_index = 'geoid', supply_name  = "supply",
              demand_cost_origin = "origin", demand_cost_dest = "dest", demand_cost_name = "cost",
              supply_cost_origin = "origin", supply_cost_dest = "dest", supply_cost_name = "cost",
              weight_fn = None, normalize = False, noise = 'quiet'):
    """
    Calculation of the floating catchment accessibility
      ratio, from DataFrames with precomputed distances.
    This is accomplished through two calls of the `access.weighted_catchment` method.

    Parameters
    ----------

    demand_df          : [pandas.DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html)
                         The origins dataframe, containing a location index and a total demand.
    supply_df          : [pandas.DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html)
                         The origins dataframe, containing a location index and level of supply
    demand_cost_df     : [pandas.DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html)
                         This dataframe contains a link between neighboring demand locations, and a cost between them.
    supply_cost_df     : [pandas.DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html)
                         This dataframe contains a link between neighboring supply locations, and a cost between them.
    max_cost           : float
                         This is the maximum cost to consider in the weighted sum;
                           note that it applies _along with_ the weight function.
    demand_index       : str
                         is the name of the column that holds the IDs.
    demand_name       : str
                         is the name of the column of `demand` that holds the aggregate demand at a location.
    supply_index       : str
                         is the name of the column that holds the IDs.
    supply_name       : str
                         is the name of the column of `supply_df` that holds the aggregate supply at a location.
    demand_cost_origin : str
                         The column name of the index locations -- this is what will be grouped.
    demand_cost_dest   : str
                         The column name of the index locations -- this is what will be grouped.
    demand_cost_name   : str
                         The column name of the travel cost.
    supply_cost_origin : str
                         The column name of the index locations -- this is what will be grouped.
    supply_cost_dest   : str
                         The column name of the index locations -- this is what will be grouped.
    supply_cost_name   : str
                         The column name of the travel cost.
    weight_fn          : function
                         This function will weight the value of resources/facilities,
                         as a function of the raw cost.
    normalize          : bool
                         True to normalize the FCA series, by default False.
    noise              : str
                         Default 'quiet', otherwise gives messages that indicate potential issues.

    Returns
    -------
    access     : pandas.Series
                 A -- potentially-weighted -- access ratio.
    """
    #if there is a discrepancy between the demand and supply cost dataframe locations, print it
    if len(set(demand_df.index.tolist()) - set(supply_cost_df[supply_cost_dest].unique())) != 0:
        warnings.warn("some tracts may be unaccounted for in supply_cost")
        

    #get a series of the total demand within the buffer zone
    total_demand_series = weighted_catchment(demand_df, demand_cost_df, max_cost, 
                                          cost_source = demand_cost_dest, cost_dest = demand_cost_origin, cost_cost = demand_cost_name,
                                          loc_loc = demand_index, loc_value = demand_name, 
                                          weight_fn = weight_fn)
    #get a series of the total supply within the buffer zone
    total_supply_series = weighted_catchment(supply_df, supply_cost_df, max_cost, 
                                          cost_source = supply_cost_dest, cost_dest = supply_cost_origin, cost_cost = supply_cost_name,
                                          loc_loc = supply_index, loc_value = supply_name, 
                                          weight_fn = weight_fn)
    
    #join the aggregate demand and the aggregate supply into one dataframe
    temp = total_supply_series.to_frame(name = 'supply').join(total_demand_series.to_frame(name = 'demand'), how = 'right').fillna(0)
    
    #calculate the floating catchement area, or supply divided by demand 
    temp['FCA'] = temp['supply'] / temp['demand']
    base_FCA_series = temp['FCA']
    
    if noise != 'quiet':
        #depending on the version history of the census tract data you use, this will print out the tracts that have undefined FCA values
        print (base_FCA_series[pd.isna(base_FCA_series)])

    return base_FCA_series