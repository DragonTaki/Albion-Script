# ----- ----- ----- -----
# safe_namespace.py
# An user-defined utility module
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/25
# Update Date: 2025/04/26
# Version: v1.1
# ----- ----- ----- -----

# Auto-expand these keys if their values are (min, max)
AUTO_BOUND_KEYS = {"WIDTH", "HEIGHT"}

class SafeNamespace:
    """
    A class to create a namespace-like structure for constants.
    It allows defining constants and retrieving them using dot notation.
    Also provides safe access, ensuring that only valid constants can be accessed.

    Attributes:
        None (Attributes are dynamically set when instantiated with key-value pairs).
    """

    def __init__(self, **entries):
        """
        Initializes the SafeNamespace object with a set of key-value pairs.

        Args:
            entries (dict): A dictionary where keys represent constant names
                             and values represent the corresponding constant values.
                             Nested dictionaries will be recursively converted into
                             SafeNamespace objects.

        Example:
            SEPARATORS = SafeNamespace(date="-", datetime="_")
        """
        for key, value in entries.items():
            # Auto convert `WIDTH`/`HEIGHT` tuple to SafeNamespace(MIN=..., MAX=...)
            if key.upper() in AUTO_BOUND_KEYS and isinstance(value, (tuple, list)) and len(value) == 2:
                value = SafeNamespace(MIN=value[0], MAX=value[1])
            # Check if the value is a dictionary. If so, recursively wrap it in SafeNamespace.
            elif isinstance(value, dict):
                value = SafeNamespace(**value)
            # Dynamically add each key-value pair as attributes to the object.
            setattr(self, key, value)

    def __getattr__(self, name):
        """
        Handles the case where an invalid constant is accessed.
        
        Args:
            name (str): The name of the constant that was attempted to be accessed.
        
        Raises:
            AttributeError: If the constant name is not valid or not defined.
        
        Example:
            Trying to access an undefined constant like `SEPARATORS.undefined` 
            will raise an AttributeError.
        """
        # Raises an error if the constant doesn't exist in the SafeNamespace.
        raise AttributeError(f"[SafeNamespace Error] '{name}' is not a valid constant")

    def __repr__(self):
        """
        Custom string representation of the SafeNamespace object for debugging.

        Returns:
            str: A string representation of the SafeNamespace object, showing its dictionary
                 of constants.
        
        Example:
            SEPARATORS will display as SafeNamespace({'date': '-', 'datetime': '_', ...})
        """
        return f"SafeNamespace({self.__dict__})"

    def register(self):
        """
        Registers all constants defined in the SafeNamespace instance to the global namespace
        so they can be accessed directly in the global scope.

        Example:
            If you define `SEPARATORS` as a SafeNamespace instance with some constants,
            calling `SEPARATORS.register()` will make all constants in SEPARATORS accessible
            as global variables like `date`, `datetime`, etc.

        This function effectively allows you to avoid manually importing the constants
        everywhere you need them.
        """
        for key, value in self.__dict__.items():
            # Registers each constant to the global namespace, making it accessible globally.
            globals()[key] = value

    def to_dict(self):
        """
        Convert the SafeNamespace object to a dictionary.

        Returns:
            dict: A dictionary representation of the SafeNamespace instance where
                  the keys are the constant names and the values are their corresponding values.

        Example:
            SEPARATORS.to_dict() will return {'date': '-', 'datetime': '_', ...}
        """
        return {key: value for key, value in self.__dict__.items()}
