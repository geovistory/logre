from typing import List, Any
import streamlit as st
import lib.state as state
from model import OntoEntity, DataSet
from lib import generate_id


def __create_entity(entity: OntoEntity, triples: List[tuple[str, str, str]]) -> None:

    # From state
    data_set = state.get_data_set()

    # Create all the triples
    data_set.graph_data.insert(triples)

    # From formular, set the session entity
    state.set_entity(entity)
    
    # Here the entity with all information are directly set, 
    # (because they are available correctly)
    # Doing so, information reloading are prevented to be fetched again
    # in the entity page (through get_entity_basic_infos)

    # Finalization: validation message and load the created entity
    state.set_toast('Entity Created', ':material/done:')
    st.switch_page("pages/entity.py")


@st.dialog('Create an entity', width='large')
def dialog_create_entity() -> None:
    """
    Dialog function allowing the user to create a new entity.
    The formular is deducted from the SHACL taken from the Model graph.
    Class (rdf:type), label (rdfs:label), comment (rdfs:comment) are mandatory, whatever the ontology.
    """

    # From state
    data_set = state.get_data_set()
    classes = data_set.ontology.get_classes()
    properties = data_set.ontology.get_properties()

    # Save triples that are going to be created on create click
    triples: List[tuple[str, str, str]] = []

    # Also, keep a list of mandatories properties to check if all of them are present
    mandatories: List[str] = []

    # In order to create those triples, we also need to have an id and a URI, 
    # They are generated on dialog open
    id = generate_id()
    entity_uri = f"base:{id}"


    ### First part: mandatory fields ###

    # In all case, we make 3 statements mandatory, independant of the ontology.
    # They are: the class, the label, and the comment.
    col_label, col_range = st.columns([2, 3])

    # Class selection
    classes_labels = list(map(lambda cls: cls.display_label, classes))
    class_label = col_label.selectbox('Class ❗️', options=classes_labels, index=None)
    mandatories.append(data_set.type_property)
    if class_label:
        # Find the selected class from the selected label
        class_index = classes_labels.index(class_label)
        selected_class = classes[class_index]

        # Add the entity type triple
        triples.append((entity_uri, data_set.type_property, selected_class.uri))

        # Input field to set the entity label
        mandatory_suffix = ''
        if data_set.ontology.is_property_mandatory(selected_class.uri, data_set.label_property):
            mandatory_suffix = ' ❗️'
            mandatories.append(data_set.label_property)
        entity_label = col_range.text_input('Label' + mandatory_suffix)
        if entity_label:
            label = entity_label.strip().replace("'", "\\'")
            triples.append((entity_uri, data_set.label_property, f"'{label}'"))

        # Input field to set the comment label
        mandatory_suffix = ''
        if data_set.ontology.is_property_mandatory(selected_class.uri, data_set.comment_property):
            mandatory_suffix = ' ❗️'
            mandatories.append(data_set.comment_property)
        entity_comment = st.text_input('Comment' + mandatory_suffix)
        if entity_comment and entity_comment.strip() != '':
            comment = entity_comment.strip().replace("'", "\\'")
            triples.append((entity_uri, data_set.comment_property, f"'{comment}'"))

        st.divider()


        ### Second part: formular for all triples from ontology

        # Get the right relevant prop from the ontology
        # Only outgoing ones!
        props_to_create = [prop for prop in properties if prop.domain_class_uri == selected_class.uri]
        # Also, remove those that are mandatory, in order to not set them multiple times
        props_to_create = [prop for prop in props_to_create if prop.uri not in [data_set.type_property, data_set.label_property, data_set.comment_property]]
        # And we order it so that it appears in the correct order
        props_to_create.sort(key=lambda p: p.order)

        # Loop through all relevant properties and display the right input Field
        for i, prop in enumerate(props_to_create):

            col_label, col_range, col_info = st.columns([4, 6, 2], vertical_alignment='bottom') 

            # Information about the property
            with col_info.popover('', icon=':material/info:'):
                st.markdown('### Property information')

                c1, c2 = st.columns([1, 1])
                c1.markdown("URI: ")
                c2.markdown(prop.uri)

                c1, c2 = st.columns([1, 1])
                c1.markdown("Order: ")
                c2.markdown(prop.order if prop.order != 1000000000000000000 else 'n')

                c1, c2 = st.columns([1, 1])
                c1.markdown("Minimal count: ")
                c2.markdown(prop.min_count)

                c1, c2 = st.columns([1, 1])
                c1.markdown("Maximal count: ")
                c2.markdown(prop.max_count if prop.max_count != 1000000000000000000 else 'n')

            # Append a special char if the field is mandatory
            # ie if the min cardinality is strictly bigger than 0
            # And add the property to the mandatories accordingly
            if prop.is_mandatory():
                suffix = "❗️"
                mandatories.append(prop.uri)
            else:
                suffix = ""

            # On the left: Property label
            col_label.markdown(f"## {prop.label} {suffix}")
            col_label.text('')
            
            # For code simplification
            field_key = f"dlg-create-entity-field-{i}"

            # If the range is a xsd:string, display a text field
            if prop.range_class_uri == 'xsd:string':
                
                # Dedicated behavior:
                # Here, if the property have a max count greater that 1,
                # We would like to give the user the possibility to add them accrodingly
                # So the strategy is the following:
                # Each time the user fill a value, we display another empty field so that he can add another value
                # Limited by the max count of the cardinality, once it is reached

                def recursive_call_xsdstring(index: int) -> None:
                    """Recursive call that add another field each time the previous one has a value (and maxcount not reached)."""
                    string_value = col_range.text_input(data_set.ontology.get_class_name(prop.range_class_uri), key=field_key + f"-{index}", placeholder="Start writing to add a new value")
                    if string_value and string_value.strip() != '':
                        value = string_value.strip().replace("'", "\\'")
                        triples.append((entity_uri, prop.uri, f"'{value}'"))
                    if string_value and index < prop.max_count:
                        recursive_call_xsdstring(index + 1)
                recursive_call_xsdstring(1)   

            # If the range is a xsd:html, display a text area
            elif prop.range_class_uri == 'xsd:html':
                
                # Dedicated behavior:
                # Here, if the property have a max count greater that 1,
                # We would like to give the user the possibility to add them accordingly
                # So the strategy is the following:
                # Each time the user fill a value, we display another empty field so that he can add another value
                # Limited by the max count of the cardinality, once it is reached

                def recursive_call_xsdhtml(index: int) -> None:
                    """Recursive call that add another field each time the previous one has a value (and maxcount not reached)."""
                    html_value = col_range.text_area(data_set.ontology.get_class_name(prop.range_class_uri), key=field_key + f"-{index}", placeholder="Start writing to add a new value")
                    if html_value and html_value.strip() != '':
                        value = html_value.strip().replace("'", "\\'")
                        triples.append((entity_uri, prop.uri, f"'{value}'"))
                    if html_value and index < prop.max_count:
                        recursive_call_xsdhtml(index + 1)
                recursive_call_xsdhtml(1)   

            # If the range is not a Literal, it should then be instances of classes 
            else: 
                # List all possible existing entities (right class) from the endpoint
                possible_objects: List[OntoEntity] = data_set.find_entities(class_uri=prop.range_class_uri)
                # Get their label
                possible_objects_label = [obj.display_label_comment for obj in possible_objects]
                # User form input field
                if prop.max_count == 1: 
                    object_label = col_range.selectbox(data_set.ontology.get_class_name(prop.range_class_uri), options=possible_objects_label, key=field_key, index=None)
                    if object_label:
                        object_index = possible_objects_label.index(object_label)
                        object = possible_objects[object_index]
                        triples.append((entity_uri, prop.uri, object.uri))
                else: 
                    object_labels = col_range.multiselect(data_set.ontology.get_class_name(prop.range_class_uri), options=possible_objects_label, key=field_key)
                    if object_labels:
                        for object_label in object_labels:
                            object_index = possible_objects_label.index(object_label)
                            object = possible_objects[object_index]
                            triples.append((entity_uri, prop.uri, object.uri))
            
            st.text('')

        st.divider()

        # Check if all the mandatory properties are actually in the triple list
        all_mandatories_present = True
        triples_properties = set([triple[1] for triple in triples])
        for mandatory in mandatories:
            if not mandatory in triples_properties:
                all_mandatories_present = False
                break
        
        # Validation, creation, and display
        if st.button('Create', disabled=not all_mandatories_present, icon=':material/add:'):
            entity = OntoEntity(
                uri=entity_uri, 
                label=entity_label, 
                comment=entity_comment, 
                class_uri=selected_class.uri,
                class_label=selected_class.label
            )
            __create_entity(entity, triples)