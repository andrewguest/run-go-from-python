# About
This is an example of creating a DLL (.so) using Go and then calling that DLL (.so) in Python.

# Steps
1. Create the DLL (.so) in Go using the `C` library and exporting the desired functions with the `//export <function name>` line.
```go
package main

import (
    "C"
    "fmt"
)

//export MyAwesomeFunction
func MyAwesomeFunction() C.int {
    fmt.Println("Hello, world!")
    return 0
}
```

2. Build the program in `c-shared` mode.
```shell
go build -ldflags "-s -w" -buildmode=c-shared -o go_dll_filename.so go_filename.go
```

3.Call the DLL (.so) functions from Python
```python
from ctypes import cdll

function_from_go = cdll.LoadLibrary("go_dll_filename.so")
```

# Resources
- [Calling Go from Python: Speed Up Python with Go - Leapcell](https://leapcell.io/blog/enhancing-python-speed-using-go)