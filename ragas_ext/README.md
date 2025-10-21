# Extensions of ragas functions for ecological domain
.
├── eco_transforms/       # Functions to process and normalize ecological contexts
├── eco_synthesizers/     # Scenario and query generation logic for ecological prompts
├── kg_aer_v2_fixed.json  # Example ecological knowledge graph
├── README.md

## eco_transforms
Functions to build a knowledge graph: a set of nodes with chunks of text, and additional attributes,
related by semantic similarity (edges).
* Context extractor: extract ecological context (a dict with location, ecosystem, species, challenges) from chunk of text using a llm.
* Functions to postprocess and uniform the terms in the ecological context
* Overlap builder: build overlap of ecological context with string similarity

## eco_synthetizer
Produce query and answers from chunk (single-hop) or chunks (multi-hop) of text. 
Q and A can be used to generate synthetic datasets.
