import argparse
import glob
import os
import time
from ctypes import POINTER, c_char_p, c_int, cdll

from rich.padding import Padding
from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import DataTable

from zipper_py import append_files_to_zip_file


def find_csv_files() -> list[str]:
    # Use recursive=True to search in subdirectories if needed
    # We use the pattern '*_[0-1][0-9].csv'
    #   * : Matches anything before the suffix
    #   _       : Matches the underscore
    #   [0-1]   : Matches '0' or '1' (the tens digit)
    #   [0-9]   : Matches any digit '0' through '9' (the ones digit)
    # This effectively captures only _00.csv through _19.csv
    # **/*.csv matches any .csv file in data/ or its subfolders
    search_path = os.path.join("data", "**", "*_[0-1][0-9].csv")
    csv_files = glob.glob(search_path, recursive=True)

    # To get absolute paths (if glob returns relative ones)
    full_paths = [os.path.abspath(p) for p in csv_files]
    print(f"Found {len(full_paths)} files")

    return full_paths


def create_zip_with_python(
    csv_file_paths: list[str], zip_filename: str
) -> tuple[str, str, str]:
    python_start_time = time.perf_counter()
    append_files_to_zip_file(csv_file_paths, zip_filename)
    time_taken = f"{time.perf_counter() - python_start_time:.2f}"
    file_size = f"{os.path.getsize(zip_filename) / (1024 * 1024):.2f}"

    # clean up to save storage space
    os.remove(zip_filename)

    return (
        "python",
        time_taken,
        file_size,
    )


def create_zip_with_go(
    csv_file_paths: list[str], zip_filename: str
) -> tuple[str, str, str]:
    full_paths = [p.encode() for p in csv_file_paths]
    c_file_paths = (c_char_p * len(full_paths))(*full_paths)
    zip_file_path = f"{os.getcwd()}/{zip_filename}".encode()

    # Import the DLL created in Go and create a docstring for it
    zipper_go = cdll.LoadLibrary("./zipper_go.so")
    zipper_go.AppendFilesToZipFile.argtypes = [POINTER(c_char_p), c_int, c_char_p]
    zipper_go.AppendFilesToZipFile.restype = c_int
    zipper_go.AppendFilesToZipFile.__doc__ = """
    Append files to a zip archive.

    Args:
        file_paths (POINTER(c_char_p)): Pointer to array of byte strings (file paths)
        file_count (c_int): Number of files in the array
        zip_file_path (c_char_p): Byte string path where the zip file will be create/appended

    Returns:
        c_int: 0 on success, 1 on error
    """
    # help(zipper_go.AppendFilesToZipFile)  <- Use this to see the documentation

    go_start_time = time.perf_counter()
    zipper_go.AppendFilesToZipFile(c_file_paths, len(full_paths), zip_file_path)

    time_taken = f"{time.perf_counter() - go_start_time:.2f}"
    file_size = f"{os.path.getsize(zip_file_path) / (1024 * 1024):.2f}"

    # clean up to save storage space
    os.remove(zip_file_path)

    return "Go", time_taken, file_size


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Zip benchmarker",
        description="Benchmark Python and Go implementations of a zipping program",
    )
    parser.add_argument(
        "-i",
        "--iterations",
        help="How many iterations of each type of zip generation to run.",
        type=int,
        default=3,
    )
    args = parser.parse_args()

    print(f"Running {args.iterations} iterations of each zip benchmark")

    data: list[tuple[str, str, str]] = [
        ("Language", "Time taken (seconds)", "Zip file size (MB)")
    ]
    files = find_csv_files()

    print("\nRunning Python benchmarks")
    for i in range(0, args.iterations):
        _lang, _time, _size = create_zip_with_python(files, f"zipped_py_{i}.zip")
        data.append((_lang, _time, _size))

    print("\nRunning Go benchmarks")
    for i in range(0, args.iterations):
        _lang, _time, _size = create_zip_with_go(files, f"zipped_go_{i}.zip")
        data.append((_lang, _time, _size))

    class TableApp(App):
        def compose(self) -> ComposeResult:
            yield DataTable()

        def on_mount(self) -> None:
            table = self.query_one(DataTable)
            table.add_columns(*data[0])
            for row in data[1:]:
                styled_row = [Padding(Text(str(cell)), (0, 1)) for cell in row]
                table.add_row(*styled_row)

    app = TableApp()
    app.run()
