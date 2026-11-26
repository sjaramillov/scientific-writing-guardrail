# Can readers follow the argument and recover its limits?

An editorial revision succeeds when the intended reader can explain what the work establishes, how the authors reached it, and where it stops. That requires evidence about the reader as well as the manuscript. The studies below motivate the proposed evaluation. This project has yet to collect reader outcomes.

## What the evidence supports

| Finding | Consequence for the guardrail |
| --- | --- |
| Guo and colleagues recruited 150 online participants to assess biomedical plain-language summaries. Readers gave human and model-written summaries similar clarity and coherence ratings, yet answered comprehension questions more accurately after human-written summaries. This was an English-language crowdsourced task in a particular domain. [Guo et al., 2026](https://doi.org/10.1016/j.jbi.2026.105038) | Ask readers to recover the method and a boundary on the conclusion. Record their answers independently of their ratings of the prose. |
| Peters and Chin-Yee examined 4,900 summaries produced by ten models. In their comparison with human-authored science summaries, the odds ratio for broad generalizations was 4.85 (95% CI 3.06–7.70). The estimate concerns the models, prompts, source materials and definition of generalization used in that study. [Peters and Chin-Yee, 2025](https://doi.org/10.1098/rsos.241776) | For each central claim, record its population or mathematical domain, assumptions, quantifier, strength of evidence and exceptions. Check these again after editing or translation. |
| Walters and Wilder checked 636 references from 84 model-generated literature reviews on 42 topics. In that 2023 experiment, 55% of the references from GPT-3.5 and 18% from GPT-4 were fabricated. Some references to real works also contained bibliographic errors. The experiment did not estimate the error rate of later models. [Walters and Wilder, 2023](https://doi.org/10.1038/s41598-023-41032-5) | Check the work’s identity against the publisher or repository. Then inspect the cited passage for support of the specific claim. A resolving DOI establishes neither entailment nor independent replication. |
| Ramírez-Castañeda surveyed 49 Spanish-speaking Colombian doctoral students and doctorate holders in biological sciences about publishing in English. Respondents reported difficulties with reading, writing and the time writing took. These are self-reported experiences from a small sample. The study did not evaluate an AI intervention. [Ramírez-Castañeda, 2020](https://doi.org/10.1371/journal.pone.0238372) | Preserve the source language alongside the revision. Trace technical terms and qualifiers across languages and recruit readers who actually use the target language. |

Record editorial assistance as the work proceeds: tool and version when known, date, affected passages, purpose, and who checked them. At submission, consult the target journal’s current instructions. For example, biodiversity publisher Pensoft requires authors to declare AI use at submission. This is a publisher policy rather than an empirical result. [Pensoft editorial policies, Responsibility of Authors](https://pensoft.net/editorial-policies)

## A first reader study

**Prepare the materials.** Choose two independent passages (A and B) of similar length, difficulty and genre. Preserve each original and its revision under versioned identifiers. Use one audience and language per comparison. To evaluate a Spanish-to-English edition, compare the revised English with a technically checked English baseline, and separately have a bilingual specialist check both against the Spanish source. Comparing Spanish with English would confound editing with language proficiency.

**Audit scientific fidelity first.** A domain reviewer matches each central claim to a passage in the source and, where applicable, to supporting evidence. Check quantities and units, provenance, qualifiers, inference steps, terminology, citations and uncertainty. Record each item as supported, changed, omitted, or unresolved, with a locator and reason. A changed denominator, reversed negation, missing hypothesis or unsupported conclusion returns the passage for correction. A second specialist adjudicates disputed items. A receipt for this check identifies the exact revision. It does not certify the underlying research.

**Counterbalance the readings.** An initial feasibility pilot could use eight target readers, two in each sequence. Use the four sequences below so each passage and each version appears equally often in both positions. Each participant sees a given passage once. Mask version labels, keep questions and reading conditions identical across versions of a passage, and give no feedback between passages.

| Sequence | First reading | Second reading |
| --- | --- | --- |
| 1 | A original | B revised |
| 2 | B revised | A original |
| 3 | A revised | B original |
| 4 | B original | A revised |

**Score understanding and editorial quality separately.** Before recruiting, a specialist writes four passage-specific questions and an answer key covering the finding, the method or decisive inference, a required assumption, and a conclusion the evidence leaves open. Readers answer in their own words with the text available. Two raters score responses blind to version (0 incorrect, 1 partly supported, 2 complete), retain disagreements and record their resolution. Separately, ask readers to mark an ambiguous referent, unfamiliar term or missing transition and rate ease of following the argument. A language editor records specific grammar and cohesion changes. Retain reading time as a descriptive measure.

**Report and decide.** Report signed-off, missing and disputed claims as counts with denominators. For comprehension, report scores by passage, sequence and version, the number of readers and unanswered items, and recurrent misreadings. A score from 0 to 8 describes one reader’s responses to one passage. The two readings by a participant are paired observations. This small design screens for failures and feasibility. It cannot establish a general improvement, long-term retention or formal correctness of a proof.

| Observation | Editorial decision |
| --- | --- |
| Unsupported claim, changed premise, or material citation mismatch | Return the passage to the author with source and locator. Fix and repeat the fidelity check before a reader trial. |
| Scientific content preserved, but readers repeatedly miss a key assumption or inference | Revise the relevant explanation and retest it with fresh readers. Preserve the technical statement. |
| Fidelity documented and pilot readers can reconstruct the intended result and limits | A named editor may approve the tested version for that audience. Report the actual scores, disagreements and remaining limitations. |
| Review or readers unavailable | Mark the corresponding evaluation pending. An automatic check can report only what it inspected. |
