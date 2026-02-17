from qm.qua import *
from qm import QuantumMachinesManager
from amp_config import qop_ip, cluster_name, config

with program() as cw_all_outputs:
    with infinite_loop_():
        align("Aom1", "Aom2")
        play("cw", "Aom1")
        play("cw", "Aom2")

qmm = QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name)
qm = qmm.open_qm(config)

job = qm.execute(cw_all_outputs)

# Let it run while you look at the spectrum analyzer/scope.
# When done:
x = input("Press any key to end")
job.cancel()

