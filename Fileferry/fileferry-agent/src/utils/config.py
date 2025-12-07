"""
Configuration loader for FileFerry AI Agent
Handles YAML configuration with environment variable substitution
"""

import yaml
import os
import re
from typing import Dict, Any


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file with environment variable substitution

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Configuration dictionary with environment variables substituted
    """
    try:
        # Use UTF-8 encoding to handle Unicode characters properly on Windows
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Substitute environment variables
        config = _substitute_env_vars(config)
        
        return config
        
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in configuration file: {e}")
    except UnicodeDecodeError as e:
        raise ValueError(
            f"Unicode decode error in config file: {e}\n"
            f"Ensure the file is saved with UTF-8 encoding."
        )


def _substitute_env_vars(config: Any) -> Any:
    """
    Recursively substitute environment variables in configuration

    Args:
        config: Configuration dictionary or value

    Returns:
        Configuration with environment variables substituted
    """
    if isinstance(config, dict):
        return {k: _substitute_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [_substitute_env_vars(item) for item in config]
    elif isinstance(config, str):
        # Replace ${VAR_NAME} with environment variable value
        pattern = re.compile(r'\$\{([^}]+)\}')
        
        def replacer(match):
            env_var = match.group(1)
            value = os.getenv(env_var)
            if value is None:
                # Keep the placeholder if env var not set
                return match.group(0)
            return value
        
        return pattern.sub(replacer, config)
    else:
        return config


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate required configuration keys

    Args:
        config: Configuration dictionary

    Raises:
        ValueError: If required configuration is missing
    """
    required_keys = ['aws', 'bedrock', 'dynamodb', 'agent']
    
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration section: {key}")
    
    # Validate AWS settings
    if 'region' not in config.get('aws', {}):
        raise ValueError("Missing required AWS region in configuration")
    
    # Validate Bedrock settings
    bedrock_config = config.get('bedrock', {})
    if 'model_id' not in bedrock_config:
        raise ValueError("Missing required Bedrock model_id in configuration")
    
    # Validate DynamoDB settings
    dynamodb_config = config.get('dynamodb', {})
    if 'tables' not in dynamodb_config:
        raise ValueError("Missing required DynamoDB tables configuration")