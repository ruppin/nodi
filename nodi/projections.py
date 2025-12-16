"""Output projection support for filtering JSON fields."""

from typing import Any, List, Dict, Union, Optional


class JSONProjection:
    """Apply field projections to JSON data to reduce output."""

    def apply(self, data: Any, projection: Union[List, Dict]) -> Any:
        """
        Apply projection to data.

        Args:
            data: JSON data (dict, list, or primitive)
            projection: Field specification (list of field names or nested dict)

        Returns:
            Projected data with only specified fields
        """
        if isinstance(data, list):
            return [self._project_item(item, projection) for item in data]
        else:
            return self._project_item(data, projection)

    def _project_item(self, item: Any, projection: Union[List, Dict]) -> Any:
        """Project a single item."""
        if not isinstance(item, dict):
            # Can't project non-dict items
            return item

        if isinstance(projection, list):
            # Simple list of field names
            return self._project_fields(item, projection)
        elif isinstance(projection, dict):
            # Nested projection spec
            return self._project_nested(item, projection)
        else:
            return item

    def _project_fields(self, item: Dict, fields: List[str]) -> Dict:
        """Project simple list of fields."""
        result = {}
        for field in fields:
            if isinstance(field, str):
                # Simple field name
                if field in item:
                    result[field] = item[field]
            elif isinstance(field, dict):
                # Nested field spec
                for key, nested_fields in field.items():
                    if key in item and isinstance(item[key], dict):
                        result[key] = self._project_fields(item[key], nested_fields)
                    elif key in item:
                        result[key] = item[key]
        return result

    def _project_nested(self, item: Dict, projection: Dict) -> Dict:
        """Project using nested dict specification."""
        result = {}
        for field, nested_spec in projection.items():
            if field not in item:
                continue

            if nested_spec is None or nested_spec is True:
                # Include field as-is
                result[field] = item[field]
            elif isinstance(nested_spec, list):
                # Nested field list
                if isinstance(item[field], dict):
                    result[field] = self._project_fields(item[field], nested_spec)
                elif isinstance(item[field], list):
                    result[field] = [
                        self._project_fields(sub_item, nested_spec)
                        if isinstance(sub_item, dict) else sub_item
                        for sub_item in item[field]
                    ]
                else:
                    result[field] = item[field]
            elif isinstance(nested_spec, dict):
                # Recursive nested spec
                if isinstance(item[field], dict):
                    result[field] = self._project_nested(item[field], nested_spec)
                else:
                    result[field] = item[field]

        return result


def parse_projection_spec(spec: Union[List, Dict, str]) -> Union[List, Dict]:
    """
    Parse projection specification into normalized format.

    Args:
        spec: Projection spec (list, dict, or string)

    Returns:
        Normalized projection spec
    """
    if isinstance(spec, str):
        # Convert comma-separated string to list
        return [field.strip() for field in spec.split(",")]
    elif isinstance(spec, list):
        return spec
    elif isinstance(spec, dict):
        return spec
    else:
        raise ValueError(f"Invalid projection spec type: {type(spec)}")
