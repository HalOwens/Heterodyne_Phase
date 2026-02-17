
from qm.qua import *
from qm import QuantumMachinesManager
from phase_config import qop_ip, cluster_name, config
# -------------------------
# User knobs
# -------------------------
DEMOD_FREQ_HZ = 5_000_000   # <---- change this later as needed
N_SHOTS = 10_000            # fixed acquisition count (no infinite loop)

with program() as iq_acquire_in1:
    n = declare(int)

    I = declare(fixed)
    Q = declare(fixed)

    I_st = declare_stream()
    Q_st = declare_stream()

    # Set the demodulation frequency by setting the element IF.
    # This assumes your element "lf_in1_iq" exists and has IF that can be updated.
    update_frequency("lf_in1_iq", DEMOD_FREQ_HZ)

    with for_(n, 0, n < N_SHOTS, n + 1):
        measure(
            "readout",
            "lf_in1_iq",
            None,
            demod.full("cos", I, "out1"),
            demod.full("sin", Q, "out1"),
        )
        save(I, I_st)
        save(Q, Q_st)

    with stream_processing():
        I_st.save_all("I")
        Q_st.save_all("Q")


qmm = QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name)
qm = qmm.open_qm(config)

job = qm.execute(iq_acquire_in1)
res = job.result_handles
res.wait_for_all_values()

I_data = res.get("I").fetch_all()
Q_data = res.get("Q").fetch_all()

print(f"Fetched {len(I_data)} shots.")
print("First 10 I:", I_data[:10])
print("First 10 Q:", Q_data[:10])
