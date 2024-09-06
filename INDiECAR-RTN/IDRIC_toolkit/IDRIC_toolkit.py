"""Main module.

Solves case study: creates and solves model instance to optimality.
Use ``IDRIC_toolkit --help`` for further information.
"""

import os
import json
import pyomo.environ as pyo
from argparse import ArgumentParser
from IDRIC_toolkit.RTN_AbstractModel import instantiate_model, backcast_model
from IDRIC_toolkit.output_files import write_output
from pyomo.util.infeasible import log_infeasible_constraints, log_infeasible_bounds
from numpy import random

 


def parse_args():
    parser = ArgumentParser("IDRIC-toolkit")
    # Selection of case study and problem input (data files)
    parser.add_argument("--pathCASE", help="File system location name of case study",
                        type=str)
    parser.add_argument("--RunName", help="File name of optimisation problem",
                        default="GHGT16", type=str)
    return parser.parse_args()


def get_solver(name, mipgap, tlimit, integralityTolerance):
    """returns solver with stop conditions for timeout and optimality"""
    solver = pyo.SolverFactory(name)
    # add options
    if name == 'glpk':
        solver.options['tmlim'] = tlimit
    elif name == 'cplex':
        solver.options['timelimit'] = tlimit
        solver.options["mip tolerances integrality"] = integralityTolerance
        solver.options["simplex tolerances feasibility"] = 1e-8
    solver.options['mipgap'] = mipgap
    return solver


def postprocess(instance, pathOUTPUT):
    """"""
    # create output folder
    if not os.path.exists(pathOUTPUT):
        os.makedirs(pathOUTPUT)
    # write results
    write_output(instance, pathOUTPUT)


def read_RunSettings(sttng):
    trgts = sorted(sttng['stateGates']['targets'], reverse=True)
    # only network optimisation
    if bool(sttng['instantiate']['CCS_network_only']) & (len(trgts) == 0):
        # we only need to design a network, no target value considered
        # and only one state gate is required
        runs = ['snapshotCCS']
        trgts = [0]
    else:
        if bool(sttng['instantiate']['CCS_network_only']):
            adm = 'CCS'
        else:
            adm = ''
        # multiple runs with reduction targets
        runs = []
        for i, t in enumerate(trgts):
            if (i == 0) | (not(bool(sttng['stateGates']['backcasting']))):
                prefix = 'snapshot'
            else:
                prefix = 'backcast'
            runs.append(f'{prefix}{adm}{t}')
    return runs, trgts


def execute_optimization(pathCASE, RunName):
    """main optimization work flow"""
    # read optimisation (input) settings
    with open(f'{pathCASE}{RunName}.json') as json_file:
        sttng = json.load(json_file)

    # load optimiser/solver
    optmzr = get_solver(**sttng['solver'])

    # solve the indicated state gates
    runs, trgts = read_RunSettings(sttng)

    for run, trgt in zip(runs, trgts):
        # result path
        pathOUTPUT = f"{pathCASE}{RunName}/{run}/"
        if not os.path.exists(pathOUTPUT):
            os.makedirs(pathOUTPUT)

        # initialisation:
        
        # <insert block here to find similar problem formulations>
        # if <ceratain criteria>
        #    load instance and perform warmstart
        #
        # else
        
        # adjust initialisation: backcast
        if 'backcast' in run:
            instnc = backcast_model(instnc)
        else:
            instnc = instantiate_model(pathCASE, **sttng['instantiate'])

        # set reduction target
        instnc.CO2_REMOVAL_FRACTION[1] = trgt / 100.

        #give a random number
        Nr = random.randint(100)

        #get CaseName from path: 
        CaseName = os.path.basename(os.path.normpath(pathCASE))
        print (CaseName)

        # solve problem
        results = optmzr.solve(instnc, logfile=f"solver_log_{CaseName}_{RunName}{Nr}.log")
        log_infeasible_constraints(instnc)
        log_infeasible_bounds(instnc)
        print(f"{run}: {results.solver.termination_condition}")

        # postprocess run
        postprocess(instnc, pathOUTPUT)


if __name__ == "__main__":
    args = parse_args()
    execute_optimization(args.pathCASE, args.RunName)

