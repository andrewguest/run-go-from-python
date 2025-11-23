build-zipper:
	go build -ldflags "-s -w" -buildmode=c-shared -o zipper_go.so zipper_go.go
