"""
Minimal OPX1000 LF-FEM config:
- Analog out 3: 10 MHz sine, 1 Vpp (direct mode => ±0.5 V peak)
- Analog out 7: 10 MHz sine, 1 Vpp (direct mode => ±0.5 V peak)
- Analog out 1: FM control voltage (DC step 0 V <-> V_FM_ON) for +5 MHz hop on your AOM driver

Notes:
- In LF "direct" mode, full scale is 1 Vpp (−0.5 V to +0.5 V).
- A 1 Vpp sine corresponds to 0.5 V peak amplitude.
- Set V_FM_ON from your driver calibration: V_FM_ON = 5e6 / K_FM  (K_FM in Hz/Vpeak).
"""

from qualang_tools.units import unit
u = unit(coerce_to_integer=True)

######################
# Network parameters #
######################
qop_ip = "192.168.88.249"
cluster_name = "Cluster"
con = "con1"

#########################
# Hardware identifiers   #
#########################
lf_fem = 1  # LF-FEM module index in the OPX1000

#########################
# Global timing/settings #
#########################
sampling_rate = int(1e9)  # or int(2e9)

#########################
# AOM FM control voltage #
#########################
# Placeholder: you must set this from calibration so that 0 -> V_FM_ON gives +5 MHz shift.
# Keep it within [-0.5, +0.5] V if staying in direct mode.
V_FM_ON = 0.30  # Volts (example only)

config = {
    "version": 1,
    "controllers": {
        con: {
            "type": "opx1000",
            "fems": {
                lf_fem: {
                    "type": "LF",
                    "analog_outputs": {
                        1: {
                            "offset": 0.0,
                            "delay": 0,
                            "output_mode": "direct",       # 1 Vpp range: -0.5..+0.5 V
                            "sampling_rate": sampling_rate,
                            "upsampling_mode": "pulse",
                        },
                        3: {
                            "offset": 0.0,
                            "delay": 0,
                            "output_mode": "direct",       # 1 Vpp range
                            "sampling_rate": sampling_rate,
                            "upsampling_mode": "pulse",
                        },
                        7: {
                            "offset": 0.0,
                            "delay": 0,
                            "output_mode": "direct",       # 1 Vpp range
                            "sampling_rate": sampling_rate,
                            "upsampling_mode": "pulse",
                        },
                    },
                    "digital_outputs": {},
                    "analog_inputs": {
                        1: {
                            "offset": 0.0,
                            "sampling_rate": sampling_rate,
                        },
                    },
                }
            },
        }
    },

    "elements": {
        # 10 MHz, 1 Vpp references (LF single-channel synthesis)
        "ref_out3_10MHz": {
            "singleInput": {"port": (con, lf_fem, 3)},
            "intermediate_frequency": 10 * u.MHz,
            "operations": {"cw": "ref_cw"},
        },
        "ref_out7_10MHz": {
            "singleInput": {"port": (con, lf_fem, 7)},
            "intermediate_frequency": 10 * u.MHz,
            "operations": {"cw": "ref_cw"},
        },
        "lf_in1_iq": {
            "outputs": {"out1": (con, lf_fem, 1)},  # LF-FEM analog input 1
            "intermediate_frequency": 0,           # we will set it in QUA via update_frequency()
            "operations": {"readout": "in1_readout"},
        },

        "aom_fm_ctrl_out1": {
            "singleInput": {"port": (con, lf_fem, 1)},
            "intermediate_frequency": 0,  # DC control
            "operations": {
                "fm_off": "fm_off_pulse",
                "fm_on": "fm_on_pulse",
            },
        },
    },

    "pulses": {
        # Continuous-wave 10 MHz reference: constant envelope -> sine at IF
        "ref_cw": {
            "operation": "control",
            "length": 1000,  # clock cycles; use whatever your program needs
            "waveforms": {"single": "ref_0p5Vpk"},
        },

# in pulses:
        "dc_on": {
            "operation": "control",
            "length": 2000,
            "waveforms": {"single": "dc_0p3V"},
        },
        "in1_readout": {
            "operation": "measurement",
            "length": 2000,
            "integration_weights": {
                "cos": "cos_w",
                "sin": "sin_w",
            },
        },
        "fm_off_pulse": {
            "operation": "control",
            "length": 1000,
            "waveforms": {"single": "dc_0V"},
        },
        "fm_on_pulse": {
            "operation": "control",
            "length": 1000,
            "waveforms": {"single": "dc_V_FM_ON"},
        },
    },

    "waveforms": {
        # 1 Vpp sine in direct mode => 0.5 V peak
        "ref_0p5Vpk": {"type": "constant", "sample": 0.5},

        # in waveforms:
        "dc_0p3V": {"type": "constant", "sample": 0.3},

        # DC levels for FM control
        "dc_0V": {"type": "constant", "sample": 0.0},
        "dc_V_FM_ON": {"type": "constant", "sample": V_FM_ON},
    },
    "integration_weights": {
        "cos_w": {
            "cosine": [(1.0, 2000)],
            "sine":   [(0.0, 2000)],
        },
        "sin_w": {
            "cosine": [(0.0, 2000)],
            "sine":   [(1.0, 2000)],
        },
    },
}
