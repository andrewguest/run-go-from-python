# Build the shared library
build-zipper:
	go build -ldflags "-s -w" -buildmode=c-shared -o zipper_go.so zipper_go.go

# Profile the benchmark application using the `pyinstrument` library
profile:
	uv run pyinstrument benchmark_zipper.py -i 1 -st

# Clean the directory
clean:
	rm profile_output* && rm zipped_*.zip && rm mprofile*
