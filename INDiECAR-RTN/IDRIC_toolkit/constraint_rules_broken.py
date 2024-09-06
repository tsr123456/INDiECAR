from __future__ import division
import pyomo.environ as pyo

# USER SETTINGS -------------------------------------------------------------
# TODO: load/parse user setting from case input files
name_for_emitted_CO2 = 'EMITTED_CO2'
name_for_stored_offshore_CO2 = 'CLIQ_CO2_OFFSHORE'
name_for_stored_onshore_CO2 = 'CLIQ_CO2_ONSHORE'
negative_emission_tech = 'NET'

MAX_DIST = 999
TON_TO_GRAM = 1000000
MEGATON_TO_TON = 1000000
MINIMUM_ASSET_AVAILABILITY = 0.7
INIT_CARBON_INTENSITY = 200 # Units: g/kWh
HHOUR_TO_SECONDS = 1800
HHOURS_IN_A_YEAR = 17520
CRF = 0.118740
MAX_PROCESS_TECH_PER_CELL = 1
MAX_DIST_TECH_PER_CELL = 10
MAX_STRG_TECH_PER_CELL = 10
#MAX_END_USE_TECH_PER_CELL = 100


# 1) UNIT BALANCES ----------------------------------------------------------
#    equation type:  value assignment
#    variable types: NonNegativeIntegers (or Binary), i.e., units
#    applied to:     process, distritibution, and storage technologies


def eqnJ1_process(m, process_tech, g, tm, s):
    """Process technology unit balance in each grid cell."""
    # github repo name: eqn2_rule
    # identify existing units at tm
    if tm > 1:
        existing = m.num_process[process_tech, g, tm-1, s]
    else:
        existing = m.EXSTNG_TECH[process_tech, g, tm]
    # total number of units from existing and newly installed
    total = existing + m.num_process_invest[process_tech, g, tm, s]
    return m.num_process[process_tech, g, tm, s] == total


def eqnJ1_enduse(m, enduse_tech, g, tm, s):
    """End-use technology unit balance in each grid cell."""
    # github repo name: *new*
    # identify existing units at tm
    if tm > 1:
        existing = m.num_end_use[enduse_tech, g, tm-1, s]
    else:
        # there is no initialisation of END USE technology
        existing = 0
    # total number of units from existing and newly installed
    total = existing + m.num_end_use_invest[enduse_tech, g, tm, s]
    return m.num_end_use[enduse_tech, g, tm, s] == total


def eqnD1_pipes(m, g0, g1, d, tm, s):
    """Distribution units balance in each grid cell."""
    # github repo name: eqn9_rule
    # identify existing units at tm
    if tm > 1 :
        existing = m.num_pipes[g0, g1, d, tm-1, s]
    else:
        existing = m.EXSTNG_PIPES[g0, g1, d, tm]
    # total number of units from existing and newly installed
    total = existing + m.num_pipes_invest[g0, g1, d, tm, s]
    return m.num_pipes[g0, g1, d, tm, s] == total


def eqnS1(m, r, strg_tech, g, tm, s):
    """Storage technology unit balance in each grid cell."""
    # github repo name: eqn6_rule
    # identify existing units at tm
    if tm > 1:
        existing = m.num_strg[r, strg_tech, g, tm-1, s]
    else:
        existing = m.EXSTNG_STRG[r, strg_tech, g, tm]
    # total number of units from existing and newly installed
    total = existing + m.num_strg_invest[r, strg_tech, g, tm, s]
    return m.num_strg[r, strg_tech, g, tm, s] == total


# 2) RATE BALANCES ----------------------------------------------------------
#    equation type:  value assignment
#    variable types: NonNegativeReals, i.e., flow_rate
#    applied to:     process, distritibution, and storage technologies


def eqnS2(m, r, g, strg_tech, t, tm, s):
    """ Storage inventory/resource balance"""
    # github repo name: eqn15_rule
    # identify existing units at tm and t
    if t == 1 and tm == 1:
        existing = m.EXSTNG_STRG[r, strg_tech, g, tm]
    elif t == 1 and tm >= 1:
        existing = m.inventory_rsrc[r, g, strg_tech, m.T[-1] , tm-1, s] 
    else:
        existing = m.inventory_rsrc[r, g, strg_tech, t-1, tm, s]
    # identify change in resources at tm and t
    rate_add = m.storage_rate[r, g, strg_tech, t, tm, s]
    rate_sub = m.retrieval_rate[r, g, strg_tech, t, tm, s]
    change = m.OPER_TIME_INTERVAL[t] * (rate_add - rate_sub)
    return m.inventory_rsrc[r, g, strg_tech, t, tm, s] == existing + change


def eqnR2_CellBalance(m, r, g, t, tm, s):
    """Resource balance for each grid cell at every time instance."""
    # github repo name: eqn4_rule
    # aggregate (stack) changes of each resource in grid cell
    # initialisation and chage due to import and demand (use)
    stack = m.EXSTNG_RSRCrate[r, g, t, tm]
    stack -= m.DEMAND[r, g, t, tm, s]
    stack += m.import_rate[r, g, t, tm, s]
    stack += m.transport_rate[r,g,t,tm,s]
    # change due to storage
    if r in m.STORAGE_R:
        for st in m.STRG_TECH:
            stack += m.retrieval_rate[r, g, st, t, tm, s]
            stack -= m.storage_rate[r, g, st, t, tm, s]
    # change due to industrial process technology (integer)
    for pt in m.PROCESS_TECH:
        conv = m.RESOURCE_CONV_RATE[pt, r]
        # catch negative emission technology
        if (r in m.R_POLLUTANT) & (conv < 0):
            # do not account for the reduction by NETs, their need is 
            # determined based on reduction targets (eqn_CO2Reduction)
            conv = 0
        stack += conv * m.prod_rate[pt, g, t, tm, s]
    # change due to (domestic) end-use technology (real)
    for et in m.END_USE_TECH:
        conv = m.RESOURCE_CONV_RATE[et, r]
        # catch negative emission technology
        if (r in m.R_POLLUTANT) & (conv < 0):
            # do not account for the reduction by NETs, their need is 
            # determined based on reduction targets (eqn_CO2Reduction)
            conv = 0
        stack += conv * m.prod_rate[et, g, t, tm, s]
    # change due to inflows and outflows from distribution network
    for d in m.D:
        for dm in m.DIST_MODE:
            for g1 in m.G:
                # TODO: correct flows by building difference with production
                # and consumption coeffitients.
                flow_out = m.flow_rate[g, g1, d, dm, t, tm, s]
                flow_in = m.flow_rate[g1, g, d, dm, t, tm, s]
                coeff = m.FLOW_PRODUCTION_COEFF[d, dm, r] 
                stack += coeff * (flow_in - flow_out)
    # the difference in resource is emitted
    return m.emission_rate[r, g, t, tm, s] == stack


def eqnR2_NetBalanceCO2(m, tm, s):
    """Net CO2 constraint based on desired CO2 removal fraction."""
    # github repo name: eqn8_rule
    # determine initial CO2 emissions
    t0_emissions = 0
    for g in m.G:
        t0_emissions += m.EMISSIONS_GRIDDED_t0[g, s]
    # determine net emissions
    net_emission = sum(sum(m.OPER_TIME_INTERVAL[t] * m.AVAILABILITY[g] * ( \
        m.emission_rate[name_for_emitted_CO2, g, t, tm, s] \
        - m.prod_rate[negative_emission_tech, g, t, tm, s]) \
        for g in m.G) for t in m.T)
    # define emission target
    target_emission = (1 - m.CO2_REMOVAL_FRACTION[tm]) * t0_emissions
    return net_emission <= target_emission


#def eqnR2_Net_company_BalanceCO2(m, tm, s): ADD this here ?
    

def eqnR2_CellBalanceCO2(m, g, tm, s):
    """Cell-based CO2 constraint based on desired CO2 removal fraction."""
    # github repo name: eqn8_rule
    # determine initial CO2 emissions
    t0_emissions = m.EMISSIONS_GRIDDED_t0[g, s]
    # determine net emissions
    net_emission = sum(m.OPER_TIME_INTERVAL[t] * m.AVAILABILITY[g] * ( \
        m.emission_rate[name_for_emitted_CO2, g, t, tm, s] \
        - m.prod_rate[negative_emission_tech, g, t, tm, s]) \
        for t in m.T)
    # define emission target
    target_emission = (1 - m.CO2_REMOVAL_FRACTION[tm]) * t0_emissions
    return net_emission <= target_emission


def eqnR2_CCS(m, r, g, t, tm, s):
    """ Resource/Material balance constraint for each grid cell."""
    # github repo name: eqn4_rule
    # aggregate (stack) changes of each resource in grid cell
    # initialisation and chage due to import and demand (use)
    stack = m.EXSTNG_RSRCrate[r, g, t, tm]
    stack += m.import_rate[r, g, t, tm, s]
    stack += m.transport_rate[r,g, t, tm, s]
    # change due to storage
    for st in m.STRG_TECH:
        stack += m.retrieval_rate[r, g, st, t, tm, s]
        stack -= m.storage_rate[r, g, st, t, tm, s]
    # change due to process and end use technology (industry and domestic)
    for pt in m.PROCESS_TECH:
        stack += m.RESOURCE_CONV_RATE[pt, r] * m.prod_rate[pt, g, t, tm, s]
    # change due to inflows and outflows from distribution network
    for d in m.D:
        for dm in m.DIST_MODE:
            for g1 in m.G:
                flow_out = m.flow_rate[g, g1, d, dm, t, tm, s]
                flow_in = m.flow_rate[g1, g, d, dm, t, tm, s]
                coeff = m.FLOW_PRODUCTION_COEFF[d, dm, r] 
                stack += coeff * (flow_in - flow_out)
    # the difference in resource is emitted
    return m.emission_rate[r, g, t, tm, s] == stack


# 3) link UNIT-RATE CONSTRAINTS ---------------------------------------------
#    equation type:  inequality, limitations by maximum rate
#    variable types: NonNegativeReals, i.e., rates
#    applied to:     injection, retrieval, and flows


def eqnS3_inj(m, storage_r, g, strg_tech, t, tm, s):
    """ General injection rate constraint."""
    # github repo name: eqn13_rule (and eqn16a_rule for CO2 w/ mistake)
    # existing storage rate
    rate = m.storage_rate[storage_r, g, strg_tech, t, tm, s]
    # maximum storage rate and storage units
    N = m.num_strg[storage_r, strg_tech, g, tm, s]
    max_rate = m.MAX_INJECTION_RATE[strg_tech]
    return rate <= N * max_rate


def eqnS3_injCO2(m, g, co2_storage_tech, t, tm, s):
    """ Injection rate limiting constraint for CO2"""
    # github repo name: eqn16b_rule
    # TODO: could this be included in initialisation?
    # onshore CO2 cannot be stored offshore and vice-versa
    # identify the name for the NOT stored CO2 resource
    if m.ONSHORE_GRIDS[g] == 0:
        name_CO2 = name_for_stored_onshore_CO2
    else:
        name_CO2 = name_for_stored_offshore_CO2
    return m.storage_rate[name_CO2, g, co2_storage_tech, t, tm, s] == 0


def eqnS3_ret(m, storage_r, g, strg_tech, t, tm, s):
    """ General retrieval rate constraint."""
    # github repo name: eqn14_rule
    # existing retrieval rate
    rate = m.retrieval_rate[storage_r, g, strg_tech, t, tm, s]
    # maximum retrieval rate and storage units
    N = m.num_strg[storage_r, strg_tech, g, tm, s]
    max_rate = m.MAX_RETRIEVAL_RATE[strg_tech]
    return rate <= N * max_rate


def eqnD3(m, g0, g1, d, t, tm, s):
    """Flow rate constraint for distribution technologies."""
    # github repo name: eqn5_rule
    # sum up all flow rates between the two grid points
    rate = 0
    for dist_mode in m.DIST_MODE:
        rate += m.flow_rate[g0, g1, d, dist_mode, t, tm, s]
    # pipes and maximum possible flow rate
    N = m.num_pipes[g0, g1, d, tm, s]
    max_rate = m.FLOW_RSRC_MAX[d]
    return rate <= N * max_rate


def eqnJ3_process(m, process_tech, g, t, tm, s):
    """Production capacity constraint for process tech in each cell."""
    # github repo name: eqn3_rule
    # existing production rate
    rate = m.prod_rate[process_tech, g, t, tm, s]
    # maximum production rate and process units
    N = m.num_process[process_tech, g, tm, s]
    max_rate = m.NAME_PLATE_CAP[process_tech]
    max_rate *= m.TECH_AVAILABILITY[process_tech, tm]
    return rate <= N * max_rate


def eqnJ3_enduse(m, end_use_tech, g, t, tm, s):
    """Production capacity constraint for end use tech in each cell."""
    # github repo name: eqn3b_rule
    # existing production rate
    rate = m.prod_rate[end_use_tech, g, t, tm, s]
    # maximum production rate and process units
    N = m.num_end_use[end_use_tech, g, tm, s]
    max_rate = m.NAME_PLATE_CAP[end_use_tech]
    max_rate *= m.TECH_AVAILABILITY[end_use_tech, tm]
    return rate <= N * max_rate


# 4) MAXIMUM CAPACITY CONSTRAINTS -------------------------------------------
#    equation type:  inequality, limitations by capacity
#    variable types: NonNegativeReals, i.e., capacity
#    applied to:     production and end use processes, storage volume


def eqnS4_CO2(m, g, co2_storage_tech, t, tm, s):
    """CO2 storage capacity constraint based on available geological volume."""
    # github repo name: eqn12a_rule
    # identify the name for the stored CO2
    if m.ONSHORE_GRIDS[g] == 0:
        name_CO2 = name_for_stored_offshore_CO2
    else:
        name_CO2 = name_for_stored_onshore_CO2
    # compute the available capacity and use it to limit the inventory
    cap = MEGATON_TO_TON * m.TOT_CO2_STORES[g]
    return (0, m.inventory_rsrc[name_CO2, g, co2_storage_tech, t, tm, s], cap)


def eqnS4_rest(m, r, g, strg_tech, t, tm, s):
    """ Storage inventory capacity constraint."""
    # github repo name: eqn8_rule
    # this function covers the inventory missed by eqnS4_CO2 function
    # resource has to be storable
    if r not in m.STORAGE_R:
        return pyo.Constraint.NoConstraint

    # not covered by eqnS4_CO2: not CO2 & tech not a CO2 tech
    if (r not in m.STORABLE_CO2) & (strg_tech not in m.CO2_STORAGE_TECH):
        N = m.num_strg[r, strg_tech, g, tm, s]
        cap_N = m.NAME_PLATE_CAP[strg_tech]
        cap = N * cap_N
        return (0, m.inventory_rsrc[r, g, strg_tech, t, tm, s], cap)
    else:
        return pyo.Constraint.NoConstraint


# D) DISTRIBUTION: additional PIPELINE UNIT CONSTRAINTS ---------------------
#    equation type:  inequality, limitations of number
#    variable types: NonNegativeIntegers, i.e., units
#    applied to:     pipelines

# D5) only unidirectional flows
#     constraints by resource

def eqnD5_CO2(m, g0, g1, tm, s):
    """Only allow one pipe to transport CO2 between two grid points."""
    # github repo name: *new*
    n_pipes = 0
    # sum of all pipes between g0 and g1 transporting CO2
    for pipe in m.PIPES_CO2:
        n_pipes += m.num_pipes_invest[g0, g1, pipe, tm, s]
        n_pipes += m.num_pipes_invest[g1, g0, pipe, tm, s]
    return (0, n_pipes, 1)


def eqnD5_NATGAS(m, g0, g1, tm, s):
    """Only allow one pipe to transport natural gas between two grid points"""
    # github repo name: *new*
    n_pipes = 0
    # sum of all pipes between g0 and g1 transporting natural gas
    for pipe in m.PIPES_NATGAS:
        n_pipes += m.num_pipes_invest[g0, g1, pipe, tm, s]
        n_pipes += m.num_pipes_invest[g1, g0, pipe, tm, s]
    return (0, n_pipes, 1)


# D6) lean network w/o branching (i.e., no downstream splitting)
#     constraints by resource

def eqnD6_CO2(m, g0, tm, s):
    """Only allow one outflowing pipe for CO2 for each grid point"""
    # github repo name: *new*
    n_pipes = 0
    # sum of all CO2 pipes leaving point p1
    for pipe in m.PIPES_CO2:
        n_pipes += sum(m.num_pipes_invest[g0, g1, pipe, tm, s] for g1 in m.G)
    return (0, n_pipes, 1)


# J)

def eqnJ5_NoAction(m, process_tech, g, tm, s):
    """Process technology unit balance in each grid cell."""
    # github repo name: *new*
    if process_tech == 'NO_ACTION':
        return pyo.Constraint.NoConstraint
    # only allow intervention or NO_ACTION per grid cell
    N = m.num_process_invest[process_tech, g, tm, s]
    return (0, N + m.num_process_invest['NO_ACTION', g, tm, s], 1)

def eqnJ6_max_num_process(m, g, tm, s):
    """Process technology unit balance in each grid cell."""
    # github repo name: *new*
    N = 0
    for pt in m.PROCESS_TECH:
        N += m.num_process_invest[pt, g, tm, s]
    return (0, N, MAX_PROCESS_TECH_PER_CELL )



# M) METRIC CONSTRAINTS -----------------------------------------------------
#    equation type:  value assignment
#    variable types: NonNegativeReals
#    applied to:     all installations

def eqnM_CAPEX(m, tm, s):
    """Aggregate total CAPEX within system."""
    # github repo name: eqn7a_rule
    capex = 0
    # add processes technology investment
    for pt, g, tm, s in m.num_process_invest:
    
    	#Old IDRIC function:
        #N = m.num_process_invest[pt, g, tm, s]
        #capex += m.INV_COEFF_GRID[pt, g, 'CAPEX', tm] * N 
        
        #New function
        rate = m.prod_rate[pt, g, 1, tm, s]
        if m.NAME_PLATE_CAP[pt] > 0:
            capex+= m.INV_COEFF_GRID[pt,g, 'CAPEX', tm]/m.NAME_PLATE_CAP[pt]*rate
        elif m.NAME_PLATE_CAP[pt] == 0:
            N = m.num_process_invest[pt, g, tm, s]
            capex += m.INV_COEFF_GRID[pt, g, 'CAPEX', tm] * N 


    # add end-use technology investment
    for et, g, tm, s in m.num_end_use_invest:
        N = m.num_end_use_invest[et, g, tm, s]
        capex += m.INV_COEFF_GRID[et, g, 'CAPEX', tm] * N
    # add storage technology investment
    for r, st, g, tm, s in m.num_strg_invest:
        N = m.num_strg_invest[r, st, g, tm, s]
        capex += m.INV_COEFF_GRID[st, g, 'CAPEX', tm] * N
    # add pipe investment
    for g0, g1, d, tm, s in m.num_pipes_invest:
        N = m.num_pipes_invest[g0, g1, d, tm, s]
        dist = m.DISTANCE[g0, g1]
        capex += m.NETWORK_COEFF[d, 'CAPEX'] * dist * N
    # add production rate investments
    for tech, g, t, tm, s in m.prod_rate:
        time = m.OPER_TIME_INTERVAL[t]
        rate = m.prod_rate[tech, g, t, tm, s]
        capex += m.PROCESS_COEFF[tech, 'CAPEX', tm] * rate * time
    # add flow rate investments
    for g0, g1, d, dm, t, tm, s in m.flow_rate:
        time = m.OPER_TIME_INTERVAL[t]
        rate = m.flow_rate[g0, g1, d, dm, t, tm, s]
        capex += m.FLOW_COEFF[d, 'CAPEX'] * rate * time
    # add import rate investments
    for r, g, t, tm, s in m.import_rate:
        time = m.OPER_TIME_INTERVAL[t]
        rate = m.import_rate[r, g, t, tm, s]
        if r in m.IMP_R:
            capex += m.IMPORT_COEFF[r, 'CAPEX'] * rate * time
    # add storage reservoir investments
    for r, g, st, t, tm, s in m.inventory_rsrc:
        level = m.inventory_rsrc[r, g, st, t, tm, s]
        capex += m.STRG_COEFF[st, 'CAPEX'] * level
    return m.total_metrics['CAPEX', tm, s] == capex


def eqnM_CAPEX_CCS(m, tm, s):
    """Aggregate total CAPEX within system."""
    # github repo name: eqn7a_rule
    capex = 0
    # add processes technology investment
    for pt, g, tm, s in m.num_process_invest:
        N = m.num_process_invest[pt, g, tm, s]
        capex += m.INV_COEFF_GRID[pt, g, 'CAPEX', tm] * N
    # add storage technology investment
    for r, st, g, tm, s in m.num_strg_invest:
        N = m.num_strg_invest[r, st, g, tm, s]
        capex += m.INV_COEFF_GRID[st, g, 'CAPEX', tm] * N
    # add pipe investment
    for g0, g1, d, tm, s in m.num_pipes_invest:
        N = m.num_pipes_invest[g0, g1, d, tm, s]
        dist = m.DISTANCE[g0, g1]
        capex += m.NETWORK_COEFF[d, 'CAPEX'] * dist * N
    # add production rate investments
    for tech, g, t, tm, s in m.prod_rate:
        time = m.OPER_TIME_INTERVAL[t]
        rate = m.prod_rate[tech, g, t, tm, s]
        capex += m.PROCESS_COEFF[tech, 'CAPEX', tm] * rate * time
    # add flow rate investments
    for g0, g1, d, dm, t, tm, s in m.flow_rate:
        time = m.OPER_TIME_INTERVAL[t]
        rate = m.flow_rate[g0, g1, d, dm, t, tm, s]
        capex += m.FLOW_COEFF[d, 'CAPEX'] * rate * time
    # add import rate investments
    for r, g, t, tm, s in m.import_rate:
        time = m.OPER_TIME_INTERVAL[t]
        rate = m.import_rate[r, g, t, tm, s]
        if r in m.IMP_R:
            capex += m.IMPORT_COEFF[r, 'CAPEX'] * rate * time
    # add storage reservoir investments
    for r, g, st, t, tm, s in m.inventory_rsrc:
        level = m.inventory_rsrc[r, g, st, t, tm, s]
        capex += m.STRG_COEFF[st, 'CAPEX'] * level
    return m.total_metrics['CAPEX', tm, s] == capex


def eqnM_OPEX(m, tm, s):
    """Aggregate total OPEX within system."""
    # github repo name: eqn7b_rule
    opex = 0
    # add processes technology operation
    for pt, g, tm, s in m.num_process:
        N = m.num_process[pt, g, tm, s]
        #if pt == 'CCS_CEMENT':
        #    opex += m.INV_COEFF_GRID[pt, g, 'OPEX', tm] * N  + m.OPEX_COEFF_GRID[g]
        #else:
        opex += m.INV_COEFF_GRID[pt, g, 'OPEX', tm] * N 

    # add end-use technology operation
    for et, g, tm, s in m.num_end_use:
        N = m.num_end_use[et, g, tm, s]
        opex += m.INV_COEFF_GRID[et, g, 'OPEX', tm] * N
    # add storage technology operation
    for r, st, g, tm, s in m.num_strg:
        N = m.num_strg[r, st, g, tm, s]
        opex += m.INV_COEFF_GRID[st, g, 'OPEX', tm] * N
    # add pipe operation
    for g0, g1, d, tm, s in m.num_pipes:
        N = m.num_pipes[g0, g1, d, tm, s]
        dist = m.DISTANCE[g0, g1]
        opex += m.NETWORK_COEFF[d, 'OPEX'] * dist * N
    # add production rate operation 
    for tech, g, t, tm, s in m.prod_rate:
        time = m.OPER_TIME_INTERVAL[t]
        rate = m.prod_rate[tech, g, t, tm, s]
        flag = m.AVAILABILITY[g]
        transport = 0
        if tech in m.POSTCOMB:
            flag *= m.LOCATION_FACTOR[g]
        #if tech == 'CCS_MINERAL_CEMENT':
        #    transport = m.OPEX_TRANS_MINERAL[g]
        #elif tech == 'BIOMASS_CEMENT':
        #    tranpsort = m.OPEX_TRANS_BIOMASS[g]
        #elif  tech == 'CCS_BIOMASS_CEMENT':
        #    transport = m.OPEX_TRANS_BIOMASS[g]
        opex += m.PROCESS_COEFF[tech, 'OPEX', tm] * rate * time * flag + transport*rate #Addd OPEX_factor here: (m.PROCESS_COEFF[tech, 'OPEX', tm]+m.OPEX_COEFF_GRID[g]) * rate * time * flag
    # add flow rate operation
    for g0, g1, d, dm, t, tm, s in m.flow_rate:
        time = m.OPER_TIME_INTERVAL[t]
        rate = m.flow_rate[g0, g1, d, dm, t, tm, s]
        flag = m.AVAILABILITY[g]
        opex += m.FLOW_COEFF[d, 'OPEX'] * rate * time * flag
    # add import rate operation
    for r, g, t, tm, s in m.import_rate:
        time = m.OPER_TIME_INTERVAL[t]
        rate = m.import_rate[r, g, t, tm, s]
        flag = m.AVAILABILITY[g]
        if r in m.IMP_R:
            opex += m.IMPORT_COEFF[r, 'OPEX'] * rate * time * flag
    
    # add transport rate operation
    for r, g, t, tm, s in m.transport_rate:
        time = m.OPER_TIME_INTERVAL[t]
        rate = m.transport_rate[r, g, t, tm, s]
        if r in m.TRAN_R:
            opex += m.TRANSPORT_COEFF[r,g] * rate * time 
   
    # add storage reservoir operation
    for r, g, st, t, tm, s in m.inventory_rsrc:
        level = m.inventory_rsrc[r, g, st, t, tm, s]
        opex += m.STRG_COEFF[st, 'OPEX'] * level
    return m.total_metrics['OPEX', tm, s] == opex


def eqnM_OPEX_CCS(m, tm, s):
    """Aggregate total OPEX within system."""
    # github repo name: eqn7b_rule
    opex = 0
    # add processes technology operation
    for pt, g, tm, s in m.num_process:
        N = m.num_process[pt, g, tm, s]
        opex += m.INV_COEFF_GRID[pt, g, 'OPEX', tm] * N
    # add storage technology operation
    for r, st, g, tm, s in m.num_strg:
        N = m.num_strg[r, st, g, tm, s]
        opex += m.INV_COEFF_GRID[st, g, 'OPEX', tm] * N
    # add pipe operation
    for g0, g1, d, tm, s in m.num_pipes:
        N = m.num_pipes[g0, g1, d, tm, s]
        dist = m.DISTANCE[g0, g1]
        opex += m.NETWORK_COEFF[d, 'OPEX'] * dist * N
    # add production rate operation 
    for tech, g, t, tm, s in m.prod_rate:
        time = m.OPER_TIME_INTERVAL[t]
        rate = m.prod_rate[tech, g, t, tm, s]
        flag = m.AVAILABILITY[g]
        if tech in m.POSTCOMB:
            flag *= m.LOCATION_FACTOR[g]
        opex += m.PROCESS_COEFF[tech, 'OPEX', tm] * rate * time * flag
    # add flow rate operation
    for g0, g1, d, dm, t, tm, s in m.flow_rate:
        time = m.OPER_TIME_INTERVAL[t]
        rate = m.flow_rate[g0, g1, d, dm, t, tm, s]
        flag = m.AVAILABILITY[g]
        opex += m.FLOW_COEFF[d, 'OPEX'] * rate * time * flag
    # add import rate operation
    for r, g, t, tm, s in m.import_rate:
        time = m.OPER_TIME_INTERVAL[t]
        rate = m.import_rate[r, g, t, tm, s]
        flag = m.AVAILABILITY[g]
        if r in m.IMP_R:
            opex += m.IMPORT_COEFF[r, 'OPEX'] * rate * time * flag
    # add storage reservoir operation
    for r, g, st, t, tm, s in m.inventory_rsrc:
        level = m.inventory_rsrc[r, g, st, t, tm, s]
        opex += m.STRG_COEFF[st, 'OPEX'] * level
    return m.total_metrics['OPEX', tm, s] == opex


# O) OBJECTIVE functions ----------------------------------------------------

def eqnO_TotLevCost(m):
    """Computes the total levelised cost of system across all scenarios."""
    # github repo name: obj_rule
    LC = 0
    p_tot = 0
    # sum up scenarios, i.e., weighted (probability) outcomes
    for s in m.S:
        p = m.PROBABILITY[s]
        p_tot += p
        # sum up all investment rounds
        for tm in m.TM:
            # CAPEX specs
            wt_cpx = m.OBJ_WEIGHT['CAPEX', tm]
            cpx = m.total_metrics['CAPEX', tm, s]
            # OPEX specs
            wt_opx = m.OBJ_WEIGHT['OPEX', tm]
            opx = m.total_metrics['OPEX', tm, s]
            LC += p * (wt_cpx * cpx * CRF + wt_opx * opx)
            # TODO: check, there seems to be a time value missing in the objective 
            # function, i.e., no difference for different tm?
    return LC / p_tot


# ----------------------------------------------------------------------------
# TODO: integrate below functions when incorporating Hydrogen of LCA


#def eqn7c_rule(m,lca_metrics,tm,s):
#   """ Total metrics calculaton - LCA metrics."""
#   return m.total_metrics[lca_metrics,tm,s] == \
#      sum(sum(sum(m.LCA_SCORE[j,lca_metrics]*( \
#       m.prod_rate[j,g,t,tm,s]*m.OPER_TIME_INTERVAL[t]*m.AVAILABILITY[g]) \
#          for j in m.J) for g in m.G) for t in m.T) \
#          + sum(sum(sum (m.NETWORK_LCA[d,lca_metrics]*m.DISTANCE[g,g1]*m.num_pipes[g,g1,d,tm,s] \
#          for d in m.D) for g1 in m.G) for g in m.G) \
#          + sum(sum(sum(sum(m.STRG_LCA[strg_tech,lca_metrics]*m.inventory_rsrc[r,g,strg_tech,t,tm,s] \
#          for strg_tech in m.STRG_TECH) for g in m.G) for r in m.R) for t in m.T)


#def eqn7c_CCS(m,lca_metrics,tm,s):
#   """ Total metrics calculaton - LCA metrics."""
#   return m.total_metrics[lca_metrics,tm,s] == \
#      sum(sum(sum(1*( \
#       m.prod_rate[j,g,t,tm,s]*m.OPER_TIME_INTERVAL[t]*m.AVAILABILITY[g]) \
#          for j in m.J) for g in m.G) for t in m.T) \
#          + sum(sum(sum (m.NETWORK_LCA[d,lca_metrics]*m.DISTANCE[g,g1]*m.num_pipes[g,g1,d,tm,s] \
#          for d in m.D) for g1 in m.G) for g in m.G) \
#          + sum(sum(sum(sum(m.STRG_LCA[strg_tech,lca_metrics]*m.inventory_rsrc[r,g,strg_tech,t,tm,s] \
#          for strg_tech in m.STRG_TECH) for g in m.G) for r in m.R) for t in m.T)


#def eqn19_rule(m,tm,s):
#    """ Ensure that total use of biomass is less than available amount."""
#    return sum(sum(m.import_rate[name_for_biomass,g,t,tm,s]*m.OPER_TIME_INTERVAL[t] \
#           for g in m.G) for t in m.T) <= BIO_AVAILABILITY_PER_YEAR*NUM_YEARS_PER_TM
#m.eqn19 = Constraint(m.TM, m.S, rule=eqn19_rule)


#def eqn20_rule(m,postcomb,g,t,tm,s):
#   """ Ensures that post-combustion capture is applied to sources that are available 
#     at least 50% of the time as opposed to ad-hoc."""
#   if m.AVAILABILITY[g] <= MINIMUM_ASSET_AVAILABILITY:
#       return m.prod_rate[postcomb,g,t,tm,s] == 0
#   else:
#       return pyo.Constraint.NoConstraint


#def eqn21_rule(m,incumbent_use_tech,g,t,tm,s):
#   """ This equation ensures that either H2 or the incumbent technology is used in a location. """
#   return m.prod_rate[incumbent_use_tech,g,t,tm,s] <= (1-m.hydrogen_use[g,tm])*BIG_M
#m.eqn21 = Constraint(m.INCUMBENT_USE_TECH, m.G, m.T, m.TM, m.S, rule=eqn21_rule)


#def eqn22_rule(m,H2_use_tech,g,t,tm,s):
#   """ This equation ensures that either H2 or the incumbent technology is used in a location. """
#   return m.prod_rate[H2_use_tech,g,t,tm,s] <= m.hydrogen_use[g,tm]*BIG_M
#m.eqn22 = Constraint(m.H2_USE_TECH, m.G, m.T, m.TM, m.S, rule=eqn22_rule)


#def eqn23_rule(m,g,tm):
#    """ Ensures that once you begin to use H2, you cannot transition backwards to old technologies. """
#    if tm > 1:
#        return m.hydrogen_use[g,tm] >= m.hydrogen_use[g,tm-1]
#    else:
#        return Constraint.NoConstraint
#m.eqn23 = Constraint(m.G, m.TM, rule=eqn23_rule)

#LCA objective
#def obj_rule(model):
#    """ Defines the objective function for the optimisation process."""
#    return sum(sum(model.total_metrics[lca_objective_metric,tm,s]*model.PROBABILITY[s] \
#    for tm in model.TM) for s in model.S)
#model.obj = Objective(rule=obj_rule,sense=minimize)