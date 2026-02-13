"""
rate_count.py

Measures click/event rate from an SNSPD (or similar) by repeating time-tagging over
multiple windows, streaming counts per window and raw (in-window) timestamps.

This version avoids two common QUA pitfalls:
1) `qua.save()` may not accept arithmetic expressions like (times[i] + k*WIN_LEN_NS).
2) QUA `int` is typically 32-bit, so "absolute timestamps in ns" can overflow quickly.

Instead, we:
- stream `n_per_win` (counts per window)
- stream `t_in_win` (timestamps within each window, as returned by your API)
- reconstruct absolute timestamps on the host with int64
"""

import numpy as np
import qm.qua as qua
from qm import QuantumMachinesManager
from Phase_Measure.config_lf_mw_fem import config, qop_ip, cluster_name

# -----------------------------
# User parameters
# -----------------------------
WIN_LEN_NS = 1_000_000_000   # 1 s tagging window (good for 1–5 Hz)
MEAS_DURATION_S = 8          # total measurement time in seconds
MAX_TAGS = 64                # max timestamps per window to keep

# If your QUA time tags are in clock cycles (CC) rather than ns, set these:
TAGS_ARE_CLOCK_CYCLES = False
CLOCK_PERIOD_NS = 4          # only used if TAGS_ARE_CLOCK_CYCLES=True

# -----------------------------
# Derived parameters
# -----------------------------
N_WINDOWS = int(np.ceil(MEAS_DURATION_S * 1e9 / WIN_LEN_NS))

# -----------------------------
# QUA program
# -----------------------------
with qua.program() as click_rate_prog:
    times = qua.declare(int, size=MAX_TAGS)  # in-window timestamps
    n_tags = qua.declare(int)                # count in this window
    i = qua.declare(int)                     # tag index
    k = qua.declare(int)                     # window index

    n_st = qua.declare_stream()              # counts per window
    t_st = qua.declare_stream()              # flattened in-window timestamps

    qua.align("snspd")

    with qua.for_(k, 0, k < N_WINDOWS, k + 1):
        # Tag events over the window
        qua.measure(
            "readout",
            "snspd",
            qua.time_tagging.analog(times, WIN_LEN_NS, n_tags),
        )

        # Stream the count for this window
        qua.save(n_tags, n_st)

        # Stream exactly n_tags timestamps from this window (raw, in-window)
        with qua.for_(i, 0, i < n_tags, i + 1):
            qua.save(times[i], t_st)

        # NOTE:
        # Usually, the time_tagging.measure occupies the full WIN_LEN_NS window.
        # If you find the loop runs "too fast" (i.e., not actually integrating over WIN_LEN_NS),
        # you may need an explicit wait here depending on your setup/element timing model.
        # Do NOT add it blindly without verifying your element clock unit:
        #
        # qua.wait(int(WIN_LEN_NS / 4), "snspd")  # example if 4 ns ticks

    with qua.stream_processing():
        n_st.save_all("n_per_win")
        t_st.save_all("t_in_win")


# -----------------------------
# Run & fetch
# -----------------------------
qmm = QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name)
qm = qmm.open_qm(config)
job = qm.execute(click_rate_prog)

res = job.result_handles
res.wait_for_all_values()

n_per_win = np.array(res.get("n_per_win").fetch_all(), dtype=int)
t_in_win = np.array(res.get("t_in_win").fetch_all(), dtype=np.int64)

# -----------------------------
# Unit handling
# -----------------------------
# We reconstruct absolute timestamps on the host:
# abs_t = t_in_win + window_index * WIN_LEN
#
# But we need per-window grouping. `t_in_win` is a flat stream containing all timestamps
# from window 0, then all from window 1, etc. We use n_per_win to slice it.

if TAGS_ARE_CLOCK_CYCLES:
    # Convert everything to ns for reporting on host
    t_in_win_ns = t_in_win * CLOCK_PERIOD_NS
    win_len_ns_for_abs = WIN_LEN_NS
else:
    t_in_win_ns = t_in_win
    win_len_ns_for_abs = WIN_LEN_NS

# Rebuild absolute timestamps as int64 (safe for long durations)
abs_ts_ns_chunks = []
idx = 0
for k, n in enumerate(n_per_win):
    if n <= 0:
        continue
    ts_chunk = t_in_win_ns[idx: idx + n]
    abs_ts_ns_chunks.append(ts_chunk + np.int64(k) * np.int64(win_len_ns_for_abs))
    idx += n

abs_ts_ns = np.concatenate(abs_ts_ns_chunks) if abs_ts_ns_chunks else np.array([], dtype=np.int64)

# -----------------------------
# Rate calculations
# -----------------------------
win_s = WIN_LEN_NS * 1e-9
rates_hz = n_per_win / win_s

total_time_s = len(n_per_win) * win_s
total_events = int(n_per_win.sum())
overall_rate_hz = total_events / total_time_s if total_time_s > 0 else float("nan")

print(f"Window length: {win_s:.3f} s")
print(f"Windows: {len(n_per_win)}")
print(f"Total time: {total_time_s:.3f} s")
print("Counts per window:", n_per_win.tolist())
print("Rates per window (Hz):", rates_hz.tolist())
print(f"Total events: {total_events}")
print(f"Overall rate: {overall_rate_hz:.6f} Hz")

# Inter-click interval stats (often more meaningful at low Hz)
if abs_ts_ns.size >= 2:
    abs_ts_ns_sorted = np.sort(abs_ts_ns)
    dt_s = np.diff(abs_ts_ns_sorted) * 1e-9

    print(f"Median inter-click interval: {np.median(dt_s):.6f} s")
    print(f"Mean inter-click interval:   {np.mean(dt_s):.6f} s")

    inst_rate_hz = 1.0 / dt_s
    print(f"Median instantaneous rate:   {np.median(inst_rate_hz):.6f} Hz")
else:
    print("Not enough timestamps to compute inter-click intervals.")

# Optional: print timestamps (can be large)
print("All absolute timestamps (ns):", abs_ts_ns.tolist())
