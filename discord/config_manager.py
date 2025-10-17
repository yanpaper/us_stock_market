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
    Performs basic type conversion based on existing value.
    """
    config = load_config()

    if not config.has_section(section):
        return False, f"섹션 '{section}'을(를) 찾을 수 없습니다."
    if not config.has_option(section, key):
        return False, f"섹션 '{section}'에 키 '{key}'을(를) 찾을 수 없습니다."

    # Try to infer type and convert value
    current_value = config.get(section, key)
    try:
        if isinstance(config.getint(section, key), int):
            new_value = int(value)
        elif isinstance(config.getfloat(section, key), float):
            new_value = float(value)
        elif isinstance(config.getboolean(section, key), bool):
            new_value = value.lower() in ('true', '1', 't', 'y', 'yes', 'on')
        else:
            new_value = value
    except ValueError:
        return False, f"키 '{key}'의 값 '{value}'이(가) 올바른 형식이 아닙니다. 현재 값의 형식은 '{type(current_value).__name__}'입니다."
    except Exception: # Fallback for string or other types
        new_value = value

    config.set(section, key, str(new_value)) # Store all values as strings in INI file
    with open(CONFIG_FILE_PATH, 'w') as configfile:
        config.write(configfile)
    return True, f"섹션 '{section}'의 키 '{key}' 값이 '{new_value}'(으)로 업데이트되었습니다."

def get_configurable_options():
    """
    Returns a dictionary of configurable options with their types/choices.
    This will be used to dynamically create Discord command options.
    """
    config = load_config()
    options = {}
    for section in config.sections():
        options[section] = {}
        for key, value in config.items(section):
            # Attempt to infer type
            try:
                if isinstance(config.getint(section, key), int):
                    options[section][key] = {'type': 'int', 'current': value}
                elif isinstance(config.getfloat(section, key), float):
                    options[section][key] = {'type': 'float', 'current': value}
                elif isinstance(config.getboolean(section, key), bool):
                    options[section][key] = {'type': 'bool', 'current': value}
                else:
                    options[section][key] = {'type': 'str', 'current': value}
            except ValueError:
                options[section][key] = {'type': 'str', 'current': value} # Default to string if type inference fails

            # Special handling for known choice fields
            if section == 'Screener' and key == 'index_name':
                options[section][key]['choices'] = ['SP500', 'NASDAQ100']
            elif section == 'Analyzer' and key == 'bollinger_band_mode':
                options[section][key]['choices'] = ['strict', 'normal', 'relaxed']
            elif section == 'Analyzer' and key == 'use_strict_filter':
                options[section][key]['choices'] = ['True', 'False']
            elif section == 'Analyzer' and key == 'use_bollinger_band':
                options[section][key]['choices'] = ['True', 'False']
            elif section == 'Analyzer' and key == 'use_volume_filter':
                options[section][key]['choices'] = ['True', 'False']
            elif section == 'Screener' and key == 'use_peg_filter':
                options[section][key]['choices'] = ['True', 'False']
            elif section == 'Fundamental' and key == 'use_analyst_filter':
                options[section][key]['choices'] = ['True', 'False']

    return options

def get_keys_by_type(target_type: str, section: str = None):
    """
    Returns a list of keys that match the target_type, optionally filtered by section.
    """
    options = get_configurable_options()
    keys = []
    for sec, sec_options in options.items():
        if section and sec != section:
            continue
        for key, details in sec_options.items():
            if details['type'] == target_type:
                keys.append(key)
    return keys

def get_choices_for_key(section: str, key: str):
    """
    Returns predefined choices for a given section and key, if any.
    """
    options = get_configurable_options()
    if section in options and key in options[section] and 'choices' in options[section][key]:
        return options[section][key]['choices']
    return []

def get_key_type(section: str, key: str):
    """
    Returns the inferred type of a given key.
    """
    options = get_configurable_options()
    if section in options and key in options[section]:
        return options[section][key]['type']
    return None