# meadoc

a docstring machine based on typing information  
...and also because I like my way of writing docstrings (not to say other formats are bad!)

- [the format](#the-format)
- [usage](#usage)
  - [linting](#linting)
  - [generating](#generating)
  - [global options](#global-options)

features:

- command-line docstring linter
  - will generate docstrings for you by filling in with `TODOC: fill in (meadow)`
  - will ~~yell~~ gently remind you if a function signature changes
    or a docstring is considered malformed by meadow

- generates markdown output for an easy api reference
  - either to an output file
  - or inserts output into another file with a given header

a real-world example of the docstring format I use, hereby just generically called the "meadow"
docstring format for ease of typing:

```python
from typing import NamedTuple, Generic, TypeVar

ResultType = TypeVar("ResultType")

class Result(NamedTuple, Generic[ResultType]):
    """
    typing.NamedTuple representing a result for safe value retrieval

    attributes:
        `value: ResultType`
            value to return or fallback value if erroneous
        `error: BaseException | None = None`
            exception if any

    methods:
        `def __bool__(self) -> bool: ...`
            method for boolean comparison for exception safety
        `def get(self) -> ResultType: ...`
            method that raises or returns an error if the Result is erroneous
        `def cry(self, string: bool = False) -> str: ...`
            method that returns the result value or raises an error
    """

    value: ResultType
    error: BaseException | None = None

    def __bool__(self) -> bool:
        """
        method for boolean comparison for exception safety
        
        returns: `bool`
            that returns True if `self.error` is not None
        """
        return self.error is None

    def cry(self, string: bool = False) -> str:  # noqa: FBT001, FBT002
        """
        method that raises or returns an error if the Result is erroneous

        arguments:
            `string: bool = False`
                if `self.error` is an Exception, returns it as a string error message
        
        returns: `str`
            returns `self.error` if it is a string, or returns an empty string if
            `self.error` is None
        """

        if isinstance(self.error, BaseException):
            if string:
                message = f"{self.error}"
                name = self.error.__class__.__name__
                return f"{message} ({name})" if (message != "") else name

            raise self.error

        if isinstance(self.error, str):
            return self.error

        return ""

    def get(self) -> ResultType:
        """
        method that returns the result value or raises an error

        returns: `ResultType`
            returns `self.value` if `self.error` is None

        raises: `BaseException`
            if `self.error` is not None
        """
        if self.error is not None:
            raise self.error
        return self.value
```

## the format

why another one? it's really just for me, but I think it's ~~a good~~ an okay-ish format

- it's easy and somewhat intuitive to read and write, especially because it's just plaintext
- it closely follows python syntax where it should, which includes type annotations

**a bonus:** it works:
- okay-ish on PyCham
- decent-ish on Zed
- slightly better on Visual Code

the format goes generally like:

```text
<short one line description>

[<more detailed description if needed>]

(attributes OR arguments):
    `python variable declaration syntax`
        description of the attribute

methods:
    `python function signature, including ALL arguments and type hints/return type (if available)`
        description of the method

[
returns: `return type`
    description of the return value
]

[
raises: `singular exception class`
    description of the exception(s) raised
OR
raises:
    `exception class 1`
        description 1
    `exception class 2`
        description 2
    ...
]

[
usage:
    ```py
    ...
    ```
]
```

sections can be positioned wherever makes sense; there can be a postamble if it reads nicely in your use case

sections in square blocks (`[...]`) are optional as:

- `return None`s can omit the `return` segment
- pure, unfailing functions can omit the `raises` segment

any other sections will just be parsed as-is, so there's no stopping you from adding an `example:`
section (but cross-ide compatibility is finicky, especially with pycharm)

### guidelines when writing meadow docstrings

#### what to care about

- use the latest or most succinct forms of syntax, so even if a codebase is for Python 3.9, unions and optionals should look like `optional_argument: T | None = None`

- externally imported/third party classes should be referenced in full:

    ```python
    class ThirdPartyExample(Exception):
        """
        blah blah
    
        attributes:
            `field_day: external.ExternalClass`
              blah blah
    
        methods:
            `def __init__(self, field_day: external.ExternalClass) -> None: ...`
                blah blah
        """
    ```

- if having a singular docstring for overloads, use variable declaration syntaxes that make sense

    ```python
    @overload
    def get_field(
        self,
    ) -> object: ...
    
    @overload
    def get_field(
        self,
        default: DefaultT,
    ) -> Union[object, DefaultT]: ...
    
    def get_field(
        self,
        default: object = None,
    ) -> object:
        """
        ...
    
        arguments:
            `default: object | None = None` <- note: technically mismatches, but works for the overload scenario
                ...
    
        returns: `object`
        """
        ...
    ```

### when to not care:

1. classes inherited for the sake of namespacing:

    ```python
    class TomlanticException(Exception):
        """base exception class for all tomlantic errors"""
        pass
    ```

2. return descriptions when its painfully obvious
from reading pretext

    ```python
    def difference_between_document(
        self, incoming_document: TOMLDocument
    ) -> Difference:
        """
        returns a `tomlantic.Difference` namedtuple object of the incoming and
        outgoing fields that were changed between the model and the comparison document
    
        arguments:
            `incoming_document: tomlkit.TOMLDocument`
    
        returns: `tomlantic.Difference`
        """
        ...
    ```

## usage

### linting

```text
$ meadow colette.py
colette.py:110:1: MDW001: function 'load_config' has no docstring
colette.py:202:1: MDW002: function 'read_from_disk' is outdated
colette.py:273:1: MDW003: function 'dump_to_disk' has a malformed docstring (fixable by passing --fix-malformed to 'meadow generate')
```

#### behaviour

with passing only a file to it, meadow will lint the file and output any errors or warnings

if any errors exist, meadow will exit with a non-zero status code

### generating

the subcommand `generate` will help you generate docstrings for your functions

```text
$ meadow generate colette.py
colette.py: generated 1 new docstring, updated 1 docstring, and skipped 1 malformed docstring (fixable by passing --fix-malformed)
```

#### behaviour

it won't override any text already in the docstring if one existed beforehand, but will add the
the attributes/.../raises sections at the end of the docstring

any newfound attributes, arguments or methods will be added to the docstring

where descriptions should be written, a `...  # TODOC: (meadow)` will be placed as a placeholder for you to fill in

newfound return types and raised exception classes will update the existing section header

#### options

- `--custom-todoc-message CUSTOM_TODOC_MESSAGE`  
  changes the default `TODOC: (meadow)` string

- `--fix-malformed`  
  will attempt to fix any malformed docstrings by adding the `TODOC: (meadow)` string
  to the end of the docstring

### global options

- `-n, --ignore-no-docstring`  
  will ignore any missing docstrings

- `-o, --ignore-outdated`  
  will ignore any malformed docstrings

- `-m, --ignore-malformed`  
  will ignore any malformed docstrings

- `--ignore IGNORE`  
  a comma-separated list of globs to match against and ignore if matched during file traversal
