import typing as t
from pydantic import BaseModel
from ragas.prompt import PydanticPrompt
from ragas.testset.persona import Persona
from ragas.testset.synthesizers.single_hop.prompts import GeneratedQueryAnswer
from ragas.testset.synthesizers.multi_hop.prompts import QueryConditions
from ragas_ext.utils.eco_personas import *

class QueryConditionEco(BaseModel):
    persona: Persona
    ecothemes: t.Dict[str, t.List[str]]
    theme : str
    query_style: str
    query_length: str
    context: str
    

class QueryAnswerGenerationPromptEco(PydanticPrompt[QueryConditionEco, GeneratedQueryAnswer]):
    instruction: str = ("""
            Generate a single-hop query and its answer using only the provided context.
            You must strictly follow all the constraints below.
            ────────────────────────────────────────
            1. PERSONA: style, vocabulary, perspective
            ────────────────────────────────────────
            Write the query exactly as this persona would:
            - Volunteer → informal, friendly, very simple words, no technical and scientifical phrasing.
            - Manager → planning-oriented, decision-focused, mentions priorities, constraints and strategy.
            - Technician → quantitative, mentions thresholds, values, metrics.
            - Researcher → analytical, causal, comparative, evidence-based wording.
            ────────────────────────────────────────
            2. THEME + ECOTHEMES
            ────────────────────────────────────────
            Your query must:
            - Center on the given theme, but might paraphrise.
            - Include at least one ecological theme (locations, ecosystems, species, or challenges).
            - Avoid copying more than 3–4 words from the context.
            ────────────────────────────────────────
            3. QUERY STYLE AND LENGTH
            ────────────────────────────────────────
            After generating the query, adjust it if necessary so that both style and length constraints 
            are satisfied exactly.
            `query_style`:
            - If WEB_SEARCH → keyword-like query; remove function words (the, for, and, which, how, etc.).
            - If MISSPELLED → include natural misspellings, swap close letters, miss ones; sentence still understandable.
            - If PERFECT_GRAMMAR → fully standard grammar, formal.
            `query_length`:
            - Short → fewer than 10 words.
            - Medium → 10–20 words.
            - Long → 20–30 words.
            ────────────────────────────────────────
            4. ANSWER
            ────────────────────────────────────────
            Generate an answer that:
            - Uses only the information from the context.
            - Contains no external knowledge.
            - Is concise, factual, and consistent with the context.
            """
    )

    input_model: t.Type[QueryConditionEco] = QueryConditionEco
    output_model: t.Type[GeneratedQueryAnswer] = GeneratedQueryAnswer

    examples: t.List[t.Tuple[QueryConditionEco, GeneratedQueryAnswer]] = [
        # Example 1: Technical context about tree planting density
        (
            QueryConditionEco(
                persona=technician,
                ecothemes={
                    "locations": ["Amazon"],
                    "ecosystems": ["tropical dry forest"],
                    "species": [],
                    "challenges": ["forest restoration"]
                },
                theme = "seedling density",
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
                persona=volunteer,
                ecothemes={
                    "locations": ["Amazon"],
                    "ecosystems": ["tropical forest"],
                    "species": [],
                    "challenges": ["reforestation"]
                },
                theme = "forest regeneration",
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
                persona= manager,
                ecothemes={
                    "locations": ["Colorado"],
                    "ecosystems": ["montane forest"],
                    "species": ["Pinus ponderosa"],
                    "challenges": ["wildfire", "replanting"]
                },
                theme = "site prioritization",
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
                persona=volunteer,
                ecothemes={
                    "locations": [],
                    "ecosystems": [],
                    "species": ["roses"],
                    "challenges": ["bare root planting"]
                },
                theme = "bare root storage",
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
    
class QueryAnswerGenerationPromptMultiEco(PydanticPrompt[QueryConditions, GeneratedQueryAnswer]):
    instruction: str = ("""
        Generate a multi-hop query and its answer using only the provided multi-segment context.
        You must strictly follow all constraints below.
        ────────────────────────────────────────
        1. PERSONA: style, vocabulary, perspective
        ────────────────────────────────────────
        Write the query exactly as this persona would:

        - Volunteer → informal, friendly, very simple words; no technical or scientific phrasing.
        - Manager → planning-oriented, decision-focused; mentions priorities, constraints, and strategy.
        - Technician → quantitative; mentions thresholds, values, metrics, comparisons.
        - Researcher → analytical, causal, comparative; evidence-based wording.

        ────────────────────────────────────────
        2. THEME + ECOLOGICAL CONTEXT
        ────────────────────────────────────────
        Your query must:
        - Center on the provided theme(s), possibly paraphrased.
        - Explicitly include ecological elements such as locations, ecosystems, species, or environmental challenges.
        - Connect information across multiple context segments (e.g., <1-hop> and <2-hop>).
        - Avoid copying more than 3–4 consecutive words from any context segment.

        ────────────────────────────────────────
        3. MULTI-HOP LOGIC
        ────────────────────────────────────────
        - Each context segment is tagged as `<1-hop>`, `<2-hop>`, etc.
        - The query must require reasoning across at least two context segments.
        - Each hop should contribute distinct information (e.g., cause → effect, constraint → outcome, location → intervention).
        - The connection between hops must be explicit or logically necessary to answer the query.

        ────────────────────────────────────────
        4. QUERY STYLE AND LENGTH
        ────────────────────────────────────────
        After generating the query, revise it so both constraints are satisfied exactly.

        query_style:
        - WEB_SEARCH → keyword-like query; remove function words (the, and, for, how, which, etc.).
        - MISSPELLED → include natural misspellings or swapped letters; sentence still understandable.
        - PERFECT_GRAMMAR → fully standard grammar and formal structure.

        query_length:
        - Short → fewer than 10 words.
        - Medium → 10–20 words.
        - Long → 20–30 words.

        ────────────────────────────────────────
        5. ANSWER
        ────────────────────────────────────────
        Generate an answer that:
        - Uses only information from the provided context segments.
        - Integrates evidence from all required hops.
        - Adds no external knowledge or unsupported inference.
        - Is concise, factual, and internally consistent with the context.
        """
    )

    input_model: t.Type[QueryConditions] = QueryConditions
    output_model: t.Type[GeneratedQueryAnswer] = GeneratedQueryAnswer

    examples: t.List[t.Tuple[QueryConditions, GeneratedQueryAnswer]] = [
        (
            QueryConditions(
                persona=technician,
                themes=["seedling density", "canopy closure"],
                query_style="PERFECT_GRAMMAR",
                query_length="Medium",
                context=[
                    "<1-hop> In the humid tropics such as the Amazon, around 800 well-distributed natural seedlings per hectare are sufficient to achieve canopy cover within three years without planting.",
                    "<2-hop> In seasonally dry tropical forests, higher seedling densities are required because water stress slows early growth. Densities between 1,600 and 3,000 seedlings per hectare determine whetherbasic forest structure or rapid canopy closure is achieved.",
                ],
            ),
            GeneratedQueryAnswer(
                query=(
                    "What seedling density thresholds are needed for canopy closure in tropical dry forest restoration compared to humid Amazon forests?"
                ),
                answer=(
                    "Humid Amazon forests can reach canopy cover with about 800 well-distributed seedlings per hectare "
                    "within three years. In contrast, tropical dry forests require higher densities, ranging from "
                    "1,600 seedlings per hectare for basic structure to around 3,000 per hectare to achieve faster canopy closure."
                ),
            ),
        ),
        (
            QueryConditions(
                persona= volunteer,
                themes=["Restoration Planning", "Ecosystem Targeting"],
                query_style="CONVERSATIONAL",
                query_length="Short",
                context=[   
                    "<1-hop> Natural regeneration can restore forest cover within a few years if enough seedlings are alreadypresent, particularly in humid tropical forests like the Amazon.",
                    "<2-hop> In drier tropical areas, natural seedlings are not likely to survive without help, and forest recovery may stall unless planting or protection is added.",     
                ],
            ),
            GeneratedQueryAnswer(
                query=(
                    "Can forest grow back on its own in dry and humid tropical areas"
                ),
                answer=(
                    "In humid tropical places like the Amazon, forests can grow back on their own if enough young trees "
                    "are already there. In drier tropical areas, recovery is harder, and the forest often needs extra "
                    "help like planting or protection."
                ),
            )
        ),
    ]
    
    
