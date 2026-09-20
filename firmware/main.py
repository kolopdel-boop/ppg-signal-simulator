from machine import Pin, UART
import time


# ============================================================
# SpO2 PROJECT - STAGE 6
# PPG WAVE + HR + R + SpO2
# ============================================================


# ============================================================
# GLCD PINS
# ============================================================

DATA_PINS = [
    Pin(4, Pin.OUT),
    Pin(5, Pin.OUT),
    Pin(6, Pin.OUT),
    Pin(7, Pin.OUT),
    Pin(8, Pin.OUT),
    Pin(9, Pin.OUT),
    Pin(10, Pin.OUT),
    Pin(11, Pin.OUT)
]

DI = Pin(12, Pin.OUT)
RW = Pin(13, Pin.OUT)
E = Pin(14, Pin.OUT)

CS1 = Pin(15, Pin.OUT)
CS2 = Pin(16, Pin.OUT)

RST = Pin(17, Pin.OUT)


# ============================================================
# UART
# ============================================================

uart = UART(
    0,
    baudrate=115200
)


# ============================================================
# PARAMETERS
# ============================================================

FS = 500

FRAME_SAMPLES = 128
BYTES_PER_SAMPLE = 8
FRAME_BYTES = FRAME_SAMPLES * BYTES_PER_SAMPLE


# ============================================================
# WAVEFORM
# ============================================================

FILTER_MIN = -250
FILTER_MAX = 250

WAVE_Y_MIN = 18
WAVE_Y_MAX = 62


# ============================================================
# WAVEFORM DISPLAY BUFFER
# ============================================================

WAVE_SAMPLES = 512
WAVE_SAMPLES_PER_COLUMN = 4

wave_buffer = [0] * WAVE_SAMPLES


# ============================================================
# HR PARAMETERS
# ============================================================

# Minimum distance between two confirmed peaks
# 0.50 second
MIN_PEAK_DISTANCE = int(FS * 0.50)

# Maximum RR interval
MAX_RR = int(FS * 2.0)

# Minimum signal level
PEAK_THRESHOLD = 40

# Number of RR intervals for averaging
RR_HISTORY_SIZE = 5

# Required drop after a local maximum
PEAK_DROP_THRESHOLD = 15


# ============================================================
# R PARAMETERS
# ============================================================

R_SCALE = 1000


# ============================================================
# SpO2 PARAMETERS
# ============================================================

# Experimental/demo equation:
#
# SpO2 = 110 - 25 * R

SPO2_A = 110
SPO2_B = 25


# ============================================================
# SpO2 FILTER
# ============================================================

SPO2_HISTORY_SIZE = 8

spo2_history = []

spo2_filtered = 0


# ============================================================
# GLCD
# ============================================================

WIDTH = 128
HEIGHT = 64

framebuffer = bytearray(
    WIDTH * HEIGHT // 8
)


# ============================================================
# SIGNAL VARIABLES
# ============================================================

red_dc = 0
ir_dc = 0

red_filtered = 0
ir_filtered = 0

filter_initialized = False


# ============================================================
# AC VARIABLES
# ============================================================

red_peak = -1000000
red_valley = 1000000

ir_peak = -1000000
ir_valley = 1000000

red_ac = 0
ir_ac = 0


# ============================================================
# HR VARIABLES
# ============================================================

last_peak_sample = -MIN_PEAK_DISTANCE

rr_history = []

heart_rate = 0

sample_counter = 0

peak_candidate = 0
peak_candidate_value = -1000000


# ============================================================
# R / SpO2
# ============================================================

ratio_r = 0

spo2 = 0


# ============================================================
# RX BUFFER
# ============================================================

rx_buffer = bytearray()


# ============================================================
# GLCD LOW LEVEL
# ============================================================

def set_data(value):

    for i in range(8):

        DATA_PINS[i].value(
            (value >> i) & 1
        )


def pulse_enable():

    E.value(1)

    time.sleep_us(1)

    E.value(0)

    time.sleep_us(1)


def glcd_write(value, is_data):

    DI.value(
        1 if is_data else 0
    )

    RW.value(0)

    set_data(value)

    pulse_enable()


def glcd_command(value):

    glcd_write(
        value,
        False
    )


def glcd_data(value):

    glcd_write(
        value,
        True
    )


def glcd_select_left():

    CS1.value(1)
    CS2.value(0)


def glcd_select_right():

    CS1.value(0)
    CS2.value(1)


def glcd_set_position(x, page):

    glcd_command(
        0xB8 | page
    )

    glcd_command(
        0x40 | (x & 0x3F)
    )


def glcd_clear():

    for controller in range(2):

        if controller == 0:

            glcd_select_left()

        else:

            glcd_select_right()


        for page in range(8):

            glcd_set_position(
                0,
                page
            )


            for x in range(64):

                glcd_data(0x00)


    framebuffer[:] = (
        b"\x00" * len(framebuffer)
    )


def glcd_init():

    RST.value(0)

    time.sleep_ms(10)

    RST.value(1)

    time.sleep_ms(10)


    glcd_select_left()

    glcd_command(0x3F)


    glcd_select_right()

    glcd_command(0x3F)


    glcd_clear()


# ============================================================
# FRAMEBUFFER
# ============================================================

def fb_clear():

    framebuffer[:] = (
        b"\x00" * len(framebuffer)
    )


def fb_pixel(x, y, value=1):

    if x < 0 or x >= WIDTH:

        return

    if y < 0 or y >= HEIGHT:

        return


    index = (
        x
        +
        (y // 8) * WIDTH
    )


    mask = 1 << (y & 7)


    if value:

        framebuffer[index] |= mask

    else:

        framebuffer[index] &= ~mask


# ============================================================
# FONT
# ============================================================

def fb_char(x, y, char):

    font = {

        "0": [0x3E, 0x51, 0x49, 0x45, 0x3E],
        "1": [0x00, 0x42, 0x7F, 0x40, 0x00],
        "2": [0x42, 0x61, 0x51, 0x49, 0x46],
        "3": [0x21, 0x41, 0x45, 0x4B, 0x31],
        "4": [0x18, 0x14, 0x12, 0x7F, 0x10],
        "5": [0x27, 0x45, 0x45, 0x45, 0x39],
        "6": [0x3C, 0x4A, 0x49, 0x49, 0x30],
        "7": [0x01, 0x71, 0x09, 0x05, 0x03],
        "8": [0x36, 0x49, 0x49, 0x49, 0x36],
        "9": [0x06, 0x49, 0x49, 0x29, 0x1E],

        "H": [0x7F, 0x08, 0x08, 0x08, 0x7F],
        "R": [0x7F, 0x09, 0x19, 0x29, 0x46],

        "S": [0x46, 0x49, 0x49, 0x49, 0x31],
        "p": [0x7E, 0x09, 0x09, 0x09, 0x06],
        "O": [0x3E, 0x41, 0x41, 0x41, 0x3E],

        "%": [0x63, 0x13, 0x08, 0x64, 0x63],

        "=": [0x14, 0x14, 0x14, 0x14, 0x14],

        " ": [0x00, 0x00, 0x00, 0x00, 0x00]
    }


    pattern = font.get(char)


    if pattern is None:

        pattern = font[" "]


    for col in range(5):

        column = pattern[col]


        for row in range(7):

            if column & (1 << row):

                fb_pixel(
                    x + col,
                    y + row,
                    1
                )


def fb_text(x, y, text):

    for char in text:

        fb_char(
            x,
            y,
            char
        )

        x += 6


# ============================================================
# WAVEFORM Y
# ============================================================

def waveform_y(value):

    if value < FILTER_MIN:

        value = FILTER_MIN


    if value > FILTER_MAX:

        value = FILTER_MAX


    y = (
        WAVE_Y_MIN
        +
        (
            (
                value
                -
                FILTER_MIN
            )
            *
            (
                WAVE_Y_MAX
                -
                WAVE_Y_MIN
            )
        )
        //
        (
            FILTER_MAX
            -
            FILTER_MIN
        )
    )


    return y


# ============================================================
# DRAW WAVEFORM
#
# Newest = LEFT
# Oldest  = RIGHT
# ============================================================

def draw_waveform_from_buffer():

    previous_y = -1


    for x in range(WIDTH):

        column = (
            WIDTH
            -
            1
            -
            x
        )


        start = (
            column
            *
            WAVE_SAMPLES_PER_COLUMN
        )


        total = 0


        for j in range(
            WAVE_SAMPLES_PER_COLUMN
        ):

            total += wave_buffer[
                start + j
            ]


        value = (
            total
            //
            WAVE_SAMPLES_PER_COLUMN
        )


        y = waveform_y(value)


        fb_pixel(
            x,
            y,
            1
        )


        if previous_y >= 0:

            if y > previous_y:

                for yy in range(
                    previous_y,
                    y + 1
                ):

                    fb_pixel(
                        x,
                        yy,
                        1
                    )


            elif y < previous_y:

                for yy in range(
                    y,
                    previous_y + 1
                ):

                    fb_pixel(
                        x,
                        yy,
                        1
                    )


        previous_y = y


# ============================================================
# DRAW DISPLAY
# ============================================================

def draw_display():

    fb_clear()


    # --------------------------------------------------------
    # HR
    # --------------------------------------------------------

    fb_text(
        2,
        2,
        "HR="
    )


    fb_text(
        20,
        2,
        str(heart_rate)
    )


    # --------------------------------------------------------
    # SpO2
    # --------------------------------------------------------

    fb_text(
        62,
        2,
        "SpO"
    )


    fb_char(
        80,
        2,
        "2"
    )


    fb_char(
        86,
        2,
        "="
    )


    fb_text(
        92,
        2,
        str(spo2)
    )


    fb_char(
        110,
        2,
        "%"
    )


    # --------------------------------------------------------
    # WAVEFORM
    # --------------------------------------------------------

    draw_waveform_from_buffer()


# ============================================================
# GLCD FLUSH
# ============================================================

def glcd_flush():

    for controller in range(2):

        if controller == 0:

            glcd_select_left()

            x_start = 0
            x_end = 64

        else:

            glcd_select_right()

            x_start = 64
            x_end = 128


        for page in range(8):

            glcd_set_position(
                0,
                page
            )


            base = (
                page
                *
                WIDTH
            )


            for x in range(
                x_start,
                x_end
            ):

                glcd_data(
                    framebuffer[
                        base + x
                    ]
                )


# ============================================================
# FILTER
# ============================================================

def filter_sample(
    red_raw,
    ir_raw
):

    global red_dc
    global ir_dc

    global red_filtered
    global ir_filtered

    global filter_initialized


    if not filter_initialized:

        red_dc = red_raw
        ir_dc = ir_raw

        red_filtered = 0
        ir_filtered = 0

        filter_initialized = True

        return 0, 0


    # DC

    red_dc += (
        red_raw
        -
        red_dc
    ) // 128


    ir_dc += (
        ir_raw
        -
        ir_dc
    ) // 128


    # AC

    red_ac_sample = (
        red_raw
        -
        red_dc
    )


    ir_ac_sample = (
        ir_raw
        -
        ir_dc
    )


    # Low pass

    red_filtered += (
        red_ac_sample
        -
        red_filtered
    ) // 8


    ir_filtered += (
        ir_ac_sample
        -
        ir_filtered
    ) // 8


    return (
        red_filtered,
        ir_filtered
    )


# ============================================================
# HR PEAK DETECTION
# ============================================================

def detect_peak(value):

    global last_peak_sample
    global rr_history
    global heart_rate
    global sample_counter

    global peak_candidate
    global peak_candidate_value


    # --------------------------------------------------------
    # Signal must be above threshold
    # --------------------------------------------------------

    if value < PEAK_THRESHOLD:

        return


    # --------------------------------------------------------
    # Search for local maximum
    # --------------------------------------------------------

    if value > peak_candidate_value:

        peak_candidate_value = value

        peak_candidate = sample_counter

        return


    # --------------------------------------------------------
    # Signal has fallen from candidate peak
    # --------------------------------------------------------

    if (
        peak_candidate_value - value
        >= PEAK_DROP_THRESHOLD
    ):


        distance = (
            peak_candidate
            -
            last_peak_sample
        )


        # ----------------------------------------------------
        # Valid RR
        # ----------------------------------------------------

        if (
            distance >= MIN_PEAK_DISTANCE
            and
            distance <= MAX_RR
        ):

            last_peak_sample = (
                peak_candidate
            )


            rr_history.append(
                distance
            )


            if len(rr_history) > RR_HISTORY_SIZE:

                rr_history.pop(0)


            # ------------------------------------------------
            # Average RR
            # ------------------------------------------------

            if len(rr_history) >= 2:

                total = 0


                for rr in rr_history:

                    total += rr


                avg_rr = (
                    total
                    //
                    len(rr_history)
                )


                if avg_rr > 0:

                    heart_rate = (
                        FS * 60
                    ) // avg_rr


                    if heart_rate > 180:

                        heart_rate = 180


                    if heart_rate < 40:

                        heart_rate = 0


        # ----------------------------------------------------
        # Search for next peak
        # ----------------------------------------------------

        peak_candidate_value = -1000000

        peak_candidate = sample_counter


# ============================================================
# PROCESS ONE SAMPLE
# ============================================================

def process_sample(
    red_raw,
    ir_raw
):

    global red_peak
    global red_valley

    global ir_peak
    global ir_valley

    global sample_counter


    red_val, ir_val = filter_sample(
        red_raw,
        ir_raw
    )


    sample_counter += 1


    # RED envelope

    if red_val > red_peak:

        red_peak = red_val


    if red_val < red_valley:

        red_valley = red_val


    # IR envelope

    if ir_val > ir_peak:

        ir_peak = ir_val


    if ir_val < ir_valley:

        ir_valley = ir_val


    # HR

    detect_peak(
        red_val
    )


    return red_val


# ============================================================
# PROCESS FRAME
# ============================================================

def process_frame(frame):

    global wave_buffer


    new_values = []


    for i in range(
        FRAME_SAMPLES
    ):

        offset = i * 8


        # RED

        red_raw = (
            frame[offset]
            |
            (
                frame[offset + 1]
                << 8
            )
            |
            (
                frame[offset + 2]
                << 16
            )
            |
            (
                frame[offset + 3]
                << 24
            )
        )


        # IR

        ir_raw = (
            frame[offset + 4]
            |
            (
                frame[offset + 5]
                << 8
            )
            |
            (
                frame[offset + 6]
                << 16
            )
            |
            (
                frame[offset + 7]
                << 24
            )
        )


        # Process

        red_val = process_sample(
            red_raw,
            ir_raw
        )


        # Save waveform

        new_values.append(
            red_val
        )


    # Add newest samples

    wave_buffer.extend(
        new_values
    )


    # Keep latest 512

    if len(wave_buffer) > WAVE_SAMPLES:

        extra = (
            len(wave_buffer)
            -
            WAVE_SAMPLES
        )


        wave_buffer = (
            wave_buffer[extra:]
        )


# ============================================================
# CALCULATE AC
# ============================================================

def calculate_ac():

    global red_peak
    global red_valley

    global ir_peak
    global ir_valley

    global red_ac
    global ir_ac


    if red_peak >= red_valley:

        red_ac = (
            red_peak
            -
            red_valley
        )

    else:

        red_ac = 0


    if ir_peak >= ir_valley:

        ir_ac = (
            ir_peak
            -
            ir_valley
        )

    else:

        ir_ac = 0


    # Reset measurement window

    red_peak = -1000000
    red_valley = 1000000

    ir_peak = -1000000
    ir_valley = 1000000


# ============================================================
# CALCULATE R
# ============================================================

def calculate_ratio_r():

    global ratio_r


    if red_dc <= 0:

        ratio_r = 0

        return


    if ir_dc <= 0:

        ratio_r = 0

        return


    if red_ac <= 0:

        ratio_r = 0

        return


    if ir_ac <= 0:

        ratio_r = 0

        return


    numerator = (
        red_ac
        *
        ir_dc
    )


    denominator = (
        ir_ac
        *
        red_dc
    )


    if denominator <= 0:

        ratio_r = 0

        return


    ratio_r = (
        numerator
        *
        R_SCALE
    ) // denominator


# ============================================================
# CALCULATE SpO2
#
# R -> raw SpO2 -> 8-sample moving average -> display
# ============================================================

def calculate_spo2():

    global spo2
    global spo2_history
    global spo2_filtered


    # --------------------------------------------------------
    # Invalid R
    # --------------------------------------------------------

    if ratio_r <= 0:

        return


    # --------------------------------------------------------
    # Experimental equation
    #
    # SpO2 = 110 - 25 * R
    # --------------------------------------------------------

    new_spo2 = (
        SPO2_A
        -
        (
            SPO2_B
            *
            ratio_r
        )
        //
        R_SCALE
    )


    # --------------------------------------------------------
    # Limit raw SpO2
    # --------------------------------------------------------

    if new_spo2 > 100:

        new_spo2 = 100


    if new_spo2 < 70:

        new_spo2 = 70


    # --------------------------------------------------------
    # Add to history
    # --------------------------------------------------------

    spo2_history.append(
        new_spo2
    )


    if len(spo2_history) > SPO2_HISTORY_SIZE:

        spo2_history.pop(0)


    # --------------------------------------------------------
    # Moving average
    # --------------------------------------------------------

    total = 0


    for value in spo2_history:

        total += value


    spo2_filtered = (
        total
        //
        len(spo2_history)
    )


    # --------------------------------------------------------
    # Final display value
    # --------------------------------------------------------

    spo2 = spo2_filtered


# ============================================================
# INITIALIZE
# ============================================================

glcd_init()


print(
    "================================"
)

print(
    "SpO2 PROJECT - STAGE 6"
)

print(
    "================================"
)

print(
    "UART0 - 115200"
)

print(
    "PPG WAVE ENABLED"
)

print(
    "512 SAMPLE WAVE BUFFER"
)

print(
    "4 SAMPLES / COLUMN"
)

print(
    "NEWEST SAMPLE = LEFT"
)

print(
    "OLDEST SAMPLE = RIGHT"
)

print(
    "HR PEAK DETECTION = IMPROVED"
)

print(
    "SpO2 FILTER = 8 SAMPLE"
)

print(
    "================================"
)


# ============================================================
# MAIN LOOP
# ============================================================

while True:


    # --------------------------------------------------------
    # Receive data
    # --------------------------------------------------------

    if uart.any():

        data = uart.read()


        if data:

            rx_buffer.extend(
                data
            )


    # --------------------------------------------------------
    # Process complete frames
    # --------------------------------------------------------

    while len(rx_buffer) >= FRAME_BYTES:


        # Extract frame safely

        frame = bytes(
            rx_buffer[
                0:FRAME_BYTES
            ]
        )


        remaining = (
            rx_buffer[
                FRAME_BYTES:
            ]
        )


        rx_buffer = bytearray(
            remaining
        )


        # Process PPG

        process_frame(
            frame
        )


        # AC

        calculate_ac()


        # R

        calculate_ratio_r()


        # SpO2

        calculate_spo2()


        # Display

        draw_display()


        glcd_flush()


        # ACK

        uart.write(
            b"FRAME_OK\n"
        )


        # Console

        print(
            "RED_DC={}".format(red_dc),
            "RED_AC={}".format(red_ac),
            "IR_DC={}".format(ir_dc),
            "IR_AC={}".format(ir_ac),
            "R_x1000={}".format(ratio_r),
            "SpO2={}%".format(spo2),
            "HR={}".format(heart_rate)
        )


    time.sleep_ms(1)