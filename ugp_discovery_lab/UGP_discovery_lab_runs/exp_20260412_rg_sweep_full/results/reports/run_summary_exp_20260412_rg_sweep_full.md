# run_summary_exp_20260412_rg_sweep_full

*Generated: 2026-04-12T23:40:36.031162*


## Run Summary: exp_20260412_rg_sweep_full

**Timestamp:** 2026-04-12T23:40:36.031039  
**Total Tasks:** 224  
**Successful:** 224  
**Failed:** 0  
**Success Rate:** 100.0%

### Experiment Results

#### rg_sweep

**Status:** completed

**Discoveries:**
- Fixed points detected in 224 runs
- Average fixed point: α = 0.276719
- Limit cycles detected in 196 runs

### Detailed Results

See individual JSON reports in the reports directory for detailed data.

### Configuration

```yaml
{
  "experiment": {
    "name": "rg_sweep",
    "description": "Extended RG exploration across policies and seeds",
    "inputs": {
      "runs": [
        "UGP_discovery_lab_runs/exp_*/results/reports/experiment_results.json",
        "UGP_discovery_lab_runs/exp_*/results/reports/*_results.json"
      ]
    },
    "rg": {
      "iterations": 12,
      "crop_policy": "center",
      "rescale_policy": "normalize",
      "tol_plane": "1e-4",
      "tol_param": "1e-4",
      "tol_cycle": "1e-5"
    },
    "param_grid": {
      "seeds": [
        [
          1,
          73,
          823
        ],
        [
          1,
          73,
          2137
        ],
        [
          2,
          89,
          1597
        ],
        [
          3,
          97,
          2203
        ]
      ],
      "windows": [
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15
      ],
      "laws": [
        {
          "c_policy": "mersenne",
          "b_policy": "fib",
          "a_policy": "gte",
          "mirror": "d2"
        },
        {
          "c_policy": "mersenne",
          "b_policy": "lucas",
          "a_policy": "gte",
          "mirror": "d2"
        },
        {
          "c_policy": "mersenne",
          "b_policy": "fib",
          "a_policy": "gte",
          "mirror": "d4"
        },
        {
          "c_policy": "mersenne",
          "b_policy": "fib",
          "a_policy": "gte",
          "mirror": "d5"
        },
        {
          "c_policy": "mersenne",
          "b_policy": "fib",
          "a_policy": "gte",
          "mirror": "d6"
        },
        {
          "c_policy": "repunit",
          "repunit_base": 3,
          "b_policy": "fib",
          "a_policy": "gte",
          "mirror": "d2"
        },
        {
          "c_policy": "repunit",
          "repunit_base": 3,
          "b_policy": "lucas",
          "a_policy": "gte",
          "mirror": "d2"
        }
      ]
    },
    "fit": {
      "model": "kM = kG + alpha*kL"
    },
    "run": {
      "steps": 1000,
      "window": 64,
      "seed": [
        42,
        173,
        823
      ]
    },
    "report": {
      "export_md": true,
      "export_json": true,
      "plots": true
    }
  }
}
```

