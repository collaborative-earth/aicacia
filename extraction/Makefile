GROBID_VERSION := 0.8.0

build/grobid:
	@mkdir -p build && cd build \
		&& curl -LO https://github.com/kermitt2/grobid/archive/$(GROBID_VERSION).zip \
		&& unzip -o $(GROBID_VERSION).zip \
		&& mv grobid-$(GROBID_VERSION) grobid

.PHONY: clean
clean:
	@rm -rf build

.PHONY: grobid-gradle-run
grobid-gradle-run: build/grobid
	@cd build/grobid && ./gradlew run
