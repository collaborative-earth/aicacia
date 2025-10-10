import typing as t
from dataclasses import dataclass
from pydantic import BaseModel
from ragas.prompt import PydanticPrompt, StringIO
from ragas.testset.graph import Node
from ragas.testset.transforms.base import LLMBasedExtractor

CONTEXT_INSTRUCTION = """
Given the following text chunk, extract the following elements as Python lists.
For challenges, include both explicit environmental problems (e.g., drought, deforestation, pollution)
and any human interventions, management practices, or activities that are relevant constraints
or considerations for ecosystem restoration (e.g., soil reclamation, controlled burning, irrigation practices).

Return exactly four Python lists in the order:

1. Locations: specific places mentioned (city, region, country, e.g., "Amazon", "California", "Brazil")
2. Ecosystems: ecosystem types mentioned (forest, wetland, grassland, etc.)
3. Species: flora or fauna mentioned (e.g., "Caesalpinia ferrea", "Pinus sylvestris")
4. Challenges: environmental challenges and management interventions affecting the ecosystem

"""
class EcoContext(BaseModel):
    locations: t.List[str]
    ecosystems: t.List[str]
    species: t.List[str]
    challenges: t.List[str]

class ContextExtractorPrompt(PydanticPrompt[StringIO, StringIO]):
    instruction: str = CONTEXT_INSTRUCTION
    input_model: t.Type[StringIO] = StringIO
    output_model: t.Type[EcoContext] = EcoContext
    examples: t.List[t.Tuple[StringIO, EcoContext]] = [
    (
        StringIO(
            text=(
                "In the Amazon rainforest, restoration efforts focus on replanting native tree species. "
                "Tropical dry forest areas in Brazil are particularly affected by drought, and projects "
                "often include Caesalpinia ferrea and Handroanthus impetiginosus to improve ecosystem recovery."
            )
        ),
        EcoContext(
            locations=["Amazon", "Brazil"],
            ecosystems=["tropical dry forest"],
            species=["Caesalpinia ferrea", "Handroanthus impetiginosus"],
            challenges=["drought"]
        ),
    )
    ]

@dataclass
class ContextExtractor(LLMBasedExtractor):
    """
    Extracts context from the given text.

    Attributes
    ----------
    property_name : str
        The name of the property to extract. 
    prompt : ThemesExtractorPrompt
        The prompt used for extraction.
    """

    property_name: str = "ecocontext"
    prompt: ContextExtractorPrompt = ContextExtractorPrompt()

    async def extract(self, node: Node) -> t.Tuple[str, t.List[str]]:
        node_text = node.get_property("page_content")
        if node_text is None:
            return self.property_name, []
        result = await self.prompt.generate(
            self.llm,
            data=StringIO(text=node_text),
        )


        return self.property_name, result.model_dump()