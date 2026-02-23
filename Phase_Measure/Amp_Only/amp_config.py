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
# Readout configuration  #
#########################
READOUT_LEN = 50000  # clock cycles (at 1 GHz => 2 us). Adjust as needed.

#########################
# RF amplitude note      #
#########################
REF_VPK = 0.5  # Volts peak (max in direct mode)

config = {
    "controllers": {
        con: {
            "type": "opx1000",
            "fems": {
                lf_fem: {
                    "type": "LF",
                    "analog_outputs": {
                        # Ref outputs only (AO3 and AO7). AO1 removed (was for aom_fm_ctrl_out1).
                        3: {
                            "offset": 0.0,
                            "delay": 0,
                            "output_mode": "direct",       # 1 Vpp range: -0.5..+0.5 V
                            "sampling_rate": sampling_rate,
                            "upsampling_mode": "pulse",
                        },
                        7: {
                            "offset": 0.0,
                            "delay": 0,
                            "output_mode": "direct",       # 1 Vpp range: -0.5..+0.5 V
                            "sampling_rate": sampling_rate,
                            "upsampling_mode": "pulse",
                        },
                    },
                    "digital_outputs": {},
                    "analog_inputs": {
                        # Keep AI1 for IQ demod / readout
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
        # Reference outputs:
        "Aom1": {
            "singleInput": {"port": (con, lf_fem, 3)},
            "intermediate_frequency": 80 * u.MHz,
            "operations": {"cw": "ref_cw"},
        },
        "Aom2": {
            "singleInput": {"port": (con, lf_fem, 7)},
            "intermediate_frequency": 85 * u.MHz,
            "operations": {"cw": "ref_cw"},
        },

        # LF-FEM analog input 1 IQ demod element (kept from your starting point)
        "lf_in1_iq": {
            "outputs": {"out1": (con, lf_fem, 1)},  # LF-FEM analog input 1
            "intermediate_frequency": 0,           # set in QUA via update_frequency()
            "time_of_flight": 80,
            "operations": {"readout": "in1_readout"},
        },
    },

    "pulses": {
        # Continuous-wave reference: constant envelope -> sine at IF
        "ref_cw": {
            "operation": "control",
            "length": READOUT_LEN,  # clock cycles; set as needed in your program
            "waveforms": {"single": "ref_vpk"},
        },

        # IQ readout pulse on analog input element
        "in1_readout": {
            "operation": "measurement",
            "length": READOUT_LEN,
            "integration_weights": {
                "cos": "cos_w",
                "sin": "sin_w",
            },
        },
    },

    "waveforms": {
        # In direct mode, "sample" is peak voltage. REF_VPK=0.5 V => 1.0 Vpp (max).
        "ref_vpk": {"type": "constant", "sample": REF_VPK},
    },

    "integration_weights": {
        "cos_w": {
            "cosine": [(1.0, READOUT_LEN)],
            "sine":   [(0.0, READOUT_LEN)],
        },
        "sin_w": {
            "cosine": [(0.0, READOUT_LEN)],
            "sine":   [(1.0, READOUT_LEN)],
        },
    },
}
