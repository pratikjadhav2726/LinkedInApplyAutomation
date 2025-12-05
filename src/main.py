import os
import warnings
from pathlib import Path

import yaml
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from validate_email import validate_email
from webdriver_manager.chrome import ChromeDriverManager

# Suppress Pydantic serialization warnings from LiteLLM
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

from src.bot.linkedin_easy_apply import LinkedinEasyApply


def find_config_file():
    """
    Find config.yaml file in multiple possible locations.
    Priority: current directory > project root > examples directory
    """
    # Get project root (assuming src/ is inside project root)
    project_root = Path(__file__).parent.parent

    # Possible config locations
    config_paths = [
        Path("config.yaml"),  # Current working directory
        project_root / "config.yaml",  # Project root
        project_root / "examples" / "config.yaml.example",  # Example file
    ]

    for config_path in config_paths:
        if config_path.exists():
            return config_path

    # If no config found, provide helpful error message
    example_path = project_root / "examples" / "config.yaml.example"
    raise FileNotFoundError(
        f"config.yaml not found. Please create config.yaml in the project root.\n"
        f"You can copy the example: cp {example_path} {project_root / 'config.yaml'}"
    )


def init_browser():
    browser_options = Options()
    options = [
        "--disable-blink-features",
        "--no-sandbox",
        "--start-maximized",
        "--disable-extensions",
        "--ignore-certificate-errors",
        "--disable-blink-features=AutomationControlled",
        "--remote-debugging-port=9222",
    ]

    # Restore session if possible (avoids login everytime)
    project_root = Path(__file__).parent.parent
    user_data_dir = project_root / "chrome_bot"
    user_data_dir.mkdir(exist_ok=True)
    browser_options.add_argument(f"user-data-dir={user_data_dir.absolute()}")

    for option in options:
        browser_options.add_argument(option)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=browser_options)
    driver.implicitly_wait(1)  # Wait time in seconds to allow loading of elements
    driver.set_window_position(0, 0)
    driver.maximize_window()
    return driver


def validate_yaml():
    config_path = find_config_file()
    with open(config_path, "r", encoding="utf-8") as stream:
        try:
            parameters = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise exc

    mandatory_params = [
        "email",
        "password",
        "disableAntiLock",
        "remote",
        "lessthanTenApplicants",
        "newestPostingsFirst",
        "experienceLevel",
        "jobTypes",
        "date",
        "positions",
        "locations",
        "residentStatus",
        "distance",
        "outputFileDirectory",
        "checkboxes",
        "universityGpa",
        "languages",
        "experience",
        "personalInfo",
        "eeo",
        "uploads",
    ]

    for mandatory_param in mandatory_params:
        if mandatory_param not in parameters:
            raise Exception(
                mandatory_param + " is not defined in the config.yaml file!"
            )

    assert validate_email(parameters["email"])
    assert len(str(parameters["password"])) > 0
    assert isinstance(parameters["disableAntiLock"], bool)
    assert isinstance(parameters["remote"], bool)
    assert isinstance(parameters["lessthanTenApplicants"], bool)
    assert isinstance(parameters["newestPostingsFirst"], bool)
    assert isinstance(parameters["residentStatus"], bool)
    assert len(parameters["experienceLevel"]) > 0
    experience_level = parameters.get("experienceLevel", [])
    at_least_one_experience = False

    for key in experience_level.keys():
        if experience_level[key]:
            at_least_one_experience = True
    assert at_least_one_experience

    assert len(parameters["jobTypes"]) > 0
    job_types = parameters.get("jobTypes", [])
    at_least_one_job_type = False
    for key in job_types.keys():
        if job_types[key]:
            at_least_one_job_type = True

    assert at_least_one_job_type
    assert len(parameters["date"]) > 0
    date = parameters.get("date", [])
    at_least_one_date = False

    for key in date.keys():
        if date[key]:
            at_least_one_date = True
    assert at_least_one_date

    approved_distances = {0, 5, 10, 25, 50, 100}
    assert parameters["distance"] in approved_distances
    assert len(parameters["positions"]) > 0
    assert len(parameters["locations"]) > 0
    assert len(parameters["uploads"]) >= 1 and "resume" in parameters["uploads"]
    assert len(parameters["checkboxes"]) > 0

    checkboxes = parameters.get("checkboxes", [])
    assert isinstance(checkboxes["driversLicence"], bool)
    assert isinstance(checkboxes["requireVisa"], bool)
    assert isinstance(checkboxes["legallyAuthorized"], bool)
    assert isinstance(checkboxes["certifiedProfessional"], bool)
    assert isinstance(checkboxes["urgentFill"], bool)
    assert isinstance(checkboxes["commute"], bool)
    assert isinstance(checkboxes["backgroundCheck"], bool)
    assert isinstance(checkboxes["securityClearance"], bool)
    assert "degreeCompleted" in checkboxes
    assert isinstance(parameters["universityGpa"], (int, float))

    languages = parameters.get("languages", [])
    language_types = {"none", "conversational", "professional", "native or bilingual"}
    for language in languages:
        assert languages[language].lower() in language_types

    experience = parameters.get("experience", [])
    for tech in experience:
        assert isinstance(experience[tech], int)
    assert "default" in experience

    assert len(parameters["personalInfo"])
    personal_info = parameters.get("personalInfo", [])
    for info in personal_info:
        assert personal_info[info] != ""

    assert len(parameters["eeo"])
    eeo = parameters.get("eeo", [])
    for survey_question in eeo:
        assert eeo[survey_question] != ""

    if parameters.get("openaiApiKey") == "sk-proj-your-openai-api-key":
        # Overwrite the default value with None to indicate internally that the OpenAI API key is not configured
        # print("OpenAI API key not configured. Defaulting to empty responses for text fields.")
        parameters["openaiApiKey"] = None

    return parameters


def main():
    """Main entry point for the LinkedIn Easy Apply Bot."""
    try:
        parameters = validate_yaml()
        browser = init_browser()

        bot = LinkedinEasyApply(parameters, browser)
        bot.login()
        bot.security_check()
        bot.start_applying()
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
