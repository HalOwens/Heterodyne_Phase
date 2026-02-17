
# Single QUA script generated at 2026-02-16 17:42:29.906343
# QUA library version: 1.2.4


from qm import CompilerOptionArguments
from qm.qua import *

with program() as prog:
    v1 = declare(int, )
    v2 = declare(fixed, )
    v3 = declare(fixed, )
    update_frequency("lf_in1_iq", 10000000, "Hz", False)
    with for_(v1,0,(v1<100000),(v1+1)):
        reset_if_phase("lf_in1_iq")
        align("Aom1", "Aom2", "lf_in1_iq")
        play("cw", "Aom1")
        play("cw", "Aom2")
        measure("readout", "lf_in1_iq", demod.full("cos", v2, "out1"), demod.full("sin", v3, "out1"))
        r1 = declare_stream()
        save(v2, r1)
        r2 = declare_stream()
        save(v3, r2)
        wait(100, )
    with stream_processing():
        r1.save_all("I")
        r2.save_all("Q")

config = {
    "controllers": {
        "con1": {
            "type": "opx1000",
            "fems": {
                "1": {
                    "type": "LF",
                    "analog_outputs": {
                        "3": {
                            "offset": 0.0,
                            "delay": 0,
                            "output_mode": "direct",
                            "sampling_rate": 1000000000,
                            "upsampling_mode": "pulse",
                        },
                        "7": {
                            "offset": 0.0,
                            "delay": 0,
                            "output_mode": "direct",
                            "sampling_rate": 1000000000,
                            "upsampling_mode": "pulse",
                        },
                    },
                    "digital_outputs": {},
                    "analog_inputs": {
                        "1": {
                            "offset": 0.0,
                            "sampling_rate": 1000000000,
                        },
                    },
                },
            },
        },
    },
    "elements": {
        "Aom1": {
            "singleInput": {
                "port": ('con1', 1, 3),
            },
            "intermediate_frequency": 80000000,
            "operations": {
                "cw": "ref_cw",
            },
        },
        "Aom2": {
            "singleInput": {
                "port": ('con1', 1, 7),
            },
            "intermediate_frequency": 85000000,
            "operations": {
                "cw": "ref_cw",
            },
        },
        "lf_in1_iq": {
            "outputs": {
                "out1": ('con1', 1, 1),
            },
            "intermediate_frequency": 0,
            "time_of_flight": 28,
            "operations": {
                "readout": "in1_readout",
            },
        },
    },
    "pulses": {
        "ref_cw": {
            "operation": "control",
            "length": 1000,
            "waveforms": {
                "single": "ref_vpk",
            },
        },
        "in1_readout": {
            "operation": "measurement",
            "length": 1000,
            "integration_weights": {
                "cos": "cos_w",
                "sin": "sin_w",
            },
        },
    },
    "waveforms": {
        "ref_vpk": {
            "type": "constant",
            "sample": 0.5,
        },
    },
    "integration_weights": {
        "cos_w": {
            "cosine": [(1.0, 1000)],
            "sine": [(0.0, 1000)],
        },
        "sin_w": {
            "cosine": [(0.0, 1000)],
            "sine": [(1.0, 1000)],
        },
    },
}

loaded_config = None


