# Reading a synthetic biodiversity inventory

A natural history editor wants to know what the ledger counts and whether it supports a species count. All counts and texts in this exercise were invented for teaching.

From the repository root, run:

```sh
python3 guardrail.py check examples/biodiversity/source.txt examples/biodiversity/packet.json
python3 guardrail.py render examples/biodiversity/source.txt examples/biodiversity/packet.json --language en --with-notes
python3 guardrail.py render examples/biodiversity/source.txt examples/biodiversity/packet.json --language es --with-notes
```

Both editions should explain that the ledger counts observations, some of which could describe the same organism. Species richness cannot be inferred. The check should return `ready_for_human_review`, an empty issue list and pending human review. The two claim IDs in the annotated copy let the editor look up their local records.

## Try two edits

Copy the packet to your own working directory; keep the original source. In the Spanish rendering of C1, replace “12” with “13”. Run the check against that copy. It should return exit code 1 and identify the missing Spanish expression for C1.

Starting from a fresh copy, exchange the positions of “12” and “3” in the same rendering. Both literals and their associated nouns are still present. The mechanical check passes although the scientific statement is wrong. Ask a reader how many plots were sampled and what each row represents. A reviewer comparing the answers with the source can locate the reversed relationship.

The regression tests exercise both edits. An annotated copy contains the edition itself. An editor should review that prose before sharing it.
