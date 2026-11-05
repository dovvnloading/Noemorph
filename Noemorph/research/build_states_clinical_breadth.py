"""Build the states, clinical-assessment, and consciousness-measurement shard.

The selection and prose below are human-curated.  Crossref is used only to
resolve exact bibliographic metadata for already-selected DOI locators.  The
script rejects exact name/alias collisions against every other catalog shard;
it does not register its output in ``catalog.json``.
"""

from __future__ import annotations

import html
import json
import re
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


APP_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = APP_DIR / "data"
OUTPUT = DATA_DIR / "catalog-2026-08-30-states-clinical-breadth.json"
RETRIEVED = "2026-08-30"
CANONICAL_KINDS = {
    "Scientific theory",
    "Model or framework",
    "Clinical / state model",
    "Theory of mind / social cognition",
    "Phenomenological construct",
    "Philosophical position",
    "Argument / challenge",
    "Historical tradition",
}


def normalize(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.casefold()).split())


def clean(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def doi_source(doi: str, authority: str, title: str | None = None) -> dict[str, str]:
    source = {"doi": doi, "authority": authority}
    if title:
        source["title"] = title
    return source


MANUAL_SOURCES: dict[str, dict[str, Any]] = {
    "ny-declaration": {
        "title": "The New York Declaration on Animal Consciousness",
        "authors": "Kristin Andrews; Jonathan Birch; Jeff Sebo; Taylor Sims",
        "year": 2024,
        "venue": "New York Declaration on Animal Consciousness",
        "url": "https://sites.google.com/nyu.edu/nydeclaration/declaration",
        "authority": "primary-consensus-statement",
        "verification": "human-verified",
        "retrieved": RETRIEVED,
    },
    "ny-background": {
        "title": "Background to the New York Declaration on Animal Consciousness",
        "authors": "Kristin Andrews; Jonathan Birch; Jeff Sebo; Taylor Sims",
        "year": 2024,
        "venue": "New York Declaration on Animal Consciousness",
        "url": "https://sites.google.com/nyu.edu/nydeclaration/background",
        "authority": "authoritative-background",
        "verification": "human-verified",
        "retrieved": RETRIEVED,
    },
    "cambridge-declaration": {
        "title": "The Cambridge Declaration on Consciousness",
        "authors": "Philip Low; Jaak Panksepp; Diana Reiss; David Edelman; Bruno Van Swinderen; Christof Koch",
        "year": 2012,
        "venue": "Francis Crick Memorial Conference on Consciousness in Human and non-Human Animals",
        "url": "https://www.ocf.berkeley.edu/~jfkihlstrom/ConsciousnessWeb/PDFs/CambridgeDeclarationOnConsciousness.pdf",
        "authority": "primary-consensus-statement",
        "verification": "human-verified",
        "retrieved": RETRIEVED,
    },
}


def manual_source(key: str) -> dict[str, str]:
    return {"manual": key}


def spec(
    record_id: str,
    name: str,
    aliases: list[str],
    kind: str,
    domain: str,
    tradition: str,
    year: int,
    proponents: list[str],
    summary: str,
    target: str,
    level: str,
    basis: list[str],
    limitations: list[str],
    boundary: str,
    questions: list[str],
    sources: list[dict[str, str]],
    keywords: list[str],
    status: str = "active research construct · interpretation bounded",
    status_note: str | None = None,
) -> dict[str, Any]:
    if status_note is None:
        status_note = (
            "The named construct has a traceable operational literature, but its output must be "
            "interpreted with convergent behavioral, clinical, or physiological evidence."
        )
    return {
        "id": record_id,
        "name": name,
        "aliases": aliases,
        "kind": kind,
        "domain": domain,
        "tradition": tradition,
        "status": status,
        "status_note": status_note,
        "summary": summary,
        "proponents": proponents,
        "year": year,
        "era": f"{year}–present",
        "scope": target,
        "keywords": keywords,
        "boundary_note": boundary,
        "claim_scope": {
            "target": target,
            "level": level,
            "does_not_establish": boundary,
        },
        "evidence_profile": {
            "basis": basis,
            "limitations": limitations,
            "independence": (
                "The citation set pairs a defining or validation source with an independent validation, "
                "systematic assessment, or authoritative comparison where available."
            ),
        },
        "open_questions": questions,
        "review_state": "provisional",
        "_sources": sources,
    }


SPECS: list[dict[str, Any]] = [
    # Disorders of consciousness and neurobehavioral assessment
    spec(
        "states-clinical-001-crs-r", "Coma Recovery Scale–Revised", ["CRS-R", "JFK CRS-R"],
        "Model or framework", "Disorders of consciousness / assessment", "Neurorehabilitation / standardized behavioral assessment", 2004,
        ["Joseph T. Giacino", "Kathleen Kalmar", "John Whyte"],
        "The CRS-R samples auditory, visual, motor, oromotor-verbal, communication, and arousal behaviors with hierarchically ordered items used to support differential diagnosis and track recovery after severe brain injury.",
        "Standardized bedside detection and longitudinal description of behaviors relevant to coma, unresponsive wakefulness syndrome, minimally conscious state, and emergence.", "Bedside behavioral and diagnostic assessment.",
        ["The original revision reported reliability and diagnostic utility across six functional subscales.", "An evidence-based systematic review identified the CRS-R as the strongest-supported standardized DoC scale in its review period."],
        ["Motor, sensory, language, fatigue, medication, and fluctuating arousal can conceal awareness.", "Repeated testing improves sensitivity but does not eliminate false-negative behavioral diagnoses."],
        "A CRS-R score is an operational behavioral assessment, not a direct meter of phenomenal consciousness and not a causal theory of consciousness.",
        ["How many repeated assessments optimize detection without impractical burden?", "Which neural measures add independent diagnostic information to CRS-R profiles?"],
        [doi_source("10.1016/j.apmr.2004.02.033", "primary-scale-validation", "The JFK Coma Recovery Scale–Revised: Measurement characteristics and diagnostic utility"), doi_source("10.1016/j.apmr.2010.07.218", "systematic-review-guideline")],
        ["CRS-R", "coma", "minimally conscious state", "behavioral assessment"]),
    spec(
        "states-clinical-002-gcs", "Glasgow Coma Scale", ["GCS", "Glasgow Coma Score"],
        "Model or framework", "Acute impaired consciousness / assessment", "Emergency medicine / neurosurgical assessment", 1974,
        ["Graham Teasdale", "Bryan Jennett"],
        "The GCS separately grades eye, verbal, and motor responses to provide a compact, repeatable description of acute impaired responsiveness and neurological severity.",
        "Rapid standardized communication of acute responsiveness after brain injury or critical illness.", "Emergency bedside assessment.",
        ["The original scale operationalized three response domains for serial observation.", "A forty-year review documents its global clinical use, revisions, and recurrent interpretation problems."],
        ["Intubation, aphasia, sedation, sensory loss, and focal motor injury can make components untestable or misleading.", "The summed score can hide clinically different component profiles."],
        "The GCS measures observable responsiveness and injury severity; it neither diagnoses every disorder of consciousness nor establishes absence of experience.",
        ["When should component profiles replace the sum in clinical decisions?", "How can untestable components be represented without false precision?"],
        [doi_source("10.1016/S0140-6736(74)91639-0", "primary-original"), doi_source("10.1016/S1474-4422(14)70120-6", "authoritative-historical-review")],
        ["GCS", "acute brain injury", "responsiveness", "coma scale"]),
    spec(
        "states-clinical-003-four", "Full Outline of UnResponsiveness Score", ["FOUR Score", "FOUR coma scale"],
        "Model or framework", "Acute impaired consciousness / assessment", "Neurocritical care / bedside assessment", 2005,
        ["Eelco F. M. Wijdicks", "William R. Bamlet", "Bob V. Maramattom", "Eelco M. Manno", "Robert L. McClelland"],
        "The FOUR Score grades eye and motor responses, brainstem reflexes, and respiration, omitting a verbal item so that intubated neurocritical-care patients can be characterized more directly.",
        "Structured assessment of responsiveness, brainstem function, and respiratory pattern in acute neurocritical illness.", "Neurocritical-care bedside assessment.",
        ["The defining study reported interrater agreement and outcome prediction in a prospectively assessed cohort.", "The scale has been compared with other coma scales in systematic clinical assessment literature."],
        ["Training, case mix, and sedation affect reliability and prognostic calibration.", "Brainstem and respiratory items add neurological detail but remain behavioral-physiological proxies."],
        "The FOUR Score is a clinical examination framework, not a measure of subjective contents or a theory of why consciousness is lost.",
        ["Which populations gain the largest prognostic benefit over GCS components?", "How should serial FOUR trajectories be combined with covert-command-following tests?"],
        [doi_source("10.1002/ana.20611", "primary-original-validation"), doi_source("10.1016/j.apmr.2010.07.218", "systematic-review-guideline")],
        ["FOUR Score", "brainstem reflex", "respiration", "neurocritical care"]),
    spec(
        "states-clinical-004-whim", "Wessex Head Injury Matrix", ["WHIM", "Wessex Head Injury Matrix scale"],
        "Model or framework", "Disorders of consciousness / assessment", "Neurorehabilitation / longitudinal behavioral measurement", 2000,
        ["Ruth Shiel", "Barbara A. Wilson", "D. I. McLellan", "A. Horn", "S. Watson", "M. J. Campbell"],
        "The WHIM orders 62 observed behaviors from early reflexive responses through more complex communication and cognition to trace small longitudinal changes during recovery after severe head injury.",
        "Fine-grained serial description of behavioral recovery from coma and very low awareness states.", "Longitudinal neurobehavioral assessment.",
        ["The original clinical study developed a hierarchical item matrix and evaluated reliability and recovery sensitivity.", "A systematic evidence review evaluated WHIM administration, scoring, reliability, and diagnostic support."],
        ["The hierarchy is not invariant for every etiology or individual recovery path.", "Observed behavior remains vulnerable to motor and sensory confounds."],
        "The WHIM is a recovery-monitoring instrument; its ordinal sequence is not a universal stage theory and does not directly quantify experience.",
        ["Which item sequences generalize across traumatic and nontraumatic etiologies?", "What change threshold is clinically meaningful within individuals?"],
        [doi_source("10.1191/0269215500cr326oa", "primary-scale-development"), doi_source("10.1016/j.apmr.2010.07.218", "systematic-review-guideline")],
        ["WHIM", "head injury", "recovery", "longitudinal assessment"]),
    spec(
        "states-clinical-005-smart", "Sensory Modality Assessment and Rehabilitation Technique", ["SMART", "Sensory Modality Assessment and Rehabilitation Technique scale"],
        "Model or framework", "Disorders of consciousness / assessment", "Neurorehabilitation / multimodal sensory assessment", 1997,
        ["Frances Gill-Thwaites", "Roger Munday"],
        "SMART uses repeated, standardized presentation of stimuli across sensory modalities and structured observation of responses to aid diagnosis and rehabilitation planning in prolonged disorders of consciousness.",
        "Repeated multimodal elicitation and documentation of behavioral evidence of awareness.", "Specialist neurorehabilitation assessment.",
        ["The defining publication described a structured assessment and rehabilitation technique for vegetative and minimally responsive patients.", "A later validation study examined reliability and validity of the SMART assessment."],
        ["Administration is resource-intensive and requires specialist training.", "Stimulus salience and residual sensory-motor capacity can alter response yield."],
        "SMART assesses elicited responsiveness; therapeutic stimulation is not proof that sensory input produces conscious recovery, and the protocol is not a causal consciousness theory.",
        ["Which stimulus personalization improves sensitivity without reducing standardization?", "How should SMART results be reconciled with discordant CRS-R or imaging findings?"],
        [doi_source("10.1080/026990597123098", "primary-method-description"), doi_source("10.1080/02699050410001719952", "primary-validation")],
        ["SMART", "sensory stimulation", "prolonged disorders of consciousness", "rehabilitation"]),
    spec(
        "states-clinical-006-docs", "Disorders of Consciousness Scale", ["DOCS", "Disorders of Consciousness Scale assessment"],
        "Model or framework", "Disorders of consciousness / assessment", "Rehabilitation measurement / neurobehavioral assessment", 2005,
        ["Theresa Louise-Bender Pape", "Allen W. Heinemann", "James P. Kelly", "Anita Giobbie Hurder", "Sandra Lundgren"],
        "DOCS samples neurobehavioral responses across sensory and functional domains to detect and quantify subtle change during recovery from severe brain injury.",
        "Reliable serial measurement of neurobehavioral functioning in people with severe disorders of consciousness.", "Multidisciplinary rehabilitation assessment.",
        ["The multicenter development study reported theory, reliability, and validity for the scale.", "An evidence-based review compared DOCS psychometric and administrative properties with other DoC instruments."],
        ["Diagnostic inference from item totals can be limited by heterogeneous impairments.", "Its sensitivity and predictive validity require context-specific interpretation."],
        "DOCS is an observational scale for neurobehavioral function; it cannot by itself determine whether an unresponsive patient has experience or explain its neural basis.",
        ["Which DOCS changes exceed measurement error at the individual level?", "How do DOCS profiles relate to later functional communication?"],
        [doi_source("10.1682/JRRD.2004.03.0032", "primary-scale-validation"), doi_source("10.1016/j.apmr.2010.07.218", "systematic-review-guideline")],
        ["DOCS", "neurobehavioral function", "severe brain injury", "assessment"]),
    spec(
        "states-clinical-007-ncs-r", "Nociception Coma Scale–Revised", ["NCS-R", "Nociception Coma Scale Revised"],
        "Model or framework", "Disorders of consciousness / pain assessment", "Clinical pain assessment / neurorehabilitation", 2012,
        ["Camille Chatelle", "Caroline Schnakers", "Steven Laureys"],
        "The NCS-R scores motor, verbal, and facial responses to potentially noxious stimulation to improve detection of nociception-related behavior in patients unable to communicate.",
        "Structured bedside assessment of nociception-related behavioral responses in disorders of consciousness.", "Clinical behavioral pain assessment.",
        ["The precursor Nociception Coma Scale was developed specifically for noncommunicative DoC populations.", "Subsequent work related NCS-R scores to anterior cingulate metabolism and characterized clinically useful response thresholds."],
        ["Nociceptive response, pain experience, arousal, and reflex motor output are not identical constructs.", "Medication and severe motor impairment can suppress scored behavior."],
        "The NCS-R measures nociception-related behavior, not pain experience directly and not the patient's global level of consciousness.",
        ["Which physiological measures improve discrimination of reflex nociception from experienced pain?", "How should analgesia decisions handle low scores with high uncertainty?"],
        [doi_source("10.1016/j.pain.2009.09.028", "primary-precursor-development"), doi_source("10.1177/1545968313503220", "primary-convergent-validation")],
        ["NCS-R", "nociception", "pain", "disorders of consciousness"]),
    spec(
        "states-clinical-008-matadoc", "Music Therapy Assessment Tool for Awareness in Disorders of Consciousness", ["MATADOC", "Music Therapy Assessment Tool for Awareness"],
        "Model or framework", "Disorders of consciousness / auditory assessment", "Music therapy / neurorehabilitation", 2014,
        ["Wendy L. Magee", "Richard J. Siegert", "Barbara A. Daveson", "Gemma Lenton-Smith", "Steve M. Taylor"],
        "MATADOC standardizes music-based and auditory interaction to observe responsiveness, support awareness assessment, and inform treatment planning in prolonged disorders of consciousness.",
        "Music-based assessment of auditory responsiveness and awareness-relevant behavior in prolonged disorders of consciousness.", "Specialist music-therapy assessment.",
        ["The principal subscale was standardized with reliability, dimensionality, and diagnostic comparison analyses.", "A later multisite study assessed concurrent validity with the CRS-R and domain-specific complementarity."],
        ["Results depend on therapist training, stimulus familiarity, hearing, and response capacity.", "Music-evoked behavior cannot alone identify phenomenal content."],
        "MATADOC is a specialized assessment and clinical-planning tool, not evidence that music uniquely restores consciousness or a theory of awareness.",
        ["Which personalized musical features improve detection while preserving reproducibility?", "When does MATADOC add information beyond standard auditory CRS-R items?"],
        [doi_source("10.1080/09602011.2013.844174", "primary-standardization"), doi_source("10.1016/j.apmr.2023.03.010", "multisite-concurrent-validation")],
        ["MATADOC", "music therapy", "auditory responsiveness", "awareness assessment"]),

    # Anesthesia, sedation, and perioperative awareness
    spec(
        "states-clinical-009-ift", "Isolated Forearm Technique", ["IFT", "isolated forearm test"],
        "Model or framework", "Anesthesia / connected consciousness assessment", "Clinical anesthesiology / command-following paradigm", 1977,
        ["M. E. Tunstall", "I. F. Russell", "Robert D. Sanders"],
        "Before neuromuscular blockade reaches one forearm, a tourniquet preserves movement there so an anesthetized patient can be asked to follow commands despite paralysis elsewhere.",
        "Intraoperative detection of connected consciousness through command following during intended general anesthesia.", "Perioperative behavioral probe under neuromuscular blockade.",
        ["Prospective IFT studies document command following in a subset of patients during anesthesia.", "A systematic review and meta-analysis assessed prevalence, methods, and heterogeneity across IFT studies."],
        ["Responses can be brief, technically difficult to elicit, and affected by tourniquet duration and command protocol.", "Lack of postoperative recall does not negate contemporaneous command following."],
        "IFT positivity operationalizes connected responsiveness, not all possible experience; IFT negativity does not prove unconsciousness.",
        ["Which standardized command and verification protocol best controls false responses?", "What predicts later distress or explicit memory among IFT-positive patients?"],
        [doi_source("10.1093/bja/aew112", "authoritative-methodological-review"), doi_source("10.1016/j.bja.2018.02.019", "systematic-review-meta-analysis")],
        ["IFT", "connected consciousness", "anesthesia", "command following"]),
    spec(
        "states-clinical-010-bis", "Bispectral Index", ["BIS", "BIS monitor", "bispectral EEG index"],
        "Model or framework", "Anesthesia / EEG monitoring", "Processed electroencephalography / anesthesiology", 1997,
        ["Jeffrey C. Sigl", "Nassib G. Chamoun"],
        "BIS compresses selected frontal EEG features into a proprietary scalar intended to track hypnotic drug effect and assist anesthetic titration.",
        "Processed-EEG index of anesthetic hypnotic state for intraoperative monitoring and drug titration.", "Frontal scalp EEG / proprietary signal processing.",
        ["The foundational report described the multivariate EEG measure and its statistical development.", "A large randomized trial tested BIS-guided anesthesia for reducing intraoperative awareness in high-risk patients."],
        ["Values vary with agent, artifact, age, physiology, and neuromuscular blockade.", "Proprietary mapping and overlapping state distributions limit mechanistic interpretation."],
        "BIS is a drug- and context-sensitive EEG index, not a direct consciousness meter; a number cannot establish absence of disconnected experience.",
        ["How should age- and drug-specific calibration be incorporated?", "Which raw-EEG features should clinicians inspect when BIS and behavior disagree?"],
        [doi_source("10.1097/00000542-199704000-00014", "primary-index-development"), doi_source("10.1056/NEJMoa0707361", "randomized-clinical-trial")],
        ["BIS", "processed EEG", "depth of anesthesia", "awareness"]),
    spec(
        "states-clinical-011-psi", "Patient State Index", ["PSI", "SedLine Patient State Index"],
        "Model or framework", "Anesthesia and sedation / EEG monitoring", "Processed electroencephalography / anesthesiology", 2002,
        ["David R. Drover", "Hans R. L. Ortega", "Donald R. Willard"],
        "PSI combines quantitative features from multichannel frontal EEG into a scalar intended to represent anesthetic or sedative state.",
        "Processed-EEG monitoring of hypnotic and sedative state across anesthesia and critical care.", "Multichannel frontal EEG / proprietary classification.",
        ["Initial validation related PSI to graded anesthetic state and responsiveness.", "Independent clinical evaluation tested PSI performance under routine general anesthesia."],
        ["Agent, electromyographic artifact, burst suppression, and patient factors alter the mapping.", "A scalar index can conceal qualitatively distinct EEG patterns."],
        "PSI estimates an EEG-defined state and is neither a phenomenological report nor a universally calibrated probability of consciousness.",
        ["How robust is PSI across drugs and neurologic comorbidity?", "When should discordance with raw EEG or command following override the index?"],
        [doi_source("10.1097/00000542-200207000-00012", "primary-validation"), doi_source("10.1093/bja/aeh082", "independent-clinical-evaluation")],
        ["PSI", "SedLine", "processed EEG", "sedation"]),
    spec(
        "states-clinical-012-entropy", "State Entropy and Response Entropy Monitoring", ["M-Entropy", "state entropy", "response entropy", "SE and RE indices"],
        "Model or framework", "Anesthesia / EEG and EMG monitoring", "Spectral entropy monitoring / anesthesiology", 2004,
        ["Hanna Viertiö-Oja", "Vesa Maja", "Matti Särkelä"],
        "The entropy module computes State Entropy from a lower-frequency EEG-dominant band and Response Entropy from a broader EEG-plus-frontal-EMG band to track hypnotic state and rapid arousal-related change.",
        "Spectral-irregularity indices used to monitor anesthetic hypnotic state and frontal muscle activation.", "Frontal EEG and EMG signal processing.",
        ["The defining publication specifies the spectral entropy algorithm and intended distinction between SE and RE.", "Clinical comparison studies evaluate how entropy indices track anesthetic concentration and responsiveness."],
        ["Entropy changes with artifact, EMG, agent, burst suppression, and the analyzed frequency distribution.", "Similar values may arise from physiologically different signals."],
        "SE and RE are engineered signal summaries, not thermodynamic brain entropy and not sufficient evidence about whether any experience is present.",
        ["Which raw-signal checks best prevent artifact-driven interpretation?", "Can entropy indices distinguish connected from disconnected consciousness?"],
        [doi_source("10.1111/j.0001-5172.2004.00322.x", "primary-algorithm-description"), doi_source("10.1111/j.0001-5172.2004.00323.x", "primary-multidrug-validation")],
        ["state entropy", "response entropy", "M-Entropy", "anesthesia EEG"]),
    spec(
        "states-clinical-013-oaas", "Observer's Assessment of Alertness/Sedation Scale", ["OAA/S", "MOAA/S", "Modified Observer's Assessment of Alertness/Sedation"],
        "Model or framework", "Sedation / behavioral assessment", "Clinical pharmacology / procedural sedation", 1990,
        ["Donald A. Chernik", "Robert J. Gillings", "Heidi Laine"],
        "OAA/S grades response to increasingly salient verbal and physical stimulation alongside speech, facial expression, and eye signs; the modified version commonly uses a single responsiveness score.",
        "Standardized clinical grading of alertness and responsiveness during pharmacologic sedation.", "Bedside behavioral sedation assessment.",
        ["The original validation related scale scores to benzodiazepine dose, clinical signs, and psychomotor measures.", "Anesthesia-depth reviews use OAA/S or MOAA/S as behavioral reference states for validating monitors."],
        ["Stimulus intensity, assessor technique, hearing, language, and motor capacity affect scores.", "Ordinal categories are not equally spaced physiological states."],
        "OAA/S measures observable sedation responsiveness, not all conscious experience and not a mechanism of sedative-induced unconsciousness.",
        ["How should stimulus delivery be standardized across settings?", "Which physiological markers add value at ambiguous intermediate scores?"],
        [doi_source("10.1097/00004714-199008000-00003", "primary-scale-validation", "Validity and Reliability of the Observer's Assessment of Alertness/Sedation Scale: Study with Intravenous Midazolam"), doi_source("10.1097/LBR.0000000000000784", "large-clinical-application")],
        ["OAA/S", "MOAA/S", "sedation", "alertness"]),
    spec(
        "states-clinical-014-rass", "Richmond Agitation–Sedation Scale", ["RASS", "Richmond Agitation Sedation Scale"],
        "Model or framework", "Critical care / arousal assessment", "Intensive care / behavioral sedation assessment", 2002,
        ["Curtis N. Sessler", "Mark S. Gosnell", "Mary Jo Grap", "Gordon M. Brophy"],
        "RASS places agitation and sedation on a ten-point ordinal continuum using observation, response to voice, and response to physical stimulation.",
        "Reliable serial assessment of agitation and sedation in critically ill adults.", "Intensive-care behavioral assessment.",
        ["The development study reported interrater reliability and criterion validity in ICU patients.", "A multicenter validation assessed reliability and validity across medical and surgical ICUs."],
        ["Neuromuscular weakness, deafness, aphasia, delirium, and medication can alter scored responses.", "RASS depth is not interchangeable with delirium or conscious-content assessment."],
        "RASS grades arousal-linked behavior; it does not establish the presence, absence, richness, or valence of subjective experience.",
        ["How should RASS be interpreted when motor output is severely impaired?", "Which trajectories best predict outcomes without embedding treatment effects?"],
        [doi_source("10.1164/rccm.2107138", "primary-scale-development"), doi_source("10.1001/jama.289.22.2983", "multicenter-validation")],
        ["RASS", "agitation", "sedation", "critical care"]),
    spec(
        "states-clinical-015-modified-brice", "Modified Brice Interview", ["Brice interview", "modified Brice questionnaire", "Brice protocol"],
        "Model or framework", "Anesthesia / explicit recall assessment", "Perioperative follow-up / structured interview", 1970,
        ["D. D. Brice", "R. R. Hetherington", "J. E. Utting"],
        "The Brice protocol uses structured postoperative questions, often at more than one time point, to identify explicit recall of events between induction and emergence and to adjudicate suspected awareness.",
        "Postoperative detection and characterization of explicit recall during general anesthesia.", "Structured retrospective patient interview.",
        ["The original study established a standardized direct-question approach to intraoperative dreaming and awareness.", "Later awareness research treats repeated modified Brice interviews as a more sensitive reference than spontaneous reporting."],
        ["Recall can emerge or fade over time and is affected by interview wording and memory impairment.", "Experience without later explicit memory will be missed."],
        "The modified Brice interview assesses postoperative explicit recall, not contemporaneous consciousness in patients who form no durable memory.",
        ["Which interview timing best balances delayed recall and forgetting?", "How should ambiguous dreamlike or uncertain reports be adjudicated?"],
        [doi_source("10.1093/bja/42.6.535", "primary-original"), doi_source("10.1056/NEJMoa0707361", "large-clinical-trial-method")],
        ["Brice interview", "anesthesia awareness", "explicit recall", "postoperative interview"]),
    spec(
        "states-clinical-016-connected-consciousness", "Connected Consciousness During General Anesthesia", ["connected consciousness", "intraoperative connected consciousness"],
        "Clinical / state model", "Anesthesia / conscious state taxonomy", "Anesthesiology / consciousness-state classification", 2012,
        ["Robert D. Sanders", "Michael S. Avidan", "Jamie W. Sleigh"],
        "Connected consciousness denotes experience that remains functionally connected to the environment during anesthesia, operationally distinguished from disconnected experience and from later explicit recall.",
        "State distinction between environment-connected experience, disconnected experience, and unresponsiveness during anesthesia.", "Perioperative state taxonomy supported by command-following and recall paradigms.",
        ["Prospective IFT studies show that command following can occur during intended anesthesia without later recall.", "A meta-analysis quantifies IFT responsiveness and methodological variation."],
        ["Command following samples only moments and depends on preserved motor output and task comprehension.", "The taxonomy does not by itself identify the neural mechanisms separating connected and disconnected experience."],
        "Connected consciousness is a state-level operational construct, not equivalent to postoperative awareness with recall and not a complete causal theory of anesthesia.",
        ["What neural signatures discriminate connected from disconnected experience in real time?", "Which forms of connected experience predict distress despite amnesia?"],
        [doi_source("10.1097/ALN.0b013e318249d0a7", "primary-concept-and-study"), doi_source("10.1016/j.bja.2018.02.019", "systematic-review-meta-analysis")],
        ["connected consciousness", "anesthesia", "IFT", "awareness without recall"]),
]

SPECS.extend([
    # Sleep, dream, and mixed-state constructs
    spec(
        "states-clinical-017-sleep-paralysis", "Sleep Paralysis", ["isolated sleep paralysis", "recurrent isolated sleep paralysis", "RISP"],
        "Clinical / state model", "Sleep and dreaming / mixed states", "Sleep medicine / REM-wake dissociation", 1876,
        ["Brian A. Sharpless", "Jacques Montplaisir", "Baland Jalal"],
        "Sleep paralysis is a transient state at sleep onset or awakening in which waking awareness and recall coexist with REM-related skeletal-muscle atonia, often with sensed presence, threat, or vestibular-motor hallucinations.",
        "Characterization of recurrent or isolated episodes combining wake-like awareness with REM atonia and dreamlike perceptual contents.", "Clinical phenomenology, polysomnography, and REM-state physiology.",
        ["Clinical and epidemiological work distinguishes isolated and recurrent episodes from narcolepsy-associated paralysis.", "Polysomnographic case studies document REM-like physiology during reported episodes."],
        ["Retrospective prevalence estimates vary with wording and population.", "Cultural interpretations shape report content without determining underlying physiology."],
        "Sleep paralysis is a mixed-state clinical construct; its hallucinations are not evidence for external agents, and the state is not a general theory of consciousness.",
        ["Which mechanisms determine threatening versus neutral episode content?", "How do cultural expectations and REM physiology interact prospectively?"],
        [doi_source("10.5664/jcsm.9056", "primary-polysomnographic-study"), doi_source("10.3390/jcm12123876", "authoritative-clinical-review")],
        ["sleep paralysis", "REM atonia", "hypnopompic hallucination", "mixed state"]),
    spec(
        "states-clinical-018-false-awakening", "False Awakening", ["dreamed awakening", "false-awakening dream"],
        "Phenomenological construct", "Sleep and dreaming / dream phenomenology", "Dream research / sleep-state dissociation", 1913,
        ["Celia Green", "Stephen LaBerge", "Remco B. B. Renfurm"],
        "A false awakening is a dream in which the person experiences having awakened and often performs routine waking activities before later recognizing that the apparent awakening occurred within sleep.",
        "Dream episodes whose central content is a convincing but mistaken experience of waking.", "First-person report linked where possible to polysomnography and lucid-dream methods.",
        ["Phenomenological collections distinguish false awakening from ordinary dream transitions and lucid recognition.", "EEG-documented cases place false awakenings and sleep paralysis near REM-wake boundary states."],
        ["The construct is identified retrospectively through report and has no unique accepted physiological marker.", "Narrative memory can merge successive awakenings."],
        "False awakening names a reported dream content and state transition; it does not imply an alternative reality and is not synonymous with lucid dreaming.",
        ["Which sleep-stage transitions preferentially generate false awakenings?", "Can prospective signaling distinguish a false awakening from later narrative reconstruction?"],
        [doi_source("10.5664/jcsm.9056", "primary-polysomnographic-case-series"), doi_source("10.3390/jcm12123876", "authoritative-clinical-review")],
        ["false awakening", "dreaming", "REM", "state misidentification"]),
    spec(
        "states-clinical-019-local-sleep", "Local Sleep", ["local sleep theory", "regional sleep", "local sleep intrusions"],
        "Model or framework", "Sleep and wakefulness / local brain states", "Systems neuroscience / sleep homeostasis", 2011,
        ["Vladyslav V. Vyazovskiy", "Umberto Olcese", "Giulio Tononi"],
        "Local-sleep research shows that neuronal populations can enter OFF-period and slow-wave-like dynamics while the organism remains behaviorally awake, making sleep-wake organization regionally heterogeneous rather than obligatorily global.",
        "Regional sleep-like neuronal dynamics and their intrusion into behavioral wakefulness.", "Cellular, circuit, EEG, and behavioral sleep neuroscience.",
        ["Intracortical recordings demonstrated local OFF periods in sleep-deprived awake rats linked to performance errors.", "A systems review synthesizes local sleep across invasive, EEG, and human evidence."],
        ["Definitions and spatial scales differ across cellular, EEG, and imaging studies.", "Regional sleep-like activity does not establish regional phenomenal absence."],
        "Local sleep is a physiological state model, not evidence that each cortical region is a separate conscious subject and not equivalent to whole-organism sleep.",
        ["What spatial scale makes a local event behaviorally consequential?", "How do local sleep intrusions alter conscious content versus performance alone?"],
        [doi_source("10.1038/nature10009", "primary-neurophysiological-study"), doi_source("10.1016/j.conb.2017.05.008", "authoritative-review")],
        ["local sleep", "OFF period", "sleep deprivation", "regional state"]),
    spec(
        "states-clinical-020-sleep-inertia", "Sleep Inertia", ["post-sleep inertia", "sleep drunkenness"],
        "Clinical / state model", "Sleep and wakefulness / state transition", "Sleep medicine / cognitive performance", 1976,
        ["Patrizia Tassi", "Alain Muzet"],
        "Sleep inertia is the transient impairment in alertness, cognition, mood, and performance immediately after awakening, with magnitude shaped by sleep stage, circadian phase, sleep debt, and task.",
        "Time-dependent cognitive and behavioral impairment during the transition from sleep to stable wakefulness.", "Sleep physiology, chronobiology, and performance measurement.",
        ["Experimental studies measure slowed reaction, decision, memory, and vigilance after scheduled or abrupt awakening.", "A dedicated review integrates sleep-stage, circadian, and sleep-deprivation determinants."],
        ["Duration and magnitude vary substantially across tasks and protocols.", "Subjective alertness and objective performance can dissociate."],
        "Sleep inertia is a transitional performance and arousal construct; it does not mean the person remains globally unconscious after behavioral awakening.",
        ["Which biomarkers predict severe individual impairment?", "How do conscious clarity, metacognitive calibration, and task performance recover at different rates?"],
        [doi_source("10.1053/smrv.2000.0098", "authoritative-review"), doi_source("10.1016/j.smrv.2016.08.005", "authoritative-clinical-review")],
        ["sleep inertia", "awakening", "alertness", "performance"]),
    spec(
        "states-clinical-021-microsleep", "Microsleep Episodes", ["microsleeps", "microsleep events", "behavioral microsleep"],
        "Clinical / state model", "Sleep and wakefulness / brief lapses", "Sleep medicine / vigilance neuroscience", 1963,
        ["Roger Broughton", "Thomas P. Poudel", "Kurtulus Izzetoglu"],
        "Microsleeps are brief, involuntary episodes of sleep-like physiology or behavioral disengagement during intended wakefulness, often associated with prolonged eye closure, vigilance failure, and increased accident risk.",
        "Brief sleep-like intrusions and lapses during nominal wakefulness.", "EEG, eye behavior, vigilance performance, and applied fatigue monitoring.",
        ["Laboratory and operational studies relate short EEG- and eye-defined events to attentional lapses.", "Recent reviews evaluate inconsistent duration thresholds and multimodal detection approaches."],
        ["Definitions range from behavioral eye closure to EEG-scored sleep and are not interchangeable.", "A missed response can have nonsleep causes."],
        "Microsleep is an operational family of brief state events; no single duration threshold or outward sign proves momentary absence of experience.",
        ["Can consensus criteria integrate EEG, ocular, and behavioral evidence?", "What conscious contents, if any, occur in brief local versus global microsleeps?"],
        [doi_source("10.1016/j.smrv.2025.102113", "systematic-review"), doi_source("10.1016/j.neuroimage.2018.03.031", "primary-multimodal-study")],
        ["microsleep", "vigilance lapse", "fatigue", "EEG"]),
    spec(
        "states-clinical-022-nrem-dreaming", "Non-REM Dreaming", ["NREM dreaming", "dreaming outside REM", "non-rapid-eye-movement dreaming"],
        "Clinical / state model", "Sleep and dreaming / conscious contents", "Cognitive neuroscience of dreaming", 1957,
        ["Francesca Siclari", "Giulio Tononi", "Mark Solms"],
        "Non-REM dreaming denotes reportable perceptual, cognitive, or affective experience arising during NREM sleep, challenging any simple identification of dreaming with REM physiology.",
        "Occurrence, content, and neural correlates of reported experience during NREM sleep.", "Serial awakening, high-density EEG, lesion, and phenomenological dream research.",
        ["Serial awakening studies obtain dream reports from NREM as well as REM sleep.", "High-density EEG work associated NREM dream reports with local posterior low-frequency reductions and high-frequency increases."],
        ["Retrospective reports depend on memory and awakening procedure.", "NREM stage labels encompass heterogeneous local brain dynamics."],
        "NREM dreaming is evidence that sleep stage and experience do not map one-to-one; a report does not show continuous awareness throughout the sampled epoch.",
        ["What is the temporal window represented in an awakening report?", "Which neural differences track experience rather than later encoding and report?"],
        [doi_source("10.1038/nn.4545", "primary-high-density-EEG-study"), doi_source("10.1016/j.tics.2009.12.001", "authoritative-theoretical-review")],
        ["NREM dreaming", "dream report", "posterior hot zone", "sleep experience"]),
    spec(
        "states-clinical-023-lucid-signal", "Signal-Verified Lucid Dream Paradigm", ["lucid-dream eye signaling", "prearranged eye-movement signaling", "LRLR signal"],
        "Model or framework", "Sleep and dreaming / experimental method", "Psychophysiology / lucid-dream verification", 1981,
        ["Keith M. T. Hearne", "Stephen LaBerge"],
        "Lucid dreamers use a prearranged sequence of left-right eye movements, visible in the electro-oculogram during REM sleep, to time-stamp recognition of dreaming and sometimes communicate task events from within the dream.",
        "Prospective physiological verification and temporal marking of lucid awareness during REM sleep.", "Polysomnography, electro-oculography, and instructed within-dream behavior.",
        ["Independent early studies demonstrated volitional eye signals during polysomnographically verified REM sleep.", "Later multisite work used signal-verified lucid dreams for real-time bidirectional communication."],
        ["Successful signaling requires rare trained participants and may select atypical lucid episodes.", "EOG patterns require controls against spontaneous REMs and partial arousal."],
        "The paradigm verifies instructed communication during some lucid dreams; it is not a scale of lucidity, proof that all lucid reports are accurate, or a theory of dreaming.",
        ["How can signal verification be made scalable and artifact-resistant?", "Which tasks can be performed without destabilizing REM sleep?"],
        [doi_source("10.2466/pms.1981.52.3.727", "primary-independent-demonstration"), doi_source("10.1016/j.cub.2021.01.026", "multisite-primary-study")],
        ["lucid dreaming", "eye signaling", "REM", "real-time communication"]),

    # Psychedelic and altered-state psychometrics
    spec(
        "states-clinical-024-apz-asc", "APZ–5D-ASC–11D-ASC Questionnaire Family", ["APZ", "5D-ASC", "5D-ASC scale", "11D-ASC", "Altered States of Consciousness Rating Scale"],
        "Model or framework", "Altered states / multidimensional assessment", "Psychometrics / experimental altered states", 1975,
        ["Adolf Dittrich", "Etzel Cardeña", "Felix Hasler"],
        "The APZ lineage operationalizes altered-state phenomenology through recurring dimensions such as oceanic boundlessness, anxious ego dissolution, visionary restructuralization, auditory alteration, and vigilance reduction; later factor work subdivides these domains.",
        "Retrospective multidimensional profiling of experiences induced by psychedelics, meditation, sensory manipulation, and other altered-state procedures.", "Self-report psychometrics and cross-condition factor analysis.",
        ["The APZ and 5D-ASC were developed through cross-etiological psychometric work.", "A large pooled factor analysis proposed eleven lower-order factors within core OAV dimensions."],
        ["Retrospective ratings are sensitive to translation, set, setting, timing, and item interpretation.", "Factor structure and score comparability vary across substances and populations."],
        "This is a questionnaire family and descriptive taxonomy, not a causal model of altered consciousness and not evidence that differently induced states share one mechanism.",
        ["Which factor solution replicates across cultures and induction methods?", "How should overlapping scale versions be harmonized without erasing item-level differences?"],
        [doi_source("10.1055/s-2007-979351", "primary-instrument-development"), doi_source("10.1371/journal.pone.0012412", "large-factor-analysis")],
        ["APZ", "5D-ASC", "11D-ASC", "altered states"]),
    spec(
        "states-clinical-025-hrs", "Hallucinogen Rating Scale", ["HRS", "Hallucinogen Rating Scale questionnaire"],
        "Model or framework", "Psychedelic states / subjective effects", "Psychopharmacology / self-report measurement", 1994,
        ["Rick J. Strassman", "Clifford R. Qualls", "Eberhard H. Uhlenhuth", "Robert Kellner"],
        "The HRS rates somesthesia, affect, perception, cognition, volition, and intensity to characterize acute hallucinogen effects, originally in controlled N,N-dimethyltryptamine studies.",
        "Multidomain retrospective assessment of acute hallucinogen subjective effects.", "Controlled psychopharmacology and self-report psychometrics.",
        ["The original dose-response study introduced the rating dimensions in controlled DMT administration.", "A later psychometric evaluation tested reliability and validity in hallucinogen-experienced volunteers."],
        ["Items were developed around a specific drug and research context.", "Retrospective intensity ratings do not establish neural mechanisms or clinical benefit."],
        "HRS profiles reported acute effects; it is not a diagnostic instrument, a universal map of altered states, or a causal psychedelic theory.",
        ["Which domains remain measurement-invariant across compounds and settings?", "How should physiological intensity be separated from phenomenological novelty?"],
        [doi_source("10.1001/archpsyc.1994.03950020009001", "primary-instrument-and-dose-study"), doi_source("10.1016/S0376-8716(00)00175-7", "psychometric-validation")],
        ["HRS", "DMT", "hallucinogen", "subjective effects"]),
    spec(
        "states-clinical-026-meq30", "Mystical Experience Questionnaire–30", ["MEQ30", "30-item Mystical Experience Questionnaire"],
        "Model or framework", "Psychedelic and contemplative states / psychometrics", "Psychology of religion / psychopharmacology", 2012,
        ["Walter N. Pahnke", "Ralph W. Hood Jr.", "Katherine A. MacLean", "Frederick S. Barrett", "Roland R. Griffiths"],
        "MEQ30 is a 30-item measure of retrospectively reported mystical-type experience organized around mystical qualities, positive mood, transcendence of time and space, and ineffability.",
        "Factor-based assessment of mystical-type phenomenology in experimental and naturalistic contexts.", "Self-report psychometrics in psychology of religion and psychedelic studies.",
        ["Factor analyses reduced and validated a four-factor 30-item form using experimental psilocybin data.", "Systematic psychometric review compares MEQ variants with other altered-state instruments."],
        ["The label 'complete mystical experience' depends on threshold conventions.", "Endorsement can be shaped by expectations, language, culture, and retrospective meaning-making."],
        "MEQ30 measures a specified report pattern; it does not authenticate metaphysical interpretations, prove therapeutic causality, or exhaust contemplative experience.",
        ["How invariant are its factors outside Western psychedelic research?", "Which outcomes are predicted beyond expectancy and global intensity?"],
        [doi_source("10.1111/j.1468-5906.2012.01685.x", "primary-factor-validation"), doi_source("10.1080/02791072.2022.2079108", "systematic-psychometric-review")],
        ["MEQ30", "mystical experience", "ineffability", "psychedelic psychometrics"]),
    spec(
        "states-clinical-027-edi", "Ego-Dissolution Inventory", ["EDI", "Ego Dissolution Inventory"],
        "Model or framework", "Psychedelic states / self-experience", "Psychopharmacology / self-report psychometrics", 2016,
        ["Matthew M. Nour", "Lisa Evans", "David Nutt", "Robin L. Carhart-Harris"],
        "The EDI is an eight-item self-report scale designed to quantify the felt weakening or loss of boundaries and unity of the ordinary self during psychedelic experience.",
        "Brief retrospective measurement of acute ego-dissolution phenomenology.", "Online and laboratory self-report psychometrics.",
        ["The development study assessed internal consistency, construct validity, and dose-related psychedelic effects.", "A systematic review evaluates its use among validated altered-state questionnaires."],
        ["A unitary score compresses distinguishable changes in body, agency, narrative self, and self-world boundary.", "Demand characteristics and global drug intensity can inflate associations."],
        "EDI measures endorsed ego-dissolution phenomenology; it does not show that the self literally ceases to exist or identify the neural cause of the experience.",
        ["Can self-dimensions be separated without sacrificing brevity?", "Which prospective measures distinguish ego dissolution from confusion or depersonalization?"],
        [doi_source("10.3389/fnhum.2016.00269", "primary-scale-development"), doi_source("10.1080/02791072.2022.2079108", "systematic-psychometric-review")],
        ["EDI", "ego dissolution", "self boundaries", "psychedelics"]),
    spec(
        "states-clinical-028-ceq", "Challenging Experience Questionnaire", ["CEQ", "Challenging Experience Questionnaire for psychedelics"],
        "Model or framework", "Psychedelic states / difficult experiences", "Psychopharmacology / adverse-experience psychometrics", 2017,
        ["Frederick S. Barrett", "Matthew W. Bradstreet", "Jeannie-Marie Leoutsakos", "Matthew B. Johnson", "Roland R. Griffiths"],
        "The CEQ quantifies acute psychedelic challenges across fear, grief, physical distress, insanity, isolation, death, and paranoia factors.",
        "Retrospective multidimensional measurement of difficult or aversive psychedelic experiences.", "Self-report psychometrics in controlled and naturalistic psychedelic use.",
        ["The validation study derived a seven-factor structure from large survey data and examined convergent associations.", "Systematic review places CEQ within the broader psychometric instrument landscape."],
        ["Survey samples are self-selected and retrospective.", "High challenge scores do not by themselves distinguish transient difficulty, clinical harm, or later benefit."],
        "CEQ describes difficult experience dimensions; it is not a safety diagnosis, a predictor of outcome on its own, or a mechanism of psychedelic action.",
        ["Which scores predict enduring impairment rather than intense but resolved difficulty?", "How do preparation and support alter factor interpretation across settings?"],
        [doi_source("10.1177/0269881116678781", "primary-scale-validation"), doi_source("10.1080/02791072.2022.2079108", "systematic-psychometric-review")],
        ["CEQ", "challenging experience", "fear", "psychedelic safety"]),
    spec(
        "states-clinical-029-ebi", "Emotional Breakthrough Inventory", ["EBI", "Emotional Breakthrough Inventory scale"],
        "Model or framework", "Psychedelic states / emotional process", "Clinical psychopharmacology / process measurement", 2019,
        ["Leor Roseman", "David J. Nutt", "Robin L. Carhart-Harris"],
        "The EBI is a six-item retrospective scale for experiences of confronting and resolving emotionally difficult material during psychedelic sessions.",
        "Brief measurement of subjectively reported emotional breakthrough during psychedelic experience.", "Clinical and naturalistic psychedelic self-report research.",
        ["The development study reported factor structure, reliability, and associations with well-being change.", "Psychometric review evaluates the EBI alongside acute and subacute psychedelic measures."],
        ["Outcome associations are observational and vulnerable to expectancy and common-method variance.", "The scale may blend acute appraisal with a later therapeutic narrative."],
        "EBI is a process self-report and does not prove that breakthrough caused improvement, that distress was therapeutically necessary, or that a memory was historically accurate.",
        ["Can temporally dense ratings separate acute process from retrospective reconstruction?", "Does EBI add predictive value beyond intensity, alliance, and expectancy?"],
        [doi_source("10.1177/0269881119855974", "primary-scale-development"), doi_source("10.1080/02791072.2022.2079108", "systematic-psychometric-review")],
        ["EBI", "emotional breakthrough", "psychedelic therapy", "process measure"]),
    spec(
        "states-clinical-030-asdb", "Altered States Database", ["ASDB", "Altered States Database resource"],
        "Model or framework", "Altered states / evidence infrastructure", "Open science / psychometric meta-data", 2022,
        ["Felix G. Gärtner", "Timo Schmitz", "Henrik Jungaberle", "Milan Scheidegger"],
        "The Altered States Database standardizes and aggregates questionnaire data from diverse pharmacological and nonpharmacological induction methods to enable profile comparison at scale.",
        "Curated comparative infrastructure for questionnaire-defined altered-state profiles across induction methods.", "Secondary data harmonization, psychometric mapping, and open data science.",
        ["The data descriptor documents source selection, scale harmonization, and machine-readable profile construction.", "A systematic review independently maps the strengths and limitations of the questionnaires on which the database depends."],
        ["Comparability inherits heterogeneity in samples, translations, doses, settings, and instrument versions.", "Shared questionnaire profiles do not establish shared neural mechanisms."],
        "ASDB is a research data resource and descriptive comparison layer, not a theory, clinical norm, or proof that altered states form natural kinds.",
        ["How should item-level uncertainty and missingness propagate into profile comparisons?", "Can prospective harmonized studies validate similarities suggested by legacy data?"],
        [doi_source("10.1038/s41597-022-01822-4", "primary-data-descriptor"), doi_source("10.1080/02791072.2022.2079108", "systematic-psychometric-review")],
        ["ASDB", "altered states", "open data", "questionnaire profiles"]),
])

SPECS.extend([
    # Developmental and comparative consciousness paradigms and positions
    spec(
        "states-clinical-045-voe", "Violation-of-Expectation Paradigm", ["VoE paradigm", "violation of expectation method", "looking-time violation paradigm"],
        "Model or framework", "Developmental cognition / infant assessment", "Developmental psychology / looking-time methods", 1985,
        ["Renée Baillargeon", "Elizabeth S. Spelke", "Stanley Wasserman"],
        "After familiarization or habituation, infants' looking at physically or psychologically possible and impossible events is compared; longer looking at an unexpected event is used to test discriminating expectations.",
        "Nonverbal inference about infants' event discrimination and expectations from differential looking.", "Developmental behavioral experimentation.",
        ["Foundational drawbridge experiments used looking-time differences to test early object permanence and physical expectation.", "A recent methodological review analyzes inferential logic, replication, and competing explanations in violation-of-expectation research."],
        ["Looking differences can reflect novelty, familiarity, perceptual salience, processing difficulty, or experimenter effects.", "The paradigm often underdetermines the representational content causing the response."],
        "VoE is an experimental inference paradigm, not a direct measure of infant phenomenal consciousness and not proof that infants possess adult-like concepts.",
        ["Which preregistered controls discriminate expectation violation from perceptual novelty?", "How can individual-level reliability be improved?"],
        [doi_source("10.1016/0010-0277(85)90008-3", "primary-paradigm-study"), doi_source("10.1037/rev0000450", "authoritative-methodological-review")],
        ["violation of expectation", "infant cognition", "looking time", "object permanence"]),
    spec(
        "states-clinical-046-vpc", "Visual Paired-Comparison Paradigm", ["VPC", "visual paired comparison", "novelty-preference paradigm", "preferential looking"],
        "Model or framework", "Developmental cognition / infant assessment", "Developmental psychobiology / recognition-memory methods", 1964,
        ["Robert L. Fantz"],
        "After familiarization with a visual stimulus, an infant is shown the familiar item beside a novel one; relative looking is used to infer discrimination, recognition memory, and processing dynamics.",
        "Nonverbal assessment of infant visual discrimination and recognition through relative looking preference.", "Developmental behavioral and eye-tracking methodology.",
        ["Fantz's foundational work established preferential looking as a method for studying infant visual experience.", "Large-scale meta-analysis quantifies infant novelty preference and moderators across many studies."],
        ["Novelty and familiarity preferences reverse with exposure duration, age, stimulus complexity, and processing speed.", "Group-level effects may have modest individual reliability."],
        "VPC indexes relative visual preference after familiarization; it is not direct evidence of conscious recognition and not a unitary measure of intelligence.",
        ["Which adaptive familiarization rules maximize interpretable individual differences?", "How do gaze preferences map to recognition without verbal report?"],
        [doi_source("10.1126/science.146.3644.668", "primary-method-demonstration"), doi_source("10.1038/s41562-024-01965-x", "large-meta-analysis")],
        ["visual paired comparison", "preferential looking", "novelty preference", "infant recognition"]),
    spec(
        "states-clinical-047-infant-late-response", "Infant Late Slow-Wave Conscious-Access Marker", ["infant late slow wave", "infant P3-like conscious-access response", "infant late ERP marker"],
        "Model or framework", "Developmental consciousness / neural assessment", "Developmental cognitive neuroscience / EEG", 2013,
        ["Sid Kouider", "Caroline Stahlhut", "Sofie V. Gelskov", "Leonardo S. Barbosa", "Michel Dutat", "Véronique de Gardelle", "Stanislas Dehaene"],
        "A late, nonlinear event-related potential following briefly presented faces has been proposed as an infant analogue of later cortical responses associated with conscious access in adults, with latency decreasing across development.",
        "Candidate electrophysiological marker of late perceptual processing and possible conscious access in preverbal infants.", "Infant EEG and masked-stimulus psychophysics.",
        ["The defining infant EEG study reported a delayed nonlinear slow-wave response across age groups.", "Developmental consciousness reviews situate such late responses among indirect behavioral and neural evidence."],
        ["The adult interpretation of late potentials remains contested and may include report, decision, attention, or memory processes.", "An infant homology does not establish the infant's phenomenal content."],
        "The late slow wave is a candidate neural marker, not direct proof of consciousness, a maturity threshold, or evidence that infant and adult experience are identical.",
        ["Which infant paradigms separate access from attention and expectation?", "Can convergent autonomic or behavioral measures validate trial-level interpretation?"],
        [doi_source("10.1126/science.1232509", "primary-infant-EEG-study"), doi_source("10.1203/PDR.0b013e3181973b0d", "authoritative-developmental-review")],
        ["infant consciousness", "late slow wave", "ERP", "conscious access"]),
    spec(
        "states-clinical-048-ny-declaration", "New York Declaration on Animal Consciousness", ["NY Declaration on Animal Consciousness", "NYDAC"],
        "Argument / challenge", "Comparative consciousness / evidential policy", "Animal consciousness science / precautionary ethics", 2024,
        ["Kristin Andrews", "Jonathan Birch", "Jeff Sebo", "Taylor Sims"],
        "The declaration states that there is strong scientific support for conscious experience in mammals and birds, a realistic possibility in all vertebrates and many invertebrates, and that decision-makers should not ignore a realistic possibility of animal consciousness.",
        "Evidence-calibrated consensus statement and precautionary decision principle for a broad range of nonhuman animals.", "Interdisciplinary expert statement grounded in comparative behavioral and neural evidence.",
        ["The signed declaration states differentiated evidential claims rather than one undifferentiated assertion about all animals.", "Its official background document summarizes research programs and the intended meaning of 'realistic possibility.'"],
        ["A declaration is not a systematic review or species-by-species adjudication.", "Signatory agreement does not settle the tests or theory of consciousness."],
        "This is a consensus and policy argument, not a biological mechanism, a claim that all animals are equally conscious, or a diagnostic test for any individual species.",
        ["How should 'realistic possibility' be operationalized in species-specific decisions?", "Which comparative evidence would materially raise or lower confidence for understudied taxa?"],
        [manual_source("ny-declaration"), manual_source("ny-background")],
        ["New York Declaration", "animal consciousness", "precaution", "comparative evidence"],
        status="expert declaration · evidential scope explicitly graded",
        status_note="The declaration is an attributable expert statement; its three propositions should be retained separately and not inflated into unanimity or proof."),
    spec(
        "states-clinical-049-cambridge-declaration", "Cambridge Declaration on Consciousness", ["Cambridge Declaration", "Cambridge Declaration on Consciousness in Human and non-Human Animals"],
        "Argument / challenge", "Comparative consciousness / neuroscience", "Comparative neuroscience / expert declaration", 2012,
        ["Philip Low", "Jaak Panksepp", "Diana Reiss", "David Edelman", "Bruno Van Swinderen", "Christof Koch"],
        "The declaration argues that convergent neuroanatomical, neurochemical, and neurophysiological evidence shows that a human neocortex is not required for affective states and that humans are not unique in possessing neurological substrates associated with consciousness.",
        "Expert evidential statement about nonhuman neural substrates and the cross-species distribution of consciousness-relevant capacities.", "Comparative affective and systems neuroscience.",
        ["The conference declaration provides the original signed wording and evidential framing.", "Peer-reviewed comparative-consciousness scholarship discusses the declaration in relation to multidimensional animal evidence."],
        ["The declaration does not specify necessary or sufficient neural criteria for consciousness.", "Its broad taxonomic wording does not adjudicate each species or experience dimension."],
        "This is an expert declaration, not a formal theory or species-level diagnostic instrument; 'substrates' must not be restated as proof of identical human-like experience.",
        ["Which neural and behavioral criteria best support species-specific inferences?", "How should new invertebrate evidence update the declaration's original scope?"],
        [manual_source("cambridge-declaration"), doi_source("10.1016/j.tics.2020.07.007", "authoritative-comparative-framework")],
        ["Cambridge Declaration", "animal consciousness", "neural substrates", "comparative neuroscience"],
        status="expert declaration · historically influential · scope debated",
        status_note="The document records a 2012 expert position and is not represented as a formal vote, a universal scientific consensus, or a species inventory."),
    spec(
        "states-clinical-050-judgement-bias", "Judgement-Bias Paradigm for Animal Affect", ["judgment bias task", "cognitive bias test", "ambiguous-cue judgement bias"],
        "Model or framework", "Comparative consciousness / affect assessment", "Animal welfare science / affective cognition", 2004,
        ["Emma J. Harding", "Elizabeth S. Paul", "Michael Mendl"],
        "Animals learn that cues predict positive or negative outcomes and are then tested with ambiguous cues; relatively optimistic or pessimistic responses are used as indicators of affect-related cognitive bias.",
        "Nonverbal assessment of affect-linked interpretation of ambiguity in nonhuman animals.", "Comparative learning, decision behavior, and animal-welfare experimentation.",
        ["The foundational rat study showed housing-related changes in responses to ambiguous cues.", "A methodological review synthesizes task designs, affect manipulations, and interpretation limits."],
        ["Responses reflect learning, motivation, arousal, reinforcement history, and sensory generalization as well as affect.", "Task variants have heterogeneous reliability and may not isolate valence."],
        "Judgement bias is an indirect behavioral indicator of affective state, not a direct report of felt emotion and not sufficient alone to establish sentience.",
        ["Which designs best separate affect from generalization and reward valuation?", "Can individual-level reliability support welfare monitoring?"],
        [doi_source("10.1038/427312a", "primary-paradigm-study"), doi_source("10.1016/j.applanim.2009.02.023", "authoritative-methodological-review")],
        ["judgement bias", "animal affect", "ambiguous cue", "welfare"]),
    spec(
        "states-clinical-051-motivational-tradeoff", "Motivational Trade-Off Paradigm for Animal Sentience", ["motivational tradeoff", "motivational trade-off test", "pain trade-off paradigm"],
        "Model or framework", "Comparative consciousness / pain assessment", "Animal welfare science / motivational analysis", 2009,
        ["Robert W. Elwood", "Stuart Barr", "Lynsey Patterson"],
        "The paradigm tests whether an animal flexibly weighs avoiding a noxious stimulus against competing goals such as shelter, resource value, or predation risk, seeking behavior beyond a fixed reflex.",
        "Behavioral assessment of flexible motivational prioritization following potentially painful stimulation.", "Comparative behavior, learning, and welfare experimentation.",
        ["Foundational hermit-crab experiments tested shock-driven evacuation against shell quality and predator cues.", "Subsequent decapod studies evaluated discrimination and longer-term motivational change after shock."],
        ["Complex trade-offs can arise without phenomenal pain and require controls for sensitization and motor effects.", "Species ecology and resource value strongly condition behavior."],
        "Motivational trade-off is one evidential criterion for pain-like experience, not a standalone proof of sentience or a claim that all avoidance is conscious.",
        ["Which convergent criteria most strongly distinguish flexible valuation from nociceptive control?", "How should ecological validity and laboratory standardization be balanced?"],
        [doi_source("10.1016/j.applanim.2009.03.013", "primary-paradigm-study"), doi_source("10.1242/jeb.072041", "primary-independent-extension")],
        ["motivational trade-off", "animal pain", "decapod", "sentience criterion"]),

    # Neural and behavioral consciousness-measurement paradigms
    spec(
        "states-clinical-052-lzc", "Lempel–Ziv EEG Complexity", ["LZc", "Lempel-Ziv complexity of consciousness", "EEG Lempel–Ziv complexity"],
        "Model or framework", "Consciousness measurement / signal complexity", "Computational neurophysiology / EEG and MEG", 2015,
        ["Michael M. Schartner", "Adam B. Barrett", "Anil K. Seth", "Carhart-Harris Research Group"],
        "LZc binarizes neural time series and measures the compressibility of resulting spatiotemporal patterns, with applications comparing wakefulness, sleep, anesthesia, psychedelic states, and disorders of consciousness.",
        "Algorithmic diversity or compressibility of recorded neural dynamics across conscious-state conditions.", "EEG, MEG, intracranial recording, and information-theoretic signal analysis.",
        ["Multistate studies reported reduced spontaneous complexity in low-consciousness conditions.", "Psychedelic MEG work reported increased signal diversity relative to ordinary wakefulness."],
        ["LZc depends on preprocessing, binarization, data length, noise, spectral content, and sensor number.", "High complexity can reflect noise and is not monotonically equivalent to richer experience."],
        "LZc is a signal statistic and candidate state marker, not a theory that consciousness is compression complexity and not sufficient for individual diagnosis.",
        ["Which normalization makes values comparable across devices and populations?", "How can structured complexity be separated from stochastic noise?"],
        [doi_source("10.1371/journal.pone.0133532", "primary-multistate-study"), doi_source("10.1038/srep46421", "primary-psychedelic-study")],
        ["LZc", "Lempel-Ziv complexity", "EEG", "signal diversity"]),
    spec(
        "states-clinical-053-wsmi", "Weighted Symbolic Mutual Information", ["wSMI", "weighted symbolic mutual information"],
        "Model or framework", "Consciousness measurement / functional connectivity", "Computational neurophysiology / EEG", 2013,
        ["Jean-Rémi King", "Jacobo D. Sitt", "F. Faugeras", "B. Rohaut", "Stanislas Dehaene"],
        "wSMI estimates shared information between symbolized EEG signals while down-weighting identical and opposite symbol pairs to reduce common-source artifacts, and has been used to index long-range information sharing in impaired consciousness.",
        "Artifact-resistant estimation of distributed statistical dependence in EEG as a candidate marker of conscious state.", "Scalp EEG and symbolic information-theoretic connectivity.",
        ["The defining study related wSMI to consciousness in controls and noncommunicating patients.", "A large bedside study compared wSMI with other EEG markers for diagnosis and outcome prediction."],
        ["Volume conduction and source mixing are reduced but not eliminated.", "Connectivity estimates depend on symbol parameters, frequency content, vigilance, and artifact rejection."],
        "wSMI is an EEG connectivity statistic, not direct evidence of information integration as experience and not an individual diagnostic verdict in isolation.",
        ["Which parameter settings generalize prospectively across centers?", "How much does wSMI add beyond spectral and complexity features?"],
        [doi_source("10.1016/j.cub.2013.07.075", "primary-method-and-clinical-study"), doi_source("10.1093/brain/awu141", "large-clinical-validation")],
        ["wSMI", "symbolic mutual information", "EEG connectivity", "disorders of consciousness"]),
    spec(
        "states-clinical-054-local-global", "Local–Global Auditory Paradigm", ["local-global paradigm", "local global auditory oddball", "Local-Global effect"],
        "Model or framework", "Conscious access / auditory assessment", "Cognitive neuroscience / hierarchical auditory prediction", 2009,
        ["Tristan A. Bekinschtein", "Stanislas Dehaene", "Bertrand Rohaut", "Lionel Naccache"],
        "Sequences contain short-range local regularities and longer-range global regularities; neural responses to global violations, especially late responses, are used to test access to relations spanning multiple stimuli.",
        "Auditory EEG assessment of local deviance processing versus access to temporally extended global regularities.", "Event-related potentials, EEG, and disorders-of-consciousness bedside testing.",
        ["The original study contrasted local and global violations across wakefulness, sleep, and patients.", "A large clinical EEG study evaluated this and other active/passive markers in DoC diagnosis and prognosis."],
        ["Late global effects can depend on attention, working memory, learning, and residual hearing.", "Absence of a response is vulnerable to low trial counts, noise, and fluctuating arousal."],
        "The local–global paradigm probes hierarchical auditory processing; a global effect is not a complete consciousness measure, and its absence does not prove no experience.",
        ["Which response features remain informative without active counting?", "How many sessions are required to address state fluctuation and low signal-to-noise?"],
        [doi_source("10.1073/pnas.0809667106", "primary-paradigm-study"), doi_source("10.1093/brain/awu141", "large-clinical-validation")],
        ["local-global", "auditory oddball", "global deviance", "conscious access"]),
    spec(
        "states-clinical-055-fmri-command-following", "fMRI Motor-Imagery Command-Following Paradigm", ["tennis imagery paradigm", "spatial navigation imagery", "fMRI command following", "mental-imagery communication"],
        "Model or framework", "Disorders of consciousness / covert command following", "Cognitive neuroimaging / clinical assessment", 2006,
        ["Adrian M. Owen", "Martin R. Coleman", "Melanie Boly", "Matthew H. Davis", "Steven Laureys", "John D. Pickard"],
        "Patients are instructed to imagine motor activity such as playing tennis or spatial navigation such as moving through a home; task-specific fMRI activation can demonstrate willful command following without overt movement.",
        "Detection of covert voluntary command following and, in some cases, binary communication in behaviorally nonresponsive patients.", "Task-based functional MRI and mental imagery.",
        ["The initial case study demonstrated instruction-specific activation in a patient diagnosed as vegetative.", "A later cohort study tested prevalence and used imagery responses for yes-no communication in one patient."],
        ["Negative results can reflect hearing, language, working memory, attention, scanner tolerance, motion, or task inability.", "Positive classification requires stringent individual statistics and does not reveal the full range of experience."],
        "The paradigm demonstrates covert command following when positive; it is not a universal consciousness detector, and a negative scan does not establish unconsciousness.",
        ["Which tasks maximize sensitivity across cognitive and motor-imagery impairments?", "How should single-patient false-positive and false-negative rates be calibrated clinically?"],
        [doi_source("10.1126/science.1130197", "primary-case-demonstration"), doi_source("10.1056/NEJMoa0905370", "primary-cohort-and-communication-study")],
        ["fMRI command following", "motor imagery", "covert awareness", "cognitive motor dissociation"]),
    spec(
        "states-clinical-056-no-report", "No-Report Paradigm Family", ["no-report paradigms", "no-report methodology", "report-free consciousness paradigm"],
        "Model or framework", "Consciousness measurement / experimental design", "Cognitive neuroscience / report-confound control", 2015,
        ["Naotsugu Tsuchiya", "Melanie Wilke", "Stefan Frässle", "Victor A. F. Lamme"],
        "No-report paradigms infer changes in perceptual experience from eye movements, optokinetic nystagmus, pupil responses, reflexes, or task-independent neural signals while minimizing explicit trial-by-trial reports.",
        "Experimental separation of candidate neural correlates of experience from processes required for overt report.", "Visual psychophysics, oculomotor and autonomic measurement, and neuroimaging.",
        ["The programmatic paper defined no-report approaches and surveyed paradigms for rivalry and perception.", "Methodological critiques analyze residual inference, attention, and validation requirements."],
        ["A proxy must first be calibrated against report, and may track stimulus or attention rather than experience.", "Removing trial-wise report does not remove all cognition, task set, or postperceptual processing."],
        "No-report names a design family, not a literal absence of all report or inference, and it does not by itself select among theories of consciousness.",
        ["How can proxies be validated without circular reliance on report?", "Which candidate neural correlates survive matched covert-task and no-task controls?"],
        [doi_source("10.1016/j.tics.2015.10.002", "primary-programmatic-method"), doi_source("10.1016/j.tics.2019.10.001", "methodological-critique")],
        ["no-report", "neural correlates", "report confound", "perceptual inference"]),
])


def existing_terms() -> dict[str, str]:
    terms: dict[str, str] = {}
    for path in sorted(DATA_DIR.glob("catalog*.json")):
        if path.resolve() == OUTPUT.resolve():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for record in payload.get("records", []):
            record_name = str(record.get("name", ""))
            for value in [record_name, *record.get("aliases", [])]:
                key = normalize(str(value))
                if key:
                    terms[key] = f"{path.name}:{record.get('id', record_name)}"
    return terms


def audit_selection() -> None:
    if len(SPECS) < 55:
        raise RuntimeError(f"Expected at least 55 records, found {len(SPECS)}")
    external = existing_terms()
    local_terms: dict[str, str] = {}
    ids: set[str] = set()
    for item in sorted(SPECS, key=lambda entry: entry["id"]):
        if item["id"] in ids:
            raise RuntimeError(f"Duplicate id in selection: {item['id']}")
        ids.add(item["id"])
        if item["kind"] not in CANONICAL_KINDS:
            raise RuntimeError(f"Noncanonical kind on {item['id']}: {item['kind']}")
        for value in [item["name"], *item["aliases"]]:
            key = normalize(value)
            if key in external:
                raise RuntimeError(f"Catalog collision for {value!r}: {external[key]}")
            if key in local_terms and local_terms[key] != item["id"]:
                raise RuntimeError(f"Local name/alias collision for {value!r}: {local_terms[key]}")
            local_terms[key] = item["id"]


def crossref_citation(source: dict[str, str], cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
    doi = source["doi"]
    key = doi.casefold()
    if key not in cache:
        url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Noemorph research catalog/1.0 (mailto:research@example.invalid)"},
        )
        last_error: Exception | None = None
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    message = json.load(response)["message"]
                cache[key] = message
                break
            except Exception as exc:  # pragma: no cover - network retry path
                last_error = exc
                time.sleep(1.5 * (attempt + 1))
        else:
            raise RuntimeError(f"Crossref resolution failed for {doi}: {last_error}")
    message = cache[key]
    titles = message.get("title") or []
    if not titles:
        raise RuntimeError(f"Crossref returned no title for {doi}")
    authors: list[str] = []
    for author in message.get("author", []):
        name = " ".join(part for part in [author.get("given", ""), author.get("family", "")] if part).strip()
        if name:
            authors.append(name)
    date_parts = (
        message.get("published-print", {}).get("date-parts")
        or message.get("published-online", {}).get("date-parts")
        or message.get("issued", {}).get("date-parts")
        or [["n.d."]]
    )
    containers = message.get("container-title") or []
    return {
        "title": source.get("title") or clean(str(titles[0])),
        "authors": "; ".join(authors) or "Authorship recorded by Crossref",
        "year": date_parts[0][0],
        "venue": clean(str(containers[0])) if containers else "Scholarly publication",
        "doi": doi,
        "url": f"https://doi.org/{doi}",
        "authority": source["authority"],
        "verification": "doi-resolved",
        "retrieved": RETRIEVED,
    }


def build_records() -> list[dict[str, Any]]:
    cache: dict[str, dict[str, Any]] = {}
    records: list[dict[str, Any]] = []
    for item in sorted(SPECS, key=lambda entry: entry["id"]):
        record = {key: value for key, value in item.items() if key != "_sources"}
        citations: list[dict[str, Any]] = []
        for source in item["_sources"]:
            if "manual" in source:
                citations.append(dict(MANUAL_SOURCES[source["manual"]]))
            else:
                citations.append(crossref_citation(source, cache))
        if len(citations) < 2:
            raise RuntimeError(f"{record['id']} has fewer than two citations")
        locators = [str(citation.get("doi") or citation["url"]).casefold() for citation in citations]
        if len(locators) != len(set(locators)):
            raise RuntimeError(f"{record['id']} repeats a citation locator")
        record["citations"] = citations
        records.append(record)
    return records


def write_atomic(payload: dict[str, Any]) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=OUTPUT.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(OUTPUT)


def main() -> None:
    audit_selection()
    records = build_records()
    payload = {
        "collection": {
            "title": "States, clinical assessment, and consciousness-measurement breadth packet",
            "created": RETRIEVED,
            "phase": "collection-only",
            "record_count": len(records),
            "scope": "Distinct attributable state constructs, assessment instruments, experimental paradigms, psychometric frameworks, and expert evidential positions spanning disorders of consciousness, anesthesia, sleep and dreaming, psychedelic and contemplative states, interoception and metacognition, development, comparative consciousness, and neural measurement.",
            "method": "Human-curated candidate selection followed by exact name and alias collision checks against every extant catalog shard, DOI resolution against Crossref, and source-level boundary review.",
            "boundary_policy": "Every record states whether it is a state construct, assessment instrument, experimental paradigm, signal statistic, or evidential declaration; none is silently promoted to a causal or constitutive theory of consciousness.",
            "citation_policy": "Each record retains at least two exact HTTPS primary, validation, systematic-review, guideline, or official locators. DOI metadata are resolved at build time; official declarations are manually verified.",
            "attribution_policy": "Claims remain local to named authors, instruments, paradigms, and documents. No inferred compatibility, causal relationship, ranking, or synthesis is asserted.",
            "deduplication_policy": "Names and aliases are normalized and compared with catalog.json and every catalog supplement present at build time; conceptual neighbors are retained only when their target and method are independently bounded.",
            "review_state": "provisional",
            "registration": "not registered by builder",
        },
        "records": records,
    }
    write_atomic(payload)
    print(f"wrote {len(records)} records to {OUTPUT}")


SPECS.extend([
    # Mindfulness and contemplative-awareness measures
    spec(
        "states-clinical-031-maas", "Mindful Attention Awareness Scale", ["MAAS", "Mindful Attention and Awareness Scale"],
        "Model or framework", "Contemplative awareness / trait and state assessment", "Contemplative science / self-report psychometrics", 2003,
        ["Kirk Warren Brown", "Richard M. Ryan"],
        "MAAS uses items about everyday lapses of attention and awareness, reverse-scored to index a receptive attention to and awareness of present experience as a dispositional or state-like tendency.",
        "Self-reported frequency of open or receptive present-centered attention in daily life.", "Trait and state self-report psychometrics.",
        ["The development paper reported internal consistency, temporal stability, convergent evidence, and state applications.", "An independent review compares construct coverage and psychometric support across mindfulness questionnaires."],
        ["Its mostly reverse-keyed inattention items may measure absent-mindedness more directly than all facets of mindfulness.", "Self-report depends on introspective access and cultural interpretation."],
        "MAAS is an operational questionnaire, not a measure of moment-to-moment phenomenal consciousness, meditation attainment, or a causal theory of mindfulness.",
        ["What variance is specific to mindfulness rather than attention failure or conscientiousness?", "How well do state scores align with experience sampling and behavior?"],
        [doi_source("10.1037/0022-3514.84.4.822", "primary-scale-development"), doi_source("10.1007/s12671-012-0122-5", "authoritative-measure-review")],
        ["MAAS", "mindfulness", "present attention", "self-report"]),
    spec(
        "states-clinical-032-ffmq", "Five Facet Mindfulness Questionnaire", ["FFMQ", "Five-Facet Mindfulness Questionnaire"],
        "Model or framework", "Contemplative awareness / multidimensional assessment", "Clinical psychology / mindfulness psychometrics", 2006,
        ["Ruth A. Baer", "Gregory T. Smith", "Jaclyn Hopkins", "Jennifer Krietemeyer", "Leslie Toney"],
        "FFMQ integrates items from earlier instruments into observing, describing, acting with awareness, nonjudging of inner experience, and nonreactivity to inner experience facets.",
        "Multifacet self-report assessment of mindfulness-related skills and tendencies.", "Factor-analytic clinical and personality psychometrics.",
        ["The original factor analysis integrated five existing questionnaires and tested a hierarchical facet structure.", "A dedicated review evaluates mindfulness instruments' content, reliability, and validity."],
        ["Facet structure and the meaning of observing differ with meditation experience and population.", "Questionnaire overlap with emotion regulation and personality complicates specificity."],
        "FFMQ is a psychometric decomposition of reported skills, not a universal ontology of mindfulness and not proof that a high total score reflects nondual or contentless awareness.",
        ["Should a total score be used when facets relate differently to outcomes?", "Which facets show measurement invariance across cultures and meditation experience?"],
        [doi_source("10.1177/1073191105283504", "primary-scale-development"), doi_source("10.1007/s12671-012-0122-5", "authoritative-measure-review")],
        ["FFMQ", "mindfulness facets", "nonjudging", "nonreactivity"]),
    spec(
        "states-clinical-033-tms", "Toronto Mindfulness Scale", ["Toronto Mindfulness Scale (TMS)", "Toronto Mindfulness Scale state measure"],
        "Model or framework", "Contemplative awareness / state assessment", "Clinical psychology / meditation-state psychometrics", 2006,
        ["Mark A. Lau", "Shauna F. Bishop", "Zindel V. Segal", "Tom Buis", "Nicole D. Anderson"],
        "TMS assesses curiosity toward and decentering from present-moment experience immediately after meditation, treating mindfulness as a temporarily cultivated state rather than only a trait.",
        "Post-practice self-report of state curiosity and decentered awareness.", "Meditation-linked state psychometrics.",
        ["The development studies derived curiosity and decentering factors and tested construct validity.", "A comparative review evaluates TMS alongside trait and state mindfulness instruments."],
        ["Post-session reporting can reflect demand, memory, and appraisal rather than online state dynamics.", "The two factors do not exhaust contemplative phenomenology."],
        "TMS measures retrospectively endorsed qualities after practice; it does not independently verify meditation depth, contentless awareness, or neural state.",
        ["Can experience sampling validate temporal changes within a meditation session?", "How does TMS perform outside novice guided-practice contexts?"],
        [doi_source("10.1002/jclp.20326", "primary-scale-development"), doi_source("10.1007/s12671-012-0122-5", "authoritative-measure-review")],
        ["TMS", "state mindfulness", "curiosity", "decentering"]),
    spec(
        "states-clinical-034-fmi", "Freiburg Mindfulness Inventory", ["FMI", "Freiburg Mindfulness Inventory–Short Form", "FMI-14"],
        "Model or framework", "Contemplative awareness / self-report assessment", "Meditation research / clinical psychometrics", 2006,
        ["Harald Walach", "Nina Buchheld", "Valentin Buttenmüller", "Norman Kleinknecht", "Stefan Schmidt"],
        "FMI was developed to assess mindfulness-related experience in meditation practitioners; its short form is commonly used more broadly as a largely unidimensional index.",
        "Self-report assessment of mindful presence and nonjudgment, initially grounded in meditation practice.", "Contemplative and clinical self-report psychometrics.",
        ["The development paper compared long and short forms and evaluated factor structure and validity.", "An independent review assesses its content and psychometric evidence relative to other measures."],
        ["Items and factor structure behave differently in novice and experienced samples.", "Broad use beyond the population of origin risks construct drift."],
        "FMI is a questionnaire operationalization, not a doctrinal definition of mindfulness, an attainment scale, or direct access to consciousness itself.",
        ["Which form is invariant across experience levels?", "What behavioral or phenomenological observations provide independent validation?"],
        [doi_source("10.1016/j.paid.2005.11.025", "primary-scale-development"), doi_source("10.1007/s12671-012-0122-5", "authoritative-measure-review")],
        ["FMI", "mindfulness inventory", "meditation", "present awareness"]),
    spec(
        "states-clinical-035-phlms", "Philadelphia Mindfulness Scale", ["PHLMS", "Philadelphia Mindfulness Scale"],
        "Model or framework", "Contemplative awareness / self-report assessment", "Clinical psychology / acceptance-based measurement", 2008,
        ["Lee Cardaciotto", "Jason D. Herbert", "Evan M. Forman", "Eliot M. Moitra", "Vishal Farrow"],
        "PHLMS measures present-moment awareness and acceptance as two theoretically distinct components of mindfulness.",
        "Two-component self-report assessment of awareness and acceptance in clinical and nonclinical populations.", "Clinical self-report and factor-analytic psychometrics.",
        ["The original studies developed separate awareness and acceptance subscales and evaluated convergent and discriminant validity.", "A comparative review assesses its construct coverage within mindfulness measurement."],
        ["Awareness items can overlap with monitoring or hypervigilance while acceptance overlaps with emotion regulation.", "A two-factor model excludes several skills represented in other instruments."],
        "PHLMS scores two proposed components; it does not establish that mindfulness has exactly two natural dimensions or that awareness scores measure phenomenal level.",
        ["When does high awareness without acceptance predict distress rather than mindfulness?", "Do both factors remain distinct across clinical conditions and cultures?"],
        [doi_source("10.1177/1073191107311467", "primary-scale-development"), doi_source("10.1007/s12671-012-0122-5", "authoritative-measure-review")],
        ["PHLMS", "awareness", "acceptance", "mindfulness"]),
    spec(
        "states-clinical-036-nada", "Nondual Awareness Dimensional Assessment", ["NADA", "Nondual Awareness Dimensional Assessment–State", "NADA-S", "NADA-T"],
        "Model or framework", "Contemplative awareness / nondual experience", "Contemplative science / state-trait psychometrics", 2018,
        ["Adam W. Hanley", "David M. P. Garland", "Eric L. Garland"],
        "NADA provides state and trait forms intended to quantify nondual awareness, emphasizing a reported reduction in subject-object division and an open field-like quality of experience.",
        "Self-reported state and dispositional qualities associated with nondual awareness.", "Contemplative self-report psychometrics.",
        ["Scale-development studies tested factor structure, internal consistency, and associations with related constructs.", "Subsequent contemplative measurement reviews situate NADA among measures of decentering and nondual experience."],
        ["The construct draws on heterogeneous contemplative vocabularies that may not be equivalent.", "Self-report cannot by itself distinguish nondual phenomenology from endorsement, absorption, or conceptual belief."],
        "NADA operationalizes a reported phenomenological dimension; it neither verifies metaphysical nonduality nor grades lineage-specific realization.",
        ["How invariant are items across contemplative traditions and nonmeditating populations?", "Which online tasks or interviews distinguish nondual awareness from absorption and depersonalization?"],
        [doi_source("10.1037/pas0000615", "primary-scale-development"), doi_source("10.1177/21582440251403827", "independent-cross-language-validation")],
        ["NADA", "nondual awareness", "subject-object", "contemplative psychometrics"]),
    spec(
        "states-clinical-037-eq-decentering", "Experiences Questionnaire Decentering Scale", ["EQ decentering scale", "Experiences Questionnaire", "EQ-Decentering"],
        "Model or framework", "Metacognition and contemplative practice / decentering", "Clinical psychology / cognitive therapy process measurement", 2007,
        ["David M. Fresco", "Gulnara R. Moore", "M. T. van Dulmen", "Zindel V. Segal", "J. M. G. Williams", "John D. Teasdale"],
        "The EQ decentering scale assesses the reported capacity to observe thoughts and feelings as temporary mental events rather than identifying with their content.",
        "Self-report measurement of decentering as a metacognitive stance in mindfulness-based and cognitive therapies.", "Clinical process psychometrics.",
        ["The original psychometric study evaluated decentering and rumination items across patient and nonpatient samples.", "Independent validation studies test factor structure, reliability, and clinical associations in additional languages and populations."],
        ["Items overlap with cognitive defusion, reappraisal, and reduced rumination.", "Trait reports may not capture momentary decentering under stress."],
        "EQ decentering is a self-reported process construct, not evidence of contentless consciousness, loss of self, or a complete model of metacognitive awareness.",
        ["Can state-sensitive measures capture when decentering is actually deployed?", "What discriminates adaptive decentering from emotional disengagement?"],
        [doi_source("10.1016/j.beth.2006.08.003", "primary-scale-validation"), doi_source("10.1016/j.beth.2014.05.004", "independent-validation")],
        ["Experiences Questionnaire", "decentering", "metacognitive stance", "mindfulness-based therapy"]),

    # Interoception, perceptual awareness, and metacognitive measures
    spec(
        "states-clinical-038-hep", "Heartbeat-Evoked Potential", ["HEP", "heartbeat-evoked response", "HER"],
        "Model or framework", "Interoception / neurophysiological assessment", "Psychophysiology / cardiac-brain electrophysiology", 1993,
        ["Pedro Montoya", "Rainer Schandry", "Achim Müller"],
        "The heartbeat-evoked potential is an EEG or MEG response time-locked to cardiac events and used as a candidate index of cortical processing of afferent cardiac signals.",
        "Neurophysiological measurement of heartbeat-locked cortical dynamics and their modulation by attention, arousal, and interoceptive performance.", "EEG or MEG averaged relative to electrocardiographic R- or T-peaks.",
        ["The foundational study characterized HEP topography and modulation by cardiac awareness and attention.", "A systematic review and meta-analysis assessed associations with behavioral interoception, attention, arousal, and clinical status."],
        ["Cardiac field artifact, pulse artifact, reference choice, latency window, and trial count can alter the waveform.", "Meta-analytic effects remain heterogeneous and protocol standardization is limited."],
        "HEP is a heartbeat-locked neural signal and putative interoceptive marker, not a direct measure of felt bodily awareness or a global consciousness index.",
        ["Which acquisition and correction pipeline yields reliable individual differences?", "What HEP variance reflects afferent processing rather than cardiac and somatosensory artifact?"],
        [doi_source("10.1016/0168-5597(93)90001-6", "primary-method-and-study"), doi_source("10.1016/j.neubiorev.2020.12.012", "systematic-review-meta-analysis")],
        ["heartbeat-evoked potential", "HEP", "interoception", "EEG"]),
    spec(
        "states-clinical-039-heartbeat-counting", "Heartbeat Counting Task", ["Schandry heartbeat counting task", "mental tracking method", "heartbeat tracking task"],
        "Model or framework", "Interoception / behavioral assessment", "Psychophysiology / cardiac interoception", 1981,
        ["Rainer Schandry"],
        "Participants silently count perceived heartbeats during timed intervals without palpating a pulse; reported counts are compared with recorded beats as an index historically labeled cardiac interoceptive accuracy.",
        "Behavioral estimation of heartbeat-related perception under no-pulse-taking instructions.", "Cardiac psychophysiology and behavioral task measurement.",
        ["The original mental-tracking method linked heartbeat counting performance to emotional experience.", "Methodological analysis demonstrates contributions from prior heart-rate knowledge, beliefs, and scoring assumptions."],
        ["Scores can be high without sensing individual beats and are mathematically coupled to actual heart rate.", "Instructions, time estimation, and knowledge strongly affect performance."],
        "Heartbeat counting is a task score, not a pure readout of afferent sensitivity, bodily awareness generally, or conscious access to every heartbeat.",
        ["Can task variants exclude knowledge and time-estimation strategies?", "Which cardiac sensations do participants actually use?"],
        [doi_source("10.1111/j.1469-8986.1981.tb02486.x", "primary-method"), doi_source("10.1016/j.biopsycho.2018.06.006", "methodological-critique")],
        ["heartbeat counting", "mental tracking", "cardiac interoception", "task validity"]),
    spec(
        "states-clinical-040-heartbeat-discrimination", "Heartbeat Discrimination Task", ["heartbeat detection task", "Whitehead heartbeat discrimination", "heartbeat simultaneity task"],
        "Model or framework", "Interoception / psychophysical assessment", "Psychophysiology / cardiac interoception", 1977,
        ["William E. Whitehead", "Kurt Drescher"],
        "Participants judge whether external tones or lights are simultaneous with or delayed from their heartbeat, using trial-wise discrimination rather than accumulating a count.",
        "Psychophysical discrimination of externally presented signals relative to cardiac events.", "Cardiac psychophysics and signal-timing judgment.",
        ["Foundational heartbeat-discrimination experiments developed trial-wise synchrony judgments.", "The three-dimensional interoception framework uses discrimination tasks while separating performance from confidence and self-report."],
        ["Fixed delays may not match the individually perceived pulse-transit timing.", "Difficulty can reflect temporal discrimination or task learning rather than absent cardiac sensation."],
        "Heartbeat discrimination estimates performance under a particular synchrony model; it is not a direct assay of all interoceptive awareness.",
        ["How should delays be individualized to pulse transit and perceived location?", "Which signal-detection models best separate sensitivity from response bias?"],
        [doi_source("10.1111/j.1469-8986.1984.tb02934.x", "primary-psychophysical-study"), doi_source("10.1016/j.biopsycho.2014.11.004", "authoritative-construct-framework")],
        ["heartbeat discrimination", "cardiac timing", "interoception", "psychophysics"]),
    spec(
        "states-clinical-041-maia", "Multidimensional Assessment of Interoceptive Awareness", ["MAIA", "MAIA-2", "Multidimensional Assessment of Interoceptive Awareness Version 2"],
        "Model or framework", "Interoception / self-report assessment", "Mind-body medicine / psychometrics", 2012,
        ["Wolf E. Mehling", "Cynthia Price", "Jennifer J. Daubenmier", "Mike Acree", "Elizabeth Bartmess", "Anita Stewart"],
        "MAIA measures multiple reported styles of attending and responding to bodily sensations, including noticing, distraction, worry, attention regulation, emotional awareness, self-regulation, body listening, and trust; MAIA-2 revises weak scales.",
        "Multidimensional self-report of interoceptive attention, appraisal, and regulation.", "Questionnaire psychometrics in mind-body and clinical research.",
        ["The original development used expert and participant input with factor and validity analyses.", "MAIA-2 revised the not-distracting and not-worrying scales and retested the multidimensional structure."],
        ["Self-report indexes beliefs and tendencies rather than objective afferent accuracy.", "Factor reliability and invariance vary by language and population."],
        "MAIA and MAIA-2 assess reported interoceptive awareness styles; they do not directly measure heartbeat detection, visceral precision, or consciousness level.",
        ["Which subscales predict online behavior beyond general distress and mindfulness?", "How stable is the factor structure across clinical and cultural groups?"],
        [doi_source("10.1371/journal.pone.0048230", "primary-scale-development"), doi_source("10.1371/journal.pone.0208034", "primary-revision-validation")],
        ["MAIA", "MAIA-2", "body awareness", "interoceptive self-report"]),
    spec(
        "states-clinical-042-bpq-sf", "Body Perception Questionnaire–Short Form", ["BPQ-SF", "Body Perception Questionnaire Short Form", "BPQ-Short"],
        "Model or framework", "Interoception and autonomic symptoms / self-report", "Psychophysiology / autonomic self-report measurement", 2018,
        ["Ana Cabrera", "Oliver A. Kolacz", "Abby Pailhez", "Stephen W. Porges"],
        "BPQ-SF is a shortened self-report instrument emphasizing body awareness and autonomic-reactivity symptoms derived from the longer Body Perception Questionnaire.",
        "Efficient self-report assessment of bodily sensation awareness and autonomic symptom burden.", "Questionnaire psychometrics and autonomic symptom research.",
        ["The short-form validation used large samples to evaluate factor structure and reliability.", "Interoception frameworks clarify why symptom report should be separated from objective detection performance."],
        ["Symptom frequency reflects attention, appraisal, health, and distress as well as bodily signals.", "Subscales should not be treated as direct vagal or autonomic physiology."],
        "BPQ-SF is a subjective symptom and awareness measure, not a physiological assay of vagal tone or a global measure of interoceptive accuracy.",
        ["How much variance reflects current health and anxiety rather than stable awareness style?", "Which physiological measures show prospective convergence at the subscale level?"],
        [doi_source("10.1002/mpr.1596", "primary-short-form-validation"), doi_source("10.1016/j.biopsycho.2014.11.004", "authoritative-construct-framework")],
        ["BPQ-SF", "body awareness", "autonomic reactivity", "self-report"]),
    spec(
        "states-clinical-043-pas", "Perceptual Awareness Scale", ["PAS", "four-point Perceptual Awareness Scale"],
        "Model or framework", "Perceptual consciousness / subjective assessment", "Experimental consciousness research / psychophysics", 2004,
        ["Thomas Zoëga Ramsøy", "Morten Overgaard"],
        "PAS asks observers to classify visual experience using graded categories commonly labeled no experience, brief glimpse, almost clear experience, and clear experience.",
        "Trial-wise graded report of the clarity of visual perceptual experience.", "Visual psychophysics and subjective-report methodology.",
        ["The scale was developed through participant-derived descriptions of perceptual experience.", "Comparative studies evaluate PAS against confidence and post-decision wagering under matched tasks."],
        ["Labels require training and can be used differently across observers.", "Reports are affected by criterion, memory, task relevance, and motor mapping."],
        "PAS is a structured subjective report scale; it does not establish that consciousness is intrinsically discrete or graded and is not a no-report measure.",
        ["Which model best separates experiential strength from response criterion?", "How should between-person category use be calibrated?"],
        [doi_source("10.1037/t59063-000", "authoritative-test-record"), doi_source("10.1016/j.concog.2009.12.013", "primary-comparative-validation")],
        ["PAS", "perceptual awareness", "subjective visibility", "visual consciousness"]),
    spec(
        "states-clinical-044-postdecision-wagering", "Post-Decision Wagering", ["PDW", "post-decision betting", "wagering measure of awareness"],
        "Model or framework", "Metacognition / awareness assessment", "Comparative cognition / decision neuroscience", 2007,
        ["Navindra Persaud", "Peter McLeod", "Alan Cowey"],
        "After a discrimination decision, observers wager on its correctness; advantageous wagering is used to infer access to information about decision accuracy without asking for a direct visibility rating.",
        "Behavioral assay of metacognitive access to decision correctness through incentive-compatible confidence choices.", "Human and comparative decision tasks.",
        ["The original study proposed wagering as a consciousness measure and applied it to blindsight and implicit learning.", "Methodological critiques identify risk preference and loss aversion as alternative determinants."],
        ["Wagers mix confidence with utility, risk attitude, learning, and reward sensitivity.", "Above-chance wagering can reflect metacognitive information without resolving phenomenal experience."],
        "Post-decision wagering is an indirect confidence method, not a pure no-report measure and not sufficient evidence for or against consciousness by itself.",
        ["Can proper scoring rules isolate confidence from risk preference?", "How should wagering be interpreted across species with different reward valuation?"],
        [doi_source("10.1038/nn1840", "primary-method"), doi_source("10.1016/j.tics.2008.02.012", "methodological-critique")],
        ["post-decision wagering", "confidence", "metacognition", "awareness"]),
])


if __name__ == "__main__":
    main()
