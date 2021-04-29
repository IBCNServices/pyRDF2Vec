from typing import Dict

import attr
import networkx as nx

from pyrdf2vec.graphs import KG
from pyrdf2vec.samplers import Sampler
from pyrdf2vec.typings import Hop


@attr.s
class PageRankSampler(Sampler):
    """Sampler that assigns a weight to each edge in a Knowledge Graph
    according to the ranking of vertices. This ranking is done by giving
    higher weights to the object vertices being more frequent. From then on,
    this node-centric approach sampling strategy prioritizes walks where
    object vertices are more frequent than others.

    Attributes:
        _is_support_remote: True if the sampling strategy can be used with a
            remote Knowledge Graph, False Otherwise
            Defaults to False.
        _pageranks: The PageRank dictionary.
            Defaults to {}.
        _random_state: The random state to use to keep random determinism with
            the sampling strategy.
            Defaults to None.
        _vertices_deg: The degree of the vertices.
            Defaults to {}.
        _visited: Tags vertices that appear at the max depth or of which all
            their children are tagged.
            Defaults to set.
        alpha: The damping for PageRank.
            Defaults to 0.85.
        inverse: True if the inverse algorithm must be used, False otherwise.
            Defaults to False.
        split: True if the split algorithm must be used, False otherwise.
            Defaults to False.

    """

    alpha = attr.ib(
        kw_only=True,
        default=0.85,
        type=float,
        validator=attr.validators.instance_of(float),
    )

    _pageranks = attr.ib(
        init=False, type=Dict[str, float], repr=False, factory=dict
    )

    def fit(self, kg: KG) -> None:
        """Fits the sampling strategy by running PageRank on a provided KG
        according to the specified damping.

        Args:
            kg: The Knowledge Graph.

        """
        super().fit(kg)
        nx_graph = nx.DiGraph()

        for vertex in kg._vertices:
            if not vertex.predicate:
                nx_graph.add_node(vertex.name, vertex=vertex)
                for predicate in kg.get_neighbors(vertex):
                    for obj in kg.get_neighbors(predicate):
                        nx_graph.add_edge(
                            vertex.name, obj.name, name=predicate.name
                        )
        self._pageranks = nx.pagerank(nx_graph, alpha=self.alpha)

    def get_weight(self, hop: Hop) -> float:
        """Gets the weight of a hop in the Knowledge Graph.

        Args:
            hop: The hop of a vertex in a (predicate, object) form to get the
                weight.

        Returns:
            The weight of a given hop.

        Raises:
            ValueError: If there is an attempt to access the weight of a hop
                without the sampling strategy having been trained.

        """
        if not self._pageranks:
            raise ValueError(
                "You must call the `fit(kg)` method before get the weight of"
                + " a hop."
            )
        return self._pageranks[hop[1].name]
