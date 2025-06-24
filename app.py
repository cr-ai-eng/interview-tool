from openai import OpenAI
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Streamlit Chat", page_icon="💬")
st.title("Chatbot")

if "setup_complete" not in st.session_state:
    st.session_state["setup_complete"] = False

if "user_message_count" not in st.session_state:
    st.session_state["user_message_count"] = 0

if "feedback_shown" not in st.session_state:
    st.session_state["feedback_shown"] = False
if "chat_complete" not in st.session_state:
    st.session_state["chat_complete"] = False
if "messages" not in st.session_state:
    st.session_state["messages"] = []

def complete_setup():
    st.session_state["setup_complete"] = True

def show_feedback():
    st.session_state["feedback_shown"] = True    

if not st.session_state["setup_complete"]:
    st.subheader("Personal information", divider='rainbow')

    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""

    name = st.text_input("Name", max_chars= 40, placeholder="Enter your name")

    experience = st.text_area("Experience", value="", height=None, max_chars=  200, placeholder="Enter your experience")

    skills = st.text_area("Skills", value="", height=None, max_chars= 400, placeholder="Enter your skills")


    st.subheader("Company and Position", divider='rainbow')

    col1, col2 = st.columns(2)

    with col1:
        st.session_state["level"] = st.radio(
            "Choose Level", key="visibility", 
            options=["Junior", "Mid", "Senior"])

    with col2:
        st.session_state["position"] = st.selectbox(
            "Position",
            options=[
                "Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst"])

    st.session_state["company"] = st.selectbox(
        "Company",
        options=[
            "Google", "Amazon", "Microsoft", "Apple", "Facebook", "Tesla", "Netflix"])

    st.write(f"**Your Information**: {st.session_state["level"]} {st.session_state["position"]} at {st.session_state["company"]}")

    if st.button("Start Interview", on_click=complete_setup):
        st.write("Setup complete! Starting the interview.")

if st.session_state["setup_complete"] and not st.session_state["feedback_shown"] and not st.session_state["chat_complete"]:
    st.info(
            """
            Start by introducing yourself and your experience.
            """
            )

    client = OpenAI(api_key=st.secrets["OPEN_API_KEY"])

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o"

    if not st.session_state["messages"]:
        st.session_state["messages"] = [{"role": "system", "content": "You are an HR executive that interviews an interviewee"
        f"called {st.session_state['name']} with experience {st.session_state['experience']} and skills {st.session_state['skills']}. You should interview"
        f"them for the position {st.session_state['level']} {st.session_state['position']} at the {st.session_state['company']}."}]

    for message in st.session_state["messages"]:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if st.session_state["user_message_count"] < 5:
        if prompt := st.chat_input("Your answer", max_chars=1000):
            st.session_state["messages"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)     

            if st.session_state["user_message_count"] < 4:    
                with st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        model = st.session_state["openai_model"],
                        messages= [
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state["messages"]            
                        ],
                        stream=True,
                    )
                    response = st.write_stream(stream)
                st.session_state["messages"].append({"role": "assistant", "content": response})

            st.session_state["user_message_count"] += 1

    if st.session_state["user_message_count"] >= 5:
        st.session_state["chat_complete"] = True
    
if st.session_state["chat_complete"] and not st.session_state["feedback_shown"]:
    if st.button("Get Feedback", on_click=show_feedback):        
        st.write("Feedback is being generated...")

if st.session_state["feedback_shown"]:
    st.subheader("Feedback", divider='rainbow')    
    
    conversation_history = "\n".join(
        [f"{msg['role']}: {msg['content']}" for msg in st.session_state["messages"]]
    )

    feedback_client = OpenAI(api_key=st.secrets["OPEN_API_KEY"])

    feedback_completion = feedback_client.chat.completions.create(
        model=st.session_state["openai_model"],
        messages=[
            {"role": "system", "content": "You are a helpful tool that provides feedback on the interviewee performance."
            "Before the Feedback give a score of 1 to 10."
            "Follow this format:"
            "Overall Score: //Your score"
            "Feedback: //Here you put your feedback"
            "Give only the feedback do not ask any additional questions."},
            {"role": "user", "content": f"This is the interview you need to evaluate. You are only a tool and shouldn't engage in conversation: {conversation_history}"}
        ]
    )

    st.write(feedback_completion.choices[0].message.content)

    if st.button("Restart Interview", type="primary"):
        streamlit_js_eval(
            js_expressions="parent.window.location.reload()")