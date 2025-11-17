#!/usr/bin/env python3
"""
Prompt Management CLI Tool for TyporaX-AI
Usage: python prompt_cli.py [command] [options]
"""

import sys
import os
import json
from prompt_manager import prompt_manager


def list_modules():
    """List all available prompt modules"""
    modules = prompt_manager.list_modules()
    if not modules:
        print("No prompt modules found.")
        return

    print("Available prompt modules:")
    for module in sorted(modules):
        print(f"  • {module}")


def list_prompts(module):
    """List all prompts in a module"""
    prompts = prompt_manager.list_prompts(module)
    if not prompts:
        print(f"No prompts found in module '{module}'")
        return

    print(f"Prompts in module '{module}':")
    for prompt in sorted(prompts):
        print(f"  • {prompt}")


def show_prompt(module, prompt_key):
    """Show a specific prompt"""
    config = prompt_manager.get_prompt_config(module, prompt_key)
    if not config:
        print(f"Prompt '{prompt_key}' not found in module '{module}'")
        return

    print(f"Prompt: {module}.{prompt_key}")
    print("=" * 50)

    if isinstance(config, str):
        print(config)
    elif isinstance(config, dict):
        if 'prompt_template' in config:
            print("Template:")
            print(config['prompt_template'])
            if 'variables' in config:
                print(f"\nVariables: {', '.join(config['variables'])}")
        elif 'system_prompt' in config:
            print("System Prompt:")
            print(config['system_prompt'])
            if 'user_prompt_template' in config:
                print("\nUser Prompt Template:")
                print(config['user_prompt_template'])
    else:
        print(json.dumps(config, indent=2, ensure_ascii=False))


def test_prompt(module, prompt_key, variables=None):
    """Test a prompt with sample variables"""
    if variables:
        # Parse variables from command line (format: key=value,key2=value2)
        var_dict = {}
        for pair in variables.split(','):
            if '=' in pair:
                key, value = pair.split('=', 1)
                var_dict[key.strip()] = value.strip()
    else:
        var_dict = {}

    prompt = prompt_manager.get_prompt(module, prompt_key, var_dict)
    if not prompt:
        print(f"Could not generate prompt for '{module}.{prompt_key}'")
        return

    print(f"Generated prompt: {module}.{prompt_key}")
    print("=" * 50)
    print(prompt)


def reload_prompts():
    """Reload all prompt configurations"""
    prompt_manager.reload_cache()
    print("All prompt configurations reloaded.")


def validate_prompts():
    """Validate all prompt configurations"""
    modules = prompt_manager.list_modules()
    errors = []

    for module in modules:
        try:
            prompts = prompt_manager.list_prompts(module)
            for prompt_key in prompts:
                config = prompt_manager.get_prompt_config(module, prompt_key)
                if not config:
                    errors.append(
                        f"{module}.{prompt_key}: Empty configuration")
                elif isinstance(config, dict) and 'prompt_template' in config:
                    # Check if template has proper variable placeholders
                    template = config['prompt_template']
                    variables = config.get('variables', [])
                    for var in variables:
                        if f'{{{var}}}' not in template:
                            errors.append(
                                f"{module}.{prompt_key}: Variable '{var}' not found in template")
        except Exception as e:
            errors.append(f"{module}: {str(e)}")

    if errors:
        print("Validation errors found:")
        for error in errors:
            print(f"  ❌ {error}")
        return False
    else:
        print("✅ All prompt configurations are valid!")
        return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python prompt_cli.py [command] [options]")
        print("\nCommands:")
        print("  list                    - List all modules")
        print("  list <module>          - List prompts in module")
        print("  show <module> <prompt> - Show specific prompt")
        print(
            "  test <module> <prompt> [variables] - Test prompt with variables")
        print("  reload                 - Reload all configurations")
        print("  validate               - Validate all configurations")
        return

    command = sys.argv[1]

    if command == "list":
        if len(sys.argv) == 2:
            list_modules()
        else:
            list_prompts(sys.argv[2])
    elif command == "show" and len(sys.argv) >= 4:
        show_prompt(sys.argv[2], sys.argv[3])
    elif command == "test" and len(sys.argv) >= 4:
        variables = sys.argv[4] if len(sys.argv) > 4 else None
        test_prompt(sys.argv[2], sys.argv[3], variables)
    elif command == "reload":
        reload_prompts()
    elif command == "validate":
        validate_prompts()
    else:
        print("Invalid command or insufficient arguments")


if __name__ == "__main__":
    main()
