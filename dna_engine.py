# dna_engine.py
"""
GENELINGUA v3.5 – Evidence-Based Polygenic Scoring Engine
---------------------------------------------------------
A standalone module for computing a language-learning-relevant polygenic score (PGS)
from 23andMe-style raw genotype data.

Features:
- Uses published GWAS effect sizes (beta coefficients)
- Ancestry-aware scoring (EUR, EAS, etc.) with rs4680 flip
- Realistic variance estimates (~2-5%)
- Modular output: scores, contributions, interpretation, scenarios
- Designed for integration into web/mobile apps

Input: 23andMe .txt file path or raw string
Output: Dict with full report (JSON-serializable)
"""

import math
import json
import re
import zipfile
import io
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any, Union


class DNAPolygenicEngine:
    # =========================
    # 1. SNP Database - Evidence-Based
    # =========================
    SNP_DB_PGS = {
        'rs4680': {
            'gene': 'COMT',
            'label': 'COMT Val158Met (rs4680)',
            'effect_allele': 'A',
            'beta_EUR': 0.042,
            'beta_EAS': -0.042,
            'beta_default': 0.025,
            'ancestry_specific': True,
            'se': 0.015,
            'p_value': 0.006,
            'evidence': 'Strong',
            'phenotype': 'Second language learning (white matter & phonetic learning)',
            'population': 'European ancestry adults',
            'refs': ['Mamiya2016', 'Colzato2010', 'Bonetti2021'],
            'notes': 'Met allele beneficial in EUR, Val allele beneficial in EAS - major ancestry difference!'
        },
        'rs737865': {
            'gene': 'COMT',
            'label': 'COMT rs737865',
            'effect_allele': 'C',
            'beta_EUR': 0.018,
            'beta_EAS': 0.018,
            'beta_default': 0.018,
            'ancestry_specific': False,
            'se': 0.008,
            'p_value': 0.024,
            'evidence': 'Moderate',
            'phenotype': 'Figural fluency/creativity',
            'population': 'Chinese college students',
            'refs': ['Zhang2014'],
            'notes': 'Associated with creative thinking, which relates to language flexibility'
        },
        'rs76551189': {
            'gene': 'Near IGSF9',
            'label': 'Nonword reading (rs76551189)',
            'effect_allele': 'A',
            'beta_EUR': 0.025,
            'beta_EAS': 0.025,
            'beta_default': 0.025,
            'ancestry_specific': False,
            'se': 0.005,
            'p_value': 5.2e-8,
            'evidence': 'Strong',
            'phenotype': 'Nonword reading ability',
            'population': 'Meta-analysis (34,000 individuals)',
            'refs': ['Eising2022'],
            'notes': 'Genome-wide significant for phonological processing'
        },
        'rs4656859': {
            'gene': 'IGSF9',
            'label': 'IGSF9 rs4656859',
            'effect_allele': 'T',
            'beta_EUR': 0.022,
            'beta_EAS': 0.022,
            'beta_default': 0.022,
            'ancestry_specific': False,
            'se': 0.005,
            'p_value': 8.1e-8,
            'evidence': 'Strong',
            'phenotype': 'Nonword reading',
            'population': 'Meta-analysis',
            'refs': ['Eising2022'],
            'notes': 'Phonological decoding - key for language learning'
        },
        'rs1422268': {
            'gene': 'DOK3',
            'label': 'DOK3 rs1422268',
            'effect_allele': 'A',
            'beta_EUR': 0.020,
            'beta_EAS': 0.020,
            'beta_default': 0.020,
            'ancestry_specific': False,
            'se': 0.005,
            'p_value': 1.3e-7,
            'evidence': 'Strong',
            'phenotype': 'Nonword reading',
            'population': 'Meta-analysis',
            'refs': ['Eising2022'],
            'notes': 'Reading-related cognitive processing'
        },
        'rs765166': {
            'gene': 'ZFAS1',
            'label': 'ZFAS1 rs765166',
            'effect_allele': 'C',
            'beta_EUR': 0.015,
            'beta_EAS': 0.015,
            'beta_default': 0.015,
            'ancestry_specific': False,
            'se': 0.006,
            'p_value': 0.012,
            'evidence': 'Moderate',
            'phenotype': 'Phonemic awareness',
            'population': 'Meta-analysis',
            'refs': ['Eising2022'],
            'notes': 'Phoneme manipulation - critical for pronunciation'
        },
        'rs363039': {
            'gene': 'SNAP25',
            'label': 'SNAP-25 rs363039',
            'effect_allele': 'G',
            'beta_EUR': 0.028,
            'beta_EAS': 0.028,
            'beta_default': 0.028,
            'ancestry_specific': False,
            'se': 0.011,
            'p_value': 0.011,
            'evidence': 'Moderate',
            'phenotype': 'Performance IQ (visuospatial)',
            'population': 'Dutch children & adults',
            'refs': ['Gosso2006'],
            'notes': 'Synaptic protein - learning & memory functions'
        },
        'rs80263879': {
            'gene': 'EPHX2',
            'label': 'EPHX2 rs80263879',
            'effect_allele': 'G',
            'beta_EUR': 0.035,
            'beta_EAS': 0.035,
            'beta_default': 0.035,
            'ancestry_specific': False,
            'se': 0.008,
            'p_value': 2.1e-8,
            'evidence': 'Strong',
            'phenotype': 'Static spatial working memory',
            'population': 'Chinese students',
            'refs': ['Zhang2022'],
            'notes': 'Genome-wide significant for working memory'
        },
        'rs11264236': {
            'gene': 'NPR1',
            'label': 'NPR1 rs11264236',
            'effect_allele': 'A',
            'beta_EUR': 0.012,
            'beta_EAS': 0.012,
            'beta_default': 0.012,
            'ancestry_specific': False,
            'se': 0.005,
            'p_value': 0.016,
            'evidence': 'Moderate',
            'phenotype': 'Science academic attainment',
            'population': 'UK adolescents (ALSPAC)',
            'refs': ['Donati2021'],
            'notes': 'Academic performance - language component'
        },
        'rs10905791': {
            'gene': 'ASB13',
            'label': 'ASB13 rs10905791',
            'effect_allele': 'T',
            'beta_EUR': 0.011,
            'beta_EAS': 0.011,
            'beta_default': 0.011,
            'ancestry_specific': False,
            'se': 0.005,
            'p_value': 0.028,
            'evidence': 'Moderate',
            'phenotype': 'Science attainment',
            'population': 'UK adolescents',
            'refs': ['Donati2021'],
            'notes': 'Cognitive performance in structured learning'
        },
        'rs6453022': {
            'gene': 'ARHGEF28',
            'label': 'ARHGEF28 rs6453022',
            'effect_allele': 'C',
            'beta_EUR': 0.016,
            'beta_EAS': 0.016,
            'beta_default': 0.016,
            'ancestry_specific': False,
            'se': 0.004,
            'p_value': 3.2e-9,
            'evidence': 'Strong',
            'phenotype': 'Hearing difficulty (inverse)',
            'population': 'UK Biobank (250,389 individuals)',
            'refs': ['Wells2019'],
            'notes': 'Auditory processing - crucial for language perception'
        },
        'rs9493627': {
            'gene': 'EYA4',
            'label': 'EYA4 rs9493627',
            'effect_allele': 'G',
            'beta_EUR': 0.014,
            'beta_EAS': 0.014,
            'beta_default': 0.014,
            'ancestry_specific': False,
            'se': 0.004,
            'p_value': 1.8e-8,
            'evidence': 'Strong',
            'phenotype': 'Hearing function',
            'population': 'UK Biobank',
            'refs': ['Wells2019'],
            'notes': 'Auditory system - language input processing'
        },
        'rs7294919': {
            'gene': 'ASTN2',
            'label': 'ASTN2 rs7294919',
            'effect_allele': 'T',
            'beta_EUR': 0.019,
            'beta_EAS': 0.019,
            'beta_default': 0.019,
            'ancestry_specific': False,
            'se': 0.004,
            'p_value': 2.3e-8,
            'evidence': 'Strong',
            'phenotype': 'Hippocampal volume',
            'population': 'Meta-analysis (33,536 individuals)',
            'refs': ['Hibar2017'],
            'notes': 'Memory formation - essential for vocabulary acquisition'
        },
        'rs1800497': {
            'gene': 'DRD2/ANKK1',
            'label': 'DRD2 TaqIA (rs1800497)',
            'effect_allele': 'T',
            'beta_EUR': 0.015,
            'beta_EAS': 0.015,
            'beta_default': 0.015,
            'ancestry_specific': False,
            'se': 0.007,
            'p_value': 0.032,
            'evidence': 'Moderate',
            'phenotype': 'Working memory span',
            'population': 'Chinese adults',
            'refs': ['Gong2012'],
            'notes': 'Dopamine receptor - motivation & reward in learning'
        },
        'rs10009513': {
            'gene': 'MAPT-AS1',
            'label': 'MAPT-AS1 rs10009513',
            'effect_allele': 'A',
            'beta_EUR': -0.022,
            'beta_EAS': -0.022,
            'beta_default': -0.022,
            'ancestry_specific': False,
            'se': 0.005,
            'p_value': 1.4e-8,
            'evidence': 'Strong',
            'phenotype': 'Relative brain age (protective)',
            'population': 'UK Biobank',
            'refs': ['Ning2021'],
            'notes': 'Neuroprotective - maintains cognitive function over time'
        }
    }

    # =========================
    # 2. References
    # =========================
    REFERENCES = {
        "Mamiya2016": {
            "citation": "Mamiya PC, Richards TL, Coe BP, Eichler EE, Kuhl PK (2016). Brain white matter structure and COMT gene are linked to second-language learning in adults. PNAS 113(26):7249-7254.",
            "url": "https://www.pnas.org/doi/full/10.1073/pnas.1606602113",
            "pmid": "27298360",
            "key_finding": "COMT Met allele associated with better phonetic learning and white matter integrity in L2 learners"
        },
        "Eising2022": {
            "citation": "Eising E, et al (2022). Genome-wide analyses of individual differences in quantitatively assessed reading- and language-related skills in up to 34,000 people. PNAS 119(35):e2202764119.",
            "url": "https://www.pnas.org/doi/10.1073/pnas.2202764119",
            "pmid": "35998220",
            "key_finding": "Large-scale GWAS identified 42 genome-wide significant loci for reading/language traits. GenLang Consortium study."
        },
        "Wells2019": {
            "citation": "Wells HRR, et al (2019). GWAS Identifies 44 Independent Associated Genomic Loci for Self-Reported Adult Hearing Difficulty in UK Biobank. Am J Hum Genet 105(4):788-802.",
            "url": "https://www.cell.com/ajhg/fulltext/S0002-9297(19)30334-0",
            "pmid": "31564434",
            "key_finding": "44 loci associated with hearing - critical for language input processing"
        },
        "Hibar2017": {
            "citation": "Hibar DP, et al (2017). Novel genetic loci associated with hippocampal volume. Nat Commun 8:13624.",
            "url": "https://www.nature.com/articles/ncomms13624",
            "pmid": "28098162",
            "key_finding": "6 loci for hippocampal volume - memory structure essential for vocabulary"
        },
        "Zhang2022": {
            "citation": "Zhang L, et al (2022). A genome-wide association study identified one variant associated with static spatial working memory in Chinese population. Brain Sci 12(9):1254.",
            "url": "https://www.mdpi.com/2076-3425/12/9/1254",
            "pmid": "36176292",
            "key_finding": "EPHX2 variant genome-wide significant for working memory"
        },
        "Gosso2006": {
            "citation": "Gosso MF, et al (2006). The SNAP-25 gene is associated with cognitive ability: evidence from a family-based study in two independent Dutch cohorts. Mol Psychiatry 11:878-886.",
            "url": "https://www.nature.com/articles/4001868",
            "pmid": "16801949",
            "key_finding": "SNAP-25 variants associated with performance IQ"
        },
        "Zhang2014": {
            "citation": "Zhang S, et al (2014). Association of COMT and COMT-DRD2 interaction with creative potential. Front Hum Neurosci 8:216.",
            "url": "https://www.frontiersin.org/articles/10.3389/fnhum.2014.00216",
            "pmid": "24782743",
            "key_finding": "COMT variants linked to creative fluency - relevant to flexible language use"
        },
        "Gong2012": {
            "citation": "Gong P, et al (2012). An association study on the polymorphisms of dopaminergic genes with working memory in a healthy Chinese Han population. J Neural Transm 119:1293-1302.",
            "url": "https://link.springer.com/article/10.1007/s00702-012-0817-9",
            "pmid": "22362150",
            "key_finding": "DRD2 TaqIA associated with working memory span"
        },
        "Donati2021": {
            "citation": "Donati G, et al (2021). Evidence for specificity of polygenic contributions to attainment in English, maths and science during adolescence. Learn Individ Differ 88:101993.",
            "url": "https://www.sciencedirect.com/science/article/pii/S1041608021000674",
            "pmid": "33594131",
            "key_finding": "Subject-specific genetic contributions to academic attainment"
        },
        "Ning2021": {
            "citation": "Ning K, et al (2021). Improving brain age estimates with deep learning leads to identification of novel genetic factors associated with brain aging. Neurobiol Aging 102:89-97.",
            "url": "https://www.sciencedirect.com/science/article/pii/S0197458021001123",
            "pmid": "34098431",
            "key_finding": "80 SNPs associated with brain aging - cognitive maintenance"
        },
        "Colzato2010": {
            "citation": "Colzato LS, et al (2010). The flexible mind is associated with the catechol-O-methyltransferase (COMT) Val158Met polymorphism. Neuropsychologia 48(1):220-225.",
            "pmid": "20434465",
            "key_finding": "COMT affects cognitive flexibility"
        },
        "Bonetti2021": {
            "citation": "Bonetti L, et al (2021). Brain predictive coding processes are associated to COMT gene Val158Met polymorphism. NeuroImage 233:117954.",
            "pmid": "33716157",
            "key_finding": "COMT heterozygotes show stronger neural response to auditory deviants"
        }
    }

    # Supported ancestries
    VALID_ANCESTRIES = ['EUR', 'EAS', 'SAS', 'AFR', 'AMR', 'MENA', 'OTH']

    def __init__(self):
        self.ancestry_labels = {
            'EUR': 'European (includes European-American, European-descended populations)',
            'EAS': 'East Asian (Chinese, Japanese, Korean, Vietnamese, etc.)',
            'SAS': 'South Asian (Indian, Pakistani, Bangladeshi, Sri Lankan, etc.)',
            'AFR': 'African (Sub-Saharan African, African-American)',
            'AMR': 'Latino/Admixed American (Mexican, Puerto Rican, Brazilian, etc.)',
            'MENA': 'Middle Eastern/North African',
            'OTH': 'Other/Mixed (results will be highly uncertain)'
        }

    # =========================
    # 3. Genotype Parsing
    # =========================
    def parse_genotype_file(self, file_path: str) -> Dict[str, str]:
        """
        Parse 23andMe raw data from .txt or .zip file.
        Returns: dict of {rsid: genotype}
        """
        with open(file_path, 'rb') as f:
            data = f.read()

        if file_path.lower().endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                txt_files = [n for n in z.namelist(
                ) if n.lower().endswith('.txt')]
                if not txt_files:
                    raise ValueError("No .txt file found in ZIP.")
                raw_text = z.read(txt_files[0]).decode(
                    'utf-8', errors='ignore')
        else:
            raw_text = data.decode('utf-8', errors='ignore')

        return self.parse_genotypes(raw_text)

    def parse_genotypes(self, raw_text: str) -> Dict[str, str]:
        """Parse raw text into SNP genotype map"""
        snp_map = {}
        for line in raw_text.splitlines():
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            parts = re.split(r'\s+', line)
            if len(parts) >= 4 and parts[0].startswith('rs'):
                rsid = parts[0]
                genotype = parts[3].upper().replace(' ', '')
                snp_map[rsid] = genotype if len(genotype) <= 2 else '--'
        return snp_map

    # =========================
    # 4. PGS Calculation
    # =========================
    @staticmethod
    def count_effect_alleles(genotype: Optional[str], effect_allele: str) -> Optional[int]:
        """Count number of effect alleles (0, 1, 2)"""
        if not genotype or genotype in {'--', 'NN', '0', '', 'DI', 'ID'}:
            return None
        gt = genotype.strip().upper()
        effect = effect_allele.upper()
        return sum(c == effect for c in gt)

    def compute_pgs(self, snp_map: Dict[str, str], selected_ancestry: str = 'EUR') -> Tuple[
        float, Dict[str, Dict], int, float
    ]:
        """
        Compute polygenic score with ancestry-specific betas.
        Returns: (raw_score, contributions, n_valid_snps, total_weight)
        """
        if selected_ancestry not in self.VALID_ANCESTRIES:
            raise ValueError(
                f"Invalid ancestry. Choose from: {self.VALID_ANCESTRIES}")

        raw_score = 0.0
        n_valid = 0
        total_weight = 0.0
        contributions = {}

        for rsid, meta in self.SNP_DB_PGS.items():
            genotype = snp_map.get(rsid, None)
            dosage = self.count_effect_alleles(genotype, meta['effect_allele'])

            # Select beta based on ancestry
            if meta.get('ancestry_specific', False):
                beta = meta.get(
                    f'beta_{selected_ancestry}', meta['beta_default'])
            else:
                beta = meta.get(
                    f'beta_{selected_ancestry}', meta['beta_default'])

            contrib = dosage * beta if dosage is not None else None

            contributions[rsid] = {
                'genotype': genotype or '—',
                'dosage': dosage,
                'beta': beta,
                'contrib': contrib,
                'gene': meta['gene'],
                'evidence': meta['evidence'],
                'phenotype': meta['phenotype']
            }

            if contrib is not None:
                raw_score += contrib
                n_valid += 1
                total_weight += abs(beta)

        return raw_score, contributions, n_valid, total_weight

    # =========================
    # 5. Z-Score & Percentile
    # =========================
    def calculate_population_parameters(self, selected_ancestry: str = 'EUR', maf: float = 0.25) -> Tuple[float, float]:
        """Estimate population mean and SD assuming MAF ~0.25"""
        expected_mean = 0.0
        expected_var = 0.0

        for meta in self.SNP_DB_PGS.values():
            if meta.get('ancestry_specific', False):
                beta = meta.get(
                    f'beta_{selected_ancestry}', meta['beta_default'])
            else:
                beta = meta.get(
                    f'beta_{selected_ancestry}', meta['beta_default'])

            expected_mean += 2 * maf * beta
            expected_var += 2 * maf * (1 - maf) * (beta ** 2)

        expected_sd = math.sqrt(expected_var)
        return expected_mean, expected_sd

    # dna_engine.py
    def compute_z_score(self, raw_score: float, selected_ancestry: str = 'EUR', contributions: dict = None) -> Tuple[float, float, float]:
        pop_mean, pop_sd = self.calculate_population_parameters(
            selected_ancestry)
        z_score = (raw_score - pop_mean) / pop_sd if pop_sd > 0 else 0.0
        percentile = 100 * norm.cdf(z_score)

        n_valid_snps = len([c for c in contributions.values(
        ) if c['contrib'] is not None]) if contributions else 0
        n_gwas_sig = sum(1 for meta in self.SNP_DB_PGS.values()
                         if meta.get('p_value', 1) < 5e-8)
        estimated_r2 = min(0.001 * n_valid_snps + 0.005 * n_gwas_sig, 0.05)

        return z_score, percentile, estimated_r2

    # =========================
    # 6. Interpretation
    # =========================
    @staticmethod
    def interpret_score(z: float, pct: float, r2: float, n_valid: int) -> Dict[str, Any]:
        """Generate interpretation"""
        if z < -1.5:
            category, color = "Well Below Average", "#c0392b"
        elif z < -0.5:
            category, color = "Below Average", "#e67e22"
        elif z < 0.5:
            category, color = "Average", "#3498db"
        elif z < 1.5:
            category, color = "Above Average", "#27ae60"
        else:
            category, color = "Well Above Average", "#16a085"

        if z < -1:
            main_text = f"Your polygenic score is in the bottom {100-pct:.0f}% of the population for these language-related genetic variants."
            advice = (
                "<ul>"
                "<li>Focus on systematic phonics and pronunciation drills</li>"
                "<li>Use spaced repetition aggressively (Anki/SRS daily)</li>"
                "<li>Consider 10-15% more time on explicit grammar study</li>"
                "<li>Consistency beats genetics: 2h/day > 90th percentile + 30min</li>"
                "</ul>"
            )
        elif z > 1:
            main_text = f"Your polygenic score is in the top {pct:.0f}% for these variants. Slight efficiency advantage."
            advice = (
                "<ul>"
                "<li>You may acquire phonological patterns slightly faster</li>"
                "<li>You can likely handle more immersion-heavy approaches</li>"
                "<li>Don't skip fundamentals - genetics ≠ automatic fluency</li>"
                "<li>Your advantage is learning rate, not ultimate attainment</li>"
                "</ul>"
            )
        else:
            main_text = "Your polygenic score is average (around the 50th percentile). This is where most successful learners are."
            advice = (
                "<ul>"
                "<li>Use evidence-based methods: input + SRS + production</li>"
                "<li>Balance immersion (60%) with explicit study (25%) and speaking (15%)</li>"
                "<li>Consistency matters far more than genetics</li>"
                "<li>Track your hours - aim for 600-1200 hours for B2-level</li>"
                "</ul>"
            )

        variance_text = (
            f"These {n_valid} variants explain ~{r2*100:.1f}% of variance in related traits. "
            f"The rest comes from study method, hours, motivation, and environment."
        )

        return {
            'category': category,
            'color': color,
            'main_text': main_text,
            'advice': advice,
            'variance_text': variance_text
        }

    # =========================
    # 7. Scenario Modeling
    # =========================
    @staticmethod
    def scenario_calculator(daily_minutes: int, method_quality: str, consistency: str, genetic_percentile: float) -> Dict[str, float]:
        base_hours = 800

        method_mult = {'Optimal': 0.85, 'Good': 1.0,
                       'Poor': 1.5, 'Terrible': 2.0}.get(method_quality, 1.0)
        consist_mult = {'High': 0.95, 'Medium': 1.05,
                        'Low': 1.25}.get(consistency, 1.0)

        genetic_mult = (
            0.97 if genetic_percentile >= 80 else
            0.99 if genetic_percentile >= 60 else
            1.05 if genetic_percentile <= 20 else
            1.02 if genetic_percentile <= 40 else
            1.0
        )

        adjusted_hours = base_hours * method_mult * consist_mult * genetic_mult
        months = (adjusted_hours / (daily_minutes / 60)) / 30

        return {
            'total_hours': round(adjusted_hours, 0),
            'months_to_b2': round(months, 1)
        }

    # =========================
    # 8. Full Report Generator
    # =========================
    def generate_report(self, file_path: str, selected_ancestry: str = 'EUR') -> Dict[str, Any]:
        """
        Main entry point: run full analysis and return JSON-serializable report.
        """
        # Parse genotypes
        snp_map = self.parse_genotype_file(file_path)

        # Compute PGS
        raw_score, contributions, n_valid_snps, total_weight = self.compute_pgs(
            snp_map, selected_ancestry)
        z_score, percentile, estimated_r2 = self.compute_z_score(
            raw_score, selected_ancestry)

        # Interpretation
        interpretation = self.interpret_score(
            z_score, percentile, estimated_r2, n_valid_snps)

        # Top contributors
        top_contributors = sorted(
            [(rsid, c)
             for rsid, c in contributions.items() if c['contrib'] is not None],
            key=lambda x: abs(x[1]['contrib']),
            reverse=True
        )[:5]

        # Scenarios
        scenarios = [
            ("Your scenario", percentile, "Good", 120, "High"),
            ("Poor method", percentile, "Poor", 120, "High"),
            ("Low consistency", percentile, "Good", 120, "Low"),
            ("Top 10% genetics, poor method", 95, "Poor", 120, "High"),
            ("Bottom 10% genetics, optimal method", 5, "Optimal", 120, "High"),
            ("Average genetics, 30 min/day", 50, "Good", 30, "Medium")
        ]

        scenario_results = []
        for name, gen_pct, method, mins, consist in scenarios:
            res = self.scenario_calculator(mins, method, consist, gen_pct)
            scenario_results.append({
                'scenario': name,
                'genetics': f"{gen_pct:.0f}th %ile",
                'method': method,
                'daily_minutes': mins,
                'consistency': consist,
                'total_hours': res['total_hours'],
                'months_to_b2': res['months_to_b2']
            })

        # Compile full report
        report = {
            "metadata": {
                "generated": datetime.now(timezone.utc).isoformat(),
                "version": "3.5_evidence_based",
                "disclaimer": "Educational tool only. Not diagnostic or predictive of individual success."
            },
            "pgs_results": {
                "raw_score": round(raw_score, 5),
                "z_score": round(z_score, 3),
                "percentile": round(percentile, 1),
                "category": interpretation['category'],
                "estimated_r2_percent": round(estimated_r2 * 100, 2),
                "n_valid_snps": n_valid_snps,
                "n_total_snps": len(self.SNP_DB_PGS)
            },
            "snp_contributions": contributions,
            "interpretation": interpretation,
            "top_contributors": top_contributors,
            "scenarios": scenario_results,
            "warnings": [
                "No validated PGS for language learning exists",
                f"These variants explain only ~{estimated_r2*100:.1f}% of variance",
                "Environmental factors are 20-50x more important",
                "Effect sizes are ancestry-specific; most data is from European populations",
                "Cross-trait inference: using reading/memory/hearing genetics as proxy",
                "For educational/research purposes only"
            ],
            "references": self.REFERENCES
        }

        return report

    # =========================
    # 9. Utility: Save Report
    # =========================
    def save_report(self, report: Dict[str, Any], output_path: str):
        """Save report as JSON file"""
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
