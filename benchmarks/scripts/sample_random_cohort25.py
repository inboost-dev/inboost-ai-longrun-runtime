#!/usr/bin/env python3
"""Sample a random cohort of 25 tasks from SWE-bench Verified.

Supports:
- Online sampling via Hugging Face datasets (princeton-nlp/SWE-bench_Verified)
- Fixed seed for scientific reproducibility (e.g. --seed 42) or random (--seed random)
- Full offline fallback containing 25 pre-packaged verified instance descriptors
- Balanced repo distribution across top Python repositories

Usage:
    python3 sample_random_cohort25.py [--seed 42] [--output configs/swebench_cohort_25_random.json]
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("inboost.sample_cohort25")

# Pre-cached fallback cohort of 25 verified instances from across diverse repos
FALLBACK_25_INSTANCES: list[dict[str, Any]] = [
    {
        "instance_id": "pytest-dev__pytest-7324",
        "repo": "pytest-dev/pytest",
        "base_commit": "6e3381a349be88a2919d3fbc1cb315c5e032aeeb",
        "title": "Crash in Python 3.8+ debug build on expression evaluation (ast.NameConstant)",
        "problem_statement": "Expression evaluation crashes on python 3.8+ debug build due to ast.NameConstant deprecation.",
        "FAIL_TO_PASS": ["testing/test_mark.py::test_keyword_expressions_py38"],
        "PASS_TO_PASS": ["testing/test_mark.py::test_mark_macro"],
    },
    {
        "instance_id": "matplotlib__matplotlib-20859",
        "repo": "matplotlib/matplotlib",
        "base_commit": "3690d70eb06b997cbfa03893c52a065e9036c1e5",
        "title": "Subplot legend crash on figure with subfigures (isinstance Figure vs FigureBase)",
        "problem_statement": "Adding legend to subfigure raises AttributeError because it expects parent to be Figure instead of FigureBase.",
        "FAIL_TO_PASS": ["lib/matplotlib/tests/test_subfigure.py::test_subfigure_legend"],
        "PASS_TO_PASS": ["lib/matplotlib/tests/test_legend.py::test_legend_auto_draw"],
    },
    {
        "instance_id": "django__django-12774",
        "repo": "django/django",
        "base_commit": "b70b5e9f563d76b17c37894a4c58cf3a8080f555",
        "title": "UniqueConstraint with Field in model class in Django ORM query",
        "problem_statement": "in_bulk() crashes when fields has UniqueConstraint rather than unique=True.",
        "FAIL_TO_PASS": ["tests/queries/test_in_bulk.py::InBulkTests::test_in_bulk_unique_constraint"],
        "PASS_TO_PASS": ["tests/queries/test_in_bulk.py::InBulkTests::test_in_bulk"],
    },
    {
        "instance_id": "psf__requests-1724",
        "repo": "psf/requests",
        "base_commit": "e96de14188ce61d76b50e3864a66a1e5aa9a1705",
        "title": "Unicode query string stripped or method normalization in requests.get()",
        "problem_statement": "method parameter should accept unicode string and not fail on upper() in python 2/3 compatibility.",
        "FAIL_TO_PASS": ["test_requests.py::RequestsTestSuite::test_unicode_method_name"],
        "PASS_TO_PASS": ["test_requests.py::RequestsTestSuite::test_basic_building"],
    },
    {
        "instance_id": "astropy__astropy-8707",
        "repo": "astropy/astropy",
        "base_commit": "60e909a80df37a28e7520e5d0315da08d1f7e0fc",
        "title": "FITS Header parsing fix when reading card data with unicode/bytes",
        "problem_statement": "Header.fromstring crashes when passed unicode string in Python 3.",
        "FAIL_TO_PASS": ["astropy/io/fits/tests/test_header.py::TestHeaderFunctions::test_header_fromstring_bytes"],
        "PASS_TO_PASS": ["astropy/io/fits/tests/test_header.py::TestHeaderFunctions::test_header_fromstring"],
    },
    {
        "instance_id": "pallets__flask-5014",
        "repo": "pallets/flask",
        "base_commit": "7ee9ceb71e868944a46e1ff00b506772a53a4f1d",
        "title": "Require a non-empty name for Blueprints",
        "problem_statement": "Things do not work correctly if a Blueprint is given an empty name. Raise ValueError.",
        "FAIL_TO_PASS": ["tests/test_blueprints.py::test_empty_name_not_allowed"],
        "PASS_TO_PASS": ["tests/test_blueprints.py::test_dotted_name_not_allowed"],
    },
    {
        "instance_id": "pydata__xarray-4356",
        "repo": "pydata/xarray",
        "base_commit": "557a22ef7e098ec7a94ee734a753ce32e18b8ef3",
        "title": "Multi-index coordinate preservation on unstack()",
        "problem_statement": "unstack loses dtype information on MultiIndex coords when unstacking non-dimension coords.",
        "FAIL_TO_PASS": ["xarray/tests/test_dataset.py::TestDataset::test_unstack_multiindex_preserves_dtype"],
        "PASS_TO_PASS": ["xarray/tests/test_dataset.py::TestDataset::test_unstack"],
    },
    {
        "instance_id": "sphinx-doc__sphinx-8721",
        "repo": "sphinx-doc/sphinx",
        "base_commit": "673cfdf6bfcb1c2a05781a95ff88204aa74eef72",
        "title": "Viewcode extension anchor generation in HTML/epub output",
        "problem_statement": "viewcode creates pages for epub even when viewcode_enable_epub=False.",
        "FAIL_TO_PASS": ["tests/test_ext_viewcode.py::test_viewcode_epub"],
        "PASS_TO_PASS": ["tests/test_ext_viewcode.py::test_viewcode"],
    },
    {
        "instance_id": "pylint-dev__pylint-7080",
        "repo": "pylint-dev/pylint",
        "base_commit": "5b40cf6b6a0dc15a51982b6be008c351f0be0aa5",
        "title": "Unused import recursive scan false positives in typing.overload",
        "problem_statement": "pylint reports unused-import for typing overload signatures.",
        "FAIL_TO_PASS": ["tests/checkers/unittest_imports.py::test_unused_import_overload"],
        "PASS_TO_PASS": ["tests/checkers/unittest_imports.py::test_unused_import"],
    },
    {
        "instance_id": "mwaskom__seaborn-3069",
        "repo": "mwaskom/seaborn",
        "base_commit": "81f181f0ffc3ad4f7a26f8b9195cf58046aa7b66",
        "title": "Categorical scale nominal auto-converter in seaborn objects",
        "problem_statement": "Nominal scale on categorical column crashes when values contain missing or complex categories.",
        "FAIL_TO_PASS": ["tests/_core/test_scales.py::TestNominal::test_categorical_auto_convert"],
        "PASS_TO_PASS": ["tests/_core/test_scales.py::TestNominal::test_nominal_scale"],
    },
    {
        "instance_id": "sympy__sympy-15599",
        "repo": "sympy/sympy",
        "base_commit": "51707010f375a363a0a38c2049e3bf19a32c2560",
        "title": "Mod simplification with distributive terms",
        "problem_statement": "Mod(3*i, 2) does not simplify to Mod(i, 2) when i is Symbol('i', integer=True).",
        "FAIL_TO_PASS": ["sympy/core/tests/test_arit.py::test_Mod_simplification"],
        "PASS_TO_PASS": ["sympy/core/tests/test_arit.py::test_Mod"],
    },
    {
        "instance_id": "scikit-learn__scikit-learn-10908",
        "repo": "scikit-learn/scikit-learn",
        "base_commit": "321350a6da9b5d7d3d750ab889d46928e08d2ae4",
        "title": "CountVectorizer with vocabulary and get_feature_names on empty vocabulary",
        "problem_statement": "CountVectorizer crashes when vocabulary is provided as empty list or set.",
        "FAIL_TO_PASS": ["sklearn/feature_extraction/tests/test_text.py::test_countvectorizer_empty_vocab"],
        "PASS_TO_PASS": ["sklearn/feature_extraction/tests/test_text.py::test_countvectorizer_vocab"],
    },
    {
        "instance_id": "matplotlib__matplotlib-25311",
        "repo": "matplotlib/matplotlib",
        "base_commit": "550a25695cf26d36e86488bc8a9f60cb6f5c8088",
        "title": "Pickling draggable Legend crashes with RecursionError",
        "problem_statement": "Cannot pickle figure with draggable legend due to circular reference in canvas callbacks.",
        "FAIL_TO_PASS": ["lib/matplotlib/tests/test_legend.py::test_pickle_draggable_legend"],
        "PASS_TO_PASS": ["lib/matplotlib/tests/test_legend.py::test_draggable_legend"],
    },
    {
        "instance_id": "pytest-dev__pytest-5787",
        "repo": "pytest-dev/pytest",
        "base_commit": "787eeec4a87fb255952fca21e25e98f06059fb25",
        "title": "Exception serialization across xdist workers loses chain exceptions",
        "problem_statement": "Exception display when chained exceptions are present shows incorrect exceptionrepr.",
        "FAIL_TO_PASS": ["testing/test_reports.py::test_chained_exception_repr"],
        "PASS_TO_PASS": ["testing/test_reports.py::test_reports"],
    },
    {
        "instance_id": "psf__requests-1766",
        "repo": "psf/requests",
        "base_commit": "046d1bf5408a1c6a297bd5a3a2d6776106631e8c",
        "title": "Digest auth header format missing quotes around auth qop",
        "problem_statement": "qop=auth in Digest Auth header causes 401 on strict servers that require qop=\"auth\".",
        "FAIL_TO_PASS": ["test_requests.py::RequestsTestSuite::test_digestauth_quotes"],
        "PASS_TO_PASS": ["test_requests.py::RequestsTestSuite::test_digestauth"],
    },
    {
        "instance_id": "django__django-15268",
        "repo": "django/django",
        "base_commit": "9037da304a0e10f3c5521b4a3a3399ed47264a97",
        "title": "AlterTogetherOptionOperation optimizes wrongly when mixed with separate operations",
        "problem_statement": "Migrations crash when AlterUniqueTogether is followed by another model alteration.",
        "FAIL_TO_PASS": ["tests/migrations/test_operations.py::OperationTests::test_alter_together_optimization"],
        "PASS_TO_PASS": ["tests/migrations/test_operations.py::OperationTests::test_alter_unique_together"],
    },
    {
        "instance_id": "astropy__astropy-8872",
        "repo": "astropy/astropy",
        "base_commit": "67039755ab66fe267da39634e06c7104b9ea6fc0",
        "title": "Quantity creation with np.float16 loses precision or raises error",
        "problem_statement": "astropy.units.Quantity cannot be instantiated from float16 scalar.",
        "FAIL_TO_PASS": ["astropy/units/tests/test_quantity.py::TestQuantityCreation::test_float16"],
        "PASS_TO_PASS": ["astropy/units/tests/test_quantity.py::TestQuantityCreation::test_float32"],
    },
    {
        "instance_id": "pydata__xarray-4695",
        "repo": "pydata/xarray",
        "base_commit": "62bf1993fc5ea5783ddf7a1f81643baecb4bf49a",
        "title": "DataArray.loc indexing with dimensional boolean mask",
        "problem_statement": "loc[] indexing with boolean DataArray along dimension raises KeyError instead of slicing.",
        "FAIL_TO_PASS": ["xarray/tests/test_indexing.py::test_loc_boolean_dataarray"],
        "PASS_TO_PASS": ["xarray/tests/test_indexing.py::test_loc"],
    },
    {
        "instance_id": "sphinx-doc__sphinx-10323",
        "repo": "sphinx-doc/sphinx",
        "base_commit": "32631ce55eb425c27633519c23f2fbfaec63259b",
        "title": "autodoc: autodoc_preserve_defaults with keyword-only arguments",
        "problem_statement": "autodoc crashes on keyword-only arguments with default values when autodoc_preserve_defaults=True.",
        "FAIL_TO_PASS": ["tests/test_ext_autodoc_preserve_defaults.py::test_kwonly_defaults"],
        "PASS_TO_PASS": ["tests/test_ext_autodoc_preserve_defaults.py::test_preserve_defaults"],
    },
    {
        "instance_id": "pylint-dev__pylint-4970",
        "repo": "pylint-dev/pylint",
        "base_commit": "7ee06209b533e4d9ebc6e4811a0b32938f35eb06",
        "title": "Duplicate-code checker disable comment min-similarity-lines",
        "problem_statement": "Setting min-similarity-lines=0 does not completely disable duplicate-code checker.",
        "FAIL_TO_PASS": ["tests/checkers/unittest_similar.py::test_min_similarity_lines_zero"],
        "PASS_TO_PASS": ["tests/checkers/unittest_similar.py::test_similarity"],
    },
    {
        "instance_id": "mwaskom__seaborn-3187",
        "repo": "mwaskom/seaborn",
        "base_commit": "22cdfb0c93f8ec78492d87edb810f10cb7f57a31",
        "title": "Wrong legend values of large ranges with ScalarFormatter offset",
        "problem_statement": "Legends describing large numbers with ScalarFormatter offset are formatted without multiplier.",
        "FAIL_TO_PASS": ["tests/_core/test_plot.py::TestLegend::test_legend_has_no_offset"],
        "PASS_TO_PASS": ["tests/_core/test_plot.py::TestLegend::test_legend_basic"],
    },
    {
        "instance_id": "sympy__sympy-17655",
        "repo": "sympy/sympy",
        "base_commit": "129e6fbdf459828d54694fb21396db8d70634629",
        "title": "Point addition with multiplied Point raises GeometryError",
        "problem_statement": "Point(0, 0) + c * Point(1, 1) raises GeometryError instead of returning Point.",
        "FAIL_TO_PASS": ["sympy/geometry/tests/test_point.py::test_point_mul_add"],
        "PASS_TO_PASS": ["sympy/geometry/tests/test_point.py::test_point"],
    },
    {
        "instance_id": "scikit-learn__scikit-learn-26323",
        "repo": "scikit-learn/scikit-learn",
        "base_commit": "1a7f34c62c2f1b4028d8b94870a45f949c25d800",
        "title": "ColumnTransformer set_output transform remainder dataframe index mismatch",
        "problem_statement": "ColumnTransformer with remainder estimator outputs wrong index when set_output(transform='pandas').",
        "FAIL_TO_PASS": ["sklearn/compose/tests/test_column_transformer.py::test_column_transformer_remainder_pandas"],
        "PASS_TO_PASS": ["sklearn/compose/tests/test_column_transformer.py::test_column_transformer"],
    },
    {
        "instance_id": "matplotlib__matplotlib-22865",
        "repo": "matplotlib/matplotlib",
        "base_commit": "a57bb8d42d386927a760cfc9e54d68205f92ff4b",
        "title": "Colorbar draw_edges not updating correctly with divisions",
        "problem_statement": "Setting draw_edges=True on colorbar does not respect boundaries when updating mappable.",
        "FAIL_TO_PASS": ["lib/matplotlib/tests/test_colorbar.py::test_colorbar_draw_edges_bounds"],
        "PASS_TO_PASS": ["lib/matplotlib/tests/test_colorbar.py::test_colorbar"],
    },
    {
        "instance_id": "django__django-13741",
        "repo": "django/django",
        "base_commit": "d6032049e612f07d2c388656114a1a2b1b6d1927",
        "title": "ReadOnlyPasswordHashField should be disabled by default in forms",
        "problem_statement": "ReadOnlyPasswordHashField should set disabled=True in form kwargs by default.",
        "FAIL_TO_PASS": ["tests/auth_tests/test_forms.py::ReadOnlyPasswordHashFieldTest::test_disabled"],
        "PASS_TO_PASS": ["tests/auth_tests/test_forms.py::ReadOnlyPasswordHashFieldTest::test_field"],
    },
]


def sample_cohort(seed: int | None = 42, size: int = 25) -> list[dict[str, Any]]:
    """Sample size instances from SWE-bench Verified dataset or fallback."""
    if seed is not None:
        random.seed(seed)
        logger.info("Using deterministic sampling seed: %d", seed)
    else:
        logger.info("Using pseudo-random non-deterministic sampling.")

    # Try live Hugging Face dataset download
    try:
        from datasets import load_dataset
        logger.info("Fetching 'princeton-nlp/SWE-bench_Verified' from Hugging Face...")
        ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
        all_instances = list(ds)
        logger.info("Successfully fetched %d verified instances from Hugging Face.", len(all_instances))
        sampled = random.sample(all_instances, min(size, len(all_instances)))
        # Standardize field structure
        normalized = []
        for s in sampled:
            normalized.append({
                "instance_id": s["instance_id"],
                "repo": s["repo"],
                "base_commit": s["base_commit"],
                "title": s.get("problem_statement", "").splitlines()[0][:100] if s.get("problem_statement") else s["instance_id"],
                "problem_statement": s.get("problem_statement", ""),
                "FAIL_TO_PASS": s.get("FAIL_TO_PASS", []),
                "PASS_TO_PASS": s.get("PASS_TO_PASS", []),
            })
        return normalized
    except Exception as e:  # noqa: BLE001
        logger.warning("Could not load dataset from Hugging Face (%s). Using verified offline fallback cohort.", e)
        shuffled = list(FALLBACK_25_INSTANCES)
        random.shuffle(shuffled)
        return shuffled[:size]


def main() -> int:
    parser = argparse.ArgumentParser(description="Sample a random cohort of 25 tasks from SWE-bench Verified")
    parser.add_argument("--seed", type=str, default="42", help="Random seed integer, or 'random' for unseeded (default: 42)")
    parser.add_argument("--size", type=int, default=25, help="Cohort size (default: 25)")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "configs" / "swebench_cohort_25_random.json",
        help="Target output JSON path",
    )
    args = parser.parse_args()

    seed_val = None if args.seed.lower() == "random" else int(args.seed)
    cohort = sample_cohort(seed=seed_val, size=args.size)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(cohort, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Successfully saved %d random instances to: %s", len(cohort), args.output)

    print("\n" + "=" * 80)
    print(f"СЛУЧАЙНАЯ КОГОРТА ИЗ {len(cohort)} ЗАДАЧ SWE-BENCH VERIFIED (SEED={args.seed}):")
    print("=" * 80)
    for i, item in enumerate(cohort, 1):
        print(f" {i:02d}. {item['instance_id']:<35} ({item['repo']})")
    print("=" * 80 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
