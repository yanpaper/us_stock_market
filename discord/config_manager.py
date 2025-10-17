import configparser
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE_PATH = os.path.join(PROJECT_ROOT, 'config.ini')

def load_config():
    """Loads the config.ini file."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE_PATH)
    return config

def get_config_display_string():
    """Reads config.ini and returns a formatted string for display."""
    config = load_config()
    display_str = "```ini\n"
    for section in config.sections():
        display_str += f"[{section}]\n"
        for key, value in config.items(section):
            display_str += f"{key} = {value}\n"
    display_str += "\n```"
    return display_str

def update_config_setting(section: str, key: str, value: str):
    """
    Updates a specific setting in config.ini.
    Performs robust type conversion based on the existing value's inferred type.
    """
    config = load_config()

    if not config.has_section(section):
        return False, f"섹션 '{section}'을(를) 찾을 수 없습니다."
    if not config.has_option(section, key):
        return False, f"섹션 '{section}'에 키 '{key}'을(를) 찾을 수 없습니다."

    inferred_type = get_key_type(section, key)

    try:
        if inferred_type == 'int':
            new_value = int(value)
        elif inferred_type == 'float':
            new_value = float(value)
        elif inferred_type == 'bool':
            if value.lower() in ('true', '1', 't', 'y', 'yes', 'on'):
                new_value = True
            elif value.lower() in ('false', '0', 'f', 'n', 'no', 'off'):
                new_value = False
            else:
                raise ValueError(f"Invalid boolean value: {value}")
        else:  # 'str'
            new_value = value
    except ValueError:
        return False, f"키 '{key}'의 값 '{value}'이(가) 올바른 형식이 아닙니다. 예상 형식은 '{inferred_type}'입니다."

    config.set(section, key, str(new_value))
    with open(CONFIG_FILE_PATH, 'w') as configfile:
        config.write(configfile)
    return True, f"섹션 '{section}'의 키 '{key}' 값이 '{new_value}'(으)로 업데이트되었습니다."

def get_configurable_options():
    """
    Returns a dictionary of configurable options with their types and choices.
    """
    config = load_config()
    options = {}
    for section in config.sections():
        options[section] = {}
        for key, value in config.items(section):
            inferred_type = 'str'
            try:
                config.getint(section, key)
                inferred_type = 'int'
            except ValueError:
                try:
                    config.getfloat(section, key)
                    inferred_type = 'float'
                except ValueError:
                    try:
                        config.getboolean(section, key)
                        inferred_type = 'bool'
                    except ValueError:
                        pass
            
            options[section][key] = {'type': inferred_type, 'current': value}

            if inferred_type == 'bool':
                options[section][key]['choices'] = ['True', 'False']
            elif key == 'index_name':
                options[section][key]['choices'] = ['SP500', 'NASDAQ100']
            elif key == 'bollinger_band_mode':
                options[section][key]['choices'] = ['strict', 'normal', 'relaxed']
    return options

def get_key_type(section: str, key: str):
    """Returns the inferred type of a given key."""
    options = get_configurable_options()
    return options.get(section, {}).get(key, {}).get('type', 'str')

def get_choices_for_key(section: str, key: str):
    """Returns predefined choices for a given section and key, if any."""
    options = get_configurable_options()
    return options.get(section, {}).get(key, {}).get('choices', [])
