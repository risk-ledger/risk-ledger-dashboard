# Risk Ledger — anonymous research release

Risk Ledger is a static academic dashboard that translates three crypto-platform
risk problems into inspectable outputs: leveraged trading costs, copy-trading path
risk, and listed-asset verification.

## Open the research objects

- [Interactive dashboard](https://risk-ledger.github.io/risk-ledger-dashboard/)
- [Run the Chapter 4 analysis in Google Colab](https://colab.research.google.com/github/risk-ledger/risk-ledger-dashboard/blob/main/chapter4_copytrading_analysis_colab.ipynb)
- `chapter4_copytrading_metrics_anonymised.json` — frozen public input for the notebook
- `RELEASE_SHA256SUMS.txt` — SHA-256 checksums for the submitted release artefacts

The dashboard is fully client-side. `index.html` contains the interface,
calculations, data, and embedded evidence needed to run the prototype on a static
host. Its optional walkthrough player connects to Vimeo to stream the public video;
the research calculations and datasets remain local to the page.

## Data and privacy

- Copy-trading snapshot: 200 lead-trader records captured 2026-07-02.
- Fee and asset snapshots: captured 2026-07-16.
- All trader nicknames are partially masked (for example, `Gleason` becomes
  `Gl***son`) and platform account IDs are excluded.
- The Dashboard embeds eight publication-copy interface captures with
  identity-bearing regions irreversibly covered and EXIF metadata removed.
- Raw screenshots and raw source exports are not included in this anonymous release.

All outputs are historical research artefacts, not forecasts or investment advice.
