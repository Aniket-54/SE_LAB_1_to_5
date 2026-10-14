Here are the issues I found:

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| `eval()` usage | Security (Bandit) | 27 | Using `eval` on user input allows arbitrary code execution. | Replace with a safe mathematical calculation or a predefined discount dictionary. |
| Mutable default arg | Bug (Pylint) | 10 | `receipts=[]` is evaluated once; the list is dangerously shared across function calls. | Change default to `None` and initialize the list inside the function. |
| Bare `except:` | Bug (Flake8) | 16 | Catching all exceptions hides real errors (like `KeyboardInterrupt`). | Replace with specific exceptions like `except (KeyError, ValueError):`. |
| Old string formatting | Style (Pylint) | 21 | Using `%` for string formatting is outdated and less readable. | Replace `%` formatting with modern f-strings as suggested in the handout. |