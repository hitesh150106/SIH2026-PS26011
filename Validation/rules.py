from shapely.geometry import Polygon

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

def check_no_volume_overlap(parcels):

    findings = []

    polygons = {}

    for parcel in parcels:

        ulpin = parcel.get("ulpin_3d")
        ring = parcel.get("footprint")

        if not ring:
            continue

        try:
            polygons[ulpin] = Polygon(ring)
        except Exception:
            continue

    # Pairwise comparison
    for i in range(len(parcels)):

        a = parcels[i]
        ulpin_a = a.get("ulpin_3d")

        if ulpin_a not in polygons:
            continue

        poly_a = polygons[ulpin_a]

        for j in range(i + 1, len(parcels)):

            b = parcels[j]
            ulpin_b = b.get("ulpin_3d")

            if ulpin_b not in polygons:
                continue

            poly_b = polygons[ulpin_b]

            # First: 2D overlap
            if not poly_a.intersects(poly_b):
                continue

            intersection_area = poly_a.intersection(
                poly_b
            ).area

            if intersection_area <= 0.001:
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

            # Second: vertical overlap
            overlap_bottom = max(
                bottom_a,
                bottom_b
            )

            overlap_top = min(
                top_a,
                top_b
            )

            z_overlap = overlap_top - overlap_bottom

            if z_overlap > 0.01:

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
            # Parent existence is handled separately
            continue

        child_ring = parcel.get("footprint")
        parent_ring = parent.get("footprint")

        if not child_ring or not parent_ring:
            continue

        try:
            child_polygon = Polygon(child_ring)
            parent_polygon = Polygon(parent_ring)

            if not child_polygon.within(parent_polygon):

                findings.append(
                    finding(
                        "WITHIN_PARENT",
                        "error",
                        (
                            f"Parcel {parcel.get('ulpin_3d')} "
                            f"is outside its parent parcel "
                            f"{parent_id}."
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
                    [parcel.get("ulpin_3d"), parent_id]
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

    for expected_level in range(
        unique_levels[0],
        unique_levels[-1] + 1
    ):

        if expected_level not in unique_levels:

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

