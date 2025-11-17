"""
Prompt management utility for GeneLingua
Loads and manages prompts from JSON configuration files
"""
import json
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages prompts loaded from JSON configuration files"""

    def __init__(self, prompts_dir: str = "prompts"):
        # Use absolute path from project root
        if not os.path.isabs(prompts_dir):
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(__file__)))
            prompts_dir = os.path.join(project_root, prompts_dir)
        self.prompts_dir = prompts_dir
        self._cache = {}

    def _load_prompt_file(self, filename: str) -> Dict[str, Any]:
        """Load a prompt configuration file"""
        if filename in self._cache:
            return self._cache[filename]

        filepath = os.path.join(self.prompts_dir, f"{filename}.json")
        if not os.path.exists(filepath):
            logger.warning(f"Prompt file not found: {filepath}")
            return {}

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._cache[filename] = data
                return data
        except Exception as e:
            logger.error(f"Failed to load prompt file {filepath}: {e}")
            return {}

    def get_prompt(self, module: str, prompt_key: str, variables: Optional[Dict[str, Any]] = None) -> str:
        """
        Get a prompt from the specified module and key

        Args:
            module: Module name (e.g., 'app', 'assessment', 'healthcare_expert')
            prompt_key: Key within the module (e.g., 'language_coach', 'expert_prompts.healthcare')
            variables: Dictionary of variables to substitute in template

        Returns:
            Formatted prompt string
        """
        prompts = self._load_prompt_file(module)

        # Handle nested keys with dot notation
        prompt_config = prompts
        keys = prompt_key.split('.')

        for key in keys:
            if isinstance(prompt_config, dict) and key in prompt_config:
                prompt_config = prompt_config[key]
            else:
                logger.warning(
                    f"Prompt key '{prompt_key}' not found in module '{module}'")
                return ""

        # Handle simple string prompts
        if isinstance(prompt_config, str):
            return self._format_prompt(prompt_config, variables or {})

        # Handle complex prompt configurations
        if isinstance(prompt_config, dict):
            if 'prompt_template' in prompt_config:
                template = prompt_config['prompt_template']
                return self._format_prompt(template, variables or {})
            elif 'system_prompt' in prompt_config:
                return prompt_config['system_prompt']

        logger.error(f"Invalid prompt configuration for {module}.{prompt_key}")
        return ""

    def get_prompt_config(self, module: str, prompt_key: str) -> Dict[str, Any]:
        """Get the full prompt configuration (including metadata)"""
        prompts = self._load_prompt_file(module)
        return prompts.get(prompt_key, {})

    def _format_prompt(self, template: str, variables: Dict[str, Any]) -> str:
        """Format a prompt template with variables"""
        try:
            return template.format(**variables)
        except KeyError as e:
            logger.error(f"Missing variable in prompt template: {e}")
            return template
        except Exception as e:
            logger.error(f"Error formatting prompt template: {e}")
            return template

    def list_modules(self) -> list:
        """List all available prompt modules"""
        if not os.path.exists(self.prompts_dir):
            return []

        modules = []
        for file in os.listdir(self.prompts_dir):
            if file.endswith('.json'):
                modules.append(file[:-5])  # Remove .json extension
        return modules

    def list_prompts(self, module: str) -> list:
        """List all prompt keys in a module"""
        prompts = self._load_prompt_file(module)
        return list(prompts.keys())

    def reload_cache(self):
        """Clear cache to force reload of all prompt files"""
        self._cache.clear()
        logger.info("Prompt cache cleared")


# Global instance
prompt_manager = PromptManager()

# Convenience functions


def get_prompt(module: str, prompt_key: str, variables: Optional[Dict[str, Any]] = None) -> str:
    """Convenience function to get a prompt"""
    return prompt_manager.get_prompt(module, prompt_key, variables)


def get_prompt_config(module: str, prompt_key: str) -> Dict[str, Any]:
    """Convenience function to get prompt configuration"""
    return prompt_manager.get_prompt_config(module, prompt_key)


def reload_prompts():
    """Convenience function to reload all prompts"""
    prompt_manager.reload_cache()
