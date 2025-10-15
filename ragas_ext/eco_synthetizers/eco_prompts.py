import typing as t
from pydantic import BaseModel
from ragas.prompt import PydanticPrompt
from ragas.testset.persona import Persona
from ragas.testset.synthesizers.single_hop.prompts import GeneratedQueryAnswer
from ragas.testset.synthesizers.multi_hop.prompts import QueryConditions

class QueryConditionEco(BaseModel):
    persona: Persona
    ecocontext: t.Dict[str, t.List[str]]
    query_style: str
    query_length: str
    context: str

class QueryAnswerGenerationPromptEco(PydanticPrompt[QueryConditionEco, GeneratedQueryAnswer]):
    instruction: str = (
        "Generate a single-hop query and answer based on the specified conditions "
        "(persona, ecological context with location, ecosystem, species, and challenge) "
        "and the provided node context.\n\n"
        "### Goals\n"
        "1. Create a question that reflects the persona's perspective and integrates the ecological context elements.\n"
        "2. Produce an answer that is fully grounded in the provided context, without adding external information.\n\n"
        "### Style Requirements\n"
        "- Reduce lexical overlap of the query from the context whenever possible, while preserving meaning.\n"
        "- Avoid **copying long sequences of words** from the context (no more than 3–4 consecutive identical words).\n"
        "- You may **paraphrase key terms** (e.g., 'drought' → 'water scarcity', 'restoration project' → 'rehabilitation effort') "
        "as long as the meaning remains faithful.\n"
        "- The query should sound natural and insightful, not like a restatement of a sentence from the context.\n\n"
        "### Steps\n"
        "1. **Generate a Query**: Based on the persona and ecological context (location, ecosystem, species, challenges), "
        "formulate a question that reflects curiosity or analytical intent, not just surface-level recall.\n"
        "2. **Generate an Answer**: Use only the information contained in the node context, but express it with varied language "
        "and natural phrasing."
    )

    input_model: t.Type[QueryConditionEco] = QueryConditionEco
    output_model: t.Type[GeneratedQueryAnswer] = GeneratedQueryAnswer

    examples: t.List[t.Tuple[QueryConditionEco, GeneratedQueryAnswer]] = [
        (
            QueryConditionEco(
                persona=Persona(
                    name="Ecological practitioner",
                    role_description="Focuses on ecological restoration and management practices."
                ),
                ecocontext={
                    "locations": ["Amazon"],
                    "ecosystems": ["tropical dry forest"],
                    "species": ["Caesalpinia ferrea"],
                    "challenges": ["drought"]
                },
                query_style="Formal",
                query_length="Medium",
                context=(
                    "In the Amazon rainforest, restoration efforts focus on replanting native tree species. "
                    "Tropical dry forest areas in Brazil are particularly affected by drought, and projects "
                    "often include Caesalpinia ferrea to improve ecosystem recovery."
                ),
            ),
            GeneratedQueryAnswer(
                query="What strategies are recommended for selecting tree species in tropical dry forest restoration projects in the Amazon?",
                answer=(
                    "For restoration in the tropical dry forests of the Amazon, species selection should include "
                    "Caesalpinia ferrea to improve ecosystem recovery, "
                    "while considering challenges such as drought."
                ),
            )
        ),
        (
            QueryConditionEco(
                persona=Persona(
                    name="Forest restoration researcher",
                    role_description="Studies post-fire forest recovery dynamics and reforestation strategies."
                ),
                ecocontext={
                    "locations": ["Colorado", "Western United States"],
                    "ecosystems": ["montane forest"],
                    "species": ["Pinus ponderosa", "Pseudotsuga menziesii"],
                    "challenges": ["wildfire", "climate change"]
                },
                query_style="Informative",
                query_length="Medium",
                context=(
                    "Following severe wildfires in the montane forests of Colorado, large-scale replanting efforts "
                    "are underway to restore forest cover. Research indicates that seedling survival after the first "
                    "growing season is highly variable and influenced by factors such as long-term climate, "
                    "post-planting weather conditions, species selection, and seed source location. "
                    "Topography, time since fire, and fire severity also play important roles in determining outcomes."
                ),
            ),
            GeneratedQueryAnswer(
                query="What are the best conditions for replanting forests after a fire in Colorado?",
                answer=(
                    "The best conditions for replanting forests after a fire typically include favorable weather, "
                    "careful selection of tree species suited to local montane environments such as Pinus ponderosa and "
                    "Pseudotsuga menziesii, and consideration of topography and burn severity. "
                    "Recent studies in Colorado show that long-term climate, post-planting weather, and seed source "
                    "location are strong predictors of early seedling survival."
                ),
                ),
            ),

    ]
    
class QueryAnswerGenerationPromptMultiEco(PydanticPrompt[QueryConditions, GeneratedQueryAnswer]):
    instruction: str = (
        "Generate a multi-hop query and answer grounded in the ecological restoration domain. "
        "Use the provided persona, themes, style, and length to guide tone and focus. "
        "The context contains multiple text segments (<1-hop>, <2-hop>, etc.), each describing "
        "different but related aspects of restoration processes, such as site conditions, interventions, or outcomes.\n\n"
        "### Instructions:\n"
        "1. **Generate a Multi-Hop Query**:\n"
        "   - Combine information from at least **two distinct context segments** (e.g., `<1-hop>` and `<2-hop>`). "
        "   - Ensure the question can only be answered by reasoning across these segments — e.g., linking causes, mechanisms, or effects.\n"
        "   - Explicitly integrate one or more of the provided **themes** in the query.\n"
        "   - Keep the query realistic and relevant to restoration ecology (e.g., soil recovery, reforestation success, hydrological effects, biodiversity response).\n\n"
        "2. **Generate an Answer**:\n"
        "   - Base the answer only on the provided context — do not add external information.\n"
        "   - Synthesize content from **both** segments into a coherent explanation.\n"
        "   - Clearly reflect the multi-hop reasoning that connects the two pieces of information (e.g., intervention → ecological outcome).\n\n"
        "3. **Multi-Hop Context Tags**:\n"
        "   - Each context segment is tagged as `<1-hop>`, `<2-hop>`, etc.\n"
        "   - Your question must integrate evidence or concepts from at least two segments."
        "### Style Requirements\n"
        "- Reduce lexical overlap of the query from the context whenever possible, while preserving meaning.\n"
        "- Avoid **copying long sequences of words** from the context (no more than 3–4 consecutive identical words).\n"
        "- You may **paraphrase key terms** (e.g., 'drought' → 'water scarcity', 'restoration project' → 'rehabilitation effort') "
        "as long as the meaning remains faithful.\n"
        "- The query should sound natural and insightful, not like a restatement of a sentence from the context.\n\n"
    )

    input_model: t.Type[QueryConditions] = QueryConditions
    output_model: t.Type[GeneratedQueryAnswer] = GeneratedQueryAnswer

    examples: t.List[t.Tuple[QueryConditions, GeneratedQueryAnswer]] = [
        (
            QueryConditions(
                persona=Persona(
                    name="Restoration Ecologist",
                    role_description="Focuses on the ecological mechanisms and practical strategies behind habitat recovery.",
                ),
                themes=["Soil Reclamation", "Native Species Establishment"],
                query_style="Analytical",
                query_length="Medium",
                context=[
                    "<1-hop> In degraded tropical areas, soil reclamation often involves amendments such as compost or biochar to improve nutrient cycling.",
                    "<2-hop> The establishment of native tree species depends strongly on improved soil fertility and microbial activity following such interventions.",
                ],
            ),
            GeneratedQueryAnswer(
                query=(
                    "How does soil reclamation using organic amendments support the establishment of native species in degraded tropical ecosystems?"
                ),
                answer=(
                    "Soil reclamation using organic amendments like compost or biochar enhances nutrient cycling and microbial activity, "
                    "which improves soil fertility. This enriched soil environment, in turn, supports the establishment and growth "
                    "of native tree species in degraded tropical ecosystems by providing better rooting conditions and nutrient availability."
                ),
            ),
        ),
        (
            QueryConditions(
                persona=Persona(
                    name="Ecological Restoration Manager'r",
                    role_description="Designs and evaluates ecosystem restoration projects, focusing on target definition and reference ecosystem selection.",
                ),
                themes=["Restoration Planning", "Ecosystem Targeting"],
                query_style="Analytical",
                query_length="Medium",
                context=[
                    "<1-hop> Forest restoration aims to accelerate natural succession toward a self-sustaining climax forest ecosystem — the target ecosystem.",
                    "<2-hop> Defining this target requires identifying reference sites that represent the desired end-state of restoration. These sites should match the project's conditions in terms of climate, topography, and forest type.",
                    "<3-hop> Existing tools like GIS mapping platforms (e.g., Google Earth) and ecological databases (e.g., GBIF, vegetation classification maps) can support the identification and characterization of suitable reference ecosystems."
                ],
            ),
            GeneratedQueryAnswer(
                query=(
                    "What is a good way to set a restoration target for an ecosystem type, and are there existing off-the-shelf tools that can help with this?"
                ),
                answer=(
                    "A good way to set a restoration target is to define a reference ecosystem that represents the desired end-state of the project. "
                    "This involves surveying relatively undisturbed remnants of the same climax forest type and ensuring they share similar environmental "
                    "conditions—such as elevation, slope, and aspect—with the restoration site. "
                    "Tools like topographic maps, Google Earth, vegetation classification systems, and global biodiversity databases such as GBIF "
                    "can be used to locate and characterize these reference sites effectively."
                ),
            )
        ),
    ]