from typing import Optional, Dict, Any, Tuple, List
from datetime import date, datetime, time


# Function to gather field constraints based on type
def get_field_constraints(st, field_type: str, method="default") -> Dict[str, Any]:
    constraints = {}
    if field_type in ["str", "Optional[str]"]:
        constraints["min_length"] = st.number_input("Minimum Length", min_value=0, step=1, value=0, key=f"min_length_{method}")
        constraints["max_length"] = st.number_input("Maximum Length", min_value=1, step=1, value=100, key=f"max_length_{method}")
        
    elif field_type in ["int", "Optional[int]", "float", "Optional[float]"]:
        constraints["gt"] = st.number_input("Greater Than", value=0, key=f"gt_{method}")
        constraints["lt"] = st.number_input("Less Than", value=100, key=f"lt_{method}")
        
        if field_type in ["float", "Optional[float]"]:
            constraints["max_digits"] = st.number_input("Max Digits", min_value=0, step=1, value=10, key=f"max_digits_{method}")
            constraints["decimal_places"] = st.number_input("Decimal Places", min_value=0, step=1, value=2, key=f"decimal_places_{method}")
            
    return constraints

# Model Generator Class to create model code
class ModelGenerator:
    @staticmethod
    def generate_code(model_name: str, field_data: list) -> str:
        code_lines = [
            "from pydantic import BaseModel, Field, field_validator\n",
            "from typing import Optional, List, Dict\n",
            "from datetime import date, datetime, time\n\n",
            f"class {model_name}(BaseModel):\n"
        ]

        example_items = []
        for field in field_data:
            field_name = field["name"]
            field_type = field["type"]
            constraints = field.get("constraints", {})
            custom_validations = field.get("custom_validations", [])
            
            # Generate field definition
            field_constraints = ", ".join([f"{k}={v!r}" for k, v in constraints.items() if k != "nullable"])
            code_lines.append(f"    {field_name}: {field_type} = Field({field_constraints})\n")

            # Generate field validators
            for idx, (logic, error_message) in enumerate(custom_validations, start=1):
                code_lines.extend([
                    f"    @field_validator('{field_name}')\n",
                    f"    def validate_{field_name}_{idx}(cls, value):\n",
                    f"        if {logic}:\n",
                    f"            raise ValueError('{error_message}')\n",
                    f"        return value\n\n"
                ])
            
            # Build example data
            example_items.append({
                "name": field.get("name", ""),
                "value": field.get("value", ""),
                "type": field.get("type", "")
            })
        
        # Generate example usage
        example_params = ", ".join(f"{item['name']}=\"{item['value']}\"" if item["type"] == "str" else f"{item['name']}={item['value']}" for item in example_items)
        code_lines.extend([
            "\n\n# Example Usage\n",
            f"{model_name.lower().replace('model', '')} = {model_name}({example_params})\n"
        ])

        return "".join(code_lines)   


class FieldManager:
    type_mapping = {
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "date": date,
        "datetime": datetime,
        "dict": dict,
        "list": list,
        "time": time,
    }

    @staticmethod
    def add_field(st, field_name: str, field_type: str, field_value: str, constraints: Dict[str, Any], custom_validations: List[Tuple[str, str]]) -> None:
        python_type = f"Optional[{field_type}]" if constraints.get("nullable", False) else field_type
        st.session_state.field_data.append({
            "name": field_name,
            "type": python_type,
            "value": field_value,
            "constraints": constraints,
            "custom_validations": custom_validations,
        })

    @staticmethod
    def remove_field(st, index: int) -> None:
        if 0 <= index < len(st.session_state.field_data):
            st.session_state.field_data.pop(index)

    @staticmethod
    def update_field(st, index: int, field_name: str, field_type: str, field_value: str, constraints: Dict[str, Any], custom_validations: List[Tuple[str, str]]) -> None:
        if 0 <= index < len(st.session_state.field_data):
            python_type = f"Optional[{field_type}]" if constraints.get("nullable", False) else field_type
            st.session_state.field_data[index] = {
                "name": field_name,
                "type": python_type,
                "value": field_value,
                "constraints": constraints,
                "custom_validations": custom_validations,
            }