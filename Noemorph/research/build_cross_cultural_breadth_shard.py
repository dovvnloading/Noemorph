"""Build the provisional cross-cultural/historical breadth supplement.

This script deliberately keeps the shard outside ``catalog.json``.  The records
are candidate catalog entries, not evidence that their vocabularies are
interchangeable with modern consciousness-science terms.  Translation and
attribution limits are therefore stored on each record.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "catalog-2026-08-30-cross-cultural-breadth.json"
RETRIEVED = "2026-08-30"


def source(
    title: str,
    authors: str,
    year: int | str,
    venue: str,
    url: str,
    authority: str,
) -> dict:
    item = {
        "title": title,
        "authors": authors,
        "year": year,
        "venue": venue,
        "url": url,
        "authority": authority,
        "verification": "doi-resolved" if url.startswith("https://doi.org/") else "locator-recorded",
        "retrieved": RETRIEVED,
    }
    if url.startswith("https://doi.org/"):
        item["doi"] = url.removeprefix("https://doi.org/")
    return item


S = {
    # South Asian and Buddhist sources
    "early_upanishads": source("The Early Upanishads: Annotated Text and Translation", "Patrick Olivelle", 1998, "Oxford University Press", "https://global.oup.com/academic/product/the-early-upanishads-9780195124354", "primary-source-scholarly-translation"),
    "person_india": source("Personhood in Classical Indian Philosophy", "Monima Chadha", 2022, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/personhood-india/", "authoritative-specialist-secondary"),
    "gita_13": source("Bhagavad Gita, Chapter 13: Kṣetra-Kṣetrajña-Vibhāga-Yoga", "Bhagavad Gītā; digital edition", "ca. 2nd century BCE–2nd century CE", "Gita Supersite, Indian Institute of Technology Kanpur", "https://www.gitasupersite.iitk.ac.in/srimad?language=dv&field_chapter_value=13", "primary-text-institutional-edition"),
    "naturalism_india": source("Naturalism in Classical Indian Philosophy", "Monima Chadha", 2024, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/naturalism-india/", "authoritative-specialist-secondary"),
    "bhavanga_collins": source("Momentariness and the bhavaṅga-mind", "Steven Collins", 1982, "Selfless Persons, Cambridge University Press", "https://doi.org/10.1017/CBO9780511621499.011", "scholarly-secondary"),
    "bhavanga_history": source("Observations on the Term Bhavaṅga in the Earlier Pāli Texts and the Doctrinal Identity of the Theravāda Tradition", "Lee Youngjin", 2016, "Journal of Buddhist Studies", "https://doi.org/10.21482/jbs.48..201609.257", "scholarly-secondary"),
    "theravada_abhidhamma": source("The Theravāda Abhidhamma: Its Inquiry into the Nature of Conditioned Reality", "Y. Karunadasa", 2010, "Centre of Buddhist Studies, University of Hong Kong / Buddhist Publication Society", "https://www.ibc-elibrary.thanhsiang.org/files/public/The%20Theravada%20Abhidhamma%20Its%20Inquiry%20into%20the%20Nature%20of%20Conditioned%20Reality%20-%20Karuanadasa.pdf", "specialist-monograph"),
    "citta_vithi": source("Cognitive Process Models Depicted in the Dhammasaṅgaṇī", "R. M. Ratnayake", 2025, "Lumbini Prabha", "https://www.nepjol.info/index.php/lumbinip/article/view/78829", "scholarly-secondary"),
    "pudgala_iep": source("Pudgalavāda Buddhist Philosophy", "James P. McDermott", 2004, "Internet Encyclopedia of Philosophy", "https://iep.utm.edu/pudgalavada-buddhist-philosophy/", "authoritative-specialist-secondary"),
    "pudgala_oup": source("Persons Keeping Their Karma Together: The Reasons for the Pudgalavāda in Early Buddhism", "Amber D. Carpenter", 2015, "The Moon Points Back, Oxford University Press", "https://doi.org/10.1093/acprof:oso/9780190226862.003.0001", "scholarly-reconstruction"),
    "mind_indian_buddhism": source("Mind in Indian Buddhist Philosophy", "William S. Waldron", 2009, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/mind-indian-buddhism/", "authoritative-specialist-secondary"),
    "abhidharmakosa": source("Abhidharmakośabhāṣyam of Vasubandhu", "Vasubandhu; translated by Leo M. Pruden", 1988, "Asian Humanities Press; CiNii Books institutional record", "https://ci.nii.ac.jp/ncid/BA07178310", "primary-source-scholarly-translation-record"),
    "dn15": source("The Great Discourse on Causation (DN 15)", "Early Buddhist discourse; translated by Bhikkhu Sujato", 2018, "SuttaCentral", "https://suttacentral.net/dn15/en/sujato", "primary-text-digital-translation"),
    "gelukpa": source("Gelukpa", "Georges Dreyfus", 2011, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/gelukpa/", "authoritative-specialist-secondary"),
    "tsongkhapa": source("Tsongkhapa: A Buddha in the Land of Snows", "Thupten Jinpa", 2019, "Shambhala Publications", "https://www.shambhala.com/tsongkhapa-15494.html", "specialist-intellectual-biography"),
    "sikh_philosophy": source("Sikh Philosophy", "Arvind-Pal Singh Mandair", 2026, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/sikh-philosophy/", "authoritative-specialist-secondary"),
    "sikh_ethics": source("Sikh Ethics", "Arvind-Pal Singh Mandair", 2026, "Cambridge Elements in Ethics", "https://www.cambridge.org/core/elements/sikh-ethics/931645585C0461FFC33D034EF558360C", "authoritative-scholarly-synthesis"),
    "charaka_manas": source("Manas (mind and mental health)", "Charak Samhita New Edition editorial group", 2021, "Charak Samhita Research, Training and Development Centre", "https://doi.org/10.47468/CSNE.2021.e01.s09.058", "institutional-textual-commentary"),
    "ayurveda_mind": source("Hallucinations in the classical Indian system of Ayurveda: A brief overview", "R. V. Trivedi and colleagues", 2014, "Indian Journal of Psychiatry", "https://pmc.ncbi.nlm.nih.gov/articles/PMC4279288/", "peer-reviewed-contextual-analysis"),
    "manasa_prakruti": source("Concept of Manasa Prakruti as described in Charaka Samhita", "Sachin S. Bagali and Umapati C. Baragi", 2016, "Journal of Ayurveda and Integrated Medical Sciences", "https://doi.org/10.21760/jaims.v1i3.4423", "scholarly-textual-analysis"),
    "jaina_sep": source("Jaina Philosophy", "Marie-Hélène Gorisse", 2023, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/jaina-philosophy/", "authoritative-specialist-secondary"),
    "uttaradhyayana": source("Uttarādhyayana-sūtra", "Śvetāmbara Jaina canon; scholarly portal", "canonical text", "JAINpedia, Institute of Jainology", "https://jainpedia.org/reading/uttaradhyayana-sutra/", "primary-text-scholarly-portal"),

    # Chinese, Korean, and Japanese sources
    "chinese_mind": source("Mind (Heart-Mind) in Chinese Philosophy", "Chris Fraser", 2023, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/chinese-mind/", "authoritative-specialist-secondary"),
    "neiye": source("Neiye (Inward Training)", "Guanzi; bilingual digital edition", "4th century BCE", "Chinese Text Project", "https://ctext.org/guanzi/nei-ye/ens", "primary-text-digital-edition"),
    "laozi": source("Laozi", "Alan Chan", 2001, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/laozi/", "authoritative-specialist-secondary"),
    "daodejing": source("Dao De Jing", "Laozi; bilingual digital edition", "received text ca. 4th–3rd century BCE", "Chinese Text Project", "https://ctext.org/dao-de-jing/ens", "primary-text-digital-edition"),
    "zhang_zai": source("Zhang Zai (Chang Tsai)", "Internet Encyclopedia of Philosophy", 2026, "Internet Encyclopedia of Philosophy", "https://iep.utm.edu/zhang-zai-chang-tsai/", "authoritative-specialist-secondary"),
    "cheng_hao": source("Cheng Hao (Cheng Mingdao)", "Internet Encyclopedia of Philosophy", 2026, "Internet Encyclopedia of Philosophy", "https://iep.utm.edu/chenghao/", "authoritative-specialist-secondary"),
    "cheng_yi": source("Cheng Yi", "Internet Encyclopedia of Philosophy", 2026, "Internet Encyclopedia of Philosophy", "https://iep.utm.edu/chengyi/", "authoritative-specialist-secondary"),
    "lu_jiuyuan": source("«Mein Geist ist das Universum»: Ontologische und erkenntnistheoretische Aspekte in der Lehre des Lu Jiuyuan", "Wolfgang Ommerborn", 1996, "Bochumer Philosophisches Jahrbuch für Antike und Mittelalter", "https://doi.org/10.1075/bpjam.1.04omm", "peer-reviewed-specialist-secondary"),
    "wang_fuzhi": source("Wang Fuzhi (1619–92)", "Alison H. Black", 1998, "Routledge Encyclopedia of Philosophy", "https://www.rep.routledge.com/articles/biographical/wang-fuzhi-1619-92/v-1", "authoritative-specialist-encyclopedia"),
    "dai_zhen": source("Dai Zhen", "Internet Encyclopedia of Philosophy", 2026, "Internet Encyclopedia of Philosophy", "https://iep.utm.edu/dai-zhen/", "authoritative-specialist-secondary"),
    "chinese_emotions": source("The Emotions in Early Chinese Philosophy", "Curie Virág", 2021, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/emotions-chinese/", "authoritative-specialist-secondary"),
    "korean_philosophy": source("Korean Philosophy", "Kevin Cawley", 2021, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/korean-philosophy/", "authoritative-specialist-secondary"),
    "korean_confucianism": source("Korean Confucianism", "Kevin Cawley", 2020, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/korean-confucianism/", "authoritative-specialist-secondary"),
    "wonhyo_book": source("Wŏnhyo: Selected Works", "Wŏnhyo; edited and translated by A. Charles Muller, Jin Y. Park, and Sem Vermeersch", 2012, "Collected Works of Korean Buddhism; UCLA Center for Buddhist Studies record", "https://www.international.ucla.edu/buddhist/article/127536", "primary-source-scholarly-translation-record"),
    "jinul_huatou": source("Zen Language in Our Time: The Case of Pojo Chinul's Huatou Meditation", "Jin Y. Park", 2005, "Philosophy East and West", "https://doi.org/10.1353/pew.2004.0047", "scholarly-secondary"),
    "dogen_sep": source("Japanese Zen Buddhist Philosophy", "Shigenori Nagatomo", 2024, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/japanese-zen/", "authoritative-specialist-secondary"),
    "shobogenzo": source("Shōbōgenzō: The True Dharma-eye Treasury", "Dōgen; translated by Gudo Wafu Nishijima and Chodo Cross", 2007, "BDK America", "https://www.bdkamerica.org/product/shobogenzo-the-true-dharma-eye-treasury/", "primary-source-scholarly-translation"),
    "watsuji_sep": source("Watsuji Tetsurō", "Robert E. Carter", 2004, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/watsuji-tetsuro/", "authoritative-specialist-secondary"),
    "watsuji_book": source("Watsuji Tetsurō's Rinrigaku: Ethics in Japan", "Watsuji Tetsurō; translated by Yamamoto Seisaku and Robert E. Carter", 1996, "State University of New York Press", "https://sunypress.edu/Books/W/Watsujio-Tetsur-s-Rinrigaku2", "primary-source-scholarly-translation"),
    "huayan_sep": source("Huayan Buddhism", "Bryan W. Van Norden and Nicholaos Jones", 2019, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/buddhism-huayan/", "authoritative-specialist-secondary"),
    "zongmi_book": source("Inquiry into the Origin of Humanity", "Guifeng Zongmi; translated by Peter N. Gregory", 1995, "University of Hawaiʻi Press", "https://uhpress.hawaii.edu/9780824817640/", "primary-source-scholarly-translation"),
    "chan_sep": source("Chan Buddhism", "Mario Poceski", 2024, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/buddhism-chan/", "authoritative-specialist-secondary"),
    "platform_sutra": source("The Platform Sutra of the Sixth Patriarch", "attributed to Huineng; translated by John R. McRae", 2000, "BDK America", "https://www.bdkamerica.org/product/the-platform-sutra-of-the-sixth-patriarch/", "primary-source-scholarly-translation"),
    "japanese_philosophy": source("Japanese Philosophy", "Thomas P. Kasulis", 2025, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/japanese-philosophy/", "authoritative-specialist-secondary"),
    "yuasa_body": source("The Body: Toward an Eastern Mind-Body Theory", "Yuasa Yasuo; translated by T. P. Kasulis and Shigenori Nagatomo", 1987, "State University of New York Press", "https://sunypress.edu/Books/T/The-Body", "primary-source-scholarly-translation"),

    # Arabic-Islamic and Jewish sources
    "arabic_mind": source("Arabic and Islamic Psychology and Philosophy of Mind", "H. A. Davidson", 2008, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/arabic-islamic-mind/", "authoritative-specialist-secondary"),
    "al_kindi": source("al-Kindī", "Peter Adamson", 2006, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/al-kindi/", "authoritative-specialist-secondary"),
    "al_razi": source("Abu Bakr al-Razi", "Peter Adamson", 2025, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/abu-bakr-al-razi/", "authoritative-specialist-secondary"),
    "ibn_tufayl": source("Ibn Ṭufayl", "Marco Lauri", 2017, "Oxford Bibliographies in Islamic Studies", "https://academic.oup.com/reference/62361/reference-article-abstract/554573383", "authoritative-specialist-reference"),
    "hayy": source("Ibn Tufayl's Hayy Ibn Yaqzan: A Philosophical Tale", "Ibn Ṭufayl; translated by Lenn Evan Goodman", 2009, "University of Chicago Press", "https://press.uchicago.edu/ucp/books/book/chicago/I/bo25938805.html", "primary-source-scholarly-translation"),
    "ikhwan": source("Ikhwān al-Ṣafāʾ", "Carmela Baffioni", 2008, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/ikhwan-al-safa/", "authoritative-specialist-secondary"),
    "ikhwan_oup": source("The Case of the Animals versus Man Before the King of the Jinn", "Ikhwān al-Ṣafāʾ; translated by Lenn E. Goodman and Richard McGregor", 2009, "Oxford University Press / Institute of Ismaili Studies", "https://global.oup.com/academic/product/the-case-of-the-animals-versus-man-before-the-king-of-the-jinn-9780199554749", "primary-source-scholarly-translation"),
    "fakhr_razi": source("Fakhr al-Din al-Razi", "Ayman Shihadeh", 2023, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/al-din-al-razi/", "authoritative-specialist-secondary"),
    "abu_barakat": source("Abu'l-Barakāt al-Baghdādī", "Wilferd Madelung", 1983, "Encyclopaedia Iranica", "https://www.iranicaonline.org/articles/abul-barakat-al-bagdadi-awhad-al-zaman-hebatallah-b/", "authoritative-specialist-encyclopedia"),
    "islamic_freewill": source("Causation in Arabic and Islamic Thought", "Kara Richardson", 2025, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/arabic-islamic-causation/", "authoritative-specialist-secondary"),
    "occasionalism": source("Occasionalism", "Sukjae Lee", 2008, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/occasionalism/", "authoritative-specialist-secondary"),
    "islamic_mysticism": source("Mysticism in Arabic and Islamic Philosophy", "Seyyed N. Nasr", 2020, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/arabic-islamic-mysticism/", "authoritative-specialist-secondary"),
    "sufi_psychology": source("Sufi Psychology", "Sara Sviri", 2012, "The Cambridge Companion to Sufism", "https://doi.org/10.1017/CCOL9780521860543.012", "scholarly-secondary"),
    "halevi": source("Judah Halevi", "Ehud Krinis", 2026, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/halevi/", "authoritative-specialist-secondary"),
    "ibn_gabirol": source("Solomon Ibn Gabirol [Avicebron]", "Sarah Pessin", 2013, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/ibn-gabirol/", "authoritative-specialist-secondary"),
    "isaac_israeli": source("Isaac Israeli", "Alexander Altmann and S. M. Stern", 2007, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/israeli/", "authoritative-specialist-secondary"),
    "ibn_ezra": source("Abraham Ibn Ezra", "Shlomo Sela", 2006, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/ibn-ezra/", "authoritative-specialist-secondary"),
    "crescas": source("Hasdai Crescas", "Warren Zev Harvey", 2012, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/crescas/", "authoritative-specialist-secondary"),
    "jewish_philosophy": source("Soul and Intellect", "T. M. Rudavsky", 2009, "The Cambridge History of Jewish Philosophy", "https://www.cambridge.org/core/books/abs/cambridge-history-of-jewish-philosophy/soul-and-intellect/A1F75E2AC8E435FBF0D7846A8B75C9E0", "authoritative-scholarly-context"),
    "zohar": source("Zohar II, 94b: layered soul vocabulary", "Zohar; bilingual digital edition", "late 13th century", "Sefaria", "https://www.sefaria.org/Zohar.2.94b?lang=bi", "primary-text-digital-edition"),
    "tanya": source("Tanya, Likkutei Amarim", "Shneur Zalman of Liadi; bilingual digital edition", 1796, "Sefaria", "https://www.sefaria.org/Tanya%2C_Part_I%3B_Likkutei_Amarim?lang=bi", "primary-text-digital-edition"),
    "chabad": source("Hasidism", "Moshe Rosman", 2021, "YIVO Encyclopedia of Jews in Eastern Europe", "https://yivoencyclopedia.org/article.aspx/Hasidism", "authoritative-specialist-secondary"),

    # African, Indigenous, Pacific, and ancient sources
    "ubuntu_iep": source("Hunhu/Ubuntu in the Traditional Thought of Southern Africa", "Motsamai Molefe", 2022, "Internet Encyclopedia of Philosophy", "https://iep.utm.edu/hunhu-ubuntu-southern-african-thought/", "authoritative-specialist-secondary"),
    "african_ethics": source("African Ethics", "Kwame Gyekye", 2010, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/african-ethics/", "authoritative-specialist-secondary"),
    "egypt_body": source("Body", "Christina Riggs", 2010, "UCLA Encyclopedia of Egyptology", "https://escholarship.org/uc/item/8f21r7sj", "peer-reviewed-specialist-encyclopedia"),
    "egypt_ba": source("Ba", "Jiří Janák", 2016, "UCLA Encyclopedia of Egyptology", "https://escholarship.org/uc/item/9tf6x6xp", "peer-reviewed-specialist-encyclopedia"),
    "egypt_heart": source("Heart Scarab with a Human Head", "Metropolitan Museum of Art", "New Kingdom object; catalogued 2026", "The Met Collection", "https://www.metmuseum.org/art/collection/search/550986", "authoritative-museum-object-record"),
    "egypt_art": source("The Art of Ancient Egypt: A Resource for Educators", "Metropolitan Museum of Art", 2005, "Metropolitan Museum of Art", "https://resources.metmuseum.org/resources/metpublications/pdf/The_Art_of_Ancient_Egypt_A_Resource_for_Educators.pdf", "authoritative-museum-synthesis"),
    "fravashi": source("Fravaši", "Mary Boyce", 2000, "Encyclopaedia Iranica", "https://www.iranicaonline.org/articles/fravasi/", "authoritative-specialist-encyclopedia"),
    "zoroastrian_history": source("Zoroastrianism I: Historical Review up to the Arab Conquest", "Mary Boyce", 2005, "Encyclopaedia Iranica", "https://www.iranicaonline.org/articles/zoroastrianism-i-historical-review/", "authoritative-specialist-encyclopedia"),
    "manichaeism_iep": source("Manichaeism", "Iain Gardner", 2015, "Oxford Classical Dictionary", "https://academic.oup.com/edited-volume/61673/chapter-abstract/549652892", "authoritative-specialist-encyclopedia"),
    "manichaeism_iranica": source("Manicheism I: General Survey", "Werner Sundermann", 2009, "Encyclopaedia Iranica", "https://www.iranicaonline.org/articles/manicheism-1-general-survey", "authoritative-specialist-encyclopedia"),
    "evagrius": source("Brain and Psyche in Early Christian Asceticism", "David T. Bradford", 2011, "Psychological Reports", "https://doi.org/10.2466/07.09.16.20.PR0.109.5.461-520", "peer-reviewed-historical-analysis"),
    "evagrius_oup": source("Evagrius Ponticus", "Augustine Casiday", 2006, "Routledge Early Church Fathers", "https://doi.org/10.4324/9780203008423", "primary-text-scholarly-translation"),
    "negritude_sep": source("Négritude", "Souleymane Bachir Diagne", 2018, "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/entries/negritude/", "authoritative-specialist-secondary"),
    "negritude_critique": source("Ethnophilosophy as Decolonization: Revisiting the Question of African Philosophy", "Ada Agada", 2025, "Philosophical Papers", "https://doi.org/10.1080/05568641.2024.2416459", "peer-reviewed-critical-analysis"),
    "tempels_reception": source("Africa's Influence on European Culture and Placide Tempels' Bantu Philosophy", "Ullrich Relebogilwe Kleinhempel", 2019, "Numen", "https://doi.org/10.34019/2236-6296.2019.v22.29624", "peer-reviewed-critical-reception"),
    "vitality": source("From Intrinsic Value to Ontological Reality—the Philosophy of Life Energy or Vital Force", "Angela Roothaan", 2026, "African Philosophy and Deep Ecology, Routledge", "https://doi.org/10.4324/9781003480914-2", "scholarly-critical-analysis"),
    "nsamenang": source("Human Ontogenesis: An Indigenous African View on Development and Intelligence", "A. Bame Nsamenang", 2006, "International Journal of Psychology", "https://doi.org/10.1080/00207590544000077", "primary-scholarly-articulation"),
    "nsamenang_review": source("Mediated Mutual Reciprocity in the Process of African Children's Social Ontogenesis", "Therese Mungah Shalo Tchombe", 2019, "Journal of Psychology in Africa", "https://doi.org/10.1080/14330237.2019.1647493", "peer-reviewed-secondary"),
    "te_wheke": source("Te Wheke model of Māori health", "Rose Pere; New Zealand Ministry of Health", 2025, "Manatū Hauora", "https://www.health.govt.nz/maori-health/maori-health-models/te-wheke", "official-community-accountable-guidance"),
    "maori_strategy": source("Hui Whakaoranga: history of Māori health-model development", "New Zealand Ministry of Health", 2024, "Manatū Hauora", "https://www.health.govt.nz/maori-health/whakamaua-maori-health-action-plan-2020-2025/hui-whakaoranga", "authoritative-government-context"),
    "fonofale_primary": source("Fonofale—Model of Health 2001", "Fuimaono Karl Pulotu-Endemann", 2001, "Community Research / Health Research Council of New Zealand", "https://communityresearch.org.nz/research/fonofale-model-of-health/", "primary-model-institutional-record"),
    "fonofale_review": source("Utilizing Pacific Methodologies as Inclusive Practice", "Vaoiva Ponton", 2018, "SAGE Open", "https://doi.org/10.1177/2158244018792962", "peer-reviewed-contextual-analysis"),
    "hawaiian_care": source("Conceptualizing a New System of Care in Hawaiʻi for Native Hawaiians and Substance Use", "Sheri-Ann P. Daniels et al.", 2022, "Hawaiʻi Journal of Health & Social Welfare", "https://pmc.ncbi.nlm.nih.gov/articles/PMC9783813/", "community-authored-peer-reviewed-model"),
    "hawaiian_health": source("E Ola Mau: The Native Hawaiian Health Needs Study", "E Ola Mau / Papa Ola Lōkahi", 1985, "Papa Ola Lōkahi", "https://papaolalokahi.org/wp-content/uploads/pol-pdf/HISTORICAL-CULTURAL-TASK-FORCE.pdf", "community-health-authority-report"),
    "perspectivism": source("Cosmological Deixis and Amerindian Perspectivism", "Eduardo Viveiros de Castro", 1998, "Journal of the Royal Anthropological Institute", "https://doi.org/10.2307/3034157", "primary-anthropological-formulation"),
    "amazon_critique": source("Beinghood and People-Making in Native Amazonia", "Fernando Santos-Granero", 2012, "HAU: Journal of Ethnographic Theory", "https://doi.org/10.14318/hau2.1.010", "peer-reviewed-comparative-analysis"),
    "nahua_ihiyotl": source("El ihiyotl, la sombra y las almas-aliento en Mesoamérica", "Alfredo López Austin", 2006, "Cuicuilco", "https://revistas.inah.gob.mx/index.php/cuicuilco/article/view/4314", "specialist-ethnohistorical-analysis"),
    "nahua_translation": source("Winds, Heart, and Heat in Premodern Franciscan and Nahua Concepts of Soul", "Molly H. Bassett", 2018, "Colonial Latin American Review", "https://doi.org/10.1080/10609164.2018.1527525", "peer-reviewed-translation-history"),
    "dadirri_primary": source("Dadirri: Inner Deep Listening and Quiet Still Awareness", "Miriam-Rose Ungunmerr-Baumann", 2002, "Dadirri / Emmaus Productions", "https://dadirri.org.au/wp-content/uploads/2015/03/Dadirri-Inner-Deep-Listening-M-R-Ungunmerr-Bauman-Refl1.pdf", "primary-community-authored-articulation"),
    "dadirri_method": source("Dadirri: An Indigenous Place-Based Research Methodology", "Miriam-Rose Ungunmerr-Baumann et al.", 2022, "AlterNative", "https://doi.org/10.1177/11771801221085353", "community-authored-peer-reviewed-method"),
    "qungasvik_primary": source("Creating Qungasvik: Case Examples from a Community-Developed and Culturally-Driven Intervention", "Stacy M. Rasmus, Billy Charles, and Gerald V. Mohatt", 2014, "American Journal of Community Psychology", "https://pmc.ncbi.nlm.nih.gov/articles/PMC4119530/", "community-collaborative-peer-reviewed-model"),
    "qungasvik_eval": source("Patterns of Protective Factors in an Intervention for Yup'ik Alaska Native Youth", "David Henry et al. and the People Awakening Team", 2012, "American Journal of Drug and Alcohol Abuse", "https://pmc.ncbi.nlm.nih.gov/articles/PMC3506184/", "community-collaborative-evaluation"),
    "tzeltal_person": source("The Two Maya Bodies: An Elementary Model of Tzeltal Personhood", "Pedro Pitarch", 2012, "Ethnos", "https://doi.org/10.1080/00141844.2011.590217", "peer-reviewed-ethnographic-analysis"),
    "chulel_review": source("El ch'ulel en los Altos de Chiapas: estado de la cuestión", "Pedro Pitarch and colleagues", 2011, "Revista Pueblos y Fronteras Digital", "https://www.pueblosyfronteras.unam.mx/index.php/index.php/pyf/article/view/139", "peer-reviewed-regional-review"),
    "strathern": source("Marriage Exchanges: A Melanesian Comment", "Marilyn Strathern", 1984, "Annual Review of Anthropology", "https://doi.org/10.1146/annurev.an.13.100184.000353", "primary-anthropological-formulation"),
    "dividual_critique": source("From Dividual and Individual Selves to Porous Subjects", "Karl Smith", 2012, "Australian Journal of Anthropology", "https://doi.org/10.1111/j.1757-6547.2012.00167.x", "peer-reviewed-critical-analysis"),
    "samoan_va": source("Relational Self and the Samoan Vā", "Tamasese, Peteru, Waldegrave, and Bush", 2005, "MAI Review", "https://www.journal.mai.ac.nz/system/files/maireview/298-2299-1-PB.pdf", "community-grounded-scholarly-articulation"),
    "va_method": source("Utilizing Pacific Methodologies as Inclusive Practice", "Vaoiva Ponton", 2018, "SAGE Open", "https://doi.org/10.1177/2158244018792962", "peer-reviewed-contextual-analysis"),
}


def record(
    *,
    name: str,
    aliases: list[str],
    kind: str,
    codes: list[str],
    domain: str,
    tradition: str,
    status: str,
    status_note: str,
    summary: str,
    proponents: list[str],
    era: str,
    year: int,
    scope: str,
    keywords: list[str],
    boundary: str,
    claim_type: str,
    applies_to: str,
    does_not: str,
    basis: list[str],
    questions: list[str],
    sources: list[str],
) -> dict:
    citations = [dict(S[key]) for key in sources]
    return {
        "name": name,
        "aliases": aliases,
        "kind": kind,
        "kind_codes": codes,
        "domain": domain,
        "tradition": tradition,
        "status": status,
        "status_note": status_note,
        "summary": summary,
        "proponents": proponents,
        "era": era,
        "year": year,
        "scope": scope,
        "keywords": keywords,
        "boundary_note": boundary,
        "claim_scope": {"type": claim_type, "applies_to": applies_to, "does_not_establish": does_not},
        "evidence_profile": {
            "basis": basis,
            "source_count": len(citations),
            "citation_mix": "Record-specific primary, specialist, or institutional source paired with independent scholarly context.",
            "verification_summary": "HTTPS locators recorded; DOI locators marked separately. Translation and attribution limits remain provisional.",
        },
        "open_questions": questions,
        "review_state": "provisional",
        "citations": citations,
    }


RECORDS: list[dict] = []


def add(**kwargs) -> None:
    RECORDS.append(record(**kwargs))


# Records are appended below in regionally scoped sections.  They are deliberately
# not related to one another by graph edges during the collection phase.

# --- South Asian, Sikh, Jaina, and Buddhist distinctions --------------------

add(
    name="Taittirīya Upaniṣad five-sheath model",
    aliases=["pañcakośa model", "five kośas", "Taittirīya layers of the person"],
    kind="Historical tradition", codes=["HT", "MF"],
    domain="Self, embodiment & layered personhood", tradition="Early Upaniṣadic thought and later Vedānta reception",
    status="historically foundational · interpretations diverge by Vedānta school",
    status_note="The fivefold sequence is textual; whether kośa means sheath, layer, or domain and how it relates to ātman differs across commentaries.",
    summary="The Taittirīya Upaniṣad describes the person through food, breath, mind, understanding, and bliss formations, proceeding inward toward an account of self and brahman. Later Vedānta authors systematized these as five kośas used to distinguish changing psycho-physical functions from the self.",
    proponents=["Taittirīya Upaniṣad textual tradition", "later Vedānta commentators"], era="late first millennium BCE; continuing reception", year=-500,
    scope="A textual and commentarial model of bodily, vital, mental, cognitive, and bliss-associated aspects of a person.",
    keywords=["Taittiriya", "pañcakośa", "self", "mind", "bliss", "Vedanta"],
    boundary="Kośa is a contested translation and does not denote five anatomical bodies or empirically separable neural levels. Later Advaita readings must not be projected back as the only meaning of the early text.",
    claim_type="historical layered-person model", applies_to="The Taittirīya sequence and its school-specific Vedānta interpretations.", does_not="A scientifically validated hierarchy of consciousness or a pan-Indian consensus.",
    basis=["scholarly primary-text translation", "authoritative history of Indian personhood"],
    questions=["How do early textual and later commentarial uses of kośa differ?", "Which distinctions are phenomenological, ritual, soteriological, or metaphysical?"], sources=["early_upanishads", "person_india"],
)

add(
    name="Māṇḍūkya four-state analysis and turīya",
    aliases=["waking-dreaming-deep-sleep-turiya model", "Māṇḍūkya states of self"],
    kind="Historical tradition", codes=["HT", "MF"],
    domain="States of consciousness, self & nonduality", tradition="Māṇḍūkya Upaniṣad and Gauḍapādīya reception",
    status="foundational state analysis · translation and ontology contested",
    status_note="Vedānta schools disagree about whether turīya is best described as a fourth state, the ground of all states, or a non-state designation.",
    summary="The Māṇḍūkya associates waking, dreaming, and deep sleep with modes of the self and uses turīya to indicate what is not exhausted by any of the three. Gauḍapāda's later verses develop this compact analysis within an explicitly nondual argument.",
    proponents=["Māṇḍūkya Upaniṣad textual tradition", "Gauḍapāda"], era="early centuries CE; continuing Vedānta reception", year=200,
    scope="First-person and metaphysical classification of waking, dream, deep sleep, and turīya.",
    keywords=["Mandukya", "turīya", "waking", "dream", "deep sleep", "self"],
    boundary="Turīya should not automatically be rendered as an experimentally measured fourth brain state, and Gauḍapāda's interpretation is later than the root Upaniṣad.",
    claim_type="historical state-and-self analysis", applies_to="Māṇḍūkya and Gauḍapādīya classifications of experience and self.", does_not="A modern sleep-stage taxonomy or one uncontested account across Vedānta.",
    basis=["scholarly primary-text translation", "authoritative personhood analysis"],
    questions=["Is turīya a distinct mode, the condition of modes, or apophatic language?", "How should deep sleep claims be assessed without importing contemporary introspective assumptions?"], sources=["early_upanishads", "person_india"],
)

add(
    name="Kaṭha Upaniṣad chariot hierarchy of self and mind",
    aliases=["Katha chariot metaphor", "ātman-buddhi-manas-senses chariot model"],
    kind="Historical tradition", codes=["HT", "MF"],
    domain="Self, intellect, attention & sensory control", tradition="Early Upaniṣadic moral psychology",
    status="canonical metaphor · later philosophical uses vary",
    status_note="The hierarchy is delivered through a soteriological teaching metaphor and is not a literal mechanical psychology.",
    summary="The Kaṭha Upaniṣad compares the embodied person to a chariot: self is passenger, intellect the driver, mind the reins, senses the horses, and sense objects their roads. The image links discriminative understanding and attentional control to the practical ordering of cognition and action.",
    proponents=["Kaṭha Upaniṣad textual tradition"], era="late first millennium BCE; continuing reception", year=-400,
    scope="A normative metaphor for relations among self, intellect, mind, senses, body, and objects.",
    keywords=["Katha Upanishad", "chariot", "buddhi", "manas", "senses", "self-control"],
    boundary="The chariot image is not evidence that early Indian authors endorsed a modern executive-control architecture, and later Yoga or Vedānta mappings require separate attribution.",
    claim_type="historical moral-psychological metaphor", applies_to="The Kaṭha text's ordering of self, cognition, attention, and sensory conduct.", does_not="Neuroanatomical localization or a unitary Indian faculty psychology.",
    basis=["scholarly primary-text translation", "authoritative comparative personhood analysis"],
    questions=["Which roles are descriptive and which are normative ideals?", "How do later commentaries alter the passenger-driver relation?"], sources=["early_upanishads", "person_india"],
)

add(
    name="Bhagavad Gītā field–knower distinction",
    aliases=["kṣetra-kṣetrajña distinction", "field and knower of the field"],
    kind="Historical tradition", codes=["HT", "PP"],
    domain="Embodiment, witnessing & self", tradition="Bhagavad Gītā and plural Vedānta commentarial traditions",
    status="canonical distinction · school-specific metaphysics",
    status_note="Commentators disagree about individual self, supreme knower, nature, and the relation between them.",
    summary="Chapter 13 distinguishes the kṣetra, the embodied field that includes body and mental-affective constituents, from the kṣetrajña, the knower of that field. The text then relates individual knowing, nature, and the supreme in language later interpreted differently by nondual, qualified-nondual, and dualist schools.",
    proponents=["Bhagavad Gītā textual tradition", "Śaṅkara, Rāmānuja, Madhva, and other distinct commentators"], era="ca. 2nd century BCE–2nd century CE; continuing reception", year=100,
    scope="Textual distinction among embodiment, mental constituents, knowing subject, and ultimate reality.",
    keywords=["Bhagavad Gita", "kṣetra", "kṣetrajña", "body", "knower", "self"],
    boundary="The record preserves the text's multivalent vocabulary; it does not merge incompatible Vedānta commentaries or equate kṣetra with the brain and kṣetrajña with a Cartesian soul.",
    claim_type="historical field-knower distinction", applies_to="Bhagavad Gītā 13 and explicitly attributed commentarial interpretations.", does_not="One settled metaphysics of mind or empirical evidence for a disembodied observer.",
    basis=["institutional primary-text edition", "authoritative specialist overview"],
    questions=["How do major commentaries individuate the knower?", "Which mental functions remain within the field rather than the knower?"], sources=["gita_13", "naturalism_india"],
)

add(
    name="Theravāda bhavaṅga continuity model",
    aliases=["bhavaṅga-citta", "life-continuum mind", "Theravāda bhavaṅga-sota"],
    kind="Historical tradition", codes=["HT", "MF"],
    domain="Mental continuity, cognition & rebirth", tradition="Theravāda Abhidhamma and commentarial thought",
    status="school-specific classical model · historical development debated",
    status_note="Bhavaṅga is prominent in later Theravāda systematics; its relation to earlier Pāli usages and to active cognition remains a specialist debate.",
    summary="Theravāda manuals use bhavaṅga for passive life-continuum moments occurring when an active sense- or mind-door cognitive process is absent. It helps model causal continuity across episodes without positing a permanent self, including linking death and rebirth within the tradition's own cosmology.",
    proponents=["Theravāda Abhidhamma commentators", "Buddhaghosa and later manual traditions"], era="early centuries BCE–medieval commentaries; living scholastic reception", year=400,
    scope="A Theravāda account of background mental continuity between active cognitive processes.",
    keywords=["Theravada", "bhavanga", "continuity", "Abhidhamma", "cognition", "no-self"],
    boundary="Bhavaṅga is not a permanent soul, Freudian unconscious, or straightforward equivalent of Yogācāra ālayavijñāna. English renderings such as 'subconscious' can mislead.",
    claim_type="school-specific continuity model", applies_to="Theravāda commentarial explanations of gaps between active cognitive sequences and life continuity.", does_not="A universal Buddhist substrate consciousness or a neuroscientific resting-state mechanism.",
    basis=["specialist historical monograph", "peer-reviewed doctrinal history"],
    questions=["When and why did technical bhavaṅga theory crystallize?", "How should intentional object and causal efficacy be interpreted during passive moments?"], sources=["bhavanga_collins", "bhavanga_history"],
)

add(
    name="Theravāda citta-vīthi cognitive-process model",
    aliases=["Theravāda process of consciousness", "cognitive series model", "mind-door and sense-door process"],
    kind="Historical tradition", codes=["HT", "MF"],
    domain="Perception, attention, intention & momentary cognition", tradition="Theravāda Abhidhamma",
    status="mature scholastic model · textual layers require separation",
    status_note="The detailed fixed sequences are clearest in post-canonical manuals; early Abhidhamma materials provide precursors rather than the entire later scheme.",
    summary="The citta-vīthi model analyzes cognition as rapidly ordered moments beginning with disturbance of the life continuum, orientation, sense or mind consciousness, reception, investigation, determination, ethically charged impulsion, and possible registration. Different sequences are specified for sense doors, mind door, absorption, and transition events.",
    proponents=["Theravāda Abhidhamma exegetes", "Anuruddha's Abhidhammatthasaṅgaha tradition"], era="post-canonical Theravāda scholasticism; continuing study", year=1100,
    scope="Fine-grained causal sequencing of perceptual and mental episodes in Theravāda scholastic psychology.",
    keywords=["citta-vithi", "Abhidhamma", "perception", "attention", "javana", "mind door"],
    boundary="The moment counts and functions are textual-analytic commitments, not timings directly measured in milliseconds, and they should not be retrojected unchanged into the earliest discourses.",
    claim_type="historical cognitive-process model", applies_to="Theravāda scholastic explanations of sense-door and mind-door episodes.", does_not="A validated neural processing pipeline or every Buddhist account of perception.",
    basis=["specialist monograph", "record-specific scholarly analysis"],
    questions=["How did the sequence develop across canonical, commentarial, and manual sources?", "Which functions are phenomenological descriptions, ethical classifications, or causal postulates?"], sources=["theravada_abhidhamma", "citta_vithi"],
)

add(
    name="Pudgalavāda person theory",
    aliases=["Buddhist Personalism", "Vātsīputrīya-Sāṃmitīya person doctrine", "pudgala neither identical nor different"],
    kind="Philosophical position", codes=["PP", "HT"],
    domain="Personhood, continuity & no-self", tradition="Pudgalavāda Buddhist schools",
    status="historically influential minority position · reconstructed largely through opponents",
    status_note="Much surviving evidence is polemical and school-internal texts are fragmentary or preserved in translation, so exact ontological strength remains disputed.",
    summary="Pudgalavādin schools defended a person dependent on the aggregates yet not reducible to identity with or difference from them. The position was used to explain ownership of action, continuity, moral responsibility, and liberation while formally rejecting a permanent Brahmanical ātman.",
    proponents=["Vātsīputrīya and Sāṃmitīya school authors", "Pudgalavādin interlocutors preserved in Buddhist scholastic sources"], era="ca. 3rd century BCE–10th century CE", year=-200,
    scope="A minority Buddhist account of real or irreducible personhood under constraints of impermanence and no-self.",
    keywords=["Pudgalavada", "pudgala", "person", "no-self", "karma", "continuity"],
    boundary="The pudgala is not safely translated as an eternal soul. Reconstructions must distinguish opponents' reports from surviving Personalist formulations and avoid treating all Pudgalavāda communities as doctrinally identical.",
    claim_type="historical personalist position", applies_to="Pudgalavādin responses to continuity, agency, and karmic ownership.", does_not="That Buddhism generally accepts a substantial self or that the exact doctrine is fully recoverable.",
    basis=["authoritative specialist reference", "peer-reviewed philosophical reconstruction"],
    questions=["Was the pudgala ultimately real, conventionally real, or deliberately indeterminate?", "How much of the received account reflects adversarial framing?"], sources=["pudgala_iep", "pudgala_oup"],
)

add(
    name="Sautrāntika representational perception and seed continuity",
    aliases=["Sautrāntika external realism", "ākāra-mediated perception", "Sautrāntika bīja continuity"],
    kind="Historical tradition", codes=["HT", "PP"],
    domain="Perception, representation & causal continuity", tradition="Sautrāntika currents in Indian Buddhist Abhidharma",
    status="reconstructed school family · attribution boundaries contested",
    status_note="'Sautrāntika' names shifting affiliations and doxographic constructions; views attributed to Vasubandhu or Dignāga are not uniformly school doctrines.",
    summary="Sautrāntika-associated arguments hold that cognition directly presents a mental form caused by an external object rather than apprehending the external particular without mediation. Seed or latent-disposition language explains how past events causally condition later mental episodes without all dharmas existing across three times.",
    proponents=["Sautrāntika-associated Abhidharma authors", "Vasubandhu in contested interpretive contexts"], era="ca. 1st century BCE–5th century CE", year=300,
    scope="Historical Buddhist accounts of indirect perception, momentariness, and diachronic causal efficacy.",
    keywords=["Sautrantika", "representation", "ākāra", "seeds", "momentariness", "perception"],
    boundary="The label is doxographically unstable, and 'representation' is an analytic translation rather than proof of a modern representational theory of mind.",
    claim_type="historical perception-and-continuity framework", applies_to="Arguments attributed to Sautrāntika currents about object causation and latent efficacy.", does_not="One uniform school doctrine or identity with contemporary indirect realism.",
    basis=["authoritative specialist history", "scholarly translation of a central polemical source"],
    questions=["Which theses belong to named authors rather than the later school label?", "How should ākāra and bīja be translated without importing modern ontology?"], sources=["mind_indian_buddhism", "abhidharmakosa"],
)

add(
    name="Early Buddhist consciousness–name-and-form reciprocal conditioning",
    aliases=["viññāṇa-nāmarūpa reciprocity", "consciousness and name-form in dependent arising"],
    kind="Historical tradition", codes=["HT", "MF"],
    domain="Consciousness, embodiment & dependent arising", tradition="Early Buddhist discourses",
    status="canonical causal pattern · interpretation contested",
    status_note="Discourses deploy dependent-arising sequences in different contexts; later schools disagree about temporal, rebirth, and moment-to-moment readings.",
    summary="The Mahānidāna discourse presents consciousness and name-and-form as mutually conditioning in the emergence and maintenance of an embodied experiential world. Consciousness is differentiated by conditions and objects rather than treated as an independent, permanent subject.",
    proponents=["Early Buddhist discourse traditions", "later Buddhist interpreters with divergent models"], era="early Buddhist oral/textual strata; continuing interpretation", year=-300,
    scope="Canonical relations among consciousness, psycho-physical organization, sense bases, contact, and experience.",
    keywords=["vinnana", "nama-rupa", "dependent arising", "embodiment", "condition", "early Buddhism"],
    boundary="Reciprocal conditioning does not establish a cosmic consciousness, Cartesian interactionism, or one agreed twelve-link chronology. Viññāṇa and nāma-rūpa carry context-sensitive meanings.",
    claim_type="canonical conditional-process account", applies_to="Early Buddhist analysis of consciousness as dependently arising with name-and-form.", does_not="A permanent bearer of rebirth or an experimentally isolated causal circuit.",
    basis=["primary canonical translation", "authoritative philosophical analysis"],
    questions=["Are the relevant sequences primarily diachronic, synchronic, or intentionally multiscalar?", "How do early recensions and later Abhidharma systems repartition nāma and rūpa?"], sources=["dn15", "naturalism_india"],
)

add(
    name="Tsongkhapa's denial of reflexive awareness and foundational consciousness",
    aliases=["Geluk rejection of svasaṃvedana", "Tsongkhapa on conventional self and mind"],
    kind="Philosophical position", codes=["PP", "HT"],
    domain="Self-awareness, memory & conventional person", tradition="Geluk Madhyamaka in Tibetan Buddhism",
    status="foundational Geluk position · disputed by rival Tibetan schools",
    status_note="The denial targets specific reified models of self-cognition and substrate consciousness while retaining ordinary conventional knowledge and persons.",
    summary="Tsongkhapa rejects an intrinsically self-present cognition that validates itself independently, and he does not use a foundational store consciousness to secure continuity. Memory and conventional self-reference are explained within dependent, transactionally warranted causal processes without an ultimately grounded mental subject.",
    proponents=["Tsongkhapa", "Geluk scholastic interpreters"], era="14th–15th centuries; living Geluk debate", year=1400,
    scope="A Geluk account of self-knowledge, memory, conventional personhood, and the absence of intrinsic mental foundations.",
    keywords=["Tsongkhapa", "Geluk", "self-awareness", "svasaṃvedana", "conventional self", "emptiness"],
    boundary="This is not a denial that people know their mental states. 'Self-awareness' translates a technical target whose scope differs across Indian and Tibetan debates.",
    claim_type="school-specific anti-foundational position", applies_to="Tsongkhapa's critique of reflexive cognition and foundational consciousness.", does_not="Behaviorism, eliminativism about persons, or a consensus across Tibetan Buddhism.",
    basis=["authoritative specialist reference", "specialist intellectual biography"],
    questions=["Which forms of first-person access remain conventionally admissible?", "How do later Geluk authors explain memory without self-validating cognition?"], sources=["gelukpa", "tsongkhapa"],
)

add(
    name="Sikh haumai–sahaj transformation of mind",
    aliases=["haumai and sahaj in Sikh philosophy", "egoic orientation and equipoised awareness"],
    kind="Historical tradition", codes=["HT", "PP"],
    domain="Self-orientation, attention & ethical awareness", tradition="Sikh philosophy and Gurmat exegesis",
    status="living scriptural-philosophical framework · translations contested",
    status_note="Haumai and sahaj have wide semantic ranges; contemporary Sikh philosophers reject simple equivalence with ego and altered state.",
    summary="Sikh texts analyze haumai as a self-centered orientation that structures desire, separation, and misrecognition. Practices of remembrance, service, truthful living, and attention cultivate sahaj: an integrated ease or equipoise in which awareness and action are aligned with hukam rather than organized around possessive selfhood.",
    proponents=["Guru Nānak and the Sikh Guru textual tradition", "contemporary Sikh philosophers and exegetes"], era="15th century–present", year=1500,
    scope="A scriptural and philosophical account of self-centered cognition and ethically transformed awareness.",
    keywords=["Sikh", "haumai", "sahaj", "hukam", "mind", "selfhood", "attention"],
    boundary="Haumai is not merely healthy autobiographical ego, and sahaj is not a decontextualized peak experience. The record does not reduce Sikh practice to private meditation.",
    claim_type="living ethical-phenomenological framework", applies_to="Sikh accounts of distorted self-relation and cultivated clarity in action.", does_not="A clinical ego-disorder model or a uniform translation accepted by all Sikh communities.",
    basis=["authoritative specialist reference", "scholarly ethics synthesis"],
    questions=["How do haumai, manmukh, gurmukh, and hukam relate across textual strata?", "How can sahaj be described without turning a normative way of life into a state score?"], sources=["sikh_philosophy", "sikh_ethics"],
)

add(
    name="Classical Āyurvedic manas faculty model",
    aliases=["Charaka model of manas", "Ayurvedic mind-sense coordinator", "manas in classical Ayurveda"],
    kind="Historical tradition", codes=["HT", "MF"],
    domain="Mind, senses, attention & health", tradition="Classical Āyurveda, especially Caraka traditions",
    status="historical medical psychology · school and text differences remain",
    status_note="Caraka, Suśruta, and later compendia differ on location and function; modern clinical comparisons are interpretive rather than direct equivalences.",
    summary="Classical Āyurvedic analyses position manas as a selective coordinator linking self, sensory faculties, objects, and action. Attention, cognition, memory, resolve, conduct, bodily constitution, and health interact within a psycho-somatic system rather than a sharply separated mind substance.",
    proponents=["Caraka Saṃhitā textual tradition", "Suśruta and later Āyurvedic commentators with differences"], era="early centuries CE–present medical reception", year=200,
    scope="A classical medical model of attention, sensory coordination, cognition, conduct, and mental health.",
    keywords=["Ayurveda", "manas", "senses", "attention", "memory", "health"],
    boundary="Manas is not simply the modern brain or a psychiatric module. Classical disease categories and locations should not be mapped one-to-one onto current diagnoses or anatomy.",
    claim_type="historical medical-faculty model", applies_to="Classical Āyurvedic explanations of mental function within embodied health.", does_not="Modern diagnostic validity or a single unchanged account across all Āyurvedic texts.",
    basis=["institutional textual commentary", "peer-reviewed historical-clinical review"],
    questions=["How do Caraka and Suśruta differ about location and causal role?", "Which current uses preserve rather than retrofit the classical categories?"], sources=["charaka_manas", "ayurveda_mind"],
)

add(
    name="Āyurvedic sattva–rajas–tamas mental-constitution model",
    aliases=["mānasa prakṛti", "Ayurvedic triguna psychology", "sattvic rajasic tamasic mind types"],
    kind="Historical tradition", codes=["HT", "MF"],
    domain="Temperament, mental health & cultivation", tradition="Classical and contemporary Āyurvedic psychology",
    status="living traditional classification · psychometric translation unsettled",
    status_note="Texts and clinicians use guṇa language normatively and medically; recent inventories do not retroactively validate the historical construct.",
    summary="Āyurvedic texts describe mental constitution through varying predominance and interaction of sattva, rajas, and tamas, associated respectively with clarity, activation, and obscuration or inertia. The scheme connects temperament, conduct, susceptibility, and cultivation while treating all three as contextually operative rather than fixed Western personality types.",
    proponents=["Caraka and later Āyurvedic textual traditions", "contemporary Āyurvedic researchers"], era="classical period–present", year=300,
    scope="Traditional classification of mental dispositions and their relevance to health and conduct.",
    keywords=["Ayurveda", "sattva", "rajas", "tamas", "manasa prakriti", "temperament"],
    boundary="Guṇas are not DSM diagnoses, Big Five traits, or immutable essences. Their meanings differ between Sāṃkhya metaphysics, the Bhagavad Gītā, and medical texts.",
    claim_type="traditional temperament framework", applies_to="Āyurvedic descriptions of mental constitution, imbalance, and cultivation.", does_not="Cross-cultural psychometric equivalence or biological determination of personality.",
    basis=["peer-reviewed textual analysis", "peer-reviewed historical-clinical context"],
    questions=["Which source-specific meanings are obscured by a single triguna scale?", "Can contemporary measures show validity without reifying normative categories?"], sources=["manasa_prakruti", "ayurveda_mind"],
)

add(
    name="Jaina leśyā soul-coloration model",
    aliases=["six leśyās", "karmic coloration of jīva", "Uttarādhyayana leśyā taxonomy"],
    kind="Historical tradition", codes=["HT", "MF"],
    domain="Conscious self, affective disposition & karma", tradition="Jaina philosophy and Śvetāmbara canonical exegesis",
    status="canonical-classificatory model · sectarian and commentarial variation",
    status_note="Color language can be literal, karmic, ethical, affective, or imagistic depending on source and commentary.",
    summary="Jaina sources classify leśyā as ways karmic matter and affective-moral disposition color the embodied jīva. Six color terms order destructive through increasingly purified orientations, illustrated in the Uttarādhyayana by travelers responding differently to a fruit tree.",
    proponents=["Uttarādhyayana-sūtra tradition", "Jaina philosophers and commentators"], era="canonical Jaina period–present", year=400,
    scope="A Jaina model relating conscious soul, karmic embodiment, affect, intention, and ethical transformation.",
    keywords=["Jain", "lesya", "jiva", "karma", "color", "affect", "purification"],
    boundary="Leśyā is not aura photography, racial coloration, or a modern personality test. The familiar six-color scheme is text- and tradition-specific and must not replace the broader Jaina account of consciousness.",
    claim_type="historical karmic-affective classification", applies_to="Jaina explanations of how disposition and karmic matter condition embodied consciousness.", does_not="Empirically visible soul colors or a complete psychology of every Jaina school.",
    basis=["primary-text scholarly portal", "authoritative specialist philosophy entry"],
    questions=["How do canonical and later technical accounts distinguish dravya- and bhāva-leśyā?", "What is metaphorical, ontological, and ethically pedagogical in color attribution?"], sources=["uttaradhyayana", "jaina_sep"],
)

# --- Chinese, Korean, and Japanese distinctions -----------------------------

add(
    name="Guanzi Neiye heart-mind and vital-energy cultivation",
    aliases=["Inward Training model", "Neiye xin-qi-jing cultivation", "inner cultivation in the Guanzi"],
    kind="Historical tradition", codes=["HT", "MF"], domain="Heart-mind, attention, breath & affect regulation", tradition="Early Chinese inner-cultivation texts",
    status="early textual model · authorship and dating are composite",
    status_note="The Neiye is transmitted within the composite Guanzi; its vocabulary overlaps but is not identical with later Daoist, medical, or qigong systems.",
    summary="The Neiye links a settled and well-ordered heart-mind with refined vital energy, regulated breathing, balanced affect, and the arrival of numinous awareness. Cultivation is embodied and ethical: agitation disperses vital resources, while alignment, stillness, and attention make reliable perception and action possible.",
    proponents=["Neiye textual stratum of the Guanzi", "early Chinese inner-cultivation communities"], era="ca. 4th century BCE; later Daoist reception", year=-350,
    scope="An early Chinese model of embodied attention, affect, breath, and heart-mind regulation.", keywords=["Neiye", "xin", "qi", "jing", "breath", "stillness", "cultivation"],
    boundary="Qi is not automatically a measurable physical energy, and the Neiye should not be retrofitted as modern qigong neuroscience or treated as a text by a single known author.",
    claim_type="historical embodied-cultivation model", applies_to="The Neiye's relations among heart-mind, breathing, affect, and vital refinement.", does_not="A clinical breathing protocol or a universal Daoist theory of consciousness.",
    basis=["primary bilingual digital edition", "authoritative philosophy-of-mind analysis"], questions=["Which concepts predate later Daoist systematization?", "How should numinous awareness be translated without making it either supernatural fact or mere attention?"], sources=["neiye", "chinese_mind"],
)

add(
    name="Laozian empty and still heart-mind",
    aliases=["Daodejing emptiness of xin", "Laozi stillness and unlearning", "Daoist empty heart-mind"],
    kind="Historical tradition", codes=["HT", "PP"], domain="Attention, desire & noncoercive action", tradition="Daodejing textual tradition",
    status="canonical Daoist orientation · chapter readings contested",
    status_note="The received text has multiple recensions, and political, ethical, mystical, and cultivation readings assign different weight to heart-mind language.",
    summary="The Daodejing recommends reducing acquisitive desire and rigid discriminations so the heart-mind can become empty, still, and responsive. Knowing is recast as noncoercive attunement expressed through wuwei rather than as detached representation or accumulation of propositions.",
    proponents=["Daodejing textual traditions", "Laozi interpreters"], era="4th–3rd centuries BCE; continuing reception", year=-300,
    scope="A textual account of desire, cognitive fixation, stillness, responsiveness, and noncoercive conduct.", keywords=["Laozi", "Daodejing", "xin", "emptiness", "stillness", "wuwei"],
    boundary="Emptying the heart-mind does not mean destroying cognition, emotional numbness, or a generic mindfulness technique. 'Laozi' does not securely identify one historical author.",
    claim_type="historical attentional-ethical orientation", applies_to="Daodejing claims about desire, learning, stillness, and responsive action.", does_not="A single systematic psychology shared by all Daoist schools.",
    basis=["primary bilingual digital edition", "authoritative specialist reference"], questions=["How do Mawangdui and received recensions affect key readings?", "Is emptiness primarily political, ethical, contemplative, or deliberately multivalent?"], sources=["daodejing", "laozi"],
)

add(
    name="Zhang Zai's qi-based mind and enlarged heart",
    aliases=["Zhang Zai on qi and xin", "Great Vacuity and mind", "enlarging the heart-mind in Zhang Zai"],
    kind="Philosophical position", codes=["PP", "HT"], domain="Mind, embodiment, qi & moral perception", tradition="Northern Song Confucian philosophy",
    status="foundational Song position · later reconstructions differ",
    status_note="Zhang's surviving writings are textually layered, and later Cheng-Zhu appropriation can obscure his distinctive account.",
    summary="Zhang Zai treats persons and things as patterned condensations and dispersals of qi, rejecting a separately existing mental substance. The cultivated heart-mind can be enlarged beyond private sensory limits to recognize kinship and shared constitution with the wider world.",
    proponents=["Zhang Zai"], era="11th century; later Neo-Confucian reception", year=1070,
    scope="A qi-based account of embodied mind, perception, moral enlargement, and continuity with the world.", keywords=["Zhang Zai", "qi", "xin", "Great Vacuity", "embodiment", "moral perception"],
    boundary="Qi should not be translated simply as matter or energy; 'one body with the world' is an ethical-metaphysical claim, not evidence for one shared phenomenal subject.",
    claim_type="historical qi-based philosophy of mind", applies_to="Zhang Zai's relation among psychophysical constitution, perception, and moral cultivation.", does_not="Reductive materialism, field physics, or undifferentiated cosmic consciousness.",
    basis=["authoritative thinker-specific reference", "authoritative Chinese-mind framework"], questions=["How does the Great Vacuity differ from emptiness or substance?", "What changes epistemically when the heart-mind is 'enlarged'?"], sources=["zhang_zai", "chinese_mind"],
)

add(
    name="Cheng Hao's one-body humane awareness",
    aliases=["Cheng Hao on forming one body", "Mingdao humane heart-mind", "ren as one-body awareness"],
    kind="Philosophical position", codes=["PP", "HT"], domain="Affective awareness, relation & moral agency", tradition="Northern Song Confucian philosophy",
    status="historically influential · distinct from later school syntheses",
    status_note="Cheng Hao and Cheng Yi are often grouped, but their surviving sayings and later lineages support different emphases.",
    summary="Cheng Hao associates ren with an unblocked affective responsiveness in which a person forms one body with the myriad things. Moral failure is numbness or obstruction, while cultivation restores responsive awareness rather than escaping embodied relations.",
    proponents=["Cheng Hao"], era="11th century; continuing Neo-Confucian reception", year=1075,
    scope="An affective-relational account of heart-mind, humane responsiveness, and moral cultivation.", keywords=["Cheng Hao", "ren", "one body", "xin", "affect", "responsiveness"],
    boundary="'One body' is not a claim that all organisms literally share one nervous system or phenomenal field, and Cheng Hao's sayings should not be merged with Cheng Yi's system.",
    claim_type="historical affective-relational position", applies_to="Cheng Hao's model of humane awareness and obstruction.", does_not="A universal Chinese collectivism or metaphysical fusion of individual subjects.",
    basis=["authoritative thinker-specific reference", "authoritative emotions analysis"], questions=["How does bodily numbness function as analogy and moral diagnosis?", "Which later xinxue readings amplify themes only implicit in Cheng Hao?"], sources=["cheng_hao", "chinese_emotions"],
)

add(
    name="Cheng Yi's heart-mind, nature, and feeling distinction",
    aliases=["Yichuan moral psychology", "Cheng Yi's reverent-attentiveness psychology", "mind governing nature and emotions"],
    kind="Philosophical position", codes=["PP", "HT"], domain="Heart-mind, nature, emotion & deliberation", tradition="Northern Song Cheng-Zhu lineage",
    status="foundational Neo-Confucian formulation · textual attribution requires care",
    status_note="The Cheng brothers' statements were edited by later students; attributing shared sayings to one brother can be uncertain.",
    summary="Cheng Yi differentiates the normative patterns of human nature, the governing heart-mind, and feelings as nature becomes active in circumstances. Cultivation uses reverent attentiveness and inquiry to keep emotion responsive to pattern without treating emotion itself as an alien substance.",
    proponents=["Cheng Yi"], era="11th century; Cheng-Zhu reception", year=1080,
    scope="A moral-psychological relation among nature, active feeling, cognition, attention, and judgment.", keywords=["Cheng Yi", "xin", "xing", "qing", "jing", "emotion"],
    boundary="The distinctions are not Cartesian faculties, and later Zhu Xi systematization must be identified rather than silently assigned to Cheng Yi.",
    claim_type="historical moral-psychological framework", applies_to="Cheng Yi's accounts of mind, nature, feeling, and reverent attentiveness.", does_not="Emotion suppression or a settled dualism of principle and matter.",
    basis=["authoritative thinker-specific reference", "authoritative emotions analysis"], questions=["Which sayings can be securely attributed to Cheng Yi?", "How does reverent attentiveness regulate without eliminating affect?"], sources=["cheng_yi", "chinese_emotions"],
)

add(
    name="Lu Jiuyuan's heart-mind as principle",
    aliases=["Lu Xiangshan moral inwardness", "the universe is my mind", "Lu Jiuyuan on xin and li"],
    kind="Philosophical position", codes=["PP", "HT"], domain="Moral awareness, self-reflection & principle", tradition="Southern Song school of heart-mind",
    status="foundational xinxue position · slogan readings require context",
    status_note="Fragments, letters, and recorded sayings support multiple readings; later Wang Yangming reception should not replace Lu's own formulations.",
    summary="Lu Jiuyuan emphasizes that moral principle is not an external object added to the heart-mind: reflective recovery of its non-selfish clarity discloses normative order. Learning therefore prioritizes identifying and removing obscuring desires over indefinitely accumulating textual distinctions.",
    proponents=["Lu Jiuyuan"], era="12th century; later school-of-mind reception", year=1180,
    scope="A Confucian account of moral awareness, introspective recovery, desire, and learning.", keywords=["Lu Jiuyuan", "xin", "li", "moral awareness", "self-reflection", "xinxue"],
    boundary="'The universe is my mind' is not automatically subjective idealism or solipsism. Lu's position is distinct from the already cataloged Wang Yangming school.",
    claim_type="historical heart-mind philosophy", applies_to="Lu Jiuyuan's claims about immanent moral principle and reflective cultivation.", does_not="That physical reality is created by an individual mind or that textual learning is worthless.",
    basis=["authoritative thinker-specific reference", "authoritative Chinese epistemology"], questions=["How idealist is Lu's rhetoric when read in Song categories?", "What evidential role does inward moral recognition have?"], sources=["lu_jiuyuan", "chinese_mind"],
)

add(
    name="Wang Fuzhi's qi-based embodied heart-mind",
    aliases=["Wang Fuzhi psychophysical monism", "Chuanshan on xin and qi", "embodied knowing in Wang Fuzhi"],
    kind="Philosophical position", codes=["PP", "HT"], domain="Embodied cognition, affect & qi", tradition="Late Ming–early Qing Confucian philosophy",
    status="major early-modern Chinese position · interpretations of monism vary",
    status_note="Calling the view materialism or monism can obscure Wang's process vocabulary and normative commitments.",
    summary="Wang Fuzhi treats heart-mind, perception, desire, and thought as refined organizations and activities of qi rather than operations of an immaterial substance. Knowledge emerges through embodied engagement with things, history, and patterned affective response.",
    proponents=["Wang Fuzhi"], era="17th century; modern scholarly recovery", year=1670,
    scope="A process account of embodied mind, sensory engagement, affect, and knowledge.", keywords=["Wang Fuzhi", "qi", "xin", "embodied cognition", "affect", "process"],
    boundary="Qi-based embodiment should not be called neuroscience or crude materialism; Wang's cosmology and ethics are inseparable from the cognitive claims.",
    claim_type="historical psychophysical process position", applies_to="Wang Fuzhi's treatment of cognition and affect as embodied qi activity.", does_not="Identity theory, eliminative materialism, or a universal Chinese monism.",
    basis=["authoritative thinker-specific reference", "authoritative Chinese-mind framework"], questions=["How should refined qi be distinguished from both matter and spirit?", "What role do historical practice and emotion play in warrant?"], sources=["wang_fuzhi", "chinese_mind"],
)

add(
    name="Dai Zhen's embodied desire and sympathetic knowing",
    aliases=["Dai Zhen moral psychology", "Qing evidential account of desire", "Dai Dongyuan on feeling and judgment"],
    kind="Philosophical position", codes=["PP", "HT"], domain="Desire, feeling, deliberation & moral cognition", tradition="Qing evidential learning and Confucian philosophy",
    status="major revisionary Confucian position · continuing interpretation",
    status_note="Dai's philological reconstruction is normative philosophy, not only dictionary work; his critique targets specific Song-Ming uses of principle.",
    summary="Dai Zhen rejects models that make moral purity the removal of bodily desire and feeling. He treats desires and affects as indispensable evidence about benefit and harm, with sympathetic extension and disciplined inquiry transforming them into responsible judgment.",
    proponents=["Dai Zhen"], era="18th century; modern recovery", year=1770,
    scope="An embodied moral psychology of desire, emotion, sympathy, inquiry, and agency.", keywords=["Dai Zhen", "desire", "qing", "sympathy", "deliberation", "embodiment"],
    boundary="Dai does not endorse every desire as good, and his appeal to embodiment is not a modern emotivist or utilitarian theory.",
    claim_type="historical embodied moral psychology", applies_to="Dai Zhen's critique of disembodied principle and his account of affective deliberation.", does_not="Hedonism or the claim that reasons reduce to raw feeling.",
    basis=["authoritative thinker-specific reference", "authoritative emotions analysis"], questions=["How does philology constrain Dai's moral theory?", "What transforms partial desire into sympathetic judgment?"], sources=["dai_zhen", "chinese_emotions"],
)

add(
    name="Wŏnhyo's one-mind and essence–function model",
    aliases=["Wonhyo one mind", "Korean Buddhist che-yong model", "harmonization of doctrinal disputes in Wŏnhyo"],
    kind="Historical tradition", codes=["HT", "MF"], domain="Mind, delusion, awakening & doctrinal harmonization", tradition="Silla Korean Buddhism",
    status="foundational Korean Buddhist synthesis · source-specific readings differ",
    status_note="Wŏnhyo comments on multiple imported texts and uses one-mind language differently by context; later East Asian essence–function schemes are not all his.",
    summary="Wŏnhyo uses one-mind and essence–function analysis to explain how deluded and awakened cognition can arise without positing two separate realities. His method of harmonizing disputes identifies the assumptions and practical standpoints from which apparently opposed Buddhist claims function.",
    proponents=["Wŏnhyo"], era="7th century; continuing Korean Buddhist reception", year=680,
    scope="A Korean Buddhist model of mind, delusion, awakening, and perspectival reconciliation.", keywords=["Wonhyo", "one mind", "essence-function", "harmonization", "delusion", "awakening"],
    boundary="One mind is not securely a single cosmic subject, and Wŏnhyo's harmonization does not declare every doctrine equivalent or true in the same respect.",
    claim_type="historical Buddhist mind-and-hermeneutics model", applies_to="Wŏnhyo's explanations of delusion, awakening, and doctrinal standpoint.", does_not="A pan-Korean theory or generic perennialism.",
    basis=["primary-source scholarly translation", "authoritative Korean-philosophy context"], questions=["How does one-mind vocabulary shift across Wŏnhyo's commentaries?", "What criteria limit rather than trivialize harmonization?"], sources=["wonhyo_book", "korean_philosophy"],
)

add(
    name="Chinul's sudden awakening and gradual cultivation model",
    aliases=["Pojo Chinul sudden-gradual model", "Korean Seon mind cultivation", "awakening followed by cultivation"],
    kind="Historical tradition", codes=["HT", "MF"], domain="Awareness, insight, habit & cultivation", tradition="Korean Seon Buddhism",
    status="foundational Korean Seon framework · multiple practice paths",
    status_note="Chinul integrates doctrinal and meditation sources; sudden/gradual labels mark different dimensions rather than a single fixed sequence for everyone.",
    summary="Chinul distinguishes an initial recognition of mind's nature from the gradual attenuation of entrenched habits and affective-cognitive obscurations. He integrates scriptural understanding, calm and insight, and later hwadu practice without treating a moment of insight as completed transformation.",
    proponents=["Pojo Chinul", "Korean Seon lineages"], era="12th–13th centuries; living reception", year=1200,
    scope="A soteriological model relating immediate insight, metacognitive recognition, habit, and ongoing practice.", keywords=["Chinul", "Seon", "sudden awakening", "gradual cultivation", "hwadu", "habit"],
    boundary="Sudden awakening is not a reaction-time event or proof of permanent enlightenment, and gradual cultivation is not generic behavioral therapy.",
    claim_type="historical transformation model", applies_to="Chinul's relation between recognition and post-awakening cultivation.", does_not="A universal sequence shared by all Zen or Seon schools.",
    basis=["authoritative Korean-philosophy context", "peer-reviewed practice-specific analysis"], questions=["How do Chinul's earlier and later practice recommendations relate?", "What counts as genuine recognition rather than conceptual assent?"], sources=["korean_philosophy", "jinul_huatou"],
)

add(
    name="Korean Four–Seven debate on mind and emotion",
    aliases=["Four Beginnings and Seven Emotions debate", "sadan-chiljeong debate", "T'oegye-Kobong and Yulgok-Ugye debate"],
    kind="Historical tradition", codes=["HT", "PP"], domain="Emotion, moral motivation & psychophysical activity", tradition="Joseon Korean Confucianism",
    status="major historical debate · internally plural",
    status_note="The debate unfolded in multiple exchanges and changed participants' formulations; it cannot be reduced to simple rational-emotional dualism.",
    summary="Joseon philosophers debated how Mencius's Four Beginnings and the Seven Emotions arise through principle and psychophysical qi. T'oegye, Kobong, Yulgok, and Ugye offered distinct accounts of motivational source, moral valence, and how one heart-mind governs nature and feeling.",
    proponents=["Yi Hwang (T'oegye)", "Ki Taesŭng (Kobong)", "Yi I (Yulgok)", "Sŏng Hon (Ugye)"], era="16th century; continuing Korean philosophical study", year=1560,
    scope="A named Korean debate about affective episodes, moral cognition, and li-qi psychophysics.", keywords=["Four-Seven", "Korean Confucianism", "emotion", "li", "qi", "heart-mind"],
    boundary="The Four and Seven are inherited textual categories, not four basic emotions versus seven universal affects. Participants revised positions over time.",
    claim_type="historical psychophysical debate", applies_to="Joseon accounts of how moral and ordinary emotions arise and are evaluated.", does_not="A single Korean theory of emotion or modern affective neuroscience.",
    basis=["authoritative debate-specific reference", "authoritative Korean-philosophy context"], questions=["How did each exchange revise the li-qi relation?", "Can moral valence be explained at origination, expression, or reflective endorsement?"], sources=["korean_confucianism", "korean_philosophy"],
)

add(
    name="Dōgen's body-mind dropping and perspectival experience",
    aliases=["shinjin datsuraku", "dropping off body-mind", "Dogen on bodymind and practice-realization"],
    kind="Historical tradition", codes=["HT", "PP"], domain="Embodiment, self, time & practice", tradition="Japanese Sōtō Zen",
    status="foundational Zen philosophy · phrase and corpus interpretation contested",
    status_note="Dōgen's fascicles span genres and dates; translations of shinjin datsuraku, uji, and genjōkōan carry substantial interpretive choices.",
    summary="Dōgen treats body and mind as a nonseparable practice-event rather than two substances, and describes realization as the dropping away of self-grasping through embodied zazen. Experience is perspectival and temporal: beings disclose worlds from situated activity rather than confronting a ready-made object realm from outside.",
    proponents=["Dōgen Kigen", "Sōtō Zen interpreters"], era="13th century; living reception", year=1240,
    scope="A practice-based account of bodymind, self-forgetting, temporality, and situated disclosure.", keywords=["Dogen", "bodymind", "shinjin datsuraku", "zazen", "being-time", "self"],
    boundary="Body-mind dropping is not dissociation, bodily disappearance, or proof of metaphysical idealism. Different Shōbōgenzō redactions must be tracked.",
    claim_type="historical embodied phenomenological position", applies_to="Dōgen's practice-realization account of self, embodiment, and experience.", does_not="A universal Japanese mind-body theory or a clinical altered state.",
    basis=["authoritative specialist reference", "primary-source scholarly translation"], questions=["How do early and late fascicles qualify practice-realization?", "What is lost when shinjin is divided into Western mind and body substances?"], sources=["dogen_sep", "shobogenzo"],
)

add(
    name="Watsuji's aidagara relational self",
    aliases=["Watsuji betweenness", "ningen relational personhood", "aidagara ethics of self"],
    kind="Philosophical position", codes=["PP"], domain="Relational self, milieu & ethics", tradition="Modern Japanese philosophy",
    status="major modern position · political context requires scrutiny",
    status_note="Watsuji's relational ethics is philosophically influential, while his nationalism and wartime context remain essential to critical evaluation.",
    summary="Watsuji analyzes human existence as ningen: at once individual and social, constituted through aidagara or betweenness and through climatic-historical milieu. Selfhood emerges in a repeated negation between individual separation and participation in relational wholes.",
    proponents=["Watsuji Tetsurō"], era="20th century–present reception", year=1937,
    scope="A relational account of personhood, embodied milieu, individuality, and social ethics.", keywords=["Watsuji", "aidagara", "ningen", "relational self", "milieu", "ethics"],
    boundary="Relational constitution does not erase individual agency or justify state collectivism; critical reception must address Watsuji's political entanglements.",
    claim_type="modern relational-self position", applies_to="Watsuji's account of individuality-in-betweenness and embodied milieu.", does_not="That Japanese people are inherently collectivist or that social wholes have unlimited moral priority.",
    basis=["authoritative specialist reference", "primary-source scholarly translation"], questions=["Can aidagara secure critique of oppressive relations?", "How should milieu be distinguished from geographic or cultural determinism?"], sources=["watsuji_sep", "watsuji_book"],
)

add(
    name="Zongmi's knowing awareness and Buddha-nature",
    aliases=["Zongmi on numinous awareness", "Guifeng Zongmi knowing mind", "lingzhi and the origin of humanity"],
    kind="Historical tradition", codes=["HT", "PP"], domain="Awareness, Buddha-nature & causal explanation", tradition="Tang-dynasty Huayan and Chan synthesis",
    status="influential Buddhist synthesis · doctrinal hierarchy contested",
    status_note="Zongmi ranks teachings for soteriological purposes; later uses of 'awareness' can overstate similarity to contemporary phenomenal consciousness.",
    summary="Zongmi argues that ordinary thought and delusion presuppose a basic capacity of knowing awareness, interpreted through Buddha-nature and one-mind texts. His Inquiry into the Origin of Humanity compares Confucian, Daoist, and Buddhist accounts while locating bodily and mental processes within a graded Buddhist causal story.",
    proponents=["Guifeng Zongmi"], era="9th century; continuing East Asian Buddhist reception", year=830,
    scope="A Huayan-Chan account of basic knowing, delusion, embodiment, and doctrinal levels.", keywords=["Zongmi", "lingzhi", "knowing awareness", "Buddha-nature", "Huayan", "Chan"],
    boundary="Knowing awareness is not automatically an eternal individual witness or a modern phenomenal property; Zongmi's hierarchy should not be treated as neutral comparative taxonomy.",
    claim_type="historical Buddhist awareness framework", applies_to="Zongmi's explanation of awareness, delusion, and teaching classification.", does_not="One cosmic experiencer or consensus among Huayan and Chan authors.",
    basis=["primary-source scholarly translation", "authoritative specialist reference"], questions=["Is knowing awareness ontological, phenomenological, soteriological, or all three?", "How does Zongmi distinguish it from conditioned thought without reifying a self?"], sources=["zongmi_book", "huayan_sep"],
)

add(
    name="Huineng tradition of no-thought and self-nature",
    aliases=["wunian no-thought", "Platform Sutra mind practice", "Huineng sudden awakening rhetoric"],
    kind="Historical tradition", codes=["HT", "MF"], domain="Thought, nonattachment & awareness", tradition="Platform Sutra and Chinese Chan",
    status="foundational Chan textual tradition · authorship and layers contested",
    status_note="The Platform Sutra developed through editions after Huineng; 'Huineng's doctrine' is partly a lineage-making textual construction.",
    summary="The Platform Sutra describes no-thought not as an empty absence of mental events but as thoughts arising without fixation or attachment. Self-nature and sudden awakening language frames recognition and conduct within Chan lineage, precepts, and practice.",
    proponents=["Platform Sutra textual community", "Huineng as attributed lineage figure"], era="8th–13th century textual development; living reception", year=800,
    scope="A Chan model of thought without attachment, sudden recognition, and enacted practice.", keywords=["Huineng", "Platform Sutra", "no-thought", "wunian", "self-nature", "Chan"],
    boundary="No-thought does not mean unconsciousness or cognitive blankness, and the received text cannot be treated as a verbatim transcript of one historical teacher.",
    claim_type="historical nonattachment-and-awareness model", applies_to="Platform Sutra accounts of thought, fixation, and sudden awakening.", does_not="Thought suppression, a universal Zen doctrine, or a laboratory-validated state.",
    basis=["primary-source scholarly translation", "authoritative Chan reference"], questions=["How do Dunhuang and later editions change key formulations?", "What distinguishes nonattachment from absent metacognitive monitoring?"], sources=["platform_sutra", "chan_sep"],
)

add(
    name="Yuasa Yasuo's cultivated bodymind model",
    aliases=["Yuasa mind-body cultivation", "body schema through practice in Yuasa", "Eastern bodymind theory"],
    kind="Philosophical position", codes=["PP", "MF"], domain="Bodymind, skill, attention & cultivation", tradition="Modern Japanese comparative philosophy",
    status="modern comparative framework · generalizations require review",
    status_note="Yuasa draws across Japanese and Asian practices; claims about 'Eastern' and 'Western' tendencies require disaggregation.",
    summary="Yuasa argues that mind-body unity is not merely a metaphysical fact but an achievement transformed through disciplined practice. Skill, attention, bodily habit, and affect reorganize the relation between reflective intention and prereflective bodily agency.",
    proponents=["Yuasa Yasuo"], era="20th century–present reception", year=1987,
    scope="A comparative model of how embodied practice changes cognition, agency, and self-experience.", keywords=["Yuasa", "bodymind", "cultivation", "skill", "habit", "attention"],
    boundary="The model should not essentialize East and West, and traditional cultivation claims are not established by philosophical comparison alone.",
    claim_type="modern cultivated-bodymind framework", applies_to="Yuasa's analysis of practice-mediated psychophysical integration.", does_not="A pan-Asian consensus or empirical proof of specific subtle-body mechanisms.",
    basis=["primary philosophical monograph", "authoritative Japanese-philosophy context"], questions=["Which claims are phenomenological, historical, or testable?", "How can comparative contrasts be retained without civilizational essentialism?"], sources=["yuasa_body", "japanese_philosophy"],
)

# --- Arabic-Islamic and Jewish distinctions ---------------------------------

add(
    name="Al-Kindī's tripartite immaterial-soul psychology",
    aliases=["al-Kindi on the soul", "Kindian rational-animal-vegetative soul", "Discourse on the Soul"],
    kind="Historical tradition", codes=["HT", "PP"], domain="Soul, intellect, imagination & embodiment", tradition="Early Arabic falsafa",
    status="early philosophical synthesis · surviving account is fragmentary",
    status_note="Al-Kindī's psychological writings do not form one complete system, and several rely on Arabic paraphrases attributed to Greek authors.",
    summary="Al-Kindī presents the soul as an immaterial, unified substance with rational, irascible or animal, and appetitive or vegetative powers. Sensation and imagination operate through bodily organs, while rational purification and knowledge orient the soul beyond corporeal attachment.",
    proponents=["Abū Yūsuf Yaʿqūb al-Kindī"], era="9th century", year=850,
    scope="An early Arabic philosophical account of soul powers, bodily faculties, intellect, and postmortem perfection.", keywords=["al-Kindi", "soul", "intellect", "imagination", "tripartite", "falsafa"],
    boundary="The view combines Aristotelian, Platonic, and Arabic Neoplatonic materials and should not be labeled simply Aristotle's psychology or a fixed Islamic doctrine.",
    claim_type="historical faculty psychology", applies_to="Al-Kindī's surviving arguments and doxographies concerning soul and cognition.", does_not="A complete unified system or consensus among Muslim philosophers.",
    basis=["thinker-specific authoritative reference", "authoritative history of Arabic philosophy of mind"], questions=["Which surviving works are authentically Kindian?", "How were sensation and imagination meant to supply rational cognition?"], sources=["al_kindi", "arabic_mind"],
)

add(
    name="Abū Bakr al-Rāzī's three-soul moral psychology",
    aliases=["Rhazes three souls", "al-Razi spiritual medicine psychology", "rational-animal-vegetative souls"],
    kind="Historical tradition", codes=["HT", "PP"], domain="Reason, appetite, affect & moral therapy", tradition="Early Arabic philosophy and philosophical medicine",
    status="distinctive historical position · sources and doctrinal affiliation disputed",
    status_note="Reports of al-Rāzī's cosmology are partly hostile, while his Spiritual Medicine offers firmer evidence for therapeutic moral psychology.",
    summary="Al-Rāzī distinguishes rational or divine, animal, and vegetative soul-functions and assigns reason the task of governing appetite and passion. His Spiritual Medicine treats destructive emotion and compulsive desire through reflection, habituation, and correction of false valuation.",
    proponents=["Abū Bakr Muḥammad ibn Zakariyyā al-Rāzī"], era="9th–10th centuries", year=920,
    scope="A medical-philosophical model of rational governance, affect, appetite, and character therapy.", keywords=["al-Razi", "Rhazes", "soul", "reason", "appetite", "spiritual medicine"],
    boundary="Three 'souls' can denote powers rather than three independently conscious subjects. Reports of transmigration and five eternals require source criticism.",
    claim_type="historical moral-therapeutic psychology", applies_to="Al-Rāzī's account of faculties, passions, and rational self-treatment.", does_not="Modern psychotherapy efficacy or one orthodox Islamic psychology.",
    basis=["authoritative thinker-specific reference", "authoritative history of Arabic philosophy of mind"], questions=["Which metaphysical reports derive from opponents?", "How does bodily medicine interact with rational moral therapy?"], sources=["al_razi", "arabic_mind"],
)

add(
    name="Ibn Ṭufayl's unaided self-knowledge in Ḥayy ibn Yaqẓān",
    aliases=["Hayy ibn Yaqzan developmental epistemology", "Ibn Tufayl natural reason narrative", "solitary knower thought experiment"],
    kind="Historical tradition", codes=["HT", "MF"], domain="Cognitive development, self-knowledge & contemplation", tradition="Andalusian Arabic philosophy",
    status="philosophical narrative · interpretations of natural reason vary",
    status_note="The work is a crafted fiction engaging earlier Ḥayy traditions, philosophy, and revelation; it is not an empirical child-development report.",
    summary="Ibn Ṭufayl's Ḥayy develops without human language or society, progressing from perception and practical inference through anatomy, cosmology, self-knowledge, and contemplative awareness. The narrative tests what unaided embodied reason might reach and where symbolic religion and social pedagogy remain necessary.",
    proponents=["Abū Bakr Ibn Ṭufayl"], era="12th century; extensive Arabic, Hebrew, and European reception", year=1170,
    scope="A philosophical narrative about cognitive development, introspection, reason, and contemplative knowledge.", keywords=["Ibn Tufayl", "Hayy ibn Yaqzan", "self-knowledge", "development", "reason", "contemplation"],
    boundary="Ḥayy is a literary-philosophical construction, not a feral-child case, and the story does not simply oppose reason to religion.",
    claim_type="historical philosophical thought experiment", applies_to="Ibn Ṭufayl's staged account of learning and self-knowledge in isolation.", does_not="That language and social learning are actually unnecessary for human cognition.",
    basis=["authoritative thinker-specific reference", "primary historical translation"], questions=["Which stages depend covertly on the author's social and textual knowledge?", "How do embodiment and contemplative abstraction interact?"], sources=["ibn_tufayl", "hayy"],
)

add(
    name="Ikhwān al-Ṣafāʾ human–world soul hierarchy",
    aliases=["Brethren of Purity psychology", "microcosm-macrocosm soul model", "Ikhwan al-Safa faculties"],
    kind="Historical tradition", codes=["HT", "MF"], domain="Soul, faculties, cosmos & moral development", tradition="Ismaili-adjacent Arabic encyclopedic philosophy",
    status="encyclopedic school framework · authorship and affiliation debated",
    status_note="The Epistles are collective and stratified; their exact authors, date, and institutional relation to Ismailism remain scholarly disputes.",
    summary="The Ikhwān relate vegetative, animal, and rational human capacities to a hierarchy extending through nature, celestial souls, and universal soul. The person is a microcosm whose embodied faculties can be educated and purified through sciences, ethical fellowship, and spiritual practice.",
    proponents=["Anonymous Ikhwān al-Ṣafāʾ authors"], era="10th century; later Islamic and Jewish reception", year=970,
    scope="An encyclopedic model connecting human cognitive faculties, moral formation, and cosmic soul hierarchy.", keywords=["Ikhwan al-Safa", "soul", "microcosm", "faculties", "universal soul", "education"],
    boundary="Universal soul is not safely equated with one phenomenal subject, and the Brethren's collective authorship prevents attributing every epistle to a single thinker.",
    claim_type="historical encyclopedic soul framework", applies_to="Ikhwān accounts of faculty development and microcosm-macrocosm correspondence.", does_not="A uniform Ismaili doctrine or evidence for cosmic consciousness.",
    basis=["authoritative school-specific reference", "primary-source scholarly translation"], questions=["How do philosophical and scriptural registers interact across epistles?", "Which hierarchy claims are explanatory, pedagogical, or soteriological?"], sources=["ikhwan", "ikhwan_oup"],
)

add(
    name="Fakhr al-Dīn al-Rāzī's aware nonbodily self",
    aliases=["Fakhr al-Din al-Razi on self-awareness", "Rāzian soul arguments", "self distinct from bodily organs"],
    kind="Philosophical position", codes=["PP", "HT"], domain="Self-awareness, soul & bodily localization", tradition="Post-Avicennian Islamic theology and philosophy",
    status="major post-classical position · development across works",
    status_note="Al-Rāzī's conclusions and argumentative posture change across a large corpus; a single timeless doctrine is unsafe.",
    summary="Fakhr al-Dīn al-Rāzī argues that a person's immediate awareness of self is not awareness of any particular bodily organ, magnitude, or configuration. He uses introspective, medical, and dialectical considerations to defend a self not reducible to the body while critically revising Avicennan proofs.",
    proponents=["Fakhr al-Dīn al-Rāzī"], era="12th–13th centuries", year=1200,
    scope="Arguments concerning first-person awareness, bodily identity, and the ontology of the soul.", keywords=["Fakhr al-Din al-Razi", "self-awareness", "soul", "body", "introspection", "kalam"],
    boundary="Nonawareness of organs does not by itself establish substance dualism, and al-Rāzī's exploratory dialectic is not always final endorsement.",
    claim_type="historical self-and-soul position", applies_to="Al-Rāzī's arguments from self-awareness and bodily change.", does_not="One stable doctrine across all works or a modern introspection-based proof.",
    basis=["authoritative thinker-specific reference", "authoritative history of Arabic philosophy of mind"], questions=["Which chronological shifts are genuine revisions?", "What follows from first-person invariance about metaphysical substance?"], sources=["fakhr_razi", "arabic_mind"],
)

add(
    name="Abū al-Barakāt al-Baghdādī's self-awareness and lived time",
    aliases=["al-Baghdadi on temporal awareness", "Kitab al-Mu'tabar psychology", "Abu al-Barakat first-person time"],
    kind="Philosophical position", codes=["PP", "HT"], domain="Self-awareness, memory & temporality", tradition="Post-Avicennian Arabic philosophy",
    status="important revisionary position · limited translation access",
    status_note="Much of the Kitāb al-Muʿtabar remains inaccessible in modern translation, so claims depend heavily on specialist reconstruction.",
    summary="Abū al-Barakāt emphasizes continuous first-person awareness and treats time as inseparable from awareness of persistence and change rather than merely celestial motion. His psychology revises Avicenna on soul, cognition, memory, and the temporality of experience.",
    proponents=["Abū al-Barakāt al-Baghdādī"], era="11th–12th centuries", year=1120,
    scope="A post-Avicennian account of self-presence, memory, motion, and experienced time.", keywords=["Abu al-Barakat", "self-awareness", "time", "memory", "soul", "Baghdad"],
    boundary="The relation between awareness and time is a historical philosophical thesis, not a direct precursor of modern internal-clock models.",
    claim_type="historical temporal-self position", applies_to="Abū al-Barakāt's revisions of soul psychology and time.", does_not="A complete phenomenology available independently of specialist textual work.",
    basis=["authoritative thinker-specific reference", "authoritative field history"], questions=["How does continuous awareness coexist with interrupted attention and sleep?", "What textual evidence distinguishes phenomenological from cosmological time?"], sources=["abu_barakat", "arabic_mind"],
)

add(
    name="Ashʿarite created-cognition and acquisition framework",
    aliases=["Ashari kasb model", "created acts and acquired agency", "occasionalist cognition in Ash'arism"],
    kind="Historical tradition", codes=["HT", "PP"], domain="Cognition, agency & divine causation", tradition="Ashʿarite kalām",
    status="school family · formulations vary across theologians",
    status_note="Al-Ashʿarī, al-Bāqillānī, al-Juwaynī, and al-Ghazālī do not offer one unchanged theory of kasb or causation.",
    summary="Ashʿarite theologians commonly hold that momentary powers, cognitions, and acts are created by God while human agents acquire acts in a relation grounding command and responsibility. Later occasionalist formulations deny that created bodies or faculties independently necessitate their effects.",
    proponents=["Abū al-Ḥasan al-Ashʿarī", "al-Bāqillānī", "al-Juwaynī", "later Ashʿarite theologians with differences"], era="10th century–present scholastic reception", year=950,
    scope="A kalām framework for mental events, voluntary action, responsibility, and causal dependence.", keywords=["Ashari", "kasb", "acquisition", "cognition", "agency", "occasionalism"],
    boundary="Ashʿarism is not one simple occasionalist formula; acquisition has multiple technical versions and should not be paraphrased as humans doing nothing.",
    claim_type="historical created-act framework", applies_to="Ashʿarite explanations of cognition, volition, causation, and responsibility.", does_not="A single Islamic view of free will or denial of practical agency.",
    basis=["authoritative free-will history", "authoritative analysis of occasionalism"], questions=["What relation does acquisition add beyond temporal conjunction?", "How do later Ashʿarites modify created power and choice?"], sources=["islamic_freewill", "occasionalism"],
)

add(
    name="Muʿtazilite human-agency and knowing-self framework",
    aliases=["Mu'tazila created human acts", "qadar and responsible agency", "Mu'tazilite theory of generated acts"],
    kind="Historical tradition", codes=["HT", "PP"], domain="Agency, intention, knowledge & responsibility", tradition="Muʿtazilite kalām",
    status="internally diverse school tradition · many sources reconstructed",
    status_note="Basran and Baghdadi branches and named theologians differ on power, intention, generated acts, and the ontology of attributes.",
    summary="Muʿtazilite theologians defend robust human origination of voluntary acts so that praise, blame, and divine justice remain intelligible. Analyses distinguish knowledge, belief, will, power, direct action, and effects generated through an agent's action.",
    proponents=["ʿAbd al-Jabbār and Basran Muʿtazilites", "Baghdadi Muʿtazilites with distinct views"], era="8th–11th centuries; later reception", year=1000,
    scope="A kalām family of analyses of mental acts, volition, causal power, and moral responsibility.", keywords=["Mu'tazila", "agency", "will", "knowledge", "generated acts", "divine justice"],
    boundary="'Free will' compresses technical debates, and Muʿtazila is not a single rationalist psychology. Much evidence survives through later transmission.",
    claim_type="historical agency-and-cognition framework", applies_to="Muʿtazilite distinctions among knowledge, will, power, and action.", does_not="Libertarianism in one modern sense or a consensus across Islamic theology.",
    basis=["authoritative free-will history", "authoritative history of Arabic philosophy of mind"], questions=["How do direct and generated acts divide responsibility?", "Which school differences are obscured by the umbrella label?"], sources=["islamic_freewill", "arabic_mind"],
)

add(
    name="Sufi laṭāʾif subtle-faculty model",
    aliases=["subtle centers of Sufi psychology", "lataif al-qalb", "heart-spirit-secret faculty map"],
    kind="Historical tradition", codes=["HT", "MF"], domain="Heart, attention, affect & spiritual cognition", tradition="Plural Sufi textual and lineage traditions",
    status="family of lineage-specific models · no canonical universal map",
    status_note="Number, name, bodily association, color, and sequence of laṭāʾif vary substantially across authors and orders.",
    summary="Sufi authors distinguish subtle capacities such as heart, spirit, secret, hidden, and most-hidden to analyze attention, affect, self-orientation, and forms of spiritual knowing. Lineages cultivate these through remembrance, ethical discipline, companionship, and sometimes bodily attentional practices.",
    proponents=["al-Qushayrī and earlier heart-psychology authors", "Kubrawī, Naqshbandī-Mujaddidī, and other distinct lineages"], era="9th century–present", year=1100,
    scope="A family of Sufi maps of subtle cognition, affective transformation, and contemplative practice.", keywords=["Sufism", "lataif", "heart", "spirit", "dhikr", "attention"],
    boundary="There is no single seven-center Sufi anatomy; popular color and body maps often combine later lineages. Laṭīfa should not be treated as a verified organ.",
    claim_type="lineage-specific subtle-faculty family", applies_to="Explicitly attributed Sufi accounts of heart, spirit, secret, and contemplative transformation.", does_not="A universal Islamic chakra system or established subtle physiology.",
    basis=["authoritative mysticism overview", "scholarly history of Sufi psychology"], questions=["Which maps belong to which texts and initiatory lineages?", "How are metaphor, phenomenology, and ontology distinguished in practice reports?"], sources=["islamic_mysticism", "sufi_psychology"],
)

add(
    name="Judah Halevi's embodied soul and prophetic faculty",
    aliases=["Kuzari psychology", "Halevi on soul and prophecy", "Jewish sage critique of rational-soul proofs"],
    kind="Philosophical position", codes=["PP", "HT"], domain="Soul, embodiment, prophecy & knowledge", tradition="Medieval Jewish philosophy in Arabic",
    status="major medieval position · dialogical voices require attribution",
    status_note="The Kuzari is a dialogue; claims voiced by its Jewish sage are authorially guided but should not erase the work's argumentative staging.",
    summary="Halevi questions philosophical proofs of the rational soul's immateriality and immortality by emphasizing how illness, injury, and aging alter memory and personality. He grounds prophetic knowledge in embodied historical-religious formation rather than unaided intellectual perfection alone.",
    proponents=["Judah Halevi", "the Jewish sage as a literary-philosophical voice in the Kuzari"], era="12th century; continuing Jewish reception", year=1140,
    scope="A critique of rational-soul proofs and an embodied, tradition-mediated account of prophetic cognition.", keywords=["Judah Halevi", "Kuzari", "soul", "embodiment", "prophecy", "memory"],
    boundary="Casting doubt on philosophical immortality arguments is not simple materialism, and the Kuzari's literary interlocutors should not be quoted without speaker context.",
    claim_type="historical embodied-soul critique", applies_to="Halevi's objections to rationalist psychology and account of prophecy.", does_not="A denial of afterlife or one Jewish doctrine of mind.",
    basis=["authoritative thinker-specific reference", "authoritative Jewish-philosophy context"], questions=["How much positive psychology follows from Halevi's skeptical method?", "What roles do body, peoplehood, land, and practice play in cognition?"], sources=["halevi", "jewish_philosophy"],
)

add(
    name="Ibn Gabirol's universal hylomorphism of soul and intellect",
    aliases=["Avicebron universal hylomorphism", "matter-form composition of intellect", "Fons Vitae soul ontology"],
    kind="Philosophical position", codes=["PP", "HT"], domain="Soul, intellect, matter & form", tradition="Medieval Jewish Neoplatonism in Arabic",
    status="historically influential · authorial identity was long obscured",
    status_note="Latin scholastics received Avicebron without recognizing the Jewish poet Ibn Gabirol; Hebrew poetry and Arabic philosophy require distinct genre handling.",
    summary="Ibn Gabirol argues that every created substance, including soul and intellect, is composed of matter and form at different levels of subtlety. Divine Will mediates the procession of forms, while ethical-intellectual return reorients the human soul toward its source.",
    proponents=["Solomon Ibn Gabirol (Avicebron)"], era="11th century; major Latin scholastic reception", year=1050,
    scope="A universal matter-form account extending beyond bodies to soul and intellect.", keywords=["Ibn Gabirol", "Avicebron", "hylomorphism", "soul", "intellect", "divine will"],
    boundary="Universal matter is not ordinary physical stuff, and hylomorphism does not make soul reducible to the biological body.",
    claim_type="historical universal-hylomorphic position", applies_to="Ibn Gabirol's ontology of created soul and intellect.", does_not="Physical materialism or a consensus in medieval Jewish philosophy.",
    basis=["authoritative thinker-specific reference", "authoritative Jewish-philosophy context"], questions=["What individuates immaterial substances sharing universal matter?", "How does Will relate causally to intellect and soul?"], sources=["ibn_gabirol", "jewish_philosophy"],
)

add(
    name="Isaac Israeli's Neoplatonic soul hierarchy",
    aliases=["Isaac Israeli on spirit and soul", "Israeli emanation psychology", "Sefer ha-Ruah v'ha-Nefesh"],
    kind="Historical tradition", codes=["HT", "PP"], domain="Soul, intellect, spirit & emanation", tradition="Early medieval Jewish Neoplatonism in Arabic",
    status="historically important · attribution and textual fragments contested",
    status_note="Several works survive only in fragments or translations, and authorship of the Book on Spirit and Soul has been disputed.",
    summary="Isaac Israeli places intellect and soul within a Neoplatonic emanative hierarchy while distinguishing soul from mortal spirit and bodily functions. His medical and philosophical works connect definition, cognition, and return of the rational soul without presenting one fully preserved psychology.",
    proponents=["Isaac Israeli ben Solomon"], era="9th–10th centuries", year=920,
    scope="An early Jewish-Arabic account of intellect, soul, spirit, body, and emanative causation.", keywords=["Isaac Israeli", "soul", "spirit", "intellect", "emanation", "Jewish Neoplatonism"],
    boundary="Textual attribution is unsettled, and Neoplatonic hierarchy should not be conflated with later Kabbalistic soul levels.",
    claim_type="historical emanative-soul framework", applies_to="Israeli's securely and provisionally attributed psychological texts.", does_not="A complete extant system or standard doctrine across Jewish philosophy.",
    basis=["authoritative thinker-specific reference", "authoritative Jewish-philosophy context"], questions=["Which psychological texts are authentically Israeli's?", "How are bodily spirit and rational soul causally related?"], sources=["isaac_israeli", "jewish_philosophy"],
)

add(
    name="Abraham Ibn Ezra's nefesh–ruaḥ–neshamah psychology",
    aliases=["Ibn Ezra tripartite soul", "nefesh appetite ruach sensation neshamah wisdom", "Ecclesiastes soul excursus"],
    kind="Historical tradition", codes=["HT", "MF"], domain="Appetite, sensation, reason & scriptural psychology", tradition="Medieval Jewish philosophy and exegesis",
    status="text-specific tripartition · terminology varies across works",
    status_note="Ibn Ezra shifts vocabulary for exegetical and philosophical purposes and sometimes withholds esoteric conclusions.",
    summary="In his Ecclesiastes commentary, Ibn Ezra distinguishes nefesh with appetite, ruaḥ with sensation and assertive affect, and neshamah with wisdom. He relates this vocabulary to, but does not simply duplicate, the philosophical vegetative-animal-rational division.",
    proponents=["Abraham Ibn Ezra"], era="12th century", year=1150,
    scope="A scriptural-philosophical classification of appetitive, sensory-affective, and rational functions.", keywords=["Ibn Ezra", "nefesh", "ruach", "neshamah", "soul", "faculties"],
    boundary="Biblical terms are polysemous and do not maintain fixed technical meanings across every verse; the three terms are not necessarily three separate subjects.",
    claim_type="historical tripartite faculty classification", applies_to="Ibn Ezra's specific exegetical treatment of soul-functions.", does_not="A timeless biblical anatomy or a universal Kabbalistic hierarchy.",
    basis=["authoritative thinker-specific reference", "authoritative Jewish-philosophy context"], questions=["When is the tripartition exegetical convenience rather than ontology?", "How do astrological and Neoplatonic commitments shape the faculties?"], sources=["ibn_ezra", "jewish_philosophy"],
)

add(
    name="Hasdai Crescas's desire-centered soul and necessitation",
    aliases=["Crescas on will and love", "Or Adonai psychology", "critique of intellectualist immortality"],
    kind="Philosophical position", codes=["PP", "HT"], domain="Will, desire, love & freedom", tradition="Late medieval Jewish philosophy",
    status="major anti-Aristotelian position · interpretation of freedom contested",
    status_note="Crescas combines causal necessity with evaluative distinctions in willingness; commentators disagree whether this is compatibilism.",
    summary="Crescas rejects the claim that intellectual apprehension alone perfects the soul and gives desire and love a central role in human fulfillment. Acts follow causes, yet willingness and affective identification remain morally significant within a divinely ordered causal world.",
    proponents=["Hasdai Crescas"], era="14th–15th centuries", year=1410,
    scope="A Jewish anti-Aristotelian account of soul perfection, desire, love, causation, and responsibility.", keywords=["Crescas", "will", "desire", "love", "necessity", "soul"],
    boundary="Causal necessity does not make Crescas a simple fatalist, and desire is not treated as mere bodily appetite.",
    claim_type="historical desire-and-agency position", applies_to="Crescas's critique of intellectualism and account of willing under necessity.", does_not="That reasons are causally irrelevant or responsibility disappears.",
    basis=["authoritative thinker-specific reference", "authoritative Jewish-philosophy context"], questions=["Which freedom remains under causal necessitation?", "How does love alter the soul's perfection without becoming a purely passive state?"], sources=["crescas", "jewish_philosophy"],
)

add(
    name="Kabbalistic nefesh–ruaḥ–neshamah soul-level family",
    aliases=["three levels of soul in Kabbalah", "Nefesh Ruach Neshamah", "NRN soul hierarchy"],
    kind="Historical tradition", codes=["HT", "MF"], domain="Soul, embodiment, affect & contemplation", tradition="Medieval and early-modern Kabbalistic traditions",
    status="textual family · mappings vary across corpora and lineages",
    status_note="Zoharic, Lurianic, Hasidic, and other Kabbalistic systems add levels and remap faculties; no single diagram is universal.",
    summary="Kabbalistic texts distinguish nefesh, ruaḥ, and neshamah as interrelated dimensions of embodied vitality, affective-moral life, and higher understanding, often adding ḥayah and yeḥidah. Relations among levels, bodies, commandments, worlds, and postmortem states change across textual systems.",
    proponents=["Zoharic textual circles", "later Kabbalistic authors with distinct systems"], era="13th century–present", year=1290,
    scope="A family of Jewish mystical models relating bodily life, affect, cognition, and spiritual attainment.", keywords=["Kabbalah", "nefesh", "ruach", "neshamah", "soul", "Zohar"],
    boundary="The labels do not denote empirically detected layers or one fixed anatomy. Biblical usage, medieval philosophy, Zoharic symbolism, and later lineage maps must be separated.",
    claim_type="historical soul-level family", applies_to="Explicitly attributed Kabbalistic mappings of soul functions and attainment.", does_not="A universal Jewish theory of mind or proof of detachable consciousness layers.",
    basis=["primary digital textual witness", "authoritative Jewish-philosophy context"], questions=["Which levels and functions belong to which textual stratum?", "How do ritual, ethics, embodiment, and postmortem claims interact?"], sources=["zohar", "jewish_philosophy"],
)

add(
    name="Chabad Tanya two-soul psychology",
    aliases=["Tanya divine and animal souls", "nefesh ha-elohit and nefesh ha-behamit", "Chabad garments of thought speech and action"],
    kind="Historical tradition", codes=["HT", "MF"], domain="Motivation, thought, affect & self-regulation", tradition="Chabad Hasidism",
    status="living lineage-specific framework · not shared unchanged by all Hasidism",
    status_note="The two-soul language belongs to Shneur Zalman's systematic Chabad teaching and has extensive internal commentary.",
    summary="The Tanya distinguishes a divine soul oriented toward attachment to God and an animal soul organizing embodied self-preservation and worldly desire. Intellective and affective powers express themselves through garments of thought, speech, and action, allowing conduct to be regulated even when motivational conflict persists.",
    proponents=["Shneur Zalman of Liadi", "Chabad exegetical tradition"], era="late 18th century–present", year=1796,
    scope="A Chabad model of competing motivations, cognitive-affective powers, attention, and behavioral self-governance.", keywords=["Tanya", "Chabad", "divine soul", "animal soul", "thought", "emotion", "action"],
    boundary="The two souls should not be diagnosed as multiple personalities or mapped directly to brain systems. Other Hasidic schools use different psychologies.",
    claim_type="lineage-specific motivational psychology", applies_to="Tanya's analysis of powers, garments, conflict, and disciplined conduct.", does_not="A universal Hasidic or Jewish model, or clinical evidence for two agents in one body.",
    basis=["primary digital textual edition", "authoritative history of Hasidism"], questions=["How do intellect and affect differ between the two souls?", "What changes phenomenologically between beinoni, tzaddik, and rasha classifications?"], sources=["tanya", "chabad"],
)

# --- African, Indigenous, Pacific, and ancient distinctions -----------------

add(
    name="Hunhu/Ubuntu relational personhood",
    aliases=["ubuntu personhood", "botho relational selfhood", "hunhu communal personhood"],
    kind="Philosophical position", codes=["PP", "HT"], domain="Personhood, relation & moral agency", tradition="Southern African philosophical traditions and contemporary reconstructions",
    status="living plural tradition · philosophical formulations contested",
    status_note="Ubuntu, hunhu, and botho occur in different languages and settings; contemporary philosophical uses cannot be projected unchanged into every community.",
    summary="Hunhu/Ubuntu accounts treat mature personhood as enacted and sustained through reciprocal recognition, care, participation, and accountable conduct. Relational constitution does not merely add social influences to a self already complete in isolation; it helps form the capacities and standing through which a person lives well with others.",
    proponents=["Southern African language and moral traditions", "Mogobe Ramose, Augustine Shutte, Thaddeus Metz, and other divergent philosophers"], era="longstanding oral/living traditions; modern written debate", year=1900,
    scope="Relational and normative accounts of personhood, moral formation, agency, and community.", keywords=["ubuntu", "hunhu", "botho", "personhood", "relation", "community"],
    boundary="This is not 'the African worldview,' simple collectivism, or denial of individual rights. Language-specific meanings, colonial histories, and philosophical disagreements must remain visible.",
    claim_type="plural relational-personhood family", applies_to="Named Southern African formulations of becoming and acting as a person through relation.", does_not="Pan-African consensus, metaphysical group minds, or unconditional priority of community over individuals.",
    basis=["authoritative specialist reference", "authoritative African-ethics context"], questions=["Which claims are linguistic, ethnographic, normative, or metaphysical?", "How can relational formation secure dissent and protect vulnerable individuals?"], sources=["ubuntu_iep", "african_ethics"],
)

add(
    name="Ancient Egyptian distributed-person model",
    aliases=["ka-ba-akh person complex", "Egyptian composite personhood", "body-name-shadow-heart-ka-ba model"],
    kind="Historical tradition", codes=["HT", "MF"], domain="Personhood, embodiment, identity & afterlife", tradition="Ancient Egyptian textual, ritual, and iconographic traditions",
    status="historically documented complex · meanings change across periods",
    status_note="Ka, ba, akh, heart, name, shadow, image, and body do not form one timeless checklist; sources span millennia and social settings.",
    summary="Ancient Egyptian sources distribute personal identity and efficacy across embodied and relational elements including body, heart, name, shadow, ka, ba, and transfigured akh. Funerary practice aims not to release one simple soul but to preserve, reunite, activate, and socially sustain aspects needed for continued personhood.",
    proponents=["Ancient Egyptian scribal, ritual, and funerary traditions"], era="3rd millennium BCE–Roman Egypt", year=-1500,
    scope="Historically changing models of embodied personhood, identity, agency, and postmortem transformation.", keywords=["ancient Egypt", "ka", "ba", "akh", "heart", "name", "personhood"],
    boundary="Ka, ba, and akh should not all be translated 'soul,' and evidence from one period or elite funerary context cannot represent every Egyptian person's belief.",
    claim_type="historical distributed-person complex", applies_to="Specified Egyptian textual, material, and ritual sources across dated periods.", does_not="A single detachable consciousness entity or one invariant Egyptian doctrine.",
    basis=["peer-reviewed Egyptological encyclopedia", "peer-reviewed term-specific Egyptological entry"], questions=["How do element relations change between Old Kingdom and later funerary corpora?", "Which models describe living persons, deceased persons, or ritual efficacy?"], sources=["egypt_body", "egypt_ba"],
)

add(
    name="Ancient Egyptian heart as cognition, memory, and moral agency",
    aliases=["ib-heart model", "Egyptian heart-mind", "heart in weighing and self-testimony"],
    kind="Historical tradition", codes=["HT", "MF"], domain="Cognition, emotion, memory & moral identity", tradition="Ancient Egyptian medical, wisdom, and funerary traditions",
    status="cross-genre historical model · lexical distinctions matter",
    status_note="Egyptian jb and ḥꜣtj can distinguish experiential and anatomical emphases but sometimes overlap; sources and periods must be identified.",
    summary="Ancient Egyptian texts and objects associate the heart with thinking, memory, emotion, intention, and moral testimony while also recognizing it as a living bodily organ. In judgment scenes the heart can testify about the deceased, joining cognition and character rather than separating rational mind from affect.",
    proponents=["Ancient Egyptian medical, literary, and funerary textual traditions"], era="3rd millennium BCE–Roman Egypt", year=-1300,
    scope="A historically situated heart-centered account of cognition, affect, memory, vitality, and moral identity.", keywords=["ancient Egypt", "heart", "ib", "memory", "emotion", "moral agency"],
    boundary="The record is not evidence that Egyptians lacked knowledge of the brain or believed one undifferentiated doctrine; modern 'heart-brain coherence' claims are not licensed.",
    claim_type="historical heart-mind model", applies_to="Egyptian uses of heart language in dated medical, literary, and funerary contexts.", does_not="Modern cardiocentric neuroscience or a single belief held across three millennia.",
    basis=["peer-reviewed Egyptological encyclopedia", "authoritative museum object and textual context"], questions=["When do jb and ḥꜣtj differ functionally?", "How do medical and funerary uses of the heart constrain one another?"], sources=["egypt_body", "egypt_heart"],
)

add(
    name="Zoroastrian urvan–fravaši–daēnā person complex",
    aliases=["Zoroastrian soul and guardian complex", "urvan fravashi daena model", "Avestan components of immaterial personhood"],
    kind="Historical tradition", codes=["HT", "MF"], domain="Soul, conscience, agency & postmortem identity", tradition="Avestan and Middle Persian Zoroastrian traditions",
    status="historically layered living tradition · philology contested",
    status_note="Meanings of fravaši and daēnā change across Gathic, Younger Avestan, and Pahlavi sources and remain debated among Iranists and practitioners.",
    summary="Zoroastrian sources distinguish urvan as the morally accountable soul, fravaši as a protective or preexistent spiritual counterpart in some sources, and daēnā as religion, vision, conscience, or the postmortem manifestation of one's lived choices. These elements relate personal agency to cosmic ethical order and judgment.",
    proponents=["Avestan textual traditions", "Middle Persian Zoroastrian exegetes", "living Zoroastrian communities with diverse interpretations"], era="2nd millennium BCE textual roots–present", year=-500,
    scope="Historically changing relations among soul, protective counterpart, conscience, moral action, and afterlife.", keywords=["Zoroastrianism", "urvan", "fravashi", "daena", "conscience", "soul"],
    boundary="Fravaši is not simply a Western guardian angel or higher self, and daēnā is not exhausted by 'conscience.' Philological reconstruction and living theology must be distinguished.",
    claim_type="historical layered personhood complex", applies_to="Explicit Avestan, Pahlavi, and attributed modern interpretations of immaterial personhood.", does_not="One fixed five-part soul anatomy or empirical survival evidence.",
    basis=["authoritative term-specific Iranica entry", "authoritative historical synthesis"], questions=["Which fravaši functions are earliest and which result from later blending with urvan?", "How do ethical, visionary, and institutional senses of daēnā relate?"], sources=["fravashi", "zoroastrian_history"],
)

add(
    name="Manichaean light-soul and mind-liberation model",
    aliases=["Manichaean particles of light", "living soul in matter", "Mani's light-mind cosmology"],
    kind="Historical tradition", codes=["HT", "MF"], domain="Soul, cognition, embodiment & cosmic mixture", tradition="Manichaean religion across Iranian, Mediterranean, and Central Asian contexts",
    status="historically global textual tradition · sources multilingual and polemical",
    status_note="Manichaean materials survive in Coptic, Middle Iranian, Chinese, and other languages as well as opponents' reports; regional formulations differ.",
    summary="Manichaean cosmology treats living soul or light as mixed with material darkness and dispersed through embodied life. Perception, knowledge, ethical discipline, and ritual help light recognize its origin and be released, while the mind is mapped within a larger mythic account of cosmic conflict and rescue.",
    proponents=["Mani", "Manichaean communities across late antique and medieval Eurasia"], era="3rd–14th centuries CE", year=260,
    scope="A dualist religious model connecting soul, cognition, embodiment, ethics, and cosmic liberation.", keywords=["Manichaeism", "light", "soul", "mind", "matter", "liberation"],
    boundary="Light and darkness are theological-cosmological categories, not electromagnetic substances or skin-color categories. Opponents' descriptions require corroboration.",
    claim_type="historical religious-cosmological mind model", applies_to="Manichaean accounts of living soul, recognition, mixture, and release.", does_not="A scientific photon theory of consciousness or one identical doctrine across all Manichaean languages.",
    basis=["authoritative philosophical reference", "authoritative Iranica historical survey"], questions=["How do regional texts repartition soul powers and cosmic actors?", "Which practices were believed to transform cognition versus cosmological substance?"], sources=["manichaeism_iep", "manichaeism_iranica"],
)

add(
    name="Evagrius Ponticus's logismoi and pure-nous model",
    aliases=["Evagrian eight thoughts", "logismoi psychology", "apatheia and pure prayer"],
    kind="Historical tradition", codes=["HT", "MF"], domain="Attention, thought, affect & contemplative transformation", tradition="Early Christian desert monastic psychology",
    status="foundational ascetic model · textual and doctrinal context essential",
    status_note="Evagrius writes within late antique Christian asceticism and Origenist controversies; later lists of deadly sins modify his eight logismoi.",
    summary="Evagrius analyzes recurring logismoi—patterns of thought, image, desire, and affect—that capture attention and disturb contemplative stability. Discernment, practical discipline, and prayer cultivate apatheia and clarify nous, understood as intellective-spiritual awareness oriented toward God.",
    proponents=["Evagrius Ponticus", "later Eastern Christian ascetic interpreters"], era="4th century; extensive Syriac, Greek, and later Christian reception", year=390,
    scope="A late antique model of intrusive thought patterns, affect regulation, attention, and contemplative awareness.", keywords=["Evagrius", "logismoi", "nous", "apatheia", "attention", "prayer"],
    boundary="Logismoi are not simply DSM symptoms, and apatheia is not emotional flattening. Nous has theological meanings not captured by intellect or consciousness alone.",
    claim_type="historical ascetic-cognitive model", applies_to="Evagrius's classifications and practices for thought, affect, and prayer.", does_not="Clinical treatment efficacy or one universal Christian psychology.",
    basis=["primary-source scholarly translation", "peer-reviewed historical psychology"], questions=["How do Greek and Syriac transmissions alter the model?", "What distinguishes attention training from theological claims about pure prayer?"], sources=["evagrius_oup", "evagrius"],
)

add(
    name="Senghorian Négritude affective-participatory knowing",
    aliases=["Senghor's reason-embrace", "Négritude epistemology of emotion", "participatory knowledge in Senghor"],
    kind="Philosophical position", codes=["PP"], domain="Affect, knowledge, relation & decolonization", tradition="20th-century Négritude and African philosophy",
    status="historically influential · strongly criticized and revised",
    status_note="Senghor's contrasts between European analytic reason and Black-African emotion have been challenged as essentialist even by Négritude allies.",
    summary="Senghor describes a mode of knowing in which affect, rhythm, participation, and relation disclose an object from within lived engagement rather than through separation alone. He presents this as part of Négritude's cultural and anti-colonial reclamation while also advocating a future synthesis of cognitive styles.",
    proponents=["Léopold Sédar Senghor"], era="1930s–2001; continuing critical reception", year=1948,
    scope="A decolonial philosophical proposal about affective participation, cognition, art, and cultural self-interpretation.", keywords=["Senghor", "Negritude", "emotion", "participation", "knowledge", "decolonization"],
    boundary="The position must not be repeated as a biological or racial fact about cognition. Césaire, Fanon, Adotevi, and later African philosophers provide major critiques.",
    claim_type="historical affective-epistemological position", applies_to="Senghor's named philosophical writings and their critical reception.", does_not="An essence of Black minds, a pan-African consensus, or inferiority of analysis.",
    basis=["authoritative specialist reference", "peer-reviewed decolonial critique"], questions=["Can participatory knowing be retained without racial-cultural essentialism?", "How did anti-colonial strategy shape Senghor's binary rhetoric?"], sources=["negritude_sep", "negritude_critique"],
)

add(
    name="Tempels's colonial Bantu vital-force formulation",
    aliases=["Bantu Philosophy vital force", "Tempels force ontology", "Baluba vital-force account in Tempels"],
    kind="Historical tradition", codes=["HT", "PP"], domain="Personhood, vitality, relation & ontology", tradition="Colonial-era ethnophilosophical formulation and African-philosophy reception",
    status="historically influential external account · authority and generalization heavily contested",
    status_note="Placide Tempels was a Belgian missionary writing under colonial conditions; the label records his theory and its reception, not an unmediated Bantu consensus.",
    summary="Tempels argued that being in the communities he called Bantu is understood dynamically as vital force, with persons and other beings situated in hierarchies of mutual strengthening and weakening. The work challenged colonial claims of no African philosophy while reproducing broad colonial generalizations.",
    proponents=["Placide Tempels as formulator", "later African philosophers as critics, revisers, and selective appropriators"], era="1945–present critical reception", year=1945,
    scope="A named colonial-era interpretation of vitality and relational ontology plus its contested reception.", keywords=["Tempels", "Bantu Philosophy", "vital force", "ethnophilosophy", "colonialism", "relation"],
    boundary="This record is not titled 'the Bantu worldview.' It does not authorize generalization across hundreds of Bantu-language communities and must retain the author's colonial positionality.",
    claim_type="bounded external philosophical-ethnographic formulation", applies_to="Tempels's text and explicitly attributed critical receptions.", does_not="Authentic pan-Bantu doctrine, community consent, or empirical life energy.",
    basis=["peer-reviewed reception history", "current critical African-philosophy analysis"], questions=["Which claims, if any, are supported by community-specific sources?", "Can relational vitality be reconstructed without reproducing Tempels's hierarchy and colonial frame?"], sources=["tempels_reception", "vitality"],
)

add(
    name="Nsamenang's African social-ontogenesis model",
    aliases=["social ontogeny of responsible intelligence", "Nsamenang developmental framework", "West African participatory developmental tasks"],
    kind="Model or framework", codes=["MF"], domain="Development, social cognition, responsibility & selfhood", tradition="African developmental psychology, grounded especially in Cameroonian and West African contexts",
    status="scholarly Indigenous-centered framework · scope is explicitly bounded",
    status_note="Nsamenang challenges universalized Euro-American stage models but does not claim every African community shares one developmental sequence.",
    summary="Nsamenang frames development as social ontogenesis through participation in age- and context-appropriate family and community responsibilities. Intelligence includes becoming able to contribute, care, coordinate, and assume accountable roles, not only performing decontextualized cognitive tasks.",
    proponents=["A. Bame Nsamenang", "African developmental scholars extending and critiquing the model"], era="1992–present", year=2006,
    scope="An eco-cultural developmental model of social selfhood, participatory learning, and responsible intelligence.", keywords=["Nsamenang", "social ontogenesis", "development", "responsible intelligence", "participation", "Africa"],
    boundary="The model is not a natural life cycle of all Africans, and productive participation must not romanticize child labor, gender inequality, poverty, or disrupted schooling.",
    claim_type="bounded developmental framework", applies_to="Nsamenang's account and community-specific research that tests or adapts it.", does_not="A universal African childhood or rejection of individual cognitive capacities.",
    basis=["primary scholarly articulation", "peer-reviewed critical extension"], questions=["Which developmental tasks are stable versus locally historical?", "How should responsibility be assessed without normalizing structural deprivation?"], sources=["nsamenang", "nsamenang_review"],
)

add(
    name="Te Wheke model of Māori family wellbeing",
    aliases=["Rose Pere Te Wheke", "octopus model of hauora", "waiora and eight tentacles"],
    kind="Model or framework", codes=["MF"], domain="Mind, emotion, spirit, identity & whānau wellbeing", tradition="Māori health scholarship in Aotearoa New Zealand",
    status="living Indigenous health framework · accountable use required",
    status_note="Te Wheke was articulated by Rose Pere and should be applied with Māori authority, local whānau, hapū, and iwi context rather than as a generic Indigenous diagram.",
    summary="Te Wheke represents whānau as the octopus head, waiora as its eyes, and eight interwoven tentacles including wairuatanga, hinengaro, tinana, whanaungatanga, mauri, mana ake, ancestral breath, and whatumanawa. Wellbeing is relational and cannot be reduced to an isolated mental-health score.",
    proponents=["Rose Pere", "Māori health practitioners and communities in situated applications"], era="1980s–present", year=1984,
    scope="A Māori family-wellbeing framework integrating mind, emotion, body, spirit, identity, ancestry, and relation.", keywords=["Te Wheke", "Maori", "hauora", "hinengaro", "whanau", "mauri", "whatumanawa"],
    boundary="This is not a standalone theory of phenomenal consciousness, not interchangeable with Te Whare Tapa Whā, and not generalizable to all Indigenous peoples.",
    claim_type="Indigenous family-wellbeing framework", applies_to="Māori health and wellbeing work using Rose Pere's model with contextual accountability.", does_not="A universal octagonal psychology or authority to redefine Māori terms externally.",
    basis=["official Indigenous-health guidance", "official historical context"], questions=["How do local services preserve interdependence rather than turning tentacles into checkboxes?", "How should whenua and colonization enter applications that simplify the original model?"], sources=["te_wheke", "maori_strategy"],
)

add(
    name="Fonofale Pacific wellbeing model",
    aliases=["Pulotu-Endemann Fonofale", "Pacific fale health model", "family-foundation holistic health framework"],
    kind="Model or framework", codes=["MF"], domain="Mental, physical, spiritual & relational wellbeing", tradition="Samoan-developed Pacific health practice in Aotearoa New Zealand",
    status="widely used Pacific framework · local adaptation required",
    status_note="Fonofale draws on a Samoan fale metaphor for multi-Pacific practice; it should not erase distinct Tongan, Cook Islands, Niuean, Tokelauan, or other epistemologies.",
    summary="Fonofale uses a fale whose foundation is family, roof is cultural values and beliefs, and posts include spiritual, physical, mental, and other dimensions. Time, environment, and context surround the structure, making wellbeing collective, cultural, and historically situated.",
    proponents=["Fuimaono Karl Pulotu-Endemann", "Pacific health communities and practitioners"], era="1984/2001–present", year=2001,
    scope="A holistic Pacific health framework centered on family, culture, context, and interdependent wellbeing domains.", keywords=["Fonofale", "Samoan", "Pacific health", "family", "mental wellbeing", "culture"],
    boundary="Fonofale is not a consciousness ontology and should not be treated as the one Pacific worldview. 'Other' posts and surrounding contexts vary by use.",
    claim_type="Pacific holistic-health framework", applies_to="Contextually accountable health, research, and service design with Pacific peoples.", does_not="Uniformity across Pacific nations or validation of each domain as an independent psychometric construct.",
    basis=["primary institutional model record", "peer-reviewed Pacific-methodology analysis"], questions=["How should multi-Pacific use avoid privileging one national metaphor?", "What evidence supports outcomes when the model guides service design?"], sources=["fonofale_primary", "fonofale_review"],
)

add(
    name="Native Hawaiian lōkahi and mauli-ola relational health model",
    aliases=["lokahi balance model", "mauli ola Native Hawaiian wellbeing", "aina-ohana-spirit health relation"],
    kind="Model or framework", codes=["MF"], domain="Self, family, land, spirituality & collective wellbeing", tradition="Kānaka Maoli health scholarship and community practice",
    status="living community-grounded framework · versions are program-specific",
    status_note="Lōkahi and mauli ola are broader living concepts; the record is limited to named health-model articulations by Native Hawaiian organizations and authors.",
    summary="Native Hawaiian health frameworks use lōkahi for dynamic balance and mauli ola for flourishing life within relations among kānaka, ʻohana, community, spirituality, and ʻāina. Recent care models treat identity, ancestry, purpose, land stewardship, and collective bonds as constitutive protective conditions rather than optional cultural additions.",
    proponents=["Papa Ola Lōkahi and E Ola Mau authors", "Sheri-Ann Daniels, Lilinoe Kauahikaua, Charis Kaio, and collaborating Kānaka Maoli health scholars"], era="1985–present", year=1985,
    scope="Community-grounded relational models of Native Hawaiian identity, balance, connection, and health.", keywords=["Native Hawaiian", "lokahi", "mauli ola", "aina", "ohana", "health"],
    boundary="This record does not disclose restricted knowledge or equate Hawaiian concepts with generic wellness. It is not a stand-alone account of phenomenal consciousness.",
    claim_type="community-grounded relational-health framework", applies_to="Named Native Hawaiian public-health and care-model publications.", does_not="A timeless belief shared identically by every Kānaka Maoli person or all Polynesian peoples.",
    basis=["community-authored peer-reviewed model", "Native Hawaiian health-authority report"], questions=["How are land return, structural determinants, and cultural practice represented beyond individual services?", "Which outcome measures remain accountable to community definitions of thriving?"], sources=["hawaiian_care", "hawaiian_health"],
)

add(
    name="Viveiros de Castro's Amerindian perspectivism",
    aliases=["Amazonian perspectivism", "multinaturalism", "cosmological deixis"],
    kind="Model or framework", codes=["MF", "PP"], domain="Personhood, embodiment & perspective", tradition="Comparative Amazonian anthropology",
    status="influential external comparative theory · scope and generalization contested",
    status_note="Viveiros de Castro synthesizes ethnographies from different Amazonian peoples; community-specific fit and the risk of overgeneralization are active critiques.",
    summary="Amerindian perspectivism proposes that humans, some animals, and spirits may be treated as persons from their own viewpoints while bodily form organizes what each perceives as food, habitat, and sociality. Shared subject-like form and differentiated bodies reverse a familiar one-nature/many-cultures contrast.",
    proponents=["Eduardo Viveiros de Castro as theorist", "Amazonian interlocutors represented through heterogeneous ethnographies"], era="1990s–present debate", year=1998,
    scope="An anthropological comparative model of perspective, body, personhood, and interspecies relations in specified Amazonian cases.", keywords=["Amerindian perspectivism", "Amazonia", "personhood", "body", "multinaturalism", "anthropology"],
    boundary="This is Viveiros de Castro's comparative theory, not a statement that all Indigenous Americans share one ontology. It is not scientific proof that every animal has human-like phenomenal consciousness.",
    claim_type="bounded comparative anthropological model", applies_to="Ethnographically specified Amazonian materials and the named theoretical synthesis.", does_not="Pan-Indigenous consensus, literal sameness of minds, or replacement of community self-description.",
    basis=["primary theoretical formulation", "peer-reviewed community-specific comparative critique"], questions=["Which communities and situations do not fit the model?", "How can Indigenous interlocutors' concepts remain primary rather than examples for an external ontology?"], sources=["perspectivism", "amazon_critique"],
)

add(
    name="Nahua teyolia–tonalli–ihiyotl animic-center model",
    aliases=["three Nahua animic entities", "heart-head-liver centers", "teyolia tonalli ihiyotl person complex"],
    kind="Historical tradition", codes=["HT", "MF"], domain="Personhood, vitality, affect & cognition", tradition="Colonial-era Nahua ethnohistorical reconstruction",
    status="scholarly reconstruction from colonial and later sources · translation effects substantial",
    status_note="Terms and distributions vary by period and Nahua community; colonial Christian translation reshaped the evidence.",
    summary="Ethnohistorical scholarship distinguishes teyolia, associated with heart, identity, memory, and postmortem continuity; tonalli, associated with heat, day-sign, vitality, and head; and ihiyotl, associated with breath, liver, affect, and potentially harmful emanation. Together they model personhood as multiply embodied rather than one soul in one location.",
    proponents=["Nahua textual and community traditions represented in specified sources", "Alfredo López Austin and later ethnohistorians as reconstructors"], era="pre-contact roots; colonial documentation; continuing regional variation", year=1500,
    scope="A bounded reconstruction of embodied animic centers in Nahua personhood.", keywords=["Nahua", "teyolia", "tonalli", "ihiyotl", "heart", "head", "liver"],
    boundary="The three terms are not three detachable Western souls, chakras, or fixed organs across all Nahua communities. Colonial lexicons often forced Christian alma/anima equivalences.",
    claim_type="bounded ethnohistorical person model", applies_to="Specified Nahua-language sources and explicitly attributed scholarly reconstructions.", does_not="A timeless Aztec doctrine or a uniform model among contemporary Nahua peoples.",
    basis=["specialist ethnohistorical analysis", "peer-reviewed translation-history analysis"], questions=["Which distinctions are pre-contact and which emerge through colonial translation?", "How do contemporary community usages differ across regions?"], sources=["nahua_ihiyotl", "nahua_translation"],
)

add(
    name="Dadirri deep-listening and quiet-awareness practice",
    aliases=["Miriam-Rose Ungunmerr-Baumann dadirri", "inner deep listening", "Ngan'gikurunggurr quiet still awareness"],
    kind="Phenomenological construct", codes=["PC", "HT"], domain="Listening, attention, relation & place", tradition="Ngan'gikurunggurr/Ngen'giwumirri teaching from Nauiyu",
    status="living Indigenous teaching and research methodology · authority is situated",
    status_note="The public articulation belongs to Miriam-Rose Ungunmerr-Baumann and her community context; similar-sounding practices elsewhere are not interchangeable.",
    summary="Dadirri names a patient, receptive practice of deep listening, quiet awareness, and respectful relation to people, place, time, and what is not immediately said. In community-authored research it becomes a place-based methodology emphasizing relational accountability and nonextractive attention.",
    proponents=["Miriam-Rose Ungunmerr-Baumann", "Nauiyu community collaborators in public methodological work"], era="public articulations 1980s–present", year=1988,
    scope="A situated Indigenous practice and methodology of receptive attention, listening, relation, and patience.", keywords=["dadirri", "deep listening", "quiet awareness", "Nauiyu", "place", "Indigenous methodology"],
    boundary="Dadirri is not generic mindfulness, a relaxation product, or 'Australian Aboriginal meditation.' Use must preserve author, language-group, place, and permissions.",
    claim_type="situated attentional and relational practice", applies_to="Ungunmerr-Baumann's public teaching and community-authored methodological adaptations.", does_not="A pan-Aboriginal practice, clinical efficacy by analogy, or permission to appropriate restricted knowledge.",
    basis=["primary community-authored articulation", "community-authored peer-reviewed methodology"], questions=["What protocols should govern adaptation outside Nauiyu?", "How can research evaluate process without converting relational practice into an extractive instrument?"], sources=["dadirri_primary", "dadirri_method"],
)

add(
    name="Qungasvik Yup'ik cultural-protective model",
    aliases=["Qungasvik Toolbox", "Qasgiq cultural logic model", "Yup'ik Ellangneq and communal mastery framework"],
    kind="Model or framework", codes=["MF"], domain="Awareness, identity, connectedness & community protection", tradition="Yup'ik community-developed prevention science in southwest Alaska",
    status="community-driven evaluated intervention · locally adaptive",
    status_note="Qungasvik was developed through specific tribal and community partnerships; modules are selected and adapted rather than imposed as a fixed manual.",
    summary="Qungasvik organizes community-chosen cultural activities through a qasgiq process of gathering, selecting knowledgeable leaders, acting, and reflecting. Protective factors include family and community connectedness, communal mastery, reasons for life, and ellangneq—becoming aware in relation to self, others, and environment.",
    proponents=["Yup'ik Elders and community planning groups", "People Awakening Team", "Stacy Rasmus, Gerald Mohatt, James Allen, and collaborating researchers"], era="1990s–present", year=2014,
    scope="A Yup'ik community intervention model connecting cultural practice, awareness, identity, and protection from suicide and alcohol harm.", keywords=["Qungasvik", "Yup'ik", "Qasgiq", "ellangneq", "connectedness", "prevention"],
    boundary="This is not a general Alaska Native psychology or a decontextualized toolkit. Community ownership, tribal approval, local experts, and historical disruption are constitutive.",
    claim_type="community-developed prevention framework", applies_to="Participating Yup'ik communities and explicitly adapted Qungasvik implementations.", does_not="Universal efficacy across Indigenous nations or a metaphysical theory of consciousness.",
    basis=["community-collaborative primary model paper", "community-collaborative evaluation"], questions=["Which protective pathways generalize across participating communities?", "How can scaling preserve community control and flexible cultural logic?"], sources=["qungasvik_primary", "qungasvik_eval"],
)

add(
    name="Tzeltal two-bodies and two-souls personhood model",
    aliases=["Pitarch two Maya bodies", "Tzeltal ch'ulel and lab person complex", "quaternary Tzeltal person model"],
    kind="Historical tradition", codes=["HT", "MF"], domain="Body, soul, alterity & personhood", tradition="Ethnographic analysis of Tzeltal Maya communities in Chiapas",
    status="community-specific external ethnographic model · translation and regional scope limited",
    status_note="The model is Pedro Pitarch's analysis of particular Tzeltal materials; Tzotzil ch'ulel accounts and other Maya communities differ.",
    summary="Pitarch analyzes Tzeltal personhood through a carnal body shared with animals, a specifically human phenomenological body, a human-shaped soul, and an animal-formed counterpart. The elements are mutually necessary and situate identity across bodily and nonhuman relations.",
    proponents=["Tzeltal interlocutors represented in Pedro Pitarch's fieldwork", "Pedro Pitarch as model author"], era="late 20th-century fieldwork and 2012 formulation", year=2012,
    scope="A bounded ethnographic model of embodied and soul-related personhood in specified Tzeltal contexts.", keywords=["Tzeltal", "Maya", "personhood", "body", "soul", "Chiapas"],
    boundary="This is not 'the Maya soul' and should not be merged with Tzotzil, Classic Maya, or tourist-spiritual accounts. External ethnographic mediation must remain explicit.",
    claim_type="bounded ethnographic personhood model", applies_to="Pitarch's specified Tzeltal field materials and analysis.", does_not="Uniform Maya belief, independent verification of animal counterparts, or authorization to disclose community-restricted knowledge.",
    basis=["peer-reviewed primary ethnographic analysis", "peer-reviewed regional concept review"], questions=["How do Tzeltal interlocutors evaluate the model's fourfold abstraction?", "Which concepts vary by municipality, generation, conversion, and language context?"], sources=["tzeltal_person", "chulel_review"],
)

add(
    name="Strathern's Melanesian dividual-person model",
    aliases=["Melanesian dividual", "partible personhood", "person as composite of relations"],
    kind="Model or framework", codes=["MF", "PP"], domain="Personhood, exchange, gender & agency", tradition="New Melanesian ethnography",
    status="influential external anthropological model · generalization contested",
    status_note="Marilyn Strathern's model is grounded especially in Papua New Guinea materials and analytic comparison; 'Melanesian' covers highly diverse societies.",
    summary="Strathern describes persons as partible composites of relations and contributions elicited and exchanged with others rather than bounded individuals who merely own relationships. Agency appears through how relational components are activated, detached, and recomposed in gendered exchange.",
    proponents=["Marilyn Strathern as theorist", "Mount Hagen and other Papua New Guinea interlocutors mediated through ethnographic sources"], era="1980s–present anthropological debate", year=1988,
    scope="An anthropological model of relationally composed personhood, exchange, and agency in specified Melanesian cases.", keywords=["Strathern", "Melanesia", "dividual", "partible person", "relation", "exchange"],
    boundary="The dividual is an analytic model, not a claim that every Melanesian lacks individuality. It originated through comparison and has been criticized, revised, and reapplied.",
    claim_type="bounded comparative personhood model", applies_to="Strathern's specified ethnographic analyses and critical extensions.", does_not="A pan-Melanesian essence or a literal group mind.",
    basis=["primary anthropological formulation", "peer-reviewed conceptual critique"], questions=["Where does the model fail to capture local self-understandings?", "How do Christianity, markets, gender, and history alter partibility?"], sources=["strathern", "dividual_critique"],
)

add(
    name="Samoan vā relational-self framework",
    aliases=["teu le vā", "vā fealoa'i relational personhood", "Samoan relational self"],
    kind="Model or framework", codes=["MF", "PP"], domain="Relational self, sacred space & social responsibility", tradition="Samoan scholarship and practice",
    status="living relational framework · term meanings are context-specific",
    status_note="Vā names relational space across Pacific languages with distinct meanings; this record is limited to named Samoan formulations.",
    summary="Samoan accounts of vā treat the space between persons not as emptiness but as a living relational field requiring care, respect, service, and appropriate boundaries. Teu le vā names active tending of these relations, so selfhood and wellbeing are inseparable from family, genealogy, role, and reciprocal obligation.",
    proponents=["Samoan scholars including Tamasese, Peteru, Waldegrave, Bush, and Anae", "Samoan communities in situated applications"], era="longstanding language-practice; modern scholarly articulation", year=2005,
    scope="A Samoan relational framework for selfhood, responsibility, social space, and wellbeing.", keywords=["Samoan", "va", "teu le va", "relational self", "family", "responsibility"],
    boundary="Vā is not a physical energy field or one generic Pacific concept. Relationships can be unequal or harmful, so 'tending' them does not mean preserving every hierarchy.",
    claim_type="living relational-self framework", applies_to="Named Samoan public scholarship and community-specific uses of vā and teu le vā.", does_not="Pan-Pacific uniformity, a collective consciousness, or automatic moral goodness of existing relations.",
    basis=["community-grounded scholarly articulation", "peer-reviewed Pacific methodology"], questions=["How do gender, migration, church, and diaspora reshape vā?", "What practices repair rather than merely preserve damaging relations?"], sources=["samoan_va", "va_method"],
)


for index, item in enumerate(RECORDS, start=1):
    item["id"] = f"cross-breadth-{index:03d}"


payload = {
    "collection": {
        "title": "Noemorph cross-cultural, historical, religious-philosophical, and Indigenous breadth additions",
        "version": "1.0.0-provisional",
        "generated_at": RETRIEVED,
        "phase": "collection",
        "synthesis": "deferred",
        "record_count": len(RECORDS),
        "method": "Candidate construction from record-specific primary translations, peer-reviewed scholarship, institutional editions, community-authored frameworks, specialist encyclopedias, and exact-name/alias collision auditing against the registered Noemorph corpus.",
        "source_policy": "Every record retains at least two HTTPS locators. DOI resolution and locator availability are recorded separately from interpretive review. Community-authored sources are preferred for living Indigenous frameworks; externally theorized ethnographic models are labeled as such.",
        "coverage_note": "This provisional shard separates named traditions and thinkers instead of treating geographic regions as single theories. It includes South Asian, Buddhist, Sikh, Jaina, Chinese, Korean, Japanese, Arabic-Islamic, Jewish, African, Indigenous American, Pacific, and ancient religious-philosophical records. It is not exhaustive.",
        "translation_policy": "Key non-English terms remain visible. English glosses are treated as provisional, polysemy and textual layers are noted per record, and no cross-tradition equivalence edges are asserted.",
        "community_and_ethnography_policy": "Living Indigenous frameworks are bounded to named authors, communities, institutions, or public scholarship. External anthropological syntheses remain attributed to their theorists and are not presented as uniform community belief.",
        "exclusions": [
            "Parent theories already represented in the merged corpus—including Advaita, Sāṃkhya–Yoga, Yogācāra, Madhyamaka, Dzogchen, Mahāmudrā, Pratyabhijñā, Tiantai, Huayan in Fazang, Wang Yangming, Akan, Yorùbá, and existing Māori/Ojibwe records—were not renamed and double-counted.",
            "Generic pan-Indigenous medicine-wheel, animism, shamanism, chakra, and 'Eastern mind' headings were excluded because they collapse distinct communities or lack bounded attribution.",
            "Restricted, initiatory, or community-controlled knowledge was not sought; only publicly available scholarship and institutional records were used.",
            "Cross-cultural synthesis, equivalence claims, and graph relationships remain deferred until candidate review and identity resolution are complete.",
        ],
    },
    "records": RECORDS,
}


OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"wrote {OUT} ({len(RECORDS)} records; {sum(len(r['citations']) for r in RECORDS)} citations)")
