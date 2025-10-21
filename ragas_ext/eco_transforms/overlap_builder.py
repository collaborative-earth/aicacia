import numpy as np
import typing as t
from dataclasses import dataclass
from ragas.metrics._string import DistanceMeasure
from ragas.testset.graph import KnowledgeGraph, Relationship
from ragas.testset.transforms.base import RelationshipBuilder

@dataclass
class EcoContextOverlapBuilder(RelationshipBuilder):
    """
    Compute overlap-based relationships between nodes in a knowledge graph
    based on their ecological context (ecocontext).

    Each node's ecocontext is a dictionary of lists (locations, ecosystems,
    species, challenges). Overlaps are computed per key using a string
    distance metric, and a combined similarity score is calculated.

    Parameters
    ----------
    kg : KnowledgeGraph
        The knowledge graph containing nodes with 'ecocontext' property.

    Returns
    -------
    List[Relationship]
        A list of Relationship objects where similarity between nodes exceeds
        the threshold.
    """
    property_name: str = "ecocontext"
    new_property_name: str = "overlap_score"
    distance_measure: DistanceMeasure = DistanceMeasure.JARO_WINKLER
    distance_threshold: float = 0.9
    threshold: float = 0.01

    def __post_init__(self):
        from rapidfuzz import distance

        self.distance_measure_map = {
            DistanceMeasure.LEVENSHTEIN: distance.Levenshtein,
            DistanceMeasure.HAMMING: distance.Hamming,
            DistanceMeasure.JARO: distance.Jaro,
            DistanceMeasure.JARO_WINKLER: distance.JaroWinkler,
        }

    def _overlap_score(self, overlaps: t.List[bool]) -> float:
        return sum(overlaps) / len(overlaps) if overlaps else 0.0

    async def transform(self, kg: KnowledgeGraph) -> t.List[Relationship]:
        distance_measure = self.distance_measure_map[self.distance_measure]
        relationships = []

        for i, node_x in enumerate(kg.nodes):
            for j, node_y in enumerate(kg.nodes):
                if i >= j:
                    continue

                x_ctx = node_x.get_property(self.property_name) or {}
                y_ctx = node_y.get_property(self.property_name) or {}
                total_overlaps = []
                overlapped_items_per_key = {}
                distance_measure = self.distance_measure_map[self.distance_measure]
                for key in x_ctx.keys():
                    
                    x_items = x_ctx.get(key, [])
                    y_items = y_ctx.get(key, [])
                    overlapped_items = []
                    
                    if not x_items and not y_items:
                        per_key_overlap = 0.0
                    else:
                      
                        x_matches = sum(
                            any(1 - distance_measure.distance(xi.lower(), yi.lower()) >= self.distance_threshold
                                for yi in y_items)
                            for xi in x_items
                        )
                        y_matches = sum(
                            any(1 - distance_measure.distance(yi.lower(), xi.lower()) >= self.distance_threshold
                                for xi in x_items)
                            for yi in y_items
                        )

                        for xi in x_items:
                            for yi in y_items:
                                sim = 1 - distance_measure.distance(xi.lower(), yi.lower())
                                if sim >= self.distance_threshold:
                                    overlapped_items.append((xi, yi))

                        prop_x = float(x_matches) / float(len(x_items)) if x_items else 0.0
                        prop_y = float(y_matches) / float(len(y_items)) if y_items else 0.0
                        per_key_overlap = (prop_x + prop_y) / 2.0

                    total_overlaps.append(per_key_overlap)
                    overlapped_items_per_key[key] = overlapped_items

                similarity = self._overlap_score(total_overlaps)
                if similarity >= self.threshold:
                    relationships.append(
                        Relationship(
                            source=node_x,
                            target=node_y,
                            type=f"{self.property_name}_overlap",
                            properties={
                                f"{self.property_name}_{self.new_property_name}": similarity,
                                "overlapped_items": overlapped_items_per_key,
                            },
                        )
                    )

        return relationships