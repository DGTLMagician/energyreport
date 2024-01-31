import datetime
import json
import logging
import os
import sys
import requests
import calendar
import html
import matplotlib.pyplot as plt
import numpy as np
import smtplib

from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from openai import OpenAI
from jinja2 import Template
from getpass import getpass
from garth.exc import GarthHTTPError
from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

def get_sleep_feedback_explanation(sleep_feedback):
    feedback_mapping = {
        'NEGATIVE_NOT_RESTORATIVE': "Sleep is observed to be non-restorative, likely indicating poor sleep quality. This could be due to various factors such as stress, late bedtime, or other disturbances.",
        'NEGATIVE_LONG_BUT_NOT_RESTORATIVE': "Although sleep duration is extended, it is still not restorative. This may be influenced by factors like very strenuous exercise, impacting the overall restfulness of the sleep.",
        'NEGATIVE_SHORT_AND_POOR_QUALITY': "Sleep duration is short, and the quality is poor. This could be a result of insufficient sleep time or other factors affecting the overall sleep experience.",
        'NEGATIVE_SHORT_AND_NONRECOVERING': "Sleep is short, and there's inadequate recovery, likely influenced by factors such as late bedtime. The sleep lacks the necessary duration for proper restoration.",
        'POSITIVE_OPTIMAL_STRUCTURE': "Sleep is structured optimally, suggesting a positive sleep pattern without any notable issues or disturbances. This is indicative of good sleep quality.",
        'POSITIVE_LONG_AND_CALM': "Sleep duration is long and characterized by a calm state. This positive sleep pattern is observed, potentially contributing to better overall well-being.",
        'POSITIVE_LONG_AND_CONTINUOUS': "Sleep duration is both long and continuous, implying a positive and uninterrupted sleep experience. This is generally associated with better restfulness.",
        'POSITIVE_DEEP': "Deep sleep is observed, indicating a positive aspect of the sleep cycle. However, it might be impacted by external factors, such as a stressful day, affecting the overall sleep experience."
    }
    return feedback_mapping.get(sleep_feedback, sleep_feedback)

def get_sleep_insight_explanation(sleep_insight):
    insight_mapping = {
        'NONE': "No specific sleep insight is identified. This could mean that there are no notable external factors influencing the sleep pattern during the analyzed period.",
        'NEGATIVE_LATE_BED_TIME': "Sleep is negatively affected by a late bedtime. Going to bed late may disrupt the natural sleep-wake cycle, potentially leading to difficulties in falling asleep or achieving restorative sleep.",
        'NEGATIVE_VERY_STRENUOUS_EXERCISE': "Intense or very strenuous exercise close to bedtime negatively impacts sleep quality. The body needs time to wind down, and vigorous exercise shortly before sleep may interfere with this process.",
        'NEGATIVE_STRESSFUL_DAY': "Sleep is negatively affected by a stressful day. High stress levels can interfere with the ability to relax and unwind, potentially impacting the overall quality of sleep.",
        'POSITIVE_EXERCISE': "The positive influence of exercise on sleep is observed. Regular physical activity is known to contribute to better sleep quality and overall well-being.",
        'POSITIVE_LATE_BED_TIME': "Going to bed late is observed as a positive factor in this context. It's important to note that individual sleep preferences and rhythms can vary, and for some, a later bedtime may align with better sleep quality."
    }
    return insight_mapping.get(sleep_insight, sleep_insight)

def extract_values(json_data):
    return [
        {"date": entry["date"], "charged": entry["charged"], "drained": entry["drained"]}
        for entry in json_data
    ]

def init_api(email, password, tokenstore, tokenstore_base64):
    try:
        garmin = Garmin()
        garmin.login(tokenstore)
    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        print(
            "Login tokens not present, login with your Garmin Connect credentials to generate them.\n"
            f"They will be stored in '{tokenstore}' for future use.\n"
        )
        try:
            if not email or not password:
                email, password = get_credentials()

            garmin = Garmin(email, password)
            garmin.login()
            garmin.garth.dump(tokenstore)
            print(
                f"Oauth tokens stored in '{tokenstore}' directory for future use. (first method)\n"
            )
            token_base64 = garmin.garth.dumps()
            dir_path = os.path.expanduser(tokenstore_base64)
            with open(dir_path, "w") as token_file:
                token_file.write(token_base64)
            print(
                f"Oauth tokens encoded as base64 string and saved to '{dir_path}' file for future use. (second method)\n"
            )
        except (
            FileNotFoundError,
            GarthHTTPError,
            GarminConnectAuthenticationError,
            requests.exceptions.HTTPError,
        ) as err:
            logger.error(err)
            return None

    return garmin

def save_drained_vs_charged_plot(data):
    dates = [entry["date"] for entry in data]
    charged = [entry["charged"] for entry in data]
    drained = [entry["drained"] for entry in data]
    avg_stress_level = [entry["avg_stress_level"] for entry in data]
    max_stress_level = [entry["max_stress_level"] for entry in data]
    sleep_seconds = [entry["sleep_seconds"] for entry in data]
    deep_sleep_seconds = [entry["deep_sleep_seconds"] for entry in data]
    light_sleep_seconds = [entry["light_sleep_seconds"] for entry in data]
    rem_sleep_seconds = [entry["rem_sleep_seconds"] for entry in data]
    awake_sleep_seconds = [entry["awake_sleep_seconds"] for entry in data]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(dates, charged, label="Charged", marker="o")
    ax.plot(dates, drained, label="Drained", marker="o")

    for i in range(len(dates)):
        if charged[i] > drained[i]:
            ax.bar(dates[i], max(charged[i], drained[i]), color="green", alpha=0.3)
        else:
            ax.bar(dates[i], max(charged[i], drained[i]), color="red", alpha=0.3)

    ax.set_xlabel("Date")
    ax.set_ylabel("Value")
    ax.set_title("Charged vs Drained")
    ax.legend()
    ax.grid(True)
    ax.set_xticks(dates)
    ax.set_xticklabels(dates, rotation=45)
    fig.tight_layout()

    plt.savefig("charged_vs_drained_plot.png")
    plt.close()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(dates, avg_stress_level, label="Average Stress Level", marker="o")
    ax.plot(dates, max_stress_level, label="Max Stress Level", marker="o")

    for i in range(len(dates)):
        if charged[i] > drained[i]:
            ax.bar(dates[i], max(charged[i], drained[i]), color="green", alpha=0.3)
        else:
            ax.bar(dates[i], max(charged[i], drained[i]), color="red", alpha=0.3)

    ax.set_xlabel("Date")
    ax.set_ylabel("Stress Level")
    ax.set_title("Stress Level Statistics")
    ax.legend()
    ax.grid(True)
    ax.set_xticks(dates)
    ax.set_xticklabels(dates, rotation=45)
    fig.tight_layout()

    plt.savefig("stress_level.png")
    plt.close()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(dates, sleep_seconds, label="Sleep Seconds", marker="o")
    ax.plot(dates, deep_sleep_seconds, label="Deep Sleep Seconds", marker="o")
    ax.plot(dates, light_sleep_seconds, label="Light Sleep Seconds", marker="o")
    ax.plot(dates, rem_sleep_seconds, label="REM Sleep Seconds", marker="o")
    ax.plot(dates, awake_sleep_seconds, label="Awake Sleep Seconds", marker="o")

    for i in range(len(dates)):
        if charged[i] > drained[i]:
            ax.bar(dates[i], max(charged[i], drained[i]), color="green", alpha=0.3)
        else:
            ax.bar(dates[i], max(charged[i], drained[i]), color="red", alpha=0.3)

    ax.set_xlabel("Date")
    ax.set_ylabel("Sleep Statistics (Seconds)")
    ax.set_title("Sleep Statistics")
    ax.legend()
    ax.grid(True)
    ax.set_xticks(dates)
    ax.set_xticklabels(dates, rotation=45)
    fig.tight_layout()

    plt.savefig("sleep_statistics.png")
    plt.close()

def generate_energy_balance_analysis(data):
    dates = [entry["date"] for entry in data]
    charged = [entry["charged"] for entry in data]
    drained = [entry["drained"] for entry in data]
    sleep_seconds = [entry["sleep_seconds"] for entry in data]
    avg_stress_level = [entry["avg_stress_level"] for entry in data]
    sleep_feedback = [entry["sleep_feedback"] for entry in data]
    sleep_insight = [entry["sleep_insight"] for entry in data]

    client = OpenAI()
    client.api_key = openai_api_key

    gpt_assistant_prompt = "You are an expert sleep, stress and health expert. You spend all your time analyzing sleep and stress data and how it influences the energy level of people. You will analyse the following data to provide an advice on how to improve daily positive energy balances."
    prompt = f"Analyse the energy balance data from {dates[0]} to {dates[-1]}. Body battery charged and drained, sleep, and stress levels. Also include the sleep insights and sleep feedback so you can identify which factors cause negative energy balance and which factors cause a positive day."
    context = f"\n\nDates: {', '.join(dates)}\nCharged: {', '.join(map(str, charged))}\nDrained: {', '.join(map(str, drained))}\nSleep (seconds): {', '.join(map(str, sleep_seconds))}\nAvg Stress Level: {', '.join(map(str, avg_stress_level))}\nSleep feedback: {', '.join(map(str, sleep_feedback))}\nSleep insight: {', '.join(map(str, sleep_insight))}\n\n"
    input_text = prompt + context
    message = [
        {"role": "assistant", "content": gpt_assistant_prompt},
        {"role": "user", "content": input_text},
    ]

    response = client.chat.completions.create(
        model="gpt-4", messages=message, temperature=0.7, max_tokens=1200
    )

    generated_text = response.choices[0].message.content

    return generated_text

def generate_html_report(
    data, report_output_filename="energy_report.html"
):
    total_charged = sum(entry["charged"] for entry in data)
    total_drained = sum(entry["drained"] for entry in data)
    net_energy_level = total_charged - total_drained

    advice = generate_energy_balance_analysis(data)

    average_trend = "Net Positive" if net_energy_level >= 0 else "Net Negative"

    negative_days = [entry for entry in data if entry["charged"] < entry["drained"]]
    positive_days = [entry for entry in data if entry["charged"] >= entry["drained"]]
    negative_days_array = [
        day for day in data if day["charged"] < day["drained"]
    ]
    positive_days_array = [
        day for day in data if day["charged"] >= day["drained"]
    ]

    if negative_days:
        days_of_week = [
            datetime.datetime.strptime(entry["date"], "%Y-%m-%d").weekday()
            for entry in negative_days
        ]
        day_of_week_counts = [days_of_week.count(day) for day in range(7)]
        max_day_of_week_negative = calendar.day_name[
            day_of_week_counts.index(max(day_of_week_counts))
        ]
    else:
        max_day_of_week_negative = "N/A"

    save_drained_vs_charged_plot(data)

    advice = advice.replace("\n", "<br>")
    advice = advice.replace("** ", "</b>")
    advice = advice.replace("** ", "<b>")

    with open("energy_report_template.html", "r") as file:
        template_content = file.read()

    template = Template(template_content)
    html_report = template.render(
        graph_output_filename="charged_vs_drained_plot.png",
        stress_graph_output_filename="stress_level.png",
        sleep_graph_output_filename="sleep_statistics.png",
        advice=advice,
        total_charged=total_charged,
        total_drained=total_drained,
        net_energy_level=net_energy_level,
        average_trend=average_trend,
        negative_days=len(negative_days),
        positive_days=len(positive_days),
        negative_days_array=negative_days_array,
        positive_days_array=positive_days_array,
        max_day_of_week_negative=max_day_of_week_negative,
    )

    with open(report_output_filename, "w") as report_file:
        report_file.write(html_report)

def send_email_report(to_address, report_output_filename, subject):
    with open(report_output_filename, "r") as f:
        html_report_content = f.read()

    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = from_address
    msg["To"] = to_address

    html_part = MIMEText(html_report_content, "html")

    image_files = [
        "charged_vs_drained_plot.png",
        "stress_level.png",
        "sleep_statistics.png",
    ]
    for image_file in image_files:
        with open(image_file, "rb") as f:
            img = MIMEImage(f.read(), "png")
            img.add_header("Content-ID", "<{}>".format(image_file))
            msg.attach(img)

    for image_file in image_files:
        html_report_content = html_report_content.replace(
            image_file, "cid:{}".format(image_file)
        )

    html_part.set_payload(html_report_content)

    msg.attach(html_part)

    s = smtplib.SMTP(smtp_server, smtp_port)
    s.starttls()
    s.login(smtp_user, smtp_password)
    s.send_message(msg)
    s.quit()

if __name__ == "__main__":
    load_dotenv()

    email = os.getenv("GARMINEMAIL")
    password = os.getenv("GARMINPASSWORD")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
    tokenstore_base64 = (
        os.getenv("GARMINTOKENS_BASE64") or "~/.garminconnect_base64"
    )
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = 587
    from_address = os.getenv("FROM_ADDRESS")
    to_address = os.getenv("SMTP_TO")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    api = None

    if not api:
        api = init_api(email, password, tokenstore, tokenstore_base64)

    today = datetime.date.today()
    startdate = today - datetime.timedelta(days=30)

    bb_result_array = extract_values(
        api.get_body_battery(startdate.isoformat(), today.isoformat())
    )

    combined_data_array = []

    for entry in bb_result_array:
        date = entry["date"]
        sleep_data = api.get_sleep_data(date)
        sleep_seconds = sleep_data["dailySleepDTO"]["sleepTimeSeconds"]
        deep_sleep_seconds = sleep_data["dailySleepDTO"]["deepSleepSeconds"]
        light_sleep_seconds = sleep_data["dailySleepDTO"]["lightSleepSeconds"]
        rem_sleep_seconds = sleep_data["dailySleepDTO"]["remSleepSeconds"]
        awake_sleep_seconds = sleep_data["dailySleepDTO"]["awakeSleepSeconds"]
        sleep_feedback = get_sleep_feedback_explanation(
            sleep_data["dailySleepDTO"]["sleepScoreFeedback"]
        )
        sleep_insight = get_sleep_insight_explanation(
            sleep_data["dailySleepDTO"]["sleepScoreInsight"]
        )

        stress_data = api.get_stress_data(date)
        avg_stress_level = stress_data["avgStressLevel"]
        max_stress_level = stress_data["maxStressLevel"]

        new_entry = {
            "date": date,
            "charged": entry["charged"],
            "drained": entry["drained"],
            "sleep_seconds": sleep_seconds,
            "deep_sleep_seconds": deep_sleep_seconds,
            "light_sleep_seconds": light_sleep_seconds,
            "rem_sleep_seconds": rem_sleep_seconds,
            "awake_sleep_seconds": awake_sleep_seconds,
            "sleep_feedback": sleep_feedback,
            "sleep_insight": sleep_insight,
            "avg_stress_level": avg_stress_level,
            "max_stress_level": max_stress_level,
        }

        combined_data_array.append(new_entry)

    generate_html_report(combined_data_array)
    send_email_report(
        to_address, "energy_report.html", "Energy Report"
    )
