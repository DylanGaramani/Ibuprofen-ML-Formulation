# Ibuprofen-ML-Formulation

Reproducible code and raw data supporting a retrospective machine-learning analysis of immediate-release ibuprofen formulations.


**Rational formulation design through retrospective machine learning methodology:  
Case study ibuprofen**

**Authors:**  
Dylan Garamani, Erik Sjögren, Albert Mihranyan*  

**Affiliation:**  
Department of Pharmaceutical Biosciences, Uppsala University  

**Corresponding author:**  
Albert Mihranyan (albert.mihranyan@uu.se)

---

## Abstract

This work investigates critical aspects of rational formulation design using machine learning (ML) methodologies to identify essential patterns in immediate-release ibuprofen oral dosage products that influence their pharmacokinetic profiles. Registry data were extracted and standardized into a consistent format using *pandas* (v1.3.5) in Python 3.9, with particular attention to harmonizing variant nomenclature for identical excipients.

Patterns related to the use of dissolution-modifying excipients and ibuprofen variants were analyzed to evaluate their influence on clinical pharmacokinetic behavior. Film-coated tablets emerged as the most common immediate-release dosage form of ibuprofen, predominantly utilizing ibuprofen acid as the active pharmaceutical ingredient and sodium lauryl sulfate as a surfactant/wetting agent. Special ibuprofen variants, including ibuprofen sodium dihydrate, ibuprofen lysine, and ibuprofen arginine, were associated with more rapid drug release and onset, characterized by significantly reduced *t*<sub>max</sub>, increased *C*<sub>max</sub>, and generally lower bioavailability variability compared with standard immediate-release ibuprofen formulations.

The approaches presented here contribute to a deeper understanding of rational formulation strategies and support regulatory and scientific decision-making aimed at ensuring predictable bioavailability and reproducible clinical responses.

**Keywords:** non-steroidal anti-inflammatory drugs; agentic drug development; artificial intelligence; developability classification system; formulation

---

## Scope of this repository

- All **analysis scripts** used for data ingestion, cleaning, feature engineering, modeling, and figure generation are openly available.
- All **raw input data** used in the study are provided.

## Repository structure

- `code/` – complete analysis pipeline (ingestion → cleaning → feature engineering → modeling → analysis)
- `data/raw/` – raw formulation and metadata sources

## Reproducibility

Running the full pipeline regenerates all figures and tables reported in the paper.


## License

This project is released under the MIT License (see `LICENSE`).
