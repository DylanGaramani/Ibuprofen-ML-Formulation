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
The presented work investigates critical aspects of rational formulation design through machine learning (ML) methodology to identify essential patterns in immediate release ibuprofen oral dosage products influencing its pharmacokinetic profile. Registry data were extracted and standardized into a consistent format using pandas (v1.3.5) in Python 3.9, with special attention to variant nomenclature for identical excipients. Patterns regarding the usage of dissolution-modifying excipients as well as ibuprofen variants were used to investigate their influence on clinical pharmacokinetic profile. Film coated tablets emerged as the most common immediate release dosage form of ibuprofen utilizing ibuprofen acid as the active ingredient and sodium lauryl sulfate as surfactant/wetting agent. Ibuprofen special variants, such as ibuprofen sodium dihydrate, ibuprofen lysine and ibuprofen arginine, offer more rapid drug release and onset with significantly reduced tmax and increased Cmax as well as generally lower bioavailability variance compared to standard immediate release ibuprofen oral dosage forms. The approaches presented in this article will be helpful in better understanding of rational formulation strategies and support regulatory scientific decisions ensuring predictable bioavailability and reproducible clinical responses.

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
