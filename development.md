# Development Guide

Unlike other Python projects that have attempted to work with the SDK, this library emphasizes:

- Low Coupling: Minimize dependencies between components for easier maintenance and testing.

- Composition Over Inheritance: Prefer composition to build flexible and reusable components.

- Fully Typed: Utilize type annotations throughout the codebase for better clarity and type safety. This ensures great editor support, with code completion, leading to less time spent debugging.

- Fully Tested: Ensure robust functionality through comprehensive testing.



## Setting Up the Development Environment

To set up the development environment for this project, follow these steps:

1. Clone the repository from GitHub:
   ```sh
   git clone https://github.com/yourusername/your_package_name.git
   cd your_package_name
   ```

2. Create a virtual environment and activate it:
   ```sh
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. Install the development dependencies:
   ```sh
   pip install .[dev]
   ```

## Running Tests

To run the test suite, use the following command:

```sh
pytest
```

This will run all tests located in the `tests/` directory.

### Running Tests with multiple Python versions

Multiple versions of Python can be tested using Tox. Versions 3.9-3.13 are supported. To have Tox run the tests, simply call its command:

```sh
tox
```

Tox will create an isolated environment for each Python version to run the tests in.

### Running Tests with Coverage

To run the tests and generate coverage reports, use the following command:

```sh
pytest --cov=streamdeck --cov-report=xml --cov-report=html --cov-report=term --junit-xml=reports/xunit-results.xml
```

- **`--cov=streamdeck`**: Measure test coverage for the `streamdeck` package.
- **`--cov-report=xml`**: Generate an XML report of the coverage (used for CI/CD tools).
- **`--cov-report=html`**: Generate an HTML report for visualizing coverage.
- **`--cov-report=term`**: Display coverage summary in the terminal.
- **`--junit-xml=reports/xunit-results.xml`**: Generate a JUnit-style XML report of the test results.

The coverage reports will be saved in the `reports/` directory.



## Building the Package

To build the package, run the following command:

```sh
python -m build
```

This will create the distribution files in the `dist/` directory.


## Building in Editable Mode from Source

To test the project while actively developing it from another plugin project directory, you can build it in editable mode:

```bash
python -m pip install -e <python-streamdeck-plugin-sdk project directory> --config-settings editable_mode=strict
```

The `--config-settings editable_mode=strict` option enforces stricter checks on the source structure, making it easier to identify problems early on and helps code editors and static checkers work more effectively.

Additionally, you can add a line to your plugin project's dependencies file to include the SDK in editable mode:

```
-e <python-streamdeck-plugin-sdk project directory>
```

This allows the SDK to be installed when running your plugin on the Stream Deck.


## Publishing to PyPI

To publish the package to PyPI, ensure you have the correct credentials and run:

```sh
python -m twine upload dist/*
```

Make sure you have set the `TWINE_USERNAME` and `TWINE_PASSWORD` environment variables or have them configured in your `.pypirc` file.