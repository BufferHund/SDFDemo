# Contributing to Supermarket Brochure AI

Thank you for your interest in contributing to this project! This document provides guidelines for contributing.

## Getting Started

1. **Fork the repository**
2. **Clone your fork:**
   ```bash
   git clone https://github.com/your-username/supermarket-brochure-ai.git
   cd supermarket-brochure-ai
   ```
3. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in development mode
   ```

## Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**

3. **Run tests:**
   ```bash
   pytest tests/
   ```

4. **Check code style:**
   ```bash
   black src/
   flake8 src/
   ```

5. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Add: brief description of your changes"
   ```

6. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request**

## Areas for Contribution

### 1. Data Collection
- Add scrapers for more supermarket chains
- Improve existing scrapers for dynamic content
- Handle edge cases in brochure formats

### 2. Preprocessing
- Improve image quality enhancement
- Add data augmentation techniques
- Better PDF to image conversion

### 3. Models
- Fine-tune LayoutLMv3 on annotated data
- Experiment with other models (Donut, Pix2Struct)
- Implement model ensemble methods

### 4. Entity Extraction
- Improve price parsing accuracy
- Better date extraction
- Product name normalization

### 5. Web Application
- UI/UX improvements
- Add more visualization options
- Implement deal recommendation system

### 6. Testing
- Add unit tests for all modules
- Integration tests
- Performance benchmarks

### 7. Documentation
- Improve code documentation
- Add more usage examples
- Create tutorials

## Code Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints where appropriate
- Write docstrings for all public functions/classes
- Keep functions focused and concise

### Example:

```python
def extract_price(text: str) -> Optional[float]:
    """
    Extract price from text.

    Args:
        text: Text containing price (e.g., "1.99€")

    Returns:
        Price as float or None if not found

    Example:
        >>> extract_price("1.99€")
        1.99
    """
    # Implementation
    pass
```

## Testing

- Write tests for new functionality
- Ensure all tests pass before submitting PR
- Aim for good test coverage

```python
def test_extract_price():
    assert extract_price("1.99€") == 1.99
    assert extract_price("€2.50") == 2.50
    assert extract_price("no price") is None
```

## Commit Messages

Use clear and descriptive commit messages:

- **Add:** when adding new features
- **Fix:** when fixing bugs
- **Update:** when updating existing functionality
- **Refactor:** when refactoring code
- **Docs:** when updating documentation
- **Test:** when adding tests

Examples:
- `Add: Penny Markt scraper`
- `Fix: Price extraction regex for Euro symbol`
- `Update: Improve OCR confidence threshold`
- `Refactor: Simplify entity extraction logic`

## Pull Request Process

1. **Update documentation** if you add/change functionality
2. **Add tests** for new features
3. **Ensure CI/CD passes** (when set up)
4. **Request review** from maintainers
5. **Address feedback** promptly
6. **Squash commits** if requested

## Code Review

All contributions go through code review. Be prepared to:
- Answer questions about your implementation
- Make requested changes
- Discuss alternative approaches

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to open an issue for:
- Bug reports
- Feature requests
- Questions about contributing
- General discussions

## Thank You!

Your contributions make this project better for everyone. We appreciate your time and effort!
