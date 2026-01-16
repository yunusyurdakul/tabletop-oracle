# 🐉 Oracle & Scribe: Ancient Rule Repository

A multi-tool tabletop gaming application designed to safeguard the balance of your realm and simplify the ancient tomes of law. This repository houses the **House Rule Oracle** for rule analysis and **The Scribe** for rulebook simplification.

🔗 **Live Demo:** [tabletop-oracle.streamlit.app](https://tabletop-oracle.streamlit.app/)

![Background](background.png)

## 🔮 House Rule Oracle
The Oracle analyzes your proposed house rules against official rulebooks (or its own vast internal knowledge) to predict their impact on your game.
- **Risk Assessment**: Instantly see if a rule is Safe, Risky, or Game-Breaking.
- **Impact Radar**: Visualizes Balance, Complexity, Fun Factor, Pacing, and Clarity.
- **Deep Dive**: Identifies contradictions, economic shifts, and potential exploits.
- **Refinement Scrolls**: Provides AI-generated suggestions to fix problematic rules.

## 📜 The Scribe (Rule Simplifier)
The Scribe transforms complex, dense rulebooks into progressive learning modes tailored for any adventurer.
- **🌱 First Game**: Simple language and core mechanics for an immediate start.
- **⚔️ Advanced**: Introduces strategic depth and secondary rules.
- **👑 Expert**: The complete codex with all nuances and edge cases.
- **Feedback**: Rate the Scribe's work to improve future divinations.

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Gemini API Key ([Get it here](https://aistudio.google.com/app/apikey))

### Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```
4. Add your `GEMINI_API_KEY` to the `.env` file.

### Running the Tool
```bash
streamlit run app.py
```

## 🛠️ Built With
- **Streamlit**: For the interactive fantasy interface.
- **Google Gemini**: Quantum-class AI for rule analysis and summarization.
- **Plotly**: For the magical radar charts.
- **PyPDF**: For extracting secrets from ancient PDFs.

---
*Analysis provided by Gemini. Data cutoff: Oct 2023.*
