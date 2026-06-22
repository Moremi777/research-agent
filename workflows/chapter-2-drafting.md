# Chapter 2 Drafting Workflow — Literature Review

## Objective
Guide the user through writing Chapter 2 (Literature Review) with a thematic structure. This chapter synthesises the literature — it does not just summarise individual papers.

## Prerequisites
- At least 20–30 sources read with notes in the tracker
- Sources tagged with relevance tags and chapter relevance labels
- Chapter 1 draft completed (provides context for the lit review scope)

## Chapter 2 Structure

### Section 2.1 — Introduction
**Purpose**: Explain the scope and structure of the literature review. What themes will be covered and why.
**Prompts**:
- "What is the purpose of this chapter? What will it cover?"
- "List the main themes you will review and why they are relevant to your research question."
- "End with a brief roadmap of the sections."

### Section 2.2 — Thematic Review of the Problem Domain

#### 2.2.1 — Indigenous Farming Knowledge Systems in Southern Africa
**Purpose**: Review the literature on IK systems, their importance, current state, and challenges.
**Prompts**:
- "What do researchers say about the value of indigenous farming knowledge?"
- "What are the threats to IK preservation in Southern Africa specifically?"
- "How do different authors define and categorise IK in agriculture?"
- "Where do authors agree? Where do they disagree?"
**Key synthesis question**: "What does the literature collectively tell us about the state of IK in Southern African agriculture?"

Show relevant sources:
```
python -m tools.manage_sources --action list --filters '{"relevance_tags": ["indigenous_knowledge"]}'
```

#### 2.2.2 — Serious Games and Game-Based Learning in Education
**Purpose**: Review how serious games have been used for education, learning theories that underpin them.
**Prompts**:
- "What learning theories support game-based learning? (Constructivism, experiential learning, situated learning)"
- "What evidence exists for the effectiveness of serious games in education?"
- "What design principles emerge from the literature?"
- "What are the criticisms or limitations of serious games in education?"
**Key synthesis question**: "What does the evidence say about when and why games work for learning?"

Show relevant sources:
```
python -m tools.manage_sources --action list --filters '{"relevance_tags": ["serious_games"]}'
```

#### 2.2.3 — Technology in Agricultural Education and Extension
**Purpose**: Review how technology has been used in agricultural education, especially in developing contexts.
**Prompts**:
- "What digital tools have been used for agricultural education in Southern Africa?"
- "What challenges exist for technology-based agricultural education in this context?"
- "How have mobile and ICT solutions been adopted by farmers and extension workers?"
**Key synthesis question**: "What works and what does not when using technology for agricultural education in developing regions?"

Show relevant sources:
```
python -m tools.manage_sources --action list --filters '{"relevance_tags": ["agricultural_education"]}'
```

#### 2.2.4 — Farmer-to-Farmer Knowledge Exchange and Peer Learning
**Purpose**: Review literature on peer-based knowledge sharing in agriculture, communities of practice, and how multiplayer/collaborative mechanics can support learning.
**Prompts**:
- "How do farmers traditionally share knowledge with each other in Southern Africa?"
- "What does the literature say about communities of practice in agriculture?"
- "How have digital platforms facilitated farmer-to-farmer knowledge exchange?"
- "What role does peer learning play in preserving indigenous knowledge?"
**Key synthesis question**: "What mechanisms for peer-based knowledge exchange exist, and how could multiplayer game mechanics replicate or enhance them?"

Show relevant sources:
```
python -m tools.manage_sources --action list --filters '{"relevance_tags": ["peer_learning"]}'
```

### Section 2.3 — Review of the Solution Domain
**Purpose**: Review existing serious games, simulations, and digital tools for agriculture and IK.
**Prompts**:
- "What existing serious games address agriculture? (FarmVille-style, simulation games, educational farming games)"
- "Have any games specifically addressed indigenous knowledge?"
- "What technologies and platforms are used? (Mobile, web, VR)"

### Section 2.4 — Existing Artefacts and Their Limitations
**Purpose**: Critical analysis of what current solutions lack.
**Prompts**:
- "For each existing artefact you reviewed, what are its strengths and weaknesses?"
- "Create a comparison table: Artefact | Focus | Platform | IK Integration | Multiplayer | Limitations"
- "What common gaps appear across all existing solutions?"

### Section 2.5 — Theoretical / Conceptual Framework
**Purpose**: Present the theoretical lens for your research.
**Prompts**:
- "What theories will guide your game design? (DSR, constructivism, experiential learning, community of practice)"
- "How do these theories connect to each other?"
- "Draw a conceptual framework diagram showing how the theories relate to your research question."

Generate a visual:
```
python -m tools.generate_visuals --type concept-map --input .tmp/framework-data.json --output data/chapters/visuals/conceptual-framework.png
```

### Section 2.6 — Identification of the Research Gap
**Purpose**: Synthesise sections 2.2–2.5 to articulate what is missing.
**Prompts**:
- "Based on everything you reviewed, what specific gap does your research fill?"
- "Why hasn't this gap been addressed before?"
- "How does your proposed artefact (the serious game) address this gap?"

### Section 2.7 — Conclusion
**Purpose**: Summarise the key themes, the gap, and transition to Chapter 3 (Methodology).

## Thematic Map Generation
After completing the thematic review, generate a visual showing literature themes and their relationships:
```
python -m tools.generate_visuals --type thematic-map --input .tmp/thematic-map-data.json --output data/chapters/visuals/thematic-map-ch2.png
```

## Quality Check
```
python -m tools.check_writing --input data/chapters/ch2-draft.md --output .tmp/writing-check-ch2.json
```

Review for:
- Americanisms
- Uncited claims (literature review should have very high citation density)
- Word count (Chapter 2 typically 8,000–15,000 words)
- Balance between themes (no single section dominating)

## Writing Tips for the User
- **Synthesise, don't summarise**: Group findings by theme, not by paper. "Several studies found that..." rather than "Smith (2020) found... Jones (2021) found..."
- **Be critical**: Identify strengths AND weaknesses of the literature
- **Show connections**: Link papers to each other and to your research question
- **Use signposting**: Start each section with what it covers, end with a transition to the next

## Critical Rule
Claude does NOT write prose. Claude guides the structure and checks quality. The user writes every sentence.
