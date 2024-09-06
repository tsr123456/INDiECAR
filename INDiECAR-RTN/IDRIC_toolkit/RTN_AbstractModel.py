import os.path
import cloudpickle
import pyomo.environ as pyo
import pandas as pd
import IDRIC_toolkit.initialisation_rules as init
import IDRIC_toolkit.constraint_rules as rule


def create_sets(m, GRID_IDS):
    """creates all sets and subsets for the RTN problem formulation"""
    # ---- GRID
    m.G = pyo.Set(initialize=GRID_IDS)
    
    # ---- TIMES
    m.T = pyo.Set(ordered=True)         # minor time step: operational
    m.TM = pyo.Set(ordered=True)        # major time step: investment

    # ---- RESOURCES
    m.R = pyo.Set(ordered=True)
    # subsets
    m.R_BALANCED = pyo.Set(within=m.R)  # resources which can not be emitted
    m.R_POLLUTANT = pyo.Set(within=m.R) # resources which could be emitted
    m.IMP_R = pyo.Set(within=m.R)       # importable resources
    m.TRAN_R = pyo.Set(within=m.R)       # transportable resources
    m.STORAGE_R = pyo.Set(within=m.R)   # storable resources
    # sub-subsets
    #m.STORABLE_H2 = Set(within=m.STORAGE_R)
    m.STORABLE_CO2 = pyo.Set(within=m.STORAGE_R)

    # ---- TECHNOLOGIES
    m.J = pyo.Set(ordered=True)
    # subsets
    m.PROCESS_TECH = pyo.Set(within=m.J)
    m.END_USE_TECH = pyo.Set(within=m.J)
    m.STRG_TECH = pyo.Set(within=m.J)
    # sub-sub sets: process
    m.CEMENT_INTERVENTIONS = pyo.Set(within=m.PROCESS_TECH)
    m.CCGT_INTERVENTIONS = pyo.Set(within=m.PROCESS_TECH)
    m.REFINERY_INTERVENTIONS = pyo.Set(within=m.PROCESS_TECH)
    m.STEELBFBOF_INTERVENTIONS = pyo.Set(within=m.PROCESS_TECH)
    m.TERMINAL_INTERVENTIONS = pyo.Set(within=m.PROCESS_TECH)
    # sub-sub sets: end use
    m.INCUMBENT_USE_TECH = pyo.Set(within=m.END_USE_TECH)
    m.POSTCOMB = pyo.Set(within=m.END_USE_TECH)
    m.NO_POSTCOMB = pyo.Set(within=m.END_USE_TECH)
    # sub-sub sets: storage
    m.CO2_STORAGE_TECH = pyo.Set(within=m.STRG_TECH)
    #m.H2_STORAGE_TECH = Set(within=m.STRG_TECH)
    m.STORAGE_TECH_ONSHORE = pyo.Set(within=m.STRG_TECH)
    m.STORAGE_TECH_OFFSHORE = pyo.Set(within=m.STRG_TECH)

    # ---- DISTRIBUTION
    m.D = pyo.Set(ordered=True)
    m.DIST_MODE = pyo.Set(ordered=True)
    # subsets
    m.PIPES_CO2 = pyo.Set(within=m.D)
    m.PIPES_NATGAS = pyo.Set(within=m.D)
    #m.PIPES_HYDROGEN = Set(within=m.D)
    m.PIPES_OFFSHORE = pyo.Set(within=m.D)
    m.PIPES_ONSHORE = pyo.Set(within=m.D)
    #m.SHIPS_CO2 = Set(within=m.D)

    # ---- METRIC
    m.M = pyo.Set(ordered=True)
    # subsets
    #m.LCA_METRICS = Set(within=m.M)

    # ---- SCENARIOS
    m.S = pyo.Set(ordered=True)


def create_params(m):
    """creates all parameters for the RTN problem formulation"""
    # A parameter containing the LCA scores for various technologies.
    #m.LCA_SCORE = Param(m.J,m.LCA_METRICS,default=0)

    # A parameter containing the LCA scores for network technologies.
    #m.NETWORK_LCA = Param(m.D,m.LCA_METRICS,default=0)

    # A parameter containing the LCA scores for storage technologies.
    #m.STRG_LCA = Param(m.STRG_TECH,m.LCA_METRICS,default=0)

    # Number of base time units within each minor time period.
    m.OPER_TIME_INTERVAL = pyo.Param(m.T)

    # The temporal variation relative to average within each minor time period.
    #m.OPER_TIME_SIGNAL = Param(m.R, m.T, default=1)

    # Spatio-temporal discrete representation of demand for a given resource.
    m.DEMAND = pyo.Param(m.R, m.G, m.T, m.TM, m.S, default=0, mutable=False)

    # Capture fraction of generated emissions.
    m.CO2_REMOVAL_FRACTION = pyo.Param(m.TM, mutable=True)

    # Total CO2 storage capacity in each grid.
    m.TOT_CO2_STORES = pyo.Param(m.G, default=0)

    # Total CO2 storage capacity in each grid.
    #m.TOT_H2_STORES = Param(m.G, default=0)

    # Distances between grid cells in km.
    m.DISTANCE = pyo.Param(m.G, m.G)

    # Weight of each metric in each major period.
    m.OBJ_WEIGHT = pyo.Param(m.M, m.TM)

    # Resource import metrics.
    m.IMPORT_COEFF = pyo.Param(m.IMP_R, m.M, default=0)

    # Resource transport metrics.
    m.TRANSPORT_COEFF = pyo.Param(m.TRAN_R, m.G, default=0)

    # Resource transport emission metrics.
    m.TRANSPORT_EMISS = pyo.Param(m.TRAN_R, m.G, default=0)

    # Network design metrics.
    m.NETWORK_COEFF = pyo.Param(m.D, m.M, default=0)

    # Flow metric coefficients.
    m.FLOW_COEFF = pyo.Param(m.D, m.M, default=0)

    # Nameplate capacity of technologies.
    m.NAME_PLATE_CAP = pyo.Param(m.J,default=0)

    # Minimum capacity of technologies.
    m.MIN_CAP = pyo.Param(m.J,default=0)

    # Exogenously imposed learning rate measured as a fraction..
    m.LEARNING_RED = pyo.Param(m.J, m.TM, default=1)

    # Maximum injection rate into the storage technology..
    m.MAX_INJECTION_RATE = pyo.Param(m.STRG_TECH, default=0)

    # Maximum retrieval rate into the storage technology..
    m.MAX_RETRIEVAL_RATE = pyo.Param(m.STRG_TECH, default=0)

    # Technology availability to define the start time of first investment.
    m.TECH_AVAILABILITY = pyo.Param(m.J, m.TM, default=1)

    # Capital investment metrics.
    m.INV_COEFF = pyo.Param(m.J, m.M, m.TM, default=0)

    # Initialise the investment coefficient in each grid.
    m.INV_COEFF_GRID = pyo.Param(m.J, m.G, m.M, m.TM, 
        default=0,
        initialize=init.init_INV_COEFF)

    # Operational metrics due to producing H2.
    m.PROCESS_COEFF = pyo.Param(m.J, m.M, m.TM, 
        default=0,
        initialize=init.init_PROCESS_COEFF)

    # RTN production/consumption coefficients.
    m.RESOURCE_CONV_RATE = pyo.Param(m.J, m.R, default=0)

    # Maximum flow of resource through a distribution mode.
    m.FLOW_RSRC_MAX = pyo.Param(m.D)

    # Represent existing infrastructure UNITS by "initial" parameters
    m.EXSTNG_TECH = pyo.Param(m.PROCESS_TECH, m.G, m.TM, default=0, mutable=False)
    m.EXSTNG_STRG = pyo.Param(m.R, m.STRG_TECH, m.G, m.TM, default=0, mutable=False)
    m.EXSTNG_PIPES = pyo.Param(m.G, m.G, m.D, m.TM, default=0, mutable=False)
    m.INITIAL_PIPES = pyo.Param(m.G, m.G, m.D, m.TM, default=1, mutable=False)

    # Represent existing resource flow rates into system by "initial" parameters
    m.EXSTNG_RSRCrate = pyo.Param(m.R, m.G, m.T, m.TM, default=0, mutable=False)

    # Emission Factor deviation for the source on the basis of fuel.
    #m.EMISSION_FACTOR = Param(m.G)

    #def EMISSION_FACTOR_init(m,r,g):
    #   if r == name_for_uncaptured_CO2:
    #       return m.EMISSION_FACTOR[g]
    #   else:
    #       return 0

    # Emission factors for region specific emission sources.
    #m.RESOURCE_FACTOR = Param(m.R, m.G, 
        #default=0, initialize=EMISSION_FACTOR_init,
        #mutable=True)

    # Probability of scenario occurence.
    m.PROBABILITY = pyo.Param(m.S, default=1)

    # Coefficients to describe the flow consumption parameter.
    m.FLOW_CONSUMPTION_COEFF = pyo.Param(m.D, m.DIST_MODE, m.R, default=0, 
        within=pyo.NonNegativeReals)

    # Coefficients to describe the flow production parameter.
    m.FLOW_PRODUCTION_COEFF = pyo.Param(m.D, m.DIST_MODE, m.R, default=0, 
        within=pyo.NonNegativeReals)

    # Parameter to indicate if a region, g is onshore or offshore.
    m.ONSHORE_GRIDS = pyo.Param(m.G, within=pyo.Binary)
    m.LANDFALL = pyo.Param(m.G, default=0, within=pyo.Binary)
    m.HARBOUR = pyo.Param(m.G, default=0, within=pyo.Binary)

    m.GRIDTYPECODE = pyo.Param(m.G, default=0, within=pyo.NonNegativeIntegers)

    #m.EMISSIONS_GRIDDED = Param(m.G)
    m.EMISSIONS_GRIDDED_t0 = pyo.Param(m.G, m.S,
        within=pyo.NonNegativeReals, 
        initialize=init.init_emissiongridded_t0,
        mutable=False)
    
    # Import locations present - True (1)  or False (0).
    m.IMPORT_LOCATIONS = pyo.Param(m.G)

    # Location factor for variable cost as function of the location.
    m.LOCATION_FACTOR = pyo.Param(m.G)

    # Operational availability of the assets located in a particular region.
    m.AVAILABILITY= pyo.Param(m.G)

    # Storage coefficient - operational effects due to storing.
    m.STRG_COEFF = pyo.Param(m.STRG_TECH, m.M, default=0)

    # Storage technology efficiency.
    m.RETRIEVAL_EFFICIENCY = pyo.Param(m.STRG_TECH, default=1)


def create_vars(m, MAX_END_USE_TECH_PER_CELL, MAX_STRG_TECH_PER_CELL,
                MAX_DIST_TECH_PER_CELL, MAX_RATE, BIG_M):
    """creates all variables for the RTN problem formulation"""
    # ---- UNITS ----
    # units are described by the technology m.J (or subsets thereof); they 
    # exist in a grid cell m.G at the investment time m.TM for all scenarios 
    # in m.S. 'num_*_invest' denotes the new investments at time TM, whereas
    # 'num_*' represent the total number of the respective technologies at TM,
    # taking into account the existing technologies.

    # number of production process: large-scale industrial (integer-decision)
    m.num_process = pyo.Var(m.PROCESS_TECH, m.G, m.TM, m.S, # process grid  time scenario.
        domain=pyo.Binary,
        initialize=init.init_num_process)

    m.num_process_invest = pyo.Var(m.PROCESS_TECH, m.G, m.TM, m.S,
        domain=pyo.Binary,
        initialize=init.init_num_processinvest)

    # number of end-use technology: small to medium scale units (continuous)
    m.num_end_use = pyo.Var(m.END_USE_TECH, m.G, m.TM, m.S,
        domain=pyo.NonNegativeReals,
        bounds=(0, MAX_END_USE_TECH_PER_CELL),
        initialize=int(MAX_END_USE_TECH_PER_CELL/2))

    m.num_end_use_invest = pyo.Var(m.END_USE_TECH, m.G, m.TM, m.S,
        domain=pyo.NonNegativeReals,
        bounds=(0, MAX_END_USE_TECH_PER_CELL),
        initialize=int(MAX_END_USE_TECH_PER_CELL/2))

    # number of storage technology (integer-decision)
    m.num_strg = pyo.Var(m.STORAGE_R, m.STRG_TECH, m.G, m.TM, m.S,
        domain=pyo.NonNegativeIntegers,
        bounds=(0, MAX_STRG_TECH_PER_CELL),
        initialize=init.init_num_strg)

    m.num_strg_invest = pyo.Var(m.STORAGE_R, m.STRG_TECH, m.G, m.TM, m.S,
        domain=pyo.NonNegativeIntegers,
        bounds=(0, MAX_STRG_TECH_PER_CELL),
        initialize=init.init_num_strginvest)

    # number of pipes built between grid cells (integer-decision)
    m.num_pipes = pyo.Var(m.G, m.G, m.D, m.TM, m.S,
        domain=pyo.NonNegativeIntegers,
        bounds=(0, MAX_DIST_TECH_PER_CELL),
        initialize=init.init_num_pipeCO2)

    m.num_pipes_invest = pyo.Var(m.G, m.G, m.D, m.TM, m.S,
        domain=pyo.NonNegativeIntegers,
        bounds=(0, MAX_DIST_TECH_PER_CELL),
        initialize=init.init_num_pipeinvest)

    # ---- RATES ----
    # Rates describe the temporal change in resources and are thus time-
    # dependent, i.e., function of m.T (contrary to UNITS). The retrieval and
    # storage rates are defined by resource, grid cell and used technology.
    # The emission rate denotes the emitted pollutants, i.e., unbalanced
    # resources and is thus not depending on a technology. Equally, the import
    # rate does not require a the indication of a technology. The production
    # rate is defined for an installed technology and the resource flows 
    # follow from the RESOURCE_CONV_RATE values. Similarly, the flow rate is 
    # defined between two grid cells and the distribution technology. Resource
    # flows follow from FLOW_PRODUCTION_COEFF and FLOW_CONSUMPTION_COEFF.

    # Retrieval rate of a resource from storage technologies
    m.retrieval_rate = pyo.Var(m.R, m.G, m.STRG_TECH, m.T, m.TM, m.S,
        domain=pyo.NonNegativeReals,
        bounds=(0, MAX_RATE),
        initialize=init.init_retrieval_rate)

    # Storage rate of a resource into storage technologies.
    m.storage_rate = pyo.Var(m.R, m.G, m.STRG_TECH, m.T, m.TM, m.S,
        domain=pyo.NonNegativeReals,
        bounds=(0, MAX_RATE),
        initialize=init.init_storage_rate)

    # Rate of emitting resources (POLLUTANTS) in each grid cell
    m.emission_rate = pyo.Var(m.R, m.G, m.T, m.TM, m.S,
        domain=pyo.NonNegativeReals,
        bounds=(0, MAX_RATE),
        initialize=init.init_emission_rate)

    # Import rate of a resource 
    m.import_rate = pyo.Var(m.R, m.G, m.T, m.TM, m.S,
        domain=pyo.NonNegativeReals,
        initialize=init.init_import_rate,
        bounds=(0, MAX_RATE))

    # transport rate of a resource 
    m.transport_rate = pyo.Var(m.R, m.G, m.T, m.TM, m.S,
        domain=pyo.NonNegativeReals,
        initialize=init.init_transport_rate,
        bounds=(0, MAX_RATE))

   # transport emissions of a resource 
    m.transport_emissions = pyo.Var(m.R, m.G, m.T, m.TM, m.S,
        domain=pyo.NonNegativeReals,
        initialize=init.init_transport_emissions,
        bounds=(0, MAX_RATE))

    # Production rate of resources based on technology
    m.prod_rate = pyo.Var(m.J, m.G, m.T, m.TM, m.S, 
        domain=pyo.NonNegativeReals,
        bounds=(0, MAX_RATE),
        initialize=0)

    # Flow rate of resources between grid cells
    m.flow_rate = pyo.Var(m.G, m.G, m.D, m.DIST_MODE, m.T, m.TM, m.S,
        domain=pyo.NonNegativeReals,
        initialize=init.init_flow_rate,
        bounds=(0, MAX_RATE))

    # ---- AGGREGATES ----
    # Continuous values resulting from the UNIT decision and the subsequent 
    # resource flows within the system

    # Inventory level for a resource in storage technologies
    m.inventory_rsrc = pyo.Var(m.R, m.G, m.STRG_TECH, m.T, m.TM, m.S,
        domain=pyo.NonNegativeReals,
        bounds=(0, BIG_M),
        initialize=0)

    # Total value of metric m in major period tm
    m.total_metrics = pyo.Var(m.M, m.TM, m.S, 
        domain=pyo.NonNegativeReals,
        bounds=(0, BIG_M),
        initialize=0)


def add_constraints(m, CCS_network_only):
    """add constraints to model instance"""
    # ---- UNITS ---- 
    m.j1process = pyo.Constraint(m.PROCESS_TECH, m.G, m.TM, m.S, rule=rule.eqnJ1_process)
    m.j6process = pyo.Constraint(m.G, m.TM, m.S, rule=rule.eqnJ6_max_num_process)
    m.j1enduse = pyo.Constraint(m.END_USE_TECH, m.G, m.TM, m.S, rule=rule.eqnJ1_enduse)
    m.d1pipes = pyo.Constraint(m.G, m.G, m.D, m.TM, m.S, rule=rule.eqnD1_pipes)
    m.s1 = pyo.Constraint(m.STORAGE_R, m.STRG_TECH, m.G, m.TM, m.S, rule=rule.eqnS1)

    # ---- RATES ----
    m.s2 = pyo.Constraint(m.R, m.G, m.STRG_TECH, m.T, m.TM, m.S, rule=rule.eqnS2)
    m.r2cell = pyo.Constraint(m.R, m.G, m.T, m.TM, m.S, rule=rule.eqnR2_CellBalance)
    #m.transport = pyo.Constraint(m.R, m.G, m.T, m.TM, m.S, rule = rule.eqnR2_add_transport_emissions)
    m.CO2reduction = pyo.Constraint(m.TM, m.S, rule=rule.eqnR2_NetBalanceCO2)
        

    # ---- UNITS + RATES ----
    m.d3 = pyo.Constraint(m.G,m.G, m.D, m.T,m.TM, m.S, rule=rule.eqnD3)
    m.s3inj = pyo.Constraint(m.STORAGE_R, m.G, m.STRG_TECH, m.T, m.TM, m.S, rule=rule.eqnS3_inj)
    m.s3ret = pyo.Constraint(m.STORAGE_R, m.G, m.STRG_TECH, m.T, m.TM, m.S, rule=rule.eqnS3_ret)
    m.s3co2 = pyo.Constraint(m.G, m.CO2_STORAGE_TECH, m.T, m.TM, m.S, rule=rule.eqnS3_injCO2)
    m.j3process = pyo.Constraint(m.PROCESS_TECH, m.G, m.T, m.TM, m.S, rule=rule.eqnJ3_process)
    m.j3enduse = pyo.Constraint(m.END_USE_TECH, m.G, m.T, m.TM, m.S, rule=rule.eqnJ3_enduse)

    # ---- AGGREGATES ----
    m.s4co2 = pyo.Constraint(m.G, m.CO2_STORAGE_TECH, m.T, m.TM, m.S, rule=rule.eqnS4_CO2)
    m.s4rest = pyo.Constraint(m.R, m.G, m.STRG_TECH, m.T, m.TM, m.S, rule=rule.eqnS4_rest)
    m.Mcpx = pyo.Constraint(m.TM, m.S, rule=rule.eqnM_CAPEX)
    m.Mopx = pyo.Constraint(m.TM, m.S, rule=rule.eqnM_OPEX)

    # ---- UNITS: distribution ----
    m.D5_CO2 = pyo.Constraint(m.G, m.G, m.TM, m.S, rule=rule.eqnD5_CO2)
    m.D5_NATGAS = pyo.Constraint(m.G, m.G, m.TM, m.S, rule=rule.eqnD5_NATGAS)
    m.D6_CO2 = pyo.Constraint(m.G, m.TM, m.S, rule=rule.eqnD6_CO2)

    # ---- UNITS: technology ----
    if not(CCS_network_only):
        m.j5NA = pyo.Constraint(m.PROCESS_TECH, m.G, m.TM, m.S, 
                                rule=rule.eqnJ5_NoAction)


def add_objectives(m, obj):
    """"""
    func = {'TLC': rule.eqnO_TotLevCost}
    m.obj = pyo.Objective(rule=func[obj], sense=pyo.minimize)


def implement_RTN(GRID_IDS, CCS_network_only, obj):
    """"""
    # create model instance
    model = pyo.AbstractModel()

    # create and define sets
    create_sets(model, GRID_IDS)
    # -- add values from csv files (pandas)

    # create and define parameters
    create_params(model)

    # create and initiate variables
    MAX_END_USE_TECH_PER_CELL = 10000
    MAX_STRG_TECH_PER_CELL = 35
    MAX_DIST_TECH_PER_CELL = 2
    MAX_RATE = 2000
    BIG_M = 10000000000
    create_vars(model, MAX_END_USE_TECH_PER_CELL, MAX_STRG_TECH_PER_CELL,
                MAX_DIST_TECH_PER_CELL, MAX_RATE, BIG_M)
    
    # add ALL constraints
    add_constraints(model, CCS_network_only)

    # add ALL objective functions
    add_objectives(model, obj)

    return model


def backcast_model(instance):
    """"""
    instance = init.backcasting(instance, instance)
    return instance


def backcast_model_from_reference(instance, pathCase, RunName, RefStateGate):
    """"""
    pathREF = f"{pathCase}{RunName}/{RefStateGate}"
    with open(f"{pathREF}/instance.pkl", mode='rb') as f:
        reference = cloudpickle.load(f)
    instance = init.backcasting(instance, reference)
    return instance


def is_csv_file_empty(filename):
    df = pd.read_csv(filename)
    return df.empty 


def instantiate_model(pathCASE, install_CC, CCS_network_only, obj):
    """"""
    # path to input data location
    path = f"{pathCASE}input/"

    ## --- create new Abstract model ---
    g = pd.read_csv(f"{path}grid_cells.csv")
    GRID_IDS = g['Grid_id'].to_list()
    model = implement_RTN(GRID_IDS, bool(CCS_network_only), obj)
    
    ## --- load data ---
    data = pyo.DataPortal(model=model)
    # load distances among grid cells
    data.load(filename = f"{path}Gridded_Linear_Distances.csv", 
        param = ['DISTANCE'],
        format = "array")

    # load existing technologies/processes IF specified
    if not(is_csv_file_empty(f"{path}existing_tech.csv")):
        data.load(filename = f"{path}existing_tech.csv", 
            param = ['EXSTNG_TECH'],
            index = ['process_tech', 'grid_id', 'TM'])
    
    # load existing pipelines IF specified
    if not(is_csv_file_empty(f"{path}existing_pipelines.csv")):
        data.load(filename = f"{path}existing_pipelines.csv", 
            param = ['EXSTNG_PIPES'],
            index = ['grid_from', 'grid_to', 'type', 'TM'])

    # load initial pipelines IF specified
    if os.path.exists(f"{path}initial_pipelines.csv"):
        if not(is_csv_file_empty(f"{path}initial_pipelines.csv")):
            data.load(filename = f"{path}initial_pipelines.csv", 
                param = ['INITIAL_PIPES'],
                index = ['grid_from', 'grid_to', 'type', 'TM'])
    
    # load existing storage IF specified
    if os.path.exists(f"{path}existing_storage.csv"):
        if not(is_csv_file_empty(f"{path}existing_storage.csv")):
            data.load(filename = f"{path}existing_storage.csv", 
                param = ['EXSTNG_STRG'],
                index = ['RESOURCE', 'STRG_TECH', 'grid_id', 'TM'])

    # load existing resource rates IF specified
    if not(is_csv_file_empty(f"{path}Gridded_ResourceRates.csv")):
        data.load(filename = f"{path}Gridded_ResourceRates.csv", 
            param = ['EXSTNG_RSRCrate'],
            index = ['RESOURCE', 'grid_id', 'T', 'TM'])
    
    # load resource demands: in [t/hhr] or [MWh/hhr]
    data.load(filename = f"{path}Gridded_Demand.csv", 
        param = ['DEMAND'],
        index = ['RESOURCE', 'grid_id', 'T', 'TM', 'S'])
    
    # load gridded data
    data.load(filename = f"{path}grid_cells.csv", 
        select = ['Grid_id', 'GRIDTYPE', 'GRIDTYPECODE', 'TOT_CO2_STORES', 
                  'LANDFALL', 'ONSHORE_GRIDS', 'IMPORT_LOCATIONS', 
                  'EMISSION_FACTOR', 'LOCATION_FACTOR', 'AVAILABILITY', 
                  'HARBOUR'],
        param = ['GRIDTYPE', 'GRIDTYPECODE', 'TOT_CO2_STORES', 'LANDFALL',
                 'ONSHORE_GRIDS', 'IMPORT_LOCATIONS', 'EMISSION_FACTOR',
                 'LOCATION_FACTOR', 'AVAILABILITY', 'HARBOUR'],
        index = ['grid_id'])

    # load transport factors:
    if os.path.exists(f"{path}TRANSPORT_COEFF.csv"):
        if not(is_csv_file_empty(f"{path}TRANSPORT_COEFF.csv")):
            data.load(filename = f"{path}TRANSPORT_COEFF.csv", 
                select = ['RESOURCE','Grid_id','TRANSPORT_COEFF','TRANSPORT_EMISS'],
                param = ['TRANSPORT_COEFF', 'TRANSPORT_EMISS'],
                index = ['RESOURCE','Grid_id'])


    ### Load Cost functions from IDRIC sheet
    #Name plate capacity
    data.load(filename = f"{path}NAME_PLATE_CAP.csv", 
        select = ['J','NAME_PLATE_CAP'],
        param = ['NAME_PLATE_CAP'],
        index = ['J'])

    #Minimum capacity
    if os.path.exists(f"{path}MIN_CAP.csv"):
        if not(is_csv_file_empty(f"{path}MIN_CAP.csv")):
            data.load(filename = f"{path}MIN_CAP.csv", 
                select = ['J','MIN_CAP'],
                param = ['MIN_CAP'],
                index = ['J'])

    #Investment coefficients (CAPEX + fixed OPEX)
    data.load(filename = f"{path}INV_COEFF.csv", 
        select = ['J','M','OBJ_WEIGHT','INV_COEFF'],
        param = ['INV_COEFF'],
        index = ['J','M','OBJ_WEIGHT'])
    
    #Process coefficients (Variable OPEX)
    data.load(filename = f"{path}PROCESS_COEFF.csv", 
        select = ['J','M','OBJ_WEIGHT','PROCESS_COEFF'],
        param = ['PROCESS_COEFF'],
        index = ['J','M','OBJ_WEIGHT'])

    #Resource conversion rates (Mass&energy balance)
    data.load(filename = f"{path}RESOURCE_CONV_RATE.csv", 
        select = ['J','R','RESOURCE_CONV_RATE'],
        param = ['RESOURCE_CONV_RATE'],
        index = ['J','M'])

   
    # install the CC interventions for INCUMBENT tech
    if bool(install_CC):
        # build CCS to existing incumbent plants
        d = data['EXSTNG_TECH'].copy()
        for pt, g, tm in data['EXSTNG_TECH'].keys():
            [flag, tech] = pt.split('_')
            if flag == 'INCUMBENT':
                CCS_tech = 'CCS_' + tech
                d[(CCS_tech, g, tm)] = 1
        data['EXSTNG_TECH'] = d
    if bool(CCS_network_only):
        # load remaining data from .dat file
        data.load(filename=f"{path}RTN_CCS.dat")
    else:
        # load .dat file
        data.load(filename=f"{path}RTN.dat")

    ## --- instantiate the model ---
    instnc = model.create_instance(data)

    return instnc