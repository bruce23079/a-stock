"""
配置管理模块
用于管理金融分析智能体的配置设置
支持通过配置文件和环境变量进行配置
"""

import yaml
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG = {
        "version": "1.0",
        "model": {
            "provider": "openrouter",
            "base_url": "https://openrouter.ai/api/v1",
            "model_name": "deepseek/deepseek-chat",
            "api_key_env": "OPENROUTER_API_KEY",  # 环境变量名称
            "parameters": {
                "max_tokens": 4000,
                "temperature": 0.1,
                "top_p": 0.9
            }
        },
        "yfinance": {
            "proxy": {
                "enabled": False,
                "http_proxy": "http://127.0.0.1:10808",
                "https_proxy": "http://127.0.0.1:10808"
            },
            "retry": {
                "max_retries": 5,
                "retry_delay": 1.0
            }
        },
        "akshare": {
            "timeout": 30,
            "retry_count": 3
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        if config_path is None:
            self.config_path = "config/settings.yaml"
        else:
            self.config_path = config_path
        
        self.config = self._load_config()
        self._apply_environment_overrides()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config_file = Path(self.config_path)
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f)
                
                # 合并默认配置和加载的配置
                config = self._merge_dicts(self.DEFAULT_CONFIG, loaded_config)
                return config
            except Exception as e:
                print(f"警告: 无法加载配置文件 {self.config_path}: {e}")
                print("使用默认配置")
                return self.DEFAULT_CONFIG.copy()
        else:
            print(f"配置文件 {self.config_path} 不存在，创建默认配置")
            self._save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """保存配置文件"""
        try:
            config_dir = Path(self.config_path).parent
            config_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            print(f"配置文件已保存到 {self.config_path}")
        except Exception as e:
            print(f"错误: 无法保存配置文件: {e}")
    
    def _merge_dicts(self, default: Dict, override: Dict) -> Dict:
        """递归合并两个字典"""
        result = default.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dicts(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_environment_overrides(self) -> None:
        """应用环境变量覆盖"""
        # 应用yfinance代理设置
        yfinance_proxy = os.environ.get('YFINANCE_PROXY')
        if yfinance_proxy:
            self.config['yfinance']['proxy']['enabled'] = True
            self.config['yfinance']['proxy']['http_proxy'] = yfinance_proxy
            self.config['yfinance']['proxy']['https_proxy'] = yfinance_proxy
    
    def get_model_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        return self.config.get('model', {})
    
    def get_yfinance_config(self) -> Dict[str, Any]:
        """获取雅虎财经配置"""
        return self.config.get('yfinance', {})
    
    def get_akshare_config(self) -> Dict[str, Any]:
        """获取akshare配置"""
        return self.config.get('akshare', {})
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        更新配置
        
        Args:
            updates: 要更新的配置字典
        """
        self.config = self._merge_dicts(self.config, updates)
        self._save_config(self.config)
    
    def get_api_key(self) -> str:
        """获取API密钥（从环境变量或配置文件中）"""
        model_config = self.get_model_config()
        api_key_env = model_config.get('api_key_env', 'OPENROUTER_API_KEY')
        
        # 优先从环境变量获取
        api_key = os.environ.get(api_key_env)
        if api_key:
            return api_key
        
        # 从配置文件中获取（如果存在）
        api_key = model_config.get('api_key', '')
        return api_key
    
    def apply_yfinance_settings(self) -> None:
        """应用雅虎财经配置到环境"""
        yfinance_config = self.get_yfinance_config()
        proxy_config = yfinance_config.get('proxy', {})
        
        if proxy_config.get('enabled', False):
            http_proxy = proxy_config.get('http_proxy')
            https_proxy = proxy_config.get('https_proxy')
            
            if http_proxy:
                os.environ['HTTP_PROXY'] = http_proxy
            if https_proxy:
                os.environ['HTTPS_PROXY'] = https_proxy
    
    def print_config_summary(self) -> None:
        """打印配置摘要"""
        print("=" * 50)
        print("配置摘要")
        print("=" * 50)
        
        model_config = self.get_model_config()
        print(f"模型提供商: {model_config.get('provider', 'N/A')}")
        print(f"模型名称: {model_config.get('model_name', 'N/A')}")
        print(f"API基础URL: {model_config.get('base_url', 'N/A')}")
        
        yfinance_config = self.get_yfinance_config()
        proxy_enabled = yfinance_config.get('proxy', {}).get('enabled', False)
        print(f"雅虎财经代理: {'启用' if proxy_enabled else '禁用'}")
        
        print(f"配置文件路径: {self.config_path}")
        print("=" * 50)


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None

def get_config_manager(config_path: Optional[str] = None) -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    return _config_manager