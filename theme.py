"""Premium visual system for the Research Assistant frontend."""

import html
import re
from typing import Dict, List, Optional

NODE_ORDER = ["decompose", "search", "draft", "review", "finalize"]
NODE_META = {
    "decompose": ("01", "Plan", "Break the question into focused research tasks"),
    "search": ("02", "Search", "Collect evidence from relevant sources"),
    "draft": ("03", "Draft", "Turn evidence into a coherent report"),
    "review": ("04", "Review", "Check the answer for gaps and weak points"),
    "finalize": ("05", "Finalize", "Prepare the polished answer and sources"),
}

BASE_STYLE = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root{--bg:#f6f7fb;--surface:#fff;--surface2:#f8f9fd;--text:#172033;--muted:#6b7487;--line:#e6e9f1;--primary:#6d5dfc;--primary2:#8d72ff;--blue:#3b82f6;--green:#17a673;--orange:#f59e0b;--red:#e45b68;--shadow:0 12px 35px rgba(31,36,58,.07)}
html,body,[data-testid="stAppViewContainer"],.stApp{background:var(--bg)!important;color:var(--text)!important}
[data-testid="stHeader"]{background:transparent!important}
[data-testid="stSidebar"]{background:#11172a!important;border-right:1px solid #252d47!important}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{
    color:#eef1ff!important
}
.stApp,.stApp p,.stApp li,.stApp label,.stApp span{font-family:'DM Sans',sans-serif}
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stButton button{font-family:'Manrope',sans-serif!important}
.block-container{padding-top:2rem!important;padding-bottom:3rem!important;max-width:1450px!important}
[data-testid="stTextArea"] textarea{background:var(--surface)!important;color:var(--text)!important;border:1px solid var(--line)!important;border-radius:16px!important;font-family:'DM Sans',sans-serif!important;font-size:1rem!important;padding:1rem!important;box-shadow:0 4px 16px rgba(31,36,58,.035)}
[data-testid="stTextArea"] textarea:focus{border-color:var(--primary)!important;box-shadow:0 0 0 3px rgba(109,93,252,.12)!important}
[data-testid="stTextArea"] textarea::placeholder{color:#9aa2b4!important}
.stButton button{background:linear-gradient(135deg,var(--primary),var(--primary2))!important;color:white!important;border:0!important;border-radius:12px!important;font-weight:700!important;padding:.72rem 1.25rem!important;box-shadow:0 8px 20px rgba(109,93,252,.2);transition:.2s ease}
.stButton button:hover{transform:translateY(-1px);box-shadow:0 12px 25px rgba(109,93,252,.27)}
[data-testid="stTextInput"] input{background:#1a2138!important;color:#eef1ff!important;border:1px solid #303953!important;border-radius:10px!important;opacity:1!important}
[data-testid="stTextInput"] input:disabled{color:#eef1ff!important;-webkit-text-fill-color:#eef1ff!important;opacity:1!important}
[data-testid="stMetric"]{background:var(--surface)!important;border:1px solid var(--line)!important;border-radius:14px!important;padding:14px!important;box-shadow:var(--shadow)}
hr{border-color:var(--line)!important}
.stAlert{border-radius:12px!important}

.ra-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.4rem}
.ra-brand{display:flex;align-items:center;gap:.8rem}
.ra-logo{width:42px;height:42px;border-radius:13px;background:linear-gradient(135deg,#6d5dfc,#8d72ff);display:flex;align-items:center;justify-content:center;color:#fff;font-size:1.2rem;font-weight:800;box-shadow:0 9px 22px rgba(109,93,252,.2)}
.ra-brand-title{font:800 1.15rem 'Manrope',sans-serif;color:var(--text);line-height:1.05}
.ra-crewai-badge{display:inline-block;margin-left:.5rem;padding:.15rem .55rem;border-radius:999px;background:#FFF1E0;color:#B45309;font:700 .65rem 'Manrope',sans-serif;letter-spacing:.02em;vertical-align:middle}
.ra-brand-sub{font-size:.74rem;color:var(--muted);margin-top:3px}
.ra-ref{font-size:.72rem;color:#7d8699;background:#fff;border:1px solid var(--line);border-radius:999px;padding:.42rem .72rem}
.ra-hero{background:linear-gradient(135deg,#161d34 0%,#25234d 58%,#3a2c6c 100%);border-radius:24px;padding:2rem 2.1rem;color:#fff;position:relative;overflow:hidden;box-shadow:0 18px 50px rgba(31,36,58,.13);margin-bottom:1.4rem}
.ra-hero:after{content:"";position:absolute;width:330px;height:330px;border-radius:50%;right:-110px;top:-150px;background:rgba(141,114,255,.18);filter:blur(4px)}
.ra-kicker{font-size:.7rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#bdb7ff;margin-bottom:.5rem}
.ra-hero h1{font-size:2.05rem;margin:0 0 .5rem;color:#fff;letter-spacing:-.035em}
.ra-hero p{color:#d8dbec;margin:0;max-width:700px;font-size:.93rem;line-height:1.65}
.ra-status{position:absolute;right:1.4rem;bottom:1.3rem;z-index:2;display:flex;align-items:center;gap:.4rem;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.14);padding:.42rem .7rem;border-radius:999px;font-size:.7rem}
.ra-dotlive{width:7px;height:7px;border-radius:50%;background:#4ade80;box-shadow:0 0 0 4px rgba(74,222,128,.12)}
.ra-section{font:700 .74rem 'Manrope',sans-serif;letter-spacing:.09em;text-transform:uppercase;color:#7b8497;margin:.2rem 0 .65rem}
.ra-card{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:1.15rem 1.2rem;box-shadow:var(--shadow)}
.ra-card-title{font:700 .95rem 'Manrope',sans-serif;color:var(--text);margin-bottom:.25rem}
.ra-card-sub{font-size:.77rem;color:var(--muted);line-height:1.5}
.ra-rail{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:1.15rem 1rem;box-shadow:var(--shadow)}
.ra-rail-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem}
.ra-rail-title{font:700 .74rem 'Manrope',sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#697286}
.ra-progress{font-size:.7rem;color:var(--primary);font-weight:700}
.ra-node{position:relative;display:flex;gap:.7rem;padding:.2rem .1rem 1.2rem}
.ra-node:last-child{padding-bottom:.15rem}
.ra-node:before{content:"";position:absolute;left:16px;top:34px;bottom:0;width:1px;background:#e5e8f0}
.ra-node:last-child:before{display:none}
.ra-node-icon{width:32px;height:32px;border-radius:10px;background:#f2f3f8;border:1px solid #e3e6ef;display:flex;align-items:center;justify-content:center;font:700 .63rem 'Manrope',sans-serif;color:#9aa2b4;z-index:1;flex:none}
.ra-node.done .ra-node-icon{background:#e9f8f2;border-color:#c9efdf;color:var(--green)}
.ra-node.active .ra-node-icon{background:#eeecff;border-color:#d9d3ff;color:var(--primary);box-shadow:0 0 0 4px rgba(109,93,252,.08);animation:pulse 1.5s infinite}
.ra-node.flag .ra-node-icon{background:#fff0f1;border-color:#ffd2d6;color:var(--red)}
@keyframes pulse{50%{box-shadow:0 0 0 8px rgba(109,93,252,.04)}}
.ra-node-label{font:700 .82rem 'Manrope',sans-serif;color:#273047}
.ra-node.pending .ra-node-label{color:#9aa2b4}
.ra-node-sub{font-size:.71rem;color:#858ea0;line-height:1.4;margin-top:2px}
.ra-loop{margin:-.55rem 0 .75rem 42px;border-left:1px dashed #f0b74b;padding-left:.55rem;font-size:.68rem;color:#b77906}
.ra-log{font:500 .7rem 'DM Sans',sans-serif;color:#687286;background:#11172a;border-radius:13px;padding:.85rem 1rem;max-height:190px;overflow:auto;line-height:1.6;white-space:pre-wrap;border:1px solid #262f4a}
.ra-log .new{color:#c9c3ff}
.ra-file{background:#fff;border:1px solid var(--line);border-radius:20px;padding:1.55rem 1.65rem;margin-top:1.1rem;box-shadow:var(--shadow)}
.ra-file-head{display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;padding-bottom:1rem;border-bottom:1px solid var(--line)}
.ra-file-tag{font-size:.67rem;text-transform:uppercase;letter-spacing:.13em;font-weight:800;color:var(--primary)}
.ra-file-title{font:800 1.22rem 'Manrope',sans-serif;color:#20283c;margin-top:.3rem}
.ra-file-ref{font-size:.68rem;color:#8c95a7;background:#f5f6fa;padding:.38rem .58rem;border-radius:8px;white-space:nowrap}
.ra-summary{margin:1rem 0;padding:1rem 1.05rem;border-radius:14px;background:linear-gradient(135deg,#f4f2ff,#f8f9ff);border:1px solid #e8e4ff}
.ra-summary-label{font-size:.65rem;text-transform:uppercase;letter-spacing:.12em;color:var(--primary);font-weight:800;margin-bottom:.35rem}
.ra-summary p{margin:0;color:#40495e;line-height:1.65;font-size:.86rem}
.ra-file h2{font:800 .85rem 'Manrope',sans-serif;color:#263047;margin:1.35rem 0 .6rem}
.ra-file p,.ra-file li{color:#4c566b;line-height:1.72;font-size:.86rem}
.ra-file a{color:#5c4ee5;text-decoration:none}.ra-file a:hover{text-decoration:underline}
.ra-source{display:flex;gap:.65rem;align-items:flex-start;padding:.7rem .75rem;background:#fafbfe;border:1px solid #edf0f5;border-radius:11px;margin:.45rem 0}
.ra-source-num{width:24px;height:24px;border-radius:7px;background:#eeecff;color:var(--primary);display:flex;align-items:center;justify-content:center;font-size:.65rem;font-weight:800;flex:none}
.ra-source-text{font-size:.75rem;line-height:1.4;overflow:hidden}.ra-source-url{display:block;color:#9098aa;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px}
.ra-flagnote{font-size:.72rem;color:#b44c58;background:#fff4f5;border:1px solid #ffdfe2;border-radius:11px;padding:.7rem .8rem;margin-top:1rem}
.ra-empty{background:#fff;border:1px dashed #d9deea;border-radius:18px;padding:2rem;text-align:center;color:#8a93a5}
.ra-chip{display:inline-block!important;background:rgba(109,93,252,.18)!important;color:#c9c3ff!important;border:1px solid rgba(141,114,255,.28)!important;border-radius:999px!important;padding:.35rem .65rem!important;font-size:.70rem!important;font-weight:700!important;margin:.18rem .2rem .18rem 0!important}
footer{visibility:hidden}
</style>
"""

def base_style(): return BASE_STYLE

def masthead(ref: str) -> str:
    return f'''<div class="ra-top"><div class="ra-brand"><div class="ra-logo">🤝</div><div><div class="ra-brand-title">Research Agent <span class="ra-crewai-badge">Powered by CrewAI</span></div><div class="ra-brand-sub">AI-powered research workspace</div></div></div><div class="ra-ref">SESSION · {html.escape(ref)}</div></div>'''

def hero():
    return '''<div class="ra-hero"><div class="ra-kicker">Research intelligence workspace</div><h1>Turn complex questions into evidence-backed answers.</h1><p>Ask a research question and watch the agent plan, search, draft, review and finalize the answer in real time.</p><div class="ra-status"><span class="ra-dotlive"></span> Agent ready</div></div>'''

def render_rail(node_status: Dict[str,str], extra_search_rounds: int=0) -> str:
    done=sum(1 for n in NODE_ORDER if node_status.get(n)=="done")
    rows=[]
    for name in NODE_ORDER:
        num,label,sub=NODE_META[name]; status=node_status.get(name,"pending")
        icon="✓" if status=="done" else ("!" if status=="flag" else num)
        rows.append(f'''<div class="ra-node {status}"><div class="ra-node-icon">{icon}</div><div><div class="ra-node-label">{label}</div><div class="ra-node-sub">{html.escape(sub)}</div></div></div>''')
        if name=="review" and extra_search_rounds:
            rows.append(f'<div class="ra-loop">↻ Returned to search · round {extra_search_rounds} of 2</div>')
    return f'''<div class="ra-rail"><div class="ra-rail-head"><div class="ra-rail-title">Agent workflow</div><div class="ra-progress">{done}/5 complete</div></div>{''.join(rows)}</div>'''

def render_log(lines: List[str]) -> str:
    if not lines: return '<div class="ra-log">Waiting for the agent to start…</div>'
    body="\n".join(html.escape(x) for x in lines[-10:])
    return f'<div class="ra-log">{body}</div>'

def _report_html(md: str) -> str:
    md=re.sub(r'^##\s+.*$', '', md, flags=re.MULTILINE)
    parts=[]
    for block in re.split(r'\n\s*\n', md):
        block=block.strip()
        if not block: continue
        lines=block.splitlines()
        if all(re.match(r'^\s*[-*]\s+', x) for x in lines):
            items=''.join(f'<li>{html.escape(re.sub(r"^\\s*[-*]\\s+", "", x))}</li>' for x in lines)
            parts.append(f'<ul>{items}</ul>')
        else:
            text=html.escape(block).replace('**','')
            parts.append(f'<p>{text}</p>')
    return ''.join(parts)

def render_case_file(ref: str, summary: str, report_markdown: str, sources: List[str], failed: Optional[List[str]]=None) -> str:
    source_html=''.join(f'<div class="ra-source"><div class="ra-source-num">{i}</div><div class="ra-source-text"><a href="{html.escape(s)}" target="_blank">{html.escape(s)}</a><span class="ra-source-url">Open source ↗</span></div></div>' for i,s in enumerate(sources,1)) or '<div class="ra-card-sub">No sources were collected.</div>'
    flag=f'<div class="ra-flagnote">⚑ {len(failed)} search step(s) returned no usable results.</div>' if failed else ''
    return f'''<div class="ra-file"><div class="ra-file-head"><div><div class="ra-file-tag">Research report</div><div class="ra-file-title">Evidence-backed findings</div></div><div class="ra-file-ref">REF-{html.escape(ref)}</div></div><div class="ra-summary"><div class="ra-summary-label">Executive summary</div><p>{html.escape(summary)}</p></div><h2>Detailed report</h2>{_report_html(report_markdown)}<h2>Sources · {len(sources)}</h2>{source_html}{flag}</div>'''
