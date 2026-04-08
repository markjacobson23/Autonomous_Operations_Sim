import json

import pytest

from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.simulation.scenario import Scenario
from autonomous_ops_sim.vehicles.vehicle import VehicleType


def write_scenario(tmp_path, data):
    scenario_path = tmp_path / "scenario.json"
    scenario_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return scenario_path

def make_valid_scenario_data():
    return {
        "name": "basic_grid_demo",
        "seed": 123,
        "duration_s": 1000.0,
        "map": {
            "kind": "grid",
            "params": {
                "grid_size": 5,
            },
        },
        "vehicles": [
            {
                "id": 1,
                "position": [0, 0, 0],
                "velocity": 0.0,
                "payload": 0.0,
                "max_payload": 100.0,
                "max_speed": 25.0,
                "vehicle_type": "GENERIC",
            }
        ],
        "execution": {
            "kind": "single_vehicle_job",
            "vehicle_id": 1,
            "job": {
                "id": "demo-job",
                "tasks": [
                    {
                        "kind": "move",
                        "destination": [1, 0, 0],
                    }
                ],
            },
        },
    }

@pytest.fixture
def valid_scenario_data():
    return make_valid_scenario_data()

def test_load_scenario_parses_valid_grid_scenario(tmp_path, valid_scenario_data):
    data = valid_scenario_data

    scenario_path = write_scenario(tmp_path, data)
    scenario = load_scenario(scenario_path)

    assert isinstance(scenario, Scenario)
    assert scenario.name == "basic_grid_demo"
    assert scenario.seed == 123
    assert scenario.duration_s == 1000.0

    assert scenario.map_spec.kind == "grid"
    assert scenario.map_spec.params["grid_size"] == 5

    assert len(scenario.vehicles) == 1

    vehicle = scenario.vehicles[0]
    assert vehicle.id == 1
    assert vehicle.position == (0.0, 0.0, 0.0)
    assert vehicle.velocity == 0.0
    assert vehicle.payload == 0.0
    assert vehicle.max_payload == 100.0
    assert vehicle.max_speed == 25.0
    assert vehicle.vehicle_type == VehicleType.GENERIC
    assert scenario.execution is not None
    assert scenario.execution.kind == "single_vehicle_job"
    assert scenario.execution.vehicle_id == 1
    assert scenario.execution.job.id == "demo-job"
    assert len(scenario.execution.job.tasks) == 1


def test_load_scenario_raises_for_missing_name(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    del data["name"]
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_raises_for_missing_seed(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    del data["seed"]
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_raises_for_invalid_duration_type(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    data["duration_s"] = "invalid"
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_raises_for_nonpositive_duration(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    data["duration_s"] = 0.0
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)


def test_load_scenario_raises_for_nonobject_top_level_json(tmp_path, valid_scenario_data):
    scenario_path = write_scenario(tmp_path, [1,2,3])
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_raises_for_missing_map_kind(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    del data["map"]["kind"]
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_raises_for_missing_map_params(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    del data["map"]["params"]
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_raises_for_unsupported_map_kind(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    data["map"]["kind"] = "unsupported"
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_raises_for_missing_grid_size(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    del data["map"]["params"]["grid_size"]
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_raises_for_invalid_grid_size_type(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    data["map"]["params"]["grid_size"] = "invalid"
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_raises_for_nonpositive_grid_size(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    data["map"]["params"]["grid_size"] = -4
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_raises_for_vehicle_entry_that_is_not_an_object(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    data["vehicles"] = [1, 2, 3]
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_raises_for_missing_vehicle_id(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    del data["vehicles"][0]["id"]
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_raises_for_invalid_vehicle_id_type(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    data["vehicles"][0]["id"] = "invalid"
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_raises_for_missing_vehicle_position(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    del data["vehicles"][0]["position"]
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_raises_for_vehicle_position_not_a_list(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    data["vehicles"][0]["position"] = "invalid"
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_raises_for_vehicle_position_with_wrong_length(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    data["vehicles"][0]["position"] = [1,2,3,4]
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_raises_for_vehicle_position_with_nonnumeric_coordinate(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    data["vehicles"][0]["position"] = [1, 2, "a"]
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_raises_for_nonnumeric_velocity(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    data["vehicles"][0]["velocity"] = "invalid"
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_raises_for_negative_payload(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    data["vehicles"][0]["payload"] = -1.0
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_raises_for_negative_max_payload(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    data["vehicles"][0]["max_payload"] = -1.0
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_raises_for_nonpositive_max_speed(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    data["vehicles"][0]["max_speed"] = -1.0
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_parses_valid_vehicle_type(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    scenario_path = write_scenario(tmp_path, data)
    scenario = load_scenario(scenario_path)
    assert scenario.vehicles[0].vehicle_type == VehicleType.GENERIC

def test_load_scenario_accepts_missing_vehicle_type(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    del data["vehicles"][0]["vehicle_type"]
    scenario_path = write_scenario(tmp_path, data)
    scenario = load_scenario(scenario_path)
    assert scenario.vehicles[0].vehicle_type is None


def test_load_scenario_accepts_missing_execution_section(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    del data["execution"]
    scenario_path = write_scenario(tmp_path, data)

    scenario = load_scenario(scenario_path)

    assert scenario.execution is None

def test_load_scenario_raises_for_invalid_vehicle_type(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    data["vehicles"][0]["vehicle_type"] = "INVALID"
    scenario_path = write_scenario(tmp_path, data)
    with pytest.raises(ValueError):
        load_scenario(scenario_path)

def test_load_scenario_converts_vehicle_position_to_tuple_of_floats(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    scenario_path = write_scenario(tmp_path, data)
    scenario = load_scenario(scenario_path)
    pos = scenario.vehicles[0].position
    assert isinstance(pos, tuple) and len(pos) == 3 and all(isinstance(x, float) for x in pos)

def test_load_scenario_converts_numeric_vehicle_fields_to_float(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    data["vehicles"][0]["velocity"] = 1
    data["vehicles"][0]["payload"] = 1
    data["vehicles"][0]["max_payload"] = 1
    data["vehicles"][0]["max_speed"] = 1
    scenario_path = write_scenario(tmp_path, data)
    scenario = load_scenario(scenario_path)
    assert isinstance(scenario.vehicles[0].velocity, float)
    assert isinstance(scenario.vehicles[0].payload, float)
    assert isinstance(scenario.vehicles[0].max_payload, float)
    assert isinstance(scenario.vehicles[0].max_speed, float)


def test_load_scenario_raises_for_unknown_execution_vehicle_id(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    data["execution"]["vehicle_id"] = 99
    scenario_path = write_scenario(tmp_path, data)

    with pytest.raises(ValueError, match="vehicle_id"):
        load_scenario(scenario_path)

def test_load_scenario_preserves_seed_value(tmp_path, valid_scenario_data):
    data = valid_scenario_data
    scenario_path = write_scenario(tmp_path, data)
    scenario = load_scenario(scenario_path)
    assert scenario.seed == data["seed"]
