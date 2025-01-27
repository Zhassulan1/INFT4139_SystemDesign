# OCR app for some Archive organization

### Why do we need this system
Some archive organization requested solution for character recognition from old papers .

### Functional requirements
1. Automatically read output of scanning device from file system
2. Recognize characters, and write recognized text to a file


### Non-functional requirements
1. No peak load, no users
2. 7 TB of images to process, 1 image ~= 2MB
3. Tests: 10 seconds/image in 14 cores, 16GB memory
5. Expected performance 2-3 second/image
4. Server CPU (Xeon/Threadripper) total ~= 70 Cores, 64GB RAM


### CAP theorem
There is no network partition