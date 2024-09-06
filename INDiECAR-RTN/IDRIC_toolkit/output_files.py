from __future__ import division
import cloudpickle
from pyomo.environ import *

name_for_nat_gas = 'NAT_GAS_HIGH_P'
MJ_TO_MWH = 3600
name_for_offset_tech = 'NET'
name_for_OpEx = 'OPEX'
MINIMUM_ASSET_AVAILABILITY = 0.7


def summary(instance, path):
    """writes aggregated values as summary of solution"""
    # create/open file
    csv = open(f'{path}Simulation_summary.csv','w')

    # summary section
    # costs:
    csv.write(f'Total annualised costs (kGBP per yr): {value(instance.obj)}\n')
    # natural gas:
#    agg = {key: 0 for key in instance.IMP_R}
#    for r, g, t, tm, s in instance.import_rate:
#        if r not in instance.IMP_R:
#            continue
#        val = instance.import_rate[r, g, t, tm, s].value * instance.AVAILABILITY[g]
#        time = instance.OPER_TIME_INTERVAL[t]
#        agg[r] += val * time
#    for k, v in agg.items():
#        csv.write(f'IMPORT: {k} requirement (MWh per yr): {v}\n')
    # emission offset:
#    agg = 0
#    for tech, g, t, tm, s in instance.prod_rate:
#        if tech != name_for_offset_tech:
#            continue
#        val = instance.prod_rate[tech, g, t, tm, s].value * instance.AVAILABILITY[g]
#        time = instance.OPER_TIME_INTERVAL[t]
#        agg += val * time
#    csv.write(f'Total cost of offsets (£k per yr): {agg}\n')
    # grid cells:
#    for g in instance.G:
#        if instance.AVAILABILITY[g] <= MINIMUM_ASSET_AVAILABILITY:
#            continue
        

#   csv.write('Grid cell, Annualised cost of capture and heat supply (£k per year)\n')
#   for g in instance.G:
       
#           csv.write('{0:d},{1:.0f}\n' .format(g,(sum(sum(sum(sum( \
#           instance.OPER_TIME_INTERVAL[t]*instance.AVAILABILITY[g]*( \
#           instance.PROCESS_COEFF[postcomb,name_for_OpEx,tm].value*instance.prod_rate[postcomb,g,t,tm,s].value \
#           + instance.import_rate[name_for_nat_gas,g,t,tm,s].value*instance.IMPORT_COEFF[name_for_nat_gas,name_for_OpEx])
#           for postcomb in instance.POSTCOMB) for t in instance.T) for tm in instance.TM) for s in instance.S))))
   


    csv.close








def prod_rate(instance, path, tol=0.01):
    """Writes prodction rates to csv file"""
    # create/open file
    csv = open(f'{path}prod_rate.csv','w')
    # write header
    header = ['Technology', 'Grid Cell', 'Major time', 
              'Minor time', 'Scenario', 'Production rate\n']
    csv.write(','.join(header))
    # fill with values which exceed the tolerance
    for key in instance.prod_rate:
       val = instance.prod_rate[key].value
       if val > tol:
          csv.write(f"{','.join([str(i) for i in [*key, val]])}\n")
    # close file
    csv.close


def emission_rate(instance, path, tol=0.01):
    """Writes emission rates to csv file"""
    # create/open file
    csv = open(f'{path}emission_rate.csv','w')
    # write header
    header = ['Resource', 'grid', 'Minor time', 'Major Time',
              'Scenario', 'rate\n']
    csv.write(','.join(header))
    # fill with values which exceed the tolerance
    for key in instance.emission_rate:
       val = instance.emission_rate[key].value
       if val > tol:
          csv.write(f"{','.join([str(i) for i in [*key, val]])}\n")
    # close file
    csv.close


def flow_rate(instance, path, tol=0.01):
    """Writes flow rates to csv file"""
    # create/open file
    csv = open(f'{path}flow_rate.csv','w')
    # write header
    header = ['From grid', 'To grid', 'Distribution type', 
              'Distribution mode', 'Minor time', 'Major Time',
              'Scenario', 'rate\n']
    csv.write(','.join(header))
    # fill with values which exceed the tolerance
    for key in instance.flow_rate:
       val = instance.flow_rate[key].value
       if val > tol:
          csv.write(f"{','.join([str(i) for i in [*key, val]])}\n")
    # close file
    csv.close


def import_rate(instance, path, tol=0.01):
    """Writes import rates to csv file"""
    # create/open file
    csv = open(f'{path}import_rate.csv','w')
    # write header
    header = ['Resource', 'grid', 'Minor time', 'Major Time',
              'Scenario', 'rate\n']
    csv.write(','.join(header))
    # fill with values which exceed the tolerance
    for key in instance.import_rate:
       val = instance.import_rate[key].value
       if val > tol:
          csv.write(f"{','.join([str(i) for i in [*key, val]])}\n")
    # close file
    csv.close

def transport_rate(instance, path, tol=0.01):
    """Writes import rates to csv file"""
    # create/open file
    csv = open(f'{path}transport_rate.csv','w')
    # write header
    header = ['Resource', 'grid', 'Minor time', 'Major Time',
              'Scenario', 'rate\n']
    csv.write(','.join(header))
    # fill with values which exceed the tolerance
    for key in instance.transport_rate:
       val = instance.transport_rate[key].value
       if val > tol:
          csv.write(f"{','.join([str(i) for i in [*key, val]])}\n")
    # close file
    csv.close


def inventory_rsrc(instance, path, tol=0.01):
    """Writes resource inventory to csv file"""
    # create/open file
    csv = open(f'{path}inventory_rsrc.csv','w')
    # write header
    header = ['Resource', 'grid', 'strg_tech', 'Minor time', 'Major Time',
              'Scenario', 'inventory\n']
    csv.write(','.join(header))
    # fill with values which exceed the tolerance
    for key in instance.inventory_rsrc:
       val = instance.inventory_rsrc[key].value
       if val > tol:
          csv.write(f"{','.join([str(i) for i in [*key, val]])}\n")
    # close file
    csv.close


def num_end_use(instance, path):
    """Writes number of end use technoglogies to csv file"""
    # create/open file
    csv = open(f'{path}num_end_use.csv','w')
    # write header
    header = ['end_use_tech', 'grid', 'Major Time',
              'Scenario', 'number\n']
    csv.write(','.join(header))
    # fill with values which exceed the tolerance
    for key in instance.num_end_use:
       val = instance.num_end_use[key].value
       if val > 0:
          csv.write(f"{','.join([str(i) for i in [*key, val]])}\n")
    # close file
    csv.close


def num_process(instance, path):
    """Writes number of processes to csv file"""
    # create/open file
    csv = open(f'{path}num_process.csv','w')
    # write header
    header = ['process_tech', 'grid', 'Major Time',
              'Scenario', 'number\n']
    csv.write(','.join(header))
    # fill with values which exceed the tolerance
    for key in instance.num_process:
       val = instance.num_process[key].value
       if val > 0:
          csv.write(f"{','.join([str(i) for i in [*key, val]])}\n")
    # close file
    csv.close


def num_process_invest(instance, path):
    """Writes number of processes to csv file"""
    # create/open file
    csv = open(f'{path}num_process_invest.csv','w')
    # write header
    header = ['process_tech', 'grid', 'Major Time',
              'Scenario', 'number\n']
    csv.write(','.join(header))
    # fill with values which exceed the tolerance
    for key in instance.num_process_invest:
       val = instance.num_process_invest[key].value
       if val > 0:
          csv.write(f"{','.join([str(i) for i in [*key, val]])}\n")
    # close file
    csv.close

def prod_rate (instance, path):
    """Writes number of processes to csv file"""
    # create/open file
    csv = open(f'{path}prod_rate.csv','w')
    # write header
    header = ['process_tech', 'grid', 'Minor Time', 'Major Time',
              'Scenario', 'rate\n']
    csv.write(','.join(header))
    # fill with values
    for key in instance.prod_rate:
       val = instance.prod_rate[key].value
       if val > 0:
          csv.write(f"{','.join([str(i) for i in [*key, val]])}\n")
    # close file
    csv.close


def num_strg(instance, path):
    """Writes number of storage technologies to csv file"""
    # create/open file
    csv = open(f'{path}num_strg.csv','w')
    # write header
    header = ['resource', 'strg_tech', 'grid', 'Major Time',
              'Scenario', 'number\n']
    csv.write(','.join(header))
    # fill with values which exceed the tolerance
    for key in instance.num_strg:
       val = instance.num_strg[key].value
       if val > 0:
          csv.write(f"{','.join([str(i) for i in [*key, val]])}\n")
    # close file
    csv.close


def num_pipes(instance, path):
    """Writes number of pipelines to csv file"""
    # create/open file
    csv = open(f'{path}num_pipes.csv','w')
    # write header
    header = ['From grid', 'To grid', 'Distribution type', 'Major time', 
              'Scenario', 'No. of units\n']
    csv.write(','.join(header))
    # fill with values
    for key in instance.num_pipes:
       val = instance.num_pipes[key].value
       if val > 0:
          csv.write(f"{','.join([str(i) for i in [*key, val]])}\n")
    # close file
    csv.close

def num_pipes_invest(instance, path):
    """Writes number of pipelines to csv file"""
    # create/open file
    csv = open(f'{path}num_pipes_invest.csv','w')
    # write header
    header = ['From grid', 'To grid', 'Distribution type', 'Major time', 
              'Scenario', 'No. of units\n']
    csv.write(','.join(header))
    # fill with values
    for key in instance.num_pipes_invest:
       val = instance.num_pipes_invest[key].value
       if val > 0:
          csv.write(f"{','.join([str(i) for i in [*key, val]])}\n")
    # close file
    csv.close


def total_metrics(instance, path, tol=0.01):
    """Writes total metrics to csv file"""
    # create/open file
    csv = open(f'{path}total_metrics.csv','w')
    # write header
    header = ['Major Time', 'Performance metric', 'Scenario', 
              'Total metric value\n']
    csv.write(','.join(header))
    # fill with values
    for key in instance.total_metrics:
       val = instance.total_metrics[key].value
       if val > tol:
          csv.write(f"{','.join([str(i) for i in [*key, val]])}\n")
    # close file
    csv.close


def store_instance(instance, path, name='instance'):
    """pickles model instance"""
    with open(f'{path}{name}.pkl', 'wb') as f:
        cloudpickle.dump(instance, f)


def write_instance_info(instance, path):
    """writes model instance info as text files"""
    with open(f'{path}run_declaration.txt', 'w') as output_file:
        instance.pprint(output_file)
    with open(f'{path}run_results.txt', 'w') as output_file:
        instance.display(ostream=output_file)


def try_postprocessing(func, instance, path):
    """wrapper function to try executing post-processing function"""
    try:
        func(instance, path)
    except Exception as e:
        print(f"Unable to execute function: {func.__name__}")
        print(e)


def write_output(instance, path):
    # check if solution is valid
    if instance == None:
       print('empty solution')
       return
   
    # call functions to write data to csv files
    try_postprocessing(emission_rate, instance, path)
    try_postprocessing(prod_rate, instance, path)
    try_postprocessing(flow_rate, instance, path)
    try_postprocessing(import_rate, instance, path)
    try_postprocessing(transport_rate, instance, path)
    try_postprocessing(inventory_rsrc, instance, path)
    try_postprocessing(num_end_use, instance, path)
    try_postprocessing(num_process, instance, path)
    try_postprocessing(num_process_invest, instance, path)
    try_postprocessing(num_strg, instance, path)
    try_postprocessing(num_pipes, instance, path)
    try_postprocessing(num_pipes_invest, instance, path)
    try_postprocessing(prod_rate, instance, path)
    try_postprocessing(total_metrics, instance, path)
    try_postprocessing(summary, instance, path)

    # pickle instance and write info
    #try_postprocessing(store_instance, instance, path)

    #Comment this out if you don't need output sheet !!!
    #try_postprocessing(write_instance_info, instance, path)
