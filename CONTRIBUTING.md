# Contributing to Whisper 2.0

First off, thank you for considering contributing to Whisper 2.0! Your help is greatly appreciated.

## How Can I Contribute?

### Reporting Bugs

If you encounter a bug, please open an issue on our GitHub repository. When you report a bug, please include:

-   Your operating system and Python version.
-   The exact steps to reproduce the bug.
-   Any relevant error messages or logs.

### Suggesting Enhancements

If you have an idea for a new feature or an improvement to an existing one, please open an issue to discuss it. This allows us to coordinate our efforts and ensure that your suggestion aligns with the project's goals.

### Pull Requests

We welcome pull requests! If you'd like to contribute code, please follow these steps:

1.  **Fork the repository** and create a new branch from `main`.
2.  **Set up your development environment:**
    ```bash
    uv sync
    ```
3.  **Make your changes.** Please ensure that your code adheres to the project's coding style by running the linter and formatter:
    ```bash
    uv run ruff check . --fix
    uv run black .
    ```
4.  **Write tests** for your new feature or bug fix.
5.  **Ensure that all tests pass:**
    ```bash
    uv run python tests/test_voice_system.py
    ```
6.  **Submit a pull request** with a clear description of your changes.

## Coding Style

We use `black` for code formatting and `ruff` for linting. Please ensure that your code conforms to these tools' standards before submitting a pull request.

Thank you for your contributions!
