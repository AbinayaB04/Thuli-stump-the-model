# Open-Set Rejection Status

The open-set rejection mechanism for the Stump the Model pipeline is implemented, meaning the system can formally output `MATCH`, `UNCERTAIN`, or `NO_MATCH` based on inner-product similarity scores.

**Important Note**: The current thresholds used to make these decisions are strictly **provisional placeholders** (`THRESHOLD_STATUS = "UNVALIDATED_PLACEHOLDER"`). 

Because verified calibration data (i.e., a rigorously verified set of known-match and known-out-of-distribution photos) was unavailable during this phase of the project, we did not attempt to fabricate accuracy metrics or artificially tune the thresholds. The rejection logic exists structurally, but it requires a future data collection and calibration phase before the thresholds can be considered scientifically validated.
