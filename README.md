# MembraneIQ

**MembraneIQ** is a dairy membrane health, fouling, cleaning-recovery, and lifecycle intelligence prototype.

The project is being built in stages, with every metric tied to an explicit engineering calculation or validated model rather than a decorative AI score.

## Current capabilities

### v0.1 — Core health engine

- Generate realistic simulated UF/RO process data.
- Establish a clean operating baseline.
- Calculate TMP, flux, permeability, normalized permeability, pressure drop, and rejection.
- Detect progressive performance deterioration.
- Quantify recovery after CIP.
- Produce a transparent membrane-system health assessment.

### v0.2 — Membrane Health Records

The current development branch adds persistent condition history for membrane assets and stage/vessel tracking.

A health record can retain:

- asset identity and location
- installation metadata
- operating hours
- condition snapshots
- normalized permeability deterioration
- TMP and pressure-drop changes
- CIP count
- CIP recovery history
- inspection/replacement events
- current health state
- estimated degradation rate

Stage and vessel summaries can then identify which part of a membrane train deserves attention first.

> Important: MembraneIQ only reports health at the finest resolution actually supported by the available measurements. The software does not claim that conventional skid-level instrumentation can magically diagnose an individual membrane element.

## Engineering architecture

```text
Process / simulated data
        ↓
Engineering calculations
        ↓
Clean baseline
        ↓
Health + fouling assessment
        ↓
CIP recovery analysis
        ↓
Membrane Health Record
        ↓
Stage / vessel condition tracking
        ↓
Future RUN / CLEAN / INSPECT / REPLACE engine
```

## Core calculations

- Transmembrane pressure (TMP)
- Flux
- Permeability
- Temperature-normalized permeability
- Feed-side pressure drop
- Conductivity rejection
- Post-CIP permeability recovery
- Recent degradation/fouling trend

## Included simulation scenarios

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
- v0.1 process inference is primarily skid/system level.
- v0.2 stage/vessel records provide the data model and aggregation framework; real localization requires suitable instrumentation.
- Fouling mechanism classification is not yet implemented.
- Remaining useful life is not yet implemented.
- Economic optimization is not yet implemented.

## Roadmap

### v0.2 — Membrane Health Records + stage/vessel tracking
- persistent asset condition history
- stage/vessel summaries
- CIP recovery history
- asset attention ranking
- multi-run histories

### v0.3 — Predictive condition intelligence
- statistical anomaly detection
- fouling-rate model
- remaining useful run-time estimate
- abnormal deterioration detection

### v0.4 — Decision support
- RUN / CLEAN / INSPECT / REPLACE logic
- economic cost model
- cleaning-timing optimization

### Later research
- fouling fingerprint classification
- improved localization
- retrofit sensing
- individual membrane-level condition inference where instrumentation supports it
- real/anonymized dairy validation

## Disclaimer

This project is an engineering research prototype and is not intended to make production, food-safety, or equipment-maintenance decisions without validation by qualified personnel and appropriate plant procedures.
