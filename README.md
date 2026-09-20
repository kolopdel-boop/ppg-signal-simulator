# PPG Signal Simulator

An embedded PPG signal simulation and analysis platform for **heart-rate estimation and experimental SpO₂ estimation** using RED/IR signals on the **ESP32-S3**.

## Overview

This project implements an embedded signal-processing workflow for replaying and analyzing photoplethysmography (PPG) data.

The system processes RED and IR PPG signals, separates DC and AC components, applies signal filtering, estimates heart rate, calculates a RED/IR ratio-of-ratios, and performs experimental SpO₂ estimation.

The project is intended as an **engineering and research prototype** for exploring physiological signal processing, embedded implementation, serial data transfer, and Proteus-based simulation.

> **Important:** This project is not a medical device. The SpO₂ algorithm is experimental and has not been clinically validated. The results must not be used for diagnosis, treatment, or medical decision-making.

---

## Key Features

* PPG signal replay and simulation
* RED and IR signal processing
* 500 Hz input data
* DC component tracking
* AC component extraction
* Signal filtering
* Heart-rate estimation
* RED/IR ratio-of-ratios calculation
* Experimental SpO₂ estimation
* Moving-average smoothing
* Real-time waveform buffering
* ESP32-S3 embedded implementation
* UART communication at 115200 baud
* GLCD waveform visualization
* Proteus simulation
* Reproducible serial PPG replay workflow

---

## System Architecture

```text
                  PPG DATA
                     │
                     ▼
             ┌───────────────┐
             │   RED / IR    │
             │     Input     │
             └───────┬───────┘
                     │
                     ▼
             ┌───────────────┐
             │ DC Tracking   │
             │ AC Extraction │
             │   Filtering   │
             └───────┬───────┘
                     │
               ┌─────┴─────┐
               │           │
               ▼           ▼
          Heart Rate    RED / IR
          Estimation    Analysis
               │           │
               │           ▼
               │     Ratio-of-Ratios
               │           │
               │           ▼
               │   Experimental SpO₂
               │           │
               └─────┬─────┘
                     │
                     ▼
             ┌───────────────┐
             │   ESP32-S3    │
             │    Processing │
             └───────┬───────┘
                     │
                ┌────┴────┐
                ▼         ▼
              GLCD       UART
            Waveform   Data Output
```

---

## Signal Processing Pipeline

The embedded processing chain follows these main stages:

```text
Raw RED / IR PPG
       │
       ▼
   DC Tracking
       │
       ▼
  AC Extraction
       │
       ▼
    Filtering
       │
       ├──────────────► Heart Rate Estimation
       │
       ▼
   RED / IR Analysis
       │
       ▼
  Ratio-of-Ratios
       │
       ▼
Experimental SpO₂
```

### DC and AC Components

PPG signals contain a slowly varying DC component and a pulsatile AC component associated with cardiac activity.

The implementation tracks the DC level and extracts the pulsatile component for subsequent signal analysis.

### Heart Rate

The processed PPG waveform is analyzed using peak-based pulse detection.

The resulting heart-rate estimate is expressed in:

```text
BPM — beats per minute
```

### SpO₂

The RED and IR signals are used to calculate a ratio-of-ratios:

```text
R = (AC_red / DC_red) / (AC_IR / DC_IR)
```

The resulting ratio is then used by the current experimental SpO₂ estimation algorithm.

The current implementation is intended for **signal-processing experimentation**, not calibrated clinical measurement.

---

## Embedded Implementation

The firmware is implemented for the **ESP32-S3** and includes:

* PPG signal processing
* RED/IR envelope processing
* DC and AC extraction
* Filtering
* Peak detection
* Heart-rate estimation
* Ratio-of-ratios calculation
* Experimental SpO₂ estimation
* Moving-average smoothing
* GLCD waveform display
* UART communication

The current firmware is provided in:

```text
firmware/main.py
```

---

## Data Replay

The repository includes a portable Python utility for replaying RED/IR PPG data over a serial connection:

```text
tools/serial_replay_ppg.py
```

The replay tool does not depend on a hard-coded local dataset path or serial-port configuration.

Usage:

```bash
py tools/serial_replay_ppg.py --csv "<path-to-csv>" --port COM11
```

For example:

```bash
py tools/serial_replay_ppg.py --csv "C:\path\to\s1_sit_40s.csv" --port COM11
```

The CSV input is expected to contain:

```text
pleth_1
pleth_2
```

where:

* `pleth_1` is used as the RED signal
* `pleth_2` is used as the IR signal

The replay utility transfers the samples as buffered RED/IR frames to the embedded simulation environment.

### Python Dependency

The replay utility requires `pyserial`.

Install it with:

```bash
py -m pip install pyserial
```

---

## Communication

The current serial communication configuration is:

```text
Baud rate:       115200
Sample rate:     500 Hz
Frame size:      128 samples
Bytes per sample: 8
```

Each sample contains:

```text
4 bytes — RED
4 bytes — IR
```

The replay utility communicates with the embedded/Proteus environment using buffered frames and waits for the corresponding frame acknowledgment.

---

## Hardware

The embedded implementation is based on:

* ESP32-S3
* GLCD display
* UART interface
* RED/IR PPG data
* Embedded signal-processing pipeline

The processing workflow can also be evaluated using the included **Proteus simulation project**.

---

## Proteus Simulation

The Proteus project is provided in:

```text
proteus/SpO2_Project.pdsprj
```

A reference image of the simulation environment is also included:

```text
proteus/SpO2_Project.png
```

The Proteus environment can be used to observe the embedded processing workflow and the interaction between the serial PPG replay utility and the simulated system.

---

## Visualization

The GLCD interface provides visual feedback of the processed PPG waveform and related signal-processing output.

The visualization is intended for engineering observation and debugging, including:

* PPG waveform behavior
* Pulsatile signal activity
* Processed signal characteristics
* Heart-rate related waveform behavior
* SpO₂ processing output

---

## Demo

A demonstration video is included in the repository:

**[Open the PPG/SpO₂ demonstration video](demo/SPO2_GitHub_Demo.mp4)**

The demo shows the embedded PPG processing and visualization workflow using the simulated/replayed signal data.

---

## Reproducibility

A typical demonstration workflow is:

```text
1. Open the Proteus project
        │
        ▼
2. Start the Proteus simulation
        │
        ▼
3. Prepare a RED/IR PPG CSV dataset
        │
        ▼
4. Run the serial replay utility
        │
        ▼
5. Stream PPG frames through UART
        │
        ▼
6. Observe waveform and processing output
        │
        ▼
7. Review HR and experimental SpO₂ results
```

Example:

```bash
py tools/serial_replay_ppg.py --csv "<your-csv-file>" --port COM11
```

The dataset itself is **not included in this repository**. Users should provide their own compatible RED/IR PPG CSV data.

---

## Validation and Testing

The project has been tested as an engineering prototype using replayed RED/IR PPG data and the Proteus simulation environment.

A current replay test successfully transferred:

```text
20,000 RED/IR samples
```

through the serial replay workflow.

The project does **not** claim clinical validation or medical accuracy.

Future quantitative testing can include:

| Test Category | Reference Condition | Result |
| ------------- | ------------------: | -----: |
| Heart Rate    |              60 BPM |    TBD |
| Heart Rate    |              75 BPM |    TBD |
| Heart Rate    |              90 BPM |    TBD |
| Heart Rate    |             120 BPM |    TBD |
| SpO₂          |                 95% |    TBD |
| SpO₂          |                 92% |    TBD |
| SpO₂          |                 90% |    TBD |

Additional engineering tests may evaluate:

* Signal noise
* Baseline drift
* Signal amplitude
* Filtering behavior
* Peak-detection stability
* Heart-rate stability
* RED/IR signal variation
* Serial communication reliability

These test cases represent **planned quantitative evaluation**, not completed clinical validation results.

---

## Repository Structure

```text
ppg-signal-simulator/
│
├── README.md
├── LICENSE
├── .gitignore
│
├── firmware/
│   └── main.py
│
├── tools/
│   └── serial_replay_ppg.py
│
├── proteus/
│   ├── SpO2_Project.pdsprj
│   └── SpO2_Project.png
│
└── demo/
    └── SPO2_GitHub_Demo.mp4
```

---

## Current Development Status

The project is currently an **engineering/research prototype**.

### Implemented

* PPG signal replay
* RED/IR processing
* DC tracking
* AC extraction
* Signal filtering
* Heart-rate estimation
* Experimental SpO₂ calculation
* ESP32-S3 implementation
* UART communication
* GLCD visualization
* Proteus simulation
* Portable serial replay utility
* GitHub-based project structure

### In Progress

* Quantitative signal validation
* Signal-quality metrics
* Additional test scenarios
* Performance benchmarking
* Extended documentation
* Additional replay datasets

---

## Limitations

This project has several important limitations:

1. The SpO₂ algorithm is experimental and has not been clinically validated.
2. The system is not intended for medical diagnosis or treatment.
3. Accuracy depends on the quality and characteristics of the input PPG data.
4. Motion artifacts, noise, sensor characteristics, and calibration can affect the results.
5. The current SpO₂ mapping is intended as an experimental signal-processing implementation.
6. Further quantitative and clinical-grade validation would be required for any medical application.

---

## Future Work

Potential future improvements include:

* Automated signal-quality assessment
* More robust peak detection
* Motion-artifact handling
* Additional filtering methods
* Quantitative HR validation
* Improved SpO₂ calibration methodology
* Automated test datasets
* Extended visualization
* Performance benchmarking on ESP32-S3
* Automated replay and regression testing

---

## License

This project is released under the **MIT License**.

See the [`LICENSE`](LICENSE) file for details.

---

## Disclaimer

This repository is provided for **research, educational, and engineering purposes**.

It is not a medical device and should not be used for diagnosis, treatment, or medical decision-making.

The experimental SpO₂ output is not a clinically validated measurement and should not be interpreted as a medical-grade oxygen saturation reading.
