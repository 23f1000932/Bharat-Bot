"""
scripts/upload_knowledge.py – Knowledge base population script for BharatBot.

Creates Azure AI Search indexes for AgriBot, HealthBot, and LawBot and
uploads sample knowledge documents with Indian content for each domain.
Run this script once to seed the knowledge base before starting BharatBot.

Usage:
    python scripts/upload_knowledge.py
"""

import logging
import os
import sys
from typing import Any

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

SEARCH_ENDPOINT: str = os.getenv("SEARCH_ENDPOINT", "")
SEARCH_KEY: str = os.getenv("SEARCH_KEY", "")

# Index names
INDEX_AGRI   = os.getenv("SEARCH_INDEX_AGRI", "agribot-knowledge")
INDEX_HEALTH = os.getenv("SEARCH_INDEX_HEALTH", "healthbot-knowledge")
INDEX_LAW    = os.getenv("SEARCH_INDEX_LAW", "lawbot-knowledge")

# ---------------------------------------------------------------------------
# Index schema
# ---------------------------------------------------------------------------

INDEX_FIELDS = [
    {"name": "id",       "type": "Edm.String",  "key": True,  "searchable": False, "filterable": True},
    {"name": "title",    "type": "Edm.String",  "key": False, "searchable": True,  "filterable": False, "analyzer": "standard.lucene"},
    {"name": "content",  "type": "Edm.String",  "key": False, "searchable": True,  "filterable": False, "analyzer": "standard.lucene"},
    {"name": "language", "type": "Edm.String",  "key": False, "searchable": False, "filterable": True},
    {"name": "domain",   "type": "Edm.String",  "key": False, "searchable": False, "filterable": True},
]

# ---------------------------------------------------------------------------
# Sample documents
# ---------------------------------------------------------------------------

AGRI_DOCS: list[dict[str, str]] = [
    {
        "id": "agri-001",
        "title": "Wheat Rust Disease (गेहूं का रतुआ रोग)",
        "content": (
            "Wheat rust is caused by Puccinia fungi and is one of the most devastating wheat diseases in India. "
            "There are three types: stem rust, leaf rust, and yellow/stripe rust. Symptoms include orange-yellow "
            "or brown pustules on leaves and stems. ICAR recommends: (1) Use rust-resistant varieties like HD-3086 "
            "and PBW-550. (2) Apply Propiconazole (Tilt 25EC) at 0.1% at first sign of infection. "
            "(3) Avoid excessive nitrogen fertilisation which increases susceptibility. "
            "गेहूं का रतुआ रोग फफूंदी से होता है। पत्तियों पर नारंगी या भूरे रंग के दाने दिखते हैं। "
            "उपाय: प्रोपीकोनाज़ोल 25EC का ०.१% घोल छिड़कें।"
        ),
        "language": "en,hi",
        "domain": "agribot",
    },
    {
        "id": "agri-002",
        "title": "PM-KISAN Scheme – Farmer Benefits",
        "content": (
            "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi) provides ₹6,000 per year to eligible farmers in three "
            "equal installments of ₹2,000 every four months. Eligibility: All landholding farmer families. "
            "Exclusions: Income tax payers, former/current government employees, institutional landholders. "
            "Registration: Visit pmkisan.gov.in or nearest Common Service Centre (CSC). Documents needed: "
            "Aadhaar card, land records (khatauni), bank passbook. "
            "पीएम किसान: पात्र किसानों को ₹6000/वर्ष तीन किस्तों में मिलते हैं। "
            "pmkisan.gov.in पर या नजदीकी CSC पर रजिस्ट्रेशन करें।"
        ),
        "language": "en,hi",
        "domain": "agribot",
    },
    {
        "id": "agri-003",
        "title": "Drip Irrigation Guide for Small Farmers",
        "content": (
            "Drip irrigation saves 40-60% water compared to flood irrigation and increases crop yield by 20-50%. "
            "Suitable for: vegetables, fruits, sugarcane, cotton. Installation cost: ₹40,000-₹1,00,000 per hectare. "
            "Government subsidy: 55% for small/marginal farmers under PMKSY (Pradhan Mantri Krishi Sinchayee Yojana). "
            "ICAR recommendations for drip: Use emitters with 2-4 LPH output, lateral spacing 60-90cm. "
            "ड्रिप सिंचाई से 40-60% पानी की बचत होती है। PMKSY योजना के तहत छोटे किसानों को 55% सब्सिडी मिलती है।"
        ),
        "language": "en,hi",
        "domain": "agribot",
    },
    {
        "id": "agri-004",
        "title": "Paddy Brown Planthopper (BPH) Control",
        "content": (
            "Brown Planthopper (Nilaparvatha lugens) is a major pest of paddy in India. Symptoms: Circular burnt "
            "patches in field (hopper burn), plants collapse and look brown. Management: (1) Use resistant varieties "
            "like MTU-7029, Swarna Sub-1. (2) Drain water from field for 3-4 days. (3) Apply Buprofezin 25SC "
            "at 1ml/litre or Imidacloprid 17.8SL at 0.3ml/litre. (4) Avoid excessive nitrogen. "
            "Avoid broad-spectrum pesticides that kill natural enemies. "
            "ब्राउन प्लांटहॉपर धान की प्रमुख कीट है। खेत से पानी निकालें, बुप्रोफेज़िन या इमिडाक्लोप्रिड का उपयोग करें।"
        ),
        "language": "en,hi",
        "domain": "agribot",
    },
    {
        "id": "agri-005",
        "title": "Mandi Price Guide and eNAM Platform",
        "content": (
            "eNAM (National Agriculture Market) is an online trading portal connecting APMC mandis across India. "
            "Farmers can check real-time prices on enam.gov.in or the eNAM mobile app. Key mandi prices (approximate): "
            "Wheat MSP ₹2,275/quintal, Paddy MSP ₹2,183/quintal, Cotton MSP ₹6,620/quintal, "
            "Soybean MSP ₹4,600/quintal, Maize MSP ₹2,090/quintal. "
            "To sell on eNAM: Register at nearest APMC, get trader licence, bring quality produce. "
            "किसान enam.gov.in पर मंडी भाव देख सकते हैं। गेहूं MSP ₹2275/क्विंटल, धान MSP ₹2183/क्विंटल।"
        ),
        "language": "en,hi",
        "domain": "agribot",
    },
    {
        "id": "agri-006",
        "title": "Soil Health Card Scheme",
        "content": (
            "Soil Health Card (SHC) scheme provides every farmer with a card showing soil nutrient status every 2 years. "
            "The card shows 12 parameters including NPK, pH, organic carbon, sulphur, zinc, boron, iron, manganese, copper. "
            "Based on the card, farmers get fertiliser recommendations to reduce input costs and improve yield. "
            "To get SHC: Contact local Agriculture Department or Krishi Vigyan Kendra (KVK). "
            "Website: soilhealth.dac.gov.in. "
            "मृदा स्वास्थ्य कार्ड से किसान को उर्वरक सलाह मिलती है। soilhealth.dac.gov.in पर जानकारी पाएं।"
        ),
        "language": "en,hi",
        "domain": "agribot",
    },
]

HEALTH_DOCS: list[dict[str, str]] = [
    {
        "id": "health-001",
        "title": "Malaria Symptoms and Treatment",
        "content": (
            "Malaria is caused by Plasmodium parasites spread by female Anopheles mosquitoes. "
            "Symptoms: High fever with chills, headache, muscle pain, vomiting, occurring in cycles (every 48-72 hours). "
            "Diagnosis: Rapid Diagnostic Test (RDT) or blood smear – available free at all government PHCs. "
            "Treatment: Chloroquine for P.vivax; Artemisinin Combination Therapy (ACT) for P.falciparum. "
            "Prevention: Sleep under insecticide-treated bed nets (ITN), use mosquito repellent, eliminate stagnant water. "
            "National Malaria Helpline: 1800-11-8181. "
            "⚠️ Always consult a doctor for diagnosis and treatment. "
            "मलेरिया: तेज़ बुखार, कंपकंपी, सिरदर्द। नजदीकी PHC में मुफ्त RDT जांच करवाएं।"
        ),
        "language": "en,hi",
        "domain": "healthbot",
    },
    {
        "id": "health-002",
        "title": "Ayushman Bharat – PMJAY Health Insurance",
        "content": (
            "Ayushman Bharat PM-JAY provides health insurance cover of ₹5 lakh per family per year for "
            "secondary and tertiary care hospitalisation to over 10 crore poor and vulnerable families. "
            "Eligibility: Families listed in SECC 2011 data. Check eligibility: mera.pmjay.gov.in. "
            "Benefits: Covers pre and post hospitalisation, medicines, diagnostics, OT charges. "
            "How to use: Show Aadhaar/ration card at empanelled hospital. "
            "Helpline: 14555 / 1800-111-565. "
            "आयुष्मान भारत: प्रति परिवार ₹5 लाख तक का मुफ्त इलाज। mera.pmjay.gov.in पर पात्रता जांचें।"
        ),
        "language": "en,hi",
        "domain": "healthbot",
    },
    {
        "id": "health-003",
        "title": "Child Immunisation Schedule in India",
        "content": (
            "India's Universal Immunisation Programme (UIP) provides free vaccines to all children. "
            "Schedule: At birth: BCG, OPV-0, Hepatitis B. At 6 weeks: OPV-1, Pentavalent-1, Rotavirus-1, fIPV-1, PCV-1. "
            "At 10 weeks: OPV-2, Pentavalent-2, Rotavirus-2. At 14 weeks: OPV-3, Pentavalent-3, IPV-2, Rotavirus-3, PCV-2. "
            "At 9-12 months: Measles-Rubella (MR)-1, PCV booster, JE-1 (endemic areas), Vitamin A. "
            "At 16-24 months: DPT booster, OPV booster, MR-2, JE-2, Vitamin A. "
            "Contact your nearest ASHA worker or ANM for the immunisation card. "
            "टीकाकरण: शिशु को सही समय पर सभी सरकारी टीके मुफ्त में लगवाएं। ASHA दीदी से संपर्क करें।"
        ),
        "language": "en,hi",
        "domain": "healthbot",
    },
    {
        "id": "health-004",
        "title": "Diarrhoea and ORS Treatment",
        "content": (
            "Diarrhoea is a leading cause of child mortality in India. Key treatment is Oral Rehydration Solution (ORS). "
            "ORS recipe: 1 litre clean boiled water + 6 teaspoons sugar + 1/2 teaspoon salt. Stir and give frequently. "
            "OR use WHO-ORS sachets available free at all PHCs and Anganwadi centres. "
            "Zinc supplementation: 20mg/day for 14 days reduces duration and severity. "
            "Warning signs to go to hospital immediately: blood in stool, no urination for 8+ hours, very sunken eyes, "
            "child refuses to drink, high fever. "
            "AYUSH tip: Pomegranate juice and boiled rice water help rehydration. "
            "⚠️ बच्चे को दस्त हो तो ORS पिलाएं। खून वाले दस्त या पेशाब बंद हो जाए तो तुरंत अस्पताल जाएं।"
        ),
        "language": "en,hi",
        "domain": "healthbot",
    },
    {
        "id": "health-005",
        "title": "Mental Health Resources and NIMHANS Helpline",
        "content": (
            "Mental health is as important as physical health. Common conditions: depression, anxiety, stress, "
            "substance addiction. Warning signs: persistent sadness, loss of interest, sleep problems, hopelessness. "
            "Free helplines in India: iCall – 9152987821. Vandrevala Foundation – 1860-2662-345. "
            "NIMHANS helpline – 080-46110007. Govt Tele MANAS – 14416. "
            "Community resources: ASHA workers trained in mhGAP, District Mental Health Programme (DMHP) at DHH. "
            "Ayurveda tips for stress: Ashwagandha, Brahmi tea, Yoga and Pranayama under certified practitioner. "
            "⚠️ Please consult a doctor for diagnosis and treatment of mental health conditions. "
            "मानसिक स्वास्थ्य हेल्पलाइन: iCall 9152987821, Tele MANAS 14416। मदद लेना कमज़ोरी नहीं है।"
        ),
        "language": "en,hi",
        "domain": "healthbot",
    },
]

LAW_DOCS: list[dict[str, str]] = [
    {
        "id": "law-001",
        "title": "How to File an FIR (First Information Report)",
        "content": (
            "An FIR is a written document prepared by police when they receive information about a cognizable offence. "
            "Steps to file an FIR: (1) Go to the police station that has jurisdiction over the area where the crime occurred. "
            "(2) Give your complaint in writing or orally. The police must write it down and read it back to you (Section 154 CrPC). "
            "(3) Sign the FIR and get a free copy. If police refuse, you can: send written complaint to Superintendent of Police. "
            "File a complaint at Magistrate's court under Section 156(3) CrPC. Email to SP/IG of police. "
            "Online FIR: Many states allow online FIR for certain offences – check your state police website. "
            "⚠️ यह जानकारी केवल सामान्य जागरूकता के लिए है, कानूनी सलाह नहीं। "
            "FIR दर्ज करवाना आपका अधिकार है। पुलिस मना करे तो SP को लिखित शिकायत दें।"
        ),
        "language": "en,hi",
        "domain": "lawbot",
    },
    {
        "id": "law-002",
        "title": "RTI Application – How to File",
        "content": (
            "The Right to Information Act 2005 gives every citizen the right to seek information from public authorities. "
            "How to file RTI: (1) Write an application addressed to the Public Information Officer (PIO) of the concerned department. "
            "Mention: Your name, address, specific information sought, preferred format (paper/electronic). "
            "(2) Pay fee: ₹10 (by IPO or demand draft) – BPL applicants are exempt. "
            "(3) Send by post or hand over at PIO's office. Get an acknowledgement. "
            "Timeline: Response in 30 days (48 hours for life/liberty matters). "
            "If no response or rejected: File First Appeal with Appellate Authority. If still unsatisfied: "
            "File Second Appeal with State/Central Information Commission. Online: rtionline.gov.in. "
            "⚠️ RTI जानकारी के लिए आवेदन PIO को ₹10 शुल्क के साथ दें। 30 दिन में जवाब मिलना चाहिए।"
        ),
        "language": "en,hi",
        "domain": "lawbot",
    },
    {
        "id": "law-003",
        "title": "NALSA – Free Legal Aid for Eligible Citizens",
        "content": (
            "The National Legal Services Authority (NALSA) provides free legal aid to eligible persons under Legal Services "
            "Authorities Act 1987. Eligible persons: Women and children, SC/ST members, persons with disabilities, "
            "BPL families, victims of trafficking, industrial workmen, persons in custody. "
            "Services: Free legal advice, free lawyer in court, mediation services, Lok Adalat. "
            "Lok Adalat: An alternative dispute resolution forum where cases are settled mutually. "
            "Award is final and binding, no court fees required. Suitable for: motor accident claims, "
            "matrimonial disputes, labour disputes, land acquisition. "
            "Contact: NALSA Helpline 1516 (toll-free). Visit District Legal Services Authority (DLSA) at District Court. "
            "⚠️ NALSA हेल्पलाइन 1516 पर मुफ्त कानूनी सलाह लें। लोक अदालत में केस जल्दी निपटता है।"
        ),
        "language": "en,hi",
        "domain": "lawbot",
    },
    {
        "id": "law-004",
        "title": "Consumer Rights and How to File a Complaint",
        "content": (
            "The Consumer Protection Act 2019 provides strong rights to consumers. Six consumer rights: "
            "Right to Safety, Right to Information, Right to Choose, Right to be Heard, Right to Redressal, "
            "Right to Consumer Education. "
            "How to file complaint: (1) First give written notice (legal notice) to seller/company. "
            "(2) If unresolved, file at Consumer Commission: District Consumer Disputes Redressal Commission (DCDRC) "
            "for claims up to ₹50 lakh. State CDRC for ₹50 lakh to ₹2 crore. National CDRC for above ₹2 crore. "
            "Online complaint: edaakhil.nic.in (free of cost). No need for lawyer. "
            "Time limit: Complaint must be filed within 2 years of cause of action. "
            "⚠️ उपभोक्ता शिकायत: edaakhil.nic.in पर ऑनलाइन मुफ्त शिकायत करें।"
        ),
        "language": "en,hi",
        "domain": "lawbot",
    },
    {
        "id": "law-005",
        "title": "Domestic Violence – Protection and Remedies",
        "content": (
            "The Protection of Women from Domestic Violence Act 2005 (PWDVA) protects women from physical, "
            "emotional, sexual, verbal, and economic abuse by any family member. "
            "Who can complain: Any woman (wife, daughter, mother, sister, live-in partner). "
            "Remedies available: Protection Order (to stop abuser from committing violence), "
            "Residence Order (cannot be evicted from shared household), Monetary Relief, "
            "Custody Order (temporary custody of children), Compensation Order. "
            "How to get help: Contact Protection Officer (PO) in your district. Visit nearest police station. "
            "Call Women Helpline 181 (free, 24/7). Contact NGOs or Legal Aid Services. "
            "Emergency: Call 112. "
            "⚠️ घरेलू हिंसा पर तुरंत महिला हेल्पलाइन 181 पर कॉल करें। यह 24/7 मुफ्त है।"
        ),
        "language": "en,hi",
        "domain": "lawbot",
    },
]

# ---------------------------------------------------------------------------
# Index creation and document upload
# ---------------------------------------------------------------------------


def create_index(client, index_name: str) -> None:
    """Create a search index with the standard BharatBot schema.

    Args:
        client: An Azure SearchIndexClient instance.
        index_name: The name of the index to create.
    """
    from azure.search.documents.indexes.models import (  # noqa: PLC0415
        SearchField, SearchFieldDataType, SearchIndex, SimpleField, SearchableField
    )

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SimpleField(name="language", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="domain", type=SearchFieldDataType.String, filterable=True),
    ]

    index = SearchIndex(name=index_name, fields=fields)
    try:
        client.create_or_update_index(index)
        logger.info("✅ Index '%s' created/updated.", index_name)
    except Exception as exc:
        logger.error("❌ Failed to create index '%s': %s", index_name, exc)
        raise


def upload_documents(client, index_name: str, docs: list[dict]) -> None:
    """Upload a list of documents to an Azure AI Search index.

    Args:
        client: An Azure SearchClient instance.
        index_name: Target index name (for logging).
        docs: List of document dicts to upload.
    """
    try:
        result = client.upload_documents(documents=docs)
        succeeded = sum(1 for r in result if r.succeeded)
        logger.info(
            "📤 Uploaded %d/%d documents to index '%s'.",
            succeeded, len(docs), index_name,
        )
    except Exception as exc:
        logger.error("❌ Failed to upload documents to '%s': %s", index_name, exc)


def main() -> None:
    """Main entry point: create indexes and upload all sample documents."""
    if not SEARCH_ENDPOINT or not SEARCH_KEY:
        logger.error(
            "SEARCH_ENDPOINT and SEARCH_KEY must be set in .env. Exiting."
        )
        sys.exit(1)

    try:
        from azure.core.credentials import AzureKeyCredential  # noqa: PLC0415
        from azure.search.documents import SearchClient  # noqa: PLC0415
        from azure.search.documents.indexes import SearchIndexClient  # noqa: PLC0415
    except ImportError:
        logger.error("azure-search-documents is not installed. Run: pip install azure-search-documents")
        sys.exit(1)

    credential = AzureKeyCredential(SEARCH_KEY)
    index_client = SearchIndexClient(endpoint=SEARCH_ENDPOINT, credential=credential)

    datasets = [
        (INDEX_AGRI,   AGRI_DOCS),
        (INDEX_HEALTH, HEALTH_DOCS),
        (INDEX_LAW,    LAW_DOCS),
    ]

    for index_name, docs in datasets:
        logger.info("─── Processing index: %s ───", index_name)
        create_index(index_client, index_name)

        search_client = SearchClient(
            endpoint=SEARCH_ENDPOINT,
            index_name=index_name,
            credential=credential,
        )
        upload_documents(search_client, index_name, docs)

    logger.info("🎉 Knowledge base population complete!")


if __name__ == "__main__":
    main()
