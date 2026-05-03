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
        'colleges': ['IIT', 'VJTI Mumbai', 'COEP Pune', 'NIT', 'SP College Pune'],
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
        'colleges': ['Sydenham College Mumbai', 'H.R. College Mumbai', 'Fergusson Pune', 'ICAI', 'Symbiosis Pune'],
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
        'colleges': ['FTII Pune', 'Symbiosis Mass Comm Pune', 'XIC Mumbai', 'JJ School of Art Mumbai'],
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
        'colleges': ['TISS Mumbai', 'D.Ed / B.Ed Colleges', 'Fergusson Pune', 'SNDT Mumbai'],
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
        'colleges': ['AIIMS', 'BJ Medical Pune', 'KEM Mumbai', 'Govt Medical Colleges MH', 'BAMS Colleges'],
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
        'colleges': ['MPKV Rahuri', 'Pune Agriculture College', 'Konkan KV', 'Forest Research Institute', 'Nagpur Agri College'],
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
        'colleges': ['NDA Khadakwasla', 'MPSC Prep Institutes', 'Law Colleges (LLB)', 'Fergusson / SP College Pune'],
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
    career_match = CAREER_MAP.get(top_group, {
        'stream': 'मार्गदर्शन आवश्यक', 'careers': ['Counselling recommended'],
        'colleges': ['School counsellor'], 'description': 'Detailed counselling needed.',
    })

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
    college_list = ''.join([f'<span class="tag">{c}</span>' for c in cm.get('colleges',[])])
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
        <div style="margin-top:12px"><strong style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.5px">Suggested Colleges / Institutes</strong><div style="margin-top:5px">{college_list}</div></div>
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

if __name__ == '__main__':
    print("=" * 60)
    print("  कलचाचणी 2025-26 Server Starting...")
    print("  Maharashtra Board authentic 7-group framework")
    print("=" * 60)
    print(f"  Test  : http://localhost:5000/test")
    print(f"  Admin : http://localhost:5000/admin?pw={ADMIN_PASSWORD}")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
