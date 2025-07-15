import kivy
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.core.window import Window

try:
    import RPi.GPIO as GPIO
    RPI_AVAILABLE = True
except ImportError:
    RPI_AVAILABLE = False

PWM_PIN = 18  # Change to your desired GPIO pin

class TestingPage(BoxLayout):
    def __init__(self, switch_to_main, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.switch_to_main = switch_to_main
        self.pwm = None
        self.duty_cycle = 0

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
