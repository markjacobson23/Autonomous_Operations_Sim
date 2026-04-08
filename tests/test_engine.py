from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation import SimulationEngine, WorldState
import pytest


def build_engine_dependencies() -> tuple[Map, WorldState, Router]:
    graph = Graph()

    node_1 = Node(1, (0.0, 0.0, 0.0))
    node_2 = Node(2, (1.0, 0.0, 0.0))

    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_edge(Edge(1, node_1, node_2, 1.0, 10.0))

    simulation_map = Map(
        graph,
        coord_to_id={
            (0.0, 0.0, 0.0): 1,
            (1.0, 0.0, 0.0): 2,
        },
    )
    world_state = WorldState(graph)
    router = Router()

    return simulation_map, world_state, router


def test_engine_initialization_keeps_runtime_dependencies_and_seed_explicit():
    simulation_map, world_state, router = build_engine_dependencies()

    engine = SimulationEngine(
        simulation_map=simulation_map,
        world_state=world_state,
        router=router,
        seed=123,
    )

    assert engine.map is simulation_map
    assert engine.world_state is world_state
    assert engine.router is router
    assert engine.seed == 123
    assert engine.simulated_time_s == 0.0


def test_engine_run_advances_simulated_time_monotonically():
    simulation_map, world_state, router = build_engine_dependencies()
    engine = SimulationEngine(simulation_map, world_state, router, seed=7)

    assert engine.run(2.5) == 2.5
    assert engine.simulated_time_s == 2.5

    assert engine.run(2.5) == 2.5
    assert engine.run(9.0) == 9.0
    assert engine.simulated_time_s == 9.0


def test_engine_run_rejects_invalid_time_targets():
    simulation_map, world_state, router = build_engine_dependencies()
    engine = SimulationEngine(simulation_map, world_state, router, seed=7)
    engine.run(4.0)

    with pytest.raises(ValueError, match="until_s must be non-negative"):
        engine.run(-1.0)

    with pytest.raises(ValueError, match="until_s must be finite"):
        engine.run(float("inf"))

    with pytest.raises(
        ValueError,
        match="until_s must be greater than or equal to current simulated time",
    ):
        engine.run(3.0)


def test_engine_same_seed_produces_deterministic_setup_random_stream():
    simulation_map_a, world_state_a, router_a = build_engine_dependencies()
    simulation_map_b, world_state_b, router_b = build_engine_dependencies()

    engine_a = SimulationEngine(simulation_map_a, world_state_a, router_a, seed=99)
    engine_b = SimulationEngine(simulation_map_b, world_state_b, router_b, seed=99)
    engine_c = SimulationEngine(simulation_map_b, world_state_b, router_b, seed=100)

    stream_a = [engine_a.rng.random() for _ in range(3)]
    stream_b = [engine_b.rng.random() for _ in range(3)]
    stream_c = [engine_c.rng.random() for _ in range(3)]

    assert stream_a == stream_b
    assert stream_a != stream_c
