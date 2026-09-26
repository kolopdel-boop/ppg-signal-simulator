# PPG Signal Simulator

Embedded PPG signal replay and processing platform for **heart-rate estimation and experimental SpO₂ estimation** using RED/IR signals on the **ESP32-S3**.

This project combines:

* RED/IR PPG signal replay
* Embedded DSP on ESP32-S3
* DC tracking and AC extraction
* Integer-based signal smoothing
* Peak-based heart-rate estimation
* RED/IR ratio-of-ratios calculation
* Experimental SpO₂ estimation
* UART frame-based data transport
* GLCD waveform visualization
* Proteus-based simulation
* Reproducible engineering test workflows

> **Important:** This project is an engineering/research prototype, not a medical device. The SpO₂ algorithm is experimental and has not been clinically validated. The output must not be used for diagnosis, treatment, or medical decision-making.

---

## 1. Project Overview

The project implements an embedded signal-processing pipeline for replaying and analyzing photoplethysmography (PPG) data.

A Python replay utility reads RED/IR samples from a CSV file and transfers them to an ESP32-S3 over UART using fixed-size binary frames. The ESP32-S3 processes the incoming samples, estimates heart rate, calculates RED/IR AC/DC characteristics, derives a ratio-of-ratios value, and produces an experimental SpO₂ estimate.

The processed waveform and calculated values are displayed on a GLCD and reported through the serial interface.

The project is intended to demonstrate practical work in:

* Biomedical signal processing
* Embedded DSP
* Physiological waveform analysis
* Serial communication
* Embedded visualization
* Signal replay and testing
* ESP32-S3 development
* Proteus simulation

---

## 2. System Architecture

```text
             RED / IR PPG CSV
                    │
                    ▼
        ┌────────────────────────┐
        │  Python Serial Replay  │
        │  serial_replay_ppg.py  │
        └────────────┬───────────┘
                     │
              Binary UART Frames
                     │
                     ▼
        ┌────────────────────────┐
        │       ESP32-S3         │
        │       main.py          │
        └────────────┬───────────┘
                     │
                     ▼
             RED / IR Samples
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
     DC Tracking          AC Extraction
          │                     │
          └──────────┬──────────┘
                     ▼
              Signal Smoothing
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
     Peak Detection        RED / IR Analysis
          │                     │
          ▼                     ▼
    Heart Rate (HR)       Ratio-of-Ratios
                                │
                                ▼
                     Experimental SpO₂
                                │
                         ┌──────┴──────┐
                         ▼             ▼
                        GLCD          UART
```

---

## 3. Key Features

* RED/IR PPG signal replay
* Nominal 500 Hz sample rate
* 128-sample framed UART transport
* 1024-byte binary frame format
* RED/IR processing on ESP32-S3
* Integer DC tracking
* AC component extraction
* Integer-based signal smoothing
* Peak-based heart-rate estimation
* RR-interval averaging
* RED/IR AC/DC analysis
* Ratio-of-ratios calculation
* Experimental SpO₂ mapping
* 8-sample SpO₂ moving average
* 512-sample waveform buffer
* GLCD waveform visualization
* UART frame acknowledgment
* Proteus simulation support
* Python/pyserial replay utility

---

## 4. Signal Processing Pipeline

The embedded processing chain is:

```text
Raw RED / IR
     │
     ▼
DC Tracking
     │
     ▼
AC Extraction
     │
     ▼
Integer Smoothing
     │
     ├──────────────► Peak Detection ──► HR Estimation
     │
     ▼
RED / IR AC + DC Analysis
     │
     ▼
Ratio-of-Ratios
     │
     ▼
Experimental SpO₂
```

### 4.1 DC Tracking

The firmware maintains a slowly varying estimate of the DC component.

For RED:

```text
red_dc += (red_raw - red_dc) / 128
```

The implementation uses integer arithmetic:

```python
red_dc += (red_raw - red_dc) // 128
```

The same method is applied to the IR signal.

---

### 4.2 AC Extraction

The pulsatile component is obtained by subtracting the tracked DC level:

```text
AC = raw_signal - DC
```

This produces the signal used for subsequent waveform analysis.

---

### 4.3 Signal Smoothing

The extracted AC signal is smoothed using an integer first-order update:

```text
filtered += (AC - filtered) / 8
```

The firmware implements this using integer arithmetic:

```python
filtered += (AC - filtered) // 8
```

This provides a lightweight embedded smoothing stage without floating-point filtering.

---

## 5. Heart-Rate Estimation

Heart rate is estimated from the filtered RED PPG waveform using peak-based pulse detection.

The current implementation uses:

```text
Sampling rate:          500 Hz
Minimum peak distance:  0.50 s
Maximum RR interval:    2.00 s
Peak threshold:         40
RR history:             5 intervals
```

The detected RR intervals are averaged and converted to BPM:

```text
HR = 60 × Fs / average_RR
```

The current firmware limits the reported HR range to approximately:

```text
40–180 BPM
```

The implementation is intended for engineering experimentation and is not a clinically validated heart-rate algorithm.

---

## 6. RED/IR AC and DC Analysis

For each completed input frame, the firmware tracks RED and IR peak/valley values and calculates frame-local AC amplitudes:

```text
RED_AC = RED_peak - RED_valley

IR_AC = IR_peak - IR_valley
```

The corresponding DC values are obtained from the continuously tracked RED and IR baselines.

These values are then used for the ratio-of-ratios calculation.

---

## 7. Ratio-of-Ratios

The current implementation calculates:

```text
R = (RED_AC × IR_DC) /
    (IR_AC × RED_DC)
```

The firmware internally scales the ratio by 1000 for integer arithmetic.

Conceptually, this corresponds to:

```text
R = (RED_AC / RED_DC) /
    (IR_AC / IR_DC)
```

The resulting value is passed to the experimental SpO₂ mapping.

---

## 8. Experimental SpO₂ Estimation

The current prototype uses the following experimental mapping:

```text
SpO₂ = 110 − 25 × R
```

The implementation applies integer scaling internally and limits the displayed result to a range of approximately:

```text
70–100 %
```

An 8-sample moving average is then applied to the calculated SpO₂ values before display.

### Important

This equation is an **experimental/demo calibration model**.

It is not a clinically derived or clinically validated calibration curve.

The resulting SpO₂ value must therefore be interpreted only as an experimental output of the signal-processing pipeline.

---

## 9. Frame-Based AC Measurement

The current firmware processes:

```text
Frame size = 128 samples
Sample rate = 500 Hz
```

Therefore:

```text
128 / 500 = 0.256 seconds
```

Each AC peak-to-valley measurement is currently based on a **256 ms frame-local window**.

This is an important limitation of the current implementation. A 256 ms window does not necessarily contain a complete PPG pulse cycle at ordinary heart rates.

Consequently, frame-local AC measurements may vary depending on the relationship between the frame boundaries and the underlying pulse waveform.

This is one of the areas identified for future quantitative validation and algorithm improvement.

---

## 10. Serial Communication

The host replay utility and ESP32-S3 firmware use the following protocol:

```text
Baud rate:        115200
Nominal sample rate: 500 Hz
Samples/frame:    128
Bytes/sample:     8
Bytes/frame:    1024
```

Each sample contains:

```text
4 bytes — RED
4 bytes — IR
```

The values are transmitted as unsigned 32-bit integers using little-endian byte order.

Conceptually:

```text
Sample 0:
    RED[4] + IR[4]

Sample 1:
    RED[4] + IR[4]

...

Sample 127:
    RED[4] + IR[4]
```

One complete frame therefore contains:

```text
128 × 8 = 1024 bytes
```

After processing a frame, the ESP32-S3 sends:

```text
FRAME_OK\n
```

The replay utility waits for this acknowledgment before continuing.

This provides a simple frame-level synchronization mechanism between the host and embedded system.

---

## 11. PPG Data Replay

The repository includes:

```text
tools/serial_replay_ppg.py
```

The utility reads RED/IR PPG samples from a CSV file.

The expected CSV columns are:

```text
pleth_1
pleth_2
```

The current replay implementation interprets:

```text
pleth_1 → RED
pleth_2 → IR
```

The samples are converted to integer values and transmitted in 128-sample binary frames.

### Current configuration

The current script contains the replay configuration directly in the source:

```text
CSV file
Serial port
Baud rate
Sample rate
Frame size
```

For example, the current development configuration uses:

```text
CSV:
C:\SpO2_Project\s1_sit_40s.csv

Serial port:
COM11

Baud rate:
115200
```

These values are development-machine configuration and may need to be changed for another environment.

---

## 12. Python Dependency

The replay utility requires `pyserial`.

Install it with:

```powershell
py -m pip install pyserial
```

Then configure the CSV path and serial port in:

```text
tools/serial_replay_ppg.py
```

and run:

```powershell
py tools/serial_replay_ppg.py
```

The current implementation sends the final incomplete frame with zero padding so that every transmitted frame remains exactly 128 samples / 1024 bytes.

---

## 13. Embedded Implementation

The ESP32-S3 firmware is located at:

```text
firmware/main.py
```

The firmware includes:

* UART reception
* Binary frame parsing
* RED/IR sample decoding
* DC tracking
* AC extraction
* Signal smoothing
* Peak detection
* RR interval calculation
* Heart-rate estimation
* RED/IR AC/DC analysis
* Ratio-of-ratios calculation
* Experimental SpO₂ estimation
* SpO₂ moving average
* Waveform buffering
* GLCD visualization
* Frame acknowledgment

---

## 14. Waveform Buffer and GLCD

The firmware maintains a waveform buffer containing the most recent:

```text
512 samples
```

The processed waveform is displayed on a 128 × 64 GLCD.

The display provides engineering/debugging feedback including:

* Processed PPG waveform
* Heart-rate estimate
* Experimental SpO₂ estimate

The visualization is intended for development and signal-processing observation rather than medical monitoring.

---

## 15. Proteus Simulation

The repository contains the Proteus project:

```text
proteus/SpO2_Project.pdsprj
```

and a reference image:

```text
proteus/SpO2_Project.png
```

The Proteus environment is used to support development and observation of the embedded system and its interaction with the serial PPG replay workflow.

---

## 16. Demonstration

A demonstration video is included in:

```text
demo/SPO2_GitHub_Demo.mp4
```

The demonstration shows the embedded PPG processing and visualization workflow using replayed signal data.

---

## 17. Reproducible Test Workflow

A typical engineering test sequence is:

```text
1. Prepare RED/IR PPG CSV data
             │
             ▼
2. Configure the replay utility
             │
             ▼
3. Open the Proteus project or connect the ESP32-S3
             │
             ▼
4. Start the embedded system
             │
             ▼
5. Run serial_replay_ppg.py
             │
             ▼
6. Transfer framed RED/IR data
             │
             ▼
7. Receive FRAME_OK acknowledgments
             │
             ▼
8. Observe the GLCD waveform
             │
             ▼
9. Review HR and experimental SpO₂ output
```

The dataset used during development is not included in this repository.

Users should provide a compatible RED/IR PPG CSV dataset.

---

## 18. Validation and Testing

The project has been evaluated as an engineering prototype using replayed RED/IR PPG data and the embedded/Proteus workflow.

A development replay test successfully transferred:

```text
20,000 RED/IR samples
```

through the serial replay workflow.

This demonstrates the operation of the data-replay and framed serial transport path.

It does **not** constitute clinical validation.

### Current validation status

| Test area                             | Current status    |
| ------------------------------------- | ----------------- |
| CSV RED/IR loading                    | Implemented       |
| RED/IR frame construction             | Implemented       |
| 128-sample framing                    | Implemented       |
| UART transfer                         | Implemented       |
| Frame acknowledgment                  | Implemented       |
| ESP32-S3 frame decoding               | Implemented       |
| DC tracking                           | Implemented       |
| AC extraction                         | Implemented       |
| Peak-based HR estimation              | Implemented       |
| Ratio-of-ratios calculation           | Implemented       |
| Experimental SpO₂ mapping             | Implemented       |
| Quantitative HR accuracy validation   | Not yet completed |
| Quantitative SpO₂ accuracy validation | Not yet completed |
| Clinical validation                   | Not performed     |

Future quantitative testing can evaluate:

* Known heart-rate conditions
* Peak-detection accuracy
* RR interval error
* Signal-to-noise effects
* Baseline drift
* RED/IR amplitude variation
* Filtering behavior
* Frame-to-frame stability
* Serial communication reliability
* SpO₂ estimation error against appropriate reference data

---

## 19. Repository Structure

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

## 20. Current Development Status

### Implemented

* PPG signal replay
* RED/IR data processing
* UART framed transport
* Frame acknowledgment
* DC tracking
* AC extraction
* Integer signal smoothing
* Peak-based heart-rate estimation
* RR interval averaging
* RED/IR AC/DC analysis
* Ratio-of-ratios calculation
* Experimental SpO₂ estimation
* SpO₂ moving-average smoothing
* ESP32-S3 implementation
* GLCD waveform visualization
* Proteus project
* Python serial replay utility

### Planned / In Progress

* Quantitative HR validation
* Quantitative SpO₂ evaluation
* Signal-quality metrics
* Robust peak detection
* Motion-artifact handling
* Improved AC measurement windows
* Improved SpO₂ calibration methodology
* Automated replay datasets
* Regression testing
* Performance benchmarking on ESP32-S3
* Extended signal visualization

---

## 21. Limitations

The current implementation has several important limitations:

1. The SpO₂ algorithm is experimental and has not been clinically validated.
2. The system is not intended for medical diagnosis or treatment.
3. The current SpO₂ calibration model is experimental.
4. AC amplitude is currently estimated from peak-to-valley values within individual 128-sample frames.
5. The 128-sample frame represents only 256 ms at the nominal 500 Hz sample rate and may not contain a complete pulse cycle.
6. Input signal quality, noise, baseline drift, motion artifacts, sensor characteristics, and calibration can affect the results.
7. The current heart-rate detector is a lightweight peak-based implementation rather than a clinically validated algorithm.
8. The host replay timing is frame-based and acknowledgment-driven; the configured 500 Hz value represents the input sample rate rather than a hard real-time acquisition clock.
9. The replay utility currently contains machine-specific CSV and serial-port configuration that must be adapted for another environment.
10. Clinical-grade validation would require appropriate reference measurements, controlled datasets, calibration, statistical evaluation, and regulatory-quality testing.

---

## 22. Future Work

Potential improvements include:

* Robust PPG pulse detection
* Adaptive thresholding
* Improved pulse-cycle segmentation
* Longer and more stable AC measurement windows
* Signal-quality assessment
* Motion-artifact rejection
* Additional digital filtering methods
* Quantitative HR validation
* Reference-based SpO₂ evaluation
* Improved calibration methodology
* Automated replay and regression testing
* Parameter configuration through command-line arguments
* Portable dataset configuration
* ESP32-S3 performance benchmarking
* Additional visualization and diagnostic outputs

---

## 23. Engineering Focus

This project is part of a broader portfolio focused on:

```text
Biomedical Signal Processing
          │
          ├── PPG
          ├── ECG
          ├── NIBP
          │
          ▼
Embedded DSP
          │
          ├── Filtering
          ├── Feature extraction
          ├── Peak detection
          ├── Physiological parameter estimation
          │
          ▼
Embedded Systems
          │
          ├── ESP32-S3
          ├── UART
          ├── GLCD
          └── Proteus
```

The goal is to demonstrate the complete engineering path from physiological signal data to embedded signal processing, visualization, and quantitative validation.

---

## 24. License

This project is released under the MIT License.

See:

```text
LICENSE
```

for details.

---

## 25. Disclaimer

This repository is provided for research, educational, and engineering purposes.

It is **not a medical device** and must not be used for diagnosis, treatment, or medical decision-making.

The experimental SpO₂ output is not a clinically validated oxygen-saturation measurement and must not be interpreted as a medical-grade SpO₂ reading.
