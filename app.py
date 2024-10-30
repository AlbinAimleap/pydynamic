from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, Tuple, List
import streamlit as st
import tempfile

from utils import FieldManager, ModelGenerator, get_field_constraints



def init_streamlit(st):
    st.set_page_config(layout="wide", page_title="Dynamic Pydantic Schema Builder", page_icon="📊")
    
    hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True) 
    
    if "field_data" not in st.session_state:
        st.session_state.field_data = []
    if "model_name" not in st.session_state:
        st.session_state.model_name = ""
    if "edit_index" not in st.session_state:
        st.session_state.edit_index = None
    if "custom_validations" not in st.session_state:
        st.session_state.custom_validations = []

# Main Application Function
def main():
    init_streamlit(st)
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
            field_types = ["str", "int", "float", "bool", "date", "datetime", "dict", "list", "time"]
            optional_field_types = [f"Optional[{field_type}]" for field_type in field_types]
            all_field_types = field_types + optional_field_types
            
            if st.session_state.edit_index is not None:
                # Editing mode
                field_data = st.session_state.field_data[st.session_state.edit_index]
                field_name_input = st.text_input("Field Name", value=field_data["name"], key="field_name_input")
                field_type_input = st.selectbox(
                    "Field Type", options=all_field_types,
                    index=all_field_types.index(field_data["type"]),
                    key="field_type_input"
                )
                field_value_input = st.text_input("Field_value", key="field_value_input")
                constraints = get_field_constraints(st, field_type_input, method="update")

                # Display current custom validations for this field
                custom_validations_key = f"custom_validations_{field_data['name']}"
                if custom_validations_key not in st.session_state:
                    st.session_state[custom_validations_key] = field_data["custom_validations"]

                # Inputs for custom validations
                with st.form("validation_form"):
                    validation_logic = st.text_input("Validation Logic (e.g., value > 100)", value=st.session_state[custom_validations_key][-1][0] if st.session_state[custom_validations_key] else "", key="validation_logic")
                    validation_message = st.text_input("Error Message", value=st.session_state[custom_validations_key][-1][1] if st.session_state[custom_validations_key] else "", key="validation_message")
                    submit_validation = st.form_submit_button("Add Validation")

                    # Append validation logic and message if provided
                    if submit_validation and validation_logic and validation_message:
                        st.session_state[custom_validations_key].append((validation_logic, validation_message))
                        st.success("Validation added!")

                # Display added custom validations
                if st.session_state[custom_validations_key]:
                    st.subheader("Custom Validations")
                    for idx, (logic, message) in enumerate(st.session_state[custom_validations_key]):
                        st.write(f"{idx + 1}. {logic} → {message}")
                        # Optionally, provide a button to remove a specific validation
                        if st.button(f"Remove Validation {idx + 1}", key=f"remove_validation_{idx}"):
                            st.session_state[custom_validations_key].pop(idx)
                            st.success(f"Validation {idx + 1} removed!")
                            st.rerun()

                # Button to confirm field update
                if st.button("Update Field"):
                    if field_name_input:
                        FieldManager.update_field(st, st.session_state.edit_index, field_name_input, field_type_input, field_value_input, constraints, st.session_state[custom_validations_key].copy())
                        st.session_state.edit_index = None  # Reset edit index
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
                field_type_input = st.selectbox(
                    "Field Type", options=all_field_types,
                    index=all_field_types.index(st.session_state.field_data[-1]["type"]) if st.session_state.field_data else 0,
                    key="field_type_input"
                )
                field_value_input = st.text_input("Field Value (Example Usage)", key="field_value_input")
                constraints = get_field_constraints(st, field_type_input, method="add")
                # Initialize custom validations for new field
                if field_name_input:
                    custom_validations_key = f"custom_validations_{field_name_input}"
                    if custom_validations_key not in st.session_state:
                        st.session_state[custom_validations_key] = []

                    # Inputs for custom validations
                    with st.form("validation_form"):
                        validation_logic = st.text_input("Validation Logic (e.g., value > 100)", key="validation_logic")
                        validation_message = st.text_input("Error Message", key="validation_message")
                        submit_validation = st.form_submit_button("Add Validation")

                        # Append validation logic and message if provided
                        if submit_validation and validation_logic and validation_message:
                            st.session_state[custom_validations_key].append((validation_logic, validation_message))
                            st.success("Validation added!")

                    # Button to confirm adding the field
                    if st.button("Add Field"):
                        if field_name_input:                            
                            FieldManager.add_field(st, field_name_input, field_type_input, field_value_input, constraints, st.session_state[custom_validations_key].copy())
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
                    constraints = ", ".join([f"{key}={value}" for key, value in field['constraints'].items()])
                    st.write(f"**{field['name']}**: {field['type']}")
                    st.write(f"  - **Constraints:** {constraints}")
                    st.write(f"  - **Custom Validations:**")
                    for validation, message in field['custom_validations']:
                        st.write(f"       • **Validation:** {validation}")
                        st.write(f"       • **Message:** {message}")
                        
                    # Button to edit the field
                    if st.button(f"Edit Field {field['name']}", key=f"edit_field_{index}"):
                        st.session_state.edit_index = index  # Set the edit index to the current field
                        st.rerun()
                    # Button to remove the field
                    if st.button(f"Remove Field {field['name']}", key=f"remove_field_{index}"):
                        FieldManager.remove_field(st, index)
                        st.success(f"Field '{field['name']}' removed successfully!")
                        st.rerun()

        # Generate Model Code Button
        if st.session_state.model_name and st.session_state.field_data:
            model_code = ModelGenerator.generate_code(st.session_state.model_name, st.session_state.field_data)
            st.subheader("Generated Model Code")
            st.code(model_code, language="python")

            with st.expander("Save and Download Model"):
                schema_name = st.text_input("Enter Schema Name", value="schema", key="schema_name")
                if st.button("Generate Model"):
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
                        tmp_file.write(model_code)
                        tmp_file.flush()
                        with open(tmp_file.name, 'rb') as f:
                            st.download_button(label=f"Download {schema_name}.py", data=f, file_name=f"{schema_name}.py", mime="text/x-python")
                    st.success(f"Model ready for download as {schema_name}.py!")
                    
                    
if __name__ == "__main__":
    main()