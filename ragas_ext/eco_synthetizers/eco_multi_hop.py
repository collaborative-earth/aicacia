from __future__ import annotations
# Multihop
from dataclasses import dataclass
import typing as t
from ragas.testset.persona import Persona
from ragas.testset.synthesizers.base import BaseScenario,Scenario,QueryLength,QueryStyle
from ragas.dataset_schema import SingleTurnSample
from ragas.testset.synthesizers.multi_hop.prompts import QueryConditions
from ragas.testset.synthesizers.multi_hop.base import (
    MultiHopQuerySynthesizer,
    MultiHopScenario,
)

if t.TYPE_CHECKING:
    from langchain_core.callbacks import Callbacks
    
@dataclass
class MultiHopQueryEco(MultiHopQuerySynthesizer):

    def prepare_combinations(
        self,
        nodes,
        themes: t.List[str],
        personas: t.List[Persona],
        property_name: str,
        ) -> t.List[t.Dict[str, t.Any]]:
        """
        Prepare base multi-hop combinations using nodes, overlapping themes, and personas.
        Simpler version: does not depend on persona–theme mappings.
        """

        possible_combinations = []
        for theme in themes:
            # Build a combination record
            combo = {
                "combination": theme,
                "nodes": nodes,
                "personas": personas,  # keep all available personas for diversity
                "styles": list(QueryStyle),
                "lengths": list(QueryLength),
            }
            possible_combinations.append(combo)

        return possible_combinations

    async def _generate_scenarios(
        self,
        n: int,
        knowledge_graph,
        persona_list,
        callbacks,
    ) -> t.List[MultiHopScenario]:

        # query and get (node_a, rel, node_b) to create multi-hop queries
        results = knowledge_graph.find_two_nodes_single_rel(
            relationship_condition=lambda rel: (
                True if rel.type == "ecocontext_overlap" else False
            )
        )

        num_sample_per_triplet = max(1, n // len(results))

        scenarios = []
        for triplet in results:
            if len(scenarios) < n:
                node_a, node_b = triplet[0], triplet[-1]
                overlapped_keywords = triplet[1].properties["overlapped_items"]
                if overlapped_keywords:

                    themes = []
                    for key, pairs in overlapped_keywords.items():
                        themes.extend([[x] for x, _ in pairs])

                    if not themes:
                        continue

                    # prepare and sample possible combinations
                    base_scenarios = self.prepare_combinations(
                        [node_a, node_b],
                        themes,
                        personas=persona_list,
                        property_name="ecocontext",
                    )

                    # get number of required samples from this triplet
                    base_scenarios = self.sample_diverse_combinations(
                        base_scenarios, num_sample_per_triplet
                    )

                    scenarios.extend(base_scenarios)

        return scenarios
    
    async def _generate_sample(
        self, scenario: Scenario, callbacks: Callbacks
    ) -> SingleTurnSample:
        if not isinstance(scenario, MultiHopScenario):
            raise TypeError("scenario type should be MultiHopScenario")
        reference_context,node_ids = self.make_contexts(scenario)
        prompt_input = QueryConditions(
            persona=scenario.persona,
            themes=scenario.combinations,
            context=reference_context,
            query_length=scenario.length.value,
            query_style=scenario.style.value,
        )
        response = await self.generate_query_reference_prompt.generate(
            data=prompt_input, llm=self.llm, callbacks=callbacks
        )
        return SingleTurnSample(
            user_input=response.query,
            reference=response.answer,
            reference_contexts=reference_context,
            reference_context_ids = node_ids
        )

    def make_contexts(self, scenario: MultiHopScenario) -> t.List[str]:
        contexts = []
        node_ids = []
        for i, node in enumerate(scenario.nodes):
            context = (
                f"<{i + 1}-hop>" + "\n\n" + node.properties.get("page_content", "")
            )
            node_ids.append(str(node.id))
            contexts.append(context)

        return contexts,node_ids