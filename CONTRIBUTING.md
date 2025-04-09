# Contributing to CombineDicts

Thank you for considering contributing to CombineDicts! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We aim to foster an inclusive and welcoming community.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue on GitHub with the following information:
- A clear and descriptive title
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Environment details (OS, Python version, etc.)

### Suggesting Enhancements

If you have ideas for improving CombineDicts, please create an issue on GitHub with:
- A clear and descriptive title
- A detailed description of the proposed enhancement
- Any relevant examples or mockups

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Add or update tests as needed
5. Ensure all tests pass
6. Commit your changes (`git commit -m 'Add some feature'`)
7. Push to the branch (`git push origin feature/your-feature-name`)
8. Open a Pull Request

#### Pull Request Guidelines

- Use clear, descriptive commit messages
- Include references to issues being addressed (if applicable)
- Update documentation as needed
- Add tests for new features

## Development Setup

1. Clone the repository
   ```bash
   git clone https://github.com/TuoFeiLun/CombineDicts.git
   cd CombineDicts
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Run tests
   ```bash
   # Add test command when available
   ```

## Adding New Dictionary Sources

If you want to add a new dictionary source:

1. Create a new class that extends the `DictionaryScraper` base class
2. Implement the `get_definition` method
3. Add your new scraper to the `CombinedDictionaryScraper` class
4. Add appropriate tests
5. Update documentation

## Style Guidelines

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to classes and functions
- Keep functions small and focused

## License

By contributing to CombineDicts, you agree that your contributions will be licensed under the project's MIT License. 