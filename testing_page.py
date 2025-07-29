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
from kivy.clock import Clock

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

        # Remove manual PWM controls (start/stop buttons, slider, label)
        # Only keep temperature, target input, control toggle, indicators, and graph
        # Temperature readout label
        self.temp_label = Label(text='Temperature: -- °C', size_hint=(1, None), height=40)
        self.grid.add_widget(self.temp_label)

        # Target temperature input
        self.target_temp_label = Label(text='Target Temperature (°C):', size_hint=(1, None), height=40)
        self.grid.add_widget(self.target_temp_label)
        from kivy.uix.textinput import TextInput
        self.target_temp_input = TextInput(text='', multiline=False, size_hint=(1, None), height=40, input_filter='float')
        self.grid.add_widget(self.target_temp_input)
        self.set_target_btn = Button(text='Set Target', size_hint=(1, None), height=40)
        self.set_target_btn.bind(on_press=self.set_target_temperature)
        self.grid.add_widget(self.set_target_btn)
        self.target_temperature = None
        self.temp_control_active = False
        self.temp_control_btn = Button(text='Enable Temp Control', size_hint=(1, None), height=40)
        self.temp_control_btn.bind(on_press=self.toggle_temp_control)
        self.grid.add_widget(self.temp_control_btn)

        # Heating indicator
        self.heating_label = Label(text='Heating: OFF', size_hint=(1, None), height=40)
        self.grid.add_widget(self.heating_label)
        # Live PWM value
        self.pwm_value_label = Label(text='PWM: 0%', size_hint=(1, None), height=40)
        self.grid.add_widget(self.pwm_value_label)

        # Add graph for temperature and PWM
        from kivy.garden.matplotlib import FigureCanvasKivyAgg
        import matplotlib.pyplot as plt
        import collections
        self.temp_history = collections.deque(maxlen=120)
        self.pwm_history = collections.deque(maxlen=120)
        self.time_history = collections.deque(maxlen=120)
        self.graph_fig, self.graph_ax1 = plt.subplots()
        self.graph_ax2 = self.graph_ax1.twinx()
        self.graph_canvas = FigureCanvasKivyAgg(self.graph_fig)
        # Workaround for resize_event error in some garden.matplotlib versions
        if not hasattr(self.graph_canvas, 'resize_event'):
            self.graph_canvas.resize_event = lambda *args, **kwargs: None
        # Workaround for motion_notify_event error in some garden.matplotlib versions
        if not hasattr(self.graph_canvas, 'motion_notify_event'):
            self.graph_canvas.motion_notify_event = lambda *args, **kwargs: None
        # Set graph size to fill available space above back button
        self.graph_canvas.size_hint = (1, 0.5)
        self.grid.add_widget(self.graph_canvas)

        self.graph_ax1.set_xlabel('Time (s)')
        self.graph_ax1.set_ylabel('Temperature (°C)', color='tab:red')
        self.graph_ax2.set_ylabel('PWM (%)', color='tab:blue')
        self.graph_temp_line, = self.graph_ax1.plot([], [], 'r-', label='Temperature')
        self.graph_pwm_line, = self.graph_ax2.plot([], [], 'b-', label='PWM')
        self.graph_fig.tight_layout()

        self.graph_update_interval = 0.5
        self.graph_last_update = time.time()

        self.add_widget(self.grid)

        self.back_btn = Button(text='Back', size_hint=(1, 0.1))
        self.back_btn.bind(on_press=lambda x: self.switch_to_main())
        self.add_widget(self.back_btn)

        if RPI_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(PWM_PIN, GPIO.OUT, pull_up_down=GPIO.PUD_DOWN)
            # Enable internal pull-up for GPIO4 (1-wire data)
            GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            print(f"[GPIO] Setup complete for pin {PWM_PIN} and internal pull-up enabled for GPIO4.")
        else:
            print("[GPIO] RPi.GPIO not available. GPIO actions will be skipped.")

        # Start temperature reading thread if on RPi
        if RPI_AVAILABLE:
            self.temp_thread = threading.Thread(target=self.update_temperature, daemon=True)
            self.temp_thread.start()

    def get_sensor_file(self):
        # Find the 1-wire sensor device file
        base_dir = '/sys/bus/w1/devices/'
        # print(f"[TEMP] Searching for 1-wire devices in {base_dir}")
        try:
            device_folders = glob.glob(base_dir + '28-*')
            # print(f"[TEMP] Found device folders: {device_folders}")
            if device_folders:
                sensor_file = device_folders[0] + '/w1_slave'
                # print(f"[TEMP] Using sensor file: {sensor_file}")
                return sensor_file
            else:
                # print("[TEMP] No 1-wire devices found.")
                pass
        except Exception as e:
            # print(f"[TEMP] Error finding sensor file: {e}")
            pass
        return None

    def read_temperature(self):
        sensor_file = self.get_sensor_file()
        # print(f"[TEMP] Sensor file resolved: {sensor_file}")
        if not sensor_file:
            # print("[TEMP] No sensor file available.")
            return None
        try:
            with open(sensor_file, 'r') as f:
                lines = f.readlines()
            # print(f"[TEMP] Sensor file contents: {lines}")
            if lines[0].strip()[-3:] != 'YES':
                # print(f"[TEMP] CRC check failed: {lines[0].strip()}")
                return None
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp_string = lines[1][equals_pos+2:]
                # print(f"[TEMP] Raw temperature string: {temp_string}")
                temp_c = float(temp_string) / 1000.0
                # print(f"[TEMP] Parsed temperature: {temp_c} °C")
                return temp_c
            else:
                # print("[TEMP] 't=' not found in sensor file.")
                pass
        except Exception as e:
            # print(f"[TEMP] Error reading temperature: {e}")
            pass
        return None

    def set_target_temperature(self, instance):
        try:
            self.target_temperature = float(self.target_temp_input.text)
            self.target_temp_label.text = f"Target Temperature (°C): {self.target_temperature:.2f}"
        except ValueError:
            self.target_temp_label.text = "Target Temperature (°C): Invalid input"

    def toggle_temp_control(self, instance):
        self.temp_control_active = not self.temp_control_active
        if self.temp_control_active:
            self.temp_control_btn.text = "Disable Temp Control"
        else:
            self.temp_control_btn.text = "Enable Temp Control"

    def update_temperature(self):
        start_time = time.time()
        while not self.stop_temp_thread:
            temp = self.read_temperature()
            current_time = time.time() - start_time
            if temp is not None:
                self.temperature = temp
                self.temp_label.text = f"Temperature: {temp:.2f} °C"
                # Automatic PWM control
                if self.temp_control_active and self.target_temperature is not None:
                    error = self.target_temperature - temp
                    if error > 0:
                        if error > 5:
                            pwm_value = 100
                        elif error > 2:
                            pwm_value = 60
                        elif error > 0.5:
                            pwm_value = 30
                        else:
                            pwm_value = 10
                        self.heating_label.text = 'Heating: ON'
                    else:
                        pwm_value = 0
                        self.heating_label.text = 'Heating: OFF'
                    if self.pwm is None:
                        self.pwm = GPIO.PWM(PWM_PIN, 1000)
                        self.pwm.start(pwm_value)
                    else:
                        self.pwm.ChangeDutyCycle(pwm_value)
                    self.pwm_value_label.text = f'PWM: {pwm_value}%'
                else:
                    pwm_value = 0
                    self.heating_label.text = 'Heating: OFF'
                    self.pwm_value_label.text = 'PWM: 0%'
                # Update graph data
                self.temp_history.append(temp)
                self.pwm_history.append(pwm_value)
                self.time_history.append(current_time)
            else:
                self.temp_label.text = "Temperature: -- °C"
                self.heating_label.text = 'Heating: OFF'
                self.pwm_value_label.text = 'PWM: 0%'
                # Update graph data with None
                self.temp_history.append(None)
                self.pwm_history.append(0)
                self.time_history.append(current_time)
            # Update graph every interval
            if time.time() - self.graph_last_update > self.graph_update_interval:
                self.graph_last_update = time.time()
                Clock.schedule_once(lambda dt: self.update_graph())
            time.sleep(0.5)

    def update_graph(self):
        times = list(self.time_history)
        temps = [t if t is not None else float('nan') for t in self.temp_history]
        pwms = list(self.pwm_history)
        self.graph_temp_line.set_data(times, temps)
        self.graph_pwm_line.set_data(times, pwms)
        self.graph_ax1.relim()
        self.graph_ax1.autoscale_view()
        self.graph_ax2.relim()
        self.graph_ax2.autoscale_view()
        self.graph_fig.canvas.draw_idle()

    def on_parent(self, widget, parent):
        # Removed super().on_parent(widget, parent) to avoid error
        if parent is None:
            # Stopped being a child of the parent (navigating away)
            self.stop_temp_thread = True
            if RPI_AVAILABLE and self.pwm:
                self.pwm.stop()
                print(f"[GPIO] PWM stopped on pin {PWM_PIN} (navigating away).")
