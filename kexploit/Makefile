TARGET = darksword-pe

CC = clang

CFLAGS = -framework Foundation -framework CoreServices -framework Security -framework IOSurface -framework IOKit -I../.include -I./src -isysroot $(shell xcrun --sdk iphoneos --show-sdk-path) -arch arm64 -arch arm64e -Wno-availability -miphoneos-version-min=15.0 -fobjc-arc
LDFLAGS = 

sign: $(TARGET)
	@ldid -Sentitlements.plist $<

$(TARGET): $(wildcard src/*.m)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

clean:
	@rm -f $(TARGET)