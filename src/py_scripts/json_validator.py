import json
import os


def validate_json_syntax(filename):
    """
    Validates the JSON syntax for a given file

    Parameters
    ----------
    filename : str
        Relative or absolute path to the file to be validated.

    Returns
    -------
    valid_json : bool
        Returns `True` if the JSON file is valid.
    """
    if filename.split(".")[-1] != "json":
        print("Not a JSON file; skipping test.")
        return True
    with open(filename, "r") as json_file:
        json.loads(json_file.read())
    return True


def get_absolute_file_paths(directory):
    """
    Gets the absolute paths for all files in a given directory.

    Parameters
    ----------
    directory : str
        Path to the directory.

    Returns
    -------
    file_path : str
        The absolute path to a file in the directory.
    """
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            yield os.path.abspath(os.path.join(dirpath, f))


def json_validator(directory):
    """
    Validates the JSON syntax for all files in a given directory.

    Parameters
    ----------
    directory : str
        Path to the directory.

    Returns
    -------
    valid_json_directory : bool
        Returns `True` if the directory's files are valid JSON.
    """
    for file in get_absolute_file_paths(directory):
        try:
            validate_json_syntax(file)
        except Exception as e:
            print("INVALID JSON SYNTAX. KINDLY VERIFY: {}".format(file))
            raise e
    return True


json_directory_list = ["./src/policies", "./src/parameters", "./src/templates"]

if __name__ == "__main__":
    print("Validating the following directories:")
    print(json_directory_list)
    for directory in json_directory_list:
        json_validator(directory)
