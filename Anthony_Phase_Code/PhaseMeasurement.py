from qm.qua import *
from qm import QuantumMachinesManager, generate_qua_script
from amp_config import qop_ip, cluster_name, config
import numpy as np
import matplotlib.pyplot as plt
#DEMOD_FREQ_HZ = 10_181_818   # <---- change this later as needed
DEMOD_FREQ_HZ = 10_000_000
N_SHOTS = 100            # fixed acquisition count (no infinite loop)
clockTime=Time*250

with program() as iq_acquire_in1:
    n = declare(int)

    I = declare(fixed)
    Q = declare(fixed)

    I_st = declare_stream()
    Q_st = declare_stream()

    # Set the demodulation frequency by setting the element IF.
    # This assumes your element "lf_in1_iq" exists and has IF that can be updated.
    update_frequency("lf_in1_iq", DEMOD_FREQ_HZ)

with for_(k, 0,k<clockTime,k+1):
    with for_(n, 0, n < N_SHOTS, n + 1):
        reset_if_phase("lf_in1_iq")
        align("Aom1", "Aom2", "lf_in1_iq")
        play("cw", "Aom1")
        play("cw", "Aom2")
        measure(
            "readout",
            "lf_in1_iq",
            demod.full("cos", I, "out1"),
            demod.full("sin", Q, "out1"),
        )
        save(I, I_st)
        save(Q, Q_st)
        wait(100)

    with stream_processing():
        I_st.save_all("I")
        Q_st.save_all("Q")

sourceFile = open('debug.py', 'w')
print(generate_qua_script(iq_acquire_in1, config), file=sourceFile)
sourceFile.close()



qmm = QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name)
qm = qmm.open_qm(config)

job = qm.execute(iq_acquire_in1)
res = job.result_handles
res.wait_for_all_values()

#I_data = np.squeeze(res.get("I").fetch_all())
#Q_data = np.squeeze(res.get("Q").fetch_all())
I_raw = res.get("I").fetch_all()
Q_raw = res.get("Q").fetch_all()

I = [x[0] for x in I_raw]
Q = [x[0] for x in Q_raw]
print(I[:2])
print(f"Fetched {len(I)} shots.")
print("First 10 I:", I[:10])
print("First 10 Q:", Q[:10])

#phis = np.arctan2(I, Q)
phis = np.arctan2(Q, I)

plt.plot(phis, label="Arctan")
plt.plot(I, label="I")
plt.plot(Q, label="Q")
plt.legend()
plt.show

#Phase drift measurement Addition-Anthony
#Question for hal about whether or not unwrapping fucks this. 
phis = np.arctan2(Q, I)
phis_unwrapped = np.unwrap(phis)
phase_drift = np.diff(phis_unwrapped)

plt.figure()
plt.plot(time_drift, phase_drift)
plt.xlabel("Time")
plt.ylabel("Phase drift (rad)")
plt.title("Consecutive Phase Drift")
plt.show()
