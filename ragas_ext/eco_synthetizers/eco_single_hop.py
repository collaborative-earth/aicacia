from __future__ import annotations

import logging
import random
import typing as t
from collections import defaultdict
from dataclasses import dataclass

import numpy as np

from ragas.prompt import PydanticPrompt
from ragas.testset.graph import KnowledgeGraph, Node
from ragas.testset.persona import Persona
from ragas.testset.synthesizers.base import BaseScenario,BaseSynthesizer,Scenario,QueryLength,QueryStyle
from ragas.dataset_schema import SingleTurnSample
from .eco_prompts import *

if t.TYPE_CHECKING:
    from langchain_core.callbacks import Callbacks
    
class SingleHopScenario_eco(BaseScenario):
    """
    Scenario for single-hop queries.

    Attributes
    ----------
    term: str
        The theme of the query.
    """

    ecocontext: t.Dict[str, t.List[str]]

    def __repr__(self) -> str:
        return f"SingleHopScenario(\nnodes={len(self.nodes)}\necocontext={self.ecocontext}\npersona={self.persona}\nstyle={self.style}\nlength={self.length})"


class SingleHopScenarioEco(BaseSynthesizer[Scenario]):

    generate_query_reference_prompt: PydanticPrompt = QueryAnswerGenerationPromptEco()

    def prepare_combinations(
        self,
        node: Node,
        ecocontext: t.Dict[str, t.List[str]],
        personas: t.List[Persona],
    ) -> t.List[t.Dict[str, t.Any]]:
        """
        For a node, create all possible combinations of context elements and personas.
        Each context element is sampled individually or can be empty.
        """
        all_samples = []

        # generate all combinations of context terms (one from each category)
        locations = ecocontext.get("locations", [""]) + [""]
        ecosystems = ecocontext.get("ecosystems", [""]) + [""]
        species = ecocontext.get("species", [""])+ [""]
        challenges = ecocontext.get("challenges", [""])+ [""]

        for loc in locations:
            for eco in ecosystems:
                for sp in species:
                    for ch in challenges:
                        for persona_name in personas:
                            all_samples.append(
                                {
                                    "node": node,
                                    "persona": persona_name,
                                    "location": loc,
                                    "ecosystem": eco,
                                    "specie": sp,
                                    "challenge": ch,
                                    "styles": list(QueryStyle),
                                    "lengths": list(QueryLength),
                                }
                            )
        return all_samples

    def sample_combinations(self, data: t.List[t.Dict[str, t.Any]], num_samples: int):
        selected_samples = []

        all_combinations = []
        for entry in data:
            node = entry["node"]
            for style in entry["styles"]:
                for length in entry["lengths"]:
                    all_combinations.append(
                        {
                            "node": node,
                            "persona": entry["persona"],
                            "location": entry["location"],
                            "ecosystem": entry["ecosystem"],
                            "specie": entry["specie"],
                            "challenge": entry["challenge"],
                            "style": style,
                            "length": length,
                        }
                    )

        random.shuffle(all_combinations)
        for sample in all_combinations:
            if len(selected_samples) >= num_samples:
                break
            selected_samples.append(sample)

        return [self.convert_to_scenario(s) for s in selected_samples]

    def convert_to_scenario(self, data: t.Dict[str, t.Any]) -> SingleHopScenario_eco:
        return SingleHopScenario_eco(
            nodes=[data["node"]],
            ecocontext={
                "location": [data.get("location", "")],
                "ecosystem": [data.get("ecosystem", "")],
                "specie": [data.get("specie", "")],
                "challenge": [data.get("challenge", "")],
            },
            persona=data["persona"],
            style=data["style"],
            length=data["length"],
        )
    async def _generate_scenarios(self, n, knowledge_graph, persona_list, callbacks):

        property_name = "ecocontext"
        nodes = []
        nodes = knowledge_graph.nodes
        if len(nodes) == 0:
            return []

        number_of_samples_per_node = max(1, n // len(nodes))

        scenarios = []
        for node in nodes:
            if len(scenarios) >= n:
                break
            ecocontext = node.properties.get(property_name, [""])
            base_scenarios = self.prepare_combinations(
                node,
                ecocontext,
                personas=persona_list,
            )
            scenarios.extend(
                self.sample_combinations(base_scenarios, number_of_samples_per_node)
            )

        return scenarios

    async def _generate_sample(
        self, scenario: Scenario, callbacks: Callbacks
    ) -> SingleTurnSample:
        if not isinstance(scenario, SingleHopScenario_eco):
            raise TypeError("scenario type should be SingleHopScenario with ecocontext")
        reference_context = scenario.nodes[0].properties.get("page_content", "")
        prompt_input = QueryConditionEco(
            persona=scenario.persona,
            ecocontext=scenario.ecocontext,
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
            reference_contexts=[reference_context],
            reference_context_ids = [str(scenario.nodes[0].id)],
            persona_name=scenario.persona.name,
        )