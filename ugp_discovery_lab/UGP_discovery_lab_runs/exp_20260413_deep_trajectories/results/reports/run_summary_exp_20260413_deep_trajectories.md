# run_summary_exp_20260413_deep_trajectories

*Generated: 2026-04-13T07:18:45.454053*


## Run Summary: exp_20260413_deep_trajectories

**Timestamp:** 2026-04-13T07:18:45.453908  
**Total Tasks:** 24  
**Successful:** 24  
**Failed:** 0  
**Success Rate:** 100.0%

### Experiment Results

#### gte_deep_trajectories

**Status:** completed

### Detailed Results

See individual JSON reports in the reports directory for detailed data.

### Configuration

```yaml
{
  "experiment": {
    "name": "gte_deep_trajectories",
    "description": "Generate 50K-step GTE trajectories for all 4 canonical seeds, 3 laws, 2 windows",
    "steps": 50000,
    "windows": [
      10,
      11
    ],
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
        "c_policy": "repunit",
        "b_policy": "fib",
        "a_policy": "gte",
        "mirror": "d2",
        "repunit_base": 3
      }
    ],
    "report": {
      "export_md": true,
      "export_json": true
    }
  }
}
```

