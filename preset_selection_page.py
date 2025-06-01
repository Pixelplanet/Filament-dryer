from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

class PresetSelectionPage(BoxLayout):
    def __init__(self, switch_to_main, presets, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        self.presets = presets
        self.switch_to_main = switch_to_main

        self.add_widget(Label(text='Select a Preset', font_size=24))

        for preset, value in self.presets.items():
            button = Button(text=f'{preset}: {value}')
            button.bind(on_press=lambda instance, p=preset: self.select_preset(p))
            self.add_widget(button)

        self.back_button = Button(text='Back to Main')
        self.back_button.bind(on_press=lambda instance: switch_to_main())
        self.add_widget(self.back_button)

    def select_preset(self, preset):
        print(f'Selected preset: {preset} with value {self.presets[preset]}')
        self.switch_to_main(preset)

    def update_presets(self, presets):
        self.presets = presets
        self.clear_widgets()
        self.add_widget(Label(text='Select a Preset', font_size=24))

        for preset, value in self.presets.items():
            button = Button(text=f'{preset}: {value}')
            button.bind(on_press=lambda instance, p=preset: self.select_preset(p))
            self.add_widget(button)

        self.add_widget(self.back_button)