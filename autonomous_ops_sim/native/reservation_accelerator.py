from __future__ import annotations

from array import array
import ctypes
from ctypes import POINTER, c_double, c_int, c_int64
from functools import lru_cache
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile


class NativeReservationDepartureAccelerator:
    """Optional shared-library helper for reservation departure scans."""

    def __init__(self, library_path: Path) -> None:
        self._library_path = library_path
        self._library = ctypes.CDLL(str(library_path))
        self._function = self._library.aos_earliest_departure_time
        self._function.argtypes = [
            c_int64,
            c_double,
            c_double,
            c_int,
            c_double,
            c_int64,
            POINTER(c_int64),
            POINTER(c_double),
            POINTER(c_double),
            c_int64,
            POINTER(c_int64),
            POINTER(c_double),
            POINTER(c_double),
            c_int64,
            POINTER(c_int64),
            POINTER(c_double),
            POINTER(c_double),
            c_int64,
            POINTER(c_int64),
            POINTER(c_double),
            POINTER(c_double),
            POINTER(c_double),
        ]
        self._function.restype = c_int

    @property
    def library_path(self) -> Path:
        return self._library_path

    def earliest_departure_time(
        self,
        *,
        vehicle_id: int,
        not_before_s: float,
        travel_time_s: float,
        node_wait_vehicle_ids: array,
        node_wait_starts_s: array,
        node_wait_ends_s: array,
        edge_vehicle_ids: array,
        edge_starts_s: array,
        edge_ends_s: array,
        node_arrival_vehicle_ids: array,
        node_arrival_starts_s: array,
        node_arrival_ends_s: array,
        corridor_vehicle_ids: array,
        corridor_starts_s: array,
        corridor_ends_s: array,
        corridor_travel_time_s: float | None,
    ) -> float:
        """Return the earliest departure time using the native helper."""

        node_wait_ptrs = _buffer_pointers(node_wait_vehicle_ids, node_wait_starts_s, node_wait_ends_s)
        edge_ptrs = _buffer_pointers(edge_vehicle_ids, edge_starts_s, edge_ends_s)
        node_arrival_ptrs = _buffer_pointers(
            node_arrival_vehicle_ids,
            node_arrival_starts_s,
            node_arrival_ends_s,
        )
        corridor_ptrs = _buffer_pointers(
            corridor_vehicle_ids,
            corridor_starts_s,
            corridor_ends_s,
        )
        result_out = c_double()
        status = self._function(
            vehicle_id,
            not_before_s,
            travel_time_s,
            1 if corridor_travel_time_s is not None else 0,
            corridor_travel_time_s or 0.0,
            len(node_wait_vehicle_ids),
            node_wait_ptrs[0],
            node_wait_ptrs[1],
            node_wait_ptrs[2],
            len(edge_vehicle_ids),
            edge_ptrs[0],
            edge_ptrs[1],
            edge_ptrs[2],
            len(node_arrival_vehicle_ids),
            node_arrival_ptrs[0],
            node_arrival_ptrs[1],
            node_arrival_ptrs[2],
            len(corridor_vehicle_ids),
            corridor_ptrs[0],
            corridor_ptrs[1],
            corridor_ptrs[2],
            ctypes.byref(result_out),
        )
        if status != 0:
            raise RuntimeError("native accelerator did not produce a finite departure time")
        return float(result_out.value)


@lru_cache(maxsize=1)
def get_native_reservation_departure_accelerator() -> (
    NativeReservationDepartureAccelerator | None
):
    """Return the shared-library accelerator when the toolchain supports it."""

    source_path = Path(__file__).with_name("reservation_accelerator.c")
    library_path = _native_library_path(source_path)
    if not library_path.exists():
        try:
            _compile_native_library(source_path, library_path)
        except (OSError, subprocess.CalledProcessError):
            return None
    try:
        return NativeReservationDepartureAccelerator(library_path)
    except OSError:
        return None


def _native_library_path(source_path: Path) -> Path:
    digest = hashlib.sha256(source_path.read_bytes()).hexdigest()[:16]
    cache_dir = Path(tempfile.gettempdir()) / "autonomous_ops_sim_native"
    cache_dir.mkdir(parents=True, exist_ok=True)
    extension = ".dylib" if sys.platform == "darwin" else ".so"
    return cache_dir / f"reservation_accelerator_{digest}{extension}"


def _compile_native_library(source_path: Path, library_path: Path) -> None:
    if sys.platform == "darwin":
        command = [
            "cc",
            "-O3",
            "-dynamiclib",
            "-o",
            str(library_path),
            str(source_path),
        ]
    else:
        command = [
            "cc",
            "-O3",
            "-shared",
            "-fPIC",
            "-o",
            str(library_path),
            str(source_path),
        ]
    subprocess.run(command, check=True, capture_output=True, text=True)


def _buffer_pointers(
    vehicle_ids: array,
    starts_s: array,
    ends_s: array,
):
    vehicle_id_buffer = _pointer_from_array(vehicle_ids, c_int64)
    starts_buffer = _pointer_from_array(starts_s, c_double)
    ends_buffer = _pointer_from_array(ends_s, c_double)
    return vehicle_id_buffer, starts_buffer, ends_buffer


def _pointer_from_array(
    values: array,
    c_type: type[c_int64] | type[c_double],
):
    if not values:
        return None
    buffer = (c_type * len(values)).from_buffer(values)
    return ctypes.cast(buffer, POINTER(c_type))
