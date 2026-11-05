"""Reusable constraint validation engine for optimization problems."""

import math
from typing import Dict, Any, List, Optional, Tuple, Union
from pydantic import BaseModel, Field


class ConstraintViolation(BaseModel):
    """Structured constraint violation detail."""
    constraint_id: str = Field(..., description="Machine-readable constraint identifier")
    constraint_name: str = Field(..., description="Human-readable constraint name")
    message: str = Field(..., description="Explanation of why the constraint failed")
    expected: Optional[Any] = Field(default=None, description="Expected value or boundary")
    actual: Optional[Any] = Field(default=None, description="Actual invalid value received")
    severity: str = Field(default="error", description="Severity level: error or warning")


class ConstraintValidator:
    """Core constraint validation engine."""

    @staticmethod
    def validate_binary_variables(
        variable_values: Dict[str, Any],
        expected_variables: Optional[List[str]] = None,
    ) -> List[ConstraintViolation]:
        """Verify that all variable assignments strictly belong to {0, 1}."""
        violations: List[ConstraintViolation] = []

        if expected_variables is not None:
            expected_set = set(expected_variables)
            provided_set = set(variable_values.keys())
            missing = expected_set - provided_set
            for var in sorted(missing):
                violations.append(
                    ConstraintViolation(
                        constraint_id="MISSING_VARIABLE",
                        constraint_name="Variable Completeness Constraint",
                        message=f"Required variable '{var}' was not provided in the candidate solution.",
                        expected=f"Binary assignment for {var}",
                        actual=None,
                        severity="error",
                    )
                )

            unexpected = provided_set - expected_set
            for var in sorted(unexpected):
                violations.append(
                    ConstraintViolation(
                        constraint_id="UNKNOWN_VARIABLE",
                        constraint_name="Variable Scope Constraint",
                        message=f"Variable '{var}' is not defined in the problem specification.",
                        expected="Only variables defined in problem instance",
                        actual=var,
                        severity="error",
                    )
                )

        for var, val in variable_values.items():
            # Boolean True/False or int 0/1 or float 0.0/1.0
            if isinstance(val, bool):
                int_val = 1 if val else 0
            elif isinstance(val, (int, float)):
                if val == 0 or val == 0.0:
                    int_val = 0
                elif val == 1 or val == 1.0:
                    int_val = 1
                else:
                    violations.append(
                        ConstraintViolation(
                            constraint_id="BINARY_DOMAIN_VIOLATION",
                            constraint_name="Binary Variable Domain Constraint",
                            message=f"Variable '{var}' has value {val}; binary variables must be in {{0, 1}}.",
                            expected="0 or 1",
                            actual=val,
                            severity="error",
                        )
                    )
                    continue
            else:
                violations.append(
                    ConstraintViolation(
                        constraint_id="BINARY_TYPE_VIOLATION",
                        constraint_name="Binary Variable Type Constraint",
                        message=f"Variable '{var}' has non-numeric type {type(val).__name__} with value '{val}'.",
                        expected="0 or 1",
                        actual=str(val),
                        severity="error",
                    )
                )

        return violations

    @staticmethod
    def validate_graph_partition(
        nodes: List[str],
        partition: Union[Dict[str, Any], List[Any]],
    ) -> Tuple[List[ConstraintViolation], Dict[str, int]]:
        """
        Verify that candidate solution assigns every vertex to exactly one partition (0 or 1).
        Supports either a node->partition dict or an ordered binary list.
        """
        violations: List[ConstraintViolation] = []
        node_set = set(nodes)
        normalized_assignment: Dict[str, int] = {}

        if isinstance(partition, list):
            if len(partition) != len(nodes):
                violations.append(
                    ConstraintViolation(
                        constraint_id="PARTITION_LENGTH_MISMATCH",
                        constraint_name="Partition Length Constraint",
                        message=f"Solution vector length ({len(partition)}) does not match node count ({len(nodes)}).",
                        expected=len(nodes),
                        actual=len(partition),
                        severity="error",
                    )
                )
                return violations, {}
            # Map aligned to nodes
            candidate_dict = {nodes[i]: partition[i] for i in range(len(nodes))}
        elif isinstance(partition, dict):
            candidate_dict = partition
        else:
            violations.append(
                ConstraintViolation(
                    constraint_id="INVALID_PARTITION_FORMAT",
                    constraint_name="Partition Structure Constraint",
                    message=f"Partition must be a dict mapping node -> {{0, 1}} or a list of length {len(nodes)}. Received: {type(partition).__name__}",
                    expected="dict[str, int] or list[int]",
                    actual=type(partition).__name__,
                    severity="error",
                )
            )
            return violations, {}

        # Validate binary values and coverage
        bin_violations = ConstraintValidator.validate_binary_variables(
            candidate_dict, expected_variables=nodes
        )
        violations.extend(bin_violations)

        for n in nodes:
            if n in candidate_dict:
                v = candidate_dict[n]
                if v in (0, 1, 0.0, 1.0, True, False):
                    normalized_assignment[n] = 1 if (v == 1 or v is True) else 0

        return violations, normalized_assignment

    @staticmethod
    def validate_assignment_constraints(
        agents: List[str],
        tasks: List[str],
        assignment: Union[Dict[str, str], List[Tuple[str, str]], List[List[int]]],
        is_square: bool = True,
    ) -> Tuple[List[ConstraintViolation], List[Tuple[str, str]]]:
        """
        Verify assignment problem constraints:
        - Each agent assigned to at most one task.
        - Each task assigned to at most one agent.
        - In square assignment (len(agents) == len(tasks)), exactly 1-to-1 bijection (all assigned).
        """
        violations: List[ConstraintViolation] = []
        pairs: List[Tuple[str, str]] = []
        agent_set = set(agents)
        task_set = set(tasks)

        if isinstance(assignment, dict):
            for a, t in assignment.items():
                pairs.append((str(a), str(t)))
        elif isinstance(assignment, list):
            if assignment and isinstance(assignment[0], list):
                # Binary matrix representation len(agents) x len(tasks)
                matrix = assignment
                if len(matrix) != len(agents):
                    violations.append(
                        ConstraintViolation(
                            constraint_id="ASSIGNMENT_MATRIX_ROW_MISMATCH",
                            constraint_name="Assignment Matrix Dimension Constraint",
                            message=f"Matrix rows ({len(matrix)}) must match agent count ({len(agents)}).",
                            expected=len(agents),
                            actual=len(matrix),
                            severity="error",
                        )
                    )
                    return violations, []
                for i, row in enumerate(matrix):
                    if len(row) != len(tasks):
                        violations.append(
                            ConstraintViolation(
                                constraint_id="ASSIGNMENT_MATRIX_COL_MISMATCH",
                                constraint_name="Assignment Matrix Dimension Constraint",
                                message=f"Row {i} length ({len(row)}) must match task count ({len(tasks)}).",
                                expected=len(tasks),
                                actual=len(row),
                                severity="error",
                            )
                        )
                        return violations, []
                    for j, val in enumerate(row):
                        if val == 1:
                            pairs.append((agents[i], tasks[j]))
            else:
                for item in assignment:
                    if isinstance(item, (tuple, list)) and len(item) == 2:
                        pairs.append((str(item[0]), str(item[1])))
                    else:
                        violations.append(
                            ConstraintViolation(
                                constraint_id="INVALID_PAIR_FORMAT",
                                constraint_name="Assignment Pair Format Constraint",
                                message=f"Expected (agent, task) pair, received: {item}",
                                expected="(agent, task)",
                                actual=str(item),
                                severity="error",
                            )
                        )
                        return violations, []
        else:
            violations.append(
                ConstraintViolation(
                    constraint_id="INVALID_ASSIGNMENT_FORMAT",
                    constraint_name="Assignment Structure Constraint",
                    message=f"Assignment must be a dict (agent->task), list of pairs, or binary matrix. Received: {type(assignment).__name__}",
                    expected="dict or list",
                    actual=type(assignment).__name__,
                    severity="error",
                )
            )
            return violations, []

        # Track usage
        assigned_agents: Dict[str, List[str]] = {}
        assigned_tasks: Dict[str, List[str]] = {}

        for a, t in pairs:
            # Validate agent identifier
            if a not in agent_set:
                violations.append(
                    ConstraintViolation(
                        constraint_id="UNKNOWN_AGENT",
                        constraint_name="Agent Identifier Validity Constraint",
                        message=f"Assignment references unknown agent '{a}'. Available agents: {agents}",
                        expected="Agent in problem definition",
                        actual=a,
                        severity="error",
                    )
                )
            # Validate task identifier
            if t not in task_set:
                violations.append(
                    ConstraintViolation(
                        constraint_id="UNKNOWN_TASK",
                        constraint_name="Task Identifier Validity Constraint",
                        message=f"Assignment references unknown task '{t}'. Available tasks: {tasks}",
                        expected="Task in problem definition",
                        actual=t,
                        severity="error",
                    )
                )

            assigned_agents.setdefault(a, []).append(t)
            assigned_tasks.setdefault(t, []).append(a)

        # Constraint: each agent assigned to at most 1 task
        for a, t_list in assigned_agents.items():
            if len(t_list) > 1:
                violations.append(
                    ConstraintViolation(
                        constraint_id="AGENT_DUPLICATE_ASSIGNMENT",
                        constraint_name="Agent Single Task Constraint",
                        message=f"Agent '{a}' is assigned to multiple tasks: {t_list}. An agent can receive at most one task.",
                        expected=1,
                        actual=len(t_list),
                        severity="error",
                    )
                )

        # Constraint: each task assigned to at most 1 agent
        for t, a_list in assigned_tasks.items():
            if len(a_list) > 1:
                violations.append(
                    ConstraintViolation(
                        constraint_id="TASK_DUPLICATE_ASSIGNMENT",
                        constraint_name="Task Single Agent Constraint",
                        message=f"Task '{t}' is assigned to multiple agents: {a_list}. A task can be assigned at most once.",
                        expected=1,
                        actual=len(a_list),
                        severity="error",
                    )
                )

        # For square instances, every agent must receive a task and all tasks must be assigned
        if is_square and len(agents) == len(tasks):
            unassigned_agents = agent_set - set(assigned_agents.keys())
            for ua in sorted(unassigned_agents):
                violations.append(
                    ConstraintViolation(
                        constraint_id="UNASSIGNED_AGENT",
                        constraint_name="Complete Matching Constraint",
                        message=f"Agent '{ua}' has no assigned task in square assignment problem.",
                        expected="1 task",
                        actual="unassigned",
                        severity="error",
                    )
                )

            unassigned_tasks = task_set - set(assigned_tasks.keys())
            for ut in sorted(unassigned_tasks):
                violations.append(
                    ConstraintViolation(
                        constraint_id="UNASSIGNED_TASK",
                        constraint_name="Complete Matching Constraint",
                        message=f"Task '{ut}' is not assigned to any agent in square assignment problem.",
                        expected="1 agent",
                        actual="unassigned",
                        severity="error",
                    )
                )

        return violations, pairs

    @staticmethod
    def validate_tsp_tour(
        cities: List[str],
        tour: Union[List[str], List[int]],
        start_city: Optional[str] = None,
    ) -> Tuple[List[ConstraintViolation], List[str]]:
        """
        Verify TSP tour constraints:
        - Must visit every city in the problem definition.
        - Must visit every city exactly once before returning to the start.
        - Must return to starting city to form a closed Hamiltonian cycle.
        - Must not contain unknown cities or sub-tours.
        - If start_city is configured, tour must begin with that city.
        """
        violations: List[ConstraintViolation] = []
        n = len(cities)
        city_set = set(cities)

        if not isinstance(tour, list) or len(tour) == 0:
            violations.append(
                ConstraintViolation(
                    constraint_id="EMPTY_OR_INVALID_TOUR",
                    constraint_name="Tour Structure Constraint",
                    message="Tour must be a non-empty list of cities.",
                    expected=f"List of {n} cities",
                    actual=str(tour),
                    severity="error",
                )
            )
            return violations, []

        # Convert index list to city names if needed
        normalized_tour: List[str] = []
        if isinstance(tour[0], int):
            for idx in tour:
                if 0 <= idx < n:
                    normalized_tour.append(cities[idx])
                else:
                    violations.append(
                        ConstraintViolation(
                            constraint_id="INVALID_CITY_INDEX",
                            constraint_name="City Index Bounds Constraint",
                            message=f"City index {idx} is out of bounds for {n} cities.",
                            expected=f"Index between 0 and {n - 1}",
                            actual=idx,
                            severity="error",
                        )
                    )
                    return violations, []
        else:
            normalized_tour = [str(c).strip() for c in tour]

        # Check if tour is explicitly closed with return to start
        # e.g. [A, B, C, A] vs [A, B, C]
        explicitly_closed = (
            len(normalized_tour) == n + 1 and normalized_tour[0] == normalized_tour[-1]
        )

        intermediate_cities: List[str]
        if explicitly_closed:
            intermediate_cities = normalized_tour[:-1]
        elif len(normalized_tour) == n:
            intermediate_cities = normalized_tour
        else:
            # Length mismatch
            violations.append(
                ConstraintViolation(
                    constraint_id="TOUR_LENGTH_MISMATCH",
                    constraint_name="Hamiltonian Cycle Length Constraint",
                    message=f"Tour contains {len(normalized_tour)} entries; expected {n} cities (or {n+1} with return to start).",
                    expected=n,
                    actual=len(normalized_tour),
                    severity="error",
                )
            )
            return violations, []

        # Validate all cities are recognized
        for c in intermediate_cities:
            if c not in city_set:
                violations.append(
                    ConstraintViolation(
                        constraint_id="UNKNOWN_CITY",
                        constraint_name="City Identifier Validity Constraint",
                        message=f"Tour references unknown city '{c}'. Defined cities: {cities}",
                        expected="City in problem definition",
                        actual=c,
                        severity="error",
                    )
                )

        # Check for duplicate visits
        seen_cities = set()
        duplicates = []
        for c in intermediate_cities:
            if c in seen_cities:
                duplicates.append(c)
            seen_cities.add(c)

        if duplicates:
            violations.append(
                ConstraintViolation(
                    constraint_id="DUPLICATE_CITY_VISIT",
                    constraint_name="Single Visit Constraint",
                    message=f"Cities visited more than once in tour cycle: {list(set(duplicates))}. Every city must be visited exactly once.",
                    expected="1 visit per city",
                    actual=f"Duplicates: {duplicates}",
                    severity="error",
                )
            )

        # Check for missing cities
        missing_cities = city_set - seen_cities
        if missing_cities:
            violations.append(
                ConstraintViolation(
                    constraint_id="OMITTED_CITIES",
                    constraint_name="Complete Tour Coverage Constraint",
                    message=f"Tour omits cities: {sorted(list(missing_cities))}. All {n} cities must be visited.",
                    expected=f"All {n} cities",
                    actual=f"Missing: {sorted(list(missing_cities))}",
                    severity="error",
                )
            )

        # Check start city if specified
        if start_city is not None:
            if intermediate_cities and intermediate_cities[0] != start_city:
                violations.append(
                    ConstraintViolation(
                        constraint_id="START_CITY_MISMATCH",
                        constraint_name="Designated Starting City Constraint",
                        message=f"Tour starts at '{intermediate_cities[0]}', expected designated starting city '{start_city}'.",
                        expected=start_city,
                        actual=intermediate_cities[0],
                        severity="error",
                    )
                )

        # Return the closed tour cycle [c0, c1, ..., cn-1, c0]
        closed_tour = intermediate_cities + [intermediate_cities[0]] if intermediate_cities else []
        return violations, closed_tour
