import pathlib

try:
    import tomllib as toml
except ImportError:
    try:
        import tomli as toml
    except ImportError:
        toml = None

class Config:
    def __init__(self):
        self.cdp_url = "http://127.0.0.1:9222"
        self.default_timeout = 180
        self.history_enabled = True
        
        self._load()

    def _load(self):
        if not toml:
            return
            
        config_path = pathlib.Path.home() / ".anklient" / "config.toml"
        if not config_path.exists():
            # Create default config
            config_path.parent.mkdir(parents=True, exist_ok=True)
            default_toml = 'cdp_url = "http://127.0.0.1:9222"\ndefault_timeout = 180\nhistory_enabled = true\n'
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(default_toml)
            return

        with open(config_path, 'rb') as f:
            data = toml.load(f)
            
        self.cdp_url = data.get("cdp_url", self.cdp_url)
        self.default_timeout = data.get("default_timeout", self.default_timeout)
        self.history_enabled = data.get("history_enabled", self.history_enabled)

settings = Config()
