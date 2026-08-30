from shapely.geometry import Polygon
from shapely.strtree import STRtree

def finding(rule, severity, message, subjects=None, metric=None, unit=None):
    return {
        "rule": rule,
        "severity": severity,
        "message": message,
        "subjects": subjects or [],
        "metric": metric,
        "unit": unit
    }


# =========================================================
# 1. UNIQUE ULPIN
# =========================================================

def check_unique_ulpins(parcels):

    findings = []
    seen = {}

    for parcel in parcels:

        ulpin = parcel.get("ulpin_3d")

        if not ulpin:
            findings.append(
                finding(
                    "UNIQUE_ULPIN",
                    "error",
                    "Parcel does not contain a ULPIN.",
                    []
                )
            )
            continue

        if ulpin in seen:

            findings.append(
                finding(
                    "UNIQUE_ULPIN",
                    "error",
                    f"Duplicate ULPIN detected: {ulpin}",
                    [seen[ulpin], ulpin]
                )
            )

        else:
            seen[ulpin] = ulpin

    return findings


# =========================================================
# 2. GEOMETRY VALIDATION
# =========================================================

def check_geometry(parcels):

    findings = []

    for parcel in parcels:

        ulpin = parcel.get("ulpin_3d")
        ring = parcel.get("footprint")

        if not ring:
            findings.append(
                finding(
                    "VALID_GEOMETRY",
                    "error",
                    "Parcel has no footprint.",
                    [ulpin]
                )
            )
            continue

        try:
            polygon = Polygon(ring)

            if polygon.is_empty:
                findings.append(
                    finding(
                        "VALID_GEOMETRY",
                        "error",
                        "Footprint is empty.",
                        [ulpin]
                    )
                )

            elif not polygon.is_valid:

                findings.append(
                    finding(
                        "VALID_GEOMETRY",
                        "error",
                        f"Invalid polygon geometry: {polygon.is_valid}",
                        [ulpin]
                    )
                )

            elif polygon.area <= 0:

                findings.append(
                    finding(
                        "VALID_GEOMETRY",
                        "error",
                        "Footprint has zero or negative area.",
                        [ulpin]
                    )
                )

        except Exception as e:

            findings.append(
                finding(
                    "VALID_GEOMETRY",
                    "error",
                    f"Could not construct polygon: {str(e)}",
                    [ulpin]
                )
            )

    return findings


# =========================================================
# 3. ELEVATION VALIDATION
# =========================================================

def check_elevation(parcels, tolerance=0.10):

    findings = []

    for parcel in parcels:

        ulpin = parcel.get("ulpin_3d")

        bottom = parcel.get("bottom_z")
        top = parcel.get("top_z")
        height = parcel.get("height_m")

        if bottom is None or top is None:

            findings.append(
                finding(
                    "ELEVATION_VALIDATION",
                    "error",
                    "Missing bottom_z or top_z.",
                    [ulpin]
                )
            )
            continue

        if top <= bottom:

            findings.append(
                finding(
                    "ELEVATION_VALIDATION",
                    "error",
                    "top_z must be greater than bottom_z.",
                    [ulpin]
                )
            )
            continue

        calculated_height = top - bottom

        if height is not None:

            difference = abs(calculated_height - height)

            if difference > tolerance:

                findings.append(
                    finding(
                        "ELEVATION_VALIDATION",
                        "error",
                        (
                            f"height_m={height} does not match "
                            f"top_z-bottom_z={calculated_height:.3f}"
                        ),
                        [ulpin],
                        difference,
                        "m"
                    )
                )

    return findings


# =========================================================
# 4. AREA VALIDATION
# =========================================================

def check_area(parcels, tolerance=0.05):

    findings = []

    for parcel in parcels:

        ulpin = parcel.get("ulpin_3d")
        ring = parcel.get("footprint")
        declared_area = parcel.get("area_m2")

        if not ring or declared_area is None:
            continue

        try:
            polygon = Polygon(ring)
            calculated_area = polygon.area

            difference_ratio = abs(
                calculated_area - declared_area
            ) / max(declared_area, 0.000001)

            if difference_ratio > tolerance:

                findings.append(
                    finding(
                        "AREA_VALIDATION",
                        "warning",
                        (
                            f"Declared area={declared_area:.2f} m², "
                            f"calculated area={calculated_area:.2f} m²"
                        ),
                        [ulpin],
                        difference_ratio * 100,
                        "%"
                    )
                )

        except Exception:
            pass

    return findings


# =========================================================
# 5. DIMENSION / VOLUME VALIDATION
# =========================================================

def check_volume(parcels, tolerance=0.05):

    findings = []

    for parcel in parcels:

        ulpin = parcel.get("ulpin_3d")

        area = parcel.get("area_m2")
        bottom = parcel.get("bottom_z")
        top = parcel.get("top_z")
        volume = parcel.get("volume_m3")

        if (
            area is None
            or bottom is None
            or top is None
            or volume is None
        ):
            continue

        calculated_volume = area * (top - bottom)

        difference_ratio = abs(
            calculated_volume - volume
        ) / max(abs(volume), 0.000001)

        if difference_ratio > tolerance:

            findings.append(
                finding(
                    "VOLUME_VALIDATION",
                    "warning",
                    (
                        f"Declared volume={volume:.2f} m³, "
                        f"calculated volume={calculated_volume:.2f} m³"
                    ),
                    [ulpin],
                    difference_ratio * 100,
                    "%"
                )
            )

    return findings    


# =========================================================
# 6. PARENT VALIDATION
# =========================================================

def check_parent_exists(parcels):

    findings = []

    ulpins = {
        p.get("ulpin_3d")
        for p in parcels
    }

    for parcel in parcels:

        ulpin = parcel.get("ulpin_3d")
        parent = parcel.get("parent")

        if parent is None:
            continue

        if parent not in ulpins:

            findings.append(
                finding(
                    "PARENT_EXISTS",
                    "error",
                    f"Parent parcel does not exist: {parent}",
                    [ulpin, parent]
                )
            )

    return findings


# =========================================================
# 7. 3D VOLUME OVERLAP VALIDATION
# =========================================================

def _is_ancestor(a_id, b_id, parcel_map):
    """
    Returns True if a_id is an ancestor of b_id,
    or b_id is an ancestor of a_id.
    """

    def is_ancestor(ancestor_id, child_id):
        current = parcel_map.get(child_id)

        visited = set()

        while current:
            current_id = current.get("ulpin_3d")

            if current_id in visited:
                break

            visited.add(current_id)

            parent_id = current.get("parent")

            if not parent_id:
                return False

            if parent_id == ancestor_id:
                return True

            current = parcel_map.get(parent_id)

        return False

    return (
        is_ancestor(a_id, b_id)
        or is_ancestor(b_id, a_id)
    )

def check_no_volume_overlap(parcels):

    findings = []

    parcel_map = {
        parcel.get("ulpin_3d"): parcel
        for parcel in parcels
        if parcel.get("ulpin_3d")
    }

    # ---------------------------------------------------------
    # Build polygon list while preserving duplicate ULPINs
    # ---------------------------------------------------------

    valid_parcels = []
    polygon_list = []

    for parcel in parcels:

        ulpin = parcel.get("ulpin_3d")
        ring = parcel.get("footprint")

        if not ulpin or not ring:
            continue

        try:
            polygon = Polygon(ring)
        except Exception:
            continue

        valid_parcels.append(parcel)
        polygon_list.append(polygon)

    if not polygon_list:
        return findings

    # ---------------------------------------------------------
    # Build spatial index
    # ---------------------------------------------------------

    tree = STRtree(polygon_list)

    # ---------------------------------------------------------
    # Spatial candidate search
    # ---------------------------------------------------------

    for index_a, poly_a in enumerate(polygon_list):

        a = valid_parcels[index_a]

        ulpin_a = a.get("ulpin_3d")

        # Query spatially possible candidates.
        candidate_indices = tree.query(poly_a)

        for candidate_index in candidate_indices:

            candidate_index = int(candidate_index)

            # Avoid self-comparison and duplicate pair checking.
            if candidate_index <= index_a:
                continue

            b = valid_parcels[candidate_index]

            ulpin_b = b.get("ulpin_3d")

            # -------------------------------------------------
            # Parent-child / ancestor-descendant overlap
            # is valid.
            # -------------------------------------------------

            if _is_ancestor(
                ulpin_a,
                ulpin_b,
                parcel_map
            ):
                continue

            poly_b = polygon_list[candidate_index]

            # -------------------------------------------------
            # 2D overlap
            # -------------------------------------------------

            if not poly_a.intersects(poly_b):
                continue

            intersection_area = poly_a.intersection(
                poly_b
            ).area

            # Shared boundary / touching polygons are allowed.
            if intersection_area <= 0.001:
                continue

            # -------------------------------------------------
            # Vertical overlap
            # -------------------------------------------------

            bottom_a = a.get("bottom_z")
            top_a = a.get("top_z")

            bottom_b = b.get("bottom_z")
            top_b = b.get("top_z")

            if None in (
                bottom_a,
                top_a,
                bottom_b,
                top_b
            ):
                continue

            overlap_bottom = max(
                bottom_a,
                bottom_b
            )

            overlap_top = min(
                top_a,
                top_b
            )

            z_overlap = overlap_top - overlap_bottom

            if z_overlap <= 0.01:
                continue

            # -------------------------------------------------
            # Legitimate vertical cadastral relationships
            # -------------------------------------------------

            type_a = a.get("space_type")
            type_b = b.get("space_type")

            allowed_pair = {
                type_a,
                type_b
            }

            if allowed_pair in (
                {"G", "R"},
                {"G", "U"},
                {"G", "T"},
            ):
                continue

            # -------------------------------------------------
            # Conflict
            # -------------------------------------------------

            findings.append(
                finding(
                    "NO_VOLUME_OVERLAP",
                    "error",
                    (
                        f"3D volume overlap detected. "
                        f"XY overlap={intersection_area:.2f} m², "
                        f"Z overlap={z_overlap:.2f} m."
                    ),
                    [ulpin_a, ulpin_b],
                    z_overlap,
                    "m"
                )
            )

    return findings


# =========================================================
# 8. REQUIRED PARCEL FIELDS VALIDATION
# =========================================================

def check_required_fields(parcels):
    """
    Check that every parcel contains the minimum
    information required for validation.
    """

    required_fields = [
        "ulpin_3d",
        "footprint",
        "bottom_z",
        "top_z"
    ]

    findings = []

    for index, parcel in enumerate(parcels):

        for field in required_fields:

            if field not in parcel:
                findings.append({
                    "rule": "REQUIRED_FIELD",
                    "severity": "error",
                    "message": f"Parcel {index} is missing '{field}'",
                    "subjects": [parcel.get("ulpin_3d", f"parcel_{index}")]
                })

    return findings


# =========================================================
# 9. VERTICAL VALIDATION
# =========================================================

def check_vertical_extent(parcels):
    """
    Check whether every parcel has a valid vertical extent.
    """

    findings = []

    for index, parcel in enumerate(parcels):

        ulpin = parcel.get("ulpin_3d", f"parcel_{index}")

        bottom_z = parcel.get("bottom_z")
        top_z = parcel.get("top_z")

        if bottom_z is None or top_z is None:
            continue

        if bottom_z >= top_z:

            findings.append({
                "rule": "VERTICAL_EXTENT",
                "severity": "error",
                "message": (
                    f"Invalid vertical extent for {ulpin}: "
                    f"bottom_z={bottom_z}, top_z={top_z}"
                ),
                "subjects": [ulpin]
            })

    return findings


# =========================================================
# 10. WITHIN PARENT VALIDATION
# =========================================================
def check_within_parent(parcels):

    findings = []

    parcel_map = {
        parcel.get("ulpin_3d"): parcel
        for parcel in parcels
        if parcel.get("ulpin_3d")
    }

    for parcel in parcels:

        parent_id = parcel.get("parent")

        if not parent_id:
            continue

        parent = parcel_map.get(parent_id)

        if not parent:
            continue

        child_ring = parcel.get("footprint")
        parent_ring = parent.get("footprint")

        if not child_ring or not parent_ring:
            continue

        try:
            child_polygon = Polygon(child_ring)
            parent_polygon = Polygon(parent_ring)

            # A child is valid when essentially none
            # of its area lies outside the parent.
            outside_area = child_polygon.difference(
                parent_polygon
            ).area

            if outside_area > 0.001:

                findings.append(
                    finding(
                        "WITHIN_PARENT",
                        "error",
                        (
                            f"Parcel {parcel.get('ulpin_3d')} "
                            f"extends outside its parent parcel "
                            f"{parent_id}. "
                            f"Outside area={outside_area:.4f} m²."
                        ),
                        [
                            parcel.get("ulpin_3d"),
                            parent_id
                        ]
                    )
                )

        except Exception as e:

            findings.append(
                finding(
                    "WITHIN_PARENT",
                    "error",
                    (
                        f"Could not validate spatial relationship "
                        f"for {parcel.get('ulpin_3d')}: {str(e)}"
                    ),
                    [
                        parcel.get("ulpin_3d"),
                        parent_id
                    ]
                )
            )    

    return findings



# =========================================================
# 11. LEVEL SEQUENCE
# =========================================================

def check_level_sequence(parcels):

    findings = []

    levels = []

    for parcel in parcels:

        level = parcel.get("level")

        if isinstance(level, int):
            levels.append(level)

    if not levels:
        return findings

    unique_levels = sorted(set(levels))

    # Underground levels may be sparse because they can
    # represent different underground structures/depths.
    # Therefore, do not assume every negative level must exist.

    non_negative_levels = [
        level for level in unique_levels
        if level >= 0
    ]

    if len(non_negative_levels) < 2:
        return findings

    for expected_level in range(
        non_negative_levels[0],
        non_negative_levels[-1] + 1
    ):

        if expected_level not in non_negative_levels:

            findings.append(
                finding(
                    "LEVEL_SEQUENCE",
                    "warning",
                    f"Missing level in sequence: {expected_level}",
                    [],
                    expected_level
                )
            )

    return findings



# =========================================================
# 12. COORDINATE VALIDATION
# =========================================================
def check_coordinate_structure(parcels):

    findings = []

    for parcel in parcels:

        ulpin = parcel.get("ulpin_3d")
        footprint = parcel.get("footprint")

        if not footprint:
            continue

        for point in footprint:

            if not isinstance(point, (list, tuple)):
                findings.append(
                    finding(
                        "COORDINATE_STRUCTURE",
                        "error",
                        "Footprint coordinate must be a list or tuple.",
                        [ulpin]
                    )
                )
                break

            if len(point) != 2:
                findings.append(
                    finding(
                        "COORDINATE_STRUCTURE",
                        "error",
                        "Each footprint coordinate must contain exactly X and Y.",
                        [ulpin]
                    )
                )
                break

            try:
                float(point[0])
                float(point[1])
            except (TypeError, ValueError):
                findings.append(
                    finding(
                        "COORDINATE_STRUCTURE",
                        "error",
                        "Footprint coordinates must be numeric.",
                        [ulpin]
                    )
                )
                break

    return findings



# =========================================================
# 13. SPACE TYPE VALIDATION
# =========================================================

def check_space_type(parcels, allowed_types=None):

    if allowed_types is None:
        allowed_types = {
            "A",   # Apartment / unit
            "P",   # Parking
            "B",   # Basement
            "U",   # Underground infrastructure
            "T",   # Tunnel / transport
            "R",   # Roof / rooftop
            "G"    # Ground / general parcel
        }

    findings = []

    for parcel in parcels:

        ulpin = parcel.get("ulpin_3d")
        space_type = parcel.get("space_type")

        if space_type is None:
            findings.append(
                finding(
                    "SPACE_TYPE_VALIDATION",
                    "error",
                    "Parcel does not contain a space_type.",
                    [ulpin]
                )
            )
            continue

        if space_type not in allowed_types:

            findings.append(
                finding(
                    "SPACE_TYPE_VALIDATION",
                    "error",
                    f"Unknown space_type: {space_type}",
                    [ulpin]
                )
            )

    return findings



# =========================================================
# 14. LEVEL / Z CONSISTENCY
# =========================================================

def check_level_z_consistency(
    parcels,
    floor_height=3.2,
    tolerance=1.5
):

    findings = []

    # Space types where level * floor_height
    # is not a reliable direct representation
    excluded_types = {
        "G",   # Ground/general parcel
        "U",   # Underground infrastructure
        "T",   # Tunnel/transport
    }

    for parcel in parcels:

        ulpin = parcel.get("ulpin_3d")
        level = parcel.get("level")
        bottom_z = parcel.get("bottom_z")
        space_type = parcel.get("space_type")

        if (
            level is None
            or bottom_z is None
            or space_type in excluded_types
        ):
            continue

        expected_bottom = level * floor_height

        difference = abs(
            bottom_z - expected_bottom
        )

        if difference > tolerance:

            findings.append(
                finding(
                    "LEVEL_Z_CONSISTENCY",
                    "warning",
                    (
                        f"Level {level} suggests bottom_z around "
                        f"{expected_bottom:.2f} m, but actual "
                        f"bottom_z={bottom_z:.2f} m."
                    ),
                    [ulpin],
                    difference,
                    "m"
                )
            )

    return findings



# =========================================================
# 15. PARENT VERTICAL CONTAINMENT
# =========================================================

def check_parent_vertical_containment(
    parcels,
    tolerance=0.05
):

    findings = []

    parcel_map = {
        parcel.get("ulpin_3d"): parcel
        for parcel in parcels
        if parcel.get("ulpin_3d")
    }

    for parcel in parcels:

        child_id = parcel.get("ulpin_3d")
        parent_id = parcel.get("parent")

        if not parent_id:
            continue

        parent = parcel_map.get(parent_id)

        if not parent:
            continue

        child_bottom = parcel.get("bottom_z")
        child_top = parcel.get("top_z")

        parent_bottom = parent.get("bottom_z")
        parent_top = parent.get("top_z")

        if None in (
            child_bottom,
            child_top,
            parent_bottom,
            parent_top
        ):
            continue

        below_parent = parent_bottom - child_bottom
        above_parent = child_top - parent_top

        if (
            below_parent > tolerance
            or above_parent > tolerance
        ):

            findings.append(
                finding(
                    "PARENT_VERTICAL_CONTAINMENT",
                    "error",
                    (
                        f"Child {child_id} vertical extent "
                        f"({child_bottom:.2f}, {child_top:.2f}) "
                        f"lies outside parent {parent_id} extent "
                        f"({parent_bottom:.2f}, {parent_top:.2f})."
                    ),
                    [child_id, parent_id]
                )
            )

    return findings



# =========================================================
# 16. FOOTPRINT STRUCTURE
# =========================================================

def check_footprint_structure(parcels):

    findings = []

    for parcel in parcels:

        ulpin = parcel.get("ulpin_3d")
        footprint = parcel.get("footprint")

        if not footprint:
            continue

        if len(footprint) < 4:

            findings.append(
                finding(
                    "FOOTPRINT_STRUCTURE",
                    "error",
                    "Footprint must contain at least 4 coordinates including the closing point.",
                    [ulpin]
                )
            )
            continue

        if footprint[0] != footprint[-1]:

            findings.append(
                finding(
                    "FOOTPRINT_STRUCTURE",
                    "warning",
                    "Footprint polygon is not explicitly closed.",
                    [ulpin]
                )
            )

        unique_points = set(
            tuple(point)
            for point in footprint
            if isinstance(point, (list, tuple))
            and len(point) == 2
        )

        if len(unique_points) < 3:

            findings.append(
                finding(
                    "FOOTPRINT_STRUCTURE",
                    "error",
                    "Footprint must contain at least 3 unique vertices.",
                    [ulpin]
                )
            )

    return findings




# =========================================================
# 17. DUPLICATE 3D GEOMETRY
# =========================================================

def check_duplicate_geometry(parcels):

    findings = []

    polygons = {}

    parcel_map = {
        p.get("ulpin_3d"): p
        for p in parcels
        if p.get("ulpin_3d")
    }

    for parcel in parcels:

        ulpin = parcel.get("ulpin_3d")
        footprint = parcel.get("footprint")

        if not ulpin or not footprint:
            continue

        try:
            polygons[ulpin] = Polygon(footprint)
        except Exception:
            continue

    ids = list(polygons.keys())

    for i in range(len(ids)):

        a_id = ids[i]
        a = parcel_map[a_id]

        for j in range(i + 1, len(ids)):

            b_id = ids[j]
            b = parcel_map[b_id]

            # Parent-child relationships are allowed
            if _is_ancestor(a_id, b_id, parcel_map):
                continue

            poly_a = polygons[a_id]
            poly_b = polygons[b_id]

            if not poly_a.equals(poly_b):
                continue

            type_a = a.get("space_type")
            type_b = b.get("space_type")

            # Different cadastral space types can legitimately
            # share the same footprint and overlap vertically.
            if type_a != type_b:
                continue

            bottom_a = a.get("bottom_z")
            top_a = a.get("top_z")

            bottom_b = b.get("bottom_z")
            top_b = b.get("top_z")

            if None in (
                bottom_a,
                top_a,
                bottom_b,
                top_b
            ):
                continue

            z_overlap = min(top_a, top_b) - max(
                bottom_a,
                bottom_b
            )

            if z_overlap > 0.01:

                findings.append(
                    finding(
                        "DUPLICATE_GEOMETRY",
                        "error",
                        (
                            f"Duplicate 3D geometry detected "
                            f"between {a_id} and {b_id}."
                        ),
                        [a_id, b_id],
                        z_overlap,
                        "m"
                    )
                )

    return findings




# =========================================================
# 18. LEVEL VERTICAL ORDER
# =========================================================

def check_level_vertical_order(parcels, tolerance=0.10):

    findings = []

    # Only these represent actual floor/unit spaces
    comparable_types = {
        "A",   # Apartment / unit
        "P",   # Parking
        "B"    # Basement
    }

    level_ranges = {}

    for parcel in parcels:

        level = parcel.get("level")
        bottom = parcel.get("bottom_z")
        top = parcel.get("top_z")
        space_type = parcel.get("space_type")

        if (
            not isinstance(level, int)
            or bottom is None
            or top is None
            or space_type not in comparable_types
        ):
            continue

        if level not in level_ranges:
            level_ranges[level] = []

        level_ranges[level].append(
            (bottom, top, parcel.get("ulpin_3d"))
        )

    levels = sorted(level_ranges.keys())

    for i in range(len(levels) - 1):

        lower_level = levels[i]
        upper_level = levels[i + 1]

        # Only compare consecutive levels
        if upper_level != lower_level + 1:
            continue

        lower_top = max(
            item[1]
            for item in level_ranges[lower_level]
        )

        upper_bottom = min(
            item[0]
            for item in level_ranges[upper_level]
        )

        if upper_bottom < lower_top - tolerance:

            findings.append(
                finding(
                    "LEVEL_VERTICAL_ORDER",
                    "warning",
                    (
                        f"Level {upper_level} begins at "
                        f"{upper_bottom:.2f} m before level "
                        f"{lower_level} ends at "
                        f"{lower_top:.2f} m."
                    ),
                    [],
                    lower_top - upper_bottom,
                    "m"
                )
            )

    return findings







