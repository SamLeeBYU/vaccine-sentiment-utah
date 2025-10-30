def get_prompts(framing: str):

    if framing == "health vs. economy":
        """
        A = Highlights public health consequences or solution
        B = Highlights economic consequences or solutions
        C = Presents both health and economic consequences equally
        D = Discussion is unrelated to health or economy
        """

        prompts = [
            (
            "You are coding media articles for their dominant framing motive.\n"
            "Return a single code from {{A,B,C,D}}.\n\n"
            "A = Highlights public health consequences or solutions\n"
            "B = Highlights economic consequences or solutions\n"
            "C = Presents both health and economic consequences equally\n"
            "D = Discussion is unrelated to health or economy\n\n"
            "Guidelines:\n"
            "- Determine which dimension—health or economy—anchors the author’s reasoning.\n"
            "- If focus is tangential or absent, choose D.\n\n"
            "=== PASSAGE ===\n"
            "{content}\n"
            "=== END PASSAGE ==="
            ),
            (
            "You are a discourse analyst evaluating framing in media writing.\n"
            "Classify the dominant focus of the author’s reasoning using one of {{A,B,C,D}}.\n\n"
            "A = Emphasizes health-related outcomes (disease prevention, wellbeing, medical systems)\n"
            "B = Emphasizes economic-related outcomes (employment, markets, financial recovery)\n"
            "C = Balances both health and economic outcomes\n"
            "D = Does not focus on health or economy\n\n"
            "Instructions:\n"
            "- Identify which type of consequence is central to the author’s argument.\n"
            "- If the passage discusses neither, select D.\n"
            "- Do not infer tone, sentiment, or accuracy.\n\n"
            "=== TEXT ===\n"
            "{content}\n"
            "=== END TEXT ==="
            ),

            (
            "You are performing content analysis of public communication.\n"
            "Decide which outcome domain the author prioritizes.\n"
            "Respond with a single label from {{A,B,C,D}}.\n\n"
            "A = Public health frame (focus on illness, mortality, or health protection)\n"
            "B = Economic frame (focus on productivity, business, or financial impact)\n"
            "C = Balanced frame (health and economic outcomes treated comparably)\n"
            "D = Frame unrelated to health or economy\n\n"
            "Guidelines:\n"
            "- Consider what the author presents as the primary reason for concern or action.\n"
            "- Ignore emotional language; focus strictly on topic emphasis.\n\n"
            "=== ARTICLE ===\n"
            "{content}\n"
            "=== END ARTICLE ==="
            ),

            (
            "You are an expert coder analyzing causal emphasis in journalism.\n"
            "Identify which type of consequence the author associates most strongly with the described issue.\n"
            "Return only one label from {{A,B,C,D}}.\n\n"
            "A = Health-oriented (prevention, treatment, wellbeing)\n"
            "B = Economic-oriented (growth, jobs, commerce)\n"
            "C = Balanced or equally weighted between health and economic aspects\n"
            "D = Unrelated or no discernible link to health or economy\n\n"
            "Rules:\n"
            "- Focus on causal claims (e.g., 'leads to fewer deaths' vs. 'leads to faster recovery').\n"
            "- If no causal emphasis appears, choose D.\n\n"
            "=== PASSAGE ===\n"
            "{content}\n"
            "=== END PASSAGE ==="
            ),
            (
            "You are coding written media for dominant interpretive framing.\n"
            "Select exactly one code from {{A,B,C,D}}.\n\n"
            "A = Health framing (author centers discussion on medical, psychological, or wellbeing outcomes)\n"
            "B = Economic framing (author centers discussion on financial, employment, or market outcomes)\n"
            "C = Mixed or balanced framing (both domains equally emphasized)\n"
            "D = Unrelated to health or economic topics\n\n"
            "Evaluation Principles:\n"
            "- Identify the thematic domain that structures the author’s argument.\n"
            "- If neither applies, mark D.\n"
            "- Avoid classifying tone, ideology, or accuracy.\n\n"
            "=== EXCERPT ===\n"
            "{content}\n"
            "=== END EXCERPT ==="
            )

        ]

    if framing == "scientific sentiment":
        prompts = [
            (
                # Variation A
                "You are an expert in science journalism analysis.\n"
                "Goal: Determine how the author characterizes scientific evidence about {topic}.\n"
                "Respond with exactly one letter from {A,B,C}.\n\n"
                "A = Depicts scientific evidence as credible and supportive of {topic}\n"
                "B = Suggests scientific evidence is unreliable, politicized, or flawed\n"
                "C = Presents evidence in a balanced or neutral manner\n\n"
                "Guidelines:\n"
                "- Evaluate the author's trust in the scientific process or consensus.\n"
                "- Disregard tone unrelated to science itself.\n\n"
                "=== TEXT ===\n"
                "{content}\n"
                "=== END ==="
            ),
            (
                # Variation B
                "Task: Assess the framing of scientific evidence in the following passage about {topic}.\n"
                "Return only one of {A,B,C}.\n\n"
                "Labels:\n"
                "A = Confidence in science or endorsement of its findings\n"
                "B = Skepticism toward science or claims of bias\n"
                "C = Objective reporting or description without judgment\n\n"
                "Consider only the author's treatment of scientific reliability, not emotions or policy positions.\n\n"
                "[START ARTICLE]\n"
                "{content}\n"
                "[END ARTICLE]"
            ),
            (
                # Variation C
                "You are evaluating the author’s stance toward scientific evidence concerning {topic}.\n"
                "Answer with a single label (A, B, or C).\n\n"
                "A: Evidence framed as trustworthy and conclusive\n"
                "B: Evidence framed as doubtful or manipulated\n"
                "C: Evidence framed neutrally, factually, or without stance\n\n"
                "Rule: Focus strictly on whether the author implies trust or distrust in science. Ignore other sentiment.\n\n"
                "--- BEGIN TEXT ---\n"
                "{content}\n"
                "--- END TEXT ---"
            ),
            (
                # Variation D
                "Classify the following article excerpt according to how it frames scientific findings about {topic}.\n"
                "Output only one character: A, B, or C.\n\n"
                "A - Science seen as reliable and validating {topic}\n"
                "B - Science questioned, minimized, or politicized\n"
                "C - Science presented neutrally without endorsement or criticism\n\n"
                "Important:\n"
                "- Evaluate framing of scientific evidence, not personal or emotional tone.\n"
                "- If unclear, choose the most neutral option (C).\n\n"
                "ARTICLE:\n"
                "{content}"
            ),
            (
                # Variation E
                "Instruction: Judge the author's trust in scientific evidence about {topic}.\n"
                "Give one code (A/B/C) only.\n\n"
                "A = Author conveys confidence in science supporting {topic}\n"
                "B = Author expresses distrust or implies bias in science\n"
                "C = Author reports or describes science without evaluation\n\n"
                "Criteria:\n"
                "- Examine verbs and adjectives describing scientists or studies.\n"
                "- Ignore unrelated opinions or emotion.\n\n"
                "TEXT BELOW\n"
                "{content}\n"
                "TEXT ABOVE"
            ),
            (
                # Variation F
                "You are a discourse analyst measuring epistemic trust.\n"
                "Read the passage about {topic} and classify the stance toward scientific evidence.\n\n"
                "Options:\n"
                "A → Science portrayed as dependable and backing {topic}\n"
                "B → Science portrayed as suspect, corrupted, or unreliable\n"
                "C → Science mentioned factually without endorsement or rejection\n\n"
                "Return one uppercase letter (A, B, or C) only.\n\n"
                "=== BEGIN ARTICLE ===\n"
                "{content}\n"
                "=== END ARTICLE ==="
            ),
            (
                # Variation G
                "You are reviewing an article for how it portrays scientific findings about {topic}.\n"
                "Select one option from {A,B,C}.\n\n"
                "A = The author affirms or relies on scientific evidence to support {topic}\n"
                "B = The author questions, downplays, or challenges the credibility of science\n"
                "C = The author describes science factually without signaling trust or doubt\n\n"
                "Guidance:\n"
                "- Identify whether the tone implies endorsement or skepticism of science.\n"
                "- Do not infer sentiment beyond how scientific evidence is treated.\n\n"
                "=== ARTICLE START ===\n"
                "{content}\n"
                "=== ARTICLE END ==="
            ),
            (
                # Variation H
                "Analyze the following passage to classify its depiction of scientific evidence regarding {topic}.\n"
                "Respond with exactly one letter: A, B, or C.\n\n"
                "A. Portrays science as trustworthy, credible, and aligned with {topic}\n"
                "B. Portrays science as flawed, manipulated, or biased\n"
                "C. Portrays science impartially, simply stating findings or facts\n\n"
                "Instructions:\n"
                "- Focus only on how the author positions science as an epistemic authority.\n"
                "- Ignore emotional language or unrelated political commentary.\n\n"
                "--- TEXT BEGINS ---\n"
                "{content}\n"
                "--- TEXT ENDS ---"
            )
        ]

    return prompts
