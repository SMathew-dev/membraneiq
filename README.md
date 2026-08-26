# MembraneIQ v0.1

**MembraneIQ** is a dairy membrane health and fouling intelligence prototype.

The v0.1 goal is intentionally narrow:

1. Generate realistic simulated UF/RO process data.
2. Establish a clean membrane baseline.
3. Calculate engineering indicators such as TMP, flux, permeability, normalized permeability, pressure drop, and rejection.
4. Detect progressive fouling.
5. Quantify recovery after CIP.
6. Produce a defensible membrane-system health score.

This version is **not** a polished dashboard and does not pretend to diagnose individual membrane elements when the available instrumentation would not support that resolution.

## Why this project exists

Industrial membrane systems are often judged using a mixture of operating thresholds, trends, cleaning history, and operator experience. MembraneIQ explores whether process data can be turned into a consistent health record that supports future **RUN / CLEAN / INSPECT / REPLACE** decisions.

## v0.1 architecture

```text
Synthetic Dairy UF/RO Simulator
        ↓
Engineering Calculations
        ↓
Clean Baseline
        ↓
Health / Fouling Engine
        ↓
CIP Recovery Analysis
        ↓
MembraneIQ Assessment
```

## Calculated variables

- Transmembrane pressure (TMP)
- Flux
- Permeability
- Temperature-normalized permeability
- Pressure drop
- Conductivity rejection

## Health score

The prototype combines deterioration relative to the clean baseline across normalized permeability, TMP, pressure drop, rejection, recent fouling trend, and latest CIP recovery.

The v0.1 health score is a **transparent engineering heuristic**, not an AI-generated number.

## Included scenarios

- healthy operation
- gradual fouling
- severe fouling
- successful CIP recovery
- incomplete CIP recovery
- repeated deterioration

## Run

```bash
pip install -r requirements.txt
python -m membraneiq.demo
```

Run tests:

```bash
pytest
```

## Current limitations

- Data are simulated.
- Health is currently calculated at skid/system level.
- Fouling mechanism classification is not yet implemented.
- Remaining useful life is not yet implemented.
- Economic optimization is not yet implemented.
- No claim is made that individual membrane element health can be inferred without suitable instrumentation.

## Roadmap

### v0.2
- Membrane Passport
- Stage/vessel histories
- Multiple independent runs
- Persistent CIP recovery history

### v0.3
- Statistical anomaly detection
- Fouling-rate model
- Remaining useful run-time estimate

### v0.4
- RUN / CLEAN decision logic
- Economic cost model

### Later research
- Fouling fingerprint classification
- Localization
- Retrofit sensing
- Individual membrane-level health where instrumentation supports it
- Real/anonymized dairy validation

## Disclaimer

This project is an engineering research prototype and is not intended to make production, food-safety, or equipment-maintenance decisions without validation by qualified personnel and appropriate plant procedures.
