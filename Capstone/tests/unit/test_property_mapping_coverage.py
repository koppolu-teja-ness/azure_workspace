from migration_assistant.mapping.equivalence_models import (
    load_property_rules,
    load_resource_mapping_types,
    missing_property_mapping_coverage,
)


def test_property_mapping_coverage_for_all_resource_type_mappings() -> None:
    mapped_types = load_resource_mapping_types()
    property_rules = load_property_rules()

    missing = missing_property_mapping_coverage(mapped_types, property_rules)

    assert not missing, (
        "Missing property mapping files or rules for resource types: "
        f"{sorted(item.value for item in missing)}"
    )
