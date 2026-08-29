# ankLIENT - Engineering & Coding Standards

To ensure `ankLIENT` scales securely and remains maintainable, all code must adhere to the following industry-standard practices.

## 1. Branding & Identity
- **Name:** The system is exclusively `ankLIENT`. All legacy references to `ChatGPT-Web2API` or `chatgpt_web2api` must be purged.
- **Paths:** All hidden configurations and lockfiles must write to `~/.anklient/`.
- **Loggers:** All Python loggers must be prefixed with `anklient.` (e.g., `anklient.engine.cdp`).

## 2. Code Style & Formatting
- **Formatter:** Code must be formatted using `black` (line length 100) and `isort` (for imports).
- **Type Hinting:** 100% strict type hinting is required. Every function must define parameter types and return types (e.g., `def send(text: str) -> bool:`).
- **Docstrings:** Use Google-style docstrings for all classes and complex functions. 
  - Explain *why* the code exists, not just *what* it does.

## 3. Extensibility (SOLID Principles)
- **Interfaces over Implementations:** Core systems must communicate via Abstract Base Classes (e.g., `BrowserDriver`). Never hardcode a specific implementation into the UI layer.
- **Dependency Injection:** Pass configurations and database connections into classes via their `__init__`, rather than using global singletons.

## 4. Error Handling & Resilience
- **No Bare Exceptions:** Never use `except Exception:`. Catch specific errors (e.g., `except TimeoutError:`).
- **Custom Exceptions:** Domain-specific errors should be defined in `anklient.core.exceptions` (e.g., `AuthRequiredError`, `BrowserDisconnectedError`).
- **Graceful Degradation:** If a UI component fails to load, it should display an error panel, not crash the entire terminal application.

## 5. Testing Architecture
- **Framework:** `pytest` and `pytest-asyncio`.
- **Unit Tests (`tests/unit/`):** Must be lightning-fast. Use `unittest.mock` to fake the browser and network calls. Tests single functions in isolation.
- **Integration Tests (`tests/integration/`):** Tests the actual background Daemon and real HTTP requests to `localhost:8080`.

## 6. Code Complexity & Optimization
- **Rule of 100:** Functions should rarely exceed 100 lines of code. If they do, they must be broken into helper methods.
- **Async Efficiency:** Do not use `time.sleep()`. Always use `asyncio.sleep()` to prevent blocking the event loop.
- **File Size:** Massive files (like the legacy `cdp_driver.py`) should be audited and split into logical modules (e.g., extracting network hooks into `cdp_network.py`).
