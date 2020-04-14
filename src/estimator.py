import json

def normalise_duration_in_days(duration, period_type):
    if period_type == "weeks":
        return duration * 7
    elif period_type == "months":
        return duration * 30
    return duration


def estimator(data):
    impact = {}
    severeImpact = {}
    output = {"data": data, "impact": impact, "severeImpact": severeImpact}

    # challenge 1
    impact["currentlyInfected"] = data["reportedCases"] * 10
    severeImpact["currentlyInfected"] = data["reportedCases"] * 50

    duration_in_days = normalise_duration_in_days(
        data["timeToElapse"], data["periodType"]
    )
    factor = duration_in_days // 3
    impact["infectionsByRequestedTime"] = impact["currentlyInfected"] * (2 ** factor)
    severeImpact["infectionsByRequestedTime"] = severeImpact["currentlyInfected"] * (
        2 ** factor
    )
    return json.dumps(output)
