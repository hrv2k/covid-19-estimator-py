import os
from flask import Flask, g, jsonify, request, Response
import logging
import dicttoxml
import json
import time

DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)

logger = logging.getLogger(__name__)
file_handler = logging.FileHandler("estimator.log")
# file_line_format = logging.Formatter("")
logger.addHandler(file_handler)
app.logger.addHandler(file_handler)


def normalise_duration_in_days(time_to_elapse, period_type):
    if period_type == "weeks":
        return time_to_elapse * 7
    elif period_type == "months":
        return time_to_elapse * 30
    return time_to_elapse


def currently_infected(reported_cases, multiplier):
    return reported_cases * multiplier


def infections_by_requested_time(currently_infected, time_to_elapse_in_days):
    factor = time_to_elapse_in_days // 3
    return currently_infected * (2 ** factor)


def severe_cases_by_requested_time(infections_by_requested_time, severity_rate):
    return infections_by_requested_time * severity_rate


def hospital_beds_by_requested_time(
    total_hospital_beds,
    infections_by_requested_time,
    expected_beds_availability,
    severity_rate,
):
    expected_beds_available = total_hospital_beds * expected_beds_availability
    remainder_beds = expected_beds_available - severe_cases_by_requested_time(
        infections_by_requested_time, severity_rate
    )
    if remainder_beds >= 0:
        return expected_beds_available
    return remainder_beds


def cases_icu_by_requested_time(infections_by_requested_time, icu_care_rate):
    return infections_by_requested_time * icu_care_rate


def cases_ventilators_by_requested_time(infections_by_requested_time, ventilator_rate):
    return infections_by_requested_time * ventilator_rate


def dollars_in_flight(
    infections_by_requested_time,
    avg_working_pop,
    avg_daily_income_usd,
    time_to_elapse_in_days,
):
    return (
        infections_by_requested_time * avg_working_pop * avg_daily_income_usd
    ) / time_to_elapse_in_days


def estimator(data):
    impact = {}
    severeImpact = {}
    output = {"data": data, "impact": impact, "severeImpact": severeImpact}

    time_to_elapse_in_days = normalise_duration_in_days(
        data["timeToElapse"], data["periodType"]
    )

    # challenge 1
    impact["currentlyInfected"] = int(currently_infected(data["reportedCases"], 10))
    severeImpact["currentlyInfected"] = int(
        currently_infected(data["reportedCases"], 50)
    )

    impact["infectionsByRequestedTime"] = int(
        infections_by_requested_time(
            impact["currentlyInfected"], time_to_elapse_in_days
        )
    )

    severeImpact["infectionsByRequestedTime"] = int(
        infections_by_requested_time(
            severeImpact["currentlyInfected"], time_to_elapse_in_days
        )
    )

    # challenge 2
    impact["severeCasesByRequestedTime"] = int(
        severe_cases_by_requested_time(impact["infectionsByRequestedTime"], 0.15)
    )
    severeImpact["severeCasesByRequestedTime"] = int(
        severe_cases_by_requested_time(severeImpact["infectionsByRequestedTime"], 0.15)
    )

    impact["hospitalBedsByRequestedTime"] = int(
        hospital_beds_by_requested_time(
            data["totalHospitalBeds"], impact["infectionsByRequestedTime"], 0.35, 0.15
        )
    )
    severeImpact["hospitalBedsByRequestedTime"] = int(
        hospital_beds_by_requested_time(
            data["totalHospitalBeds"],
            severeImpact["infectionsByRequestedTime"],
            0.35,
            0.15,
        )
    )

    # challenge 3
    impact["casesForICUByRequestedTime"] = int(
        cases_icu_by_requested_time(impact["infectionsByRequestedTime"], 0.05)
    )
    severeImpact["casesForICUByRequestedTime"] = int(
        cases_icu_by_requested_time(severeImpact["infectionsByRequestedTime"], 0.05)
    )

    impact["casesForVentilatorsByRequestedTime"] = int(
        cases_ventilators_by_requested_time(impact["infectionsByRequestedTime"], 0.02)
    )
    severeImpact["casesForVentilatorsByRequestedTime"] = int(
        cases_ventilators_by_requested_time(
            severeImpact["infectionsByRequestedTime"], 0.02
        )
    )

    impact["dollarsInFlight"] = int(
        dollars_in_flight(
            impact["infectionsByRequestedTime"],
            data["region"]["avgDailyIncomePopulation"],
            data["region"]["avgDailyIncomeInUSD"],
            time_to_elapse_in_days,
        )
    )
    severeImpact["dollarsInFlight"] = int(
        dollars_in_flight(
            severeImpact["infectionsByRequestedTime"],
            data["region"]["avgDailyIncomePopulation"],
            data["region"]["avgDailyIncomeInUSD"],
            time_to_elapse_in_days,
        )
    )

    return output


@app.route("/api/v1/on-covid-19", methods=["POST"])
@app.route("/api/v1/on-covid-19/json", methods=["POST"])
def covid19_estimator():
    data = request.get_json()
    estimation = estimator(data)
    data_json = json.dumps(estimation)
    return jsonify(estimation)
    # return Response(data_json, status=200, mimetype="application/json")


@app.route("/api/v1/on-covid-19/xml", methods=["POST"])
def covid19_estimator_xml():
    data = request.get_json()
    estimation = estimator(data)
    xml = dicttoxml.dicttoxml(estimation)
    return Response(xml, status=200, mimetype="application/xml")


@app.route("/api/v1/on-covid-19/logs", methods=["GET"])
def requests_logs():
    logs = []
    with open("estimator.log", "r") as log_file:
        for line in log_file:
            logs.append(line)

    resp = Response("".join(logs), status=200, mimetype="text/plain")
    resp.headers["Content-Type"] = "text/plain; charset=utf-8"
    return resp


@app.route("/api/v1/on-covid-19/test", methods=["GET"])
def test_estimator():
    data = {
        "region": {
            "name": "Africa",
            "avgAge": 19.7,
            "avgDailyIncomeInUSD": 3,
            "avgDailyIncomePopulation": 0.56,
        },
        "periodType": "months",
        "timeToElapse": 3,
        "reportedCases": 1718,
        "population": 6759997,
        "totalHospitalBeds": 94314,
    }
    estimation = estimator(data)
    return jsonify(estimation)


@app.route("/", methods=["GET"])
def home():
    response_object = {"status": "success", "message": "covid19-estimator"}
    return jsonify(response_object)


@app.before_request
def start_time():
    g.request_start_time = time.time()


@app.after_request
def log_request(response):
    now = time.time()
    duration = "{:02}ms".format(int((now - g.request_start_time)*1000))
    # line = f"{request.method}\t\t{request.path}\t\t{response.status_code}\t\t{duration}"
    # app.logger.info(
    #     "{:4}\t{:26} {:>5}\t{:^3}".format(
    #         request.method, request.path, response.status_code, duration
    #     )
    # )
    app.logger.info(
        "{} {} {} {}".format(
            request.method, request.path, response.status_code, duration
        )
    )
    return response


if __name__ == "__main__":
    # app.run()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
