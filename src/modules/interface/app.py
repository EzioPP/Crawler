import json
import streamlit as st
import random
import time


def read_data():
    try:
        with open("streamlit_in.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    

def write_data(data):
    with open("streamlit_out.json", "w") as f:
        json.dump(data, f, indent=4)

def get_inputs():
    with st.form("crawler_inputs"):
        base_url = st.text_input("URL Base", "https://example.com")
        max_depth = st.slider("Profundidade Máxima", min_value=1, max_value=10, value=3)
        question = st.text_area("Pergunta", "Que informação você está procurando?")
        processes = st.slider("Número de Processos Concorrentes", min_value=1, max_value=8, value=4)
        
        submitted = st.form_submit_button("Iniciar Crawler")
        
        if submitted:
            data = {
                "type": "main",
                "base_url": base_url,
                "max_depth": max_depth,
                "question": question,
                "processes": processes,
                "current_step": 0
            }
            write_data(data)
            return data
    return None

if __name__ == "__main__":
    input = False
    st.title("Crawler 🕷️")
    
    if 'completed_steps' not in st.session_state:
        st.session_state.completed_steps = set()
    if 'last_file_update' not in st.session_state:
        st.session_state.last_file_update = time.time()
    if 'last_data' not in st.session_state:
        st.session_state.last_data = {}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    step_container = st.container()
    completion_container = st.empty()
    
    while True: 
        data = read_data()
        
        if data != st.session_state.last_data:
            st.session_state.last_data = data
            st.session_state.last_file_update = time.time()
            
        if not data and not input:
            get_inputs()
            input = True
            break
            
        if data and "steps" in data:
            steps = data["steps"]
        else:
            steps = [f"Step {i}: Processing data" for i in range(1, 11)]
        
        current_step = data.get("current_step", 0)
        
        progress = current_step / len(steps) if steps else 0
        progress_bar.progress(progress)
        
        status_text.info(f"Processing step {current_step}/{len(steps)}")
        
        with step_container:
            st.empty()
            for i, step in enumerate(steps):
                if i < current_step:
                    st.success(f"✅ {step} (complete)")
                    if i not in st.session_state.completed_steps:
                        st.session_state.completed_steps.add(i)
                        write_data({"progress": (i + 1) / len(steps)})
                elif i == current_step:
                    st.info(f"⏳ {step} (running...)")
                else:
                    st.text(f"⏹️ {step} (pending)")
        
        if current_step >= len(steps) and steps:
            completion_container.success("All processes completed successfully!")
            st.balloons()
            write_data({"status": "completed"})
            break
        
        time.sleep(1)
        st.rerun()
