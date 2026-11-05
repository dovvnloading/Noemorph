"""Apply human-approved Closer to Truth profile matches to base records.

Only the explicit mapping below is eligible.  Fuzzy discovery matches are never
written automatically.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1]
CATALOG = APP_DIR / "data" / "catalog.json"
REGISTRY = APP_DIR / "data" / "discovery-closer-to-truth.json"


PROFILES = {
    "seed-035-first-order-representationalism": {
        "slug": "carruthers-first-order-representationalism",
        "boundary": "First-order representationalism makes first-order content sufficient for conscious experience; it is not a higher-order monitoring theory and does not by itself settle whether representation explains qualitative character.",
        "questions": ["What makes one first-order representation conscious while another remains unconscious?", "Can the account explain absent, inverted, or misrepresented qualitative character without adding higher-order structure?"],
    },
    "seed-021-cosmopsychism": {
        "slug": "cosmopsychism",
        "boundary": "Cosmopsychism makes cosmic consciousness fundamental and must not be collapsed into micropsychist panpsychism, theism, or the claim that the universe has a human-like mind.",
        "questions": ["How do bounded individual subjects derive from or relate to the cosmic subject?", "What empirically or explanatorily distinguishes cosmopsychism from other priority monisms?"],
    },
    "seed-050-dendritic-integration-theory-dit": {
        "slug": "dendritic-integration-theory",
        "boundary": "DIT assigns a specific role to apical dendritic integration; evidence that anesthesia or state changes affect dendrites is not yet proof that this process is sufficient for phenomenal consciousness.",
        "questions": ["Is apical integration necessary across conscious modalities, species, and altered states?", "Which intervention would distinguish DIT from recurrent-processing and global-broadcast accounts?"],
    },
    "seed-062-free-energy-principle-active-inference": {
        "slug": "friston-s-free-energy-principle-and-active-inference",
        "boundary": "The free-energy principle is a broad account of self-organizing inference and action; additional bridge claims are required before it becomes a theory of phenomenal consciousness specifically.",
        "questions": ["Which formal quantity maps to level or content of consciousness rather than generic adaptive regulation?", "What prediction differs from predictive-processing accounts that remain neutral about phenomenality?"],
    },
    "seed-004-functionalism": {
        "slug": "functionalism",
        "boundary": "Functionalism characterizes mental states by causal role and comes in multiple versions; it should not be treated as one neural architecture or as automatically resolving qualia objections.",
        "questions": ["Which level of functional organization is sufficient for phenomenal consciousness?", "How should absent-qualia, inverted-spectrum, and multiple-realization objections be adjudicated?"],
    },
    "seed-085-husserlian-transcendental-phenomenology": {
        "slug": "husserl-s-transcendental-phenomenology",
        "boundary": "Husserlian transcendental phenomenology is a disciplined philosophical method and account of intentional constitution, not an introspection-only empirical theory or a claim about a neural ego module.",
        "questions": ["How can transcendental structures constrain empirical consciousness research without being reduced to it?", "How should prereflective self-awareness and the transcendental ego be compared with no-self and minimal-self accounts?"],
    },
    "seed-005-non-reductive-physicalism": {
        "slug": "murphy-s-non-reductive-physicalism",
        "boundary": "Non-reductive physicalism is a family of positions; dependence on the physical does not by itself explain realization, causal efficacy, or phenomenal character.",
        "questions": ["How can irreducible mental properties remain causally efficacious under physical causal closure?", "Which dependence relation avoids both reductive identity and substance dualism?"],
    },
    "seed-020-panprotopsychism": {
        "slug": "panprotopsychism",
        "boundary": "Panprotopsychism attributes ubiquitous proto-phenomenal bases rather than ubiquitous full experiences; it remains distinct from both micropsychism and neutral monism.",
        "questions": ["How do proto-phenomenal properties jointly constitute actual phenomenal character?", "What distinguishes a proto-phenomenal base from a merely structural physical property?"],
    },
    "seed-018-russellian-monism": {
        "slug": "russellian-monism",
        "boundary": "Russellian monism identifies a structural-description gap in physics and proposes intrinsic categorical bases; different versions are physicalist, panpsychist, or panprotopsychist and should not be conflated.",
        "questions": ["Why should the intrinsic nature of matter be phenomenal or proto-phenomenal?", "Can the view solve combination and structural-mismatch problems without adding unsupported primitives?"],
    },
    "seed-008-biological-naturalism": {
        "slug": "searle-s-biological-naturalism",
        "boundary": "Biological naturalism treats consciousness as a real, causally efficacious biological feature; it rejects both eliminativism and substance dualism but leaves the precise emergence relation contested.",
        "questions": ["Which biological causal powers are sufficient for consciousness and why?", "Can causal emergence be specified without reducing the view to identity theory or property dualism?"],
    },
}

# These are lower string-similarity matches that were manually checked as the
# same catalog entity (usually because the source page prefixes an author's
# possessive name).  The map is explicit to prevent unrelated fuzzy matches
# from entering the catalog.
PROFILES.update(
    {
        "seed-043-neurophenomenology": {
            "slug": "varela-s-neurophenomenology",
            "boundary": "Neurophenomenology is a reciprocal research strategy linking disciplined first-person reports and neurobiology; it is not itself a single neural mechanism or a license to treat every introspective report as incorrigible.",
            "questions": ["Which first-person structures produce reproducible constraints on neural analysis?", "How can mutual constraints disconfirm, rather than merely redescribe, a hypothesis?"],
        },
        "seed-011-epiphenomenalism": {
            "slug": "epiphenomenalism-dualism",
            "boundary": "Epiphenomenalism makes phenomenal states causally inert with respect to physical behavior; it must be separated from methodological claims that reports can be studied without granting consciousness causal power.",
            "questions": ["How could knowledge and report of experience arise if experience is causally inert?", "Can evolutionary explanations accommodate causally idle phenomenal properties?"],
        },
        "seed-023-analytic-idealism": {
            "slug": "kastrup-s-analytic-idealism",
            "boundary": "Analytic idealism is Kastrup's specific universal-consciousness and dissociation model, not a synonym for every historical idealism or nondual tradition.",
            "questions": ["What makes dissociation an explanatory mechanism rather than an analogy?", "Which observations distinguish analytic idealism from neutral monism or cosmopsychism?"],
        },
        "seed-009-eliminative-materialism": {
            "slug": "churchland-s-eliminative-materialism",
            "boundary": "Eliminative materialism predicts replacement of parts of folk psychology; it is not identical to illusionism about phenomenal properties or to denying all conscious function and report.",
            "questions": ["Which folk-psychological categories should mature neuroscience eliminate rather than reduce?", "How does the position account for the apparent epistemic authority of experience reports?"],
        },
        "seed-019-panpsychism": {
            "slug": "panpsychisms-overview",
            "boundary": "Panpsychism is a family-level record; micropsychism, cosmopsychism, constitutive, emergent, and panprotopsychist variants retain separate commitments and combination problems.",
            "questions": ["How do basic experiential properties compose into unified subjects?", "What explanatory or empirical leverage distinguishes panpsychist variants from structural physicalism?"],
        },
        "seed-016-neutral-monism": {
            "slug": "neutral-monism-overview",
            "boundary": "Neutral monism posits a base intrinsically neither mental nor physical; it does not by itself identify that base with information, pure experience, or quantum structure.",
            "questions": ["What is the neutral base and how are mental and physical descriptions derived from it?", "Can the view avoid merely renaming the mind-body relation?"],
        },
        "seed-070-holonomic-brain-theory": {
            "slug": "pribram-s-holonomic-brain-theory",
            "boundary": "Holonomic brain theory uses distributed, transform-domain processing to explain aspects of memory and perception; holographic mathematics does not alone explain phenomenal consciousness.",
            "questions": ["Which transform-domain signatures are specific to the proposed conscious organization?", "Can causal interventions distinguish the account from ordinary distributed neural coding?"],
        },
        "seed-037-multiple-drafts-model": {
            "slug": "dennett-s-multiple-drafts-model",
            "boundary": "The Multiple Drafts Model rejects a single Cartesian theater and final presentation point; it should not be reduced to the weaker claim that processing is distributed.",
            "questions": ["How does the model explain apparent temporal order and phenomenal unity without a privileged draft?", "Which experiments distinguish multiple drafts from global-workspace or recurrent accounts?"],
        },
        "seed-003-anomalous-monism": {
            "slug": "davidson-s-anomalous-monism",
            "boundary": "Anomalous monism combines token physicalism with the denial of strict psychophysical laws; it is not a paranormal claim and differs from neutral or dual-aspect monism.",
            "questions": ["How can mental descriptions retain causal relevance under token identity?", "Does the absence of strict laws block systematic scientific explanation of mental events?"],
        },
        "seed-069-society-of-mind": {
            "slug": "minsky-s-society-of-mind",
            "boundary": "Society of Mind explains intelligence through interacting subagents; whether that architecture explains phenomenal consciousness is an additional and disputed claim.",
            "questions": ["Which organization of subagents is sufficient for a unified conscious perspective?", "Can the framework explain phenomenality rather than flexible cognition alone?"],
        },
        "seed-059-entropic-brain-hypothesis": {
            "slug": "carhart-harris-s-entropic-brain-hypothesis",
            "boundary": "The Entropic Brain Hypothesis concerns measurable disorder and repertoire in brain dynamics across states; entropy is not synonymous with information, complexity, or intensity of consciousness.",
            "questions": ["Which entropy measure generalizes across psychedelics, dreaming, psychosis, and ordinary wakefulness?", "Does increased entropy track conscious level, content diversity, or cognitive flexibility?"],
        },
        "seed-017-dual-aspect-monism": {
            "slug": "atmanspacher-s-dual-aspect-monism",
            "boundary": "Dual-aspect monism is a family of views in which mental and physical are aspects of one reality; Atmanspacher's formulation is one version and is not merged with Spinozist, Russellian, or theological variants.",
            "questions": ["What grounds lawful correlations between aspects without hidden causal interaction?", "How do competing dual-aspect formulations differ in testable or explanatory content?"],
        },
        "seed-146-perceptual-reality-monitoring-theory-prm": {
            "slug": "lau-s-perceptual-reality-monitoring-theory",
            "boundary": "PRM ties conscious perception to higher-order estimates that sensory representations are reality-indicating; it is not equivalent to first-order signal strength or generic confidence.",
            "questions": ["Can reality-monitoring estimates be manipulated independently of performance and report?", "How does PRM handle conscious imagery, dreams, and hallucination?"],
        },
        "seed-058-homeostatic-feelings-theory": {
            "slug": "damasio-s-homeostatic-feelings-and-emergence-of-consciousness",
            "boundary": "Damasio's account makes organism regulation and feeling central to subjectivity; it does not imply that every homeostatic control loop is conscious.",
            "questions": ["Which homeostatic and interoceptive processes are necessary for conscious feeling?", "How does the account explain nonaffective-seeming perceptual and conceptual experience?"],
        },
        "seed-067-computational-theory-of-mind-computationalism": {
            "slug": "computational-theories",
            "boundary": "Computational theories of mind are a family defined by representational or computational organization; a computation account of cognition does not automatically establish computational sufficiency for consciousness.",
            "questions": ["Which computation, implementation relation, and grain are consciousness-relevant?", "How can the view avoid triviality and explain qualitative character?"],
        },
        "seed-042-enactivism-autopoietic-enactivism": {
            "slug": "enactivism",
            "boundary": "Enactivism treats cognition as embodied sense-making in organism-environment coupling; autopoietic, sensorimotor, and radical variants make different claims about representation and consciousness.",
            "questions": ["Which forms of embodied coupling are necessary for phenomenal consciousness?", "What empirical result distinguishes enactive explanation from embodied predictive processing?"],
        },
        "seed-066-conscious-turing-machine-ctm": {
            "slug": "blums-conscious-turing-machine",
            "boundary": "The Conscious Turing Machine is a formal global-workspace-style architecture; its functional broadcasts should not be assumed identical with phenomenal consciousness without a bridge argument.",
            "questions": ["Which architectural properties are necessary rather than implementation conveniences?", "Could a behaviorally equivalent architecture lack the proposed conscious status?"],
        },
        "seed-194-dreaming-and-rem-protoconsciousness": {
            "slug": "hobson-s-dreaming-protoconsciousness",
            "boundary": "Protoconsciousness theory assigns REM dreaming a developmental and virtual-world-modeling role; dreaming is not restricted to REM and the proposal is distinct from the AIM state-space model.",
            "questions": ["Which developmental outcomes specifically depend on REM protoconsciousness?", "How should non-REM dreams and conscious imagery outside sleep be accommodated?"],
        },
        "seed-163-higher-order-representation-of-a-representation-horor": {
            "slug": "brown-s-horor-higher-order-representationalism",
            "boundary": "HOROR requires a higher-order representation whose target is itself a representation; it differs from standard HOT, inner-sense, and same-order theories.",
            "questions": ["Can HOROR explain conscious states when no explicit higher-order thought is reportable?", "What neural or behavioral signature uniquely indicates representation of a representation?"],
        },
        "seed-055-projective-consciousness-model-pcm": {
            "slug": "projective-consciousness-model",
            "boundary": "PCM uses projective geometry and active inference to model first-person perspective and evaluation; projective structure is not by itself a complete account of phenomenal existence.",
            "questions": ["How are projective parameters estimated neurally and behaviorally?", "Which prediction distinguishes PCM from other active-inference or spatial self-model accounts?"],
        },
        "seed-046-neural-correlates-of-consciousness-ncc-framework": {
            "slug": "crick-and-koch-s-neural-correlates-of-consciousness",
            "boundary": "The NCC program seeks minimally sufficient neural conditions and is a discovery framework, not one theory of why those conditions yield experience; prerequisites and consequences must be separated from correlates.",
            "questions": ["Which candidate NCCs are causal rather than prerequisites or report consequences?", "Can content-specific NCCs be separated from general conscious level and task access?"],
        },
        "seed-065-integrated-world-modeling-theory-iwmt": {
            "slug": "safron-s-integrated-world-modeling-theory",
            "boundary": "IWMT synthesizes active inference, global workspace, and integrated-information ideas; the synthesis must retain which component supports each claim rather than treating neighboring theories as already unified.",
            "questions": ["Which prediction is unique to the integrated architecture?", "How are workspace access, world modeling, and information integration jointly necessary?"],
        },
        "seed-028-integrated-information-theory-iit": {
            "slug": "tononi-s-integrated-information-theory",
            "boundary": "IIT identifies consciousness with maximally irreducible cause-effect structure under its postulates; empirical proxies for complexity are not equivalent to calculating the theory's full intrinsic structure.",
            "questions": ["How should system grain and exclusion be fixed without observer-relative choices?", "Can feasible experiments test IIT's counterintuitive predictions against rival theories?"],
        },
        "seed-029-recurrent-processing-theory-rpt": {
            "slug": "lamme-s-recurrent-processing-theory",
            "boundary": "RPT makes local recurrent sensory processing central to phenomenal consciousness and separates it from later global access; recurrence in general is not sufficient without specifying the relevant circuits and dynamics.",
            "questions": ["Can local recurrence support experience without attention, report, or frontoparietal access?", "Which perturbation cleanly isolates recurrent from feedforward and global processes?"],
        },
        "seed-071-conscious-electromagnetic-information-cemi-field-theory": {
            "slug": "mcfadden-s-conscious-electromagnetic-information-theory",
            "boundary": "CEMI proposes that integrated electromagnetic information has a causal role in consciousness; ordinary correlations between neural currents and experience do not establish independent field causation.",
            "questions": ["Can field effects be perturbed while holding ordinary synaptic signaling sufficiently constant?", "What field property determines conscious content and excludes ubiquitous non-neural fields?"],
        },
    }
)


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    entries = {entry["slug"]: entry for entry in registry["entries"]}
    records = {record["id"]: record for record in catalog["records"]}

    for record_id, profile in PROFILES.items():
        record = records[record_id]
        source = entries[profile["slug"]]
        # Keep project-authored scope text; the external registry is a locator,
        # not a license to republish its descriptions or takeaways.
        record["claim_scope"] = {"Catalog scope": record["summary"]}
        record["boundary_note"] = profile["boundary"]
        record["evidence_profile"] = {
            "Source-frame support": f"Dedicated attributed profile with {len(source.get('references', []))} retained references.",
            "Existing catalog basis": f"{len(record.get('citations', []))} independently retained works preceded this enrichment.",
            "Review limit": "The profile match and locator are verified; claim-level evidential adjudication remains open.",
        }
        record["open_questions"] = profile["questions"]
        if source["url"] not in {citation["url"] for citation in record["citations"]}:
            record["citations"].append(
                {
                    "title": source["name"],
                    "authors": "Closer To Truth, Landscape of Consciousness",
                    "year": 2025,
                    "url": source["url"],
                    "venue": "Landscape of Consciousness",
                    "authority": "authoritative-secondary",
                    "retrieved": "2026-08-30",
                    "verification": "human-verified",
                    "note": "Dedicated source profile retained as an attributed locator.",
                }
            )

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=CATALOG.parent, delete=False) as handle:
        json.dump(catalog, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(CATALOG)
    print(f"Enriched {len(PROFILES)} exact-match base records")


if __name__ == "__main__":
    main()
