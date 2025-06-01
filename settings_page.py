import json
from kivy.metrics import sp
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.slider import Slider

class SettingsPage(BoxLayout):
    def __init__(self, switch_to_main, presets_data_file='presets.json', **kwargs):
        self.presets_file = presets_data_file
        self.presets = self.load_presets()
        super().__init__(orientation='vertical', **kwargs)

        self.preset_buttons = {}

        self.add_widget(Label(text='Settings', font_size=sp(32), bold=True, size_hint=(1, 0.2)))

        grid_layout = GridLayout(cols=2, size_hint=(1, 0.6))

        for preset, value in self.presets.items():
            label = Label(text=f'{preset}:', font_size=sp(18))
            grid_layout.add_widget(label)

            button = Button(text=f'{value}', font_size=sp(18))
            button.bind(on_press=lambda instance, p=preset: self.open_slider_popup(p))
            grid_layout.add_widget(button)

            self.preset_buttons[preset] = button

        self.add_widget(grid_layout)

        button_layout = BoxLayout(size_hint=(1, 0.2))

        self.save_button = Button(text='Save Presets', font_size=sp(18))
        self.save_button.bind(on_press=self.save_presets)
        button_layout.add_widget(self.save_button)

        self.back_button = Button(text='Back to Main', font_size=sp(18))
        self.back_button.bind(on_press=lambda instance: switch_to_main())
        button_layout.add_widget(self.back_button)

        self.add_widget(button_layout)

    def load_presets(self):
        try:
            with open(self.presets_file, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                'PLA': '50°C',
                'ABS': '60°C',
                'PETG': '55°C'
            }

    def open_slider_popup(self, preset):
        popup_layout = BoxLayout(orientation='vertical')

        slider = Slider(min=0, max=100, value=int(self.presets[preset].replace('°C', '')))
        slider_label = Label(text=f'{int(slider.value)}°C', font_size=sp(18))
        slider.bind(value=lambda instance, value: self.update_slider_label(slider_label, value))
        popup_layout.add_widget(slider_label)
        popup_layout.add_widget(slider)

        close_button = Button(text='Set', size_hint=(1, 0.2), font_size=sp(18))
        close_button.bind(on_press=lambda instance: self.set_preset_value_and_close(preset, slider.value, popup))
        popup_layout.add_widget(close_button)

        popup = Popup(title=f'Set {preset}', content=popup_layout, size_hint=(0.8, 0.5))
        popup.open()

    def update_slider_label(self, label, value):
        label.text = f'{int(value)}°C'

    def set_preset_value_and_close(self, preset, value, popup):
        self.presets[preset] = f'{int(value)}°C'
        popup.dismiss()

        if preset in self.preset_buttons:
            self.preset_buttons[preset].text = f'{self.presets[preset]}'

        print(f'Updated {preset} to {self.presets[preset]}')

    def save_presets(self, instance=None):
        with open(self.presets_file, 'w') as file:
            json.dump(self.presets, file)
        print('Presets saved:', self.presets)