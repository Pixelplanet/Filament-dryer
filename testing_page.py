import kivy
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.label import Label

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

        self.start_btn = Button(text='Start PWM', size_hint=(1, 0.2))
        self.start_btn.bind(on_press=self.start_pwm)
        self.add_widget(self.start_btn)

        self.stop_btn = Button(text='Stop PWM', size_hint=(1, 0.2))
        self.stop_btn.bind(on_press=self.stop_pwm)
        self.add_widget(self.stop_btn)

        self.slider_label = Label(text='Duty Cycle: 0%', size_hint=(1, 0.1))
        self.add_widget(self.slider_label)

        self.slider = Slider(min=0, max=100, value=0, size_hint=(1, 0.2))
        self.slider.bind(value=self.on_slider_value)
        self.add_widget(self.slider)

        self.back_btn = Button(text='Back', size_hint=(1, 0.2))
        self.back_btn.bind(on_press=lambda x: self.switch_to_main())
        self.add_widget(self.back_btn)

        if RPI_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(PWM_PIN, GPIO.OUT)

    def start_pwm(self, instance):
        if RPI_AVAILABLE:
            if self.pwm is None:
                self.pwm = GPIO.PWM(PWM_PIN, 1000)  # 1kHz frequency
            self.pwm.start(self.slider.value)
        self.slider_label.text = f"Duty Cycle: {int(self.slider.value)}% (Started)"

    def stop_pwm(self, instance):
        if RPI_AVAILABLE and self.pwm:
            self.pwm.stop()
            self.pwm = None
        self.slider_label.text = f"Duty Cycle: {int(self.slider.value)}% (Stopped)"

    def on_slider_value(self, instance, value):
        self.duty_cycle = int(value)
        self.slider_label.text = f"Duty Cycle: {self.duty_cycle}%"
        if RPI_AVAILABLE and self.pwm:
            self.pwm.ChangeDutyCycle(self.duty_cycle)

    def on_parent(self, widget, parent):
        # Clean up GPIO when leaving page
        if not parent and RPI_AVAILABLE and self.pwm:
            self.pwm.stop()
            GPIO.cleanup(PWM_PIN)
