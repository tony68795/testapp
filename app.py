import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from st_aggrid import GridUpdateMode, DataReturnMode
import os
import time
import traceback

# Pagina configuratie
st.set_page_config(page_title="Supermarkt Verkopen", layout="wide")
st.title("Supermarkt Verkopen Dashboard")

# Data inladen
@st.cache_data(ttl=1)  # Cache vervalt na 1 seconde
def load_data():
    try:
        # Laad hoofddata
        df = pd.read_excel('supermarkt_sales.xlsx')
        
        # Probeer bestaande opmerkingen te laden
        try:
            opmerkingen_df = pd.read_excel('opmerkingen.xlsx')
            df = pd.merge(df, opmerkingen_df[['Invoice ID', 'Opmerkingen']], 
                         on='Invoice ID', how='left', suffixes=('', '_y'))
        except:
            df['Opmerkingen'] = ''
            
        return df
    except Exception as e:
        st.error(f"Error bij het inladen van het bestand: {e}")
        return None

# Forceer herladen van data
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()

# Laad data
df = load_data()

if df is not None:
    # AG Grid configuratie
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(enabled=False)
    gb.configure_side_bar()
    
    # Configureer alle kolommen behalve Opmerkingen als niet-bewerkbaar
    for col in df.columns:
        if col != 'Opmerkingen':
            gb.configure_column(
                col,
                editable=False,
                groupable=True,
                value=True,
                enableRowGroup=True,
                aggFunc="sum",
                resizable=True,
                sortable=True,
                width=120  # Standaard breedte voor alle kolommen
            )
    
    # Configureer de Opmerkingen kolom als laatste
    gb.configure_column(
        "Opmerkingen",
        editable=True,
        width=200,
        pinned="right",
        headerName="Opmerkingen",  # Expliciete kolomnaam
        cellEditor='agLargeTextCellEditor',  # Grotere teksteditor
        cellEditorPopup=True,  # Editor in popup venster
        cellStyle={'white-space': 'normal'}  # Tekst kan wrappen
    )
    
    gridOptions = gb.build()
    
    # Voeg alternerende rijkleuren toe
    gridOptions['getRowStyle'] = JsCode("""
    function(params) {
        if (params.node.rowIndex % 2 === 0) {
            return {
                'background-color': '#f0f0f0'
            }
        }
    }
    """)

    # AG Grid weergeven
    grid_response = AgGrid(
        df,
        gridOptions=gridOptions,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=False,
        theme="streamlit",
        height=600,
        allow_unsafe_jscode=True,
        key='grid1'
    )

    # Update en sla de data op
    if st.button('Wijzigingen Opslaan'):
        try:
            # Converteer grid response naar DataFrame
            updated_df = pd.DataFrame(grid_response['data'])
            
            # Sla hoofddata op
            updated_df.to_excel('supermarkt_sales.xlsx', index=False, engine='openpyxl')
            
            # Filter en sla opmerkingen op
            opmerkingen_df = updated_df[['Invoice ID', 'Opmerkingen']].copy()
            opmerkingen_df = opmerkingen_df[opmerkingen_df['Opmerkingen'].notna() & 
                                          (opmerkingen_df['Opmerkingen'] != '')]
            
            # Sla opmerkingen op
            opmerkingen_df.to_excel('opmerkingen.xlsx', index=False, engine='openpyxl')
            
            # Update timestamp en clear cache
            st.session_state.last_update = time.time()
            st.cache_data.clear()
            
            st.success('Wijzigingen zijn opgeslagen!')
            
            # Toon opgeslagen opmerkingen
            if not opmerkingen_df.empty:
                st.write("Opgeslagen opmerkingen:")
                st.dataframe(opmerkingen_df)
            
            # Herlaad de pagina
            st.rerun()
            
        except Exception as e:
            st.error(f'Error bij het opslaan: {e}')
            st.write("Error details:", str(e))

    # Statistieken
    st.subheader("Dataset Statistieken")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Aantal Records", len(df))
    with col2:
        st.metric("Totaal Aantal Kolommen", len(df.columns))
    with col3:
        if "Total" in df.columns:
            st.metric("Totale Verkopen", f"€ {df['Total'].sum():,.2f}")