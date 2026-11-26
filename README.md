# Scientific Writing Guardrail

An editorial toolkit for people turning AI-assisted research into prose that another person can read, translate and check. The first release supports technical English and Spanish. The editorial protocol does the rewriting with an editor or a model; a small offline Python program checks the agreed claims and protected expressions against a frozen source and renders each edition.

## Start with an example

Requires Python 3.9+ and its standard library. Run these commands from this repository.

```sh
python3 guardrail.py check examples/riemann/source.txt examples/riemann/packet.json
python3 guardrail.py render examples/riemann/source.txt examples/riemann/packet.json --language es --with-notes
python3 -m unittest discover -s tests -v
```

## Edit your own passage

1. Save a UTF-8 copy of the passage and any relevant primary evidence in a single local source file. Keep confidential manuscripts in the ignored `private/` folder or outside this repository. The sample is public mathematics.
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

For a review copy that will travel outside the project, add `--with-notes`. This includes claim markers, their evidence locators, the editorial assistance declaration and the packet hash. The default rendering is a local reading preview.

The check returns exit code **0** for a packet ready for human review, **1** for a detected mismatch, and **2** for invalid input. An unsupported assertion can retain every protected word. A claim may have been omitted when constructing the map. People must check those failures, citation support, mathematical implication, grammar, cohesion and audience comprehension. Every automated receipt leaves human review pending. The CLI itself performs no network calls.

## Evidence and first evaluation

The [Riemann case](docs/riemann-case.md) distinguishes a formally verified mathematical statement from the work of explaining its argument. The [research and evaluation plan](docs/evidence-and-evaluation.md) connects empirical findings to specific editing decisions and describes a small counterbalanced reader study with a scoring key. Initial scope is one passage at a time. Reader testing and evidence about transfer across disciplines remain open.
