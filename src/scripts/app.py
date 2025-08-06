import PySimpleGUI as sg
from dataclasses import dataclass, asdict
from aio_conf.core import OptionSpec, ConfigSpec
import json
import ast
import re

# --- Helper Functions ---

def safe_literal(val: str):
    try:
        return ast.literal_eval(val)
    except Exception:
        return val

def sanitize_env_part(s: str) -> str:
    return re.sub(r'[-\s]+', '_', s.strip().upper())

def generate_cli_arg(name: str) -> str:
    return f"--{name.strip().lower().replace('_', '-').replace(' ', '-')}"

# --- Option Draft DataClass ---
@dataclass
class OptionDraft:
    name: str
    type_: str
    default: str
    required: bool
    env: str
    cli: str
    description: str

    def to_spec(self):
        type_map = {'str': str, 'int': int, 'float': float, 'bool': bool}
        python_type = type_map.get(self.type_, str)
        default_val = safe_literal(self.default)
        cli_args = [arg.strip() for arg in self.cli.split(',')] if self.cli else []

        return OptionSpec(
            name=self.name,
            type=python_type,
            default=default_val,
            required=self.required,
            env=self.env or None,
            cli=cli_args,
            description=self.description or None
        )

# --- Main App Class ---
class ConfigSpecBuilderApp:
    def __init__(self):
        sg.theme('DarkAmber')

        self.options = []

        self.layout = [
            [sg.Text('🛠️ AIO-Conf ConfigSpec Builder', font='Any 16')],

            [sg.Frame('Program Settings', [
                [sg.Text('Program Name'), sg.Input(key='-PROG-', enable_events=True), sg.Checkbox('Abbrev Env Vars', key='-ACRO-')]
            ])],

            [sg.Frame('Add Option', [
                [sg.Text('Name'), sg.Input(key='-NAME-', enable_events=True)],
                [sg.Text('Type'), sg.Combo(['str', 'int', 'float', 'bool'], default_value='str', key='-TYPE-')],
                [sg.Text('Default'), sg.Input(key='-DEFAULT-')],
                [sg.Checkbox('Required', key='-REQ-')],
                [sg.Text('Env Name'), sg.Input(key='-ENV-')],
                [sg.Text('CLI Arg'), sg.Input(key='-CLI-')],
                [sg.Text('Description'), sg.Multiline(key='-DESC-', size=(40,3))],
                [sg.Button('Add Option', key='-ADD_OPT-')]
            ])],

            [sg.Frame('Options List', [
                [sg.Listbox(values=[], size=(50,10), key='-OPTIONS-', enable_events=True)],
                [sg.Button('Remove Selected', key='-REMOVE-'), sg.Button('Clear All', key='-CLEAR-')]
            ])],

            [sg.Button('Generate ConfigSpec', key='-GENERATE-'), sg.Exit()]
        ]

        self.window = sg.Window('AIO-Conf ConfigSpec Builder', self.layout, finalize=True)

    def add_option(self, values):
        """
        Adds a new option to the builder based on the values entered in the GUI.

        Parameters:
            values (dict):
                A dictionary containing the values entered in the GUI.

        Returns:
            None
        """
        opt = OptionDraft(
            name        = values['-NAME-'],
            type_       = values['-TYPE-'],
            default     = values['-DEFAULT-'],
            required    = values['-REQ-'],
            env         = values['-ENV-'],
            cli         = values['-CLI-'],
            description = values['-DESC-'].strip()
        )
        self.options.append(opt)
        self.update_options_list()
        for key in ['-NAME-', '-DEFAULT-', '-ENV-', '-CLI-', '-DESC-']:
            self.window[key].update('')

    def update_options_list(self):
        """
        Updates the options list in the GUI with the current options added to the builder.

        Returns:
            None
        """
        self.window['-OPTIONS-'].update([f"{o.name} ({o.type_})" for o in self.options])

    def generate_configspec(self):
        """
        Generates a ConfigSpec JSON string based on the options added to the builder.

        Returns:
            str:
                A JSON string representing the ConfigSpec.
        """
        specs = [opt.to_spec() for opt in self.options]

        json_config = json.dumps({
            "options": [
                {
                    "name": spec.name,
                    "type": spec.type.__name__,
                    "default": spec.default,
                    "required": spec.required,
                    "env": spec.env,
                    "cli": spec.cli,
                    "description": spec.description
                } for spec in specs
            ]
        }, indent=2)

        sg.popup_scrolled('Generated ConfigSpec', json_config, title='🎉 ConfigSpec Generated!')

    def auto_populate_fields(self, values):
        prog_name = sanitize_env_part(values['-PROG-'])
        name_part = sanitize_env_part(values['-NAME-'])
        abbrev = values['-ACRO-']
        prefix = ''.join(word[0] for word in prog_name.split('_')) if abbrev else prog_name
        env_var = f"{prefix}_{name_part}" if prog_name and name_part else ""
        cli_arg = f"{generate_cli_arg(values['-NAME-'])}, -{values['-NAME-'][0].lower()}" if values['-NAME-'] else ""
        self.window['-ENV-'].update(env_var)
        self.window['-CLI-'].update(cli_arg)

    def run(self):
        while True:
            event, values = self.window.read()

            if event in (sg.WIN_CLOSED, 'Exit'):
                break

            if event in ('-PROG-', '-NAME-', '-ACRO-'):
                self.auto_populate_fields(values)

            if event == '-ADD_OPT-':
                if values['-NAME-'].strip():
                    self.add_option(values)
                else:
                    sg.popup('⚠️ Option name cannot be empty.', title='Input Error')

            elif event == '-REMOVE-':
                selected = values['-OPTIONS-']
                if selected:
                    idx = self.window['-OPTIONS-'].get_indexes()[0]
                    self.options.pop(idx)
                    self.update_options_list()

            elif event == '-CLEAR-':
                self.options.clear()
                self.update_options_list()

            elif event == '-GENERATE-':
                self.generate_configspec()

        self.window.close()


if __name__ == '__main__':
    app = ConfigSpecBuilderApp()
    app.run()
