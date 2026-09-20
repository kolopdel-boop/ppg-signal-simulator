
import serial
import time
import csv
from pathlib import Path
import struct
import argparse


# ============================================================
# CONFIG
# ============================================================

BAUDRATE = 115200

SAMPLE_RATE = 500
SAMPLE_PERIOD = 1.0 / SAMPLE_RATE

FRAME_SIZE = 128
SAMPLE_BYTES = 8
FRAME_BYTES = FRAME_SIZE * SAMPLE_BYTES


# ============================================================
# LOAD CSV
# ============================================================

def load_ppg_csv(filename):

    red = []
    ir = []

    with open(filename, "r", newline="") as f:

        reader = csv.DictReader(f)

        for row in reader:

            r = int(float(row["pleth_1"]))
            i = int(float(row["pleth_2"]))

            red.append(r)
            ir.append(i)

    return red, ir


# ============================================================
# BUILD ONE FRAME
# ============================================================

def build_frame(red_samples, ir_samples):

    frame = bytearray()

    for red, ir in zip(red_samples, ir_samples):

        frame.extend(
            struct.pack(
                "<II",
                red,
                ir
            )
        )

    return frame


# ============================================================
# WAIT FOR ACK
# ============================================================

def wait_for_ack(ser):

    deadline = time.perf_counter() + 2.0

    ack = bytearray()

    while time.perf_counter() < deadline:

        if ser.in_waiting:

            data = ser.read(ser.in_waiting)

            if data:
                ack.extend(data)

                if b"FRAME_OK" in ack:
                    return True

    return False


# ============================================================
# SEND ONE FRAME
# ============================================================

def send_frame(ser, red, ir, frame_number):

    frame = build_frame(red, ir)

    if len(frame) != FRAME_BYTES:

        raise RuntimeError(
            f"Invalid frame size: {len(frame)} bytes"
        )

    ser.write(frame)
    ser.flush()

    if not wait_for_ack(ser):

        print(
            f"WARNING: No ACK for frame {frame_number}"
        )

        return False

    return True


# ============================================================
# ARGUMENTS
# ============================================================

def parse_arguments():

    parser = argparse.ArgumentParser(
        description="Replay RED/IR PPG CSV data over serial."
    )

    parser.add_argument(
        "--csv",
        required=True,
        help="Path to CSV file containing pleth_1 (RED) and pleth_2 (IR)."
    )

    parser.add_argument(
        "--port",
        required=True,
        help="Serial port, for example COM11."
    )

    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================

def main():

    args = parse_arguments()

    csv_file = Path(args.csv)
    serial_port = args.port

    print("=" * 60)
    print("SpO2 PPG SERIAL REPLAY - STAGE 2")
    print("=" * 60)

    print()
    print("CSV:", csv_file)
    print("PORT:", serial_port)
    print("BAUD:", BAUDRATE)
    print("FS:", SAMPLE_RATE)
    print("FRAME SIZE:", FRAME_SIZE)
    print("BYTES/SAMPLE:", SAMPLE_BYTES)
    print("BYTES/FRAME:", FRAME_BYTES)
    print()

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    red, ir = load_ppg_csv(csv_file)

    total_samples = len(red)

    if total_samples != len(ir):

        raise RuntimeError(
            "RED and IR sample counts are different"
        )

    print("Samples loaded:", total_samples)

    print()
    print("FIRST SAMPLE")
    print("RED =", red[0])
    print("IR  =", ir[0])

    print()
    print("LAST SAMPLE")
    print("RED =", red[-1])
    print("IR  =", ir[-1])

    print()

    # --------------------------------------------------------
    # Open serial
    # --------------------------------------------------------

    print("Opening serial...")

    ser = serial.Serial(
        serial_port,
        BAUDRATE,
        timeout=1
    )

    time.sleep(1.0)

    # Clear old data
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    print("Serial opened.")
    print()

    # --------------------------------------------------------
    # Send frames
    # --------------------------------------------------------

    total_frames = (
        total_samples + FRAME_SIZE - 1
    ) // FRAME_SIZE

    samples_sent = 0

    start_time = time.perf_counter()

    try:

        for frame_number in range(total_frames):

            start_index = frame_number * FRAME_SIZE
            end_index = min(
                start_index + FRAME_SIZE,
                total_samples
            )

            frame_red = red[start_index:end_index]
            frame_ir = ir[start_index:end_index]

            # ------------------------------------------------
            # Last frame must also contain exactly 128 samples
            # ------------------------------------------------

            if len(frame_red) < FRAME_SIZE:

                print(
                    "Padding last frame..."
                )

                missing = FRAME_SIZE - len(frame_red)

                frame_red.extend(
                    [0] * missing
                )

                frame_ir.extend(
                    [0] * missing
                )

            ok = send_frame(
                ser,
                frame_red,
                frame_ir,
                frame_number
            )

            if not ok:

                print()
                print("SERIAL ERROR")
                print(
                    "Stopping transmission."
                )
                break

            samples_sent += min(
                FRAME_SIZE,
                total_samples - start_index
            )

            if frame_number % 10 == 0:

                elapsed = (
                    time.perf_counter()
                    - start_time
                )

                rate = (
                    samples_sent / elapsed
                    if elapsed > 0
                    else 0
                )

                print(
                    f"FRAME {frame_number + 1}/{total_frames} "
                    f"| samples={samples_sent} "
                    f"| rate={rate:.2f} Hz"
                )

            # ------------------------------------------------
            # Maintain approximately 500 Hz
            # ------------------------------------------------
            #
            # Each frame contains 128 samples.
            # 128 / 500 = 0.256 sec
            #

            time.sleep(
                FRAME_SIZE / SAMPLE_RATE
            )

    finally:

        elapsed = (
            time.perf_counter()
            - start_time
        )

        ser.close()

    print()
    print("=" * 60)
    print("TRANSMISSION COMPLETE")
    print("=" * 60)

    print("Samples sent:", samples_sent)
    print("Elapsed:", f"{elapsed:.3f}", "s")

    if elapsed > 0:

        print(
            "Average rate:",
            f"{samples_sent / elapsed:.2f} Hz"
        )

    print()
    print("Expected first sample:")
    print("RED =", red[0])
    print("IR  =", ir[0])

    print()
    print("Expected last sample:")
    print("RED =", red[-1])
    print("IR  =", ir[-1])


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()

