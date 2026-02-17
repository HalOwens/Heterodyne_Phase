import qm.qua as qua
from qm import QuantumMachinesManager
from Phase_Measure.Drivers.phase_config import config, qop_ip, cluster_name
import numpy as np
from qualang_tools.units import unit

u = unit(coerce_to_integer=True)

###################
# The QUA program #
###################
with qua.program() as dual_tone_loopback:
    #n = qua.declare(int)
    #a = qua.declare(qua.fixed)
    adc_st = qua.declare_stream(adc_trace=True)
    #my_int = qua.declare(int)
    #qua.assign(my_int, 100)
    #qua.assign(a, 1.0)

    #qua.align("lf_out1", "lf_out8", "lf_in1", "qubit")
    #qua.play(qua.amp(a) * "cw", "lf_out1")
    #qua.play(qua.amp(a) * "cw", "lf_out8")
    #qua.play("cw", "qubit")
    qua.measure("readout", "lf_in1", adc_stream=adc_st)
    #with qua.for_(n, 0, n < 5, n + 1):
    #    qua.measure("readout", "lf_in1", adc_stream=adc_st)
    #    qua.wait(1000, "lf_out1")

    with qua.stream_processing():
        adc_st.input1().save("adc1_single_run")
        #adc_st.input1().buffer(2).save_all("adc1_single_run")

#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name)
###########################
# Run and Fetch Results   #
###########################
qm = qmm.open_qm(config)
dark_counts = []
N = 1
while True:
    job = qm.execute(dual_tone_loopback)
    res = job.result_handles
    res.wait_for_all_values()
    adc1_single_run = u.raw2volts(res.get("adc1_single_run").fetch_all())
    i = 150
    while i < len(adc1_single_run):
        if adc1_single_run[i] < -0.05:
            dark_counts.append(adc1_single_run[i-100:i+1000])
            i += 1000
        else:
            i += 1
    print(len(dark_counts))

    dark_counts_copy = np.array(dark_counts)
    np.savez("counts_no_signal_2", dark_counts_copy)