from typing import List, Optional
from llama_index.core.schema import TransformComponent, NodeWithScore, MetadataMode
from llama_index.core.bridge.pydantic import Field

DEFAULT_VALID_TAGS = ['abstract', 'introduction', 'discussion']

class TEINodeFilter(TransformComponent):
    """
    A TransformComponent that filters nodes based on their TEI tags.
    
    Attributes:
        valid_tags: List of valid tags to keep. Nodes with tags not in this list
                   will be filtered out.
    """
    is_text_node_only: bool = True
    
    valid_tags: List[str] = Field(
        default_factory=lambda: DEFAULT_VALID_TAGS.copy(),
        description="List of valid tags to keep. Nodes with tags not in this list will be filtered out."
    )
    show_progress: bool = Field(
        default=True,
        description="Whether to show progress during filtering."
    )
    reverse: bool = Field(
        default=False,
        description="If True, keeps nodes without the valid tags instead of filtering them out."
    )
    
    def __call__(self, nodes: List[NodeWithScore], **kwargs) -> List[NodeWithScore]:
        """
        Filter nodes based on their TEI tags.
        
        Args:
            nodes: List of nodes to filter.
            **kwargs: Additional keyword arguments (not used but required by interface).
        
        Returns:
            List of filtered nodes.
        """
        if self.reverse:
            filtered_nodes = [
                node for node in nodes
                if node.metadata.get('tag', '').strip().lower() not in self.valid_tags
                and node.get_content(metadata_mode=MetadataMode.NONE).strip()
            ]
        else:
            filtered_nodes = [
                node for node in nodes
                if node.metadata.get('tag', '').strip().lower() in self.valid_tags
                and node.get_content(metadata_mode=MetadataMode.NONE).strip()
            ]
        
        return filtered_nodes