# Parsing and tagging tei-xml files
The tei_parser define a TEINodeParser that make use of the tei_document class defined in extraction/src to parse tei documents into llama-index nodes,
tagging each node with the corresponding section name extracted. This allows to use the efficient metadata and relationship information management of llama-index
together with the fine-grained parsing of tei_document to create document chunks that can be easily processed in a llama-index pipeline (mainly fine tuning?).