import streamlit as st
from tools.sparql_queries import list_used_classes, list_entities
from datetime import datetime
import pandas as pd


@st.dialog("Find an entity", width='large')
def dialog_find_entity() -> None:
    """
    Dialog function that will look in the SPARQL endpoint in order to make the user find a given entity.
    Dialog will close once the user choses the wanted entity.
    The chosen entity will be set in the session as "selected_entity".
    """

    if 'endpoint' not in st.session_state:
        st.warning('You must first choose an endpoint')
        return

    # First, begin to load all the used classes on the endpoint
    classes = []
    selected_graphs = [graph for graph in st.session_state['all_graphs'] if graph['activated']]
    for graph in selected_graphs:
        with st.spinner(f'Fetching all classes from graph {graph["label"]}...'):
            classes += list_used_classes(graph['uri'])

    # If no classes has been found on the endpoint
    if not classes: 
        st.info("Nothing is listed as a class on this endpoint")
        return

    # User commands: Select a class, and type an entity name
    col1, col2 = st.columns([2, 4])
    selected_class_label = col1.selectbox('Entity class (optional)', [cls['label'] for cls in classes], index=None, placeholder='Class', help="Performance is highly improved when selecting a class.")
    label = col2.text_input("Entity label", placeholder='Start to write the entity label')

    # If the user has selected a class, find the one
    if selected_class_label:
        selected_class = [cls for cls in classes if cls['label'] == selected_class_label][0]
    else:
        selected_class = None

    # When the input is validated
    if label:
        with st.spinner("Fetching corresponding entities from endpoint"):
            for graph in selected_graphs:
                entities = list_entities(label, selected_class['uri'] if selected_class is not None else None, graph=graph['uri'])

            # If some entities match: display them with a select option
            if entities:
                st.divider()

                for i, entity in enumerate(entities):
                    display_label = f"{entity['label']} ({entity['class_label']})"
                    col1, col2 = st.columns([5, 2])
                    if st.button(display_label, type='tertiary', key=f"find_entity_{i}"):
                        st.session_state['selected_entity'] = {
                            'uri': entity['uri'],
                            'display_label': display_label
                        }
                        st.rerun()
                    
            else:
                st.info('No entities found')

