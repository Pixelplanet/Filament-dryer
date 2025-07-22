import kivy
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.core.window import Window
import platform
import glob
import threading
import time

def is_raspberry_pi():
    print("[RPI CHECK] Starting Raspberry Pi detection...")
    # Check for Raspberry Pi by reading /proc/cpuinfo or using platform
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
        print("[RPI CHECK] /proc/cpuinfo read successfully.")
        if 'Raspberry Pi' in cpuinfo:
            print("[RPI CHECK] Found 'Raspberry Pi' in /proc/cpuinfo.")
            return True
        if 'BCM' in cpuinfo:
            print("[RPI CHECK] Found 'BCM' in /proc/cpuinfo.")
            return True
        print("[RPI CHECK] No Raspberry Pi markers found in /proc/cpuinfo.")
    except Exception as e:
        print(f"[RPI CHECK] Failed to read /proc/cpuinfo: {e}")
    # Fallback: check platform
    try:
        node_name = platform.uname().node
        print(f"[RPI CHECK] platform.uname().node: {node_name}")
        if 'raspberrypi' in node_name.lower():
            print("[RPI CHECK] Found 'raspberrypi' in platform.uname().node.")
            return True
        print("[RPI CHECK] No Raspberry Pi markers found in platform.uname().node.")
    except Exception as e:
        print(f"[RPI CHECK] platform.uname() failed: {e}")
    print("[RPI CHECK] Device is NOT a Raspberry Pi.")
    return False

try:
    import RPi.GPIO as GPIO
    GPIO_IMPORTED = True
    print("[GPIO] RPi.GPIO imported successfully.")
except ImportError as e:
    GPIO_IMPORTED = False
    print(f"[GPIO] Failed to import RPi.GPIO: {e}")

RPI_AVAILABLE = GPIO_IMPORTED and is_raspberry_pi()
print(f"[SETUP] GPIO_IMPORTED={GPIO_IMPORTED}, RPI_AVAILABLE={RPI_AVAILABLE}")

PWM_PIN = 18  # Change to your desired GPIO pin

class TestingPage(BoxLayout):
    def __init__(self, switch_to_main, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.switch_to_main = switch_to_main
        self.pwm = None
        self.duty_cycle = 0
        self.temperature = None
        self.stop_temp_thread = False

        # Use GridLayout for better touch area distribution
        self.grid = GridLayout(cols=1, spacing=10, padding=20, size_hint=(1, 0.8))

        self.start_btn = Button(text='Start PWM', size_hint=(1, None), height=60)
        self.start_btn.bind(on_press=self.start_pwm)
        self.grid.add_widget(self.start_btn)

        self.stop_btn = Button(text='Stop PWM', size_hint=(1, None), height=60)
        self.stop_btn.bind(on_press=self.stop_pwm)
        self.grid.add_widget(self.stop_btn)

        self.slider_label = Label(text='Duty Cycle: 0%', size_hint=(1, None), height=40)
        self.grid.add_widget(self.slider_label)

        self.slider = Slider(min=0, max=100, value=0, size_hint=(1, None), height=60)
        self.slider.bind(value=self.on_slider_value)
        self.grid.add_widget(self.slider)

        # Temperature readout label
        self.temp_label = Label(text='Temperature: -- °C', size_hint=(1, None), height=40)
        self.grid.add_widget(self.temp_label)

        self.add_widget(self.grid)

        self.back_btn = Button(text='Back', size_hint=(1, 0.2))
        self.back_btn.bind(on_press=lambda x: self.switch_to_main())
        self.add_widget(self.back_btn)

        if RPI_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(PWM_PIN, GPIO.OUT)
            print(f"[GPIO] Setup complete for pin {PWM_PIN}")
        else:
            print("[GPIO] RPi.GPIO not available. GPIO actions will be skipped.")

        # Start temperature reading thread if on RPi
        if RPI_AVAILABLE:
            self.temp_thread = threading.Thread(target=self.update_temperature, daemon=True)
            self.temp_thread.start()

    def get_sensor_file(self):
        # Find the 1-wire sensor device file
        base_dir = '/sys/bus/w1/devices/'
        try:
            device_folders = glob.glob(base_dir + '28-*')
            if device_folders:
                return device_folders[0] + '/w1_slave'
        except Exception as e:
            print(f"[TEMP] Error finding sensor file: {e}")
        return None

    def read_temperature(self):
        sensor_file = self.get_sensor_file()
        if not sensor_file:
            return None
        try:
            with open(sensor_file, 'r') as f:
                lines = f.readlines()
            if lines[0].strip()[-3:] != 'YES':
                return None
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp_string = lines[1][equals_pos+2:]
                temp_c = float(temp_string) / 1000.0
                return temp_c
        except Exception as e:
            print(f"[TEMP] Error reading temperature: {e}")
        return None

    def update_temperature(self):
        while not self.stop_temp_thread:
            temp = self.read_temperature()
            if temp is not None:
                self.temperature = temp
                self.temp_label.text = f"Temperature: {temp:.2f} °C"
            else:
                self.temp_label.text = "Temperature: -- °C"
            time.sleep(2)

    def start_pwm(self, instance):
        print(f"[GPIO] Start PWM requested on pin {PWM_PIN} at {self.slider.value}% duty cycle.")
        if RPI_AVAILABLE:
            if self.pwm is None:
                self.pwm = GPIO.PWM(PWM_PIN, 1000)  # 1kHz frequency
                self.pwm.start(self.slider.value)
                print(f"[GPIO] PWM started on pin {PWM_PIN} at {self.slider.value}% duty cycle.")
            else:
                self.pwm.ChangeDutyCycle(self.slider.value)
                print(f"[GPIO] PWM duty cycle changed to {self.slider.value}%.")
        self.slider_label.text = f"Duty Cycle: {int(self.slider.value)}% (Started)"

    def stop_pwm(self, instance):
        print(f"[GPIO] Stop PWM requested on pin {PWM_PIN}.")
        if RPI_AVAILABLE and self.pwm:
            self.pwm.stop()
            self.pwm = None
            print(f"[GPIO] PWM stopped on pin {PWM_PIN}.")
        self.slider_label.text = f"Duty Cycle: {int(self.slider.value)}% (Stopped)"

    def on_slider_value(self, instance, value):
        self.duty_cycle = int(value)
        self.slider_label.text = f"Duty Cycle: {self.duty_cycle}%"
        if RPI_AVAILABLE and self.pwm:
            self.pwm.ChangeDutyCycle(self.duty_cycle)
            print(f"[GPIO] PWM duty cycle changed to {self.duty_cycle}%.")

    def on_parent(self, widget, parent):
        # Removed super().on_parent(widget, parent) to avoid error
        if parent is None:
            # Stopped being a child of the parent (navigating away)
            self.stop_temp_thread = True
            if RPI_AVAILABLE and self.pwm:
                self.pwm.stop()
                print(f"[GPIO] PWM stopped on pin {PWM_PIN} (navigating away).")
