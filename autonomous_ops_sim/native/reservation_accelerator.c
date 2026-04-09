#include <math.h>
#include <stddef.h>
#include <stdint.h>

static int windows_overlap(double start_a, double end_a, double start_b, double end_b) {
    return start_a < end_b && start_b < end_a;
}

int aos_earliest_departure_time(
    int64_t vehicle_id,
    double not_before_s,
    double travel_time_s,
    int has_corridor,
    double corridor_travel_time_s,
    int64_t node_wait_count,
    const int64_t *node_wait_vehicle_ids,
    const double *node_wait_starts,
    const double *node_wait_ends,
    int64_t edge_count,
    const int64_t *edge_vehicle_ids,
    const double *edge_starts,
    const double *edge_ends,
    int64_t node_arrival_count,
    const int64_t *node_arrival_vehicle_ids,
    const double *node_arrival_starts,
    const double *node_arrival_ends,
    int64_t corridor_count,
    const int64_t *corridor_vehicle_ids,
    const double *corridor_starts,
    const double *corridor_ends,
    double *result_out
) {
    double candidate = not_before_s;

    while (1) {
        double max_blocker = -1.0;

        if (candidate > not_before_s) {
            for (int64_t index = 0; index < node_wait_count; ++index) {
                if (node_wait_vehicle_ids[index] == vehicle_id) {
                    continue;
                }
                if (windows_overlap(
                    not_before_s,
                    candidate,
                    node_wait_starts[index],
                    node_wait_ends[index]
                )) {
                    if (node_wait_ends[index] > max_blocker) {
                        max_blocker = node_wait_ends[index];
                    }
                    break;
                }
            }
        }

        double arrival_time_s = candidate + travel_time_s;
        for (int64_t index = 0; index < edge_count; ++index) {
            if (edge_vehicle_ids[index] == vehicle_id) {
                continue;
            }
            if (windows_overlap(
                candidate,
                arrival_time_s,
                edge_starts[index],
                edge_ends[index]
            )) {
                if (edge_ends[index] > max_blocker) {
                    max_blocker = edge_ends[index];
                }
                break;
            }
        }

        for (int64_t index = 0; index < node_arrival_count; ++index) {
            if (node_arrival_vehicle_ids[index] == vehicle_id) {
                continue;
            }
            if (
                node_arrival_starts[index] <= arrival_time_s &&
                arrival_time_s < node_arrival_ends[index]
            ) {
                if (node_arrival_ends[index] > max_blocker) {
                    max_blocker = node_arrival_ends[index];
                }
                break;
            }
        }

        if (has_corridor) {
            double corridor_end_time_s = candidate + corridor_travel_time_s;
            for (int64_t index = 0; index < corridor_count; ++index) {
                if (corridor_vehicle_ids[index] == vehicle_id) {
                    continue;
                }
                if (windows_overlap(
                    candidate,
                    corridor_end_time_s,
                    corridor_starts[index],
                    corridor_ends[index]
                )) {
                    if (corridor_ends[index] > max_blocker) {
                        max_blocker = corridor_ends[index];
                    }
                    break;
                }
            }
        }

        if (max_blocker < 0.0) {
            *result_out = candidate;
            return 0;
        }

        candidate = max_blocker;
        if (!isfinite(candidate)) {
            return 1;
        }
    }
}
