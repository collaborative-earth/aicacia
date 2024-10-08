from typing import TYPE_CHECKING, Any, List, Optional, Sequence

from llama_index.core.bridge.pydantic import Field
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.node_parser.node_utils import build_nodes_from_splits
from llama_index.core.schema import BaseNode, MetadataMode, TextNode
from llama_index.core.node_parser.interface import NodeParser
from llama_index.core.utils import get_tqdm_iterable

from extraction.src.aicacia_extraction.grobid import IDNOType, TEIDocument

DEFAULT_TAGS = ['abstract','sections']

class TEINodeParser(NodeParser):
    
    '''
    TEINodeParser

        The `TEINodeParser` is designed to parse TEI (Text Encoding Initiative) XML documents and extract specific sections of text into `TextNode` objects used in llama-index. 
        This parser is integrated with the LlamaIndex framework and can be used to process TEI-encoded documents by extracting content from tags such as `abstract`, `sections`, and others
        using the TEIDocument class.
        The parser supports customization of the TEI tags that are extracted and can handle both simple and nested document structures.

        ### Key Features:
        - **Customizable TEI Tags**: Allows extraction of text from specific TEI tags, such as `abstract` and `sections`, by default. Users can modify the `tags` parameter to specify custom tags for extraction.
        - **Node Parsing**: Converts each extracted TEI tag's content into `TextNode` objects that are compatible with LlamaIndex. Each node includes metadata about the tag it was extracted from, providing rich context for the text.
        - **Metadata Handling**: Each parsed `TextNode` is associated with metadata, such as the tag name or section title, allowing users to easily trace the origin of the text within the document.
        - **Integration with LlamaIndex**: Compatible with LlamaIndex's node-parsing framework, including support for features like progress tracking during long parsing operations.

        
        ### Usage Example:
        The `TEINodeParser` can be used as follows:
        parser = TEINodeParser()
        nodes = parser.get_nodes_from_documents(documents,show_progress=True)
        where documents is a list of Document or Nodes with plain xml text as content.
    '''
    tags: List[str] = Field(
        default=DEFAULT_TAGS, description="TEI tags to extract text from."
    )

    @classmethod
    def from_defaults(
        cls,
        include_metadata: bool = True,
        include_prev_next_rel: bool = True,
        callback_manager: Optional[CallbackManager] = None,
        tags: Optional[List[str]] = DEFAULT_TAGS,
    ) -> "TEINodeParser":
        callback_manager = callback_manager or CallbackManager([])

        return cls(
            include_metadata=include_metadata,
            include_prev_next_rel=include_prev_next_rel,
            callback_manager=callback_manager,
            tags=tags,
        )
    
    @classmethod
    def class_name(cls) -> str:
        """Get class name."""
        return "TEINodeParser"
    
    def _parse_nodes(
        self,
        nodes: Sequence[BaseNode],
        show_progress: bool = False,
        **kwargs: Any,
    ) -> List[BaseNode]:
        all_nodes: List[BaseNode] = []
        nodes_with_progress = get_tqdm_iterable(nodes, show_progress, "Parsing nodes")

        for node in nodes_with_progress:
            nodes = self.get_nodes_from_node(node)
            all_nodes.extend(nodes)

        return all_nodes

    def get_nodes_from_node(self, node: BaseNode) -> List[TextNode]:
        """Get nodes from document."""
        
        # Extract text and parse it using teidocument
        text = node.get_content(metadata_mode=MetadataMode.NONE)
        tei = TEIDocument(text)
        
        tei_nodes = []
        last_tag = None

        tags = self.tags
        for tag in tags:
            
            tei_property = getattr(tei,tag)
            
            if isinstance(tei_property, str):
                tag_text = tei_property 
                last_tag = tag
                tei_nodes.append(
                    self._build_node_from_split(
                        tag_text.strip(), node, {"tag": last_tag}
                    )
                )
                
            elif isinstance(tei_property, list):
                for sec in tei_property:
                    tag_text = sec.text
                    last_tag = sec.title if sec.title else "Unnamed Section"
                    tei_nodes.append(
                        self._build_node_from_split(
                            tag_text.strip(), node, {"tag": last_tag}
                        )
                    )
                

        return tei_nodes
    
    def _build_node_from_split(
        self,
        text_split: str,
        node: BaseNode,
        metadata: dict,
    ) -> TextNode:
        """Build node from single text split."""
        node = build_nodes_from_splits([text_split], node, id_func=self.id_func)[0]

        if self.include_metadata:
            node.metadata = {**node.metadata, **metadata}

        return node