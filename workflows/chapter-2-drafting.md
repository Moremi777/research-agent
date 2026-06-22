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

#### 2.2.1 — Indigenous Farming Knowledge
**Purpose**: Review IK systems in agriculture — their importance, how they are defined, current state, and threats to preservation.
**Prompts**:
- "What do researchers say about the value of indigenous farming knowledge?"
- "How do different authors define and categorise IK in agriculture?"
- "What are the threats to IK preservation, especially in Southern Africa?"
- "Where do authors agree? Where do they disagree?"
**Key synthesis question**: "What does the literature collectively tell us about the state of indigenous farming knowledge?"

Show relevant sources:
```
python -m tools.manage_sources --action list --filters '{"relevance_tags": ["indigenous_knowledge"]}'
```

#### 2.2.2 — Sustainable Agriculture
**Purpose**: Review literature on sustainable farming practices, food security, and how sustainability relates to both IK and modern science.
**Prompts**:
- "How is sustainable agriculture defined in the literature?"
- "What role does indigenous farming knowledge play in sustainability?"
- "What are the key challenges to achieving sustainable agriculture in Southern Africa?"
- "How do sustainability goals connect to farming education?"
**Key synthesis question**: "How does the literature position indigenous knowledge within the broader sustainability agenda?"

Show relevant sources:
```
python -m tools.manage_sources --action list --filters '{"relevance_tags": ["sustainable_agriculture"]}'
```

#### 2.2.3 — Modern Agricultural Science
**Purpose**: Review how modern agricultural science complements or conflicts with indigenous farming knowledge, and how integration can work.
**Prompts**:
- "What does modern agricultural science offer that IK does not, and vice versa?"
- "What examples exist of successfully integrating IK with modern agricultural science?"
- "What tensions or challenges arise when combining these two knowledge systems?"
- "How has technology (IoT, precision farming, extension services) changed agriculture?"
**Key synthesis question**: "What does the evidence say about integrating indigenous and modern agricultural knowledge for better outcomes?"

Show relevant sources:
```
python -m tools.manage_sources --action list --filters '{"relevance_tags": ["modern_ag_science"]}'
```

### Section 2.3 — Thematic Review of the Solution Domain

#### 2.3.1 — Serious Games
**Purpose**: Review how serious games have been used for education, learning theories that underpin them, and their application in agriculture.
**Prompts**:
- "What learning theories support game-based learning? (Constructivism, experiential learning, situated learning)"
- "What evidence exists for the effectiveness of serious games in education?"
- "What existing serious games address agriculture or farming?"
- "What design principles emerge from the literature?"
**Key synthesis question**: "What does the evidence say about when and why serious games work for learning?"

Show relevant sources:
```
python -m tools.manage_sources --action list --filters '{"relevance_tags": ["serious_games"]}'
```

#### 2.3.2 — Multiplayer and Simulations
**Purpose**: Review multiplayer game mechanics, farming simulations, peer-based learning through games, and farmer-to-farmer knowledge exchange.
**Prompts**:
- "How have multiplayer mechanics been used in educational games?"
- "What agricultural simulation games exist and what do they simulate?"
- "How do farmers traditionally share knowledge with each other?"
- "What role does peer learning and collaborative play have in knowledge transfer?"
**Key synthesis question**: "How can multiplayer and simulation mechanics facilitate the transfer of farming knowledge between players?"

Show relevant sources:
```
python -m tools.manage_sources --action list --filters '{"relevance_tags": ["multiplayer_simulations"]}'
```

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
