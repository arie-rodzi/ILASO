# ============================================================
# ILASO — Configuration & Premium Academic Styles
# Replace your existing config_styles.py with this file.
# ============================================================

SEMESTER_WEEKS = 14
DEFAULT_MIN = 15
DEFAULT_MAX = 17
TARGET_KS = 16
LATE_ENTRY_CUTOFF_WEEK = 10
MAX_SUBJECTS = 2
MAX_CLASSES_SAME_SUBJECT = 3
SCORE_PREF = {1: 100, 2: 80, 3: 60, 4: 40, 5: 20}
SCORE_NOT_PREF = -30

APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root{
  --navy:#061A40;
  --navy2:#082B66;
  --navy3:#0E3A8A;
  --gold:#D9B75F;
  --gold2:#F6D77A;
  --paper:#F5F7FB;
  --ink:#0F172A;
  --muted:#64748B;
  --line:#E5E7EB;
}

html, body, [class*="css"]{
  font-family:'Inter', sans-serif;
}

.stApp{
  background:
    radial-gradient(circle at 10% 0%, rgba(217,183,95,.13), transparent 25%),
    radial-gradient(circle at 92% 8%, rgba(8,43,102,.12), transparent 28%),
    linear-gradient(180deg,#F7F9FC 0%,#EEF2F7 100%);
}

.block-container{
  padding-top:1.15rem;
  padding-left:2rem;
  padding-right:2rem;
  max-width:1560px;
}

[data-testid="stSidebar"]{
  background:
    radial-gradient(circle at 30% 0%, rgba(246,215,122,.18), transparent 32%),
    linear-gradient(180deg,#061A40 0%,#0B3678 100%);
}
[data-testid="stSidebar"] *{color:white !important;}

/* ============================================================
   HERO SECTION — NO WORD PREMIUM
   ============================================================ */
.hero-shell{
  position:relative;
  overflow:hidden;
  color:white;
  padding:46px 50px 34px 50px;
  border-radius:38px;
  margin-bottom:30px;
  min-height:350px;
  border:1px solid rgba(246,215,122,.36);
  box-shadow:
    0 34px 90px rgba(6,26,64,.34),
    inset 0 1px 0 rgba(255,255,255,.14);
  background:
    linear-gradient(135deg, rgba(4,16,40,.98) 0%, rgba(8,43,102,.98) 48%, rgba(7,31,77,.99) 100%);
}
.hero-shell:before{
  content:"";
  position:absolute;
  inset:0;
  background:
    linear-gradient(90deg, rgba(255,255,255,.07) 1px, transparent 1px),
    linear-gradient(0deg, rgba(255,255,255,.045) 1px, transparent 1px);
  background-size:46px 46px;
  mask-image:linear-gradient(90deg, rgba(0,0,0,.35), transparent 78%);
  opacity:.55;
}
.hero-shell:after{
  content:"";
  position:absolute;
  right:-120px;
  top:-140px;
  width:520px;
  height:520px;
  border-radius:999px;
  background:radial-gradient(circle, rgba(246,215,122,.26), rgba(246,215,122,.08) 35%, transparent 68%);
  filter:blur(2px);
}
.hero-glow{
  position:absolute;
  border-radius:999px;
  pointer-events:none;
}
.hero-glow-one{
  left:38%;
  bottom:-120px;
  width:500px;
  height:210px;
  background:radial-gradient(circle, rgba(246,215,122,.23), transparent 70%);
  transform:rotate(-8deg);
}
.hero-glow-two{
  left:-100px;
  top:-100px;
  width:300px;
  height:300px;
  background:radial-gradient(circle, rgba(255,255,255,.12), transparent 66%);
}
.hero-content-grid{
  position:relative;
  z-index:2;
  display:grid;
  grid-template-columns:230px minmax(0,1fr);
  gap:36px;
  align-items:center;
}
.hero-logo-card{
  width:216px;
  height:216px;
  border-radius:44px;
  display:flex;
  align-items:center;
  justify-content:center;
  background:
    linear-gradient(145deg, rgba(255,255,255,.18), rgba(255,255,255,.05));
  border:1px solid rgba(246,215,122,.48);
  box-shadow:
    0 28px 70px rgba(0,0,0,.32),
    inset 0 0 46px rgba(246,215,122,.13);
  overflow:hidden;
}
.hero-logo-card img{
  width:204px;
  height:204px;
  object-fit:cover;
  border-radius:38px;
  filter:drop-shadow(0 12px 22px rgba(0,0,0,.25));
}
.sigma-fallback{
  font-size:92px;
  font-weight:1000;
  color:var(--gold2);
}
.hero-eyebrow{
  display:inline-flex;
  align-items:center;
  gap:10px;
  letter-spacing:.22em;
  text-transform:uppercase;
  font-weight:900;
  font-size:13px;
  color:var(--gold2);
  padding:10px 16px;
  border:1px solid rgba(246,215,122,.30);
  border-radius:999px;
  background:rgba(246,215,122,.08);
  margin-bottom:16px;
}
.hero-title-main{
  font-size:96px;
  line-height:.88;
  font-weight:1000;
  letter-spacing:.04em;
  color:#FFFFFF;
  text-shadow:0 18px 45px rgba(0,0,0,.24);
}
.hero-title-sub{
  margin-top:15px;
  font-size:30px;
  line-height:1.15;
  font-weight:850;
  color:rgba(255,255,255,.96);
}
.hero-description{
  margin-top:14px;
  max-width:920px;
  font-size:17px;
  line-height:1.7;
  color:rgba(255,255,255,.76);
}
.hero-chip-row{
  display:flex;
  flex-wrap:wrap;
  gap:12px;
  margin-top:25px;
}
.hero-chip-row span{
  display:inline-flex;
  align-items:center;
  gap:8px;
  padding:12px 17px;
  border-radius:999px;
  color:#FFE59B;
  font-weight:800;
  font-size:13px;
  background:rgba(255,255,255,.075);
  border:1px solid rgba(246,215,122,.28);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.08);
  backdrop-filter:blur(10px);
}
.hero-workflow{
  position:relative;
  z-index:2;
  display:grid;
  grid-template-columns:repeat(5,1fr);
  gap:12px;
  margin-top:30px;
}
.hero-step{
  padding:15px 16px;
  border-radius:22px;
  background:rgba(255,255,255,.07);
  border:1px solid rgba(255,255,255,.12);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.08);
}
.hero-step b{
  display:block;
  color:var(--gold2);
  font-size:13px;
  letter-spacing:.08em;
}
.hero-step span{
  display:block;
  color:rgba(255,255,255,.86);
  font-size:13px;
  margin-top:5px;
  font-weight:650;
}

.section-title{
  font-size:26px;
  font-weight:950;
  color:var(--navy);
  margin:32px 0 8px 0;
  letter-spacing:-.02em;
}
.section-note{
  font-size:15px;
  color:var(--muted);
  margin-bottom:16px;
}
.soft-card{
  background:rgba(255,255,255,.86);
  border:1px solid rgba(226,232,240,.95);
  border-radius:28px;
  padding:24px;
  box-shadow:0 18px 45px rgba(15,23,42,.08);
  backdrop-filter:blur(12px);
}
.metric-card{
  background:
    radial-gradient(circle at 88% 0%, rgba(246,215,122,.18), transparent 28%),
    linear-gradient(180deg,#FFFFFF 0%,#F8FAFC 100%);
  border:1px solid rgba(148,163,184,.22);
  border-left:6px solid var(--gold);
  border-radius:26px;
  padding:21px 23px;
  box-shadow:0 16px 40px rgba(2,6,23,.085);
  min-height:122px;
}
.metric-label{
  font-size:12px;
  color:#64748B;
  text-transform:uppercase;
  letter-spacing:.10em;
  font-weight:900;
}
.metric-value{
  font-size:34px;
  color:var(--navy);
  font-weight:1000;
  margin-top:9px;
}
.metric-note{
  font-size:13px;
  color:#64748B;
  margin-top:6px;
}
.badge{
  display:inline-flex;
  padding:8px 12px;
  border-radius:999px;
  background:#EEF2FF;
  color:#1E3A8A;
  font-weight:800;
  font-size:12px;
}
.stButton > button{
  border-radius:18px !important;
  font-weight:900 !important;
  border:1px solid rgba(217,183,95,.34) !important;
  background:linear-gradient(135deg,#061A40 0%,#0E3A8A 100%) !important;
  color:white !important;
  min-height:48px;
  box-shadow:0 14px 34px rgba(6,26,64,.18) !important;
}
.stButton > button:hover{
  transform:translateY(-1px);
  border-color:rgba(246,215,122,.72) !important;
}
[data-testid="stDataFrame"]{
  border-radius:22px;
  overflow:hidden;
  border:1px solid rgba(226,232,240,.95);
  box-shadow:0 14px 30px rgba(15,23,42,.055);
}
.footer{
  margin-top:44px;
  padding:22px;
  color:#64748B;
  text-align:center;
  border-top:1px solid #E5E7EB;
}
@media(max-width:900px){
  .hero-content-grid{grid-template-columns:1fr;}
  .hero-logo-card{width:150px;height:150px;}
  .hero-logo-card img{width:142px;height:142px;}
  .hero-title-main{font-size:62px;}
  .hero-title-sub{font-size:23px;}
  .hero-workflow{grid-template-columns:1fr;}
}
</style>
"""
