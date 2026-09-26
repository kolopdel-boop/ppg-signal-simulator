# PPG Signal Simulator

An embedded PPG signal replay and processing platform for heart-rate estimation and experimental SpO₂ estimation using RED/IR photoplethysmography signals on an ESP32-S3.

> **Disclaimer:** This project is for engineering, signal-processing, and educational experimentation. It is **not a medical device**. The SpO₂ estimation is experimental and has not been clinically validated or calibrated against a medical-grade reference device.

---

## 1. Overview

This project implements an end-to-end PPG signal replay and embedded processing pipeline:

```text
CSV PPG Data
     │
     ▼
Python Serial Replay Tool
     │
     │ Binary UART frames
     ▼
ESP32-S3
     │
     ├── DC tracking
     ├── AC extraction
     ├── Signal smoothing
     ├── Pulse peak detection
     ├── Heart-rate estimation
     ├── RED/IR AC/DC analysis
     ├── Ratio-of-ratios calculation
     └── Experimental SpO₂ estimation
     │
     ├── GLCD
     └── UART debug output
```

The project is designed as an embedded biomedical signal-processing experiment, combining:

* PPG signal handling
* Embedded DSP
* Heart-rate estimation
* RED/IR signal analysis
* Experimental pulse-oximetry processing
* UART binary communication
* Python-based signal replay
* GLCD waveform visualization
* Proteus simulation

---

## 2. Features

### Signal processing

* Nominal sampling rate: **500 Hz**
* RED and IR PPG channels
* Integer DC tracking
* AC signal extraction
* Integer smoothing filter
* Frame-local peak-to-valley AC estimation
* RED/IR AC/DC analysis

### Heart-rate estimation

* Peak-based pulse detection
* Minimum peak separation: **0.50 s**
* Maximum RR interval: **2.00 s**
* Peak threshold: **40**
* RR history: **5 intervals**
* Average RR-based HR calculation
* Heart-rate display on GLCD

With the current 0.50 s minimum peak separation, the effective upper detection limit is approximately **120 BPM**. The firmware also applies a lower reporting threshold of 40 BPM.

The current HR calculation is:

```text
HR = 60 × Fs / average_RR
```

where:

* `Fs = 500 Hz`
* `average_RR` is the average RR interval in samples.

The current detector is intentionally lightweight and is intended for experimental signal-processing work rather than clinical-grade heart-rate detection.

---

## 3. RED/IR Processing

The firmware maintains separate RED and IR DC estimates.

The DC tracking follows an integer first-order update:

```python
red_dc += (red_raw - red_dc) // 128
ir_dc  += (ir_raw  - ir_dc)  // 128
```

The AC component is then calculated as:

```text
AC = raw - DC
```

A lightweight smoothing stage is applied to the AC signal:

```python
filtered += (AC - filtered) // 8
```

The current implementation uses the filtered RED signal for pulse peak detection.

---

## 4. Experimental SpO₂ Estimation

The current implementation estimates RED and IR AC amplitudes using frame-local peak-to-valley measurements:

```text
RED_AC = RED_peak - RED_valley
IR_AC  = IR_peak - IR_valley
```

The ratio-of-ratios is then calculated as:

```text
R = (RED_AC × IR_DC) / (IR_AC × RED_DC)
```

Internally, the ratio is scaled by 1000 to allow integer arithmetic.

The experimental SpO₂ mapping is:

```text
SpO₂ = 110 − 25 × R
```

The displayed value is limited to:

```text
70% ≤ SpO₂ ≤ 100%
```

An 8-sample moving average is applied to the resulting SpO₂ estimate.

### Important limitation

This is **not a clinical pulse-oximetry algorithm**.

The current implementation uses a simplified empirical relationship and has not been calibrated against a reference pulse oximeter or validated across different subjects, sensors, skin conditions, perfusion levels, motion conditions, or ambient-light conditions.

---

## 5. Frame-Local AC Measurement

The serial protocol processes:

```text
128 samples/frame
```

At a nominal 500 Hz sampling rate:

```text
128 / 500 = 0.256 seconds
```

Therefore, each frame represents approximately **256 ms** of signal.

The current AC calculation is frame-local. The peak and valley are reset after each frame.

As a result, a frame may not contain a complete pulse cycle. This can cause RED/IR AC amplitudes to vary depending on the position of the frame boundary relative to the PPG waveform.

This is an intentional simplification of the current prototype.

Possible future improvements include:

* Longer analysis windows
* Pulse-cycle segmentation
* Beat-synchronous AC measurement
* Running peak/valley tracking
* Adaptive pulse segmentation
* Signal-quality assessment

---

## 6. Serial Communication Protocol

The Python replay tool communicates with the ESP32-S3 using a binary UART protocol.

| Parameter             |           Value |
| --------------------- | --------------: |
| Baud rate             |          115200 |
| Nominal sample rate   |          500 Hz |
| Samples per frame     |             128 |
| Bytes per sample      |               8 |
| Frame size            |      1024 bytes |
| RED format            | Unsigned 32-bit |
| IR format             | Unsigned 32-bit |
| Byte order            |   Little-endian |
| Frame acknowledgement |    `FRAME_OK\n` |

Each sample is encoded as:

```text
RED: 4 bytes
IR:  4 bytes
```

The Python replay tool uses:

```python
struct.pack("<II", red, ir)
```

The ESP32-S3 accumulates incoming bytes until a complete 1024-byte frame is available.

After successful frame processing, the firmware sends:

```text
FRAME_OK
```

The replay tool waits for this acknowledgement before continuing.

This provides a simple frame-level flow-control mechanism between the host and embedded target.

---

## 7. Python Serial Replay Tool

The replay tool is located at:

```text
tools/serial_replay_ppg.py
```

It:

1. Loads RED/IR samples from CSV
2. Reads the `pleth_1` and `pleth_2` columns
3. Maps them to RED and IR channels
4. Converts samples to unsigned 32-bit integers
5. Packs samples into 128-sample binary frames
6. Sends each frame through UART
7. Waits for `FRAME_OK`
8. Continues until all samples are transmitted

The current implementation uses command-line arguments for the CSV file and serial port.

Example:

```powershell
py tools/serial_replay_ppg.py --csv "path\to\data.csv" --port COM11
```

For example, with a local dataset:

```powershell
py tools/serial_replay_ppg.py --csv "C:\path\to\ppg_data.csv" --port COM11
```

The CSV must contain:

```text
pleth_1
pleth_2
```

columns.

### Timing model

The replay operates on complete frames rather than individual real-time samples.

Each 128-sample frame represents:

```text
128 / 500 = 256 ms
```

The host waits for the ESP32 acknowledgement and then applies the frame interval.

Therefore, the **500 Hz value represents the nominal sample rate of the data**, not a hard real-time guarantee of host-to-device sample timing.

---

## 8. Last Partial Frame

If the CSV contains a number of samples that is not an exact multiple of 128, the final frame is zero-padded to 128 samples before transmission.

This guarantees that every transmitted frame has exactly:

```text
1024 bytes
```

However, because the firmware processes the complete frame, the zero-padding can influence DSP quantities calculated from the final frame.

This is a known limitation of the current replay implementation.

---

## 9. ESP32-S3 Firmware

The embedded firmware is located at:

```text
firmware/main.py
```

The firmware performs:

```text
UART reception
      ↓
Frame reconstruction
      ↓
RED/IR decoding
      ↓
DC tracking
      ↓
AC extraction
      ↓
Smoothing
      ↓
Peak detection
      ↓
HR estimation
      ↓
RED/IR AC/DC analysis
      ↓
Ratio-of-ratios
      ↓
Experimental SpO₂
      ↓
GLCD + UART output
```

The firmware is implemented in MicroPython and is intended to run on an ESP32-S3 development platform.

---

## 10. GLCD Visualization

The firmware drives a graphical LCD directly from the ESP32-S3.

The display provides:

* Heart rate
* Experimental SpO₂
* PPG waveform

The waveform buffer contains 512 samples.

The waveform display uses a reduced number of samples per horizontal pixel to fit the signal into the available display width.

The firmware also clamps waveform values to a defined display range to prevent extreme signal values from dominating the visualization.

---

## 11. Proteus Simulation

The project includes a Proteus design:

```text
proteus/SpO2_Project.pdsprj
```

A screenshot of the simulation is also included:

```text
proteus/SpO2_Project.png
```

The Proteus project is intended to document the embedded hardware concept and provide an additional engineering artifact alongside the physical ESP32-S3 implementation.

Machine-specific Proteus workspace files are intentionally excluded from version control.

---

## 12. Running the Project

### Requirements

* ESP32-S3
* MicroPython
* GLCD compatible with the firmware pin configuration
* USB/UART connection
* Python 3
* `pyserial`
* Optional: Proteus

Install the Python serial dependency:

```powershell
py -m pip install pyserial
```

### Step 1 — Flash the firmware

Copy:

```text
firmware/main.py
```

to the ESP32-S3 MicroPython environment.

### Step 2 — Connect the ESP32-S3

Determine the serial port assigned by Windows.

For example:

```text
COM11
```

### Step 3 — Prepare the CSV

The replay CSV should contain:

```text
pleth_1,pleth_2
```

with RED and IR PPG samples.

### Step 4 — Start replay

Run:

```powershell
py tools/serial_replay_ppg.py --csv "path\to\data.csv" --port COM11
```

The replay tool will send binary PPG frames and wait for:

```text
FRAME_OK
```

after each frame.

### Step 5 — Observe the output

The ESP32-S3 provides:

* HR
* Experimental SpO₂
* RED DC
* RED AC
* IR DC
* IR AC
* Ratio-of-ratios
* PPG waveform

through the GLCD and UART debug output.

---

## 13. Repository Structure

```text
ppg-signal-simulator/
│
├── demo/
│   └── ...
│
├── firmware/
│   └── main.py
│
├── proteus/
│   ├── SpO2_Project.pdsprj
│   └── SpO2_Project.png
│
├── tools/
│   └── serial_replay_ppg.py
│
├── .gitignore
├── LICENSE
└── README.md
```

---

## 14. Validation Status

The project has been tested using development PPG replay data and the ESP32-S3 processing pipeline.

| Test area                             | Current status    |
| ------------------------------------- | ----------------- |
| CSV loading                           | Implemented       |
| RED/IR binary packing                 | Implemented       |
| 1024-byte frame transmission          | Implemented       |
| UART frame acknowledgement            | Implemented       |
| ESP32-S3 frame processing             | Implemented       |
| DC tracking                           | Implemented       |
| AC extraction                         | Implemented       |
| Signal smoothing                      | Implemented       |
| Peak-based HR estimation              | Implemented       |
| RED/IR AC/DC calculation              | Implemented       |
| Ratio-of-ratios                       | Implemented       |
| Experimental SpO₂ estimation          | Implemented       |
| GLCD visualization                    | Implemented       |
| Proteus design                        | Included          |
| Quantitative HR accuracy validation   | Not yet completed |
| Quantitative SpO₂ accuracy validation | Not yet completed |
| Clinical validation                   | Not performed     |

A development replay test successfully transferred a large PPG sample set through the Python-to-ESP32 pipeline.

This should be interpreted as **transport and system-integration validation**, not clinical accuracy validation.

---

## 15. Limitations

The current implementation intentionally uses lightweight algorithms suitable for an embedded prototype.

Known limitations include:

* Experimental, non-clinical SpO₂ estimation
* No calibration against a reference pulse oximeter
* Frame-local AC measurement
* 256 ms processing frames
* Sensitivity to signal quality and noise
* Sensitivity to baseline drift
* Potential sensitivity to motion artifacts
* Lightweight peak detector
* Fixed peak-detection threshold
* Fixed minimum peak separation
* Host replay is frame-based rather than hard real-time
* Final incomplete frames are zero-padded
* No formal quantitative accuracy study yet

These limitations are documented explicitly because the purpose of the project is to demonstrate the engineering pipeline and embedded DSP implementation rather than claim medical performance.

---

## 16. Future Work

Potential next development steps include:

### Signal processing

* Adaptive peak detection
* Improved pulse segmentation
* Longer analysis windows
* Robust baseline estimation
* Signal-quality metrics
* Motion-artifact detection
* Better RED/IR pulse-cycle synchronization

### Heart-rate estimation

* Adaptive thresholds
* More robust peak rejection
* Physiological plausibility checks
* Improved RR interval filtering
* Quantitative validation against reference annotations

### SpO₂ estimation

* Calibration using reference measurements
* Improved AC/DC estimation
* Longer averaging windows
* Better handling of low-perfusion signals
* Quantitative comparison with a reference pulse oximeter

### Embedded implementation

* More deterministic frame timing
* DMA-based acquisition
* Hardware ADC/sensor integration
* Improved display rendering
* Lower-overhead integer DSP
* Hardware-based PPG acquisition instead of replay-only input

### Testing

* Automated regression tests
* Multiple PPG datasets
* Noise injection tests
* Motion-artifact tests
* Parameter sensitivity analysis
* HR and SpO₂ error metrics

---

## 17. Engineering Focus

This project is part of a broader biomedical embedded-systems portfolio focused on:

```text
Biomedical Signal Processing
        │
        ├── PPG
        ├── ECG
        └── NIBP
        │
        ▼
Embedded DSP
        │
        ├── Filtering
        ├── Peak Detection
        ├── Feature Extraction
        └── Physiological Parameter Estimation
        │
        ▼
Embedded Systems
        │
        ├── ESP32-S3
        ├── UART
        ├── GLCD
        └── Proteus
```

The primary engineering objective is to demonstrate the complete path from physiological signal data to embedded signal processing and physiological parameter estimation.

---

## 18. Project Status

**Current status: Functional engineering prototype**

Implemented:

* PPG CSV replay
* RED/IR binary UART protocol
* ESP32-S3 frame processing
* DC/AC signal processing
* Smoothing
* Peak-based HR estimation
* RED/IR AC/DC analysis
* Ratio-of-ratios
* Experimental SpO₂ estimation
* GLCD visualization
* UART diagnostics
* Proteus documentation

Planned:

* More robust DSP algorithms
* Quantitative validation
* Better signal-quality handling
* Improved real-time acquisition
* Hardware PPG sensor integration
* Automated testing

---

## 19. License

See [`LICENSE`](LICENSE).
