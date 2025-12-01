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


    
class QueryAnswerGenerationPromptMultiEco(PydanticPrompt[QueryConditions, GeneratedQueryAnswer]):
    instruction: str = (
        "Generate a multi-hop query and answer based on the provided conditions "
        "(persona, ecological context with locations, ecosystems, species, and challenges) "
        "and the provided multi-segment node context and the themes they share.\n\n"
        "### Instructions:\n"
        "1. **Generate a Multi-Hop Query**: Use the provided context segments and themes to form a query that requires combining "
        "information from multiple segments (e.g., `<1-hop>` and `<2-hop>`). Ensure the query explicitly incorporates one or more "
        "themes and reflects their relevance to the context. Formulate question with analytical or actionable intent.\n"
        "2. **Generate an Answer**: Use only the content from the provided context to create a detailed and faithful answer to "
        "the query. Avoid adding information that is not directly present or inferable from the given context.\n"
        "3. **Multi-Hop Context Tags**:\n"
        "   - Each context segment is tagged as `<1-hop>`, `<2-hop>`, etc.\n"
        "   - Ensure the query uses information from at least two segments and connects them meaningfully."
        "### Style\n"
        "- Reduce lexical overlap of the query from the contexts whenever possible, while preserving meaning.\n"
        "- Avoid **copying long sequences of words** from the context (no more than 3–4 consecutive identical words).\n"
        "- You may **paraphrase key terms** (e.g., 'drought' → 'water scarcity', 'restoration project' → 'rehabilitation effort') "
        "as long as the meaning remains faithful.\n"
        "- Formulate the question naturally using varied starters (How, What, Why, Which) depending on the persona."

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
    
    
class QueryAnswerGenerationPromptEco(PydanticPrompt[QueryConditionEco, GeneratedQueryAnswer]):
    instruction: str = ("""
        **Instructions:**\n
        Generate **one single-hop query** and its **answer** based strictly on the provided context. The query must follow the persona, style, and length specified,
        Ensure the answer is entirely faithful to the context, using only the information directly from the provided context.\n
        \n
       ### Requirements\n
        1. **Query:**\n
        - Must align with the persona perspective.\n
        - Include at least one ecological element from the context.\n
        - Match the specified style and length.\n
        - Each persona asks a fundamentally different type of question.\n
        - Generate the question first based on persona and ecological context.\n
        - If style is WEB_SEARCH, remove some words (and, for, which, what).\n
        - If style is MISSPELLED, introduce spelling errors (remove letters inside the word, exchange them).\n
        2. **Answer:**\n
        - Must be entirely faithful to the provided context.\n
        - Do **not** add any external information.\n
        - Be detailed and self-contained.\n

        """

    )

    input_model: t.Type[QueryConditionEco] = QueryConditionEco
    output_model: t.Type[GeneratedQueryAnswer] = GeneratedQueryAnswer

    examples: t.List[t.Tuple[QueryConditionEco, GeneratedQueryAnswer]] = [
        # Example 1: Technical context about tree planting density
        (
            QueryConditionEco(
                persona=Persona(
                    name="Quantitative Restoration Technician",
                    role_description=(
                        "Implements field measurements, remote-sensing analysis, and monitoring protocols. "
                        "Works with precise definitions, thresholds, and data-collection methodologies. "
                        "Technical terminology, high technical knowledge, quantitative intent."
                    )
                ),
                ecocontext={
                    "locations": ["Amazon"],
                    "ecosystems": ["tropical dry forest"],
                    "species": [],
                    "challenges": ["forest restoration"]
                },
                query_style="PERFECT_GRAMMAR",
                query_length="Medium",
                context=(
                    "Natural regeneration, if present in sufficient density, can restore forest cover on "
                    "its own within a few years. As a general rule, in the humid tropics (e.g., Amazon), 800 well-distributed "
                    "natural seedlings per hectare should be sufficient to achieve canopy cover within three "
                    "years. In seasonally dry tropics, the minimum seedling density required range from 1 600 "
                    "per ha (to restore basic forest structure within five years) to 3 000 per ha (to initiate canopy "
                    "closure within two years) without enrichment planting."
                ),
            ),
            GeneratedQueryAnswer(
                query="What seedling density thresholds are needed for canopy closure in tropical dry forest restoration?",
                answer=(
                    "In seasonally dry tropics, minimum densities range from 1,600 seedlings/ha for basic forest "
                    "structure within five years to 3,000 seedlings/ha for canopy closure within two years. "
                    "Humid tropical regions require approximately 800 well-distributed seedlings/ha to achieve "
                    "canopy cover in three years."
                ),
            )
        ),
        
        # Example 2: Same context, different persona
        (
            QueryConditionEco(
                persona=Persona(
                    name="Community Restoration Volunteer",
                    role_description=(
                        "Participates in hands-on restoration events. Asks about simple practices, why actions matter, "
                        "and how to avoid mistakes in the field. Informal terminology, low domain scientific knowledge, "
                        "practical curiosity."
                    )
                ),
                ecocontext={
                    "locations": ["Amazon"],
                    "ecosystems": ["tropical forest"],
                    "species": [],
                    "challenges": ["reforestation"]
                },
                query_style="CONVERSATIONAL",
                query_length="Short",
                context=(
                    "Natural regeneration, if present in sufficient density, can restore forest cover on "
                    "its own within a few years. As a general rule, in the humid tropics (e.g., Amazon), 800 well-distributed "
                    "natural seedlings per hectare should be sufficient to achieve canopy cover within three "
                    "years. In seasonally dry tropics, the minimum seedling density required range from 1 600 "
                    "per ha (to restore basic forest structure within five years) to 3 000 per ha (to initiate canopy "
                    "closure within two years) without enrichment planting."
                ),
            ),
            GeneratedQueryAnswer(
                query="Can the forest grow back on its own without us planting trees?",
                answer=(
                    "Yes, if there are enough young trees already growing naturally (at least a few per small area), "
                    "the forest can recover by itself within a few years. Otherwise, you'll need to plant to help it along."
                ),
            )
        ),
        
        # Example 3: Wildfire context with Manager persona
        (
            QueryConditionEco(
                persona=Persona(
                    name="Ecological Restoration Manager",
                    role_description=(
                        "Oversees planning, budgeting, and coordination of restoration projects. "
                        "Speaks in medium-length, slightly complex sentences focusing on trade-offs, "
                        "predictability, site prioritization, and resource allocation."
                    )
                ),
                ecocontext={
                    "locations": ["Colorado"],
                    "ecosystems": ["montane forest"],
                    "species": ["Pinus ponderosa"],
                    "challenges": ["wildfire", "replanting"]
                },
                query_style="MISSPELLED",
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
                query="What factors should guide our site prioritization when plannig ponderosa pine replanting after wildifre in Colorado?",
                answer=(
                    "Survival depends on long-term climate patterns, topography, fire severity, and seed source matching. "
                    "Sites with favorable climate, appropriate topography, and moderate burn severity will likely show "
                    "better establishment. Time since fire also matters, so prioritize sites where these factors align "
                    "with available resources."
                ),
            ),
        ),
        
        # Example 4: Bare root planting for Volunteer with web search style
        (
            QueryConditionEco(
                persona=Persona(
                    name="Community Restoration Volunteer",
                    role_description=(
                        "Participates in hands-on restoration events. Asks about simple practices, why actions matter, "
                        "and how to avoid mistakes. Informal terminology, low scientific knowledge, practical curiosity."
                    )
                ),
                ecocontext={
                    "locations": [],
                    "ecosystems": [],
                    "species": ["roses"],
                    "challenges": ["bare root planting"]
                },
                query_style="Web Search",
                query_length="Short",
                context=(
                    "Bare root plants (like rose bushes) can be stored in a cool, dark place before planting. Some good options include: "
                    "A garage or shed, a basement or cellar, an unheated room, or a shady spot outdoors. Store in a dark location "
                    "until you are ready to plant. When storing bare root plants, keep the roots moist by wrapping them in damp "
                    "burlap or newspaper and placing them in a plastic bag. Open the bag every few days to let in fresh air."
                ),
            ),
            GeneratedQueryAnswer(
                query="bare root rose storage before planting",
                answer=(
                    "Keep bare root roses in a cool, dark spot like a garage or basement. Wrap the roots in damp burlap "
                    "or newspaper inside a loose plastic bag, and open it every few days for air. Plant when conditions are right."
                ),
            ),
        ),
    ]