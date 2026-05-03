"""
Kalchachani 2025-26 — SSC Career Guidance Assessment
Maharashtra State Board authentic framework (based on original Kalchachani 2016-17)
7 Career Interest Groups (रुची गट) — NOT Holland RIASEC

Flask Backend: submission handler, scoring engine, HTML report generator
Run: python app.py
Admin: http://localhost:5000/admin?pw=kalchachani2025
Test:  http://localhost:5000/test
"""

from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for, abort
from flask_cors import CORS
import json, os, uuid, datetime
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from io import BytesIO
import base64

app = Flask(__name__)
CORS(app)

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "kalchachani2025")

# ─────────────────────────────────────────────
# AUTHENTIC MAHARASHTRA BOARD FRAMEWORK
# 7 Career Interest Groups (रुची गट)
# Directly from the original Kalchachani assessment
# ─────────────────────────────────────────────

INTEREST_GROUPS = [
    'vigyan_tantra',      # विज्ञान-तंत्रज्ञान
    'vanijya_udyog',      # वाणिज्य-उद्योग
    'kala_sahitya',       # कला-साहित्य
    'samaj_shikshan',     # समाजसेवा-शिक्षण
    'arogya_seva',        # आरोग्य-सेवा
    'krushi_paryavaran',  # कृषी-पर्यावरण
    'prashasan_rakshan',  # प्रशासन-संरक्षण
]

INTEREST_MR = {
    'vigyan_tantra':      'विज्ञान-तंत्रज्ञान',
    'vanijya_udyog':      'वाणिज्य-उद्योग',
    'kala_sahitya':       'कला-साहित्य',
    'samaj_shikshan':     'समाजसेवा-शिक्षण',
    'arogya_seva':        'आरोग्य-सेवा',
    'krushi_paryavaran':  'कृषी-पर्यावरण',
    'prashasan_rakshan':  'प्रशासन-संरक्षण',
}

INTEREST_EN = {
    'vigyan_tantra':      'Science & Technology',
    'vanijya_udyog':      'Commerce & Industry',
    'kala_sahitya':       'Arts & Literature',
    'samaj_shikshan':     'Social Service & Education',
    'arogya_seva':        'Health & Medical',
    'krushi_paryavaran':  'Agriculture & Environment',
    'prashasan_rakshan':  'Administration & Defence',
}

INTEREST_COLOR = {
    'vigyan_tantra':      '#2563EB',
    'vanijya_udyog':      '#D97706',
    'kala_sahitya':       '#7C3AED',
    'samaj_shikshan':     '#16A34A',
    'arogya_seva':        '#DC2626',
    'krushi_paryavaran':  '#059669',
    'prashasan_rakshan':  '#374151',
}

# ─────────────────────────────────────────────
# LOCATION → MMR REGION MAPPING
# Maps student district to the nearest MMR hub (≤70 km radius)
# ─────────────────────────────────────────────

# Districts/talukas that fall within ~60-70 km of each MMR hub
MMR_REGION_MAP = {
    # Mumbai city & island
    'mumbai':           'mumbai',
    'mumbai city':      'mumbai',
    'mumbai suburban':  'mumbai',
    'south mumbai':     'mumbai',
    'colaba':           'mumbai',
    'fort':             'mumbai',
    'dadar':            'mumbai',
    'worli':            'mumbai',
    'bandra':           'mumbai',
    'andheri':          'mumbai',
    'borivali':         'mumbai',
    'malad':            'mumbai',
    'goregaon':         'mumbai',
    'kandivali':        'mumbai',
    'dahisar':          'mumbai',
    'kurla':            'mumbai',
    'ghatkopar':        'mumbai',
    'vikhroli':         'mumbai',
    'mulund':           'mumbai',
    'chembur':          'mumbai',
    'mankhurd':         'mumbai',
    'trombay':          'mumbai',
    # Thane & surroundings (within 60 km of Thane)
    'thane':            'thane',
    'kalyan':           'thane',
    'dombivli':         'thane',
    'ulhasnagar':       'thane',
    'ambarnath':        'thane',
    'badlapur':         'thane',
    'murbad':           'thane',
    'shahapur':         'thane',
    'bhiwandi':         'thane',
    'navi mumbai':      'thane',
    'nerul':            'thane',
    'vashi':            'thane',
    'belapur':          'thane',
    'panvel':           'thane',
    'kharghar':         'thane',
    'airoli':           'thane',
    'ghansoli':         'thane',
    'kopar khairane':   'thane',
    'turbhe':           'thane',
    # Vasai-Virar / Palghar belt (within 60 km of Vasai)
    'vasai':            'vasai',
    'virar':            'vasai',
    'nalasopara':       'vasai',
    'nala sopara':      'vasai',
    'palghar':          'vasai',
    'boisar':           'vasai',
    'dahanu':           'vasai',
    'mira road':        'vasai',
    'bhayander':        'vasai',
    'vasai-virar':      'vasai',
    'vasai virar':      'vasai',
    # Raigad (within 70 km of Panvel/Raigad HQ)
    'raigad':           'raigad',
    'alibag':           'raigad',
    'pen':              'raigad',
    'uran':             'raigad',
    'khopoli':          'raigad',
    'karjat':           'raigad',
    'mahad':            'raigad',
    'mangaon':          'raigad',
    # Pune (within 60 km of Pune city)
    'pune':             'pune',
    'pimpri':           'pune',
    'chinchwad':        'pune',
    'pimpri-chinchwad': 'pune',
    'talegaon':         'pune',
    'lonavala':         'pune',
    'khed':             'pune',
    'chakan':           'pune',
    'dehu road':        'pune',
    'alandi':           'pune',
    'hadapsar':         'pune',
    'wagholi':          'pune',
    'katraj':           'pune',
    'sinhagad':         'pune',
}

def get_mmr_region(district_raw: str) -> str:
    """Return the MMR hub key for a district string, defaulting to 'mumbai'."""
    key = district_raw.strip().lower()
    return MMR_REGION_MAP.get(key, 'mumbai')


# ─────────────────────────────────────────────
# COLLEGE DATABASE — Location-aware, ranked best→good
# Each region lists 10-15 top colleges per interest group
# All colleges are within 60-70 km of the region hub
# ─────────────────────────────────────────────

COLLEGE_DB = {

  # ══════════════════════════════════════════
  # MUMBAI REGION (South Mumbai, Central, Western Suburbs)
  # ══════════════════════════════════════════
  'mumbai': {
    'vigyan_tantra': [
      '🥇 IIT Bombay, Powai — Premier engineering & technology (JEE Advanced)',
      '🥈 VJTI (Veermata Jijabai Technological Institute), Matunga',
      '🥉 ICT Mumbai (Institute of Chemical Technology), Matunga',
      '4. UDCT / ICT affiliated — Pharmacy & Chemical Engineering',
      '5. Fr. Conceicao Rodrigues College of Engineering (CRCE), Bandra',
      '6. Thadomal Shahani Engineering College (TSEC), Bandra',
      '7. K.J. Somaiya College of Engineering, Vidyavihar',
      '8. Sardar Patel College of Engineering (SPCE), Andheri',
      '9. Dwarkadas J. Sanghvi College of Engineering (DJSCE), Vile Parle',
      '10. Ramrao Adik Institute of Technology (RAIT), Nerul',
      '11. Vidyalankar Institute of Technology (VIT), Wadala',
      '12. Rizvi College of Engineering, Bandra',
      '13. Shah & Anchor Kutchhi Engineering College, Chembur',
      '14. Don Bosco Institute of Technology (DBIT), Kurla',
      '15. Atharva College of Engineering, Malad',
    ],
    'vanijya_udyog': [
      '🥇 Sydenham College of Commerce & Economics, Churchgate — Top Commerce (Mumbai Univ)',
      '🥈 H.R. College of Commerce & Economics, Churchgate',
      '🥉 N.M. College of Commerce & Economics, Vile Parle',
      '4. Jai Hind College, Churchgate — Commerce & Arts',
      '5. K.C. College (Hyderabad Estate), Churchgate',
      '6. Podar College of Commerce & Economics, Matunga',
      '7. R.A. Podar College of Commerce, Matunga',
      '8. Mithibai College of Arts, Science & Commerce, Vile Parle',
      '9. Narsee Monjee College of Commerce, Vile Parle',
      '10. Lala Lajpatrai College of Commerce & Economics, Mahalaxmi',
      '11. Sathaye College, Vile Parle — Commerce',
      '12. Guru Nanak Khalsa College, Matunga',
      '13. VES College of Arts, Science & Commerce, Chembur',
      '14. Bhavan\'s College, Andheri — Commerce',
      '15. Wilson College, Chowpatty — Commerce',
    ],
    'kala_sahitya': [
      '🥇 Sir J.J. School of Art, Byculla — Premier Fine Arts & Design',
      '🥈 Xavier Institute of Communications (XIC), CST — Mass Media',
      '🥉 Sophia College for Women, Breach Candy — Arts & Mass Media',
      '4. Wilson College, Chowpatty — Arts / Literature',
      '5. St. Xavier\'s College, CST — Arts & Humanities',
      '6. Elphinstone College, Fort — Arts & Humanities',
      '7. Mithibai College, Vile Parle — Arts & Literature',
      '8. Ruia College, Matunga — Arts & Humanities',
      '9. K.J. Somaiya College of Arts & Commerce, Vidyavihar',
      '10. SNDT Women\'s University, Santacruz — Arts, Design',
      '11. Rachana Sansad School of Art & Design, Prabhadevi',
      '12. Sasmira\'s College of Arts, Science & Commerce, Worli',
      '13. Sathaye College, Vile Parle — Arts',
      '14. Jai Hind College, Churchgate — Arts & Media',
      '15. Bhavan\'s College, Andheri — Journalism & Communication',
    ],
    'samaj_shikshan': [
      '🥇 TISS (Tata Institute of Social Sciences), Deonar — Social Work (Autonomous)',
      '🥈 SNDT Women\'s University, Santacruz — Education, Psychology',
      '🥉 St. Xavier\'s College, CST — Sociology, Psychology',
      '4. Sophia College for Women — Psychology, Sociology',
      '5. Wilson College — Sociology & Political Science',
      '6. Elphinstone College, Fort — Sociology, Political Science',
      '7. Ruia College, Matunga — Psychology, Sociology',
      '8. VES College of Arts, Chembur — Social Sciences',
      '9. Nirmala Niketan College of Social Work, CST',
      '10. College of Social Work, Nirmala Niketan, Fort',
      '11. K.J. Somaiya College — Humanities & Education',
      '12. Bhavan\'s College, Andheri — Arts & Psychology',
      '13. Sathaye College, Vile Parle — Arts',
      '14. D.Ed / B.Ed Colleges across Mumbai under Mumbai University',
      '15. SNDT B.Ed College, Santacruz — Teacher Training',
    ],
    'arogya_seva': [
      '🥇 Seth G.S. Medical College & KEM Hospital, Parel — Top Govt Medical',
      '🥈 Grant Medical College & J.J. Hospital, Byculla — Govt Medical',
      '🥉 Topiwala National Medical College (TNMC) & BYL Nair Hospital, Mumbai Central',
      '4. Lokmanya Tilak Medical College (LTMC), Sion',
      '5. K.J. Somaiya Medical College & Hospital, Sion',
      '6. Bai Jerbai Wadia Hospital / Wadia Medical — Paediatrics',
      '7. Bombay Hospital Medical College, Marine Lines',
      '8. Sir H.N. Reliance Foundation Hospital — Allied Health',
      '9. Haffkine Institute, Parel — Pharmacy & Biomedical',
      '10. SNDT College of Nursing, Santacruz',
      '11. St. George\'s Hospital Nursing College, CST',
      '12. MAEER\'s Maharashtra Institute of Pharmacy, Pune Road',
      '13. MGM Dental College, Navi Mumbai',
      '14. TN Medical College & BYL Nair Hospital — Physiotherapy',
      '15. Rajiv Gandhi Medical College, Thane (within 30 km)',
    ],
    'krushi_paryavaran': [
      '🥇 ICT Mumbai — Environmental Science & Engineering',
      '🥈 Bombay Natural History Society (BNHS), Hornbill House — Wildlife / Env',
      '🥉 College of Fisheries, Palghar / Ratnagiri (affiliated DBATU)',
      '4. VJTI Mumbai — Environmental Engineering',
      '5. Rizvi College of Engineering — Environmental Engg',
      '6. UDCT / ICT — Food Technology & Agri-Chemistry',
      '7. SNDT College — Home Science / Food & Nutrition',
      '8. Sathaye College — Environmental Studies',
      '9. Sophia College — Life Sciences / Botany',
      '10. St. Xavier\'s College — Zoology, Botany, Environment',
      '11. Ruia College — Zoology, Botany',
      '12. Wilson College — Life Sciences',
      '13. K.J. Somaiya College of Science — Biotechnology, Environment',
      '14. SNDT Women\'s University — Food Nutrition & Dietetics',
      '15. Jai Hind College — Life Sciences',
    ],
    'prashasan_rakshan': [
      '🥇 Government Law College, Churchgate — Top Law / UPSC',
      '🥈 ILS Law College (affiliated) / Sydenham — Law & Political Science',
      '🥉 K.C. Law College, Churchgate',
      '4. Rizvi Law College, Bandra',
      '5. New Law College, Bharati Vidyapeeth, Mumbai',
      '6. NMIMS School of Law, Vile Parle',
      '7. St. Xavier\'s College — Political Science & Civics',
      '8. Elphinstone College — Political Science, History',
      '9. Wilson College — Political Science',
      '10. Podar College — Commerce (for Bank/MPSC prep)',
      '11. Sydenham College — MPSC / Civil Services oriented Commerce',
      '12. NDA (National Defence Academy) — via Khadakwasla, Pune (for Std XII boys)',
      '13. Sainik School, Satara (entrance-based, residential)',
      '14. Maharashtra Police Academy orientation — SPJ Sadhana College, Andheri',
      '15. IDBI Bank / SBI affiliated coaching: Dadar Institute of Management Studies',
    ],
  },

  # ══════════════════════════════════════════
  # THANE / NAVI MUMBAI REGION (within 60 km of Thane station)
  # Covers: Kalyan, Dombivli, Ulhasnagar, Ambarnath, Badlapur,
  #         Navi Mumbai, Panvel, Bhiwandi, Shahapur
  # ══════════════════════════════════════════
  'thane': {
    'vigyan_tantra': [
      '🥇 VJTI Mumbai, Matunga (~30 km from Thane) — Top Engg',
      '🥈 Lokmanya Tilak College of Engineering (LTCE), Kopar Khairane, Navi Mumbai',
      '🥉 Pillai College of Engineering (PCE), New Panvel',
      '4. SIES Graduate School of Technology, Nerul, Navi Mumbai',
      '5. Thakur College of Engineering & Technology (TCET), Kandivali (40 km)',
      '6. Terna Engineering College, Nerul, Navi Mumbai',
      '7. Rajiv Gandhi Institute of Technology (RGIT), Andheri (~35 km)',
      '8. K.C. College of Engineering & Management Studies, Kopri, Thane',
      '9. Universal College of Engineering, Vasai (~50 km)',
      '10. Datta Meghe College of Engineering, Airoli, Navi Mumbai',
      '11. Guru Nanak Institutions Technical Campus, Ibrahimpatnam (~45 km)',
      '12. Maharashtra Institute of Technology (MIT), Polytechnic — Thane',
      '13. Saraswati College of Engineering, Kharghar, Navi Mumbai',
      '14. Finolex Academy of Management & Technology, Ratnagiri (~via coastal)',
      '15. Bharati Vidyapeeth College of Engineering, Navi Mumbai',
    ],
    'vanijya_udyog': [
      '🥇 Sydenham College of Commerce, Churchgate (~32 km from Thane)',
      '🥈 Ramniranjan Jhunjhunwala (RJ) College, Ghatkopar — Commerce',
      '🥉 Vivekanand Education Society (VES) College, Chembur — Commerce',
      '4. B.N. Bandodkar College of Science & Commerce, Thane',
      '5. K.V. Pendharkar College of Arts, Science & Commerce, Dombivli',
      '6. Rambhau Mhalgi Prabodhini — Governance & Policy, Thane',
      '7. SIES College of Arts, Science & Commerce, Sion (~28 km)',
      '8. Karmaveer Bhaurao Patil College (KBP), Vashi, Navi Mumbai',
      '9. Pillai College of Arts, Commerce & Science, New Panvel',
      '10. Dnyanasadhana College, Thane — Commerce',
      '11. Saraswat College, Borivali (~40 km) — Commerce',
      '12. Pace Junior Science College, Thane — Foundation for CA/CS',
      '13. Vidyalankar College of Commerce, Wadala (~30 km)',
      '14. Shri Chinai College, Andheri (~35 km) — Commerce',
      '15. ICAI (CA Foundation) — Study Centres in Thane, Navi Mumbai',
    ],
    'kala_sahitya': [
      '🥇 Sir J.J. School of Art, Byculla (~32 km) — Fine Arts & Design',
      '🥈 XIC (Xavier Institute of Communications), CST (~32 km) — Mass Media',
      '🥉 Rachana Sansad Academy of Fine Arts & Crafts, Dadar (~30 km)',
      '4. B.N. Bandodkar College, Thane — Arts & Literature',
      '5. K.V. Pendharkar College of Arts, Dombivli',
      '6. Pillai College of Arts, Panvel — Journalism, Literature',
      '7. SIES College of Arts, Sion — Literature, Mass Media',
      '8. V.G. Vaze College, Mulund — Arts',
      '9. Ramniranjan Jhunjhunwala College, Ghatkopar — Arts',
      '10. Dnyanasadhana College, Thane — Arts',
      '11. Chikitsak Samuha\'s RD National College, Bandra (~40 km) — Arts',
      '12. Guru Nanak Khalsa College, Matunga (~30 km) — Arts',
      '13. KBP College, Vashi — Arts & Communication',
      '14. Mithibai College, Vile Parle (~35 km) — Mass Media',
      '15. Jai Hind College, Churchgate (~35 km) — Media & Arts',
    ],
    'samaj_shikshan': [
      '🥇 TISS (Tata Institute of Social Sciences), Deonar (~32 km) — Social Work',
      '🥈 SNDT Women\'s University, Santacruz (~35 km) — Education, Psychology',
      '🥉 B.N. Bandodkar College of Science, Thane — Psychology',
      '4. K.V. Pendharkar College, Dombivli — Psychology, Sociology',
      '5. Pilllai College, Panvel — Social Sciences',
      '6. VES College, Chembur (~30 km) — Psychology',
      '7. Ramniranjan Jhunjhunwala College, Ghatkopar — Social Sciences',
      '8. KBP College, Vashi — Education & Social Work',
      '9. Kalyan College, Kalyan — Arts & Social Sciences',
      '10. Ulhasnagar College — Arts (Social Sciences)',
      '11. Dombivli College — Arts & Education',
      '12. Saraswati Education Society College, Kharghar — Social Work',
      '13. D.Ed / B.Ed Colleges in Thane, Kalyan, Dombivli districts',
      '14. Maharashtra College of Education, Thane — B.Ed',
      '15. Nirmala Niketan College of Social Work, Fort (~32 km)',
    ],
    'arogya_seva': [
      '🥇 Rajiv Gandhi Medical College & CSM Hospital, Thane',
      '🥈 MGM Medical College & Hospital, Kamothe, Navi Mumbai',
      '🥉 Sion Hospital (LTMC & GH), Sion (~30 km)',
      '4. D.Y. Patil Medical College, Nerul, Navi Mumbai',
      '5. MGM Dental College & Hospital, Kamothe',
      '6. Terna Medical College, Nerul, Navi Mumbai',
      '7. Grant Medical College (GS Medical), Byculla (~32 km)',
      '8. Maharashtra University of Health Sciences (MUHS) affiliated — Panvel',
      '9. Dr. D.Y. Patil Ayurved College (BAMS), Nerul',
      '10. Thane Belapur Industrial Area — Allied Health Institutes',
      '11. Apollo Pharmacy College, Navi Mumbai',
      '12. Lokmanya Tilak Municipal Medical College, Sion (~30 km)',
      '13. SIES College of Physiotherapy, Sion',
      '14. Nursing Colleges — Thane Civil Hospital, KEM Thane',
      '15. Pillai College of Pharmacy, New Panvel',
    ],
    'krushi_paryavaran': [
      '🥇 Dr. Balasaheb Sawant Konkan Krishi Vidyapeeth, Dapoli (~120 km, regional best)',
      '🥈 College of Fisheries, Shirgaon, Ratnagiri (DBSKKV affiliated)',
      '🥉 VJTI Mumbai — Environmental Engineering (~32 km)',
      '4. Pillai College of Engineering — Environmental Engg, Panvel',
      '5. B.N. Bandodkar College — Zoology, Botany, Life Sciences, Thane',
      '6. K.V. Pendharkar College — Life Sciences, Dombivli',
      '7. SIES College, Sion — Biotechnology, Life Sciences',
      '8. Terna College, Nerul — Environmental Science',
      '9. V.G. Vaze College, Mulund — Botany, Zoology',
      '10. Ramniranjan Jhunjhunwala College — Life Sciences',
      '11. KBP College, Vashi — Environmental Science',
      '12. Saraswati College, Kharghar — Life Sciences',
      '13. Ulhasnagar College — Life Sciences / Agriculture',
      '14. ICT Mumbai — Food Technology & Agri-Chemistry (~32 km)',
      '15. SNDT College — Food Science & Nutrition (~35 km)',
    ],
    'prashasan_rakshan': [
      '🥇 Government Law College, Churchgate (~32 km) — Law & UPSC prep',
      '🥈 New Law College, Vashi, Navi Mumbai',
      '🥉 School of Law, MIT-WPU, Navi Mumbai Campus',
      '4. K.C. Law College, Churchgate (~32 km)',
      '5. Pillai College, Panvel — Political Science',
      '6. B.N. Bandodkar College, Thane — Political Science, History',
      '7. K.V. Pendharkar College, Dombivli — Arts & Political Science',
      '8. Kalyan College, Kalyan — Arts & Civics',
      '9. Ulhasnagar College — Arts & Social Sciences',
      '10. KBP College, Vashi — Commerce & Administration',
      '11. VES College, Chembur — Political Science (~30 km)',
      '12. NDA, Khadakwasla, Pune (~90 km — best for defence)',
      '13. Sainik School Satara — residential, competitive entry',
      '14. MPSC / UPSC coaching: Rambhau Mhalgi Prabodhini, Thane',
      '15. Bank PO Prep: Datta Meghe Institute — Management Studies, Airoli',
    ],
  },

  # ══════════════════════════════════════════
  # VASAI-VIRAR / PALGHAR REGION
  # Covers: Vasai, Virar, Nalasopara, Mira Road, Bhayander,
  #         Palghar, Boisar, Dahanu (within 60 km)
  # ══════════════════════════════════════════
  'vasai': {
    'vigyan_tantra': [
      '🥇 Universal College of Engineering (UCOE), Kaman, Vasai',
      '🥈 Shri L.R. Tiwari College of Engineering, Mira Road',
      '🥉 Thakur College of Engineering & Technology (TCET), Kandivali (~35 km)',
      '4. Atharva College of Engineering, Malad (~35 km)',
      '5. Rizvi College of Engineering, Bandra (~50 km)',
      '6. Sandip Institute of Technology, Nashik (~60 km)',
      '7. Sardar Patel College of Engineering (SPCE), Andheri (~45 km)',
      '8. Lokmanya Tilak College of Engineering, Kopar Khairane (~45 km)',
      '9. VJTI, Matunga (~55 km via train) — Premier Engg',
      '10. Bhagwan Mahavir Polytechnic, Vasai — Diploma',
      '11. Government Polytechnic, Palghar',
      '12. Maharashtra Academy of Engineering, Alandi (~65 km) — Polytechnic',
      '13. Rajiv Gandhi Institute of Technology, Andheri (~45 km)',
      '14. K.C. College of Engineering, Kopri, Thane (~40 km)',
      '15. SIES Graduate School of Technology, Nerul (~50 km)',
    ],
    'vanijya_udyog': [
      '🥇 Sydenham College of Commerce, Churchgate (~55 km) — Top Commerce',
      '🥈 H.R. College, Churchgate (~55 km)',
      '🥉 N.M. College, Vile Parle (~45 km)',
      '4. Mithibai College, Vile Parle (~45 km) — Commerce',
      '5. St. Gonsalo Garcia College of Arts & Commerce, Vasai',
      '6. Fr. Agnel College of Arts & Commerce, Vasai',
      '7. Gokhale Education Society\'s College, Palghar',
      '8. Saraswat Education Society College, Borivali (~35 km)',
      '9. Thakur College of Science & Commerce, Kandivali (~35 km)',
      '10. Malini Kishor Sanghvi College, Vile Parle (~45 km)',
      '11. Bhavan\'s College, Andheri (~48 km) — Commerce',
      '12. ICAI Study Centre — Vasai Road, Mira Road',
      '13. Bhagwan Mahavir College of Commerce & Management, Vasai',
      '14. SNDT College, Santacruz (~50 km) — Commerce',
      '15. Pace Junior Science College — Mira Road (Commerce)',
    ],
    'kala_sahitya': [
      '🥇 Sir J.J. School of Art, Byculla (~55 km) — Fine Arts & Design',
      '🥈 Rachana Sansad Academy of Fine Arts, Dadar (~50 km)',
      '🥉 XIC Mumbai, CST (~55 km) — Mass Media & Journalism',
      '4. Fr. Agnel College, Vasai — Arts & Literature',
      '5. St. Gonsalo Garcia College, Vasai — Arts',
      '6. Mithibai College, Vile Parle (~45 km) — Mass Media',
      '7. Jai Hind College, Churchgate (~55 km) — Mass Media',
      '8. Thakur College of Science & Commerce, Kandivali — Arts',
      '9. Saraswat College, Borivali (~35 km) — Arts',
      '10. N.M. College, Vile Parle — Mass Media',
      '11. SNDT Women\'s University — Mass Comm & Design (~50 km)',
      '12. Gokhale Education Society College, Palghar — Arts',
      '13. Bhavan\'s College, Andheri (~48 km) — Arts',
      '14. Bhagwan Mahavir College, Vasai — Arts & Humanities',
      '15. Government Diploma in Art, Vasai (State Art School)',
    ],
    'samaj_shikshan': [
      '🥇 TISS, Deonar (~55 km) — Social Work (Best in India)',
      '🥈 SNDT Women\'s University, Santacruz (~50 km) — Education',
      '🥉 Fr. Agnel College, Vasai — Social Sciences & Psychology',
      '4. St. Gonsalo Garcia College, Vasai — Psychology & Sociology',
      '5. Gokhale Education Society College, Palghar — Arts',
      '6. Saraswat College, Borivali (~35 km) — Psychology',
      '7. Thakur College, Kandivali — Arts & Social Sciences',
      '8. VES College, Chembur (~50 km) — Social Sciences',
      '9. Mithibai College, Vile Parle (~45 km) — Psychology',
      '10. St. Xavier\'s College, CST (~55 km) — Social Work',
      '11. D.Ed / B.Ed Colleges in Vasai, Virar, Palghar',
      '12. Maharashtra College of Education — Vasai-Virar',
      '13. Wilson College, Chowpatty (~55 km) — Sociology',
      '14. St. Andrew\'s College, Bandra (~50 km) — Sociology',
      '15. KVNNS College, Dahanu — Arts & Social Sciences',
    ],
    'arogya_seva': [
      '🥇 Rajiv Gandhi Medical College, Thane (~30 km)',
      '🥈 Vedic Sansthan Ayurvedic Medical College (BAMS), Vasai',
      '🥉 Holy Family Hospital & Medical Research Centre, Bandra (~50 km)',
      '4. Dr. D.Y. Patil Medical College, Nerul (~45 km)',
      '5. Grant Medical College (J.J. Hospital), Byculla (~55 km)',
      '6. MGM Medical College, Kamothe (~55 km)',
      '7. Terna Medical College, Nerul (~45 km)',
      '8. St. Luke\'s Hospital Nursing College, Andheri (~45 km)',
      '9. Palghar District Civil Hospital — Nursing & Allied Health',
      '10. Boisar Government Medical Resources — Nursing Training',
      '11. Bhagwan Mahavir Pharmacy College, Vasai',
      '12. Pillai College of Pharmacy, New Panvel (~55 km)',
      '13. SNDT Nursing College, Santacruz (~50 km)',
      '14. MGM Dental College, Kamothe (~55 km)',
      '15. Physiotherapy College — Central India Institute, Mira Road',
    ],
    'krushi_paryavaran': [
      '🥇 Govind Ballabh Pant College of Agriculture, Pantnagar (~regional, NW)',
      '🥈 DBSKKV College of Fisheries, Dapoli (~120 km — nearest agri univ)',
      '🥉 Gokhale Education Society\'s Nature & Science College, Palghar',
      '4. Fr. Agnel College, Vasai — Life Sciences & Environment',
      '5. St. Gonsalo Garcia College, Vasai — Zoology, Botany',
      '6. Saraswat College, Borivali — Life Sciences (~35 km)',
      '7. Thakur College, Kandivali — Environmental Science',
      '8. V.G. Vaze College, Mulund (~40 km) — Botany, Zoology',
      '9. ICT Mumbai — Environmental & Chemical Engineering (~55 km)',
      '10. VJTI — Environmental Engineering (~55 km)',
      '11. Wilson College — Life Sciences (~55 km)',
      '12. Government Agriculture Office Training, Palghar — Extension',
      '13. Boisar Agri Research Centre (BARC support area) — Environment',
      '14. SNDT College — Food Science & Nutrition (~50 km)',
      '15. Bhagwan Mahavir College — Life Sciences, Vasai',
    ],
    'prashasan_rakshan': [
      '🥇 Government Law College, Churchgate (~55 km) — Law & MPSC/UPSC',
      '🥈 Fr. Agnel College, Vasai — Arts (Political Science)',
      '🥉 St. Gonsalo Garcia College, Vasai — Arts & Civics',
      '4. Gokhale Education Society College, Palghar — Arts & History',
      '5. Thakur College, Kandivali (~35 km) — Arts & Political Science',
      '6. Saraswat College, Borivali (~35 km) — Political Science',
      '7. Atharva Law School / NMD College of Law, Malad (~38 km)',
      '8. K.C. Law College, Churchgate (~55 km)',
      '9. New Law College, Vashi (~50 km)',
      '10. Bhavan\'s College, Andheri (~48 km) — Political Science',
      '11. NDA, Khadakwasla, Pune (~110 km — best for defence)',
      '12. MPSC Coaching: Mira Road Institute of Management & Civil Services',
      '13. Rambhau Mhalgi Prabodhini, Thane (~30 km) — Governance Studies',
      '14. IBPS / SBI PO prep: Tutorials in Virar & Nalasopara',
      '15. Sainik School Satara — residential, national competitive entry',
    ],
  },

  # ══════════════════════════════════════════
  # RAIGAD REGION (Alibag, Pen, Panvel, Khopoli, Karjat, Uran)
  # ══════════════════════════════════════════
  'raigad': {
    'vigyan_tantra': [
      '🥇 Pillai College of Engineering, New Panvel (~30 km from Alibag via Nhava)',
      '🥈 SIES Graduate School of Technology, Nerul, Navi Mumbai (~35 km)',
      '🥉 Terna Engineering College, Nerul (~35 km)',
      '4. Lokmanya Tilak College of Engineering, Kopar Khairane (~30 km)',
      '5. D.Y. Patil College of Engineering, Navi Mumbai (~32 km)',
      '6. Bharati Vidyapeeth College of Engineering, CBD Belapur (~28 km)',
      '7. MIT College of Engineering, Pune (~80 km — best for Karjat/Khopoli)',
      '8. Saraswati College of Engineering, Kharghar',
      '9. MGM College of Engineering, Navi Mumbai',
      '10. VJTI, Matunga (~50 km via Panvel) — Premier',
      '11. Datta Meghe College of Engineering, Airoli (~28 km)',
      '12. SIES Polytechnic, Sion (~45 km) — Diploma',
      '13. Government Polytechnic, Alibag',
      '14. Government Polytechnic, Khopoli',
      '15. Finolex Institute of Technology, Ratnagiri (~150 km — best coastal)',
    ],
    'vanijya_udyog': [
      '🥇 Sydenham College, Churchgate (~55 km via ferry+rail) — Top Commerce',
      '🥈 Pillai College of Arts, Commerce & Science, New Panvel',
      '🥉 KBP College of Arts, Commerce & Science, Vashi (~28 km)',
      '4. D.Y. Patil International University, Navi Mumbai — Commerce',
      '5. Saraswati Education Society College, Kharghar',
      '6. H.R. College, Churchgate (~55 km) — Commerce',
      '7. N.M. College, Vile Parle (~50 km) — Commerce',
      '8. Terna College of Commerce, Nerul (~30 km)',
      '9. Guru Nanak College, Navi Mumbai — Commerce',
      '10. Pen College, Pen — Arts & Commerce (Raigad dist)',
      '11. MGM College, Navi Mumbai — Commerce',
      '12. ICAI — Study Centre, Kharghar / Navi Mumbai',
      '13. Alibag College — Commerce',
      '14. Mahad College — Commerce (South Raigad)',
      '15. Bharati Vidyapeeth Commerce College, CBD Belapur',
    ],
    'kala_sahitya': [
      '🥇 Sir J.J. School of Art, Byculla (~50 km) — Fine Arts',
      '🥈 XIC Mumbai, CST (~55 km) — Mass Media',
      '🥉 Rachana Sansad, Dadar (~48 km) — Fine Arts & Design',
      '4. Pillai College, New Panvel — Arts & Literature',
      '5. KBP College, Vashi — Arts & Journalism',
      '6. Terna College, Nerul — Arts',
      '7. MGM College, Navi Mumbai — Humanities',
      '8. Alibag College, Alibag — Arts (Local)',
      '9. Pen College, Pen — Arts (Local)',
      '10. Saraswati College, Kharghar — Arts',
      '11. Mithibai College, Vile Parle (~50 km) — Mass Media',
      '12. Sophia College, Mumbai (~52 km) — Mass Media',
      '13. SNDT Women\'s University (~52 km) — Mass Comm',
      '14. D.Y. Patil University — Mass Comm, Navi Mumbai',
      '15. Mahad College, Mahad — Arts',
    ],
    'samaj_shikshan': [
      '🥇 TISS, Deonar (~45 km) — Social Work (Premier)',
      '🥈 SNDT Women\'s University (~52 km) — Education',
      '🥉 Pillai College, New Panvel — Social Sciences',
      '4. KBP College, Vashi — Social Work, Psychology',
      '5. Saraswati College, Kharghar — Psychology',
      '6. D.Y. Patil University, Navi Mumbai — Social Sciences',
      '7. MGM College — Social Sciences',
      '8. Alibag College, Alibag — Arts (Sociology, Pol Sci)',
      '9. Pen College, Pen — Sociology',
      '10. Mahad College — Arts',
      '11. VES College, Chembur (~45 km) — Psychology',
      '12. Terna College, Nerul — Arts',
      '13. D.Ed / B.Ed Colleges in Alibag, Pen, Panvel',
      '14. Karjat College, Karjat — Arts',
      '15. Nirmala Niketan College of Social Work (~52 km)',
    ],
    'arogya_seva': [
      '🥇 MGM Medical College & Hospital, Kamothe, Navi Mumbai',
      '🥈 D.Y. Patil Medical College, Nerul, Navi Mumbai',
      '🥉 Terna Medical College, Nerul, Navi Mumbai',
      '4. Rajiv Gandhi Medical College, Thane (~35 km)',
      '5. Grant Medical College (J.J. Hospital), Byculla (~52 km)',
      '6. MGM Dental College, Kamothe',
      '7. Dr. D.Y. Patil Ayurved College (BAMS), Nerul',
      '8. Alibag District Civil Hospital — Nursing & Allied Health',
      '9. Khopoli & Karjat Government Medical Resources',
      '10. MGM School of Nursing, Navi Mumbai',
      '11. Pillai College of Pharmacy, New Panvel',
      '12. Navi Mumbai Municipal Corporation — Nursing Training',
      '13. SIES Physiotherapy College, Sion (~45 km)',
      '14. Maharashtra University of Health Sciences (MUHS) — affiliated Panvel',
      '15. Rural Medical College / Ayurveda, Alibag (upcoming)',
    ],
    'krushi_paryavaran': [
      '🥇 DBSKKV College of Fisheries, Dapoli (~100 km — nearest specialized)',
      '🥈 ICT Mumbai — Environmental Engineering (~52 km)',
      '🥉 Pillai College of Engineering — Environmental Engg, Panvel',
      '4. SIES College — Biotechnology, Nerul',
      '5. KBP College, Vashi — Life Sciences, Environment',
      '6. MGM College — Environmental Science',
      '7. Alibag College — Botany, Zoology',
      '8. Mahad College — Life Sciences',
      '9. VJTI — Environmental Engineering (~50 km)',
      '10. D.Y. Patil University — Environmental Science',
      '11. Pen College — Botany, Life Sciences',
      '12. Karjat College — Agriculture & Environment',
      '13. ICT Mumbai — Food Technology (~52 km)',
      '14. Kharghar College — Environmental Studies',
      '15. SNDT College — Food Science (~52 km)',
    ],
    'prashasan_rakshan': [
      '🥇 Government Law College, Churchgate (~52 km) — Law, UPSC/MPSC',
      '🥈 New Law College, Vashi (~25 km)',
      '🥉 Pillai College, Panvel — Political Science, Arts',
      '4. KBP College, Vashi — Commerce, Administration',
      '5. Alibag College — Political Science, History',
      '6. Pen College — Arts & Political Science',
      '7. MGM Institute of Management — Navi Mumbai',
      '8. K.C. Law College, Churchgate (~52 km)',
      '9. NDA, Khadakwasla, Pune (~90 km — for defence aspirants)',
      '10. Sainik School, Satara — competitive entry, residential',
      '11. D.Y. Patil University — Law & Governance, Navi Mumbai',
      '12. MPSC Coaching: Rambhau Mhalgi Prabodhini, Thane (~35 km)',
      '13. Karjat College — Political Science',
      '14. Mahad College — Arts & Civics',
      '15. IBPS/SBI PO Prep — Kharghar & Panvel Tutorials',
    ],
  },

  # ══════════════════════════════════════════
  # PUNE REGION (within 60 km of Pune city)
  # Covers: Pimpri-Chinchwad, Lonavala, Talegaon, Chakan, Alandi, Hadapsar
  # ══════════════════════════════════════════
  'pune': {
    'vigyan_tantra': [
      '🥇 College of Engineering Pune (COEP Technological University), Shivajinagar',
      '🥈 Vishwakarma Institute of Technology (VIT), Bibwewadi',
      '🥉 MIT College of Engineering (MITCOE), Kothrud, Pune',
      '4. Army Institute of Technology (AIT), Dighi Hills, Pune',
      '5. Pune Institute of Computer Technology (PICT), Dhankawadi',
      '6. Symbiosis Institute of Technology (SIT), Lavale, Pune',
      '7. Zeal College of Engineering & Research, Narhe',
      '8. Maharashtra Institute of Technology (MIT), Kothrud',
      '9. Sinhgad College of Engineering, Vadgaon, Pune',
      '10. Dr. D.Y. Patil Institute of Technology, Pimpri',
      '11. Indira College of Engineering & Management, Parandwadi',
      '12. Ajeenkya DY Patil University, Charoli, Pune',
      '13. Modern Education Society\'s College of Engineering, Pune',
      '14. International Institute of Information Technology (I²IT), Hinjewadi',
      '15. JSPM\'s RSCOE (Rajarshi Shahu College of Engineering), Tathawade',
    ],
    'vanijya_udyog': [
      '🥇 Symbiosis College of Arts & Commerce, Senapati Bapat Road — Top Commerce',
      '🥈 Fergusson College (autonomous), Deccan Gymkhana — Commerce',
      '🥉 Brihan Maharashtra College of Commerce (BMCC), Deccan',
      '4. Nowrosjee Wadia College of Arts & Science, Pune — Commerce',
      '5. SP College (Sir Parashurambhau College), Tilak Road',
      '6. Gokhale Institute of Politics & Economics, Deccan — Economics',
      '7. Savitribai Phule Pune University Dept of Commerce',
      '8. Indira College of Commerce & Science, Paud Road',
      '9. ICAI (CA Foundation) — Pune Branches (Camp, Deccan)',
      '10. Modern College of Arts, Science & Commerce, Shivajinagar',
      '11. Abhinav Education Society\'s College, Narhe — Commerce',
      '12. Abasaheb Garware College, Karve Road — Commerce',
      '13. Symbiosis Centre for Management Studies (SCMS), Pune',
      '14. Deccan Education Society\'s Wrangler R.P. Paranjpe College (Tilak Rd)',
      '15. Bharati Vidyapeeth College of Commerce, Katraj',
    ],
    'kala_sahitya': [
      '🥇 Film & Television Institute of India (FTII), Law College Road — Film & TV',
      '🥈 Abhinav Kala Mahavidyalaya (Abhinav Art College), Shivajinagar — Fine Arts',
      '🥉 MIT School of Design, Kothrud — Design & Visual Arts',
      '4. Symbiosis Institute of Media & Communication (SIMC), Lavale',
      '5. Fergusson College — Marathi & English Literature',
      '6. SP College — Arts & Literature',
      '7. Modern College of Arts — Journalism & Mass Comm',
      '8. Gokhale Institute — Economics & Humanities',
      '9. Pune Institute of Fine Arts, Deccan',
      '10. MIT Art, Design & Technology University, Rajbaug',
      '11. Savitribai Phule Pune University — Marathi, Hindi, English Depts',
      '12. Deccan College Post-Graduate Research Institute — Linguistics',
      '13. Indira College — Journalism & Mass Comm',
      '14. Abasaheb Garware College — Mass Comm',
      '15. Sinhgad College of Arts & Commerce — Mass Comm',
    ],
    'samaj_shikshan': [
      '🥇 Tata Institute of Social Sciences (TISS) Pune Campus, Yerwada',
      '🥈 Gokhale Institute of Politics & Economics — Social Sciences',
      '🥉 Fergusson College — Psychology, Sociology, Political Science',
      '4. SP College — Sociology, Political Science',
      '5. SNDT Women\'s University Pune Campus — Education & Social Work',
      '6. Savitribai Phule Pune University — Psychology Dept',
      '7. Symbiosis College of Arts — Sociology, Psychology',
      '8. Modern College — Psychology, Sociology',
      '9. B.Ed Colleges affiliated Pune University (50+ institutions)',
      '10. Abasaheb Garware College — Psychology',
      '11. Brihan Maharashtra College of Commerce — Economics',
      '12. Symbiosis Institute of Health Sciences — Social Health',
      '13. Shrimati Nathibai Damodar Thackersey College, Pune',
      '14. Nowrosjee Wadia College — Sociology, Psychology',
      '15. Jnana Prabodhini Prashala — Education Research, Sadashiv Peth',
    ],
    'arogya_seva': [
      '🥇 B.J. Government Medical College & Sassoon Hospital, Pune — Top Govt Medical',
      '🥈 Armed Forces Medical College (AFMC), Wanowrie, Pune',
      '🥉 D.Y. Patil Medical College, Pimpri',
      '4. Bharati Vidyapeeth Medical College & Hospital, Katraj',
      '5. Deenanath Mangeshkar Hospital Medical School',
      '6. MGM Medical College, Aurangabad (for reference)',
      '7. KEM Hospital Pune — Allied Health',
      '8. College of Ayurveda (BAMS) — Tilak Ayurved College, Pune',
      '9. Pune Institute of Medical Sciences',
      '10. Mahatma Gandhi Vidyamandir Dental College, Panchavati',
      '11. Dr. D.Y. Patil Dental College, Pimpri',
      '12. BVDU Dental College, Katraj',
      '13. Bharati Vidyapeeth Nursing College, Katraj',
      '14. MIT School of Nursing, Kothrud',
      '15. Symbiosis Institute of Health Sciences, Lavale',
    ],
    'krushi_paryavaran': [
      '🥇 Mahatma Phule Krishi Vidyapeeth (MPKV), Rahuri (~90 km — regional HQ)',
      '🥈 College of Agriculture, Pune (MPKV affiliated), Shivajinagar',
      '🥉 COEP — Environmental Engineering, Shivajinagar',
      '4. MIT College — Environmental Engg, Kothrud',
      '5. Fergusson College — Botany, Zoology, Environmental Science',
      '6. SP College — Life Sciences, Botany',
      '7. Modern College — Zoology, Botany, Environmental Sci',
      '8. Nowrosjee Wadia College — Life Sciences',
      '9. Gokhale Institute — Agricultural Economics',
      '10. Symbiosis Institute of Technology — Environmental Engineering',
      '11. National Chemical Laboratory (NCL), Homi Bhabha Road — Research',
      '12. ICAR-Agharkar Research Institute, Pune — Agriculture & Biotech',
      '13. College of Fisheries, Shirgaon (~130 km — nearest fisheries)',
      '14. Abasaheb Garware College — Environmental Science',
      '15. Sinhgad Institutes — Environmental Science, Vadgaon',
    ],
    'prashasan_rakshan': [
      '🥇 NDA (National Defence Academy), Khadakwasla, Pune — Best for Defence',
      '🥈 ILS Law College, Law College Road, Pune — Law & Civil Services',
      '🥉 New Law College, Bharati Vidyapeeth, Pune',
      '4. Symbiosis Law School, Viman Nagar',
      '5. Fergusson College — Political Science, History',
      '6. SP College — Political Science, History',
      '7. YASHADA (Yashwantrao Chavan Academy of Development Administration) — Governance',
      '8. Gokhale Institute — Public Policy & Economics',
      '9. Modern College — Political Science',
      '10. Nowrosjee Wadia College — Political Science',
      '11. MIT School of Government, Pune',
      '12. Indira College of Law, Paud Road',
      '13. Dr. D.Y. Patil Law College, Pimpri',
      '14. MPSC / UPSC Coaching: Aishwarya IAS Academy, Deccan',
      '15. Sainik School, Satara (~90 km) — residential, competitive entry',
    ],
  },
}

def get_colleges_for_location(district_raw: str, interest_group: str) -> list:
    """Return ranked list of 10-15 colleges for a given district and interest group."""
    region = get_mmr_region(district_raw)
    region_data = COLLEGE_DB.get(region, COLLEGE_DB['mumbai'])
    return region_data.get(interest_group, [])


CAREER_MAP = {
    'vigyan_tantra': {
        'stream': 'Science — PCM (भौतिकशास्त्र, रसायनशास्त्र, गणित)',
        'careers': [
            'Mechanical / Civil / Electrical Engineer',
            'Software Developer / Computer Engineer',
            'Data Scientist / AI Engineer',
            'Architect / Urban Planner',
            'Research Scientist / Physicist',
        ],
        'colleges': [],  # populated dynamically from COLLEGE_DB
        'description': (
            'तुम्हाला विज्ञान, गणित आणि तंत्रज्ञानामध्ये विशेष रुची आहे. '
            'अभियांत्रिकी, संगणक विज्ञान आणि संशोधन क्षेत्र तुमच्यासाठी योग्य आहे.'
        ),
    },
    'vanijya_udyog': {
        'stream': 'Commerce — वाणिज्य (लेखा, अर्थशास्त्र, व्यापार)',
        'careers': [
            'Chartered Accountant (CA)',
            'Business Manager / MBA Professional',
            'Stock Analyst / Investment Banker',
            'Startup Founder / Entrepreneur',
            'Marketing & Brand Manager',
        ],
        'colleges': [],
        'description': (
            'तुम्हाला व्यापार, अर्थकारण आणि उद्योग यामध्ये रुची आहे. '
            'वाणिज्य शाखा तुमच्यासाठी सर्वोत्तम — CA, व्यवसाय व उद्योजकता क्षेत्रात भरपूर संधी आहेत.'
        ),
    },
    'kala_sahitya': {
        'stream': 'Arts / Humanities — कला शाखा (साहित्य, कला, माध्यम)',
        'careers': [
            'Journalist / Content Writer / Author',
            'Film Director / Scriptwriter',
            'Graphic Designer / Animator',
            'Musician / Visual Artist / Photographer',
            'Mass Communication / Media Professional',
        ],
        'colleges': [],
        'description': (
            'तुमच्यामध्ये सर्जनशीलता आणि कला-साहित्याची आवड आहे. '
            'माध्यम, लेखन, डिझाईन आणि ललित कला क्षेत्रात उत्तम करिअर घडवू शकता.'
        ),
    },
    'samaj_shikshan': {
        'stream': 'Arts / Humanities — समाजशास्त्र, मानसशास्त्र, शिक्षण',
        'careers': [
            'Teacher / Professor / Principal',
            'Social Worker / NGO Professional',
            'Psychologist / Counsellor',
            'HR Manager / Corporate Trainer',
            'Community Development Officer',
        ],
        'colleges': [],
        'description': (
            'तुम्हाला लोकांशी संवाद साधणे, शिकवणे आणि समाजसेवा करणे आवडते. '
            'शिक्षण, समाजकार्य, मानसशास्त्र आणि HR क्षेत्रात उत्तम भवितव्य आहे.'
        ),
    },
    'arogya_seva': {
        'stream': 'Science — PCB (भौतिकशास्त्र, रसायनशास्त्र, जीवशास्त्र)',
        'careers': [
            'MBBS Doctor / Specialist Physician',
            'Pharmacist / Drug Researcher',
            'Nurse / Physiotherapist',
            'Dentist / Ayurvedic Practitioner (BAMS)',
            'Public Health Officer',
        ],
        'colleges': [],
        'description': (
            'तुम्हाला आरोग्यसेवा आणि माणसांच्या कल्याणाची आवड आहे. '
            'वैद्यकीय क्षेत्र — MBBS, BAMS, Pharmacy, Nursing — तुमच्यासाठी आदर्श आहे.'
        ),
    },
    'krushi_paryavaran': {
        'stream': 'Science PCM/PCB किंवा Vocational / Agriculture',
        'careers': [
            'Agricultural Scientist / Agronomist',
            'Forest Officer / Wildlife Biologist',
            'Environmental Engineer',
            'Veterinary Doctor',
            'Farm Entrepreneur / Agri-Business Manager',
        ],
        'colleges': [],
        'description': (
            'तुम्हाला शेती, निसर्ग आणि पर्यावरणाची आवड आहे. '
            'कृषी विज्ञान, वनशास्त्र आणि पर्यावरण अभियांत्रिकीत उत्तम भवितव्य आहे.'
        ),
    },
    'prashasan_rakshan': {
        'stream': 'Arts / Commerce — स्पर्धा परीक्षा, संरक्षण, प्रशासन',
        'careers': [
            'IAS / IPS Officer (UPSC / MPSC)',
            'Army / Navy / Air Force Officer (NDA)',
            'Police Sub-Inspector / Constable',
            'Bank Officer (IBPS / SBI PO)',
            'Administrative Officer / Clerk',
        ],
        'colleges': [],
        'description': (
            'तुम्हाला नेतृत्व, शिस्त, प्रशासन आणि देशसेवेची आवड आहे. '
            'MPSC/UPSC, NDA, पोलीस सेवा आणि बँकिंग क्षेत्रात उत्तम यश मिळवू शकता.'
        ),
    },
}

# ── Other dimension labels ────────────────────────────────────────────────────

PERSONALITY_TRAITS = ['jigyasa', 'niyojan', 'samvad', 'sahkar', 'sthairya', 'netrutva']
# Chart labels — English only (Matplotlib on Linux servers lacks Devanagari fonts)
# Marathi labels appear in the HTML report via Google Fonts; charts use English only.
PERSONALITY_LABELS = {
    'jigyasa':  'Curiosity',
    'niyojan':  'Organisation',
    'samvad':   'Communication',
    'sahkar':   'Cooperation',
    'sthairya': 'Emotional Stability',
    'netrutva': 'Leadership',
}
# Full bilingual labels used only in HTML report sections (not in matplotlib charts)
PERSONALITY_LABELS_FULL = {
    'jigyasa':  'जिज्ञासा / Curiosity',
    'niyojan':  'नियोजन / Organisation',
    'samvad':   'संवाद / Communication',
    'sahkar':   'सहकार्य / Cooperation',
    'sthairya': 'स्थैर्य / Emotional Stability',
    'netrutva': 'नेतृत्व / Leadership',
}

SKILL_TRAITS = ['logical', 'comm', 'creative', 'digital', 'empathy', 'manual']
SKILL_LABELS = {
    'logical':  'Logical',
    'comm':     'Communication',
    'creative': 'Creativity',
    'digital':  'Digital',
    'empathy':  'People Skills',
    'manual':   'Manual Skill',
}
SKILL_LABELS_FULL = {
    'logical':  'तार्किक विचार / Logical',
    'comm':     'संवाद / Communication',
    'creative': 'सर्जनशीलता / Creativity',
    'digital':  'डिजिटल / Digital',
    'empathy':  'सहानुभूती / People Skills',
    'manual':   'कौशल्य / Manual Skill',
}

SUBJECT_TRAITS = ['math', 'science', 'lang', 'social_sci', 'tech', 'arts']
SUBJECT_LABELS = {
    'math':       'Maths',
    'science':    'Science',
    'lang':       'Languages',
    'social_sci': 'Social Sci',
    'tech':       'Tech',
    'arts':       'Arts & PE',
}
SUBJECT_LABELS_FULL = {
    'math':       'गणित / Maths',
    'science':    'विज्ञान / Science',
    'lang':       'भाषा / Languages',
    'social_sci': 'सामाजिकशास्त्र / Social Sci',
    'tech':       'संगणक / Tech',
    'arts':       'कला / Arts & PE',
}


# ─────────────────────────────────────────────
# SCORING ENGINE
# ─────────────────────────────────────────────

def avg_score(r, keys):
    """Average a list of response keys, ignoring missing, return 0-100%."""
    nums = [int(r[k]) for k in keys if r.get(k)]
    return round((sum(nums) / (len(nums) * 5)) * 100) if nums else 0


def score_submission(data):
    r = data.get('responses', {})

    # Interest group scores — 6 questions each → averaged → %
    interests = {}
    for grp in INTEREST_GROUPS:
        keys = [f'ruchi_{grp}_{i}' for i in range(1, 7)]
        interests[grp] = avg_score(r, keys)

    # Personality — 3 questions each → averaged → %
    personality = {}
    for trait in PERSONALITY_TRAITS:
        keys = [f'p_{trait}_{i}' for i in range(1, 4)]
        personality[trait] = avg_score(r, keys)

    # Skills — 2 questions each → averaged → %
    skills = {}
    for trait in SKILL_TRAITS:
        keys = [f'sk_{trait}_{i}' for i in range(1, 3)]
        skills[trait] = avg_score(r, keys)

    # Subject aptitude — 2 questions each → averaged → %
    subjects = {}
    SUBJECT_KEYS = {
        'math':       ['apt_math_1','apt_math_2'],
        'science':    ['apt_science_1','apt_science_2'],
        'lang':       ['apt_lang_1','apt_lang_2'],
        'social_sci': ['apt_social_1','apt_social_2'],
        'tech':       ['apt_tech_1','apt_tech_2'],
        'arts':       ['apt_arts_1','apt_arts_2'],
    }
    for trait, keys in SUBJECT_KEYS.items():
        subjects[trait] = avg_score(r, keys)

    top_group    = max(interests, key=interests.get)
    district_raw = data.get('student', {}).get('district', 'Mumbai')
    career_match = dict(CAREER_MAP.get(top_group, {
        'stream': 'मार्गदर्शन आवश्यक', 'careers': ['Counselling recommended'],
        'colleges': [], 'description': 'Detailed counselling needed.',
    }))
    # Inject location-specific ranked college list (10-15 colleges within 60-70 km)
    career_match['colleges'] = get_colleges_for_location(district_raw, top_group)
    # Store per-group colleges for all interest groups
    all_group_colleges = {
        grp: get_colleges_for_location(district_raw, grp)
        for grp in INTEREST_GROUPS
    }

    stream_map = {
        'science_pcm': 'Science (PCM)',
        'science_pcb': 'Science (PCB)',
        'commerce':    'Commerce (वाणिज्य)',
        'arts':        'Arts / Humanities (कला)',
        'vocational':  'Vocational / ITI',
        'unsure':      'Undecided — मार्गदर्शन हवे',
    }

    return {
        'interests':            interests,
        'top_interest_group':   top_group,
        'personality':          personality,
        'skills':               skills,
        'subjects':             subjects,
        'career_match':         career_match,
        'all_group_colleges':   all_group_colleges,
        'student_stream_choice': stream_map.get(r.get('stream_choice', ''), r.get('stream_choice', '—')),
        'top_skills':    sorted(skills.items(),   key=lambda x: x[1], reverse=True)[:3],
        'top_subjects':  sorted(subjects.items(), key=lambda x: x[1], reverse=True)[:2],
        'career_fields': r.get('career_fields', []),
        'val_priority':  r.get('val_priority', ''),
        'val_environment': r.get('val_environment', ''),
        'learn_style':   r.get('learn_style', ''),
        'think_style':   r.get('think_style', ''),
        'ai_attitude':   r.get('ai_attitude', ''),
        'main_concern':  r.get('main_concern', ''),
    }


# ─────────────────────────────────────────────
# CHART GENERATORS
# ─────────────────────────────────────────────

def fig_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=130, bbox_inches='tight', facecolor=fig.get_facecolor())
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return img_b64


def chart_interest_radar(interests):
    # English-only labels — Devanagari fonts not available on Linux servers
    labels = [INTEREST_EN[g] for g in INTEREST_GROUPS]
    values = [interests[g]   for g in INTEREST_GROUPS]
    values_plot = values + [values[0]]
    angles = np.linspace(0, 2 * np.pi, len(INTEREST_GROUPS), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(5.5, 5.5), subplot_kw=dict(polar=True), facecolor='#FDF8EF')
    ax.set_facecolor('#FDF8EF')
    ax.plot(angles, values_plot, 'o-', linewidth=2.5, color='#E8671A')
    ax.fill(angles, values_plot, alpha=0.22, color='#E8671A')
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, size=7.5, fontweight='bold', color='#1A2E52')
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], size=7, color='#888')
    ax.grid(color='#ccc', linestyle='--', linewidth=0.5)
    ax.spines['polar'].set_color('#ddd')
    ax.set_title('Career Interest Profile', size=10, fontweight='bold', color='#1A2E52', pad=20)
    return fig_to_base64(fig)


def chart_interest_bars(interests):
    labels = [INTEREST_EN[g]  for g in INTEREST_GROUPS]
    values = [interests[g]    for g in INTEREST_GROUPS]
    colors = [INTEREST_COLOR[g] for g in INTEREST_GROUPS]
    sorted_data = sorted(zip(values, labels, colors), reverse=True)
    sv, sl, sc  = zip(*sorted_data)

    fig, ax = plt.subplots(figsize=(6.5, 4), facecolor='#FDF8EF')
    ax.set_facecolor('#FDF8EF')
    bars = ax.barh(list(reversed(sl)), list(reversed(sv)), color=list(reversed(sc)), height=0.55, edgecolor='none')
    for bar, val in zip(bars, list(reversed(sv))):
        ax.text(min(val + 1.5, 97), bar.get_y() + bar.get_height() / 2,
                f'{val}%', va='center', ha='left', fontsize=9, fontweight='bold', color='#333')
    ax.set_xlim(0, 115)
    ax.set_xlabel('Interest Score (%)', color='#555', fontsize=9)
    ax.set_title('Interest Groups — Ranked', fontsize=11, fontweight='bold', color='#1A2E52', pad=10)
    ax.axvline(x=50, color='#ccc', linestyle='--', linewidth=0.8)
    ax.tick_params(axis='y', labelsize=8.5, colors='#333')
    ax.tick_params(axis='x', labelsize=8,   colors='#888')
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#ddd'); ax.spines['bottom'].set_color('#ddd')
    fig.tight_layout()
    return fig_to_base64(fig)


def chart_personality_bar(personality):
    labels = [PERSONALITY_LABELS[t] for t in PERSONALITY_TRAITS]
    values = [personality[t]        for t in PERSONALITY_TRAITS]
    colors = ['#E8671A', '#2563EB', '#7C3AED', '#16A34A', '#D97706', '#DC2626']
    fig, ax = plt.subplots(figsize=(6.5, 3.8), facecolor='#FDF8EF')
    ax.set_facecolor('#FDF8EF')
    bars = ax.barh(labels, values, color=colors, height=0.55, edgecolor='none')
    for bar, val in zip(bars, values):
        ax.text(min(val + 2, 97), bar.get_y() + bar.get_height() / 2,
                f'{val}%', va='center', ha='left', fontsize=9, color='#333', fontweight='bold')
    ax.set_xlim(0, 105)
    ax.set_xlabel('Score (%)', color='#555', fontsize=9)
    ax.set_title('Personality Profile', fontsize=11, fontweight='bold', color='#1A2E52', pad=10)
    ax.axvline(x=50, color='#ccc', linestyle='--', linewidth=0.8)
    ax.tick_params(axis='y', labelsize=9, colors='#333')
    ax.tick_params(axis='x', labelsize=8, colors='#888')
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#ddd'); ax.spines['bottom'].set_color('#ddd')
    fig.tight_layout()
    return fig_to_base64(fig)


def chart_skills_bubble(skills):
    labels = [SKILL_LABELS[t] for t in SKILL_TRAITS]
    values = [skills[t]  for t in SKILL_TRAITS]
    x = [1, 2, 3, 1, 2, 3]; y = [2, 2, 2, 1, 1, 1]
    colors = ['#E8671A', '#2563EB', '#7C3AED', '#16A34A', '#D97706', '#DC2626']
    fig, ax = plt.subplots(figsize=(6.5, 3.5), facecolor='#FDF8EF')
    ax.set_facecolor('#FDF8EF')
    for i in range(len(labels)):
        ax.scatter(x[i], y[i], s=max(values[i] * 25, 200), color=colors[i], alpha=0.75, edgecolors='white', linewidths=1.5)
        ax.text(x[i], y[i], f'{values[i]}%', ha='center', va='center', fontsize=9, fontweight='bold', color='white')
        ax.text(x[i], y[i] - 0.28, labels[i], ha='center', va='top', fontsize=7.5, color='#333')
    ax.set_xlim(0.5, 3.5); ax.set_ylim(0.5, 2.5); ax.axis('off')
    ax.set_title('Skills & Abilities', fontsize=11, fontweight='bold', color='#1A2E52', pad=8)
    fig.tight_layout()
    return fig_to_base64(fig)


def chart_subjects(subjects):
    labels     = [SUBJECT_LABELS[t] for t in SUBJECT_TRAITS]
    values     = [subjects[t]  for t in SUBJECT_TRAITS]
    colors_bar = ['#2563EB' if v >= 60 else '#FCA5A5' if v < 40 else '#FCD34D' for v in values]
    fig, ax = plt.subplots(figsize=(6.5, 3.5), facecolor='#FDF8EF')
    ax.set_facecolor('#FDF8EF')
    bars = ax.bar(labels, values, color=colors_bar, edgecolor='none', width=0.55)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 1.5, f'{val}%',
                ha='center', fontsize=8.5, fontweight='bold', color='#333')
    ax.set_ylim(0, 115)
    ax.set_ylabel('Aptitude (%)', fontsize=9, color='#555')
    ax.set_title('Subject Aptitude', fontsize=11, fontweight='bold', color='#1A2E52', pad=10)
    ax.tick_params(axis='x', labelsize=7.5, colors='#333', rotation=15)
    ax.tick_params(axis='y', labelsize=8,   colors='#888')
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#ddd'); ax.spines['bottom'].set_color('#ddd')
    ax.legend(handles=[
        mpatches.Patch(color='#2563EB', label='Strong (≥60%)'),
        mpatches.Patch(color='#FCD34D', label='Average (40-59%)'),
        mpatches.Patch(color='#FCA5A5', label='Needs work (<40%)')
    ], fontsize=7.5, loc='upper right', framealpha=0.7)
    fig.tight_layout()
    return fig_to_base64(fig)


def generate_charts(scored):
    return {
        'interest_radar': chart_interest_radar(scored['interests']),
        'interest_bars':  chart_interest_bars(scored['interests']),
        'personality':    chart_personality_bar(scored['personality']),
        'skills':         chart_skills_bubble(scored['skills']),
        'subjects':       chart_subjects(scored['subjects']),
    }


# ─────────────────────────────────────────────
# DATA HELPERS
# ─────────────────────────────────────────────

def save_submission(ref_id, data, scored):
    record = {
        'ref_id': ref_id,
        'submitted_at': data.get('timestamp', datetime.datetime.now().isoformat()),
        'student': data.get('student', {}),
        'raw_responses': data.get('responses', {}),
        'open_reflection': data.get('openReflection', ''),
        'scored': scored,
    }
    with open(RESULTS_DIR / f"{ref_id}.json", 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)


def load_all_results():
    results = []
    for f in sorted(RESULTS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            with open(f, encoding='utf-8') as fp:
                results.append(json.load(fp))
        except Exception:
            pass
    return results


def load_result(ref_id):
    path = RESULTS_DIR / f"{ref_id}.json"
    if not path.exists():
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)


# ─────────────────────────────────────────────
# HTML REPORT GENERATOR
# ─────────────────────────────────────────────

def generate_report_html(record, charts):
    s   = record['student']
    sc  = record['scored']
    cm  = sc['career_match']
    top = sc.get('top_interest_group', '')

    strengths    = ', '.join([SKILL_LABELS_FULL[k]   for k, v in sc['top_skills']])
    subjects_str = ', '.join([SUBJECT_LABELS_FULL[k] for k, v in sc['top_subjects']])

    val_map  = {'high_income':'उच्च उत्पन्न / High Income','social_impact':'समाजसेवा / Social Impact',
                'creativity':'सर्जनशीलता / Creativity','stability':'स्थिरता / Stability',
                'independence':'स्वातंत्र्य / Independence','prestige':'प्रतिष्ठा / Prestige'}
    env_map  = {'office':'ऑफिस / Corporate','outdoor':'मैदानी / Outdoor',
                'creative_studio':'स्टुडिओ / Creative Lab','hospital_school':'रुग्णालय/शाळा',
                'home_remote':'घरून / Remote','govt_uniform':'सरकारी / Govt Uniform'}
    learn_map= {'visual':'दृश्य / Visual','auditory':'श्रवण / Auditory',
                'reading':'वाचन/लेखन / Reading-Writing','kinesthetic':'क्रियाशील / Kinesthetic'}
    think_map= {'analytical':'विश्लेषक / Analytical','creative':'सर्जनशील / Creative',
                'practical':'व्यावहारिक / Practical','collaborative':'सहयोगी / Collaborative'}
    concern_map={'financial':'शिक्षणाचा खर्च / Financial constraints',
                 'marks':'परीक्षेचे गुण / Exam performance',
                 'unclear':'करिअर अनिश्चितता / Direction unclear',
                 'competition':'स्पर्धा / Competition','family_pressure':'कौटुंबिक दबाव / Family pressure',
                 'no_concern':'स्पष्ट योजना / Has a clear plan'}

    interest_rows = ''.join([
        f'<tr><td style="padding:6px 4px;font-size:12px">'
        f'<span style="color:{INTEREST_COLOR[g]};font-weight:700">{INTEREST_MR[g]}</span>'
        f'<br><span style="color:#888;font-size:10px">{INTEREST_EN[g]}</span></td>'
        f'<td style="padding:6px 4px"><div style="background:#eee;border-radius:4px;height:13px;width:100%">'
        f'<div style="background:{INTEREST_COLOR[g]};width:{v}%;height:13px;border-radius:4px"></div></div></td>'
        f'<td style="text-align:right;font-weight:700;color:{INTEREST_COLOR[g]};padding:6px 4px">{v}%</td></tr>'
        for g, v in sorted(sc['interests'].items(), key=lambda x: x[1], reverse=True)
    ])

    career_list  = ''.join([f'<li>{c}</li>'              for c in cm.get('careers',[])])
    district_raw = s.get('district', 'Mumbai')
    colleges_for_report = cm.get('colleges', []) or get_colleges_for_location(district_raw, top)
    college_list = ''.join([
        f'<div style="padding:6px 10px;border-bottom:1px solid #F0EBE0;font-size:12.5px;color:#1A2E52;line-height:1.5">{c}</div>'
        for c in colleges_for_report
    ])
    fields_list  = ''.join([f'<span class="tag">{f.replace("_"," ").title()}</span>'
                            for f in sc.get('career_fields',[])])
    submitted_dt = record.get('submitted_at','')[:10]
    top_color    = INTEREST_COLOR.get(top, '#E8671A')

    return f"""<!DOCTYPE html>
<html lang="mr">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kalchachani Report — {s.get('name','Student')}</title>
<link href="https://fonts.googleapis.com/css2?family=Tiro+Devanagari+Marathi&family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'DM Sans',sans-serif;background:#f5f0e8;color:#1a1a2e;font-size:14px}}
.page{{max-width:900px;margin:0 auto;background:white}}
.header{{background:linear-gradient(135deg,#0E1C35,#1A2E52);color:white;padding:28px 40px}}
.mr-title{{font-family:'Tiro Devanagari Marathi',serif;font-size:34px;color:#D4A017;margin-bottom:4px}}
.en-title{{font-family:'Playfair Display',serif;font-size:18px;color:rgba(255,255,255,0.85);margin-bottom:4px}}
.subtitle{{font-size:11px;color:rgba(255,255,255,0.5);letter-spacing:0.8px;text-transform:uppercase}}
.student-bar{{background:#FFF3E8;border-bottom:3px solid #E8671A;padding:14px 40px;display:flex;gap:24px;flex-wrap:wrap;align-items:center}}
.sf{{display:flex;flex-direction:column}}
.sf label{{font-size:9px;color:#888;text-transform:uppercase;letter-spacing:0.5px}}
.sf span{{font-weight:600;font-size:13px;color:#1A2E52}}
.ref-chip{{margin-left:auto;background:#1A2E52;color:white;padding:5px 12px;border-radius:20px;font-size:11px;font-weight:600}}
.body{{padding:28px 40px}}
.section{{margin-bottom:32px}}
.sec-title{{font-family:'Playfair Display',serif;font-size:16px;font-weight:600;color:#1A2E52;border-left:4px solid #E8671A;padding-left:12px;margin-bottom:14px}}
.two-col{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
img.chart{{width:100%;border-radius:10px;border:1px solid #eee}}
.career-box{{background:linear-gradient(135deg,#FFF3E8,#FFF8F0);border:2px solid #E8671A;border-radius:14px;padding:22px;margin-bottom:16px}}
.career-box h2{{font-family:'Playfair Display',serif;font-size:17px;color:#1A2E52;margin-bottom:8px}}
.badge{{display:inline-block;background:#E8671A;color:white;padding:3px 12px;border-radius:20px;font-size:11px;font-weight:600;margin-bottom:10px}}
.top-badge{{display:inline-block;background:{top_color};color:white;padding:3px 12px;border-radius:20px;font-size:11px;font-weight:600;margin-bottom:8px}}
.career-box p{{font-family:'Tiro Devanagari Marathi',serif;color:#444;line-height:1.75;margin-bottom:12px;font-size:14px}}
.career-box ul{{list-style:none;padding:0}}
.career-box ul li{{padding:5px 0;color:#1A2E52;font-weight:500;border-bottom:1px solid #f0e8d8;font-size:13px}}
.career-box ul li::before{{content:"✦ ";color:#E8671A;font-size:10px}}
.tag{{display:inline-block;background:#EEF4FF;color:#3056A0;border:1px solid #C7DAFF;padding:2px 9px;border-radius:12px;font-size:11px;margin:2px}}
.info-grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.info-card{{background:#F8F6F0;border-radius:8px;padding:11px 13px;border-left:3px solid #E8671A}}
.info-card label{{font-size:9px;color:#888;text-transform:uppercase;letter-spacing:0.5px;display:block;margin-bottom:3px}}
.info-card span{{font-weight:600;font-size:12px;color:#1A2E52}}
.interest-table{{width:100%;border-collapse:collapse}}
.reflection-box{{background:#F8F6F0;border-radius:10px;padding:14px;border-left:3px solid #7C3AED;font-style:italic;color:#444;line-height:1.7}}
.footer{{background:#1A2E52;color:rgba(255,255,255,0.45);text-align:center;padding:14px;font-size:11px}}
.concern-box{{background:#FFF0F0;border:1px solid #FCA5A5;border-radius:8px;padding:11px 14px;font-size:13px;color:#7f1d1d}}
.concern-box strong{{display:block;margin-bottom:3px;color:#dc2626}}
@media print{{body{{background:white}}.page{{max-width:100%}}}}
</style>
</head>
<body>
<div class="page">
  <div class="header">
    <div class="mr-title">कलचाचणी</div>
    <div class="en-title">Kalchachani — Career Aptitude Assessment Report</div>
    <div class="subtitle">Confidential · For School Counsellor Use Only</div>
  </div>

  <div class="student-bar">
    <div class="sf"><label>विद्यार्थ्याचे नाव</label><span>{s.get('name','—')}</span></div>
    <div class="sf"><label>शाळा / School</label><span>{s.get('school','—')}</span></div>
    <div class="sf"><label>जिल्हा / District</label><span>{s.get('district','—')}</span></div>
    <div class="sf"><label>माध्यम / Medium</label><span>{s.get('medium','—')}</span></div>
    <div class="sf"><label>दिनांक / Date</label><span>{submitted_dt}</span></div>
    <div class="ref-chip">Ref: {record['ref_id'][:8].upper()}</div>
  </div>

  <div class="body">
    <div class="section">
      <div class="sec-title">करिअर शिफारस / Career Recommendation</div>
      <div class="career-box">
        <div class="top-badge">{INTEREST_MR.get(top,'—')} — {INTEREST_EN.get(top,'')}</div>
        <h2>शिफारस: <span class="badge">{cm.get('stream','—')}</span></h2>
        <p>{cm.get('description','')}</p>
        <div style="margin-bottom:8px"><strong style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.5px">Top Career Paths</strong></div>
        <ul>{career_list}</ul>
        <div style="margin-top:12px"><strong style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.5px">📍 Colleges Near {s.get('district','Your Location')} (≤60-70 km) — Best to Good</strong><div style="margin-top:6px;border:1px solid #F0EBE0;border-radius:8px;overflow:hidden">{college_list}</div></div>
      </div>
      <div style="font-size:12px;color:#888;padding-left:4px">★ विद्यार्थ्याची स्वतःची पसंती: <strong>{sc.get('student_stream_choice','—')}</strong></div>
    </div>

    <div class="section">
      <div class="sec-title">रुची प्रोफाइल / Career Interest Profile — 7 रुची गट</div>
      <div class="two-col">
        <img class="chart" src="data:image/png;base64,{charts['interest_radar']}" alt="Interest Radar">
        <img class="chart" src="data:image/png;base64,{charts['interest_bars']}"  alt="Interest Bars">
      </div>
      <div style="margin-top:14px"><table class="interest-table">{interest_rows}</table></div>
    </div>

    <div class="section">
      <div class="sec-title">व्यक्तिमत्त्व / Personality Profile</div>
      <img class="chart" src="data:image/png;base64,{charts['personality']}" alt="Personality">
    </div>

    <div class="section">
      <div class="sec-title">कौशल्ये आणि विषय क्षमता / Skills & Subject Aptitude</div>
      <div class="two-col">
        <img class="chart" src="data:image/png;base64,{charts['skills']}"   alt="Skills">
        <img class="chart" src="data:image/png;base64,{charts['subjects']}" alt="Subjects">
      </div>
    </div>

    <div class="section">
      <div class="sec-title">वैयक्तिक सारांश / Personal Profile Summary</div>
      <div class="info-grid">
        <div class="info-card"><label>कौशल्य सामर्थ्य / Top Skills</label><span>{strengths}</span></div>
        <div class="info-card"><label>मजबूत विषय / Strong Subjects</label><span>{subjects_str}</span></div>
        <div class="info-card"><label>करिअर मूल्य / Career Value</label><span>{val_map.get(sc.get('val_priority',''),'—')}</span></div>
        <div class="info-card"><label>कामाचे वातावरण / Work Environment</label><span>{env_map.get(sc.get('val_environment',''),'—')}</span></div>
        <div class="info-card"><label>शिकण्याची पद्धत / Learning Style</label><span>{learn_map.get(sc.get('learn_style',''),'—')}</span></div>
        <div class="info-card"><label>विचार शैली / Thinking Style</label><span>{think_map.get(sc.get('think_style',''),'—')}</span></div>
      </div>
      <div style="margin-top:12px"><strong style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.5px">करिअर क्षेत्रे / Career Fields of Interest</strong><div style="margin-top:5px">{fields_list or '—'}</div></div>
    </div>

    <div class="section">
      <div class="sec-title">समुपदेशकांसाठी नोंद / Counsellor's Note</div>
      <div class="concern-box">
        <strong>विद्यार्थ्याची मुख्य काळजी / Main Concern:</strong>
        {concern_map.get(sc.get('main_concern',''),'—')}
      </div>
      {f'<div class="reflection-box" style="margin-top:12px"><strong style="font-style:normal;font-size:10px;color:#7C3AED;text-transform:uppercase;letter-spacing:0.5px;display:block;margin-bottom:5px">विद्यार्थ्याचे स्वतःचे विचार</strong>"{record.get("open_reflection","")}"</div>' if record.get('open_reflection') else ''}
      <div style="margin-top:14px;padding:13px;background:#F0FFF4;border-radius:8px;border-left:3px solid #16A34A;font-size:13px;color:#14532d;line-height:1.7">
        <strong>Counsellor Action Points:</strong><br>
        1. शीर्ष रुची गट: <strong>{INTEREST_MR.get(top,'—')} ({INTEREST_EN.get(top,'')})</strong> — या क्षेत्रातील करिअर पर्यायांची चर्चा करा.<br>
        2. शिफारस केलेली शाखा: <strong>{cm.get('stream','—')}</strong> (विद्यार्थ्याची पसंती: {sc.get('student_stream_choice','—')}).<br>
        3. मुख्य काळजी: <em>{concern_map.get(sc.get('main_concern',''),'—')}</em><br>
        4. कौशल्य सामर्थ्य: {strengths}.
      </div>
    </div>
  </div>

  <div class="footer">कलचाचणी 2025-26 · Career Aptitude Assessment · Report ID: {record['ref_id']}</div>
</div>
</body></html>"""


# ─────────────────────────────────────────────
# STUDENT-FACING REPORT (public, no password)
# ─────────────────────────────────────────────

def generate_student_report_html(record, charts):
    s   = record['student']
    sc  = record['scored']
    cm  = sc['career_match']
    top = sc.get('top_interest_group', '')
    top_color = INTEREST_COLOR.get(top, '#E8671A')

    career_list  = ''.join([f'<li>{c}</li>' for c in cm.get('careers', [])])
    district_raw_s = s.get('district', 'Mumbai')
    colleges_for_student = cm.get('colleges', []) or get_colleges_for_location(district_raw_s, top)
    college_list = ''.join([
        f'<div style="padding:8px 12px;border-bottom:1px solid #F5EFE6;font-size:13px;color:#1A2E52;line-height:1.6">{c}</div>'
        for c in colleges_for_student
    ])
    submitted_dt = record.get('submitted_at', '')[:10]
    strengths    = ', '.join([SKILL_LABELS_FULL[k] for k, v in sc['top_skills']])

    interest_rows = ''.join([
        f'<tr>'
        f'<td style="padding:7px 4px;font-size:13px">'
        f'<span style="color:{INTEREST_COLOR[g]};font-weight:700">{INTEREST_MR[g]}</span>'
        f'<br><span style="color:#888;font-size:11px">{INTEREST_EN[g]}</span></td>'
        f'<td style="padding:7px 4px"><div style="background:#eee;border-radius:4px;height:14px;width:100%">'
        f'<div style="background:{INTEREST_COLOR[g]};width:{v}%;height:14px;border-radius:4px"></div></div></td>'
        f'<td style="text-align:right;font-weight:700;color:{INTEREST_COLOR[g]};padding:7px 4px;font-size:14px">{v}%</td>'
        f'</tr>'
        for g, v in sorted(sc['interests'].items(), key=lambda x: x[1], reverse=True)
    ])

    val_map = {
        'high_income':'उच्च उत्पन्न / High Income','social_impact':'समाजसेवा / Social Impact',
        'creativity':'सर्जनशीलता / Creativity','stability':'स्थिरता / Stability',
        'independence':'स्वातंत्र्य / Independence','prestige':'प्रतिष्ठा / Prestige'
    }
    learn_map = {
        'visual':'दृश्य / Visual','auditory':'श्रवण / Auditory',
        'reading':'वाचन/लेखन / Reading-Writing','kinesthetic':'क्रियाशील / Kinesthetic'
    }

    return f"""<!DOCTYPE html>
<html lang="mr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>माझा कलचाचणी अहवाल — {s.get('name','')}</title>
<link href="https://fonts.googleapis.com/css2?family=Tiro+Devanagari+Marathi&family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'DM Sans',sans-serif;background:#f5f0e8;color:#1a1a2e;font-size:15px}}
.page{{max-width:860px;margin:0 auto;background:white;border-radius:0 0 16px 16px;box-shadow:0 4px 32px rgba(0,0,0,0.10)}}
.header{{background:linear-gradient(135deg,#0E1C35,#1A2E52);color:white;padding:32px 36px 28px;border-radius:0}}
.mr-title{{font-family:'Tiro Devanagari Marathi',serif;font-size:42px;color:#D4A017;margin-bottom:6px}}
.en-title{{font-family:'Playfair Display',serif;font-size:18px;color:rgba(255,255,255,0.8);margin-bottom:4px}}
.subtitle{{font-size:12px;color:rgba(255,255,255,0.45);letter-spacing:0.8px;text-transform:uppercase}}
.student-bar{{background:#FFF3E8;border-bottom:3px solid #E8671A;padding:14px 36px;display:flex;gap:22px;flex-wrap:wrap;align-items:center}}
.sf{{display:flex;flex-direction:column}}
.sf label{{font-size:9px;color:#888;text-transform:uppercase;letter-spacing:0.5px}}
.sf span{{font-weight:600;font-size:13px;color:#1A2E52}}
.ref-chip{{margin-left:auto;background:#1A2E52;color:white;padding:5px 12px;border-radius:20px;font-size:11px;font-weight:600}}
.body{{padding:30px 36px}}
.section{{margin-bottom:32px}}
.sec-title{{font-family:'Playfair Display',serif;font-size:17px;font-weight:600;color:#1A2E52;border-left:4px solid #E8671A;padding-left:12px;margin-bottom:16px}}
.career-box{{background:linear-gradient(135deg,#FFF3E8,#FFF8F0);border:2px solid #E8671A;border-radius:14px;padding:24px;margin-bottom:14px}}
.career-box h2{{font-family:'Playfair Display',serif;font-size:19px;color:#1A2E52;margin-bottom:10px}}
.top-badge{{display:inline-block;background:{top_color};color:white;padding:4px 14px;border-radius:20px;font-size:12px;font-weight:600;margin-bottom:10px}}
.stream-badge{{display:inline-block;background:#E8671A;color:white;padding:3px 14px;border-radius:20px;font-size:12px;font-weight:600;margin-bottom:12px}}
.career-box p{{font-family:'Tiro Devanagari Marathi',serif;color:#444;line-height:1.8;margin-bottom:14px;font-size:14px}}
.career-box ul{{list-style:none;padding:0}}
.career-box ul li{{padding:7px 0;color:#1A2E52;font-weight:500;border-bottom:1px solid #f0e8d8;font-size:14px}}
.career-box ul li::before{{content:"✦ ";color:#E8671A;font-size:10px}}
.tag{{display:inline-block;background:#EEF4FF;color:#3056A0;border:1px solid #C7DAFF;padding:3px 10px;border-radius:12px;font-size:12px;margin:3px}}
.two-col{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
img.chart{{width:100%;border-radius:10px;border:1px solid #eee}}
.interest-table{{width:100%;border-collapse:collapse}}
.info-grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.info-card{{background:#F8F6F0;border-radius:10px;padding:12px 14px;border-left:3px solid #E8671A}}
.info-card label{{font-size:9px;color:#888;text-transform:uppercase;letter-spacing:0.5px;display:block;margin-bottom:4px}}
.info-card span{{font-weight:600;font-size:13px;color:#1A2E52}}
.next-box{{background:linear-gradient(135deg,#F0FFF4,#E8FFF0);border:1.5px solid #16A34A;border-radius:12px;padding:20px 24px;margin-top:8px}}
.next-box h3{{font-family:'Playfair Display',serif;font-size:16px;color:#14532d;margin-bottom:12px}}
.next-box ul{{list-style:none;padding:0}}
.next-box ul li{{padding:6px 0;color:#14532d;font-size:14px;border-bottom:1px solid #bbf7d0}}
.next-box ul li::before{{content:"→ ";color:#16A34A;font-weight:700}}
.download-btn{{display:inline-block;background:linear-gradient(135deg,#E8671A,#C4511A);color:white;padding:13px 32px;border-radius:50px;font-size:15px;font-weight:600;text-decoration:none;box-shadow:0 4px 16px rgba(232,103,26,0.35);font-family:'DM Sans',sans-serif}}
.download-btn:hover{{opacity:0.92}}
.footer{{background:#1A2E52;color:rgba(255,255,255,0.4);text-align:center;padding:14px;font-size:11px;border-radius:0 0 16px 16px}}
@media(max-width:600px){{
  .header{{padding:22px 18px 20px}}
  .mr-title{{font-size:32px}}
  .student-bar{{padding:12px 16px;gap:14px}}
  .body{{padding:20px 16px}}
  .two-col{{grid-template-columns:1fr}}
  .info-grid{{grid-template-columns:1fr}}
  .ref-chip{{margin-left:0;margin-top:4px}}
  .download-btn{{padding:12px 24px;font-size:14px}}
}}
@media print{{body{{background:white}}.page{{box-shadow:none;border-radius:0}}}}
</style>
</head>
<body>
<div class="page">

  <div class="header">
    <div class="mr-title">कलचाचणी</div>
    <div class="en-title">Kalchachani — माझा करिअर अहवाल / My Career Report</div>
    <div class="subtitle">Career Aptitude Assessment · 2025-26</div>
  </div>

  <div class="student-bar">
    <div class="sf"><label>नाव / Name</label><span>{s.get('name','—')}</span></div>
    <div class="sf"><label>शाळा / School</label><span>{s.get('school','—')}</span></div>
    <div class="sf"><label>जिल्हा / District</label><span>{s.get('district','—')}</span></div>
    <div class="sf"><label>दिनांक / Date</label><span>{submitted_dt}</span></div>
    <div class="ref-chip">Ref: {record['ref_id'][:8].upper()}</div>
  </div>

  <div class="body">

    <!-- CAREER RECOMMENDATION -->
    <div class="section">
      <div class="sec-title">🎯 तुमच्यासाठी शिफारस / Your Career Recommendation</div>
      <div class="career-box">
        <div class="top-badge">{INTEREST_MR.get(top,'—')} — {INTEREST_EN.get(top,'')}</div>
        <h2>शिफारस केलेली शाखा:</h2>
        <div class="stream-badge">{cm.get('stream','—')}</div>
        <p>{cm.get('description','')}</p>
        <div style="margin-bottom:10px"><strong style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.5px">Top Career Paths तुमच्यासाठी</strong></div>
        <ul>{career_list}</ul>
        <div style="margin-top:14px">
          <strong style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.5px">📍 तुमच्या जवळचे महाविद्यालय / Colleges Near {s.get('district','Your Location')} (≤60-70 km) — सर्वोत्तम क्रमाने</strong>
          <div style="margin-top:8px;border:1px solid #F0EBE0;border-radius:10px;overflow:hidden;background:#FFFDF9">{college_list or '<div style="padding:12px;color:#888;font-size:13px">Location-specific list not available.</div>'}</div>
        </div>
      </div>
      <p style="font-size:12px;color:#999;padding-left:4px">★ तुमची स्वतःची पसंती: <strong style="color:#1A2E52">{sc.get('student_stream_choice','—')}</strong></p>
    </div>

    <!-- INTEREST PROFILE -->
    <div class="section">
      <div class="sec-title">📊 तुमचा रुची प्रोफाइल / Your Interest Profile</div>
      <div class="two-col">
        <img class="chart" src="data:image/png;base64,{charts['interest_radar']}" alt="Interest Radar">
        <img class="chart" src="data:image/png;base64,{charts['interest_bars']}"  alt="Interest Bars">
      </div>
      <div style="margin-top:16px">
        <table class="interest-table">{interest_rows}</table>
      </div>
    </div>

    <!-- PERSONALITY -->
    <div class="section">
      <div class="sec-title">🧠 व्यक्तिमत्त्व / Personality Profile</div>
      <img class="chart" src="data:image/png;base64,{charts['personality']}" alt="Personality">
    </div>

    <!-- SKILLS & SUBJECTS -->
    <div class="section">
      <div class="sec-title">💡 कौशल्ये आणि विषय / Skills &amp; Subject Aptitude</div>
      <div class="two-col">
        <img class="chart" src="data:image/png;base64,{charts['skills']}"   alt="Skills">
        <img class="chart" src="data:image/png;base64,{charts['subjects']}" alt="Subjects">
      </div>
    </div>

    <!-- PERSONAL SUMMARY -->
    <div class="section">
      <div class="sec-title">📋 तुमचा सारांश / Your Personal Summary</div>
      <div class="info-grid">
        <div class="info-card"><label>तुमची सर्वोत्तम कौशल्ये / Top Skills</label><span>{strengths}</span></div>
        <div class="info-card"><label>करिअर मूल्य / Career Value</label><span>{val_map.get(sc.get('val_priority',''),'—')}</span></div>
        <div class="info-card"><label>शिकण्याची पद्धत / Learning Style</label><span>{learn_map.get(sc.get('learn_style',''),'—')}</span></div>
        <div class="info-card"><label>तुमची शाखा पसंती / Your Stream Choice</label><span>{sc.get('student_stream_choice','—')}</span></div>
      </div>
    </div>

    <!-- NEXT STEPS -->
    <div class="section">
      <div class="sec-title">🚀 पुढे काय करायचे? / What To Do Next</div>
      <div class="next-box">
        <h3>तुमच्यासाठी सुचवलेली पुढील पावले</h3>
        <ul>
          <li>तुमच्या शिक्षक किंवा समुपदेशकाशी हा अहवाल शेअर करा — ते तुम्हाला अधिक मार्गदर्शन करतील.</li>
          <li>शिफारस केलेल्या शाखेबद्दल अधिक माहिती मिळवा: <strong>{cm.get('stream','—')}</strong></li>
          <li>वरील महाविद्यालयांच्या वेबसाइट पहा आणि प्रवेश प्रक्रिया समजून घ्या.</li>
          <li>तुमच्या आवडीच्या क्षेत्रातील एखाद्या व्यावसायिकाशी किंवा विद्यार्थ्याशी बोला.</li>
          <li>हा अहवाल डाउनलोड करा आणि तुमच्या पालकांना दाखवा.</li>
        </ul>
      </div>
    </div>

    <!-- DOWNLOAD -->
    <div style="text-align:center;padding:16px 0 8px">
      <a href="/result/{record['ref_id']}/download" class="download-btn">⬇ अहवाल डाउनलोड करा / Download My Report</a>
      <p style="margin-top:12px;font-size:12px;color:#999">तुमचा Reference ID: <strong style="color:#E8671A;font-family:monospace">{record['ref_id'][:8].upper()}</strong> — हा लिहून ठेवा</p>
    </div>

  </div>

  <div class="footer">कलचाचणी 2025-26 · Career Aptitude Assessment · Report ID: {record['ref_id']}</div>
</div>
</body>
</html>"""


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def index():
    return redirect('/test')

@app.route('/test')
def test_page():
    return render_template('kalchachani_test.html')

@app.route('/api/submit', methods=['POST'])
def api_submit():
    try:
        data   = request.get_json(force=True)
        ref_id = str(uuid.uuid4())
        scored = score_submission(data)
        save_submission(ref_id, data, scored)
        return jsonify({'success': True, 'ref_id': ref_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin')
def admin_dashboard():
    pw = request.args.get('pw', '')
    if pw != ADMIN_PASSWORD:
        return '''<html><body style="font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;background:#f5f0e8">
        <div style="background:white;padding:40px;border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,0.1);text-align:center">
        <h2 style="color:#1A2E52;margin-bottom:20px">Admin Login — कलचाचणी</h2>
        <form method="GET"><input name="pw" type="password" placeholder="Password"
        style="padding:10px 16px;border:1.5px solid #ddd;border-radius:8px;font-size:14px;width:220px">
        <br><br><button type="submit" style="background:#E8671A;color:white;border:none;padding:10px 28px;border-radius:8px;font-size:14px;cursor:pointer">Login</button>
        </form></div></body></html>''', 200

    results = load_all_results()
    rows = ''
    for r in results:
        s   = r.get('student', {})
        sc  = r.get('scored',  {})
        top = sc.get('top_interest_group', '')
        cm  = sc.get('career_match', {})
        top_str = f"{INTEREST_MR.get(top,'—')} ({sc.get('interests',{}).get(top,0)}%)"
        rid = r.get('ref_id', '')
        dt  = r.get('submitted_at', '')[:16].replace('T', ' ')
        rows += f"""<tr>
          <td style="font-weight:600">{s.get('name','—')}</td>
          <td>{s.get('school','—')}</td>
          <td>{s.get('district','—')}</td>
          <td>{dt}</td>
          <td><span style="background:#FFF3E8;color:#E8671A;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600">{cm.get('stream','—')}</span></td>
          <td style="font-size:12px;color:#555">{top_str}</td>
          <td>
            <a href="/report/{rid}?pw={pw}" target="_blank" style="background:#E8671A;color:white;padding:5px 12px;border-radius:6px;text-decoration:none;font-size:12px;font-weight:600">View</a>
            &nbsp;
            <a href="/report/{rid}/download?pw={pw}" style="background:#1A2E52;color:white;padding:5px 12px;border-radius:6px;text-decoration:none;font-size:12px;font-weight:600">Download</a>
          </td></tr>"""

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Kalchachani Admin</title>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    <style>*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:'DM Sans',sans-serif;background:#F5F0E8}}
    .top-bar{{background:linear-gradient(135deg,#0E1C35,#1A2E52);color:white;padding:18px 40px;display:flex;align-items:center;justify-content:space-between}}
    .top-bar h1{{font-size:18px;font-weight:600}}.top-bar span{{font-size:12px;color:rgba(255,255,255,0.6)}}
    .stat-bar{{background:white;border-bottom:1px solid #e0d5c5;padding:12px 40px;display:flex;gap:28px}}
    .stat{{display:flex;flex-direction:column}}.stat label{{font-size:9px;color:#888;text-transform:uppercase;letter-spacing:0.5px}}
    .stat span{{font-size:20px;font-weight:600;color:#E8671A}}.container{{padding:20px 28px}}
    table{{width:100%;border-collapse:collapse;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.06)}}
    thead{{background:#1A2E52;color:white}}th{{padding:11px 13px;text-align:left;font-size:11px;font-weight:500;letter-spacing:0.3px}}
    td{{padding:11px 13px;border-bottom:1px solid #f0ebe0;font-size:12px;vertical-align:middle}}
    tr:last-child td{{border-bottom:none}}tr:hover td{{background:#FFF8F0}}
    .empty{{text-align:center;padding:60px;color:#888}}</style></head><body>
    <div class="top-bar"><h1>🎓 कलचाचणी 2025-26 — Admin</h1><span>{len(results)} submissions</span></div>
    <div class="stat-bar">
      <div class="stat"><label>Total Students</label><span>{len(results)}</span></div>
      <div class="stat"><label>Today</label><span>{sum(1 for r in results if r.get('submitted_at','')[:10]==datetime.date.today().isoformat())}</span></div>
    </div>
    <div class="container"><table>
      <thead><tr><th>विद्यार्थी</th><th>School</th><th>District</th><th>Date</th><th>Recommended Stream</th><th>Top Interest Group</th><th>Actions</th></tr></thead>
      <tbody>{''.join([rows]) if results else '<tr><td colspan="7" class="empty">No submissions yet.</td></tr>'}</tbody>
    </table></div></body></html>"""

@app.route('/report/<ref_id>')
def view_report(ref_id):
    pw = request.args.get('pw', '')
    if pw != ADMIN_PASSWORD: abort(403)
    record = load_result(ref_id)
    if not record: abort(404)
    return generate_report_html(record, generate_charts(record['scored']))

@app.route('/report/<ref_id>/download')
def download_report(ref_id):
    pw = request.args.get('pw', '')
    if pw != ADMIN_PASSWORD: abort(403)
    record = load_result(ref_id)
    if not record: abort(404)
    html = generate_report_html(record, generate_charts(record['scored']))
    name = record['student'].get('name', 'student').replace(' ', '_')
    return send_file(BytesIO(html.encode('utf-8')), mimetype='text/html',
                     as_attachment=True,
                     download_name=f'Kalchachani_{name}_{ref_id[:8]}.html')

# ── PUBLIC STUDENT RESULT — no password needed ────────────────────────────────
@app.route('/result/<ref_id>')
def student_result(ref_id):
    record = load_result(ref_id)
    if not record: abort(404)
    charts = generate_charts(record['scored'])
    return generate_student_report_html(record, charts)

@app.route('/result/<ref_id>/download')
def student_download(ref_id):
    record = load_result(ref_id)
    if not record: abort(404)
    html = generate_student_report_html(record, generate_charts(record['scored']))
    name = record['student'].get('name', 'student').replace(' ', '_')
    return send_file(BytesIO(html.encode('utf-8')), mimetype='text/html',
                     as_attachment=True,
                     download_name=f'Kalchachani_My_Report_{name}.html')

if __name__ == '__main__':
    print("=" * 60)
    print("  कलचाचणी 2025-26 Server Starting...")
    print("  Maharashtra Board authentic 7-group framework")
    print("=" * 60)
    print(f"  Test  : http://localhost:5000/test")
    print(f"  Admin : http://localhost:5000/admin?pw={ADMIN_PASSWORD}")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
