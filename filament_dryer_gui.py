from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from main_page import MainPage
from settings_page import SettingsPage
from preset_selection_page import PresetSelectionPage
from testing_page import TestingPage

class FilamentDryerApp(App):
    def build(self):
        self.presets_file = 'presets.json'
        self.presets = SettingsPage(switch_to_main=self.switch_to_main, presets_data_file=self.presets_file).load_presets()

        self.screen_manager = ScreenManager()

        self.main_page = MainPage(switch_to_settings=self.switch_to_settings, switch_to_preset_selection=self.switch_to_preset_selection, switch_to_testing=self.switch_to_testing)
        self.settings_page = SettingsPage(switch_to_main=self.switch_to_main, presets_data_file=self.presets_file)
        self.preset_selection_page = PresetSelectionPage(switch_to_main=self.switch_to_main_with_preset, presets=self.presets)
        self.testing_page = TestingPage(switch_to_main=self.switch_to_main)

        self.main_screen = Screen(name='main')
        self.main_screen.add_widget(self.main_page)
        self.screen_manager.add_widget(self.main_screen)

        self.settings_screen = Screen(name='settings')
        self.settings_screen.add_widget(self.settings_page)
        self.screen_manager.add_widget(self.settings_screen)

        self.preset_selection_screen = Screen(name='preset_selection')
        self.preset_selection_screen.add_widget(self.preset_selection_page)
        self.screen_manager.add_widget(self.preset_selection_screen)

        self.testing_screen = Screen(name='testing')
        self.testing_screen.add_widget(self.testing_page)
        self.screen_manager.add_widget(self.testing_screen)

        return self.screen_manager

    def switch_to_settings(self):
        self.screen_manager.current = 'settings'

    def switch_to_main(self):
        self.screen_manager.current = 'main'

    def switch_to_preset_selection(self):
        self.screen_manager.current = 'preset_selection'

    def switch_to_testing(self):
        self.screen_manager.current = 'testing'

    def switch_to_main_with_preset(self, preset):
        self.main_page.update_selected_preset(preset)
        target_temperature_str = self.presets.get(preset, "0°C")  # Default to "0°C" if preset not found
        target_temperature = float(target_temperature_str.replace("°C", ""))  # Remove unit and convert to float
        self.main_page.set_target_temperature(target_temperature)
        self.screen_manager.current = 'main'
        self.preset_selection_page.update_presets(self.presets)  # Ensure preset selection page is updated

if __name__ == '__main__':
    FilamentDryerApp().run()