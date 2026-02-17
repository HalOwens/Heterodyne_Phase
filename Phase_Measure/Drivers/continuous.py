from qm.qua import *
from qm import QuantumMachinesManager
from phase_config import qop_ip, cluster_name, config
# Elements names must match your minimal config:
# - "ref_out3_10MHz"
# - "ref_out7_10MHz"
# - "aom_fm_ctrl_out1"
#
# Pulses must exist:
# - ref_out3_10MHz: operation "cw" -> pulse "ref_cw"
# - ref_out7_10MHz: operation "cw" -> pulse "ref_cw"
# - aom_fm_ctrl_out1: operations "fm_off" and "fm_on"

with program() as cw_all_outputs:
    fm_on = False

    with infinite_loop_():
        # 10 MHz references on out3 and out7
        align("ref_out3_10MHz", "ref_out7_10MHz", "aom_fm_ctrl_out1")
        play("cw", "ref_out3_10MHz")
        play("cw", "ref_out7_10MHz")

        # DC level on out1 (FM control)
        if fm_on:
            play("fm_on", "aom_fm_ctrl_out1")
        else:
            play("fm_off", "aom_fm_ctrl_out1")

with program() as test_dc7:
    with infinite_loop_():
        play("on", "dc_out7")

qmm = QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name)
qm = qmm.open_qm(config)

#job = qm.execute(test_dc7)
job = qm.execute(cw_all_outputs)

# Let it run while you look at the spectrum analyzer/scope.
# When done:
x = input("Press any key to end")
job.cancel()

