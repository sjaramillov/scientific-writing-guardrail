# Scientific Writing Guardrail

Scientific Writing Guardrail helps an editor trace a scientific passage across English and Spanish. The editor records the claims, marks expressions to preserve and writes each edition. The offline Python checker compares the declared passages and expressions against the frozen source and renders the text for a reviewer. Version 0.1.0 is an experimental, passage-level release.

## Start with an example

Requires Python 3.9+ and its standard library. Run these commands from this repository.

```sh
python3 guardrail.py check examples/biodiversity/source.txt examples/biodiversity/packet.json
python3 guardrail.py render examples/biodiversity/source.txt examples/biodiversity/packet.json --language es --with-notes
python3 -m unittest discover -s tests -v
```

In the [synthetic biodiversity exercise](examples/biodiversity/README.md), change one count and then swap the two counts between their referents. The first change triggers a mismatch. The second can pass the literal check and gives the reader a scientifically different result. A [mathematics example](examples/riemann/) explores how to attribute a formally verified result.

## Edit your own passage

1. Save a UTF-8 copy of the passage and any relevant primary evidence in a single local source file. Keep confidential manuscripts in the ignored `private/` folder or outside this repository.
2. Generate a blank packet. This first command emits a template. Supply the reader, intended task, assistance record, claims, source locators, and both edited texts before running the checks. A new source version requires a deliberate review of the packet.
3. Apply the [editing protocol](docs/editing-protocol.md) in Codex or with a human editor. Give every claim an exact source passage and an evidence locator. Write an idiomatic full passage for each audience. Each rendering must cover the complete claim map; the ordering can follow the language.
4. Check the packet, produce each draft and keep the receipt with it. The receipt binds the input bytes and packet by SHA-256. Changed files have to be checked again. Ask a domain reviewer to compare the reasoning and a representative reader to explain the result and its limits.

```sh
mkdir -p private
# Place your excerpt at private/source.txt first. Use new output names for each revision.
python3 guardrail.py prepare private/source.txt > private/draft-v1.json
# Complete the packet before the following commands.
python3 guardrail.py check private/source.txt private/draft-v1.json > private/receipt-v1.json
python3 guardrail.py render private/source.txt private/draft-v1.json --language en
```

### What to put in the packet

- **Audience and assistance.** Describe who must understand the passage and what they need to do; record the tool, editorial task and date. Set the claim status to one of `observed`, `reported`, `formal`, `interpretation`, `planned` or `limitation`.
- **Evidence and quote.** Give the primary document, version and section, or the artifact and run ID. Copy an exact passage from the local source bundle. A locator is a pointer that the reviewer follows; the CLI does not fetch or authenticate a reference.
- **Anchors.** For each quantity, qualifier, symbol or term to protect, give a literal source expression and its expected wording in English and Spanish. Set `"invariant": true` for expressions that must be identical in every version. Two purely numeric literals must match exactly. For a change from numerals to words, record and review the equivalence explicitly.
- **Versions.** Give every claim exactly one text segment per language. A segment can contain multiple sentences. Consecutive segments form a continuous paragraph. Set `"new_paragraph": true` on a segment to start a paragraph. Exact matches preserve case and normalize NFC and whitespace for anchors. The source quotation itself remains verbatim.

### Share a review copy

Use `render --language en --with-notes` (or `es`) for an annotated reading copy. It includes the selected edition, claim IDs, the declared evidence status, a packet fingerprint and a brief pointer to the editor’s assistance record. Full evidence locators, source quotations, audience details and the free-text assistance record stay in the local packet. Existing version 1 packets use the same defaults.

To share a citation, put a **bare DOI that you intend to disclose** in that claim's optional `public_doi` field. The CLI checks its format and prints a doi.org link. Confirm the DOI is publicly appropriate, resolves to the intended work and supports this statement. The draft body is exported as written. Read it before sharing, including citations or identifying details an author put into the prose. Keep source files, packets and receipts with the editor. Record any assistance disclosure required by the journal in the text prepared for submission.

### Read a check receipt

| Receipt or check | What it tells the reviewer |
| --- | --- |
| SHA-256 fingerprints | Which source and packet bytes were supplied, and whether the source matched the digest declared in the packet. |
| Structure and coverage | Exactly one segment per declared claim in each edition, known statuses and valid required fields. A claim omitted from the original map still needs an editor to find it. |
| Quotations and anchors | The supplied quotation occurs in the source. Declared expressions appear in the specified passage and edition. Invariant expressions and pairs of recognized numeric literals are compared literally. |
| Review state | `ready_for_human_review` means the implemented checks passed. The receipt records the checker version, its scope and outstanding assessments. Evidence status is the editor's declaration. A reviewer must judge whether a citation supports the claim, the two passages mean the same thing and a reader can follow the inference. |

Exit codes are **0** for a checked packet ready for review, **1** for a mismatch, and **2** for invalid input. The CLI runs locally using the Python standard library.

## Evidence and first evaluation

The [Riemann case](docs/riemann-case.md) distinguishes a formally verified mathematical statement from the work of explaining its argument. The [research and evaluation plan](docs/evidence-and-evaluation.md) connects empirical findings to specific editing decisions and describes a small counterbalanced reader study with a scoring key. Initial scope is one passage at a time. Reader testing and evidence about transfer across disciplines remain open.


## Prior work, citation and license

The [related work review](docs/related-work.md) compares five tools and three research or design antecedents, with links to the versions examined. Cite this software using [CITATION.cff](CITATION.cff).

The software, original documentation and original teaching examples in this distribution are licensed under the [Apache License, Version 2.0](LICENSE). Works cited by the examples retain their own terms. Authors retain the rights they hold in manuscripts, data and review notes they process with the tool.
