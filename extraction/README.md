# Aicacia Extraction

## Running GROBID

There's two methods for running the GROBID service /supported by this repository:
1. the preferred way with Docker
2. from source with Gradle

The first is ideal on Linux-based AMD64 architectures. To use the docker-based method:

```
docker compose up grobid # or grobid-crf if Tensorflow isn't supported by a GPU
```

The second method is as follows:

```
make grobid-gradle-run
```

Once up and running, visit http://localhost:8070.
