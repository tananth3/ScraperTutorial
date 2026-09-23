import boto3
import pandas as pd
import requests
from datetime import datetime


def timenow():
    return datetime.strftime(datetime.now(), "%m-%d-%Y %H:%M:%S")


def scraper_gp_api(url, driver):
    def fetch():
        print(f"fetching outages from {url}")

        current_state_url = "https://kubra.io/stormcenter/api/v1/stormcenters/7b38c047-7950-444b-a25c-9b3e5ab986eb/views/67b44af5-3847-4ca3-9f4e-9190aac343d6/currentState?preview=false"
        generation_path = requests.get(current_state_url).json()["data"]["interval_generation_data"]

        report_url = f"https://kubra.io/{generation_path}/public/reports/59c1e70f-68f4-4dcb-a92e-c096199a1ebf_report.json"
        return requests.get(report_url).json()

    def parse():
        return {"per_County": _parse(fetch())}

    def _parse(report_data):
        areas = report_data.get("file_data", {}).get("areas", [])
        records = [{
            "County": area.get("name"),
            "Customers Affected": area.get("cust_a", {}).get("val"),
            "Customers Served": area.get("cust_s"),
            "Outages": area.get("n_out"),
        } for area in areas]

        df = pd.DataFrame(records)
        if len(df) > 0:
            df["timestamp"] = timenow()
        return df

    return parse()


def handler(event, context):
    s3 = boto3.client("s3")
    bucket = "tananthtutorialbucketing"

    url = "https://outagemap.georgiapower.com/"
    data = scraper_gp_api(url, None)

    for key, df in data.items():
        current_time = timenow()
        filename = f"GeorgiaPower_{key}_{current_time}.csv"
        csv_buffer = pd.DataFrame(df).to_csv(index=False)
        s3.put_object(Bucket=bucket, Key=filename, Body=csv_buffer)

    return {
        "statusCode": 200,
        "body": "Successfully scraped Georgia Power outage map!",
    }
