from qualang_tools.units import unit
u = unit(coerce_to_integer=True)

######################
# Network parameters #
######################
qop_ip = "192.168.88.249"# Write the OPX IP address
cluster_name = "Cluster"  # Write your cluster_name if version >= QOP220

#####################
# OPX configuration #
#####################
mw_fem = 2  # This should be the index of the LF-FEM module, e.g., 1
lf_fem = 1  # This should be the index of the LF-FEM module, e.g., 1
con = "con1"
# Frequencies
# TODO How can I change this?
sampling_rate = int(1e9)  # or, int(2e9)
LO_freq = 2.83 * u.GHz
mw_delay = 0 * u.ns


wait_between_runs = 100

config = {
    "version": 1,
    "controllers": {
        con: {
            "type": "opx1000",
            "fems": {
                lf_fem: {
                    "type": "LF",
                    "analog_outputs": {
                        # Output 1 → Oscilloscope
                        1: {
                            "offset": 0.0,
                            "delay": mw_delay,
                            "output_mode": "direct",       # 1 Vpp (-0.5 V → 0.5 V)
                            "sampling_rate": sampling_rate,
                            "upsampling_mode": "pulse",    # unmodulated DC/slow tones → cleaner steps
                        },
                        # Output 8 → wired into Input 1
                        8: {
                            "offset": 0.0,
                            "delay": mw_delay,
                            "output_mode": "direct",
                            "sampling_rate": sampling_rate,
                            "upsampling_mode": "pulse",
                        },
                    },
                    "digital_outputs": {1: {}},
                    "analog_inputs": {
                        1: {
                            "offset": 0,
                            "gain_db": 3,
                            "sampling_rate": sampling_rate,
                        },
                    },
                },
                mw_fem: {
                    # The keyword "band" refers to the following frequency bands:
                    #   1: (50 MHz - 5.5 GHz)
                    #   2: (4.5 GHz - 7.5 GHz)
                    #   3: (6.5 GHz - 10.5 GHz)
                    # Note that the "coupled" ports O1 & I1, O2 & O3, O4 & O5, O6 & O7, and O8 & I2
                    # must be in the same band.
                    # MW-FEM outputs are delayed with respect to the LF-FEM outputs by 141ns for bands 1 and 3 and 161ns for band 2.
                    # The keyword "full_scale_power_dbm" is the maximum power of
                    # normalized pulse waveforms in [-1,1]. To convert to voltage,
                    #   power_mw = 10**(full_scale_power_dbm / 10)
                    #   max_voltage_amp = np.sqrt(2 * power_mw * 50 / 1000)
                    #   amp_in_volts = waveform * max_voltage_amp
                    #   ^ equivalent to OPX+ amp
                    # Its range is -11dBm to +16dBm with 3dBm steps.
                    "type": "MW",
                    "analog_outputs": {
                        4: {
                            "band": 1,
                            "full_scale_power_dbm": 7,
                            "upconverters": {1: {"frequency": LO_freq}},
                        },  # NV
                        8: {
                            "band": 1,
                            "full_scale_power_dbm": 7,
                            "upconverters": {1: {"frequency": LO_freq}},
                        },
                    },

                    "digital_outputs": {},
                    "analog_inputs": {
                    },
                },
            },
        }
    },
    "elements": {
        "snspd": {
            "outputs": {"out1": (con, lf_fem, 1)},  # ADC In1 sees SNSPD pulses (via your room-temp chain)
            "digitalInputs": {
                "marker": {
                    "port": (con, lf_fem, 1),
                    "delay": 0,
                    "buffer": 0,
                }
            },
            "operations": {"readout": "snspd_readout"},
            "time_of_flight": 28 * u.ns,
            "smearing": 0,
            "outputPulseParameters": {
                "signalThreshold": -0.10,  # Volts; set to your SNSPD pulse level (negative or positive)
                "signalPolarity": "Below",  # "Below" for negative pulses, "Above" for positive
                'derivativeThreshold': -10000,  # in ADC units / ns (OPX+)
                'derivativePolarity': 'Above'
            },
        },
        "lf_out1": {
            "singleInput": {"port": (con, lf_fem, 1)},  # controller, FEM index, port number
            "intermediate_frequency": 1000 * u.kHz,  # the tone’s digital IF
            "operations": {
                "cw": "const_pulse_lf",  # points to the pulse defined below
            },
        },
        "lf_out8": {
            "singleInput": {"port": (con, lf_fem, 8)},
            "intermediate_frequency": 1000 * u.kHz,
            "operations": {
                "cw": "const_pulse_lf",
            },
        },
        "lf_in1": {
            "outputs": {"out1": (con, lf_fem, 1)},  # ADC In 1
            "digitalInputs": {
                "marker": {
                    "port": (con, lf_fem, 1),  # matches the DO you enabled above
                    "delay": 0,
                    "buffer": 0,
                }
            },
            "time_of_flight": 32 * u.ns,
            "smearing": 0,
            "operations": {
                "readout": "readout_pulse",
            },
        },
        "qubit": {
            "MWInput": {
                "port": (con, mw_fem, 4),
                "upconverter": 1,
            },
            "intermediate_frequency": 1 * u.MHz,
            "operations": {"cw": "const_pulse"}
        },
    },
    "pulses": {
        "const_pulse": {
            "operation": "control",
            "length": 4000,
            "waveforms": {
                "I": "const_wf",
                "Q": "zero_wf",
            },
        },
        "const_pulse_lf": {
            "operation": "control",
            "length": 4e3,
            "waveforms": {
                "single": "const_wf"
            },
        },
        "readout_pulse": {
            "operation": "measurement",
            "length": 1e7,
            "digital_marker": "ON"
        },
        "snspd_readout": {
            "operation": "measurement",
            "length": 100_000_000,  # 100 ms window; use multiple windows back-to-back
            "digital_marker": "ON",  # REQUIRED to gate time-tag acquisition
        },
    },
    "waveforms": {
        "const_wf": {"type": "constant", "sample": .5},
        "zero_wf": {"type": "constant", "sample": 0.0}
    },
    "digital_waveforms": {
        "ON":  {"samples": [(1, 0)]},
        "OFF": {"samples": [(0, 0)]},
    },
}