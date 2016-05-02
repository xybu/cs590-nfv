TARGET=test_rdtsc

all:
	gcc -g -O3 -o $(TARGET) test_rdtsc.c

perf:
	time ./$(TARGET)
	sudo operf -g ./$(TARGET)
	opannotate --source --assembly $(TARGET)

clean:
	sudo rm -rfv oprofile_data test_rdtsc
