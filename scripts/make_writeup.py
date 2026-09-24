"""Render the three-page Scientific Track report from current result JSON."""
import json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle
from PIL import Image as PILImage
ROOT=Path(__file__).resolve().parents[1]

def main():
    load=lambda name:json.loads((ROOT/'data'/name).read_text())
    clean=load('summary.json');noise=load('noise_analysis.json');second=load('second_method.json');finite=load('finite_shot_recalibration.json')
    budget=load('budget_study.json');size=load('commensuration.json');large=load('large_n_cut_analysis.json')
    styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='Body',fontName='Helvetica',fontSize=9.2,leading=12,spaceAfter=6,textColor=colors.HexColor('#152638')))
    styles['Title'].textColor=colors.HexColor('#152638');styles['Title'].alignment=0;styles['Heading2'].textColor=colors.HexColor('#007F7A');styles['Heading2'].fontSize=12;styles['Heading2'].spaceBefore=7;styles['Heading2'].spaceAfter=6
    story=[]
    def p(text,style='Body'):story.append(Paragraph(text,styles[style]))
    def fig(name,width=480):
        path=ROOT/'figures'/name;w,h=PILImage.open(path).size;story.append(Image(str(path),width=width,height=width*h/w));story.append(Spacer(1,5))
    def table(rows,widths):
        t=Table([[Paragraph(str(x),styles['Body']) for x in row] for row in rows],colWidths=widths)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EAF3F2')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.35,colors.HexColor('#CBD8DE')),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]));story.append(t);story.append(Spacer(1,5))
    p('PHASE HUNTER','Title');p('Team Popeyes - solo: Tanish Singh Rajpal | Q-SITE 2026 Scientific Track')
    p('A game about finding a quantum phase boundary with a finite measurement budget. Players scan a hidden map, interpret two correlators and draw a border. The contribution is a reproducible investigation of finite-size frustration, gate noise and measurement strategy, made playable in a browser.')
    p('1. Model, observables and classification','Heading2')
    p('The periodic ANNNI ring has H = -sum ZZ(1) + kappa sum ZZ(2) - h sum X. We scan kappa in [0,1] and h in [0,2]. C1 and C2 average Z correlations over all sites. Three seeded k-means clusters classify ferromagnetic, paramagnetic and antiphase regions. The analytic floating band is excluded from the primary metric; it is not independently detected.')
    fig('clean_phase_diagram.png',380)
    p(f"The N=8, 40 x 40 exact PennyLane grid agrees with the qualitative analytic reference on {100*clean['accuracy_excluding_floating']:.2f}% of non-floating cells ({100*clean['accuracy_all_cells']:.2f}% of all cells). NumPy and PennyLane energies/correlators agree to about 3e-14. Finite-size label agreement is not an exact thermodynamic transition location.")
    p('2. A ring-size trap: period-four order','Heading2')
    p('A perfect ++-- stripe closes only when N is divisible by four. On N=6, C2 cannot be below -1/3 for any Z-basis bitstring, so averaging quantum outcomes cannot recover the -1 stripe signature. The same classifier therefore behaves very differently even without gate noise.')
    table([['Ring N','C2 at kappa=0.8, h=0.1','24 x 24 label agreement']]+[[r['qubits'],f"{r['zz2']:.3f}",f"{100*r['agreement_excluding_floating']:.1f}%"] for r in size['rows']],[70,215,215])
    p('This is finite-ring commensuration and a classifier limitation, not disappearance of the infinite-model antiphase. The 24 x 24 size comparison uses the same grid, reference mask and three-cluster rule; its N=8 score differs from the denser 40 x 40 headline result.')
    story.append(PageBreak())
    p('3. Noise changes the signal and the inferred map','Heading2')
    fig('phase_diagrams_noise.png',300)
    rows=[['Gate noise p','Ordered area: fixed clean rule','Ordered area: refitted rule']]
    for key,row in noise['phase_areas'].items():rows.append([key,f"{100*row['fixed_rule']['ordered']:.2f}%",f"{100*row['recalibrated']['ordered']:.2f}%"])
    table(rows,[80,210,210])
    q=noise['vqe_quality'];p(f"The 24 x 24 N=8 scan uses four-layer VQE fits on default.qubit, then identical parameters on default.mixed with target depolarization after each CNOT. Mean preparation-energy error is {q['energy_error_mean']:.3f}, maximum {q['energy_error_max']:.3f}; {q['points_above_0_05']}/576 points exceed 0.05. Comparisons across p share the prepared state.")
    p('At p=0.05 the fixed classifier calls about 39% less area ordered. Recalibration recovers most of that area, with small boundary changes. This demonstrates classifier sensitivity, not invariant physical transitions. Antiphase and ferromagnetic interiors lose about 47% and 40% of their signals; the N=12 cuts reproduce the ordering (0.512 vs 0.615). Likely mechanism: the antiphase lives on the distance-2 correlator, with more gates between the compared spins, so the same per-gate error costs it more. Both sizes agree with this handout prediction, but isolating distance would need a third distance or a depth sweep.')
    f20=finite['noise']['0.05']['20'];l20=finite['noise']['0.01']['20'];p(f"Paired finite-shot test (200 seeds, same full-register observations): at p=0.05 and 20 shots/point, recalibration raises agreement with the noiseless prepared-map labels from {100*f20['fixed']['mean']:.1f}% to {100*f20['recalibrated']['mean']:.1f}%. At p=0.01 it falls from {100*l20['fixed']['mean']:.1f}% to {100*l20['recalibrated']['mean']:.1f}%, showing that refitting is useful conditionally rather than automatically. This is transductive map inference, not state repair or held-out generalization.")
    p('4. Larger-system check: N=12 with noise','Heading2')
    rows=[['Cut (kappa)','p=0.05 attenuation','Fixed / rescaled shift in h']]
    for name,e in large['cuts'].items():
        v=e['noise']['p0.05'];fmt=lambda x:'not crossed' if x is None else f'{x:+.3f}'
        rows.append([f"{e['kappa']:.1f}",f"{v['attenuation_factor']:.3f}",f"{fmt(v['shift_fixed'])} / {fmt(v['shift_rescaled'])}"])
    table(rows,[110,140,250])
    p(f"Two nine-point cuts use h=0.1 to 1.3 (step 0.15), four-layer VQE and the same noise placement. Rescaling brings crossings within 0.037 of their p=0 positions; sparse threshold interpolation is not a phase-transition proof. Preparation-energy errors are {large['preparation_energy_error']['mean']:.3f} mean and {large['preparation_energy_error']['max']:.3f} maximum. Full data and plots are in the notebook.")
    p('5. Independent diagnostic and mitigation','Heading2')
    f=second['fidelity_susceptibility'];z=second['zero_noise_extrapolation']
    p(f"Fidelity susceptibility in one fixed translation-invariant, spin-flip-even sector (h=0 excluded) locates peaks a mean {f['mean_abs_deviation_from_analytic']:.3f} in h from the analytic reference, at spacing {f['grid_spacing_in_h']:.3f}. Its mean gap to clustering is {f['mean_abs_gap_to_clustering']:.3f}; the methods do not agree within one grid step on average.")
    p(f"Two-point exponential zero-noise extrapolation reduces C1/C2 errors from {z['mean_abs_error_before']['zz1']:.3f}/{z['mean_abs_error_before']['zz2']:.3f} to {z['mean_abs_error_after']['zz1']['exponential']:.4f}/{z['mean_abs_error_after']['zz2']['exponential']:.4f}, relative to the same noiseless variational state. These infinite-shot results do not assess finite-shot error amplification or exact-ground-state recovery.")
    story.append(PageBreak())
    p('6. Shared readout and a fair measurement budget','Heading2');fig('budget_study.png',490)
    p('One shot measures the whole register in Z. The same bitstring supplies both C1 and C2, each averaged over N sites. A ping draws 100 joint outcomes from the exact computational-basis distribution of its prepared state. Multinomial sampling preserves physical bounds, per-shot variance and covariance; it neither splits shots nor reuses clean-state widths for noisy states. Recovered N=8 fits are checked against every archived mean and energy.')
    p('Random, grid, bisection and adaptive methods use exactly 6, 10, 16, 24, 36 or 50 pings, with 200 seeds per budget. A fixed max(C1,-C2)>0.46 rule supplies votes; three-nearest weighted voting reconstructs the map. Scores use stage cluster labels, excluding reference floating cells. Shading is one standard deviation across seeds, not a confidence interval.')
    rows=[['16 pings','Random','Grid','Bisect','Adaptive']]
    for name in ['Clear skies','Static','Whiteout']:rows.append([name]+[f"{100*budget[name][m]['16']['mean']:.1f}%" for m in ['random','grid','bisect','adaptive']])
    table(rows,[120,95,95,95,95])
    for stage,methods in budget['pings_to_reach_90pct'].items():
        p(stage+': first tested 90% crossing - '+', '.join(f'{m}: {b if b is not None else "not reached"}' for m,b in methods.items())+'.')
    p(f"{len(budget['borderline_crossings'])} tested means lie within two standard errors of 90%; their crossing budgets are provisional. Cross-stage comparisons also mix state preparation and classification, so they do not isolate a universal noise overhead.")
    p('7. Play, reproduce and extend','Heading2')
    p('Open game/index.html. Practice/Hunter provide 90/60 energy. Weak/solid/deep scans use 20/100/500 whole-register shots for 1/2/4 energy. The AI visibly scans the same map and budget; its five-handle interpolation differs from the study reconstruction. Twelve famous GIFs, personal recordings and short lessons reward meaningful events. Retry keeps the map and AI target.')
    p('Limitations: finite rings, heuristic classifiers, unresolved floating phase, imperfect VQE fits and no hardware or quantum-advantage claim. Team Popeyes is solo: Tanish Singh Rajpal. The presentation video remains to be recorded. README.md contains the current UI captures, reproducible commands and links to validation data.')
    p('Sources: Quantum Coalition QSITE-2026 Scientific Track handout/starter kit; PennyLane ANNNI tutorial, computational-basis probabilities and DepolarizingChannel documentation. See README.md for direct links.')
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#546573'));canvas.drawString(51,28,'PHASE HUNTER | TEAM POPEYES | SCIENTIFIC TRACK');canvas.drawRightString(561,28,str(doc.page))
    SimpleDocTemplate(str(ROOT/'docs/Phase_Hunter_Writeup.pdf'),pagesize=(612,792),rightMargin=51,leftMargin=51,topMargin=36,bottomMargin=43).build(story,onFirstPage=footer,onLaterPages=footer)
    print('Wrote docs/Phase_Hunter_Writeup.pdf')
if __name__=='__main__':main()
