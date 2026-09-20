# PPG Signal Simulator

An embedded PPG signal simulation and analysis platform for **heart-rate estimation and experimental SpO₂ estimation** using RED/IR signals on the **ESP32-S3**.

## Overview

This project implements an embedded signal-processing pipeline for working with photoplethysmography (PPG) data.

The system can replay or process PPG data, separate DC and AC components, filter the signal, estimate heart rate, and use RED/IR signal characteristics for experimental SpO₂ estimation.

The project is designed as an **engineering and research prototype** for exploring physiological signal processing and embedded implementation.

> **Note:** This project is not a medical device and the SpO₂ estimation is experimental. It is not intended for clinical diagnosis or medical decision-making.

---

## Key Features

* PPG signal replay and simulation
* RED and IR signal processing
* 500 Hz sample-rate data processing
* DC component tracking
* AC component extraction
* Low-pass filtering
* Heart-rate estimation
* RED/IR ratio-of-ratios calculation
* Experimental SpO₂ estimation
* Moving-average smoothing
* Real-time waveform buffering
* ESP32-S3 embedded implementation
* UART data streaming
* GLCD waveform visualization
* Proteus-based simulation
* Reproducible signal-processing workflow

---

## System Architecture

```text
                 PPG DATA
                    │
                    ▼
          ┌───────────────────┐
          │   RED / IR Input  │
          └─────────┬─────────┘
                    │
                    ▼
          ┌───────────────────┐
          │  DC Tracking      │
          │  AC Extraction    │
          │  Filtering        │
          └─────────┬─────────┘
                    │
              ┌─────┴─────┐
              │           │
              ▼           ▼
        Heart Rate      RED / IR
        Estimation      Analysis
              │           │
              │           ▼
              │     Ratio-of-Ratios
              │           │
              │           ▼
              │    Experimental
              │      SpO₂
              │           │
              └─────┬─────┘
                    │
                    ▼
          ┌───────────────────┐
          │    ESP32-S3       │
          │ Signal Processing │
          └─────────┬─────────┘
                    │
             ┌──────┴──────┐
             ▼             ▼
           GLCD           UART
         Waveform      Data Output
```

---

## Signal Processing Pipeline

The processing chain is based on the following stages:

```text
Raw PPG
   │
   ▼
DC Tracking
   │
   ▼
AC Extraction
   │
   ▼
Low-Pass Filtering
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
Experimental SpO₂ Estimation
```

### DC and AC Components

The PPG signal contains a relatively slow-varying DC component and a pulsatile AC component associated with cardiac activity.

The implementation tracks the DC level and extracts the pulsatile component for further analysis.

### Heart Rate

The processed PPG waveform is analyzed to estimate the cardiac pulse rate.

The resulting heart rate is expressed in:

```text
BPM (beats per minute)
```

### SpO₂

RED and IR PPG information is used to calculate a ratio-of-ratios:

```text
R = (AC_red / DC_red) / (AC_IR / DC_IR)
```

This value is then used for experimental SpO₂ estimation.

The current implementation should be considered a **signal-processing demonstration rather than a clinically calibrated SpO₂ measurement system**.

---

## Hardware

The embedded implementation is based on:

* **ESP32-S3**
* GLCD display
* UART communication
* RED/IR PPG data
* Embedded signal-processing pipeline

The system can also be evaluated using a **Proteus simulation environment**.

---

## Data Processing

The project supports processing of PPG data at a sampling rate of:

```text
500 Hz
```

The implementation uses buffered signal processing for waveform analysis and visualization.

Example processing components include:

```text
Sampling
   ↓
Buffering
   ↓
DC estimation
   ↓
AC extraction
   ↓
Filtering
   ↓
Feature extraction
   ↓
HR / SpO₂ estimation
```

---

## Communication

The embedded system supports UART-based data streaming.

Current communication parameters include:

```text
Baud rate: 115200
```

The data pipeline uses buffered frames for transferring PPG samples between the data source and embedded processing system.

---

## Visualization

The processed waveform can be displayed on a GLCD for real-time observation.

The display is intended to provide visual feedback of:

* PPG waveform
* Pulsatile signal behavior
* Signal processing output
* Heart-rate related waveform characteristics

---

## Demo

A demonstration video showing the PPG/SpO₂ processing pipeline will be included in the repository.

**Demo:** `demo/SPO2.mp4`

The demo illustrates the embedded processing and visualization of the PPG signal and experimental SpO₂ estimation.

---

## Validation

Validation is being performed using controlled PPG data and known signal conditions.

Planned validation includes:

| Test       | Reference | Estimated | Error |
| ---------- | --------: | --------: | ----: |
| Heart Rate |    60 BPM |       TBD |   TBD |
| Heart Rate |    75 BPM |       TBD |   TBD |
| Heart Rate |    90 BPM |       TBD |   TBD |
| Heart Rate |   120 BPM |       TBD |   TBD |
| SpO₂       |       95% |       TBD |   TBD |
| SpO₂       |       92% |       TBD |   TBD |
| SpO₂       |       90% |       TBD |   TBD |

Additional testing will evaluate:

* Signal noise
* Baseline drift
* Signal amplitude
* Filtering behavior
* Heart-rate stability
* RED/IR signal variation

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
│   └── ...
│
├── data/
│   └── ...
│
├── proteus/
│   └── ...
│
├── docs/
│   └── ...
│
├── images/
│   └── ...
│
└── demo/
    └── SPO2.mp4
```

---

## Current Development Status

The project is currently an **engineering/research prototype**.

### Implemented

* PPG signal processing
* RED/IR processing
* DC tracking
* AC extraction
* Filtering
* Heart-rate estimation
* Experimental SpO₂ calculation
* ESP32-S3 implementation
* UART communication
* GLCD visualization
* Proteus simulation

### In Progress

* Quantitative validation
* Signal-quality metrics
* Additional test scenarios
* Documentation
* Performance evaluation

---

## Limitations

This project has several important limitations:

1. The SpO₂ algorithm is experimental and has not been clinically validated.
2. The system is not intended for medical diagnosis.
3. Measurement accuracy depends on the quality and characteristics of the input PPG data.
4. Motion artifacts, noise, sensor characteristics, and calibration can affect the results.
5. Further validation is required before any medical or clinical application could be considered.

---

## Future Work

Planned improvements include:

* Automated signal-quality assessment
* More robust peak detection
* Motion-artifact handling
* Additional filtering methods
* Quantitative HR validation
* SpO₂ calibration and validation
* Automated test datasets
* Extended visualization
* Performance benchmarking on ESP32-S3

---

## License

This project is released under the **MIT License**.

See the [`LICENSE`](LICENSE) file for details.

---

## Disclaimer

This repository is provided for **research, educational, and engineering purposes**.

It is not a medical device and should not be used for diagnosis, treatment, or medical decision-making.
