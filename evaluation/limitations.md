# Evaluation Limitations

## Hidden set
The hidden set was not distributed and was not available to this project. It must not be evaluated or claimed. The first hidden-set run should be a single final run with the report recording its date and system version.

## Human citation and hallucination review
No human assessor is available to this implementation. The project does not claim a measured hallucination rate or semantic citation-accuracy rate. Automated checks establish only that citations resolve to retrieved passage identifiers and that prohibited commitments/private data are absent.

Before deployment:
- Review at least fifty generated responses.
- Use two independent assessors.
- Report agreement rate and disagreement resolution.
- Classify each factual claim as supported, unsupported or irrelevant.
- Calculate hallucination rate as the share of responses containing at least one unsupported claim.
- Calculate citation accuracy by checking whether each cited passage supports the attached claim.

## Confidence calibration
The held-out development split produced a calibration report. It found calibration error in every confidence band and should not be described as calibrated. The threshold 0.30 is a development holdout starting point, not a validated hidden-set threshold.

## Business outcomes
First-contact resolution, satisfaction and repeat contacts cannot be measured from the supplied dataset as live business outcomes. Historical fields are baselines only.
