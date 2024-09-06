from __future__ import division

# USER SETTINGS -------------------------------------------------------------
# TODO: load/parse user setting from case input files
MAX_DIST = 999
MAX_DIST_TECH_PER_CELL = 4
MAX_STRG_TECH_PER_CELL = 1000
INIT_INTERVENTION = 0
BIG_M = 10000000000


# ---- PARAMETERS -----------------------------------------------------------

def init_INV_COEFF(m, j, g, m0, tm):
    """Defines the investment coefficient in each grid cell."""
    # NOTE: this coeff is NOT a function of the grid cell (identical for all)
    return m.INV_COEFF[j, m0, 1] * m.LEARNING_RED[j, tm]


def init_PROCESS_COEFF(m, j, m0, tm):
    """Defines the process investment coefficient."""
    return m.PROCESS_COEFF[j, m0, 1] * m.LEARNING_RED[j, tm]


def init_emissiongridded_t0(m, g, s):
    """Computes the initial emission from EXSTNG_TECH and EXSTNG_RSRCrate."""
    t0_emissions = 0
    # identify emission from initialised technology processes
    exst_tech = [k for k in m.EXSTNG_TECH.keys() if m.EXSTNG_TECH[k] > 0]
    rCO2 = "GENERATED_CO2"
    for pt, gInit, _ in exst_tech:
        # check grid cell: do we have a EXSTNG_TECH in grid cell
        if g != gInit:
            continue
        # determine produced resource by exst_tech
        for r in m.R_BALANCED:
            if (m.RESOURCE_CONV_RATE[pt, r] == 1) & (r != rCO2):
                r_prod = r
                continue
        # assess CO2 based on demand
        conv_CO2 = m.RESOURCE_CONV_RATE[pt, rCO2]
        for t in m.T:
            time = m.OPER_TIME_INTERVAL[t]
            t0_emissions += m.DEMAND[r_prod, g, t, 1, s] * conv_CO2 * time
    
    # add emission from initialisation
    rCO2 = "EMITTED_CO2"
    for t in m.T:
        time = m.OPER_TIME_INTERVAL[t]
        t0_emissions += m.EXSTNG_RSRCrate[rCO2, g, t, 1] * time
    return t0_emissions


# ---- VARIABLES ------------------------------------------------------------

def init_num_strg(m, r, strg_tech, g, tm, s):
    """Defines the storage unit constraints."""
    # No storage units if resource not storable or no tech available
    if (r not in m.STORAGE_R):
        m.num_strg[r, strg_tech, g, tm, s].fixed = True
        return 0
    # catch CO2 storage: for offshore points
    elif (r in m.STORABLE_CO2):
        # storage tech for CO2 and offshore + point and resource offshore
        tech = (strg_tech in m.CO2_STORAGE_TECH) & (strg_tech in m.STORAGE_TECH_OFFSHORE)
        off = (m.ONSHORE_GRIDS[g] == 0) & ('OFFSHORE' in r)
        if tech & off:
            return int(MAX_STRG_TECH_PER_CELL/2)
        # all other combinations with CO2 are not valid
        else:
            m.num_strg[r, strg_tech, g, tm, s].fixed = True
            return 0
    # <add other storable resources here>
    else:
        m.num_strg[r, strg_tech, g, tm, s].fixed = True
        return 0
    

def init_num_strginvest(m, r, strg_tech, g, tm, s):
    """Defines the storage unit constraints for new investment."""
    # base initialisation on the function: init_num_strg()
    init_fixed = m.num_strg[r, strg_tech, g, tm, s].fixed
    zero_val = m.num_strg[r, strg_tech, g, tm, s].value == 0
    if zero_val & init_fixed:
        m.num_strg_invest[r, strg_tech, g, tm, s].fixed = True
        return 0
    else:
        return int(MAX_STRG_TECH_PER_CELL/2)


def init_num_process(m, process_tech, g, tm, s):
    """Constrains the number of process technologies."""
    # TODO: look-up gridtypecode
    # 10: power CCGT
    # 11: cement
    # 12: refinery
    # 13: steel BFBOF
    # 20: storage
    # 30: terminal
    # 40: trunkline

    # catch POWER CCGT
    if m.GRIDTYPECODE[g] == 10:
        if process_tech in m.CCGT_INTERVENTIONS:
            return INIT_INTERVENTION
        else:
            m.num_process[process_tech, g, tm, s].fixed = True
            return 0
    # catch CEMENT
    elif m.GRIDTYPECODE[g] == 11:
        if process_tech in m.CEMENT_INTERVENTIONS:
            return INIT_INTERVENTION
        else:
            m.num_process[process_tech, g, tm, s].fixed = True
            return 0
    # catch REFINERY
    elif m.GRIDTYPECODE[g] == 12:
        if process_tech in m.REFINERY_INTERVENTIONS:
            return INIT_INTERVENTION
        else:
            m.num_process[process_tech, g, tm, s].fixed = True
            return 0
    # catch STEEL BF-BOF
    elif m.GRIDTYPECODE[g] == 13:
        if process_tech in m.STEELBFBOF_INTERVENTIONS:
            return INIT_INTERVENTION
        else:
            m.num_process[process_tech, g, tm, s].fixed = True
            return 0
    # catch TERMINAL
    elif m.GRIDTYPECODE[g] == 30:
        if process_tech in m.TERMINAL_INTERVENTIONS:
            return INIT_INTERVENTION
        else:
            m.num_process[process_tech, g, tm, s].fixed = True
            return 0
    # catch STORAGE
    elif m.GRIDTYPECODE[g] == 20:
        # no process technology at storage site
        m.num_process[process_tech, g, tm, s].fixed = True
        return 0

    # catch TRUNKLINE
    elif m.GRIDTYPECODE[g] == 40:
        # no process technology at trunkline site
        m.num_process[process_tech, g, tm, s].fixed = True
        return 0


def init_num_processinvest(m, process_tech, g, tm, s):
    """Constrains the number of new process technologies."""
    # base initialisation on the function: init_num_process()
    init_fixed = m.num_process[process_tech, g, tm, s].fixed
    zero_val = m.num_process[process_tech, g, tm, s].value == 0
    if zero_val & init_fixed:
        m.num_process_invest[process_tech, g, tm, s].fixed = True
        return 0
    else:
        return INIT_INTERVENTION


def init_num_pipe(m, g0, g1, d, tm, s):
    """Constrains the number of pipe units."""
    # ---- 1st Level: LIMIT based on spatial constraints
    # identical start and end point or exceeds distance limit
    if (m.DISTANCE[g0, g1] == 0) | (m.DISTANCE[g0, g1] > MAX_DIST):
        m.num_pipes[g0, g1, d, tm, s].fixed = True
        return 0
    else:
        return int(MAX_DIST_TECH_PER_CELL/2)


def init_num_pipeCO2(m, g0, g1, d, tm, s):
    """Constrains the number of distribution technologies."""
    # ---- 1st Level: LIMIT based on spatial constraints
    # identical start and end point or exceeds distance limit
    if (m.DISTANCE[g0, g1] == 0) | (m.DISTANCE[g0, g1] > MAX_DIST):
        m.num_pipes[g0, g1, d, tm, s].fixed = True
        return 0

    # ---- 2nd Level: initialise non-CO2 pipes
    # <add more sophisticated rules here>
    # no other pipes but CO2 pipes
    if d not in m.PIPES_CO2:
        m.num_pipes[g0, g1, d, tm, s].fixed = True
        return 0
        #return MAX_DIST_TECH_PER_CELL / 2
    
    # ---- 3rd Level: ENABLE CO2 pipes based on grid point types
    # identify type of start point
    if m.LANDFALL[g0] == 1:
        start = 'LANDFALL'
    elif m.HARBOUR[g0] == 1:
        start = 'HARBOUR'
    elif m.ONSHORE_GRIDS[g0] == 1:
        start = 'INLAND'
    else:
        start = 'OFFSHORE'

    # from landfall to offshore
    if (start == 'LANDFALL') & (m.ONSHORE_GRIDS[g1] == 0):
        # only offshore connections possible
        if d in m.PIPES_OFFSHORE:
            return MAX_DIST_TECH_PER_CELL / 2
        else:
            m.num_pipes[g0, g1, d, tm, s].fixed = True
            return 0
    # from inland onshore (no landfall or harbour) to any other onshore
    elif (start == 'INLAND') & (m.ONSHORE_GRIDS[g1] == 1):
        # only onshore connections possible
        if d in m.PIPES_ONSHORE:
            return MAX_DIST_TECH_PER_CELL / 2
        else:
            m.num_pipes[g0, g1, d, tm, s].fixed = True
            return 0
    # <add constraints on pipes for harbour as starting points here>
    # elif (start == 'HARBOUR') & (<condition on end point>):
    #     if <condition for pipe>
    #         return None
    #     else:
    #         m.num_pipes[g0, g1, d, tm, s].fixed = True
    #         return 0
    # no other connections are possible
    else:
        m.num_pipes[g0, g1, d, tm, s].fixed = True
        return 0


def init_num_pipeinvest(m, g0, g1, d, tm, s):
    """Constrains the number of pipe units for new investment."""
    # base initialisation on: init_num_pipe() or init_num_pipeCO2()
    init_fixed = m.num_pipes[g0, g1, d, tm, s].fixed
    zero_val = m.num_pipes[g0, g1, d, tm, s].value == 0
    if zero_val & init_fixed:
        m.num_pipes_invest[g0, g1, d, tm, s].fixed = True
        return 0
    else:
        return m.INITIAL_PIPES[g0, g1, d, tm]

def init_retrieval_rate(m, r, g, strg_tech, t, tm, s):
    """Defines constraints on the retrieval rate variable."""
    # catch stored CO2: cannot be retrieved
    if r in m.STORABLE_CO2:
        m.retrieval_rate[r, g, strg_tech, t, tm, s].fixed = True
        return 0
    # <add retrievable resources here>
    # non-storable resources cannot be retrieved
    elif r not in m.STORAGE_R:
        m.retrieval_rate[r, g, strg_tech, t, tm, s].fixed = True
        return 0
    else:
        return BIG_M / 1e5


def init_storage_rate(m, r, g, strg_tech, t, tm, s):
    """Defines constraints on the storage rate variable."""
    # catch CO2 storage
    if (r in m.STORABLE_CO2):
        # can only store CO2 with CO2 storage tech
        if (strg_tech in m.CO2_STORAGE_TECH):
            return BIG_M / 1e5
        else:
            m.storage_rate[r, g, strg_tech, t, tm, s].fixed = True
            return 0
    # <add other storable resources here>
    # No storage units if resource not storable or no tech available
    else:
        m.storage_rate[r, g, strg_tech, t, tm, s].fixed = True
        return 0


def init_emission_rate(m, r, g, t, tm, s):
    """Defines constraints for the emission rate variable. """
    # catch emissions which are pollutants
    if r in m.R_POLLUTANT:
        return 0
    # all other resources have to be balanced
    else :
        m.emission_rate[r, g, t, tm, s].fixed = True
        return 0
        

def init_flow_rate(m, g0, g1, d, dist_mode, t, tm, s):
    """Initialises flow variable constraints"""
    # identical start and end point or exceeds distance limit
    if (m.DISTANCE[g0, g1] == 0) | (m.DISTANCE[g0, g1] > MAX_DIST):
        m.flow_rate[g0, g1, d, dist_mode, t, tm, s].fixed = True
        return 0
    else:
        return BIG_M / 1e5


def init_import_rate(m, r, g, t, tm, s):
    """Defines import rate constraints for importable resources."""
    # catch importable resources at import locations
    if (r in m.IMP_R) & (m.IMPORT_LOCATIONS[g] == 1):
        return 0
    # no import for all other resource-location pairs
    else:
        m.import_rate[r, g, t, tm, s].fixed = True
        return 0

def init_transport_rate(m, r, g, t, tm, s):
    """Defines transport rate constraints for transportable resources."""
    # catch importable resources at import locations
    if (r in m.TRAN_R) & (m.IMPORT_LOCATIONS[g] == 1):
        return 0
    # no import for all other resource-location pairs
    else:
        m.transport_rate[r, g, t, tm, s].fixed = True
        return 0

def init_transport_emissions(m, r, g, t, tm, s):
    """Defines transport emissions constraints for transportable resources."""
    # catch importable resources at import locations
    if (r in m.TRAN_R) & (m.IMPORT_LOCATIONS[g] == 1):
        return 0
    # no import for all other resource-location pairs
    else:
        m.transport_emissions[r, g, t, tm, s].fixed = True
        return 0


def backcasting(m, ref, tol=1e-5):
    # fix all investments to zero for for unselected solutions
    for key in ref.num_process:
        val = ref.num_process[key].value
        if (val <= tol) & (key[0] != 'NO_ACTION'):
            m.num_process[key].fixed = True
            m.num_process[key] = 0
    # 
    for key in ref.num_process_invest:
        val = ref.num_process_invest[key].value
        if (val <= tol) & (key[0] != 'NO_ACTION'):
            # change this here, if you want to have sequential interventions
            m.num_process_invest[key].fixed = True
            m.num_process_invest[key] = 0
    # 
    for key in ref.num_end_use:
        val = ref.num_end_use[key].value
        if (val <= tol) & (key[0] != 'NO_ACTION'):
            m.num_end_use[key].fixed = True
            m.num_end_use[key] = 0
    # 
    for key in ref.num_end_use_invest:
        val = ref.num_end_use_invest[key].value
        if (val <= tol) & (key[0] != 'NO_ACTION'):
            m.num_end_use_invest[key].fixed = True
            m.num_end_use_invest[key] = 0
    # 
    for key in ref.num_strg:
        val = ref.num_strg[key].value
        if (val <= tol):
            m.num_strg[key].fixed = True
            m.num_strg[key] = 0
    # 
    for key in ref.num_strg_invest:
        val = ref.num_strg_invest[key].value
        if (val <= tol):
            m.num_strg_invest[key].fixed = True
            m.num_strg_invest[key] = 0
    # 
    for key in ref.num_pipes:
        val = ref.num_pipes[key].value
        if (val <= tol):
            m.num_pipes[key].fixed = True
            m.num_pipes[key] = 0
    # 
    for key in ref.num_pipes_invest:
        val = ref.num_pipes_invest[key].value
        if (val <= tol):
            m.num_pipes_invest[key].fixed = True
            m.num_pipes_invest[key] = 0
    
    return m
