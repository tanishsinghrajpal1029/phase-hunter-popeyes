"""Build the results narrative and tables from verified result files."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 load=lambda name:json.loads((ROOT/'data'/name).read_text())
 clean=load('summary.json');noise=load('noise_analysis.json');size=load('commensuration.json')
 budget=load('budget_study.json');large=load('large_n_cut_analysis.json');second=load('second_method.json');readout=load('readout_validation.json')
 comparison=load('comparison.json')
 maprows='\n'.join(f"| {name.capitalize()} | {100*r['ordered_area']:.2f}% | {100*r['agreement_to_clean']:.2f}% | {r['signal_mae']:.4f} |" for name,r in comparison['maps'].items())
 interiorrows='\n'.join(f"| {r['label']} | {r['points']} | {100*r['signal_loss']:.2f}% | {100*r['area_loss']:.2f}% |" for r in comparison['interiors'])
 shotrows='\n'.join(f"| {r['shots']} | {r['total_shots_per_map']:,} | "+' | '.join(f"{r[name]['mae']:.4f} ± {r[name]['mae_sd']:.4f}" for name in ['noisy','low_noise','corrected'])+' |' for r in comparison['finite_shots']['results'])
 stages=['Clear skies','Static','Whiteout'];methods=['random','grid','bisect','adaptive']
 sizes='\n'.join(f"| {r['qubits']} | {'Yes' if r['period_four_fits'] else 'No'} | {r['zz2']:.3f} | {100*r['agreement_excluding_floating']:.1f}% |" for r in size['rows'])
 areas='\n'.join(f"| {p} | {100*r['fixed_rule']['ordered']:.2f}% | {100*r['recalibrated']['ordered']:.2f}% |" for p,r in noise['phase_areas'].items())
 scores='\n'.join('| '+stage+' | '+' | '.join(f"{100*budget[stage][m]['16']['mean']:.2f}%" for m in methods)+' |' for stage in stages)
 crossings='\n'.join('| '+stage+' | '+' | '.join(str(budget['pings_to_reach_90pct'][stage][m] or 'Not reached') for m in methods)+' |' for stage in stages)
 borderline='\n'.join(f"| {r['stage']} | {r['strategy']} | {r['budget']} | {100*r['mean']:.2f}% | {100*r['standard_error']:.2f} pp |" for r in budget['borderline_crossings']) or '| None | — | — | — | — |'
 fmt=lambda v:'No crossing' if v is None else f'{v:.3f}'
 cutrows='\n'.join(f"| {e['kappa']:.1f} | {p[1:]} | {r['attenuation_factor']:.3f} | {r['mean_residual_after_rescaling']:.4f} | {fmt(r['shift_fixed'])} | {fmt(r['shift_rescaled'])} |" for e in large['cuts'].values() for p,r in e['noise'].items())
 residuals=[v['mean_residual_after_rescaling'] for e in large['cuts'].values() for v in e['noise'].values()]
 shifts=[abs(v['shift_rescaled']) for e in large['cuts'].values() for v in e['noise'].values() if v['shift_rescaled'] is not None]
 quality=noise['vqe_quality'];fidelity=second['fidelity_susceptibility'];zne=second['zero_noise_extrapolation']
 text=f'''# Phase Hunter

**Team Popeyes (Lead): Tanish Singh Rajpal**

Members: Paul Jeon, Sumedhaa Ruhil.

Q-SITE 2026 · Quantum Coalition Scientific Track

Carnegie Mellon University, Information Networking Institute

**[Play the game](game/index.html)** — scan a hidden quantum phase map, spend a finite measurement budget, and try to beat the AI.

![Phase Hunter nautical interface with measured points and an educational reaction](figures/gameplay.png)

The game exposes a real inference problem: how much can you learn about a quantum magnet from a small number of noisy measurements? Drag five boundary handles, reveal your map score, and retry the same map to improve your strategy. No build step or account is needed.

<details>
<summary>Watch a current gameplay recording</summary>

![A round in the current nautical interface](figures/gameplay.gif)

</details>

## Submission artifacts

- [Executed scientific notebook](phase_hunter.ipynb): model checks, commensuration, noisy inference, shared readout, strategy comparisons, fidelity, mitigation and N=12 cuts.
- [Three-page writeup](docs/Phase_Hunter_Writeup.pdf).
- [Playable browser experiment](game/index.html).
- Presentation video: still to be recorded.
- Team roster: **Team Popeyes — Tanish Singh Rajpal, Paul Jeon, Sumedhaa Ruhil**.

## Questions and contributions

1. **Does the ring fit the order?** A six-spin ring frustrates the period-four stripe and strongly degrades the same classifier's reference agreement.
2. **What does gate noise change?** Separate signal attenuation from the response of a fixed or recalibrated inference rule.
3. **How should a player spend measurements?** Compare four strategies at exact equal budgets, using shared whole-register shots and 200 seeds.
4. **Does the noise observation extend to a larger ring?** Test two completed noisy cuts at N=12, including preparation error and threshold shifts.
5. **Can another diagnostic corroborate the map?** Compare fidelity-susceptibility peaks with clustering, and quantify where they disagree.

The underlying quantum states are simulated classically. There is no hardware result, quantum-speedup claim, or claim that this game is impossible classically.

## Model and observables

The periodic axial next-nearest-neighbour Ising model is

`H = -Σ ZᵢZᵢ₊₁ + κ Σ ZᵢZᵢ₊₂ - h Σ Xᵢ`.

The scan spans κ∈[0,1] and h∈[0,2]. Two site-averaged observables provide the fingerprint:

| Observable | Interpretation |
|---|---|
| C1 = meanᵢ ⟨ZᵢZᵢ₊₁⟩ | Large positive values indicate neighboring spins align. |
| C2 = meanᵢ ⟨ZᵢZᵢ₊₂⟩ | Large negative values identify the ++-- stripe signature. |
| Both small | Weak Z correlations, characteristic of the paramagnetic region. |

Three seeded k-means clusters start in known phase interiors. The analytic floating-band reference is excluded from primary scoring because the classifier does not independently detect it. Finite-size label agreement should not be confused with a thermodynamic transition measurement.

### Clean N=8 diagram

The 40×40 PennyLane grid contains 1,600 exact ground states. Agreement with the handout's reference is **{100*clean['accuracy_excluding_floating']:.2f}% excluding floating cells**, or **{100*clean['accuracy_all_cells']:.2f}% over all cells**. An independent NumPy implementation agrees to approximately 3×10⁻¹⁴ in energies and correlators.

![Clean phase diagram](figures/clean_phase_diagram.png)

### Commensuration: the distinctive six-spin failure

A perfect period-four `++--` stripe closes on a ring only when N is divisible by four. On N=6, enumeration gives the strict bound **C2 ≥ −1/3** for every Z-basis bitstring; a quantum expectation is a convex average and obeys the same bound. For N=8 and N=12 the lower bound is −1.

At the same antiphase-interior point, **κ={size['kappa']}, h={size['h']}**, the exact ground-state values and matched-grid classifier scores are:

| Ring size | Period four fits? | C2 | 24×24 reference agreement |
|---|---|---:|---:|
{sizes}

![Commensuration signal and matched-grid classification scores](figures/commensuration.png)

The N=6 result is finite-ring frustration and a limitation of this correlation-based classifier. It does **not** mean that the infinite-model antiphase disappears. Choose N divisible by four when testing an unfrustrated stripe; other sizes are useful controlled frustration experiments. These 24×24 game-grid scores differ from the denser 40×40 headline metric above.

[Quantitative data](data/commensuration.json) · Rebuild with `python scripts/analyse_size.py`.

## Gate noise: signal attenuation versus classification

The saved 24×24 N=8 scan fits a four-layer RY/RZ and CNOT-ring ansatz on `default.qubit`. Identical parameters are evaluated on `default.mixed` at p=0, 0.01 and 0.05. A target `DepolarizingChannel(p)` follows every CNOT. Keeping the prepared state fixed across noise strengths separates channel effects from preparation differences within each point.

| Noise p | Ordered area: fixed clean rule | Ordered area: recalibrated rule |
|---|---:|---:|
{areas}

A fixed classifier labels about **39% less area as ordered at p=0.05**. Recalibration recovers most area, with small boundary changes: the cut near κ=0.30 shifts one h-grid step. This establishes sensitivity of inferred labels to noisy observables, not invariance of physical transitions under noise.

![Noise comparison](figures/phase_diagrams_noise.png)

The selected antiphase interior loses about 47% of its order parameter versus 40% for the ferromagnetic interior, and the independent N=12 cuts reproduce the ordering (attenuation 0.512 against 0.615 at p=0.05). The likely mechanism: the antiphase order parameter lives on the distance-2 correlator, which has more gates between the two spins being compared, so the same per-gate error costs it more. The handout predicts this and both ring sizes are consistent with it, but we did not isolate distance as the cause — that would need a third correlator distance or a circuit-depth sweep, which we did not run.

Preparation remains imperfect: mean energy error **{quality['energy_error_mean']:.3f}**, maximum **{quality['energy_error_max']:.3f}**, and **{quality['points_above_0_05']}/576** points above 0.05. Mean correlator errors versus exact states are 0.027 and 0.042. Future scans retain the better warm/cold fit and save parameters; the archived expectation values used here remain unchanged.

## Whole-register shots: use all the information

Both correlators are diagonal in Z. A single shot measures the full register and produces one bitstring z. From it compute `C_d(z) = (1/N) Σ zᵢzᵢ₊d` for **both** distances.

- Every one of the 20, 100 or 500 shots contributes to both estimates.
- Site averaging is performed within each readout; sites are not assumed independent.
- Bitstrings with identical (C1,C2) are grouped into joint outcomes without losing information about these observables.
- A ping samples multinomial counts over those outcomes. Estimates remain bounded, and the shared-shot covariance is retained.
- The ping covariance is the per-shot covariance divided by the shot count.

Two independent binomials would discard the joint statistics. Likewise, borrowing clean-state standard deviations for noisy states is not justified. The notebook compares against a random-pair protocol that splits preparations between distances and discards simultaneous readouts and spatial averaging.

The noisy archive originally saved only means. `recover_readout.py` replays its deterministic fits, verifies each saved energy and noisy mean, then stores circuit parameters and joint outcome probabilities. Maximum recovery discrepancy is **{readout['max_recovery_difference']:.2g}**. No target accuracy was used to tune these distributions.

[Readout validation](data/readout_validation.json) · [Recovered distributions](data/readout_N8.npz) · [Sampling implementation](src/measurement.py).

## Measurement-budget study

Random, grid, bisection and adaptive sampling each receive exactly **6, 10, 16, 24, 36 or 50 pings**, at **100 whole-register shots per ping**, across **200 seeds**. Grid fills its entire budget; bisection distributes leftover scans across columns.

A fixed heuristic `max(C1,-C2)>0.46` labels each measurement. Three-nearest weighted voting reconstructs the map. Scores compare with each stage's cluster labels, excluding reference floating cells. This reconstruction differs from the game's five-handle line.

![Whole-register budget study](figures/budget_study.png)

| Stage, 16 pings | Random | Grid | Bisection | Adaptive |
|---|---:|---:|---:|---:|
{scores}

### First tested budget reaching 90% mean agreement

| Stage | Random | Grid | Bisection | Adaptive |
|---|---:|---:|---:|---:|
{crossings}

These are crossings on a coarse budget ladder, not interpolated minimum costs or guarantees for an individual run. A strategy need not improve monotonically at every tested budget. Cross-stage changes mix noise, preparation and stage-specific classification; they do not isolate universal noise overhead.

### Borderline crossings

Any tested mean within **two standard errors of 90%** is flagged below, including points just below the line. Standard error is `sample SD / sqrt(200)`. Plot shading is **one standard deviation across runs**, not a confidence interval for the mean. The two-SE flag is an uncertainty screen, not a simultaneous confidence guarantee across all comparisons.

| Stage | Strategy | Pings | Mean | Standard error |
|---|---|---:|---:|---:|
{borderline}

[Full results and protocol](data/budget_study.json). Grid, bisection and adaptive sampling first reach 90% at 24 pings in Whiteout; random sampling remains below 90% through 50 pings, although its final mean is borderline. In Clear skies, all three structured strategies first cross at 24 versus 36 for random, whose crossing is also borderline.

## Larger-system extension: noisy N=12 cuts

The completed run contains **18 points: two nine-point cuts** at κ=0.2 and κ=0.8, h=0.1…1.3 with spacing 0.15. The four-layer variational circuit uses the same target-channel placement as N=8. This tests whether attenuation and inference sensitivity persist at larger N without claiming a full noisy N=12 phase diagram.

Fit one attenuation factor α per cut, then compare a fixed 0.46 threshold with the rescaled threshold α×0.46. Shifts below are relative to the same cut's p=0 crossing; a negative shift means a lower h. “No crossing” means the fixed threshold was not crossed in the sampled interval.

| κ | p | Attenuation α | Mean rescaling residual | Fixed shift Δh | Rescaled shift Δh |
|---:|---:|---:|---:|---:|---:|
{cutrows}

![N=12 noisy cuts with fixed and rescaled thresholds](figures/large_n_cut.png)

Across the four cut/noise combinations, the largest mean residual after rescaling is **{max(residuals):.4f}** and the largest available absolute rescaled-crossing shift is **{max(shifts):.3f} in h**, compared with spacing 0.15. This supports approximate attenuation of these sampled observables to the extent shown by those residuals; it does not prove invariant thermodynamic boundaries.

N=12 preparation-energy errors are **{large['preparation_energy_error']['mean']:.3f} mean** and **{large['preparation_energy_error']['max']:.3f} maximum**. Sparse interpolation, the chosen threshold and remaining fit error limit interpretation. This completed larger-system noise experiment is the evidence relevant to the rubric extension; credit is the judges' decision.

[Raw cuts](data/large_n_cut.json) · [Analysis](data/large_n_cut_analysis.json) · `python scripts/large_n_cut.py --analyse-only`.

## Independent diagnostic and mitigation

Fidelity susceptibility is calculated in a fixed translation-invariant, spin-flip-even sector, excluding h=0 from the stencil. For h>0 the unique positive ground state lies in this sector, avoiding arbitrary near-degenerate symmetry partners. No classifier labels enter the calculation.

Mean peak deviation from the analytic reference is **{fidelity['mean_abs_deviation_from_analytic']:.3f} in h**, at spacing **{fidelity['grid_spacing_in_h']:.3f}**. Mean disagreement with clustering is **{fidelity['mean_abs_gap_to_clustering']:.3f}**: the methods do not agree within one grid step on average.

![Independent diagnostic and mitigation](figures/second_method.png)

Two-point exponential extrapolation from p=0.01 and 0.05 reduces mean C1/C2 errors from **{zne['mean_abs_error_before']['zz1']:.3f}/{zne['mean_abs_error_before']['zz2']:.3f}** to **{zne['mean_abs_error_after']['zz1']['exponential']:.4f}/{zne['mean_abs_error_after']['zz2']['exponential']:.4f}**. The target is the **same variational state at p=0**, not the exact ground state. This infinite-shot experiment does not test finite-shot error amplification, unknown noise or hardware performance.

## Clean, noisy and corrected: interactive comparison

Select **Compare noise** in the game to see the three maps side by side, with an optional clean-boundary overlay. Every panel uses the same archived 24×24 N=8 variational circuit scan and the same three centroids fitted once on its p=0 signals. The corrected map uses the archived two-point **exponential** estimator, with its existing linear fallback; the maps show infinite-shot expectations. Agreement below means matching the clean circuit's labels, not agreement with the exact ground state or analytic phase boundaries.

| Map | Classified ordered area | Agreement with clean labels | Mean C1/C2 absolute error |
|---|---:|---:|---:|
{maprows}

The corrected labels match every clean label on this finite grid, although its signal error remains nonzero. This does not establish exact state recovery or a thermodynamic boundary. The exponential model is also imperfect for small signals that change sign between noise levels; the downloadable results include these diagnostics.

### Why signal loss and map-area loss differ

At p=0.05, compare predefined interior patches with each phase's full classified area:

| Phase | Interior points | Interior signal loss | Classified area loss |
|---|---:|---:|---:|
{interiorrows}

The ferromagnetic patch uses mean |C1| at κ<0.3, 0.1<h<0.4; the antiphase patch uses mean |C2| at κ>0.8, 0.1<h<0.4. Signal loss is one minus the ratio of these noisy and clean means. Area loss is relative to that phase's clean area over the whole grid.

The stripe signal weakens more, but the ferromagnetic labeled region shrinks more. Labels depend on **both correlators and their distance from the frozen classifier's decision boundaries**. Interior attenuation alone cannot tell how many grid points cross those boundaries. This explains why the two metrics can disagree; it does not isolate spin separation as the cause of the different circuit responses or show that a physical phase disappears.

### Finite shots: an equal-budget correction test

The comparison also includes a separate **linear** extrapolation experiment on all 576 grid points, with 200 independent seeded repetitions. Each method receives B total whole-register shots per point. The two uncorrected baselines spend all B shots at p=0.05 or p=0.01. Correction splits B/2 at each setting and computes `1.25 C(0.01) − 0.25 C(0.05)` without clipping. Both C1 and C2 come from every shot, retaining their covariance. The split is fixed, not optimized.

The target and classifier remain the same archived p=0 circuit. Values are the full-grid mean absolute C1/C2 error **± one standard deviation across repetitions**:

| Total shots per point | Total shots per map, per method | No correction, p=0.05 | Lower noise only, p=0.01 | Linear correction |
|---:|---:|---:|---:|---:|
{shotrows}

Correction lowers signal error relative to p=0.05 at every tested budget. At 20 shots, spending all shots at p=0.01 is better. At 100 shots, correction has a small signal-error advantage over p=0.01 but **lower phase-label agreement**; at 500 shots its signal-error advantage grows while the phase-agreement difference is inconclusive. Better signal estimation and better classification are distinct outcomes.

The methods share half-batches for paired comparisons while each retains its B-shot marginal distribution. [Full results](data/comparison.json) report per-method means, SDs and SEs, plus paired mean differences and approximate 95% intervals (`mean ± 1.96 SE`). These intervals describe sampling variation for this fixed archive. The study assumes known noise settings with equal per-shot cost, excludes the cost of clean reference/classifier calibration, and does not test unknown noise or hardware. It tests linear correction, not the exponential estimator used by the maps above.

Rebuild the JSON and browser data with `python3 scripts/make_comparison.py`; this uses only NumPy and the shipped archives, with no VQE rerun. Run the focused scientific checks with `python3 -m unittest discover -s tests -p test_comparison.py`.

## Play, learn and replay

Five stages cover clean N=8, N=8 with 1% or 5% gate noise, frustrated clean N=6, and clean N=12. The N=12 game stage is clean; the larger-system noisy cuts above are a separate scientific experiment.

Practice supplies labels and 90 energy; Hunter removes hints and supplies 60. Weak/solid/deep scans cost 1/2/4 energy for 20/100/500 shots. The AI spends the same energy on the same map: 45 solid scans in Practice or 30 in Hunter. Its scans animate and remain visible until **Your turn — same map** restores the player's budget. Retry preserves the target; New map clears it.

On a first visit, a short guided round opens on a clean map: three scans, one boundary guess, then the result. The advanced controls stay tucked away until the first reveal, and the intro can be replayed from the controls whenever the demo needs a reset.

After revealing, **Why noise changes the map** opens the interactive clean/noisy/corrected comparison and its finite-shot study. Returning players can replay the first voyage or skip directly to the full controls.

**Start presentation demo** selects the full clean N=8 game map, fixes scans at 100 shots, seeds the measurements for repeatability and turns reactions off. Both player and AI receive **45 scans × 100 shots = 4,500 shots per side**. Restarting the fixed map repeats the demonstration; exiting restores the saved play preferences. The game score is labeled as reference-map agreement. The comparison's clean panel instead uses the variational circuit archive described above.

The nautical theme uses chart paper, navy controls, sailor-red actions and spinach-green selections. Phase colors retain their scientific meaning.

The game canvas scales its backing resolution with the display's device-pixel ratio so labels stay sharp on high-density screens. The vertical **Field strength (h)** title has its own margin outside the tick labels. Comparison maps use SVG axes and labels.

**Personal memes** and **Famous meme GIFs** have independent switches. Both default on, alternating where both fit. Twelve GIFs and twenty-seven contextual captions attach short lessons to meaningful events. SUIII celebrates measured three-star results or AI wins; a no-scan reveal gets confused Travolta. Common events rotate through variants. Popeye supplies three fallback stills with thirteen captions.

<details>
<summary>Preview the current reaction library</summary>

![Current GIF reactions and learning tips](figures/memes.gif)

</details>

The original personal recordings remain available. **Memes: off** removes reaction popups and result artwork; reduced-motion mode uses still GIF previews and manual personal playback. Media are credited separately from the software license: [GIF credits](game/assets/famous/CREDITS.md), [Popeye credits](game/assets/popeye/CREDITS.md).

## Reproduce

Use a fresh Python environment with `requirements.txt`; Jupyter is optional for opening the notebook interactively. The notebook builder executes and embeds every code cell without requiring Jupyter.

```bash
python -m pip install -r requirements.txt
python scripts/run_pennylane.py --check --qubits 8
python scripts/make_stages.py
python scripts/analyse_size.py
python scripts/analyse_noise.py --qubits 8
python scripts/budget_study.py
python scripts/second_method.py
python3 scripts/make_comparison.py
python scripts/large_n_cut.py --analyse-only
python scripts/write_readme.py
python scripts/build_notebook.py
python scripts/make_writeup.py
python -m unittest discover -s tests -v
python3 -m unittest discover -s tests -p test_comparison.py
node tests/test_game.cjs
```

The shipped readout and exact-state caches make stage regeneration inexpensive. To independently recover the archived noisy distributions, remove the relevant recovery cache/output in a working copy and run:

```bash
python scripts/recover_readout.py --workers 2
```

This is the expensive step: it replays VQE preparation, checks every archived energy and mean, and writes resumable checkpoints. The output records its source archive hash. To rebuild the clean headline grid, run `python scripts/make_dataset.py --qubits 8 --grid 40 --backend pennylane`, then `python scripts/make_figures.py`.

To record the current interface:

```bash
python -m pip install playwright pillow
python -m playwright install chromium
python scripts/make_gifs.py
```

The recorder uses stable control IDs and measured element bounds, validates non-static frames, and writes `figures/gameplay.png`, `figures/gameplay.gif` and `figures/memes.gif`.

## Validation and limits

[Validation record](data/validation.json) documents Hamiltonian equality, clean-grid cross-checks and the archived scan hash. [Readout validation](data/readout_validation.json) documents recovered-state agreement. These are records tied to specific inputs, not automatically refreshed certificates.

Tests cover joint sampling means/variance/covariance, exact budgets, ring-size bounds, basis-invariant fidelity, better-fit persistence, visible AI progress, same-map handoff, reaction switches and victory conditions.

The comparison checks additionally verify the source archive and recovered means, fixed classifier identities, exponential-estimator parity, linear-estimator covariance, unclipped extrapolates, seeded reproducibility and matching browser/JSON exports.

Remaining limitations: unresolved floating phase; finite-ring and VQE bias; heuristic inference rules; sparse larger-system cuts; the finite-shot correction study is restricted to the archived N=8 circuit, known noise and a fixed shot split; no hardware run or quantum advantage. The presentation video remains to be recorded.

## Sources

- [Quantum Coalition Scientific Track handout and starter kit](https://github.com/benmcdonough20/QSITE-2026-QuantumCoalition/tree/main/Scientific%20Track).
- [PennyLane ANNNI tutorial](https://pennylane.ai/qml/demos/tutorial_annni).
- [Computational-basis probabilities (`qml.probs`)](https://docs.pennylane.ai/en/stable/code/api/pennylane.probs.html).
- [PennyLane DepolarizingChannel](https://docs.pennylane.ai/en/stable/code/api/pennylane.DepolarizingChannel.html).
'''
 (ROOT/'README.md').write_text(text);print('Wrote README.md from current results')
if __name__=='__main__':main()
