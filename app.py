from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, Tuple, List
from datetime import date, datetime, time
import streamlit as st
import tempfile


def init_streamlit():
    st.set_page_config(layout="wide", page_title="Dynamic Pydantic Schema Builder", page_icon="📊")
    
    hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True) 
    

    # Initialize session state for model name and fields
    if "field_data" not in st.session_state:
        st.session_state.field_data = []
    if "model_name" not in st.session_state:
        st.session_state.model_name = ""
    if "edit_index" not in st.session_state:
        st.session_state.edit_index = None
    if "custom_validations" not in st.session_state:
        st.session_state.custom_validations = []


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
    def add_field(field_name: str, field_type: str, constraints: Dict[str, Any], custom_validations: List[Tuple[str, str]]) -> None:
        python_type = f"Optional[{field_type}]" if constraints.get("nullable", False) else field_type
        st.session_state.field_data.append({
            "name": field_name,
            "type": python_type,
            "constraints": constraints,
            "custom_validations": custom_validations,
        })

    @staticmethod
    def remove_field(index: int) -> None:
        if 0 <= index < len(st.session_state.field_data):
            st.session_state.field_data.pop(index)

    @staticmethod
    def update_field(index: int, field_name: str, field_type: str, constraints: Dict[str, Any], custom_validations: List[Tuple[str, str]]) -> None:
        if 0 <= index < len(st.session_state.field_data):
            st.session_state.field_data[index] = {
                "name": field_name,
                "type": field_type,
                "constraints": constraints,
                "custom_validations": custom_validations,
            }

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

        for field in field_data:
            field_name = field["name"]
            field_type = field["type"]
            constraints = field.get("constraints", {})
            constraints_code = ", ".join([f"{k}={v!r}" for k, v in constraints.items() if k != "nullable"])

            code_lines.append(f"    {field_name}: {field_type} = Field({constraints_code})\n")

            # Adding field validators for custom validations
            for idx, (logic, error_message) in enumerate(field["custom_validations"], start=1):
                code_lines.append(
                    f"    @field_validator('{field_name}')\n"
                    f"    def validate_{field_name}_{idx}(cls, value):\n"
                    f"        if {logic}:\n"
                    f"            raise ValueError('{error_message}')\n"
                    f"        return value\n\n"
                )

        return "".join(code_lines)

# Function to gather field constraints based on type
def get_field_constraints(field_type: str) -> Dict[str, Any]:
    constraints = {}
    if field_type == "str":
        constraints["min_length"] = st.number_input("Minimum Length", min_value=0, step=1, value=0, key="min_length")
        constraints["max_length"] = st.number_input("Maximum Length", min_value=1, step=1, value=100, key="max_length")
        constraints["nullable"] = st.checkbox("Nullable", value=False, key="nullable")
    elif field_type in ["int", "float"]:
        constraints["gt"] = st.number_input("Greater Than", value=0, key="gt")
        constraints["lt"] = st.number_input("Less Than", value=100, key="lt")
        if field_type == "float":
            constraints["max_digits"] = st.number_input("Max Digits", min_value=0, step=1, value=10, key="max_digits")
            constraints["decimal_places"] = st.number_input("Decimal Places", min_value=0, step=1, value=2, key="decimal_places")
        constraints["nullable"] = st.checkbox("Nullable", value=False, key="nullable")
    elif field_type in ["date", "datetime", "time"]:
        constraints["nullable"] = st.checkbox("Nullable", value=False, key="nullable")
    elif field_type == "dict":
        constraints["nullable"] = st.checkbox("Nullable", value=False, key="nullable")
    elif field_type == "list":
        constraints["nullable"] = st.checkbox("Nullable", value=False, key="nullable")

    return constraints

# Main Application Function
def main():
    init_streamlit()
    st.title("Dynamic Pydantic Schema Builder")
    st.write("Streamlit application to build Pydantic models dynamically within the UI, with validation and error handling.")

    # Input for model name
    model_name_input = st.text_input("**Enter Model Name**", key="model_name_input").strip().capitalize() + "Model"
    if model_name_input != st.session_state.model_name:
        st.session_state.model_name = model_name_input

    col1, col2 = st.columns(2)

    # Expander for adding a new field or editing an existing field
    with col1:
        with st.expander("**Add / Edit Field**"):
            if st.session_state.edit_index is not None:
                # Editing mode
                field_data = st.session_state.field_data[st.session_state.edit_index]
                field_name_input = st.text_input("Field Name", value=field_data["name"], key="field_name_input")
                field_type_input = st.selectbox("Field Type", options=["str", "int", "float", "bool", "date", "datetime", "dict", "list", "time"],
                                                 index=["str", "int", "float", "bool", "date", "datetime", "dict", "list", "time"].index(field_data["type"]),
                                                 key="field_type_input")
                constraints = get_field_constraints(field_type_input)

                # Display current custom validations
                st.session_state.custom_validations = field_data["custom_validations"]

                # Inputs for custom validations
                with st.form("validation_form"):
                    validation_logic = st.text_input("Validation Logic (e.g., value > 100)", value=st.session_state.custom_validations[-1][0] if st.session_state.custom_validations else "", key="validation_logic")
                    validation_message = st.text_input("Error Message", value=st.session_state.custom_validations[-1][1] if st.session_state.custom_validations else "", key="validation_message")
                    submit_validation = st.form_submit_button("Add Validation")

                    # Append validation logic and message if provided
                    if submit_validation and validation_logic and validation_message:
                        st.session_state.custom_validations.append((validation_logic, validation_message))
                        st.success("Validation added!")

                # Display added custom validations
                if st.session_state.custom_validations:
                    st.subheader("Custom Validations")
                    for idx, (logic, message) in enumerate(st.session_state.custom_validations):
                        st.write(f"{idx + 1}. {logic} → {message}")
                        # Optionally, provide a button to remove a specific validation
                        if st.button(f"Remove Validation {idx + 1}", key=f"remove_validation_{idx}"):
                            st.session_state.custom_validations.pop(idx)
                            st.success(f"Validation {idx + 1} removed!")
                            st.rerun()

                # Button to confirm field update
                if st.button("Update Field"):
                    if field_name_input:
                        FieldManager.update_field(st.session_state.edit_index, field_name_input, field_type_input, constraints, st.session_state.custom_validations.copy())
                        st.session_state.edit_index = None  # Reset edit index
                        st.session_state.custom_validations.clear()  # Reset custom validations
                        st.success(f"Field '{field_name_input}' updated successfully!")

                        # Reset input fields after confirmation
                        st.session_state.field_type = "str"  # Reset to default field type
                        for key in st.session_state.keys():  # Clear all constraint input fields
                            if key in ["min_length", "max_length", "gt", "lt", "max_digits", "decimal_places", "nullable", "validation_logic", "validation_message"]:
                                del st.session_state[key]
                        st.rerun()

            else:
                # Adding new field mode
                field_name_input = st.text_input("Field Name", key="field_name_input")
                field_type_input = st.selectbox("Field Type", options=["str", "int", "float", "bool", "date", "datetime", "dict", "list", "time"],
                                                 index=["str", "int", "float", "bool", "date", "datetime", "dict", "list", "time"].index(st.session_state.field_data[-1]["type"]) if st.session_state.field_data else 0,
                                                 key="field_type_input")
                constraints = get_field_constraints(field_type_input)

                # Inputs for custom validations
                with st.form("validation_form"):
                    validation_logic = st.text_input("Validation Logic (e.g., value > 100)", key="validation_logic")
                    validation_message = st.text_input("Error Message", key="validation_message")
                    submit_validation = st.form_submit_button("Add Validation")

                    # Append validation logic and message if provided
                    if submit_validation and validation_logic and validation_message:
                        st.session_state.custom_validations.append((validation_logic, validation_message))
                        st.success("Validation added!")

                # Button to confirm adding the field
                if st.button("Add Field"):
                    if field_name_input:
                        FieldManager.add_field(field_name_input, field_type_input, constraints, st.session_state.custom_validations.copy())
                        st.success(f"Field '{field_name_input}' added successfully!")

                        # Reset input fields after confirmation
                        st.session_state.field_type = "str"  # Reset to default field type
                        for key in st.session_state.keys():  # Clear all constraint input fields
                            if key in ["min_length", "max_length", "gt", "lt", "max_digits", "decimal_places", "nullable", "validation_logic", "validation_message"]:
                                del st.session_state[key]
                        st.rerun()

    # Column for displaying and editing fields
    with col2:
        if st.session_state.field_data:
            with st.expander("Field List"):
                for index, field in enumerate(st.session_state.field_data):
                    st.write(f"**{field['name']}**: {field['type']}")
                    st.write(f"  - **Constraints:** {field['constraints']}")
                    st.write(f"  - **Custom Validations:** {field['custom_validations']}")
                    # Button to edit the field
                    if st.button(f"Edit Field {field['name']}", key=f"edit_field_{index}"):
                        st.session_state.edit_index = index  # Set the edit index to the current field
                        st.rerun()
                    # Button to remove the field
                    if st.button(f"Remove Field {field['name']}", key=f"remove_field_{index}"):
                        FieldManager.remove_field(index)
                        st.success(f"Field '{field['name']}' removed successfully!")
                        st.rerun()

        # Generate Model Code Button
        if st.session_state.model_name and st.session_state.field_data:
            model_code = ModelGenerator.generate_code(st.session_state.model_name, st.session_state.field_data)
            st.subheader("Generated Model Code")
            st.code(model_code, language="python")

            with st.expander("Save and Download Model"):
                schema_name = st.text_input("Enter Schema Name", value="schema", key="schema_name")
                if st.button("Download Model"):
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
                        tmp_file.write(model_code)
                        tmp_file.flush()
                        with open(tmp_file.name, 'rb') as f:
                            st.download_button(label=f"Download {schema_name}.py", data=f, file_name=f"{schema_name}.py", mime="text/x-python")
                    st.success(f"Model ready for download as {schema_name}.py!")
if __name__ == "__main__":
    main()