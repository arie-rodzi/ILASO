ILASO Premium 6-File System
===========================

Run:
    pip install streamlit pandas numpy openpyxl pulp plotly
    streamlit run app.py

Files:
1. app.py               Main Streamlit app and workflow
2. config_styles.py     Constants and premium CSS
3. ui_components.py     Hero, KPI cards and reusable UI
4. data_utils.py        File reading, cleaning, preparation, export helpers
5. optimizer.py         Fair KS optimizer and output builder
6. emergency_engine.py  Emergency reallocation engine with repeated log support

Emergency workflow:
- Run Fair KS Allocation first.
- Emergency section uses saved allocation only.
- It does not rerun optimizer.
- Multiple emergency cases are appended into Emergency Log.
- Previous emergency KS is considered when selecting next replacement lecturer.
