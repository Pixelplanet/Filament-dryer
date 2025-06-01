from kivy.metrics import sp
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.gridlayout import GridLayout

class MainPage(BoxLayout):
    def __init__(self, switch_to_settings, switch_to_preset_selection, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        self.add_widget(Label(text='Filament Dryer Control', font_size=sp(32), bold=True, size_hint=(1, 0.2)))

        grid_layout = GridLayout(cols=2, size_hint=(1, 0.6))

        self.temperature_label = Label(text='Temperature: 0°C', font_size=sp(18))
        grid_layout.add_widget(self.temperature_label)

        self.temperature_slider = Slider(min=0, max=100, value=0)
        self.temperature_slider.bind(value=self.update_temperature)
        grid_layout.add_widget(self.temperature_slider)

        self.start_button = Button(text='Start Dryer', size_hint=(1, 0.2), font_size=sp(18))
        self.start_button.bind(on_press=self.start_dryer)
        grid_layout.add_widget(self.start_button)

        self.stop_button = Button(text='Stop Dryer', size_hint=(1, 0.2), font_size=sp(18))
        self.stop_button.bind(on_press=self.stop_dryer)
        grid_layout.add_widget(self.stop_button)

        self.add_widget(grid_layout)

        self.settings_button = Button(text='Settings', size_hint=(1, 0.2), font_size=sp(18))
        self.settings_button.bind(on_press=lambda instance: switch_to_settings())
        self.add_widget(self.settings_button)

        self.presets_button = Button(text='Select Preset', size_hint=(1, 0.2), font_size=sp(18))
        self.presets_button.bind(on_press=lambda instance: switch_to_preset_selection())
        self.add_widget(self.presets_button)

        self.selected_preset_label = Label(text='Selected Preset: None', font_size=sp(18), size_hint=(1, 0.2))
        self.add_widget(self.selected_preset_label)

    def update_temperature(self, instance, value):
        self.temperature_label.text = f'Temperature: {int(value)}°C'

    def start_dryer(self, instance):
        print('Dryer started at', self.temperature_label.text)

    def stop_dryer(self, instance):
        print('Dryer stopped')

    def update_selected_preset(self, preset):
        self.selected_preset_label.text = f'Selected Preset: {preset}'

    def set_target_temperature(self, temperature):
        self.temperature_slider.value = temperature
        self.update_temperature(self.temperature_slider, temperature)