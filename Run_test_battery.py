##### don't show warnings
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

##### import packages
from brian2 import *
from brian2.units.constants import zero_celsius, gas_constant as R, faraday_constant as F
import thorns as th
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

##### set working directory to folder of script
#abspath = os.path.abspath(__file__)
#dname = os.path.dirname(abspath)
#os.chdir(dname)

##### import functions
import functions.stimulation as stim
import functions.create_plots as plot
import functions.model_tests as test
import functions.calculations as calc

##### import models
import models.Rattay_2001 as rattay_01
import models.Frijns_1994 as frijns_94
import models.Frijns_2005 as frijns_05
import models.Smit_2009 as smit_09
import models.Smit_2010 as smit_10
import models.Imennov_2009 as imennov_09
import models.Negm_2014 as negm_14

##### makes code faster and prevents warning
prefs.codegen.target = "numpy"

# =============================================================================
# Initializations
# =============================================================================
##### choose model
model_name = "rattay_01"
model = eval(model_name)

##### initialize clock
dt = 5*us

##### define way of processing
backend = "serial"

# =============================================================================
# Get thresholds for certain stimulation types and stimulus durations
# =============================================================================
##### define phase durations to test (in us)
phase_durations_mono = [40,50,100]
phase_durations_bi = [20,40,50,200,400]

##### define test parameters
phase_durations = [ii*1e-6 for ii in phase_durations_mono + phase_durations_bi]
pulse_form = np.repeat(["mono","bi"], (len(phase_durations_mono),len(phase_durations_bi)))
runs_per_stimulus_type = 2

##### define varied parameters 
params = [{"phase_duration" : phase_durations[ii],
           "pulse_form" : pulse_form[ii]} for ii in range(0,len(phase_durations))]

##### get thresholds
threshold_table = th.util.map(func = test.get_threshold,
                              space = params,
                              backend = backend,
                              cache = "no",
                              kwargs = {"model_name" : model_name,
                                        "dt" : dt,
                                        "delta" : 0.0001*uA,
                                        "stimulation_type" : "extern",
                                        "amps_start_interval" : [0,30]*uA,
                                        "add_noise" : False,
                                        "run_number" : 1})

##### change index to column
threshold_table.reset_index(inplace=True)

##### change column names
threshold_table = threshold_table.rename(index = str, columns={"phase_duration" : "phase duration",
                                                               "pulse_form" : "pulse form",
                                                               0:"threshold"})

##### add unit to phase duration
threshold_table["phase duration"] = [ii*second for ii in threshold_table["phase duration"]]

##### built subset of dataframe
threshold_table = threshold_table[["phase duration", "pulse form", "threshold"]]

##### Save dataframe as csv    
threshold_table.to_csv("test_battery_results/{}/Threshold_table {}.csv".format(model.display_name,model.display_name), index=False, header=True)

# =============================================================================
# Get chronaxie and rheobase
# =============================================================================
##### get rheobase
rheobase = test.get_threshold(model_name = model_name,
                              dt = dt,
                              phase_duration = 1*ms,
                              delta = 0.0001*uA,
                              amps_start_interval = [0,20]*uA,
                              stimulation_type = "extern",
                              pulse_form = "mono")

##### get chronaxie
chronaxie = test.get_chronaxie(model = model,
                               dt = dt,
                               rheobase = rheobase,
                               phase_duration_start_interval = [0,1000]*us,
                               delta = 1*us,
                               stimulation_type = "extern",
                               pulse_form = "mono",
                               time_before = 2*ms)

##### round values
rheobase = np.round(rheobase/nA,1)*nA
chronaxie = np.round(chronaxie/us,1)*us

##### save values in dataframe
strength_duration_data = pd.DataFrame(np.array([[rheobase/uA], [chronaxie/us]]).T,
                                         columns = ["rheobase (uA)", "chronaxie (us)"])

##### Save table as csv    
strength_duration_data.to_csv("test_battery_results/{}/Strength_duration_data {}.csv".format(model.display_name,model.display_name), index=False, header=True)

# =============================================================================
# Get strength-duration curve
# =============================================================================
##### define phase durations
phase_durations = np.round(np.logspace(1, 9, num=20, base=2.0))*us

##### define varied parameter    
params = {"phase_duration" : phase_durations}

##### get thresholds
strength_duration_plot_table = th.util.map(func = test.get_threshold,
                                      space = params,
                                      backend = backend,
                                      cache = "no",
                                      kwargs = {"model_name" : model_name,
                                                "dt" : 1*us,
                                                "delta" : 0.01*uA,
                                                "pulse_form" : "mono",
                                                "stimulation_type" : "extern",
                                                "amps_start_interval" : [0,20]*uA,
                                                "add_noise" : False})

##### change index to column
strength_duration_plot_table.reset_index(inplace=True)

##### change column names
strength_duration_plot_table = strength_duration_plot_table.rename(index = str, columns={0:"threshold"})

##### change column order
strength_duration_plot_table = strength_duration_plot_table[["phase_duration", "threshold"]] 

##### plot strength duration curve
strength_duration_curve = plot.strength_duration_curve(plot_name = "Strength duration curve {}".format(model.display_name),
                                                       threshold_matrix = strength_duration_plot_table,
                                                       rheobase = rheobase,
                                                       chronaxie = chronaxie)

##### save strength duration curve and table
strength_duration_plot_table.to_csv("test_battery_results/{}/Strength_duration_plot_table {}.csv".format(model.display_name,model.display_name), index=False, header=True)
strength_duration_curve.savefig("test_battery_results/{}/Strength_duration_curve {}.png".format(model.display_name,model.display_name))

# =============================================================================
# Get the relative spread of thresholds for certain stimulation types and stimulus durations
# =============================================================================
##### define phase durations to test (in us)
phase_durations_mono = [40,100]
phase_durations_bi = [200,400]

##### define test parameters
phase_durations = [ii*1e-6 for ii in phase_durations_mono + phase_durations_bi]
pulse_form = np.repeat(["mono","bi"], (len(phase_durations_mono),len(phase_durations_bi)))
runs_per_stimulus_type = 50

##### define varied parameters 
params = [{"phase_duration" : phase_durations[ii],
           "run_number" : jj,
           "pulse_form" : pulse_form[ii]} for ii in range(0,len(phase_durations)) for jj in range(0,runs_per_stimulus_type)]

##### get thresholds
relative_spread_plot_table = th.util.map(func = test.get_threshold,
                                         space = params,
                                         backend = backend,
                                         cache = "no",
                                         kwargs = {"model_name" : model_name,
                                                   "dt" : dt,
                                                   "delta" : 0.0005*uA,
                                                   "stimulation_type" : "extern",
                                                   "amps_start_interval" : [0,20]*uA,
                                                   "time_before" : 2*ms,
                                                   "time_after" : 2*ms,
                                                   "add_noise" : True})

##### change index to column
relative_spread_plot_table.reset_index(inplace=True)

##### change column names
relative_spread_plot_table = relative_spread_plot_table.rename(index = str, columns={"phase_duration" : "phase duration",
                                                                                     "pulse_form" : "pulse form",
                                                                                     0:"threshold"})

##### add unit to phase duration
relative_spread_plot_table["phase duration"] = [ii*second for ii in relative_spread_plot_table["phase duration"]]

##### adjust pulse form column
relative_spread_plot_table["pulse form"] = ["monophasic" if pulse_form[ii]=="mono" else "biphasic" for ii in range(0,len(phase_durations))]

##### built subset of dataframe
relative_spread_plot_table = relative_spread_plot_table[["phase duration", "pulse form", "threshold"]]

##### plot relative spreads
relative_spread_plot = plot.relative_spread(plot_name = "Relative spreads {}".format(model.display_name),
                                            threshold_matrix = relative_spread_plot_table)

##### save relative spreads plot
relative_spread_plot_table.to_csv("test_battery_results/{}/Relative_spread_plot_table {}.csv".format(model.display_name,model.display_name), index=False, header=True)
relative_spread_plot.savefig("test_battery_results/{}/Relative_spreads_plot {}.png".format(model.display_name,model.display_name))

##### calculate relative spread values
thresholds = relative_spread_plot_table.groupby(["phase duration", "pulse form"])
relative_spreads = round(thresholds.std()/thresholds.mean()*100, 2)
relative_spreads.reset_index(inplace=True)
relative_spreads = relative_spreads.rename(index = str, columns={"threshold" : "relative spread"})
relative_spreads["relative spread"] = ["{}%".format(relative_spreads["relative spread"][ii]) for ii in range(0,np.shape(relative_spreads)[0])]

##### Save table as csv    
relative_spreads.to_csv("test_battery_results/{}/Relative_spreads {}.csv".format(model.display_name,model.display_name), index=False, header=True)   

# =============================================================================
# Measure conduction velocity
# =============================================================================
##### define compartments to start and end measurements
node_indexes = np.where(model.structure == 2)[0]

##### models with a soma
if hasattr(model, "index_soma"):
    
    ##### dendrite
    node_indexes_dendrite = node_indexes[node_indexes < min(model.index_soma)[0]]
        
    conduction_velocity_dendrite = test.get_conduction_velocity(model = model,
                                                                dt = dt,
                                                                stimulated_compartment = node_indexes_dendrite[0],
                                                                measurement_start_comp = node_indexes_dendrite[1],
                                                                measurement_end_comp = node_indexes_dendrite[-1])
    
    conduction_velocity_dendrite_ratio = round((conduction_velocity_dendrite/(meter/second))/(model.dendrite_outer_diameter/um),2)
    
    ##### axon
    node_indexes_axon = node_indexes[node_indexes > max(model.index_soma)[0]]

    conduction_velocity_axon = test.get_conduction_velocity(model = model,
                                                            dt = dt,
                                                            stimulated_compartment = node_indexes_dendrite[0],
                                                            measurement_start_comp = node_indexes_axon[0],
                                                            measurement_end_comp = node_indexes_axon[-3])
    
    conduction_velocity_axon_ratio = round((conduction_velocity_axon/(meter/second))/(model.axon_outer_diameter/um),2)
    
    ##### save values in dataframe
    conduction_velocity_table = pd.DataFrame(np.array([[conduction_velocity_dendrite], [conduction_velocity_dendrite_ratio], [conduction_velocity_axon], [conduction_velocity_axon_ratio]]).T,
                                             columns = ["velocity dendrite (m/s)", "velocity/diameter dendrite", "velocity axon (m/s)", "velocity/diameter axon"])

##### models without a soma 
else:
   conduction_velocity = test.get_conduction_velocity(model = model,
                                                      dt = dt,
                                                      stimulated_compartment = node_indexes[1],
                                                      measurement_start_comp = node_indexes[2],
                                                      measurement_end_comp = node_indexes[-3])
   
   conduction_velocity_ratio = round((conduction_velocity/(meter/second))/(model.fiber_outer_diameter/um),2)
   
   ##### save values in dataframe
   conduction_velocity_table = pd.DataFrame(np.array([[conduction_velocity], [conduction_velocity_ratio]]).T,
                                            columns = ["velocity (m/s)", "velocity/diameter"])

##### Save table as csv    
conduction_velocity_table.to_csv("test_battery_results/{}/Conduction_velocity_table {}.csv".format(model.display_name,model.display_name), index=False, header=True)

# =============================================================================
# Measure single node response properties
# =============================================================================
##### define phase durations to test (in us)
phase_durations_mono = [40,50,100]
phase_durations_bi = [200]

##### generate lists with test parameters
phase_duration = [i*us for i in phase_durations_mono + phase_durations_bi]
pulse_form = np.repeat(["mono","bi"], (len(phase_durations_mono),len(phase_durations_bi)))    

##### define how many stimulus amplitudes to test
nof_stim_amps = 2

##### define number of stochastic runs
nof_stochastic_runs = 20

##### initialize summary dataset
column_names = ["phase duration (us)", "pulse form", "stimulus amplitude level", "AP height (mV)", "rise time (ms)",
                "fall time (ms)", "AP duration (ms)", "latency (ms)", "jitter (ms)"]
node_response_data_summary = pd.DataFrame(np.zeros((len(phase_duration*nof_stim_amps), len(column_names))), columns = column_names)

##### initialize list of datasets to save voltage course data
voltage_courses = [pd.DataFrame()]*len(phase_duration)*nof_stim_amps

##### loop over all phase durations to test
for ii in range(0,len(phase_duration)):
    
    ##### look up threshold for actual stimulation
    threshold = threshold_table["threshold"][threshold_table["pulse form"] == pulse_form[ii]]\
                                            [threshold_table["phase duration"]/us == phase_duration[ii]/us].iloc[0]
    
    ##### loop over stimulus amplitudes to test
    for jj in range(0,nof_stim_amps):
        
        ##### define stimulus amplitude
        stim_amp = (jj+1)*threshold                                        
        
        ##### measure single node response properties
        voltage_data, node_response_data = \
        test.get_single_node_response(model = model,
                                      dt = dt,
                                      param_1 = "stim_amp",
                                      param_1_ratios = [1],
                                      param_2 = "stochastic_runs",
                                      stimulation_type = "extern",
                                      pulse_form = pulse_form[ii],
                                      time_after_stimulation = 2*ms,
                                      stim_amp = stim_amp,
                                      phase_duration = phase_duration[ii],
                                      nof_runs = nof_stochastic_runs)
        
        ##### write voltage dataset in voltage courses list
        voltage_courses[nof_stim_amps*ii+jj] = voltage_data
        voltage_courses[nof_stim_amps*ii+jj] = voltage_courses[nof_stim_amps*ii+jj].drop(columns = "stimulus amplitude (uA)")
        voltage_courses[nof_stim_amps*ii+jj]["phase duration (us)"] = round(phase_duration[ii]/us)
        voltage_courses[nof_stim_amps*ii+jj]["pulse form"] = "monophasic" if pulse_form[ii]=="mono" else "biphasic"
        voltage_courses[nof_stim_amps*ii+jj]["stimulus amplitude level"] = "threshold" if jj==0 else "{}*threshold".format(jj+1)
        

        ##### write results in summary table
        node_response_data_summary.loc[nof_stim_amps*ii+jj,"phase duration (us)"] = phase_duration[ii]/us
        node_response_data_summary.loc[nof_stim_amps*ii+jj,"pulse form"] = "monophasic" if pulse_form[ii]=="mono" else "biphasic"
        node_response_data_summary.loc[nof_stim_amps*ii+jj,"stimulus amplitude level"] = "threshold" if jj==0 else "{}*threshold".format(jj+1)
        node_response_data_summary.loc[nof_stim_amps*ii+jj,["AP height (mV)", "rise time (ms)", "fall time (ms)", "latency (ms)"]] =\
        node_response_data[["AP height (mV)", "rise time (ms)", "fall time (ms)", "latency (ms)"]].mean()
        node_response_data_summary.loc[nof_stim_amps*ii+jj,"latency (ms)"] = node_response_data_summary.loc[nof_stim_amps*ii+jj,"latency (ms)"]
        node_response_data_summary.loc[nof_stim_amps*ii+jj,"jitter (ms)"] = node_response_data["latency (ms)"].std()
        node_response_data_summary.loc[nof_stim_amps*ii+jj,"AP duration (ms)"] = sum(node_response_data_summary.loc[ii,["rise time (ms)", "fall time (ms)"]])

##### round for 3 significant digits
for ii in ["AP height (mV)", "rise time (ms)", "fall time (ms)", "AP duration (ms)", "latency (ms)", "jitter (ms)"]:
    node_response_data_summary[ii] = ["%.3g" %node_response_data_summary[ii][jj] for jj in range(0,node_response_data_summary.shape[0])]

##### Save table as csv    
node_response_data_summary.to_csv("test_battery_results/{}/Node_response_data_summary {}.csv".format(model.display_name,model.display_name), index=False, header=True)

##### combine list entries of voltage courses to one dataset
voltage_course_dataset = pd.concat(voltage_courses)
voltage_course_dataset["stimulation info"] = voltage_course_dataset["phase duration (us)"].map(str) + [" us; "] + voltage_course_dataset["pulse form"].map(str) +\
["; "] + voltage_course_dataset["stimulus amplitude level"].map(str)
voltage_course_dataset = voltage_course_dataset[["stimulation info", "run", "time / ms", "membrane potential / mV"]]

##### plot voltage courses of single node
single_node_response = plot.single_node_response_voltage_course(plot_name = "Voltage courses {}".format(model.display_name),
                                                                voltage_data = voltage_course_dataset,
                                                                col_wrap = 2,
                                                                height = 3.5)

###### save voltage courses plot
single_node_response.savefig("test_battery_results/{}/Single_node_response {}.png".format(model.display_name,model.display_name))

# =============================================================================
# Refractory periods
# =============================================================================
##### define phase durations to test (in us)
phase_durations_mono = [40,50,100]
phase_durations_bi = [50,200]

##### generate lists with test parameters
phase_durations = [ii*1e-6 for ii in phase_durations_mono + phase_durations_bi]
pulse_form = np.repeat(["mono","bi"], (len(phase_durations_mono),len(phase_durations_bi)))

##### look up thresholds
thresholds = [threshold_table["threshold"][threshold_table["pulse form"] == pulse_form[ii]]\
                                         [threshold_table["phase duration"]/us == (phase_durations_mono + phase_durations_bi)[ii]].iloc[0]\
                                         for ii in range(0,len(phase_durations))]/amp

##### define varied parameters 
params = [{"phase_duration" : phase_durations[ii],
           "pulse_form" : pulse_form[ii],
           "threshold" : thresholds[ii],
           "amp_masker" : thresholds[ii]*1.5} for ii in range(0,len(phase_durations))]

##### get refractory periods
refractory_table = th.util.map(func = test.get_refractory_periods,
                               space = params,
                               backend = backend,
                               cache = "no",
                               kwargs = {"model_name" : model_name,
                                         "dt" : dt,
                                         "delta" : 1*us,
                                         "stimulation_type" : "extern"})
    
##### change index to column
refractory_table.reset_index(inplace=True)

##### change column names
refractory_table = refractory_table.rename(index = str, columns={"phase_duration" : "phase duration",
                                                                 "pulse_form" : "pulse form"})

##### extract refractory periods
refractory_table["absolute refractory period (ms)"] = [round(refractory_table[0][ii][0]/ms, 3) for ii in range(0,len(phase_durations))]
refractory_table["relative refractory period (ms)"] = [round(refractory_table[0][ii][1]/ms, 3) for ii in range(0,len(phase_durations))]

##### add unit to phase duration
refractory_table["phase duration"] = [ii*second for ii in refractory_table["phase duration"]] 

##### adjust pulse form column
refractory_table["pulse form"] = ["monophasic" if pulse_form[ii]=="mono" else "biphasic" for ii in range(0,len(phase_durations))]

##### built subset of dataframe
refractory_table = refractory_table[["phase duration", "pulse form", "absolute refractory period (ms)","relative refractory period (ms)"]]

##### Save dataframe as csv    
refractory_table.to_csv("test_battery_results/{}/Refractory_table {}.csv".format(model.display_name,model.display_name), index=False, header=True)   

# =============================================================================
# Refractory curve
# =============================================================================
##### define inter-pulse-intervals
inter_pulse_intervals = np.logspace(-1.3, 2.9, num=3, base=2)*ms

##### define stimulation parameters
phase_duration = 100*us
pulse_form = "mono"

##### look up threshold
threshold = threshold_table["threshold"][threshold_table["pulse form"] == pulse_form]\
                                         [threshold_table["phase duration"]/us == phase_duration/us].iloc[0]

##### define varied parameter    
params = {"inter_pulse_interval" : inter_pulse_intervals}

##### get thresholds
refractory_curve_table = th.util.map(func = test.get_refractory_curve,
                                     space = params,
                                     backend = backend,
                                     cache = "no",
                                     kwargs = {"model_name" : model_name,
                                               "dt" : dt,
                                               "delta" : 0.0001*uA,
                                               "pulse_form" : pulse_form,
                                               "stimulation_type" : "extern",
                                               "phase_duration" : phase_duration,
                                               "threshold" : threshold,
                                               "amp_masker" : threshold*1.5})

##### change index to column
refractory_curve_table.reset_index(inplace=True)

##### change column name
refractory_curve_table = refractory_curve_table.rename(index = str, columns={"inter_pulse_interval" : "interpulse interval"})

##### extract refractory periods
refractory_curve_table["minimum required amplitude"] = [refractory_curve_table[0][ii][0] for ii in range(0,len(inter_pulse_intervals))]

##### built subset of dataframe
refractory_curve_table = refractory_curve_table[["interpulse interval", "minimum required amplitude"]]


##### plot refractory curve
refractory_curve = plot.refractory_curve(plot_name = "Refractory curve {}".format(model.display_name),
                                         inter_pulse_intervals = refractory_curve_table["interpulse interval"],
                                         stimulus_amps = refractory_curve_table["minimum required amplitude"],
                                         threshold = threshold)

##### save refractory curve
refractory_curve_table.to_csv("test_battery_results/{}/Refractory_curve_table {}.csv".format(model.display_name,model.display_name), index=False, header=True)   
refractory_curve.savefig("test_battery_results/{}/Refractory_curve {}.png".format(model.display_name,model.display_name))

# =============================================================================
# Post Stimulus Time Histogram
# =============================================================================
##### pulse rates to test
pulses_per_second = [250,1000,5000,10000]

##### phase durations for respective pulse rates
phase_duration = [40,40,40,20]*us

##### stimulus levels (will be multiplied with the threshold for a certain stimulation) 
stim_amp_level = [1,1.2,1.5]

##### number of runs
nof_runs = 5

##### look up thresholds
thresholds = [threshold_table["threshold"][threshold_table["pulse form"] == "bi"]\
                           [threshold_table["phase duration"]/us == phase_duration[ii]/us].iloc[0]\
                           for ii in range(0,len(phase_duration))]

##### define varied parameters 
params = [{"pulses_per_second" : pulses_per_second[ii],
           "phase_duration" : phase_duration[ii]/second,
           "stim_amp" : stim_amp_level[jj]*thresholds[ii]/amp,
           "run_number" : kk}
            for ii in range(0,len(pulses_per_second))\
            for jj in range(0,len(stim_amp_level))\
            for kk in range(0,nof_runs)]

##### get thresholds
psth_table = th.util.map(func = test.post_stimulus_time_histogram,
                         space = params,
                         backend = backend,
                         cache = "no",
                         kwargs = {"model_name" : model_name,
                                   "dt" : dt,
                                   "stim_duration" : 20*ms,
                                   "stimulation_type" : "extern",
                                   "pulse_form" : "bi"})

##### change index to column
psth_table.reset_index(inplace=True)

##### change column names
psth_table = psth_table.rename(index = str, columns={"phase_duration" : "phase duration (us)",
                                                     "pulses_per_second" : "pulse rate",
                                                     "stim_amp" : "stimulus amplitude (uA)",
                                                     "run_number" : "run",
                                                     0 : "spike times (us)"})

##### add row with stimulus amplitude information
psth_table["amplitude"] = ["{}*threshold".format(stim_amp_level[jj])
                            for ii in range(0,len(pulses_per_second))
                            for jj in range(0,len(stim_amp_level))
                            for kk in range(0,nof_runs)]

##### built subset of dataframe
psth_table = psth_table[["phase duration (us)", "pulse rate", "stimulus amplitude (uA)", "amplitude", "run", "spike times (us)"]]

##### split lists in spike times column to multiple rows
psth_table = calc.explode(psth_table, ["spike times (us)"])

##### change units from second to us and form amp to uA
psth_table["phase duration (us)"] = round(psth_table["phase duration (us)"]*1e6).astype(int)
psth_table["stimulus amplitude (uA)"] = round(psth_table["stimulus amplitude (uA)"]*1e6,2)
psth_table["spike times (us)"] = round(psth_table["spike times (us)"]*1e6).astype(int)

##### save PSTH dataset to csv
psth_table.to_csv("test_battery_results/{}/PSTH_table {}.csv".format(model.display_name,model.display_name), index=False, header=True)   

##### plot post_stimulus_time_histogram
post_stimulus_time_histogram = plot.post_stimulus_time_histogram(plot_name = "PSTH {}".format(model.display_name),
                                                                 psth_dataset = psth_table)

###### save post_stimulus_time_histogram
post_stimulus_time_histogram.savefig("test_battery_results/{}/PSTH {}.png".format(model.display_name,model.display_name))

## =============================================================================
## Inter-stimulus interval Histogram
## =============================================================================
###### pulse rates to test
#pulses_per_second = [150,1000,5000]
#
###### phase durations for respective pulse rates
#phase_duration = [40,40,40]*us
#
###### stimulus levels (will be multiplied with the threshold for a certain stimulation) 
#stim_amp_level = [1,1.1,1.2]
#
###### initialize list of datasets to save bin heights end edges for each type of stimulation
#isi_data = [pd.DataFrame()]*len(pulses_per_second)*len(stim_amp_level)
#
###### loop over pulse rates and phase duraions
#for ii in range(0,len(pulses_per_second)):
#    
#    ##### look up threshold for actual stimulation
#    threshold = threshold_table["threshold"][threshold_table["pulse form"] == "bi"]\
#                               [threshold_table["phase duration"]/us == phase_duration[ii]/us].iloc[0]
#    
#    ##### loop over stimulus amplitudes
#    for jj in range(0,len(stim_amp_level)):
#                                        
#        ##### calculate bin heigths and edges
#        isi = test.inter_stimulus_interval_histogram(model = model,
#                                                      dt = dt,
#                                                      nof_repeats = 5,
#                                                      pulses_per_second = pulses_per_second[ii],
#                                                      stim_duration = 30*ms,
#                                                      stim_amp = stim_amp_level[jj]*threshold,
#                                                      stimulation_type = "extern",
#                                                      pulse_form = "bi",
#                                                      phase_duration = phase_duration[ii])
#        
#        ##### write the data in a list of dataframes
#        isi_data[len(stim_amp_level)*ii+jj] = isi
#        isi_data[len(stim_amp_level)*ii+jj]["amplitude"] = "{}*threshold".format(stim_amp_level[jj])
#        
###### combine list entries of psth_data to one dataset
#isi_dataset = pd.concat(isi_data)
#
###### plot inter_stimulus_interval_histogram
#plot.inter_stimulus_interval_histogram(plot_name = "ISI {}".format(model.display_name),
#                                        isi_dataset = isi_dataset)
#
####### save inter_stimulus_interval_histogram
#inter_stimulus_interval_histogram.savefig("test_battery_results/{}/ISI {}.png".format(model.display_name,model.display_name))
