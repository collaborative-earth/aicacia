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
        "### Instructions:\n"
        "1. **Generate a Query**: Based on the context, persona, ecological context, style, and length, create a question "
        "that aligns with the persona's intent, knowledge and terminology and incorporates at least one concept among location,"
        "ecosystem, species, and challenge from the ecological context."
        "2. **Generate an Answer**: Using only the content from the provided context, construct a detailed answer "
        "to the query. Do not add any information not included in or inferable from the context.\n"
        "### Style\n"
        "- Reduce lexical overlap of the query from the context whenever possible, while preserving meaning and persona terminology.\n"
        "- Avoid **copying long sequences of words (>4)** from the context.\n"
        "- You may **paraphrase key terms** (e.g., 'drought' → 'water scarcity', 'restoration project' → 'rehabilitation effort') "
        "as long as the meaning remains faithful.\n"
        "- Formulate the question naturally using varied starters (How, What, Why, Which) depending on the persona."
    )

    input_model: t.Type[QueryConditionEco] = QueryConditionEco
    output_model: t.Type[GeneratedQueryAnswer] = GeneratedQueryAnswer

    examples: t.List[t.Tuple[QueryConditionEco, GeneratedQueryAnswer]] = [
        (
            QueryConditionEco(
                persona=Persona(
                    name="Quantitative Restoration Technician",
                    role_description=(
                        """
                        Implements field measurements, remote-sensing analysis, and monitoring protocols. 
                        Works with precise definitions, thresholds, and data-collection methodologies.
                        Technical terminology, high technical knowledge, quantitative intent (numbers).
                        """
                    )
                ),
                ecocontext={
                    "locations": ["Amazon"],
                    "ecosystems": ["tropical dry forest"],
                    "species": [],
                    "challenges": ["forest restoration"]
                },
                query_style="PERFECT_GRAMMAR",
                query_length="Short",
                context=(
                    """
                    Natural regeneration, if present in sufficient density, can restore forest cover on
                    its own within a few years. As a general rule, in the humid tropics (e.g., Amazon), 800 well-distributed
                    natural seedlings per hectare should be sufficient to achieve canopy cover within three
                    years. In seasonally dry tropics, the minimum seedling density required range from 1 600
                    per ha (to restore basic forest structure within five years) to 3 000 per ha (to initiate canopy
                    closure within two years) without enrichment planting (see Elliott et al., Section 3.1). Such
                    general guidelines should be communicated to practitioners to help improve restoration
                    success.
                    """
                ),
            ),
            GeneratedQueryAnswer(
                query="At what density should I plant trees in a tropical forest restoration project?",
                answer=(
                    """
                    Tree densities suitable for tropical forest restoration generally range from around 800 seedlings/ha 
                    in humid regions to 1600–3000 seedlings/ha in seasonally dry areas, depending on how quickly canopy 
                    closure is desired.
                    """
                ),
            )
        ),
        (
            QueryConditionEco(
                persona=Persona(
                    name="Ecological Restoration Manager",
                    role_description=(
                        """
                        Oversees planning, budgeting, and coordination of restoration projects. Focuses on practical outcomes (survival rates,
                        landscape connectivity, intervention choices)and must balance ecological goals with logistical and financial constraints.
                        Specific terminology, project designing intent, mid-high knowledge of whole restoration process."""
                    )
                ),
                ecocontext={
                    "locations": ["Colorado", "Western United States"],
                    "ecosystems": ["montane forest"],
                    "species": ["Pinus ponderosa", "Pseudotsuga menziesii"],
                    "challenges": ["wildfire", "climate change"]
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
                query="What are the best conditions for replantng forests after a fire in Colrado?",
                answer=(
                    "The best conditions for replanting forests after a fire typically include favorable weather, "
                    "careful selection of tree species suited to local montane environments such as Pinus ponderosa and "
                    "Pseudotsuga menziesii, and consideration of topography and burn severity. "
                    "Recent studies in Colorado show that long-term climate, post-planting weather, and seed source "
                    "location are strong predictors of early seedling survival."
                ),
                ),
            ),
        (
            QueryConditionEco(
                persona=Persona(
                    name="Community Restoration Volunteer",
                    role_description=(
                    """
                    Participates in hands-on restoration events. Asks about simple practices, why actions matter, and how to 
                    avoid mistakes in the field. Informal terminology, low domain scientific knowledge, practical curiosity 
                    (planting, maintenance)."""
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
                    """
                    Bare root plants (like rose bushes) can be stored in a cool, dark place before planting. Some good options include:A garage or shed
                    A basement or cellar An unheated room in your house A shady spot outdoors If you store your bare root plants in a cool,
                    dark place, they will stay dormant and will not start to grow. This will give you time to plant them when the weather is
                    right. Be sure to store in a dark location until you are ready to plant.When storing bare root plants, it is important 
                    to keep the roots moist. You can do this by wrapping the roots in damp burlap or newspaper and placing them in a plastic 
                    bag. Be sure to open the bag every few days to let in some fresh air.
                    """
                ),
            ),
            GeneratedQueryAnswer(
                query="store bare root plants before planting”",
                answer=(
                        "Store bareroot plants in a cool, dark spot like a garage or shed, and keep the roots moist by wrapping "
                        "them in damp burlap or newspaper inside a loose plastic bag. Open the bag every few days for air and plant "
                        "them when conditions are right."
                    ),
                ),
            )

    ]
    
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