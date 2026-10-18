"""Static archive and compiled, escaped LaTeX from actual Parse output.

No model-generated TeX is executed. Missing parses and failed compilations stay
visible in the archive report. Boxes and OCR remain explicitly unreviewed.
"""
from __future__ import annotations

import html
import json
import shutil
import subprocess
from pathlib import Path

from .corpus import manifest
from .util import digest, load_json, now, write_json

UNSUPPORTED_GLYPHS={"衰","을","⨉","╳"}


def tex_escape(text):
    replacements={"\\":r"\textbackslash{}","{":r"\{","}":r"\}","$":r"\$","&":r"\&","#":r"\#","%":r"\%","_":r"\_","~":r"\textasciitilde{}","^":r"\textasciicircum{}"}
    return "".join(r"\fbox{\texttt{U+"+format(ord(c),"04X")+"}}" if c in UNSUPPORTED_GLYPHS else replacements.get(c,c)
                   for c in str(text) if ord(c)>=32 or c in "\n\t")


def latex_document(page,parsed):
    blocks=[]
    missing={c for c in parsed["text"] if c in UNSUPPORTED_GLYPHS}
    if missing:
        blocks.append(r"{\small\color{red} Rendering note: glyphs unsupported by this document font appear as boxed Unicode codes. Original characters remain in the raw model output and HTML transcription. No corrected reading is inferred.\par}")
    for region in parsed["regions"]:
        text=tex_escape(region["text"])
        kind=region.get("type","").lower()
        if "heading" in kind or "title" in kind:
            blocks.append(r"\subsection*{"+text+"}")
        elif "header" in kind or "footer" in kind or "caption" in kind:
            blocks.append(r"{\small\itshape "+text+r"\par}")
        else:blocks.append(text+"\n\\par")
        blocks.append(r"{\scriptsize\color{gray} Region "+tex_escape(region["region_id"])+r"; provider order "+str(region.get("reading_order","unspecified"))+r".\par}"+"\n\\medskip")
    if parsed.get("unparsed_residual", "").strip():
        blocks.append(r"\section*{Unassigned provider output}"+"\n"+tex_escape(parsed["unparsed_residual"]))
    return r"""\documentclass[11pt]{article}
\usepackage[a4paper,margin=22mm]{geometry}
\usepackage{fontspec}
\setmainfont{LinLibertine_R.otf}[BoldFont=LinLibertine_RB.otf,ItalicFont=LinLibertine_RI.otf,BoldItalicFont=LinLibertine_RBI.otf]
\usepackage{xcolor}
\usepackage{hyperref}
\hypersetup{colorlinks=true,urlcolor=blue}
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}
\sloppy
\emergencystretch=2em
\begin{document}
\section*{Historical Britannica: extracted source}
"""+tex_escape(page["metadata"])+r"\par"+"\n"+r"{\small Source row "+str(page["row_index"])+r". Parser: "+tex_escape(parsed["parse_model"])+r".\par}"+"\n"+r"{\small This is model-extracted text, not a corrected transcription. OCR errors, reading order and region alignment require human review.\par}"+"\n\\hrule\\medskip\n"+"\n\n".join(blocks)+"\n\\newpage\\section*{Source record}\n"+tex_escape(page["page_id"])+r"\par"+"\n"+r"Image SHA-256: \texttt{"+tex_escape(page["sha256"][:32])+r"}\par\texttt{"+tex_escape(page["sha256"][32:])+r"}\par"+"\n"+r"Dataset revision: \texttt{"+tex_escape(page["revision"][:20])+r"}\texttt{"+tex_escape(page["revision"][20:])+r"}\par"+"\n"+r"National Library of Scotland, Encyclopaedia Britannica Illustrated (CC0).\par"+"\n"+r"\url{"+page["source_url"]+"}\n\\end{document}\n"


STYLE="""body{margin:0;background:#f7f5ef;color:#232a28;font:16px/1.6 system-ui,sans-serif}main{max-width:1400px;margin:auto;padding:32px}a{color:#23614c}h1,h2,h3{font-family:Georgia,serif;line-height:1.2}header{border-bottom:1px solid #cfd4cc;padding-bottom:20px}.muted{color:#596660}.badge{display:inline-block;border:1px solid #cfd4cc;padding:3px 10px;border-radius:20px;font-size:13px}.grid{display:grid;grid-template-columns:minmax(300px,1fr) minmax(300px,1fr);gap:24px;margin-top:24px}.scan{position:relative;line-height:0}.scan img{width:100%;height:auto}.box{position:absolute;border:1px solid #35786299;background:#52a07814;padding:0;cursor:pointer}.box:hover,.box:focus{background:#ffca4955;border-color:#ad6900}.region{padding:16px;background:white;border:1px solid #dce0d8;margin-bottom:12px;scroll-margin:20px}.region:target{border:2px solid #ad6900}.region pre{white-space:pre-wrap;font:15px/1.6 Georgia,serif}details{background:white;padding:12px;border:1px solid #dce0d8;margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}table{border-collapse:collapse;width:100%;background:white}th,td{text-align:left;padding:10px;border-bottom:1px solid #e0e4dc}iframe{width:100%;height:750px;border:1px solid #ccd2c9}.notice{padding:14px;border-left:3px solid #b38b22;background:#fff8df}@media(max-width:800px){.grid{grid-template-columns:1fr}main{padding:18px}}"""


def document(title,body):
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>'+STYLE+'</style><main>'+body+'</main></html>'


def build_archive(engine) -> dict:
    root=engine.root;site=root/"site"
    for folder in ["pages","documents","images","records","sources"]:(site/folder).mkdir(parents=True,exist_ok=True)
    selected=manifest(root);report={"built":True,"created_at":now(),"selected":len(selected["pages"]),"parsed":0,"compiled":0,"pages":[],"path":str(site),
        "method":"Actual Parse regions in provider order; text escaped before LaTeX compilation. No source corrections. Coordinates are unreviewed; compilation is not OCR validation."}
    compiler=shutil.which(engine.settings.latex_engine)
    for page in selected["pages"]:
        pid=page["page_id"];folder=root/"pages"/pid;parsed=load_json(folder/"parse.json")
        image_name=Path(page["image_file"]).name;shutil.copyfile(page["image_file"],site/"images"/image_name)
        row={"page_id":pid,"row_index":page["row_index"],"parsed":bool(parsed),"compiled":False}
        source={k:v for k,v in page.items() if k!="image_file"}
        source["image_file"]="../images/"+image_name
        write_json(site/"records"/(pid+".json"),source)
        head='<header><a href="../index.html">← All 100 pages</a><h1>Source row '+str(page["row_index"])+'</h1><p>'+html.escape(page["metadata"])+'</p><p class="muted">'+html.escape(pid)+'</p></header>'
        if not parsed:
            error=load_json(folder/"parse-error.json")
            if error:
                row["parse_error"]=error
                status='Extraction failed: '+html.escape(str(error.get("message","Inspect the retained error record")))+'. The failed page remains in the selected set.'
            else:status='Not yet extracted. No text or compiled document has been invented.'
            body=head+'<p class="notice">'+status+'</p><img alt="Original Britannica source scan" style="max-width:900px;width:100%" src="../images/'+image_name+'">'
        else:
            report["parsed"]+=1
            row["rendering_substitutions"]=["U+"+format(ord(c),"04X") for c in sorted(set(parsed["text"])&UNSUPPORTED_GLYPHS)]
            tex=latex_document(page,parsed);tex_path=site/"documents"/(pid+".tex");tex_path.write_text(tex)
            pdf_path=tex_path.with_suffix(".pdf");receipt_path=tex_path.with_suffix(".receipt.json")
            fingerprint=digest(tex);receipt=load_json(receipt_path,{})
            if receipt.get("tex_sha256")==fingerprint and receipt.get("status")=="compiled" and pdf_path.is_file():
                row["compiled"]=True
            elif compiler:
                # This generated document contains escaped source text only.
                try:
                    result=subprocess.run([compiler,"--untrusted","--keep-logs","--outdir",str(pdf_path.parent),str(tex_path)],capture_output=True,text=True,timeout=180)
                    row["compiled"]=result.returncode==0 and pdf_path.is_file() and pdf_path.read_bytes().startswith(b"%PDF")
                    receipt={"status":"compiled" if row["compiled"] else "error","tex_sha256":fingerprint,"compiler":Path(compiler).name,"exit_code":result.returncode,"output":(result.stdout+result.stderr)[-12000:],"at":now()}
                except (OSError,subprocess.TimeoutExpired) as error:
                    receipt={"status":"error","tex_sha256":fingerprint,"error":type(error).__name__,"at":now()}
                write_json(receipt_path,receipt)
            else:
                receipt={"status":"error","error":"LaTeX compiler unavailable; install tectonic and set LATEX_ENGINE","tex_sha256":fingerprint};write_json(receipt_path,receipt)
            if row["compiled"]:report["compiled"]+=1
            else:row["compilation_error"]=receipt.get("error",receipt.get("output","Compilation failed"))
            boxes=[];regions=[]
            for region in parsed["regions"]:
                rid=region["region_id"];bbox=region.get("bbox_raw")
                if region.get("bbox_within_page") and bbox:
                    x1,y1,x2,y2=bbox
                    boxes.append('<a class="box" title="Unreviewed '+html.escape(rid)+'" href="#'+rid+'" style="left:'+str(x1*100)+'%;top:'+str(y1*100)+'%;width:'+str((x2-x1)*100)+'%;height:'+str((y2-y1)*100)+'%"></a>')
                regions.append('<article class="region" id="'+rid+'"><span class="badge">'+html.escape(rid)+' · '+html.escape(str(region.get("type","unspecified")))+'</span><pre>'+html.escape(region["text"])+'</pre></article>')
            pdf='<a href="../documents/'+pid+'.pdf">Compiled LaTeX PDF</a> · ' if row["compiled"] else '<strong>LaTeX compilation pending/failed</strong> · '
            residual=parsed.get("unparsed_residual","")
            residual_html='<p class="notice">Some provider output could not be assigned to a region; it is retained below and requires review.</p><pre>'+html.escape(residual)+'</pre>' if residual.strip() else ''
            body=head+'<p>'+pdf+'<a href="../documents/'+pid+'.tex">LaTeX source</a> · <a href="../records/'+pid+'.json">Source record</a></p><p class="notice">Model-extracted text; OCR errors remain. Boxes show unreviewed provider coordinates. Click a box to inspect its region.</p>'+residual_html+'<div class="grid"><section><h2>Original scan</h2><div class="scan"><img alt="Original Britannica source scan" src="../images/'+image_name+'">'+''.join(boxes)+'</div></section><section><h2>Extracted regions</h2>'+''.join(regions)+'</section></div>'
            if row["compiled"]:body+='<details><summary>Read compiled LaTeX</summary><iframe title="Compiled LaTeX transcription" src="../documents/'+pid+'.pdf"></iframe></details>'
            comparison=load_json(folder/"comparison.json")
            if comparison:
                body+='<h2>Generated comparison</h2><p>Generated claims require source review.</p><pre>'+html.escape(json.dumps(comparison,indent=2,ensure_ascii=False))+'</pre>'
                for source_id in comparison.get("source_ids",[]):
                    try:
                        s=engine.store.source(source_id);s.pop("provenance",None)
                        write_json(site/"sources"/(digest(source_id)+".json"),s)
                    except KeyError:pass
        body+='<footer><p>Scans: National Library of Scotland, CC0. Wikipedia excerpts: Wikipedia contributors, CC BY-SA 4.0; revision links and provenance accompany each excerpt. Text segmentation and model comparisons are team-derived.</p></footer>'
        (site/"pages"/(pid+".html")).write_text(document("Britannica source row "+str(page["row_index"]),body))
        report["pages"].append(row)
        write_json(site/"archive-report.json",report)
    rows=''.join('<tr><td><a href="pages/'+r["page_id"]+'.html">'+str(r["row_index"])+'</a></td><td>'+html.escape(r["page_id"])+'</td><td>'+('Extracted' if r["parsed"] else 'Pending')+'</td><td>'+('Compiled' if r["compiled"] else 'Pending / failed')+'</td></tr>' for r in report["pages"])
    body='<header><p class="muted">Knowledge Across Time · source archive</p><h1>Britannica, with the evidence attached.</h1><p>100 fixed source scans. Extraction, matching and comparison remain separate records.</p></header><p>'+str(report["parsed"])+' / 100 extracted · '+str(report["compiled"])+' / 100 compiled LaTeX documents</p><p class="notice">A compiled document is a readable rendering of model output, not proof of transcription accuracy.</p><details><summary>Page selection method</summary><p>'+html.escape(selected.get("selection_method","Not prepared"))+'</p><p>'+html.escape(selected.get("bias",""))+'</p></details><table><thead><tr><th>Source row</th><th>Stable page ID</th><th>Extraction</th><th>LaTeX</th></tr></thead><tbody>'+rows+'</tbody></table><p><a href="archive-report.json">Machine-readable archive report</a> · <a href="cases.json">Reviewed agent cases</a></p>'
    (site/"index.html").write_text(document("Knowledge Across Time — source archive",body))
    write_json(site/"cases.json",engine.store.cases())
    write_json(site/"archive-report.json",report)
    return report
