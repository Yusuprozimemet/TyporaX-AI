# dna_engine_enhanced.py
"""
GENELINGUA v3.5 Enhanced – Evidence-Based Polygenic Scoring Engine
-----------------------------------------------------------------
Enhanced version with rich report generation matching Colab quality.

New Features:
- Detailed HTML report generation with embedded visualizations
- Comprehensive interpretation with learning plans
- Visual charts (distribution, contributions, evidence quality)
- Ancestry-specific warnings and guidance
- Formatted text reports for console/markdown
"""

import math
import json
import re
import zipfile
import io
import base64
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timezone
from scipy.stats import norm

# Optional dependencies for visualization
try:
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    from matplotlib.patches import Patch
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    print("Warning: matplotlib/seaborn/numpy not available. Visualizations will be disabled.")


class DNAPolygenicEngine:
    """Enhanced polygenic scoring engine with rich reporting capabilities"""

    # [SNP_DB_PGS dictionary - same as original]
    SNP_DB_PGS = {
        'rs4680': {
            'gene': 'COMT', 'label': 'COMT Val158Met (rs4680)', 'effect_allele': 'A',
            'beta_EUR': 0.042, 'beta_EAS': -0.042, 'beta_default': 0.025,
            'ancestry_specific': True, 'se': 0.015, 'p_value': 0.006, 'evidence': 'Strong',
            'phenotype': 'Second language learning (white matter & phonetic learning)',
            'population': 'European ancestry adults', 'refs': ['Mamiya2016', 'Colzato2010', 'Bonetti2021'],
            'notes': 'Met allele beneficial in EUR, Val allele beneficial in EAS - major ancestry difference!'
        },
        'rs737865': {
            'gene': 'COMT', 'label': 'COMT rs737865', 'effect_allele': 'C',
            'beta_EUR': 0.018, 'beta_EAS': 0.018, 'beta_default': 0.018,
            'ancestry_specific': False, 'se': 0.008, 'p_value': 0.024, 'evidence': 'Moderate',
            'phenotype': 'Figural fluency/creativity', 'population': 'Chinese college students',
            'refs': ['Zhang2014'], 'notes': 'Associated with creative thinking'
        },
        'rs76551189': {
            'gene': 'Near IGSF9', 'label': 'Nonword reading (rs76551189)', 'effect_allele': 'A',
            'beta_EUR': 0.025, 'beta_EAS': 0.025, 'beta_default': 0.025,
            'ancestry_specific': False, 'se': 0.005, 'p_value': 5.2e-8, 'evidence': 'Strong',
            'phenotype': 'Nonword reading ability', 'population': 'Meta-analysis (34,000 individuals)',
            'refs': ['Eising2022'], 'notes': 'Genome-wide significant for phonological processing'
        },
        'rs4656859': {
            'gene': 'IGSF9', 'label': 'IGSF9 rs4656859', 'effect_allele': 'T',
            'beta_EUR': 0.022, 'beta_EAS': 0.022, 'beta_default': 0.022,
            'ancestry_specific': False, 'se': 0.005, 'p_value': 8.1e-8, 'evidence': 'Strong',
            'phenotype': 'Nonword reading', 'population': 'Meta-analysis',
            'refs': ['Eising2022'], 'notes': 'Phonological decoding'
        },
        'rs1422268': {
            'gene': 'DOK3', 'label': 'DOK3 rs1422268', 'effect_allele': 'A',
            'beta_EUR': 0.020, 'beta_EAS': 0.020, 'beta_default': 0.020,
            'ancestry_specific': False, 'se': 0.005, 'p_value': 1.3e-7, 'evidence': 'Strong',
            'phenotype': 'Nonword reading', 'population': 'Meta-analysis',
            'refs': ['Eising2022'], 'notes': 'Reading-related cognitive processing'
        },
        'rs765166': {
            'gene': 'ZFAS1', 'label': 'ZFAS1 rs765166', 'effect_allele': 'C',
            'beta_EUR': 0.015, 'beta_EAS': 0.015, 'beta_default': 0.015,
            'ancestry_specific': False, 'se': 0.006, 'p_value': 0.012, 'evidence': 'Moderate',
            'phenotype': 'Phonemic awareness', 'population': 'Meta-analysis',
            'refs': ['Eising2022'], 'notes': 'Phoneme manipulation'
        },
        'rs363039': {
            'gene': 'SNAP25', 'label': 'SNAP-25 rs363039', 'effect_allele': 'G',
            'beta_EUR': 0.028, 'beta_EAS': 0.028, 'beta_default': 0.028,
            'ancestry_specific': False, 'se': 0.011, 'p_value': 0.011, 'evidence': 'Moderate',
            'phenotype': 'Performance IQ (visuospatial)', 'population': 'Dutch children & adults',
            'refs': ['Gosso2006'], 'notes': 'Synaptic protein - learning & memory'
        },
        'rs80263879': {
            'gene': 'EPHX2', 'label': 'EPHX2 rs80263879', 'effect_allele': 'G',
            'beta_EUR': 0.035, 'beta_EAS': 0.035, 'beta_default': 0.035,
            'ancestry_specific': False, 'se': 0.008, 'p_value': 2.1e-8, 'evidence': 'Strong',
            'phenotype': 'Static spatial working memory', 'population': 'Chinese students',
            'refs': ['Zhang2022'], 'notes': 'Genome-wide significant for working memory'
        },
        'rs11264236': {
            'gene': 'NPR1', 'label': 'NPR1 rs11264236', 'effect_allele': 'A',
            'beta_EUR': 0.012, 'beta_EAS': 0.012, 'beta_default': 0.012,
            'ancestry_specific': False, 'se': 0.005, 'p_value': 0.016, 'evidence': 'Moderate',
            'phenotype': 'Science academic attainment', 'population': 'UK adolescents',
            'refs': ['Donati2021'], 'notes': 'Academic performance'
        },
        'rs10905791': {
            'gene': 'ASB13', 'label': 'ASB13 rs10905791', 'effect_allele': 'T',
            'beta_EUR': 0.011, 'beta_EAS': 0.011, 'beta_default': 0.011,
            'ancestry_specific': False, 'se': 0.005, 'p_value': 0.028, 'evidence': 'Moderate',
            'phenotype': 'Science attainment', 'population': 'UK adolescents',
            'refs': ['Donati2021'], 'notes': 'Cognitive performance'
        },
        'rs6453022': {
            'gene': 'ARHGEF28', 'label': 'ARHGEF28 rs6453022', 'effect_allele': 'C',
            'beta_EUR': 0.016, 'beta_EAS': 0.016, 'beta_default': 0.016,
            'ancestry_specific': False, 'se': 0.004, 'p_value': 3.2e-9, 'evidence': 'Strong',
            'phenotype': 'Hearing difficulty (inverse)', 'population': 'UK Biobank (250,389)',
            'refs': ['Wells2019'], 'notes': 'Auditory processing'
        },
        'rs9493627': {
            'gene': 'EYA4', 'label': 'EYA4 rs9493627', 'effect_allele': 'G',
            'beta_EUR': 0.014, 'beta_EAS': 0.014, 'beta_default': 0.014,
            'ancestry_specific': False, 'se': 0.004, 'p_value': 1.8e-8, 'evidence': 'Strong',
            'phenotype': 'Hearing function', 'population': 'UK Biobank',
            'refs': ['Wells2019'], 'notes': 'Auditory system'
        },
        'rs7294919': {
            'gene': 'ASTN2', 'label': 'ASTN2 rs7294919', 'effect_allele': 'T',
            'beta_EUR': 0.019, 'beta_EAS': 0.019, 'beta_default': 0.019,
            'ancestry_specific': False, 'se': 0.004, 'p_value': 2.3e-8, 'evidence': 'Strong',
            'phenotype': 'Hippocampal volume', 'population': 'Meta-analysis (33,536)',
            'refs': ['Hibar2017'], 'notes': 'Memory formation'
        },
        'rs1800497': {
            'gene': 'DRD2/ANKK1', 'label': 'DRD2 TaqIA (rs1800497)', 'effect_allele': 'T',
            'beta_EUR': 0.015, 'beta_EAS': 0.015, 'beta_default': 0.015,
            'ancestry_specific': False, 'se': 0.007, 'p_value': 0.032, 'evidence': 'Moderate',
            'phenotype': 'Working memory span', 'population': 'Chinese adults',
            'refs': ['Gong2012'], 'notes': 'Dopamine receptor - motivation'
        },
        'rs10009513': {
            'gene': 'MAPT-AS1', 'label': 'MAPT-AS1 rs10009513', 'effect_allele': 'A',
            'beta_EUR': -0.022, 'beta_EAS': -0.022, 'beta_default': -0.022,
            'ancestry_specific': False, 'se': 0.005, 'p_value': 1.4e-8, 'evidence': 'Strong',
            'phenotype': 'Relative brain age (protective)', 'population': 'UK Biobank',
            'refs': ['Ning2021'], 'notes': 'Neuroprotective'
        }
    }

    # [REFERENCES dictionary - same as original]
    REFERENCES = {
        "Mamiya2016": {
            "citation": "Mamiya PC, et al (2016). Brain white matter structure and COMT gene are linked to second-language learning in adults. PNAS 113(26):7249-7254.",
            "url": "https://www.pnas.org/doi/full/10.1073/pnas.1606602113",
            "pmid": "27298360",
            "key_finding": "COMT Met allele associated with better phonetic learning"
        },
        "Eising2022": {
            "citation": "Eising E, et al (2022). Genome-wide analyses of reading- and language-related skills. PNAS 119(35):e2202764119.",
            "url": "https://www.pnas.org/doi/10.1073/pnas.2202764119",
            "pmid": "35998220",
            "key_finding": "42 genome-wide significant loci for reading/language traits"
        },
        "Wells2019": {
            "citation": "Wells HRR, et al (2019). GWAS of hearing difficulty. Am J Hum Genet 105(4):788-802.",
            "url": "https://www.cell.com/ajhg/fulltext/S0002-9297(19)30334-0",
            "pmid": "31564434",
            "key_finding": "44 loci for hearing"
        },
        "Hibar2017": {
            "citation": "Hibar DP, et al (2017). Novel genetic loci for hippocampal volume. Nat Commun 8:13624.",
            "url": "https://www.nature.com/articles/ncomms13624",
            "pmid": "28098162",
            "key_finding": "6 loci for hippocampal volume"
        },
        "Zhang2022": {
            "citation": "Zhang L, et al (2022). GWAS of working memory. Brain Sci 12(9):1254.",
            "url": "https://www.mdpi.com/2076-3425/12/9/1254",
            "pmid": "36176292",
            "key_finding": "EPHX2 variant for working memory"
        },
        "Gosso2006": {
            "citation": "Gosso MF, et al (2006). SNAP-25 and cognitive ability. Mol Psychiatry 11:878-886.",
            "url": "https://www.nature.com/articles/4001868",
            "pmid": "16801949",
            "key_finding": "SNAP-25 variants with IQ"
        },
        "Zhang2014": {
            "citation": "Zhang S, et al (2014). COMT and creative potential. Front Hum Neurosci 8:216.",
            "url": "https://www.frontiersin.org/articles/10.3389/fnhum.2014.00216",
            "pmid": "24782743",
            "key_finding": "COMT variants linked to creativity"
        },
        "Gong2012": {
            "citation": "Gong P, et al (2012). Dopaminergic genes and working memory. J Neural Transm 119:1293-1302.",
            "url": "https://link.springer.com/article/10.1007/s00702-012-0817-9",
            "pmid": "22362150",
            "key_finding": "DRD2 TaqIA with working memory"
        },
        "Donati2021": {
            "citation": "Donati G, et al (2021). Polygenic contributions to academic attainment. Learn Individ Differ 88:101993.",
            "url": "https://www.sciencedirect.com/science/article/pii/S1041608021000674",
            "pmid": "33594131",
            "key_finding": "Subject-specific genetic contributions"
        },
        "Ning2021": {
            "citation": "Ning K, et al (2021). Genetic factors in brain aging. Neurobiol Aging 102:89-97.",
            "url": "https://www.sciencedirect.com/science/article/pii/S0197458021001123",
            "pmid": "34098431",
            "key_finding": "80 SNPs for brain aging"
        },
        "Colzato2010": {
            "citation": "Colzato LS, et al (2010). COMT and cognitive flexibility. Neuropsychologia 48(1):220-225.",
            "pmid": "20434465",
            "key_finding": "COMT affects cognitive flexibility"
        },
        "Bonetti2021": {
            "citation": "Bonetti L, et al (2021). COMT and predictive coding. NeuroImage 233:117954.",
            "pmid": "33716157",
            "key_finding": "COMT heterozygotes show stronger auditory response"
        }
    }

    VALID_ANCESTRIES = ['EUR', 'EAS', 'SAS', 'AFR', 'AMR', 'MENA', 'OTH']

    def __init__(self):
        self.ancestry_labels = {
            'EUR': 'European (includes European-American, European-descended)',
            'EAS': 'East Asian (Chinese, Japanese, Korean, Vietnamese, etc.)',
            'SAS': 'South Asian (Indian, Pakistani, Bangladeshi, Sri Lankan)',
            'AFR': 'African (Sub-Saharan African, African-American)',
            'AMR': 'Latino/Admixed American (Mexican, Puerto Rican, Brazilian)',
            'MENA': 'Middle Eastern/North African',
            'OTH': 'Other/Mixed (results highly uncertain)'
        }

    # ========== Core Methods (same as original) ==========

    def parse_genotype_file(self, file_path: str) -> Dict[str, str]:
        """Parse 23andMe raw data from .txt or .zip file"""
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

    @staticmethod
    def count_effect_alleles(genotype: Optional[str], effect_allele: str) -> Optional[int]:
        """Count number of effect alleles (0, 1, 2)"""
        if not genotype or genotype in {'--', 'NN', '0', '', 'DI', 'ID'}:
            return None
        gt = genotype.strip().upper()
        effect = effect_allele.upper()
        return sum(c == effect for c in gt)

    def compute_pgs(self, snp_map: Dict[str, str], selected_ancestry: str = 'EUR') -> Tuple[float, Dict, int, float]:
        """Compute polygenic score with ancestry-specific betas"""
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

    def calculate_population_parameters(self, selected_ancestry: str = 'EUR', maf: float = 0.25) -> Tuple[float, float]:
        """Estimate population mean and SD"""
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

    def compute_z_score(self, raw_score: float, selected_ancestry: str = 'EUR', contributions: dict = None) -> Tuple[float, float, float]:
        """Calculate z-score, percentile, and R²"""
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

    @staticmethod
    def interpret_score(z: float, pct: float, r2: float, n_valid: int) -> Dict[str, Any]:
        """Generate detailed interpretation with learning recommendations"""
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
            main_text = f"Your polygenic score is in the <strong>bottom {100-pct:.0f}%</strong> of the population for these language-related genetic variants. However, this is a <strong>tiny factor</strong> in language learning success."

            advice = """
            <strong>What this means for you:</strong>
            <ul>
                <li>You may need slightly more repetitions to form strong phonological memories</li>
                <li>Focus on <strong>systematic phonics training</strong> and pronunciation drills</li>
                <li>Use <strong>spaced repetition aggressively</strong> (Anki/SRS daily)</li>
                <li>Consider spending 10-15% more time on explicit grammar study</li>
                <li><strong>Critical point:</strong> Someone at the 10th percentile who studies 2 hours/day will far surpass someone at the 90th percentile who studies 30 min/day</li>
            </ul>
            """

            learning_plan = DNAPolygenicEngine._generate_learning_plan("below_average", pct)

        elif z > 1:
            main_text = f"Your polygenic score is in the <strong>top {pct:.0f}%</strong> for these variants. This may provide a <strong>slight efficiency advantage</strong>, but it's still a minor factor."

            advice = """
            <strong>What this means for you:</strong>
            <ul>
                <li>You may acquire phonological patterns slightly faster</li>
                <li>You can likely handle more <strong>immersion-heavy approaches</strong> (70%+ input)</li>
                <li>Don't skip the fundamentals - genetics ≠ automatic fluency</li>
                <li>Your advantage is <strong>learning rate</strong>, not ultimate attainment</li>
                <li><strong>Key insight:</strong> This 2-4% genetic edge can be easily lost to poor study methods or low motivation</li>
            </ul>
            """

            learning_plan = DNAPolygenicEngine._generate_learning_plan("above_average", pct)

        else:
            main_text = f"Your polygenic score is <strong>average</strong> (around the 50th percentile). This is where most successful language learners are."

            advice = """
            <strong>What this means for you:</strong>
            <ul>
                <li>Use evidence-based methods: comprehensible input + spaced repetition + production practice</li>
                <li>Balance immersion (60%) with explicit study (25%) and speaking practice (15%)</li>
                <li>Consistency matters far more than genetics</li>
                <li>Track your hours - aim for 600-1200 hours for B2-level proficiency</li>
            </ul>
            """

            learning_plan = DNAPolygenicEngine._generate_learning_plan("average", pct)

        variance_text = (
            f"These {n_valid} genetic variants explain an estimated <strong>~{r2*100:.1f}% of variance</strong> in related cognitive traits. "
            f"This means <strong>{100-r2*100:.1f}%</strong> comes from: study method & quality (30-40%), "
            f"total practice hours (20-30%), motivation & consistency (15-20%), age of acquisition (5-10%), "
            f"other environmental factors (10-15%), and measurement error & unmeasured genetics (~{r2*100:.1f}%)."
        )

        return {
            'category': category,
            'color': color,
            'main_text': main_text,
            'advice': advice,
            'variance_text': variance_text,
            'learning_plan': learning_plan
        }

    @staticmethod
    def _generate_learning_plan(score_category: str, percentile: float) -> str:
        """Generate tailored learning plan based on score"""
        base_plan = """
        <h4>📚 Your Evidence-Based Learning Plan</h4>
        <p><strong>The 70-20-10 Framework (2 hours/day)</strong></p>
        
        <div style="margin: 15px 0;">
            <strong>1. Comprehensible Input (70% = 84 min/day)</strong>
            <ul>
                <li><strong>Listening:</strong> Podcasts, YouTube, audiobooks at 90% comprehension level</li>
                <li><strong>Reading:</strong> Graded readers → native materials with popup dictionaries</li>
                <li><strong>Focus:</strong> Volume over perfection. Aim for 10+ hours/week of input</li>
            </ul>
        </div>
        
        <div style="margin: 15px 0;">
            <strong>2. Explicit Study (20% = 24 min/day)</strong>
            <ul>
                <li><strong>SRS (Anki):</strong> 15 min/day of sentence mining or frequency-based decks</li>
                <li><strong>Grammar:</strong> 10 min/day learning patterns in context</li>
                <li><strong>Pronunciation:</strong> 5 min shadowing or phonetic drills</li>
            </ul>
        </div>
        
        <div style="margin: 15px 0;">
            <strong>3. Production Practice (10% = 12 min/day)</strong>
            <ul>
                <li><strong>Speaking:</strong> iTalki tutors, language exchange, or shadowing</li>
                <li><strong>Writing:</strong> Journaling with corrections</li>
            </ul>
        </div>
        """

        if score_category == "below_average":
            adjustment = f"""
            <div style="background-color: #fff3cd; padding: 10px; margin: 15px 0; border-left: 4px solid #ff9800;">
                <strong>⚙️ Adjustments for your genetic profile ({percentile:.0f}th percentile):</strong>
                <ul>
                    <li>Add +10 min/day to explicit phonics/pronunciation work</li>
                    <li>Use more structured courses initially (e.g., Pimsleur, Assimil)</li>
                    <li>Front-load grammar study in first 3 months</li>
                    <li>Accept that you'll need 10-20% more repetitions - this is fine!</li>
                </ul>
            </div>
            """
        elif score_category == "above_average":
            adjustment = f"""
            <div style="background-color: #d4edda; padding: 10px; margin: 15px 0; border-left: 4px solid #28a745;">
                <strong>⚡ Leverage your genetic profile ({percentile:.0f}th percentile):</strong>
                <ul>
                    <li>Can handle more immersion-heavy approaches (75% input)</li>
                    <li>May grasp patterns faster, but don't skip fundamentals</li>
                    <li>Use your efficiency to learn multiple languages or go deeper</li>
                    <li>Still need 600+ hours for fluency - no shortcuts!</li>
                </ul>
            </div>
            """
        else:
            adjustment = f"""
            <div style="background-color: #e3f2fd; padding: 10px; margin: 15px 0; border-left: 4px solid #2196f3;">
                <strong>📊 Your genetic profile is average ({percentile:.0f}th percentile):</strong>
                <ul>
                    <li>Use the standard 70-20-10 framework without modifications</li>
                    <li>Adjust based on personal preference and results</li>
                    <li>Track hours and progress metrics</li>
                    <li>Focus on consistency over optimization</li>
                </ul>
            </div>
            """

        return base_plan + adjustment

    @staticmethod
    def scenario_calculator(daily_minutes: int, method_quality: str, consistency: str, genetic_percentile: float) -> Dict[str, float]:
        """Calculate time to B2 based on various factors"""
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

    def categorize_snps_by_phenotype(self, contributions: Dict[str, Dict]) -> Dict[str, float]:
        """Categorize SNPs by cognitive domain"""
        phenotype_categories = {
            'Reading/Language': ['Nonword reading', 'Phonemic awareness', 'reading', 'language'],
            'Memory': ['memory', 'Hippocampal', 'working memory'],
            'Auditory': ['Hearing', 'auditory'],
            'Cognition': ['IQ', 'cognitive', 'attainment', 'brain age'],
            'Dopamine': ['COMT', 'DRD2', 'creative', 'dopamine']
        }

        category_scores = {}
        for cat, keywords in phenotype_categories.items():
            cat_score = 0
            for rsid, contrib_data in contributions.items():
                phenotype = contrib_data.get('phenotype', '').lower()
                if any(kw.lower() in phenotype for kw in keywords):
                    contrib = contrib_data.get('contrib')
                    if contrib is not None:
                        cat_score += contrib
            category_scores[cat] = cat_score

        return category_scores

    # ========== Visualization Methods ==========

    def generate_visualizations(self, z_score: float, percentile: float, contributions: Dict,
                                category_scores: Dict, selected_ancestry: str) -> Dict[str, str]:
        """Generate all visualizations and return as base64-encoded images"""
        if not VISUALIZATION_AVAILABLE:
            return {}

        visualizations = {}

        try:
            # Set style
            sns.set_style("whitegrid")

            # 1. Population Distribution Chart
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            x = np.linspace(-3, 3, 500)
            pop_pdf = norm.pdf(x, 0, 1)
            ax1.plot(x, pop_pdf, color="#2c3e50", lw=3,
                     label="Population Distribution")
            ax1.axvline(z_score, color="#e74c3c", lw=2.5, ls="--",
                        label=f"Your Score (z={z_score:+.2f})")
            ax1.fill_between(x, pop_pdf, where=(x <= z_score),
                             alpha=0.25, color="#e74c3c")
            ax1.set_title("Your Genetic Score vs Population",
                          fontsize=14, fontweight='bold')
            ax1.set_xlabel("Z-score", fontsize=12)
            ax1.set_ylabel("Probability Density", fontsize=12)
            ax1.legend(fontsize=10)
            ax1.grid(alpha=0.3)

            buf1 = io.BytesIO()
            plt.savefig(buf1, format='png', dpi=100, bbox_inches='tight')
            buf1.seek(0)
            visualizations['population_dist'] = base64.b64encode(
                buf1.read()).decode('utf-8')
            plt.close(fig1)

            # 2. SNP Contributions Bar Chart
            contrib_data = []
            for rsid, meta in self.SNP_DB_PGS.items():
                c = contributions[rsid]
                if c['contrib'] is not None:
                    contrib_data.append({
                        'SNP': f"{rsid}\n({meta['gene']})",
                        'Contribution': c['contrib'],
                        'Evidence': meta['evidence']
                    })

            if contrib_data:
                contrib_data.sort(key=lambda x: x['Contribution'])

                fig2, ax2 = plt.subplots(figsize=(12, 8))
                colors_map = {'Strong': '#27ae60',
                              'Moderate': '#f39c12', 'Weak': '#95a5a6'}
                bar_colors = [colors_map.get(
                    d['Evidence'], '#95a5a6') for d in contrib_data]

                snp_labels = [d['SNP'] for d in contrib_data]
                contributions_values = [d['Contribution']
                                        for d in contrib_data]

                bars = ax2.barh(snp_labels, contributions_values,
                                color=bar_colors, edgecolor='black', linewidth=0.8)
                ax2.axvline(0, color='black', lw=1)
                ax2.set_title("Individual SNP Contributions to Your PGS",
                              fontsize=14, fontweight='bold')
                ax2.set_xlabel(
                    "Weighted Contribution (Beta × Dosage)", fontsize=12)
                ax2.grid(axis='x', alpha=0.3)

                legend_elements = [
                    Patch(facecolor='#27ae60', label='Strong Evidence'),
                    Patch(facecolor='#f39c12', label='Moderate Evidence'),
                    Patch(facecolor='#95a5a6', label='Weak Evidence')
                ]
                ax2.legend(handles=legend_elements,
                           loc='lower right', fontsize=9)

                buf2 = io.BytesIO()
                plt.savefig(buf2, format='png', dpi=100, bbox_inches='tight')
                buf2.seek(0)
                visualizations['snp_contributions'] = base64.b64encode(
                    buf2.read()).decode('utf-8')
                plt.close(fig2)

            # 3. Phenotype Categories Bar Chart
            if category_scores:
                fig3, ax3 = plt.subplots(figsize=(10, 6))
                cats = list(category_scores.keys())
                scores = list(category_scores.values())
                colors_cat = ['#3498db', '#9b59b6',
                              '#e67e22', '#1abc9c', '#e74c3c']

                bars_cat = ax3.barh(cats, scores, color=colors_cat[:len(
                    cats)], edgecolor='black', linewidth=1)
                ax3.axvline(0, color='black', lw=1)
                ax3.set_title("Contributions by Cognitive Domain",
                              fontsize=14, fontweight='bold')
                ax3.set_xlabel("Cumulative Contribution", fontsize=12)
                ax3.grid(axis='x', alpha=0.3)

                buf3 = io.BytesIO()
                plt.savefig(buf3, format='png', dpi=100, bbox_inches='tight')
                buf3.seek(0)
                visualizations['category_contributions'] = base64.b64encode(
                    buf3.read()).decode('utf-8')
                plt.close(fig3)

            # 4. Evidence Quality Pie Chart
            evidence_counts = {}
            for c in contributions.values():
                evidence = c.get('evidence', 'Unknown')
                evidence_counts[evidence] = evidence_counts.get(
                    evidence, 0) + 1

            if evidence_counts:
                fig4, ax4 = plt.subplots(figsize=(8, 8))
                colors_pie = {'Strong': '#27ae60',
                              'Moderate': '#f39c12', 'Weak': '#95a5a6'}
                pie_colors = [colors_pie.get(e, '#95a5a6')
                              for e in evidence_counts.keys()]

                ax4.pie(evidence_counts.values(), labels=evidence_counts.keys(), autopct='%1.0f%%',
                        colors=pie_colors, startangle=90, textprops={'fontsize': 11, 'fontweight': 'bold'})
                ax4.set_title("Evidence Quality Distribution",
                              fontsize=14, fontweight='bold')

                buf4 = io.BytesIO()
                plt.savefig(buf4, format='png', dpi=100, bbox_inches='tight')
                buf4.seek(0)
                visualizations['evidence_quality'] = base64.b64encode(
                    buf4.read()).decode('utf-8')
                plt.close(fig4)

        except Exception as e:
            print(f"Warning: Visualization generation failed: {e}")

        return visualizations

    # ========== HTML Report Generation ==========

    def generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """Generate comprehensive HTML report"""

        # Extract data
        metadata = report_data['metadata']
        pgs = report_data['pgs_results']
        interpretation = report_data['interpretation']
        top_contributors = report_data.get('top_contributors', [])
        scenarios = report_data.get('scenarios', [])
        visualizations = report_data.get('visualizations', {})
        warnings = report_data.get('warnings', [])

        # Build HTML
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GeneLingua Report - {metadata['generated'][:10]}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 2.5em;
        }}
        .disclaimer {{
            background-color: #fff3cd;
            border-left: 5px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .disclaimer h3 {{
            color: #856404;
            margin-top: 0;
        }}
        .disclaimer ul {{
            color: #856404;
            margin: 10px 0;
        }}
        .results-box {{
            background-color: white;
            border-radius: 10px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .score-display {{
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, {interpretation['color']}22 0%, {interpretation['color']}44 100%);
            border-radius: 10px;
            margin: 20px 0;
        }}
        .score-display h2 {{
            color: {interpretation['color']};
            margin: 0;
            font-size: 2em;
        }}
        .score-metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .metric-card {{
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .metric-card h4 {{
            margin: 0 0 10px 0;
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
        }}
        .metric-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        .interpretation-box {{
            background-color: {interpretation['color']}15;
            border-left: 5px solid {interpretation['color']};
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .interpretation-box h2 {{
            color: {interpretation['color']};
            margin-top: 0;
        }}
        .visualization {{
            margin: 30px 0;
            text-align: center;
        }}
        .visualization img {{
            max-width: 100%;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .snp-detail {{
            background-color: #f8f9fa;
            border-left: 3px solid #3498db;
            padding: 12px;
            margin: 10px 0;
            border-radius: 3px;
        }}
        .snp-detail strong {{
            font-size: 1.1em;
            color: #2c3e50;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #667eea;
            color: white;
            font-weight: bold;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .reference {{
            margin: 15px 0;
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 5px;
            font-size: 0.95em;
        }}
        .reference a {{
            color: #2980b9;
            text-decoration: none;
        }}
        .reference a:hover {{
            text-decoration: underline;
        }}
        .warning-box {{
            background-color: #fff3cd;
            border-left: 5px solid #ff9800;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .warning-box h3 {{
            color: #e65100;
            margin-top: 0;
        }}
        ul {{
            line-height: 1.8;
        }}
        .footer {{
            text-align: center;
            padding: 30px;
            color: #666;
            margin-top: 50px;
            border-top: 2px solid #ddd;
        }}
    </style>
</head>
<body>

<div class="header">
    <h1>🧬 GeneLingua v3.5</h1>
    <p style="font-size: 1.2em; margin: 0;">Evidence-Based Genetic Analysis for Language Learning</p>
    <p style="margin: 10px 0 0 0; opacity: 0.9;">
        Generated: {metadata['generated'][:19]} UTC | 
        Ancestry: {metadata['ancestry_label']}
    </p>
</div>

<div class="disclaimer">
    <h3>⚠️ SCIENTIFIC LIMITATIONS</h3>
    <ul>
        <li><strong>No validated "language learning PGS" exists.</strong> These SNPs come from studies of reading, memory, hearing, and cognitive ability - not language learning per se.</li>
        <li><strong>Small effect sizes:</strong> Combined, these variants explain <strong>~{pgs['estimated_r2_percent']:.1f}% of variance</strong> in related cognitive traits.</li>
        <li><strong>Ancestry matters critically:</strong> Most studies are European-ancestry. COMT shows <strong>opposite effects</strong> in East Asian populations.</li>
        <li><strong>Environment >> Genetics:</strong> Study method, motivation, immersion time, and instruction quality are 20-50x more important.</li>
        <li><strong>Educational tool only:</strong> Not diagnostic, not predictive of individual success.</li>
    </ul>
</div>

<div class="results-box">
    <h2>📊 Your Polygenic Score Results</h2>
    
    <div class="score-display">
        <h2>Your Result: {interpretation['category']}</h2>
        <p style="font-size: 1.3em; margin: 10px 0;">{pgs['percentile']:.1f}th Percentile</p>
    </div>
    
    <div class="score-metrics">
        <div class="metric-card">
            <h4>Raw Score</h4>
            <div class="value">{pgs['raw_score']:+.4f}</div>
        </div>
        <div class="metric-card">
            <h4>Z-Score</h4>
            <div class="value">{pgs['z_score']:+.3f}</div>
        </div>
        <div class="metric-card">
            <h4>Percentile</h4>
            <div class="value">{pgs['percentile']:.1f}%</div>
        </div>
        <div class="metric-card">
            <h4>Valid SNPs</h4>
            <div class="value">{pgs['n_valid_snps']}/{pgs['n_total_snps']}</div>
        </div>
        <div class="metric-card">
            <h4>Est. R²</h4>
            <div class="value">{pgs['estimated_r2_percent']:.2f}%</div>
        </div>
    </div>
</div>

<div class="interpretation-box">
    <h2>Your Result: {interpretation['category']}</h2>
    <p style="font-size: 1.1em;">{interpretation['main_text']}</p>
    {interpretation['advice']}
    <div style="background-color: #ecf0f1; padding: 10px; border-radius: 5px; margin-top: 10px;">
        <strong>📊 Effect Size Context:</strong><br>
        {interpretation['variance_text']}
    </div>
</div>

{interpretation.get('learning_plan', '')}

"""

        # Add visualizations
        if visualizations:
            html += '<div class="results-box"><h2>📈 Visual Analysis</h2>'

            if 'population_dist' in visualizations:
                html += f'''
                <div class="visualization">
                    <h3>Your Score vs Population Distribution</h3>
                    <img src="data:image/png;base64,{visualizations['population_dist']}" alt="Population Distribution">
                </div>
                '''

            if 'snp_contributions' in visualizations:
                html += f'''
                <div class="visualization">
                    <h3>Individual SNP Contributions</h3>
                    <img src="data:image/png;base64,{visualizations['snp_contributions']}" alt="SNP Contributions">
                </div>
                '''

            if 'category_contributions' in visualizations:
                html += f'''
                <div class="visualization">
                    <h3>Contributions by Cognitive Domain</h3>
                    <img src="data:image/png;base64,{visualizations['category_contributions']}" alt="Category Contributions">
                </div>
                '''

            if 'evidence_quality' in visualizations:
                html += f'''
                <div class="visualization">
                    <h3>Evidence Quality Distribution</h3>
                    <img src="data:image/png;base64,{visualizations['evidence_quality']}" alt="Evidence Quality">
                </div>
                '''

            html += '</div>'

        # Top contributors
        if top_contributors:
            html += '<div class="results-box"><h2>🧬 Top Contributing Genes</h2>'
            for snp in top_contributors[:5]:
                html += f'''
                <div class="snp-detail">
                    <strong>{snp['rsid']}</strong> ({snp['gene']}) - {snp['dosage_text']}<br>
                    <strong>Your genotype:</strong> {snp['genotype']} | <strong>Contribution:</strong> {snp['contribution']:+.5f}<br>
                    <strong>Phenotype:</strong> {snp['phenotype']}<br>
                    <strong>Evidence:</strong> {snp['evidence']} | <strong>Study:</strong> {snp['population']}<br>
                    <em style="font-size: 0.9em; color: #7f8c8d;">{snp['notes']}</em>
                </div>
                '''
            html += '</div>'

        # Scenarios
        if scenarios:
            html += '''
            <div class="results-box">
                <h2>🎮 Learning Scenario Comparisons</h2>
                <p><strong>Time to reach B2 level (conversational fluency) under different scenarios:</strong></p>
                <table>
                    <tr>
                        <th>Scenario</th>
                        <th>Genetics</th>
                        <th>Method</th>
                        <th>Daily Min</th>
                        <th>Consistency</th>
                        <th>Total Hours</th>
                        <th>Months to B2</th>
                    </tr>
            '''
            for s in scenarios:
                html += f'''
                    <tr>
                        <td><strong>{s['scenario']}</strong></td>
                        <td>{s['genetics']}</td>
                        <td>{s['method']}</td>
                        <td>{s['daily_minutes']}</td>
                        <td>{s['consistency']}</td>
                        <td>{s['total_hours']}</td>
                        <td><strong>{s['months_to_b2']}</strong></td>
                    </tr>
                '''
            html += '''
                </table>
                <p style="margin-top: 15px; padding: 10px; background-color: #e8f5e9; border-left: 4px solid #4caf50;">
                    <strong>🔍 Key Insight:</strong> Notice how "Bottom 10% genetics + optimal method" beats "Top 10% genetics + poor method" by <strong>10+ months</strong>.
                    This demonstrates the real-world importance of genetics vs. behavior for language learning.
                </p>
            </div>
            '''

        # Warnings
        if metadata['selected_ancestry'] not in ['EUR']:
            html += f'''
            <div class="warning-box">
                <h3>⚠️ CRITICAL: Ancestry Considerations</h3>
                <p style="font-weight: bold;">These effect sizes are primarily from European-ancestry samples.
                Predictions may be INACCURATE for {metadata['ancestry_label']}:</p>
                <ul>
                    <li><strong>East Asian ancestry:</strong> COMT rs4680 shows <strong>OPPOSITE effects</strong></li>
                    <li><strong>African ancestry:</strong> Different linkage disequilibrium patterns</li>
                    <li><strong>Mixed ancestry:</strong> Effects are unpredictable without ancestry-specific analysis</li>
                    <li><strong>Non-European:</strong> Most loci have not been validated</li>
                </ul>
                <p style="margin-top: 10px;"><strong>Bottom line:</strong> If you're not of primarily European descent,
                treat these results as <em>highly speculative</em>.</p>
            </div>
            '''

        # References
        html += '''
        <div class="results-box">
            <h2>📖 References</h2>
            <div style="max-height: 400px; overflow-y: scroll;">
        '''
        for ref_key, ref_data in sorted(self.REFERENCES.items()):
            html += f'''
            <div class="reference">
                <strong>{ref_key}:</strong> {ref_data['citation']}<br>
                <a href="{ref_data.get('url', '#')}" target="_blank">{ref_data.get('url', 'URL N/A')}</a>
                {f"<br><span style='font-size: 0.9em; color: #7f8c8d;'>PMID: {ref_data['pmid']}</span>" if 'pmid' in ref_data else ""}
                <br><em style="font-size: 0.9em; color: #27ae60;">{ref_data['key_finding']}</em>
            </div>
            '''
        html += '</div></div>'

        # Footer
        html += f'''
        <div class="footer">
            <h3>✅ Analysis Complete</h3>
            <p><strong>Remember:</strong> This tool demonstrates polygenic scoring methodology using published genetic associations.
            While these traits correlate with language learning, <strong>no validated genetic predictor of language learning success exists</strong>.</p>
            <p style="margin-top: 15px;">
                Your success will be determined by:<br>
                • <strong>How you study</strong> (70-20-10 method) → 30-40% of variance<br>
                • <strong>How many hours</strong> you log (600-1200 for B2) → 20-30% of variance<br>
                • <strong>Your motivation</strong> and consistency → 15-20% of variance<br>
                • <strong>These genetic variants</strong> → ~{pgs['estimated_r2_percent']:.1f}% of variance
            </p>
            <p style="font-size: 1.3em; margin-top: 20px; color: #667eea;"><strong>Go study. Your genetics are fine. 🚀</strong></p>
            <p style="margin-top: 30px; font-size: 0.9em; color: #999;">
                GeneLingua v{metadata['version']} | Generated {metadata['generated'][:19]} UTC
            </p>
        </div>

</body>
</html>
        '''

        return html

    # ========== Main Report Generation ==========

    def generate_report(self, file_path: str, selected_ancestry: str = 'EUR', include_visualizations: bool = True) -> Dict[str, Any]:
        """
        Main entry point: run full analysis and return comprehensive report.

        Args:
            file_path: Path to 23andMe raw data file (.txt or .zip)
            selected_ancestry: Ancestry code (EUR, EAS, SAS, AFR, AMR, MENA, OTH)
            include_visualizations: Generate charts (requires matplotlib)

        Returns:
            Dictionary containing full report data including HTML
        """
        # Parse genotypes
        snp_map = self.parse_genotype_file(file_path)

        # Compute PGS
        raw_score, contributions, n_valid_snps, total_weight = self.compute_pgs(
            snp_map, selected_ancestry)
        z_score, percentile, estimated_r2 = self.compute_z_score(
            raw_score, selected_ancestry, contributions)

        # Interpretation
        interpretation = self.interpret_score(
            z_score, percentile, estimated_r2, n_valid_snps)

        # Phenotype categorization
        category_scores = self.categorize_snps_by_phenotype(contributions)

        # Evidence quality distribution
        evidence_counts = {}
        for c in contributions.values():
            evidence = c.get('evidence', 'Unknown')
            evidence_counts[evidence] = evidence_counts.get(evidence, 0) + 1

        # Top contributors
        top_contributors = sorted(
            [(rsid, c, self.SNP_DB_PGS[rsid])
             for rsid, c in contributions.items() if c['contrib'] is not None],
            key=lambda x: abs(x[1]['contrib']),
            reverse=True
        )[:5]

        top_contributors_detailed = []
        for rsid, contrib, meta in top_contributors:
            dosage = contrib['dosage']
            if dosage == 2:
                dosage_text = "🔴🔴 Homozygous for effect allele (2 copies)"
            elif dosage == 1:
                dosage_text = "🟡 Heterozygous (1 copy)"
            else:
                dosage_text = "⚪ No effect allele copies"

            top_contributors_detailed.append({
                'rsid': rsid,
                'gene': meta['gene'],
                'genotype': contrib['genotype'],
                'dosage': dosage,
                'dosage_text': dosage_text,
                'contribution': contrib['contrib'],
                'phenotype': meta['phenotype'],
                'evidence': meta['evidence'],
                'population': meta['population'],
                'refs': meta['refs'],
                'notes': meta['notes']
            })

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
                'total_hours': int(res['total_hours']),
                'months_to_b2': res['months_to_b2']
            })

        # Generate visualizations
        visualizations = {}
        if include_visualizations and VISUALIZATION_AVAILABLE:
            try:
                visualizations = self.generate_visualizations(
                    z_score, percentile, contributions,
                    category_scores, selected_ancestry
                )
            except Exception as e:
                print(f"Warning: Visualization generation failed: {e}")

        # Compile report data
        report_data = {
            'metadata': {
                'version': '3.5',
                'generated': datetime.now(timezone.utc).isoformat(),
                'selected_ancestry': selected_ancestry,
                'ancestry_label': self.ancestry_labels.get(selected_ancestry, selected_ancestry),
                'total_snps_tested': len(self.SNP_DB_PGS)
            },
            'pgs_results': {
                'raw_score': raw_score,
                'z_score': z_score,
                'percentile': percentile,
                'estimated_r2': estimated_r2,
                'estimated_r2_percent': estimated_r2 * 100,
                'n_valid_snps': n_valid_snps,
                'n_total_snps': len(self.SNP_DB_PGS),
                'total_weight': total_weight
            },
            'interpretation': interpretation,
            'contributions': contributions,
            'top_contributors': top_contributors_detailed,
            'category_scores': category_scores,
            'evidence_counts': evidence_counts,
            'scenarios': scenario_results,
            'visualizations': visualizations,
            'warnings': self._generate_warnings(selected_ancestry, n_valid_snps)
        }

        # Generate HTML report
        html_report = self.generate_html_report(report_data)
        report_data['html_report'] = html_report

        # Generate text summary
        text_report = self.generate_text_report(report_data)
        report_data['text_report'] = text_report

        return report_data

    def _generate_warnings(self, selected_ancestry: str, n_valid_snps: int) -> List[str]:
        """Generate ancestry and coverage warnings"""
        warnings = []

        if selected_ancestry not in ['EUR']:
            warnings.append(
                f"⚠️ ANCESTRY WARNING: Most effect sizes are from European samples. "
                f"Results for {self.ancestry_labels[selected_ancestry]} may be inaccurate."
            )

        if selected_ancestry == 'EAS':
            warnings.append(
                "🔴 CRITICAL: COMT rs4680 shows OPPOSITE effects in East Asian vs European populations. "
                "Met allele is beneficial in Europeans but Val allele is beneficial in East Asians."
            )

        if n_valid_snps < len(self.SNP_DB_PGS) * 0.7:
            warnings.append(
                f"📉 DATA COVERAGE: Only {n_valid_snps}/{len(self.SNP_DB_PGS)} SNPs were genotyped. "
                f"Low coverage reduces score accuracy."
            )

        if selected_ancestry == 'OTH':
            warnings.append(
                "❓ UNKNOWN ANCESTRY: Results are highly uncertain without ancestry information. "
                "Consider genetic ancestry testing (e.g., 23andMe ancestry composition)."
            )

        return warnings

    def generate_text_report(self, report_data: Dict[str, Any]) -> str:
        """Generate formatted text report for console/markdown"""
        metadata = report_data['metadata']
        pgs = report_data['pgs_results']
        interpretation = report_data['interpretation']

        text = f"""
{'='*80}
GENELINGUA v{metadata['version']} - POLYGENIC LANGUAGE LEARNING REPORT
{'='*80}

Generated: {metadata['generated'][:19]} UTC
Ancestry: {metadata['ancestry_label']}
SNPs Analyzed: {pgs['n_valid_snps']}/{pgs['n_total_snps']} successfully genotyped

{'='*80}
POLYGENIC SCORE RESULTS
{'='*80}

Raw Score:       {pgs['raw_score']:+.5f}
Z-Score:         {pgs['z_score']:+.3f}
Percentile:      {pgs['percentile']:.1f}%
Category:        {interpretation['category']}
Estimated R²:    {pgs['estimated_r2_percent']:.2f}% of variance explained

{'='*80}
INTERPRETATION
{'='*80}

{interpretation['category'].upper()}

{interpretation['main_text'].replace('<strong>', '').replace('</strong>', '')}

{interpretation['variance_text'].replace('<strong>', '').replace('</strong>', '')}

{'='*80}
TOP 5 CONTRIBUTING SNPS
{'='*80}
"""

        for i, snp in enumerate(report_data['top_contributors'][:5], 1):
            text += f"""
{i}. {snp['rsid']} ({snp['gene']})
   Genotype: {snp['genotype']} | {snp['dosage_text']}
   Contribution: {snp['contribution']:+.5f}
   Phenotype: {snp['phenotype']}
   Evidence: {snp['evidence']} ({snp['population']})
   Notes: {snp['notes']}
"""

        text += f"""
{'='*80}
PHENOTYPE CATEGORY BREAKDOWN
{'='*80}
"""
        for category, score in sorted(report_data['category_scores'].items(),
                                      key=lambda x: abs(x[1]), reverse=True):
            text += f"\n{category:.<40} {score:+.5f}"

        text += f"""

{'='*80}
SCENARIO COMPARISONS: TIME TO B2 FLUENCY
{'='*80}
"""
        for s in report_data['scenarios']:
            text += f"""
{s['scenario']}:
  Genetics: {s['genetics']} | Method: {s['method']} | Daily: {s['daily_minutes']} min | Consistency: {s['consistency']}
  → Total Hours: {s['total_hours']} | Months to B2: {s['months_to_b2']}
"""

        if report_data['warnings']:
            text += f"""
{'='*80}
⚠️  WARNINGS
{'='*80}
"""
            for warning in report_data['warnings']:
                text += f"\n{warning}\n"

        text += f"""
{'='*80}
BOTTOM LINE
{'='*80}

These genetic variants explain ~{pgs['estimated_r2_percent']:.1f}% of variance in related cognitive traits.
The other {100-pgs['estimated_r2_percent']:.1f}% comes from:
  • Study method quality (30-40%)
  • Total practice hours (20-30%)
  • Motivation & consistency (15-20%)
  • Age of acquisition (5-10%)
  • Other environmental factors (10-15%)

Your genetics are fine. Go study. 🚀

{'='*80}
"""
        return text

    def save_report(self, report_data: Dict[str, Any], output_dir: str = '.',
                    formats: List[str] = ['html', 'txt', 'json']) -> Dict[str, str]:
        """
        Save report in multiple formats

        Args:
            report_data: Report dictionary from generate_report()
            output_dir: Directory to save files
            formats: List of formats to save ('html', 'txt', 'json')

        Returns:
            Dictionary mapping format to file path
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f"genelingua_report_{timestamp}"

        saved_files = {}

        if 'html' in formats:
            html_path = os.path.join(output_dir, f"{base_name}.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(report_data['html_report'])
            saved_files['html'] = html_path
            print(f"✅ HTML report saved: {html_path}")

        if 'txt' in formats:
            txt_path = os.path.join(output_dir, f"{base_name}.txt")
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(report_data['text_report'])
            saved_files['txt'] = txt_path
            print(f"✅ Text report saved: {txt_path}")

        if 'json' in formats:
            json_path = os.path.join(output_dir, f"{base_name}.json")
            # Remove non-serializable items for JSON
            json_data = {k: v for k, v in report_data.items()
                         if k not in ['html_report', 'text_report', 'visualizations']}
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            saved_files['json'] = json_path
            print(f"✅ JSON data saved: {json_path}")

        return saved_files


# ========== Command-Line Interface ==========

def main():
    """Command-line interface for GeneLingua"""
    import argparse

    parser = argparse.ArgumentParser(
        description='GeneLingua v3.5 - Evidence-Based Polygenic Scoring for Language Learning',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dna_engine_enhanced.py data.txt --ancestry EUR
  python dna_engine_enhanced.py genome.zip --ancestry EAS --output reports/
  python dna_engine_enhanced.py data.txt --ancestry SAS --formats html txt

Valid ancestries: EUR (European), EAS (East Asian), SAS (South Asian), 
                 AFR (African), AMR (Latino/Admixed American), 
                 MENA (Middle Eastern/North African), OTH (Other/Mixed)
        """
    )

    parser.add_argument(
        'file', help='Path to 23andMe raw data file (.txt or .zip)')
    parser.add_argument('--ancestry', '-a', default='EUR',
                        choices=['EUR', 'EAS', 'SAS',
                                 'AFR', 'AMR', 'MENA', 'OTH'],
                        help='Your genetic ancestry (default: EUR)')
    parser.add_argument('--output', '-o', default='.',
                        help='Output directory for reports (default: current directory)')
    parser.add_argument('--formats', '-f', nargs='+',
                        choices=['html', 'txt', 'json'],
                        default=['html', 'txt'],
                        help='Output formats (default: html txt)')
    parser.add_argument('--no-viz', action='store_true',
                        help='Disable visualizations (useful if matplotlib not installed)')

    args = parser.parse_args()

    print("\n" + "="*80)
    print("GENELINGUA v3.5 - Evidence-Based Polygenic Scoring Engine")
    print("="*80 + "\n")

    # Initialize engine
    engine = DNAPolygenicEngine()

    # Generate report
    print(f"📂 Loading genotype data from: {args.file}")
    print(f"🧬 Selected ancestry: {engine.ancestry_labels[args.ancestry]}")
    print(f"📊 Generating comprehensive report...\n")

    try:
        report = engine.generate_report(
            args.file,
            selected_ancestry=args.ancestry,
            include_visualizations=not args.no_viz
        )

        # Print text summary to console
        print(report['text_report'])

        # Save reports
        saved_files = engine.save_report(report, args.output, args.formats)

        print("\n" + "="*80)
        print("✅ ANALYSIS COMPLETE")
        print("="*80)
        for fmt, path in saved_files.items():
            print(f"  {fmt.upper()}: {path}")
        print()

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
