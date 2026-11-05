"""Build the manually delimited Kuhn sections 17--18 research shard.

The source registry supplies exact page/reference metadata.  Selection,
paraphrased scope, record kind, evidence boundary, and open questions below are
human-authored so running this script cannot promote arbitrary crawl results.
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any


APP_DIR = Path(__file__).resolve().parents[1]
REGISTRY = APP_DIR / "data" / "discovery-closer-to-truth.json"
OUTPUT = APP_DIR / "data" / "catalog-2026-08-30-anomalous-challenge.json"
KUHN_URL = "https://doi.org/10.1016/j.pbiomolbio.2023.12.003"


SELECTION: dict[str, dict[str, Any]] = {
    "combs-s-chaotic-attractor-and-autopoietic-systems": {
        "kind": "Model or framework",
        "summary": "Conscious states are modeled as self-organizing, dynamically stable patterns near the edge of chaos, with transitions between states treated as changes among attractor regimes.",
        "boundary": "This is a nonlinear-dynamics framing of conscious-state organization, not evidence that a specific chaotic variable is necessary or sufficient for phenomenal experience.",
        "standing": "Conceptual and dynamical-systems proposal; neural operationalization remains limited.",
        "questions": ["Which measurable state variables define the proposed attractors?", "What result would distinguish this account from generic brain-state dynamics?"],
    },
    "dops-s-consciousness-research-and-theory": {
        "kind": "Model or framework",
        "summary": "The University of Virginia DOPS research program treats reports of survival, reincarnation, near-death experience, and related phenomena as a joint evidential challenge to brain-production accounts of mind.",
        "boundary": "DOPS is a research program and family of interpretations, not one mechanistic theory; cataloging it does not validate survival or psi claims.",
        "standing": "Long-running but highly contested anomalous-experience research program.",
        "questions": ["Which claims survive prospective, blinded, and independently replicated designs?", "What positive mechanism links the heterogeneous phenomena in the program?"],
    },
    "graboi-s-three-aspect-model": {
        "kind": "Philosophical position",
        "summary": "The proposal distinguishes physical, nonconscious mental, and conscious aspects while treating them as coordinated expressions within a broader ontology.",
        "boundary": "This named three-aspect proposal is kept separate from Pereira's triple-aspect monism and generic dual-aspect theories; its independent scholarly footprint is small.",
        "standing": "Speculative metaphysical proposal with sparse independent assessment.",
        "questions": ["What individuates the three aspects without turning them into substances?", "Does the model yield empirical consequences beyond other aspect monisms?"],
    },
    "grinberg-s-syntergic-neuronal-field-theory": {
        "kind": "Model or framework",
        "summary": "Syntergic theory proposes that neural activity transforms or interacts with an informational lattice to generate experienced reality, combining neurophysiological and field-like claims.",
        "boundary": "The neural-field and lattice claims are not established by standard neuroscience; controversial transferred-potential reports do not by themselves verify the full theory.",
        "standing": "Historically documented, non-mainstream field proposal with disputed evidence.",
        "questions": ["Can the lattice construct be independently operationalized?", "Can preregistered replications separate ordinary coupling and artifact from the proposed interaction?"],
    },
    "harp-s-universal-or-god-consciousness": {
        "kind": "Philosophical position",
        "summary": "The account places individual consciousness within or in relation to a universal divine consciousness and uses that ontology to interpret finite minds.",
        "boundary": "This is a theological-metaphysical proposal, not a neuroscientific model or an empirically confirmed cosmology.",
        "standing": "Speculative theological position with limited independent literature.",
        "questions": ["How is individual subjectivity individuated within universal consciousness?", "What would count against the proposed universal-consciousness ontology?"],
    },
    "hiller-s-eternal-discarnate-consciousness": {
        "kind": "Philosophical position",
        "summary": "The proposal treats consciousness as fundamentally nonphysical and capable of existing independently of embodied brains, with embodiment constraining rather than producing it.",
        "boundary": "Claims of discarnate persistence are metaphysical and remain unsupported by a generally accepted evidential protocol.",
        "standing": "Non-mainstream survival-oriented metaphysics.",
        "questions": ["What establishes personal continuity without neural realization?", "Which observation would discriminate discarnate consciousness from brain-dependent alternatives?"],
    },
    "josephson-s-psi-informed-models": {
        "kind": "Model or framework",
        "summary": "Josephson explores whether physics must be extended to accommodate mind, biological organization, and reported psi phenomena, using quantum and complex-systems ideas as conceptual resources.",
        "boundary": "A Nobel Prize in condensed-matter physics does not confer empirical support on these later consciousness and psi proposals; quantum terminology is not itself a mechanism.",
        "standing": "Physics-inspired speculative program outside mainstream consciousness science.",
        "questions": ["Can the proposal specify a quantitative interaction law?", "Are any psi-linked predictions robust under independent high-powered replication?"],
    },
    "jung-s-collective-unconscious-and-synchronicity": {
        "kind": "Historical tradition",
        "summary": "Jungian psychology posits inherited archetypal structures in a collective unconscious and uses synchronicity to describe meaningful acausal correspondences between psychic and external events.",
        "boundary": "The collective unconscious is a depth-psychology construct; synchronicity is not an accepted causal mechanism in contemporary psychology or physics.",
        "standing": "Historically influential interpretive framework with contested empirical status.",
        "questions": ["Can archetypal regularities be separated from cultural transmission and interpretive flexibility?", "Can synchronicity generate prospective predictions rather than retrospective meaning?"],
    },
    "radin-s-challenge-to-materialism": {
        "kind": "Argument / challenge",
        "summary": "Radin argues that experimental parapsychology and anomalous experience undermine strictly brain-bound materialist accounts of consciousness.",
        "boundary": "This is an evidential challenge, not a positive theory of consciousness; the underlying meta-analytic methods and claimed effects remain disputed.",
        "standing": "Contested parapsychological argument against materialism.",
        "questions": ["Do claimed effects persist under adversarial collaboration and preregistration?", "Even if an anomaly were established, which ontology would it favor?"],
    },
    "sheldrake-s-morphic-fields": {
        "kind": "Model or framework",
        "summary": "Morphic-resonance theory proposes that self-organizing systems inherit form and behavioral tendencies through nonlocal similarities to prior systems rather than through ordinary local causes alone.",
        "boundary": "Morphic fields are not accepted biological fields, and the proposal should not be conflated with developmental morphogen gradients or standard learning effects.",
        "standing": "Well-known but non-mainstream and frequently criticized hypothesis.",
        "questions": ["Can morphic resonance be isolated from genetic, environmental, and publication effects?", "What physical or informational quantity carries the proposed influence?"],
    },
    "swimme-s-cosmogenesis": {
        "kind": "Philosophical position",
        "summary": "Cosmogenesis presents consciousness and value within an evolving-universe narrative in which cosmological, biological, and cultural creativity form a continuous developmental story.",
        "boundary": "This is a synthetic cosmological philosophy and spiritual narrative, not a discriminating scientific theory of phenomenal consciousness.",
        "standing": "Interpretive evolutionary-cosmology framework.",
        "questions": ["Which claims are metaphorical, theological, or empirically testable?", "How does the narrative explain subjectivity rather than situate it historically?"],
    },
    "campbell-s-theory-of-everything": {
        "kind": "Model or framework",
        "summary": "Campbell's model treats physical reality as a virtual information environment embedded in a larger consciousness system whose evolution is described in information-processing terms.",
        "boundary": "This self-authored virtual-reality cosmology is not established by computer science or physics and is distinct from simulation arguments that do not posit primordial consciousness.",
        "standing": "Non-mainstream informational metaphysics.",
        "questions": ["What formal dynamics govern the larger consciousness system?", "Which observation uniquely favors this model over other simulation or idealist accounts?"],
    },
    "tart-s-emergent-interactionism": {
        "kind": "Philosophical position",
        "summary": "Tart's pragmatic dualism proposes consciousness as a system property emerging from interaction between brain-body processes and a distinct mental or life system, with psi assigned an interaction role.",
        "boundary": "The account depends on controversial psi claims and differs from ordinary emergent physicalism because one interacting system is explicitly nonphysical.",
        "standing": "Historically documented, non-mainstream interactionist proposal.",
        "questions": ["How are the physical and mental-life systems individuated and coupled?", "Can auto-psi and allo-psi be operationalized without circular appeal to anomalies?"],
    },
    "wilber-s-integral-theory": {
        "kind": "Model or framework",
        "summary": "Integral theory organizes subjective, behavioral, cultural, and social perspectives together with developmental levels, states, and types in a broad map of consciousness and human development.",
        "boundary": "It is a synthetic metatheory and classificatory framework, not one neural mechanism or a single experimentally adjudicable theory of phenomenal consciousness.",
        "standing": "Influential in transpersonal and integral communities; limited uptake in mainstream experimental science.",
        "questions": ["Which components have independent operational definitions and validation?", "How should incompatible source traditions be integrated without erasing their differences?"],
    },
    "bitbol-s-phenomenological-ontology": {
        "kind": "Philosophical position",
        "summary": "Bitbol uses a radical phenomenological stance to suspend objectivist assumptions and examine whether consciousness is a condition for articulating ontology rather than another object within it.",
        "boundary": "This is an epistemic and phenomenological interpretation, not a claim that altered-state reports directly prove a new physical entity.",
        "standing": "Contemporary phenomenological philosophy with interpretive, not mechanistic, aims.",
        "questions": ["How does methodological suspension constrain positive ontological claims?", "Can the stance guide empirical comparison without presupposing objectivism?"],
    },
    "nagel-s-mind-and-cosmos": {
        "kind": "Argument / challenge",
        "summary": "Nagel argues that reductive materialist naturalism has not adequately explained consciousness, cognition, and value and considers teleological or otherwise expanded naturalistic alternatives.",
        "boundary": "The argument challenges explanatory sufficiency; it does not supply a worked neural theory or establish any specific nonmaterialist ontology.",
        "standing": "Prominent and controversial philosophical critique of reductive naturalism.",
        "questions": ["Can a nonintentional teleology be made scientifically precise?", "Which expanded naturalism best explains consciousness without explanatory regress?"],
    },
    "eagleman-s-possibilianism": {
        "kind": "Argument / challenge",
        "summary": "Possibilianism recommends holding multiple live metaphysical possibilities open when current evidence underdetermines questions about mind, reality, and existence.",
        "boundary": "This is an epistemic attitude toward uncertainty, not a substantive theory of consciousness.",
        "standing": "Public-facing methodological stance rather than a research theory.",
        "questions": ["What evidential thresholds move a possibility into or out of serious consideration?", "How does the stance avoid treating poorly supported options as evidential peers?"],
    },
    "tallis-s-anti-neuromania-skepticism": {
        "kind": "Argument / challenge",
        "summary": "Tallis argues that neural descriptions are routinely overextended into explanations of consciousness, agency, culture, and personhood that they do not yet provide.",
        "boundary": "The critique targets explanatory overreach; it does not deny neural dependence or itself constitute a positive consciousness mechanism.",
        "standing": "Philosophical critique of reductionist explanatory claims.",
        "questions": ["Which bridge principles would make neural explanations genuinely constitutive?", "Where is the boundary between useful neural explanation and category error?"],
    },
    "nagasawa-s-mind-body-problem-in-an-infinitely-decomposable-universe": {
        "kind": "Argument / challenge",
        "summary": "Nagasawa asks whether endless physical decomposability blocks any final microphysical level from grounding a complete reductive explanation of consciousness.",
        "boundary": "This is a conditional metaphysical challenge based on infinite decomposition, not empirical evidence that the physical world is infinitely decomposable.",
        "standing": "Analytic philosophical challenge to bottom-up reduction.",
        "questions": ["Does reduction require a fundamental physical level?", "Would grounding or structural explanation survive infinite decomposition?"],
    },
    "musser-s-is-it-really-so-hard": {
        "kind": "Argument / challenge",
        "summary": "Musser examines whether relational, predictive, and self-modeling approaches can reframe why consciousness appears uniquely difficult rather than treating the hard problem as methodologically isolated.",
        "boundary": "This is a comparative synthesis and challenge framing, not one independently specified theory.",
        "standing": "Science-synthesis perspective requiring theory-by-theory evaluation.",
        "questions": ["Which reframings make novel predictions rather than rename the explanatory gap?", "Can relational accounts explain phenomenal character as well as access and report?"],
    },
    "davies-s-consciousness-in-the-cosmos": {
        "kind": "Argument / challenge",
        "summary": "Davies situates consciousness within questions about information, biological organization, cosmology, and whether current physics exhausts the principles needed to explain observers.",
        "boundary": "The cosmological framing does not establish that consciousness is fundamental or that information alone is conscious.",
        "standing": "Speculative physics-informed challenge and research question.",
        "questions": ["What additional principle links information processing to subjectivity?", "Can cosmological claims produce observations unavailable to biological theories?"],
    },
    "s-harris-s-mystery-of-consciousness": {
        "kind": "Argument / challenge",
        "summary": "Harris emphasizes that correlations between brain activity and experience leave unresolved why physical processing is accompanied by first-person consciousness at all.",
        "boundary": "This restates an explanatory challenge and contemplative motivation; it is not a distinct mechanism and should not be merged with Harris's other positions.",
        "standing": "Public philosophical formulation of the explanatory mystery.",
        "questions": ["Does the formulation differ substantively from the hard problem or explanatory gap?", "What evidence could discriminate its favored interpretations?"],
    },
}


def year_from(value: str) -> int | str:
    match = re.search(r"(?:19|20)\d{2}", value)
    return int(match.group()) if match else "n.d."


def write_atomic(payload: dict[str, Any]) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=OUTPUT.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(OUTPUT)


def main() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    by_slug = {entry["slug"]: entry for entry in registry["entries"]}
    missing = sorted(set(SELECTION) - by_slug.keys())
    if missing:
        raise RuntimeError(f"Discovery entries missing: {', '.join(missing)}")

    records: list[dict[str, Any]] = []
    for ordinal, (slug, profile) in enumerate(SELECTION.items(), start=1):
        source = by_slug[slug]
        proponents = [item["name"] for item in source.get("proponents", []) if item.get("name")]
        source_year = year_from(str(source.get("modified_at", "")))
        citations = [
            {
                "title": source["name"],
                "authors": "Closer To Truth, Landscape of Consciousness",
                "year": source_year,
                "url": source["url"],
                "venue": "Landscape of Consciousness",
                "authority": "authoritative-secondary",
                "verification": "human-verified",
                "retrieved": "2026-08-30",
                "note": "Exact named-theory profile and retained reference trail.",
            },
            {
                "title": "A Landscape of Consciousness: Toward a Taxonomy of Explanations and Implications",
                "authors": "Robert Lawrence Kuhn",
                "year": 2024,
                "url": KUHN_URL,
                "doi": "10.1016/j.pbiomolbio.2023.12.003",
                "venue": "Progress in Biophysics and Molecular Biology",
                "authority": "authoritative-secondary",
                "verification": "doi-resolved",
                "retrieved": "2026-08-30",
                "note": "Inclusive landscape source; inclusion is not endorsement.",
            },
        ]
        direct_reference = next(
            (
                (reference, locator)
                for reference in source.get("references", [])
                for locator in reference.get("locators", [])
                if locator.startswith("https://")
                and "scholar.google" not in locator
                and "lumignosis.org" not in locator
                and ", https://" not in locator
                and locator not in {source["url"], KUHN_URL}
            ),
            None,
        )
        if direct_reference:
            reference, locator = direct_reference
            citations.append(
                {
                    "title": reference.get("title") or reference.get("label") or "Referenced work",
                    "authors": reference.get("authors") or "Authorship recorded in source frame",
                    "year": year_from(str(reference.get("label", ""))),
                    "url": locator,
                    "venue": reference.get("container") or "Source-frame reference",
                    "authority": "referenced-source-locator",
                    "verification": "locator-recorded",
                    "retrieved": "2026-08-30",
                }
            )

        records.append(
            {
                "id": f"kac-{ordinal:03d}-{slug}",
                "name": source["name"],
                "aliases": [],
                "kind": profile["kind"],
                "domain": "Anomalous and altered-state proposals" if source["category"] == "Anomalous & Altered States" else "Meta-theoretical challenges",
                "tradition": source["category"],
                "status": "documented · contested · non-consensus",
                "status_note": "Included for landscape coverage; inclusion is not evidential endorsement.",
                "summary": profile["summary"],
                "proponents": proponents or ["Attribution retained in source frame"],
                "era": "20th–21st century",
                "scope": "Kuhn landscape sections 17–18 and dedicated source profile",
                "claim_scope": {"Core scope": profile["summary"]},
                "boundary_note": profile["boundary"],
                "evidence_profile": {
                    "Current standing": profile["standing"],
                    "Collection basis": "Named in Kuhn's inclusive taxonomy and retained in a dedicated Closer To Truth source profile.",
                    "Review limit": "This pass establishes identity, attribution, scope, and locators; it does not adjudicate truth, replication, or evidential weight.",
                },
                "open_questions": profile["questions"],
                "keywords": [source["category"], "Kuhn landscape", "non-consensus proposal"],
                "citations": citations,
                "review_state": "provisional",
            }
        )

    payload = {
        "collection": {
            "name": "Kuhn sections 17–18: anomalous proposals and explanatory challenges",
            "date": "2026-08-30",
            "record_count": len(records),
            "source_frames": [KUHN_URL, "https://loc.closertotruth.com/theory"],
            "method": "Manual identity and boundary selection from the reproducible Closer To Truth discovery registry; source descriptions were paraphrased and all entries retain exact frame locators.",
            "phase_policy": "Collection only; no conceptual relationship edges or synthesis claims.",
        },
        "records": records,
    }
    write_atomic(payload)
    print(f"Wrote {len(records)} records to {OUTPUT}")


if __name__ == "__main__":
    main()
