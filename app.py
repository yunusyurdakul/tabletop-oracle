import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os
from dotenv import load_dotenv
import json
import plotly.graph_objects as go
from io import BytesIO
import traceback
import logging

# Configure terminal logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Oracle & Scribe: Ancient Rule Repository
# A tool for tabletop game masters and players to analyze house rules and simplify complex manuals.

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
default_model = os.getenv("GEMINI_MODEL_NAME", "gemini-3-flash-preview")

if api_key:
    genai.configure(api_key=api_key)

# Global CSS for Premium Look
def local_css():
    import base64
    bg_img_path = os.path.join(os.getcwd(), "background.png")
    bg_img_base64 = ""
    if os.path.exists(bg_img_path):
        with open(bg_img_path, "rb") as img_file:
            bg_img_base64 = base64.b64encode(img_file.read()).decode()

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=MedievalSharp&display=swap');

    html, body, [class*="css"] {{
        font-family: 'MedievalSharp', cursive;
    }}

    .stApp {{
        background-image: linear-gradient(rgba(18, 18, 31, 0.85), rgba(18, 18, 31, 0.95)), 
                          url("data:image/png;base64,{bg_img_base64}");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }}
    .main {{
        background: transparent;
        color: #e0e0e0;
    }}
    .stMetric {{
        background-color: rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(10px);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(0, 210, 255, 0.2);
    }}
    .stTextArea textarea, .stTextInput input {{
        background-color: rgba(37, 37, 56, 0.6) !important;
        backdrop-filter: blur(5px);
        color: #ffffff !important;
        border: 1px solid rgba(0, 210, 255, 0.3) !important;
        font-family: 'MedievalSharp', cursive !important;
    }}
    h1, h2, h3, h4 {{
        color: #00d2ff !important;
        font-family: 'Cinzel', serif !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        letter-spacing: 1px;
    }}
    /* Sidebar glassmorphism */
    [data-testid="stSidebar"] {{
        background-color: rgba(18, 18, 31, 0.7) !important;
        backdrop-filter: blur(15px);
    }}
    .stButton button {{
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    .stButton button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 210, 255, 0.4);
    }}
    .stExpander {{
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def extract_text_from_pdf(pdf_file_bytes, file_name):
    """Extracts text from an uploaded PDF file (cached)."""
    try:
        reader = PdfReader(BytesIO(pdf_file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting PDF text from {file_name}: {e}")
        logger.error(traceback.format_exc())
        return None

class HouseRuleOracle:
    @staticmethod
    def create_radar_chart(impact_scores):
        categories = ['Balance', 'Complexity', 'Fun Factor', 'Pacing', 'Clarity']
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=[impact_scores.get(c, 5) for c in categories],
            theta=categories,
            fill='toself',
            name='Impact',
            line_color='#00d2ff',
            fillcolor='rgba(0, 210, 255, 0.3)',
            hovertemplate='<b>%{theta}</b>: %{r}/10<extra></extra>'
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True, 
                    range=[0, 10], 
                    gridcolor="rgba(255,255,255,0.1)",
                    tickfont=dict(color="rgba(255,255,255,0.5)")
                ),
                angularaxis=dict(
                    gridcolor="rgba(255,255,255,0.1)",
                    tickfont=dict(size=12, color="#00d2ff")
                ),
                bgcolor="rgba(0,0,0,0)"
            ),
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=60, r=60, t=20, b=20),
            height=320,
            hovermode='closest'
        )
        return fig

    @staticmethod
    def analyze(game_title, official_rules, house_rule, model_name):
        if not house_rule: return None
        context_str = f"Game Title: {game_title}\n\n" if game_title else ""
        if official_rules:
            context_str += f"Official Rules (Context from PDFs):\n---\n{official_rules}\n---"
        else:
            context_str += "Note: No official rulebook PDF was provided. Rely on your internal knowledge."

        prompt = f"""
        You are an expert tabletop game designer and rules lawyer. 
        Analyze the 'House Rule' for '{game_title or 'this game'}'.

        {context_str}

        Proposed House Rule:
        ---
        {house_rule}
        ---

        Analysis Criteria:
        1. **Contradictions**: Breaks existing rules?
        2. **Economics**: Resource impact?
        3. **Exploits**: Infinite loops/Solved states?
        4. **Pacing**: Game length impact?
        5. **Impact Scores** (0-10): Balance, Complexity, Fun Factor, Pacing, Clarity.

        Return JSON:
        {{
            "risk_score": "Safe | Risky | Game-Breaking",
            "risk_emoji": "✅ | ⚠️ | ❌",
            "risk_explanation": "A detailed 1-2 sentence explanation of the risk level.",
            "summary": "...",
            "contradictions": [],
            "impact_scores": {{ "Balance": 7, "Complexity": 8, "Fun Factor": 9, "Pacing": 6, "Clarity": 10 }},
            "balance_impact": "...",
            "exploits": "...",
            "game_pace": "...",
            "suggestions": [
                {{ "rule": "...", "explanation": "..." }}
            ]
        }}
        """
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.2))
            content = response.text
            if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content: content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"Oracle Analysis Error: {e}")
            logger.error(traceback.format_exc())
            return None

class RuleSimplifier:
    @staticmethod
    def simplify(rulebook_text, game_title, model_name):
        if not rulebook_text: return None
        
        prompt = f"""
        You are an expert tabletop game educator. 
        Your task is to rewrite the provided rulebook text for '{game_title or 'a tabletop game'}' into three progressive learning modes.

        Rulebook Text:
        ---
        {rulebook_text}
        ---

        Output Specifications:
        1. **First Game Rules**: Simplify using straightforward language, focusing ONLY on core mechanics and essential gameplay. Use bullet points and short paragraphs.
        2. **Advanced Rules**: Include additional mechanics and strategies but maintain clarity. Provide clear examples.
        3. **Expert Rules**: Comprehensive overview including all nuances, edge cases, and advanced strategies for experienced players.

        Return JSON:
        {{
            "first_game": "Markdown text for first game rules",
            "advanced": "Markdown text for advanced rules",
            "expert": "Markdown text for expert rules",
            "summary": "Quick meta-summary of the rulebook structure"
        }}
        """
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.3))
            content = response.text
            if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content: content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"Scribe Simplification Error: {e}")
            logger.error(traceback.format_exc())
            return None

class RulebookValidator:
    KEYWORDS = ["setup", "gameplay", "components", "turn order", "victory conditions", "rules", "player", "phase"]
    
    @staticmethod
    def validate(text, file_name, model_name):
        """Validates if a document is a board game rulebook using keywords and AI."""
        if not text:
            return {"is_rulebook": False, "reason": "No readable text found in the tome."}
        
        # 1. Fast Keyword Check
        text_lower = text.lower()
        found_keywords = [k for k in RulebookValidator.KEYWORDS if k in text_lower]
        
        # If very few keywords found, trigger AI verification
        if len(found_keywords) < 2:
            prompt = f"""
            Analyze the following text snippet from a file named '{file_name}'.
            Determine if this is a board game rulebook.
            
            Text Snippet:
            ---
            {text[:2000]}
            ---
            
            Return JSON:
            {{
                "is_rulebook": bool,
                "reason": "Clear explanation of why it is or isn't a rulebook"
            }}
            """
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.1))
                return json.loads(response.text.replace("```json", "").replace("```", "").strip())
            except Exception as e:
                logger.error(f"Validator AI check failed for {file_name}: {e}")
                logger.error(traceback.format_exc())
                return {"is_rulebook": False, "reason": "The Oracle could not verify this text's nature."}
        
        return {"is_rulebook": True, "reason": "Valid board game terminology detected."}

class LogicValidator:
    @staticmethod
    def is_logical_input(text, context_type, model_name):
        """Checks if the input text is a logical game rule or question."""
        if not text or len(text.strip()) < 5:
            return {"is_logical": False, "reason": "The scroll is too short or empty to be meaningful."}
        
        prompt = f"""
        Determine if the following text is a logical and relevant {context_type} for a tabletop game.
        It should not be gibberish, offensive, or completely unrelated to gaming.
        
        Text: "{text}"
        
        Return JSON:
        {{
            "is_logical": bool,
            "reason": "Brief explanation (1 sentence)"
        }}
        """
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.1))
            content = response.text
            if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content: content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"Logic Validator Error: {e}")
            return {"is_logical": True, "reason": "The Oracle's intuition allows this to pass."}

class RuleMasterAssistant:
    @staticmethod
    def answer_question(question, rulebook_text, game_title, model_name):
        if not question: return None
        
        context_str = f"Game Title: {game_title}\n\n" if game_title else ""
        if rulebook_text:
            context_str += f"Official Rules (Context from PDFs):\n---\n{rulebook_text}\n---"
        else:
            context_str += "Note: No official rulebook PDF was provided. Rely on your internal knowledge."

        prompt = f"""
        You are the 'RuleMaster Assistant', a divine sage and expert in tabletop game rules for '{game_title or 'all games'}'. 
        Your task is to answer user questions about the game rules accurately and concisely, citing the official rules where possible.

        {context_str}

        User Question:
        ---
        {question}
        ---

        Return your answer in Markdown format. If the answer is not found in the provided rules, use your vast internal knowledge but mention that it's based on general game expertise.
        """
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.4))
            return response.text
        except Exception as e:
            logger.error(f"RuleMaster Assistant Error: {e}")
            logger.error(traceback.format_exc())
            return None

# Main UI Logic
st.set_page_config(page_title="Tabletop Oracle", page_icon="🧙", layout="wide")
local_css()

if not api_key:
    st.warning("Please configure your GEMINI_API_KEY in the .env file.")

# Sidebar Navigation
with st.sidebar:
    st.title("🧙 Rule Repository")
    tool_choice = st.radio("Choose Your Tool", ["🐉 House Rule Oracle", "📜 Rule Simplifier", "🧙 RuleMaster Assistant"])
    st.divider()
    st.header("Campaign Settings")
    game_title = st.text_input("Game Title", placeholder="e.g., D&D 5e, Terraforming Mars")
    uploaded_files = st.file_uploader("Ancient Tomes (Rulebooks)", type="pdf", accept_multiple_files=True)
    
    # Real-time Validation
    if uploaded_files:
        st.subheader("🛡️ Tome Authentication")
        valid_files = []
        for uf in uploaded_files:
            # Check cached validation
            file_key = f"valid_{uf.name}_{uf.size}"
            if file_key not in st.session_state:
                text = extract_text_from_pdf(uf.getvalue(), uf.name)
                st.session_state[file_key] = RulebookValidator.validate(text, uf.name, default_model)
            
            v_res = st.session_state[file_key]
            if v_res.get("is_rulebook"):
                st.success(f"✅ **{uf.name}**: Authenticated rulebook.")
                valid_files.append(uf)
            else:
                st.error(f"⚠️ **{uf.name}**: Rejected.\n*{v_res.get('reason')}*")
        
        uploaded_files = valid_files # Only pass valid files to tools

    with st.expander("Advanced Tools"):
        selected_model = st.selectbox("Engine", ["gemini-3-flash-preview", "gemini-2.0-flash-exp", "gemini-1.5-pro"])
        context_preview = st.checkbox("Preview Context", value=False)

# Shared Session State
if "house_rule" not in st.session_state: st.session_state.house_rule = ""
if "processing" not in st.session_state: st.session_state.processing = False
if "simplification_result" not in st.session_state: st.session_state.simplification_result = None

def set_processing(): st.session_state.processing = True

# Page Rendering
if tool_choice == "🐉 House Rule Oracle":
    st.title("🐉 House Rule Oracle")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📜 Proposed House Rule")
        house_rule_input = st.text_area("Proposed House Rule", value=st.session_state.house_rule, height=180, key="oracle_input", placeholder="Scribe your ancient rule change here...", label_visibility="collapsed")
        
        if st.button("🔮 Consult the Oracle", use_container_width=True, disabled=st.session_state.processing, on_click=set_processing):
            if not uploaded_files:
                st.warning("Please upload at least one ancient tome (rulebook) before consulting the Oracle.")
                st.session_state.processing = False
            elif not house_rule_input.strip():
                st.warning("Rule cannot be empty.")
                st.session_state.processing = False
            else:
                status_placeholder = st.empty()
                with status_placeholder.status("Consulting the Oracle...", expanded=True) as status_box:
                    # Logic Validation
                    status_box.write("Checking the logic of your rule...")
                    logic_res = LogicValidator.is_logical_input(house_rule_input, "house rule", selected_model)
                    if not logic_res.get("is_logical"):
                        st.error(f"⚠️ **The Oracle rejects this rule:** {logic_res.get('reason')}")
                        st.session_state.processing = False
                        status_box.update(label="Logic Check Failed", state="error", expanded=False)
                        st.stop() # Stop execution

                    combined_text = ""
                    if uploaded_files:
                        for uf in uploaded_files:
                            text = extract_text_from_pdf(uf.getvalue(), uf.name)
                            if text: combined_text += f"\nFILE: {uf.name}\n{text}"
                    
                    if len(combined_text) > 1000000: combined_text = combined_text[:1000000]
                    
                    result = HouseRuleOracle.analyze(game_title, combined_text, house_rule_input, selected_model)
                    st.session_state.oracle_result = result
                    status_box.update(label="Divination Complete!", state="complete", expanded=False)
                st.session_state.processing = False
                st.rerun()

    if "oracle_result" in st.session_state:
        res = st.session_state.oracle_result
        with col2:
            if res is None: st.error("⚠️ The Oracle has gone silent. Please try again.")
            else:
                st.subheader("🔮 Divination Results")
                
                # Enhanced Risk Display
                risk_level = res.get('risk_score', 'Unknown')
                risk_emoji = res.get('risk_emoji', '❓')
                risk_expl = res.get('risk_explanation', 'The Oracle weighs the consequences...')
                
                if "Safe" in risk_level:
                    st.success(f"### {risk_emoji} Risk Status: {risk_level}\n{risk_expl}")
                elif "Risky" in risk_level:
                    st.warning(f"### {risk_emoji} Risk Status: {risk_level}\n{risk_expl}")
                else:
                    st.error(f"### {risk_emoji} Risk Status: {risk_level}\n{risk_expl}")

                st.plotly_chart(HouseRuleOracle.create_radar_chart(res.get('impact_scores', {})), use_container_width=True)
                st.write(f"**Insight:** {res.get('summary', 'No summary available.')}")
                with st.expander("🔍 Deep Dive Details"):
                    tabs = st.tabs(["Contradictions", "Economics", "Pacing"])
                    with tabs[0]: 
                        for c in res.get('contradictions', []): st.info(c)
                    with tabs[1]: st.write(res.get('balance_impact', 'N/A'))
                    with tabs[2]: st.write(res.get('game_pace', 'N/A'))
                st.divider()
                st.subheader("💡 Expert Refinements")
                for i, sugg in enumerate(res.get('suggestions', [])):
                    with st.container():
                        st.markdown(f"**Scroll {i+1}:** {sugg.get('rule')}")
                        st.caption(sugg.get('explanation'))
                        if st.button(f"✨ Invoke Scroll {i+1}", key=f"apply_{i}"):
                            st.session_state.house_rule = sugg.get('rule')
                            st.rerun()
                
                # Export Oracle Result
                oracle_md = f"# Oracle Divination: {game_title or 'Unknown Game'}\n\n"
                oracle_md += f"## Risk: {res.get('risk_score')}\n"
                oracle_md += f"**Risk Explanation:** {res.get('risk_explanation', 'N/A')}\n\n"
                oracle_md += f"**Summary:** {res.get('summary')}\n\n"
                oracle_md += f"### Impact Scores\n"
                for k, v in res.get('impact_scores', {}).items():
                    oracle_md += f"- {k}: {v}/10\n"
                
                st.download_button(
                    label="📜 Download Divination Scroll",
                    data=oracle_md,
                    file_name=f"oracle_results_{game_title or 'game'}.md",
                    mime="text/markdown"
                )

elif tool_choice == "📜 Rule Simplifier":
    st.title("📜 Rule Simplifier")
    st.markdown("Rewrite complex ancient rulebooks into three progressive learning modes.")
    
    if st.button("✨ Scribe Simplified Rules", use_container_width=True, disabled=st.session_state.processing, on_click=set_processing):
        if not uploaded_files:
            st.warning("Please upload at least one ancient tome (rulebook) first.")
            st.session_state.processing = False
        else:
            status_placeholder = st.empty()
            with status_placeholder.status("Simplifying the Tomes...", expanded=True) as status_box:
                combined_text = ""
                for uf in uploaded_files:
                    text = extract_text_from_pdf(uf.getvalue(), uf.name)
                    if text: combined_text += f"\nFILE: {uf.name}\n{text}"
                
                if len(combined_text) > 500000: combined_text = combined_text[:500000]
                
                result = RuleSimplifier.simplify(combined_text, game_title, selected_model)
                st.session_state.simplification_result = result
                status_box.update(label="Scribing Complete!", state="complete", expanded=False)
            st.session_state.processing = False
            st.rerun()

    if st.session_state.simplification_result:
        res = st.session_state.simplification_result
        if res is None: st.error("⚠️ The Scribe failed to simplify the rules. Please try again.")
        else:
            st.write(f"**The Scribe's Overview:** {res.get('summary', 'No summary available.')}")
            
            tabs = st.tabs(["🌱 First Game", "⚔️ Advanced", "👑 Expert"])
            with tabs[0]: 
                st.info("Perfect for families and first-time adventurers.")
                st.markdown(res.get('first_game', 'Error generation.'))
            with tabs[1]: 
                st.warning("For those who have completed their first quest.")
                st.markdown(res.get('advanced', 'Error generation.'))
            with tabs[2]: 
                st.error("The complete codex for masters of the realm.")
                st.markdown(res.get('expert', 'Error generation.'))
            
            # Export Simplified Rules
            simplifier_md = f"# Rule Simplification: {game_title or 'Unknown Game'}\n\n"
            simplifier_md += f"## 🌱 First Game Rules\n{res.get('first_game')}\n\n"
            simplifier_md += f"## ⚔️ Advanced Rules\n{res.get('advanced')}\n\n"
            simplifier_md += f"## 👑 Expert Rules\n{res.get('expert')}\n"

            st.download_button(
                label="📜 Download Simplified Scroll",
                data=simplifier_md,
                file_name=f"simplified_rules_{game_title or 'game'}.md",
                mime="text/markdown"
            )
            
            st.divider()
            st.subheader("📝 Feedback to the Scribe")
            rating = st.feedback("stars")
            if rating is not None:
                st.success(f"The Scribe bows in gratitude for your {rating+1}-star review!")

elif tool_choice == "🧙 RuleMaster Assistant":
    st.title("🧙 RuleMaster Assistant")
    st.markdown("Ask the divine sage any question about the rules of your game.")
    
    if "assistant_qa" not in st.session_state:
        st.session_state.assistant_qa = []

    # Display previous Q&A
    for q, a in st.session_state.assistant_qa:
        with st.chat_message("user", avatar="👤"):
            st.write(q)
        with st.chat_message("assistant", avatar="🧙"):
            st.write(a)

    user_question = st.chat_input("Ask the RuleMaster Sage...")
    
    if user_question:
        if not uploaded_files:
            st.warning("Please upload at least one ancient tome (rulebook) before asking questions.")
        else:
            with st.chat_message("user", avatar="👤"):
                st.write(user_question)
            
            status_placeholder = st.empty()
            with status_placeholder.status("Consulting the Sage...", expanded=True) as status_box:
                # Logic Validation
                status_box.write("Analyzing your inquiry...")
                logic_res = LogicValidator.is_logical_input(user_question, "question about game rules", selected_model)
                if not logic_res.get("is_logical"):
                    st.chat_message("assistant", avatar="🧙").error(f"The Sage only discusses game rules. {logic_res.get('reason')}")
                    status_box.update(label="Inquiry Rejected", state="error", expanded=False)
                    st.stop() # Stop execution

                combined_text = ""
                if uploaded_files:
                    for uf in uploaded_files:
                        text = extract_text_from_pdf(uf.getvalue(), uf.name)
                        if text: combined_text += f"\nFILE: {uf.name}\n{text}"
                
                if len(combined_text) > 800000: combined_text = combined_text[:800000]
                
                answer = RuleMasterAssistant.answer_question(user_question, combined_text, game_title, selected_model)
                
                if answer:
                    st.session_state.assistant_qa.append((user_question, answer))
                    status_box.update(label="The Sage has spoken!", state="complete", expanded=False)
                    st.rerun()
                else:
                    status_box.update(label="The Sage is silent...", state="error", expanded=False)
                    st.error("The Sage could not provide an answer. Please try again.")

st.divider()
st.caption("Quantum-class analysis provided by Gemini. Data cutoff: Oct 2023.")
