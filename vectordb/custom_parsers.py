import json
from typing import TYPE_CHECKING, Any, List, Optional, Sequence
from llama_index.core.bridge.pydantic import Field
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.node_parser.node_utils import build_nodes_from_splits
from llama_index.core.schema import BaseNode, MetadataMode, TextNode
from llama_index.core.node_parser.interface import NodeParser
from llama_index.core.utils import get_tqdm_iterable

from extraction.src.aicacia_extraction.grobid import IDNOType, TEIDocument

DEFAULT_TAGS = ['abstract','sections']
DEFAULT_EXCLUDED_TAGS = ["FIGURE","TABLE"]

    
class MyJSONNodeParser(NodeParser):
    '''
    Custom parser for extracting and processing text from JSON documents.

    This parser handles JSON inputs with a chapter structure, concatenates
    content using Markdown-style headers, and merges adjacent chapters if 
    their content length is below a specified minimum (`min_len`), and form a list of llama index nodes.

    Attributes:
        excluded_tags (List[str]): tags to exclude from text extraction (default FIGURE and TABLES).
        min_len (int): Minimum character length for a text chunk.
    '''
    excluded_tags: List[str] = Field(
        default=DEFAULT_EXCLUDED_TAGS, description="Tags of chapters to exclude from "
    )
    min_len: int = Field(
        default=500, description="Minimum character lengths for text chunks independent."
    )

    @classmethod
    def from_defaults(
        cls,
        include_metadata: bool = True,
        include_prev_next_rel: bool = True,
        callback_manager: Optional[CallbackManager] = None,
        excluded_tags: Optional[List[str]] = DEFAULT_EXCLUDED_TAGS,
    ) -> "MyJSONNodeParser":
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


    def _concatenate_chapters_markdown(self,chapters):
        """Concatenate chapters contained in custom json files using Markdown-style headers."""
        results = []
        processed_chapters = set()  
        for idx, chapter in enumerate(chapters):
            chapter_type = chapter["type"]
            if (chapter_type in self.excluded_tags) | (idx in processed_chapters):
                continue

            header_text = chapter["header"]["extracted_text"]
            elements_text = "\n".join([element["extracted_text"] for element in chapter["elements"]])
            markdown_text = f"## {header_text}\n\n"  # Assuming level 2 header
            concatenated_text = markdown_text + elements_text

            # If chapter type is DEFAULT and concatenated text is too short, consider the adjacent chapters
            if chapter_type == "DEFAULT":
                lookup = 0
                while len(concatenated_text) < self.min_len:
                    if idx+lookup < len(chapters) - 1:
                        next_chapter = chapters[idx + 1+ lookup]
                        if next_chapter["type"] == "DEFAULT" and (idx + 1+lookup) not in processed_chapters:
                            next_text = f"## {next_chapter['header']['extracted_text']}\n\n" + \
                                        " ".join([element["extracted_text"] for element in next_chapter["elements"]])
                            concatenated_text = concatenated_text + "\n\n" + next_text
                            processed_chapters.add(idx + lookup + 1)
                        lookup +=1
                    else:
                        break
            results.append(concatenated_text)
            processed_chapters.add(idx)
        return results

    def get_nodes_from_node(self, node: BaseNode) -> List[TextNode]:
        """Get nodes from document."""
        nodes = []
        text = node.get_content(metadata_mode=MetadataMode.NONE)
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return []
        chapters = data["chapters"]
        concatenated_chapters = self._concatenate_chapters_markdown(chapters)
        nodes = build_nodes_from_splits(concatenated_chapters,node)
        return nodes