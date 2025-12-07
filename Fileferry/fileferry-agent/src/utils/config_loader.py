def load_config(file_path):
    import json
    import os

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    with open(file_path, 'r') as config_file:
        config = json.load(config_file)

    return config

def load_environment_variables():
    env_vars = {}
    for key, value in os.environ.items():
        env_vars[key] = value
    return env_vars

def get_config():
    config = load_config('./config/fileferry_config.json')
    env_vars = load_environment_variables()
    
    # Merge environment variables into config
    config.update(env_vars)
    
    return config