import streamlit as st
from google import genai
from google.genai import types

# --- CONFIGURATION ---
# In a real deployment, put your API key in Streamlit secrets (.streamlit/secrets.toml)
# For local testing, paste it below.
api_key = st.secrets.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")

# Initialize Gemini Client
client = genai.Client(api_key=api_key)

# --- THE HOMELORD SYSTEM PROMPT ---
SYSTEM_PROMPT = """
You are the "HomeLord Deal Analyzer," an expert real estate underwriter for Justin Midgley.
Your goal is to analyze Utah residential real estate listings to determine if they are viable "House Hacks".
You value math over emotion. You follow the "HomeLord Method" strictly.

**CRITICAL INSTRUCTION:**
1. You have access to Google Search. You MUST use it to search for the specific property address on UtahRealEstate.com, Zillow, or Redfin.
2. VISUALLY VERIFY "Basement Entrance" and "Rehab Needs" from listing descriptions or photos found in search.

### STEP 1: DATA EXTRACTION & ASSUMPTIONS
Extract live data. If missing, use these DEFAULTS:
- Down Payment: 3.5% (FHA)
- Interest Rate: 6.5%
- PMI: 0.5% of Loan Amount annually
- Home Insurance: $100/mo
- Property Tax (Utah Default): 0.6% of Purchase Price annually (if specific tax not listed)
- Rehab Cost: $5,000 (Cosmetic) unless photos imply "Fixer Upper"

### STEP 2: THE MATH (Calculate Precisely)
1. Total Loan = Price - Down Payment
2. Monthly PITI = Principal + Interest + Taxes + Insurance + PMI + HOA
3. Projected Income (BASEMENT ONLY):
   - Studio/1 Bed: $1,100
   - 2 Bed: $1,550
   - 3 Bed: $1,800
4. Offset % = Projected Income / Monthly PITI
5. Net Cost to Live = Monthly PITI - Projected Income
6. Standard Buying Power: Reverse engineer the Principal amount based on the "Net Cost to Live" payment using the same Rate/Tax/Ins assumptions.

### STEP 3: SCORING
- FAIL (F): No separate entrance OR HOA > $150/mo OR Ceiling < 7ft.
- PASS (C): Offset < 30%
- GOOD (B): Offset 30% - 39%
- GREAT (A): Offset 40% - 49%
- UNICORN (A+): Offset 50%+

### OUTPUT FORMAT (Strict Markdown):
---
**HOMELORD DEAL SCORE: [Grade]**
**Status:** [Viable / Not Viable]

**THE NUMBERS**
* **List Price:** $[Amount]
* **Total Monthly Payment (PITI):** $[Amount]
* **Est. Basement Rent:** $[Amount]
* **Net Cost to Live:** $[Amount] *(You save $[Savings vs PITI]/mo)*
* **Offset:** [Percent]%

**THE "WHY"**
* **Standard Buying Power:** $[Amount]
  *(Note: Without house hacking, a monthly payment of $[Net Cost to Live] would only allow you to buy a house at this price point. This deal gives you $[List Price] of value for $[Standard Buying Power] of payment.)*

**RISK ANALYSIS**
* **Pros:** [2-3 specific pros]
* **Cons:** [2-3 cons]

**MARKETING SNIPPET (Hormozi Style)**
*[Blind Deal hook focusing on Buying Power arbitrage]*

**DISCLAIMER:**
*Analysis based on listing data. Deep investigation required.*
---
"""

# --- THE APP INTERFACE ---
st.set_page_config(page_title="HomeLord Analyzer (Gemini)", page_icon="🏠")

st.title("🏠 HomeLord Deal Analyzer")
st.markdown("**Powered by Google Gemini + Google Search**")

# Input Section
address = st.text_input("Enter the Property Address or URL:", placeholder="e.g. 123 Main St, Salt Lake City, UT")

if st.button("Analyze Deal"):
    if not address:
        st.warning("Please enter an address.")
    else:
        with st.spinner(f"Searching Google for {address}... (This uses live search grounding)"):
            try:
                # Configure the tool for Google Search
                google_search_tool = types.Tool(
                    google_search=types.GoogleSearch()
                )

                # Call Gemini
                # We use 'gemini-2.0-flash' or 'gemini-1.5-pro' as they support search grounding well.
                response = client.models.generate_content(
                    model='gemini-2.0-flash', 
                    contents=f"Analyze this property: {address}",
                    config=types.GenerateContentConfig(
                        tools=[google_search_tool],
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.7
                    )
                )
                
                # Extract and display result
                # Gemini often returns "grounding metadata" (sources).
                # The text response is usually in the first candidate.
                analysis = response.text
                st.markdown(analysis)
                
                # Optional: Show Sources (Grounding)
                if response.candidates[0].grounding_metadata.search_entry_point:
                     st.markdown("---")
                     st.caption(f"Sources found: {response.candidates[0].grounding_metadata.search_entry_point.rendered_content}")

            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.info("Ensure your API key is correct and you are using a model that supports search (gemini-2.0-flash or gemini-1.5-pro).")

# Footer
st.markdown("---")
st.caption("Powered by The HomeLord Method | Built for Justin Midgley")
