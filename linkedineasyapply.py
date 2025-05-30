import time, random, csv, pyautogui, traceback, os, re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from datetime import date, datetime
from itertools import product
from pypdf import PdfReader
import requests
# from docx import Document
from docx2pdf import convert
import json
import ollama
from litellm import completion

class AIResponseGenerator:
    def __init__(self, api_key, personal_info, experience, languages, resume_path, checkboxes, ollama_model, text_resume_path=None, debug=False):
        self.personal_info = personal_info
        self.experience = experience
        self.languages = languages
        self.pdf_resume_path = resume_path
        self.text_resume_path = text_resume_path
        self.checkboxes = checkboxes
        self._resume_content = None
        self._client = True
        self.ollama_model = ollama_model
        self.debug = debug
    @property
    def resume_content(self):
        if self._resume_content is None:
            # First try to read from text resume if available
            if self.text_resume_path:
                try:
                    with open(self.text_resume_path, 'r', encoding='utf-8') as f:
                        self._resume_content = f.read()
                        print("Successfully loaded text resume")
                        return self._resume_content
                except Exception as e:
                    print(f"Could not read text resume: {str(e)}")

            # Fall back to PDF resume if text resume fails or isn't available
            try:
                content = []
                reader = PdfReader(self.pdf_resume_path)
                for page in reader.pages:
                    content.append(page.extract_text())
                self._resume_content = "\n".join(content)
                print("Successfully loaded PDF resume")
            except Exception as e:
                print(f"Could not extract text from resume PDF: {str(e)}")
                self._resume_content = ""
        return self._resume_content
    def _build_context(self):
        return f"""
        Personal Information:
        - Name: {self.personal_info['First Name']} {self.personal_info['Last Name']}
        - Current Role: {self.experience.get('currentRole', 'AI Specialist')}
        - Current Location: {self.personal_info['City']}, {self.personal_info['State']}, United States
        - Authorized to work in the US: {'Yes' if self.checkboxes.get('legallyAuthorized') else 'No'}
        - Skills: {', '.join(self.experience.keys())}
        - Languages: {', '.join(f'{lang}: {level}' for lang, level in self.languages.items())}

        Resume Content:
        {self.resume_content}
        """
    def get_tailored_skills_replacements(self,job_description):
        # context = self._build_context()
        system_prompt = f"""You are an expert resume and job description analyst.

            Your task is to read the job description below and extract the **top 10 technical skills or tools** that are essential for the role.

            Guidelines:
            - Return skills exactly as written in the job description (no synonyms, no rewording).
            - Include programming languages, libraries, frameworks, cloud platforms, APIs, machine learning techniques, tools, and standards mentioned.
            - Focus on the most important and unique technical terms. Do not include soft skills or generic phrases.
            - Return the output as a **comma-separated list** of skill keywords, in order of relevance and frequency.

            Job Description:
            {job_description}
            """
        response = requests.post("http://localhost:11434/api/generate", json={
                    "model": self.ollama_model,
                    "prompt": system_prompt,
                    "stream": False
                })
        job_skills = response['message']['content'].strip()
        
        MAX_SKILL_REPLACEMENTS = 5
        system_prompt ="""
                        You are an AI assistant specialized in optimizing resumes for Applicant Tracking Systems (ATS).

                        Your task:
                        Given a list of resume skills and a list of job description skills, identify **exactly 5 skills** from the resume that can be replaced with **more relevant skills from the job description** to improve alignment and ATS score.

                        Strict Rules:
                        1. Each "old" skill must exist in the resume.
                        2. Each "new" skill must exist in the job description and **must NOT already exist in the resume**.
                        3. DO NOT suggest replacements that are already present in the resume in any form (no duplicates, no synonyms).
                        4. Only suggest replacements where the old and new skills are **semantically similar** — i.e., they belong to the same category or purpose (e.g., frameworks, cloud platforms, dev tools, AI methods, APIs).
                        5. Return **exactly 5 valid replacements**. If there are not enough matches, return fewer — do not force unrelated replacements.
                        6. Your output must be a **JSON array**, in this exact format:

                        [
                        {"old": "old_resume_skill", "new": "new_job_description_skill"},
                        {"old": "old_resume_skill", "new": "new_job_description_skill"},
                        ...
                        ]

                        Do not include any explanation, heading, or commentary. Only output the JSON array.
                                                """
        try:
            user_content=f""" Job Skills:
                    {job_skills}

                    Resume:
                    {self.resume_content}
                    """
            response = requests.post("http://localhost:11434/api/generate", json={
                    "model": self.ollama_model,
                    "prompt": system_prompt+user_content,
                    "stream": False
                })
            answer = response['message']['content'].strip()
            replacements = json.loads(re.search(r'\[.*\]', answer, re.DOTALL).group())
            print(f"AI response: {answer}") 
            return replacements[:MAX_SKILL_REPLACEMENTS]
        except Exception as e:
            print(f"Error using AI to generate resume tailoring skills: {str(e)}")
            return None
    def tailor_resume_pdf(self,replacements):
        try:
            # job_description = self.browser.find_element(
            #                     By.ID, 'job-details'
            #                 ).text 
            # replacements=self.get_tailored_skills_replacements(job_description)
            doc = Document(self.docx_resume)
            def replace_in_runs(runs, old, new):
                for run in runs:
                    if old in run.text:
                        run.text = run.text.replace(old, new)

            for paragraph in doc.paragraphs:
                for r in replacements:
                    replace_in_runs(paragraph.runs, r['old'], r['new'])
            output_docx_path= "Pratik_Shankar_Jadhav.docx"
            output_pdf_path= "Pratik_Shankar_Jadhav_.pdf"
            doc.save(output_docx_path)
            convert(output_docx_path, output_pdf_path)
            self.resume_dir = output_pdf_path
            print(f"Resume updated and converted to PDF and resume path changed: {output_pdf_path}")

        except Exception as e:
            print(f"Error using tailor resume: {str(e)}")
            return None




            
            

    def generate_response(self, question_text, response_type="text", options=None, max_tokens=100, jd=""):
        """
        Generate a response using OpenAI's API
        
        Args:
            question_text: The application question to answer
            response_type: "text", "numeric", or "choice"
            options: For "choice" type, a list of tuples containing (index, text) of possible answers
            max_tokens: Maximum length of response
            
        Returns:
            - For text: Generated text response or None
            - For numeric: Integer value or None
            - For choice: Integer index of selected option or None
        """
        # if not self._client:
        #     return None
            
        try:
            context = self._build_context()
            # print(context)
            system_prompt = {
                "text": "You are a helpful assistant answering job application questions professionally and short. Use the candidate's background information and resume to personalize responses. Pretend you are the candidate.Only give the answer if you are sure from background. Otherwise return NA.",
                "numeric": "You are a helpful assistant providing numeric answers to job application questions. Based on the candidate's experience, provide a single number as your response. No explanation needed.",
                "choice": "You are a helpful assistant selecting the most appropriate answer choice for job application questions. Based on the candidate's background, select the best option by returning only its index number. No explanation needed."
            }[response_type]

            user_content = f"Using this candidate's background and resume:\n{context} JD{jd}\n\nPlease answer this job application question: {question_text}"
            if response_type == "choice" and options:
                options_text = "\n".join([f"{idx}: {text}" for idx, text in options])
                user_content += f"\n\nSelect the most appropriate answer by providing its index number from these options:\n{options_text}"

            response = completion(
                model="groq/llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
                # max_tokens=max_tokens,
                # temperature=0.7
            )
            
            answer = response.choices[0]['message']['content'].strip()
            print(f"AI response: {answer}")  # TODO: Put logging behind a debug flag
            
            if response_type == "numeric":
                # Extract first number from response
                numbers = re.findall(r'\d+', answer)
                if numbers:
                    return int(numbers[0])
                return 0
            elif response_type == "choice":
                # Extract the index number from the response
                numbers = re.findall(r'\d+', answer)
                if numbers and options:
                    index = int(numbers[0])
                    # Ensure index is within valid range
                    if 0 <= index < len(options):
                        return index
                return None  # Return None if the index is not within the valid range
                
            return answer
            
        except Exception as e:
            print(f"Error using AI to generate response: {str(e)}")
            return None

    def evaluate_job_fit(self, job_title, job_description):
        """
        Given a job description and my current resume, evaluate whether this job is worth applying for based on a 50–60% alignment threshold.
        
        Args:
            job_title: The title of the job posting
            job_description: The full job description text
            
        Returns:
            bool: True if should apply, False if should skip
        """
        # if not self._client:
        #     return True  # Proceed with application if AI not available
        try:
            system_prompt=""" Given Job description summarize it in 120 words, focus on qualifications and years of experience and technical skills. Expertise needed"""
            response = completion(
                model="groq/llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Job: {job_title}\n{job_description}"}
                ]
                # max_tokens=250 if self.debug else 1,  # Allow more tokens when debug is enabled
                # temperature=0.2  # Lower temperature for more consistent decisions
            )
            
            job_description = response.choices[0]['message']['content'].strip()
            # print(f"Job Summary: {job_description}")
            time.sleep(5)
        except Exception as e:
            print(f"Error evaluating job fit: {str(e)}")
            return True  # Proceed with application if evaluation fails
        try:
            context=self._build_context()
            # print(context)
            percent="80"
            system_prompt = """
                Based on the candidate’s resume and the job description, respond with APPLY if the resume matches at least 85 percent of the required qualifications and experience. Otherwise, respond with SKIP.
                Only return APPLY or SKIP.
            """
            #Consider the candidate's education level when evaluating whether they meet the core requirements. Having higher education than required should allow for greater flexibility in the required experience.
            
            if self.debug:
                pass
                # system_prompt += """
                # You are in debug mode. Return a detailed explanation of your reasoning for each requirement.

                # Return APPLY or SKIP followed by a brief explanation.

                # Format response as: APPLY/SKIP: [brief reason]"""
            else:
                system_prompt += """Return only APPLY or SKIP."""

            response = completion(
                model="groq/gemma2-9b-it",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Job: {job_title}\n{job_description}\n\nCandidate:\n{context}"}
                ],
                temperature=0.9,
                max_completion_tokens=250 if self.debug else 1,  # Allow more tokens when debug is enabled
                # max_tokens=250 if self.debug else 1,  # Allow more tokens when debug is enabled
                # temperature=0.2  # Lower temperature for more consistent decisions
            )
            
            answer = response.choices[0]['message']['content'].strip()
            print(f"AI evaluation: {answer}")
            time.sleep(5)
            return answer.upper().startswith('A')  # True for APPLY, False for SKIP
            
        except Exception as e:
            print(f"Error evaluating job fit: {str(e)}")
            return True  # Proceed with application if evaluation fails

class LinkedinEasyApply:
    def __init__(self, parameters, driver):
        self.browser = driver
        self.email = parameters['email']
        self.password = parameters['password']
        self.openai_api_key = parameters.get('openaiApiKey', '')  # Get API key with empty default
        self.ollama_model = parameters.get('ollamaModel', '')
        self.disable_lock = parameters['disableAntiLock']
        self.company_blacklist = parameters.get('companyBlacklist', []) or []
        self.title_blacklist = parameters.get('titleBlacklist', []) or []
        self.poster_blacklist = parameters.get('posterBlacklist', []) or []
        self.positions = parameters.get('positions', [])
        self.locations = parameters.get('locations', [])
        self.residency = parameters.get('residentStatus', [])
        self.base_search_url = self.get_base_search_url(parameters)
        self.seen_jobs = []
        self.file_name = "output"
        self.unprepared_questions_file_name = "unprepared_questions"
        self.output_file_directory = parameters['outputFileDirectory']
        self.resume_dir = parameters['uploads']['resume']
        self.text_resume = parameters.get('textResume', '')
        self.docx_resume = parameters.get('docxResume','')
        if 'coverLetter' in parameters['uploads']:
            self.cover_letter_dir = parameters['uploads']['coverLetter']
        else:
            self.cover_letter_dir = ''
        self.checkboxes = parameters.get('checkboxes', [])
        self.university_gpa = parameters['universityGpa']
        self.salary_minimum = parameters['salaryMinimum']
        self.notice_period = int(parameters['noticePeriod'])
        self.languages = parameters.get('languages', [])
        self.experience = parameters.get('experience', [])
        self.personal_info = parameters.get('personalInfo', [])
        self.eeo = parameters.get('eeo', [])
        self.experience_default = int(self.experience['default'])
        self.debug = parameters.get('debug', False)
        self.evaluate_job_fit = parameters.get('evaluateJobFit', True)
        self.tailor_resume = parameters.get('tailorResume', True)
        self.ai_response_generator = AIResponseGenerator(
            api_key=self.openai_api_key,
            personal_info=self.personal_info,
            experience=self.experience,
            languages=self.languages,
            resume_path=self.resume_dir,
            checkboxes=self.checkboxes,
            text_resume_path=self.text_resume,
            debug=self.debug,
            ollama_model=self.ollama_model
        )

    def login(self):
        try:
            # Check if the "chrome_bot" directory exists
            print("Attempting to restore previous session...")
            if os.path.exists("chrome_bot"):
                self.browser.get("https://www.linkedin.com/feed/")
                time.sleep(random.uniform(5, 10))

                # Check if the current URL is the feed page
                if self.browser.current_url != "https://www.linkedin.com/feed/":
                    print("Feed page not loaded, proceeding to login.")
                    self.load_login_page_and_login()
            else:
                print("No session found, proceeding to login.")
                self.load_login_page_and_login()

        except TimeoutException:
            print("Timeout occurred, checking for security challenges...")
            self.security_check()
            # raise Exception("Could not login!")

    def security_check(self):
        current_url = self.browser.current_url
        page_source = self.browser.page_source

        if '/checkpoint/challenge/' in current_url or 'security check' in page_source or 'quick verification' in page_source:
            input("Please complete the security check and press enter on this console when it is done.")
            time.sleep(random.uniform(5.5, 10.5))

    def load_login_page_and_login(self):
        self.browser.get("https://www.linkedin.com/login")

        # Wait for the username field to be present
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )

        self.browser.find_element(By.ID, "username").send_keys(self.email)
        self.browser.find_element(By.ID, "password").send_keys(self.password)
        self.browser.find_element(By.CSS_SELECTOR, ".btn__primary--large").click()

        # Wait for the feed page to load after login
        WebDriverWait(self.browser, 10).until(
            EC.url_contains("https://www.linkedin.com/feed/")
        )

        time.sleep(random.uniform(5, 10))

    def start_applying(self):
        searches = list(product(self.positions, self.locations))
        random.shuffle(searches)

        page_sleep = 0
        minimum_time = 60 * 2  # minimum time bot should run before taking a break
        minimum_page_time = time.time() + minimum_time

        for (position, location) in searches:
            location_url = "&location=" + location
            job_page_number = -1

            print("Starting the search for " + position + " in " + location + ".")

            try:
                while True:
                    page_sleep += 1
                    job_page_number += 1
                    print("Going to job page " + str(job_page_number))
                    self.next_job_page(position, location_url, job_page_number)
                    time.sleep(random.uniform(1.5, 3.5))
                    print("Starting the application process for this page...")
                    self.apply_jobs(location)
                    print("Job applications on this page have been successfully completed.")

                    time_left = minimum_page_time - time.time()
                    if time_left > 0:
                        print("Sleeping for " + str(time_left) + " seconds.")
                        time.sleep(time_left)
                        minimum_page_time = time.time() + minimum_time
                    if page_sleep % 5 == 0:
                        sleep_time = random.randint(180, 300)  # Changed from 500, 900 {seconds}
                        print("Sleeping for " + str(sleep_time / 60) + " minutes.")
                        time.sleep(sleep_time)
                        page_sleep += 1
            except:
                traceback.print_exc()
                pass

            time_left = minimum_page_time - time.time()
            if time_left > 0:
                print("Sleeping for " + str(time_left) + " seconds.")
                time.sleep(time_left)
                minimum_page_time = time.time() + minimum_time
            if page_sleep % 5 == 0:
                sleep_time = random.randint(500, 900)
                print("Sleeping for " + str(sleep_time / 60) + " minutes.")
                time.sleep(sleep_time)
                page_sleep += 1

    def apply_jobs(self, location):
        no_jobs_text = ""
        try:
            no_jobs_element = self.browser.find_element(By.CLASS_NAME,
                                                        'jobs-search-two-pane__no-results-banner--expand')
            no_jobs_text = no_jobs_element.text
        except:
            pass
        if 'No matching jobs found' in no_jobs_text:
            raise Exception("No more jobs on this page.")

        if 'unfortunately, things are' in self.browser.page_source.lower():
            raise Exception("No more jobs on this page.")
        try:
            with open("output.csv", 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                self.seen_jobs = [row[2] for row in reader if len(row) > 2]  # Assuming the link is in the 3rd column
        except FileNotFoundError:
            print("output.csv not found. Starting with an empty seen_jobs list.")
        except Exception as e:
            print(f"Error reading output.csv: {e}")
        job_results_header = ""
        maybe_jobs_crap = ""
        job_results_header = self.browser.find_element(By.CLASS_NAME, "jobs-search-results-list__text")
        maybe_jobs_crap = job_results_header.text

        if 'Jobs you may be interested in' in maybe_jobs_crap:
            raise Exception("Nothing to do here, moving forward...")

        try:
            # TODO: Can we simply use class name scaffold-layout__list for the scroll (necessary to show all li in the dom?)? Does it need to be the ul within the scaffold list?
            #      Then we can simply get all the li scaffold-layout__list-item elements within it for the jobs

            # Define the XPaths for potentially different regions
            xpath_region1 = "/html/body/div[6]/div[3]/div[4]/div/div/main/div/div[2]/div[1]/div"
            xpath_region2 = "/html/body/div[5]/div[3]/div[4]/div/div/main/div/div[2]/div[1]/div"
            job_list = []

            # Attempt to locate the element using XPaths
            try:
                job_results = self.browser.find_element(By.XPATH, xpath_region1)
                ul_xpath = "/html/body/div[6]/div[3]/div[4]/div/div/main/div/div[2]/div[1]/div/ul"
                ul_element = self.browser.find_element(By.XPATH, ul_xpath)
                ul_element_class = ul_element.get_attribute("class").split()[0]
                print(f"Found using xpath_region1 and detected ul_element as {ul_element_class} based on {ul_xpath}")

            except NoSuchElementException:
                job_results = self.browser.find_element(By.XPATH, xpath_region2)
                ul_xpath = "/html/body/div[5]/div[3]/div[4]/div/div/main/div/div[2]/div[1]/div/ul"
                ul_element = self.browser.find_element(By.XPATH, ul_xpath)
                ul_element_class = ul_element.get_attribute("class").split()[0]
                print(f"Found using xpath_region2 and detected ul_element as {ul_element_class} based on {ul_xpath}")

            # Extract the random class name dynamically
            random_class = job_results.get_attribute("class").split()[0]
            print(f"Random class detected: {random_class}")

            # Use the detected class name to find the element
            job_results_by_class = self.browser.find_element(By.CSS_SELECTOR, f".{random_class}")
            print(f"job_results: {job_results_by_class}")
            print("Successfully located the element using the random class name.")

            # Scroll logic (currently disabled for testing)
            self.scroll_slow(job_results_by_class)  # Scroll down
            self.scroll_slow(job_results_by_class, step=300, reverse=True)  # Scroll up

            # Find job list elements
            job_list = self.browser.find_elements(By.CLASS_NAME, ul_element_class)[0].find_elements(By.CLASS_NAME, 'scaffold-layout__list-item')
            print(f"Found {len(job_list)} jobs on this page")

            if len(job_list) == 0:
                raise Exception("No more jobs on this page.")  # TODO: Seemed to encounter an error where we ran out of jobs and didn't go to next page, perhaps because I didn't have scrolling on?

        except NoSuchElementException:
            print("No job results found using the specified XPaths or class.")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        for job_tile in job_list:
            job_title, company, poster, job_location, apply_method, link = "", "", "", "", "", ""

            try:
                ## patch to incorporate new 'verification' crap by LinkedIn
                # job_title = job_tile.find_element(By.CLASS_NAME, 'job-card-list__title').text # original code
                job_title_element = job_tile.find_element(By.CLASS_NAME, 'job-card-list__title--link')
                job_title = job_title_element.find_element(By.TAG_NAME, 'strong').text

                link = job_tile.find_element(By.CLASS_NAME, 'job-card-list__title--link').get_attribute('href').split('?')[0]
            except:
                pass
            try:
                # company = job_tile.find_element(By.CLASS_NAME, 'job-card-container__primary-description').text # original code
                company = job_tile.find_element(By.CLASS_NAME, 'artdeco-entity-lockup__subtitle').text
            except:
                pass
            try:
                # get the name of the person who posted for the position, if any is listed
                hiring_line = job_tile.find_element(By.XPATH, '//span[contains(.,\' is hiring for this\')]')
                hiring_line_text = hiring_line.text
                name_terminating_index = hiring_line_text.find(' is hiring for this')
                if name_terminating_index != -1:
                    poster = hiring_line_text[:name_terminating_index]
            except:
                pass
            try:
                job_location = job_tile.find_element(By.CLASS_NAME, 'job-card-container__metadata-item').text
            except:
                pass
            try:
                apply_method = job_tile.find_element(By.CLASS_NAME, 'job-card-container__apply-method').text
            except:
                pass

            contains_blacklisted_keywords = False
            job_title_parsed = job_title.lower().split(' ')
            
            for word in self.title_blacklist:
                if word.lower() in job_title_parsed:
                    contains_blacklisted_keywords = True
                    break

            if company.lower() not in [word.lower() for word in self.company_blacklist] and \
                    poster.lower() not in [word.lower() for word in self.poster_blacklist] and \
                    contains_blacklisted_keywords is False and link not in self.seen_jobs:
                try:
                    # Click the job to load description
                    max_retries = 3
                    retries = 0
                    while retries < max_retries:
                        try:
                            # TODO: This is throwing an exception when running out of jobs on a page
                            job_el = job_tile.find_element(By.CLASS_NAME, 'job-card-list__title--link')
                            job_el.click()
                            break
                        except StaleElementReferenceException:
                            retries += 1
                            continue

                    time.sleep(random.uniform(3, 5))

                    # TODO: Check if the job is already applied or the application has been reached
                    # "You’ve reached the Easy Apply application limit for today. Save this job and come back tomorrow to continue applying."
                    # Do this before evaluating job fit to save on API calls
                    if self.tailor_resume:
                        try:
                            job_description = self.browser.find_element(
                                By.ID, 'job-details'
                            ).text 
                            replacements = self.ai_response_generator.get_tailored_skills_replacements(job_description)
                            self.ai_response_generator.tailor_resume_pdf(replacements)
                        except:
                            print("Could not load job description and tailorResume")
                    if self.evaluate_job_fit:
                        try:
                            # Get job description
                            job_description = self.browser.find_element(
                                By.ID, 'job-details'
                            ).text  

                            # Evaluate if we should apply
                            if not self.ai_response_generator.evaluate_job_fit(job_title, job_description):
                                print("Skipping application: Job requirements not aligned with candidate profile per AI evaluation.")
                                continue
                        except:
                            print("Could not load job description")

                    try:
                        done_applying = self.apply_to_job()
                        if done_applying:
                            print(f"Application sent to {company} for the position of {job_title}.")
                        else:
                            print(f"An application for a job at {company} has been submitted earlier.")
                    except:
                        temp = self.file_name
                        self.file_name = "failed"
                        print("Failed to apply to job. Please submit a bug report with this link: " + link)
                        try:
                            self.write_to_file(company, job_title, link, job_location, location)
                        except:
                            pass
                        self.file_name = temp
                        print(f'updated {temp}.')

                    try:
                        self.write_to_file(company, job_title, link, job_location, location)
                    except Exception:
                        print(
                            f"Unable to save the job information in the file. The job title {job_title} or company {company} cannot contain special characters,")
                        traceback.print_exc()
                except:
                    traceback.print_exc()
                    print(f"Could not apply to the job in {company}")
                    pass
            else:
                print(f"Job for {company} by {poster} contains a blacklisted word {word}.")

            self.seen_jobs += link
    def apply_to_ashby(self, jd=""):
        """
        Fills and submits an Ashby application form.
        Only fills fields that are empty (not already autofilled by resume).
        :param jd: (optional) job description to pass into LLM context
        """
        import time
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        print("Starting Ashybq Application.")
        personal_info = self.personal_info
        wait = WebDriverWait(self.browser, 20)

        try:
            # 1. Go to "Application" tab (if not already there)
            try:
                app_tab = self.browser.find_element(By.XPATH, "//span[contains(@class,'ashby-job-posting-right-pane-application-tab') and contains(text(),'Application')]")
                app_tab.click()
                time.sleep(1)
            except Exception:
                pass  # Already on tab or not present

            # 2. Upload resume (if the upload button exists and file not already attached)
            try:
                upload_btn = self.browser.find_element(By.XPATH, "//button[.//span[contains(text(),'Upload File')]]")
                upload_btn.click()
                # Now find the hidden input[type=file] in the same parent container
                file_input = self.browser.find_element(By.XPATH, "//input[@type='file' and @id='_systemfield_resume']")
                file_input.send_keys(self.resume_dir)
                print("Resume uploaded for autofill.")
                # Wait for parsing/autofill to finish (adjust timing as needed)
                time.sleep(5)
            except Exception as e:
                print(f"Could not upload resume (may already be uploaded): {e}")

            # 3. Fill any empty text input fields
            text_inputs = self.browser.find_elements(By.XPATH, "//input[@type='text' or @type='email']")
            for inp in text_inputs:
                try:
                    # Skip if already filled by autofill
                    value = inp.get_attribute("value")
                    if value and value.strip() != "":
                        continue

                    label_text = ""
                    try:
                        label_elem = self.browser.find_element(By.XPATH, f"//label[@for='{inp.get_attribute('id')}']")
                        label_text = label_elem.text.strip()
                    except Exception:
                        pass

                    # Smart logic for known fields
                    if "name" in label_text.lower():
                        inp.clear()
                        inp.send_keys(personal_info.get("First Name", "") + " " + personal_info.get("Last Name", ""))
                    elif "email" in label_text.lower():
                        inp.clear()
                        inp.send_keys(personal_info.get("Email", ""))
                    elif "linkedin" in label_text.lower():
                        inp.clear()
                        inp.send_keys(personal_info.get("Linkedin", ""))
                    elif "github" in label_text.lower():
                        inp.clear()
                        inp.send_keys(personal_info.get("GitHub", ""))
                    elif "website" in label_text.lower() or "portfolio" in label_text.lower():
                        inp.clear()
                        inp.send_keys(personal_info.get("Website", ""))
                    elif "city" in label_text.lower():
                        inp.clear()
                        inp.send_keys(personal_info.get("City", ""))
                    elif "state" in label_text.lower():
                        inp.clear()
                        inp.send_keys(personal_info.get("State", ""))
                    elif "zip" in label_text.lower() or "postal" in label_text.lower():
                        inp.clear()
                        inp.send_keys(personal_info.get("Zip", ""))
                    elif "location" in label_text.lower():
                        inp.clear()
                        inp.send_keys(personal_info.get("Location", ""))
                    elif "visa sponsership" in label_text.lower() or "h1b" in label_text.lower():
                        inp.clear()
                        inp.send_keys("yes")
                    elif "work schedule" in label_text.lower():
                        inp.clear()
                        inp.send_keys("Yes")
                    else:
                        # Fallback to AI for custom questions
                        ai_answer = self.ai_response_generator.generate_response(label_text, response_type="text", jd=jd)
                        inp.clear()
                        inp.send_keys(ai_answer)
                except Exception as e:
                    print(f"Could not fill Ashby text input: {e}")

            # 4. Fill any empty textareas
            textareas = self.browser.find_elements(By.XPATH, "//textarea")
            for ta in textareas:
                try:
                    value = ta.get_attribute("value")
                    if value and value.strip() != "":
                        continue
                    label_text = ""
                    try:
                        label_elem = self.browser.find_element(By.XPATH, f"//label[@for='{ta.get_attribute('id')}']")
                        label_text = label_elem.text.strip()
                    except Exception:
                        pass
                    ai_answer = self.ai_response_generator.generate_response(label_text, response_type="text", jd=jd)
                    ta.clear()
                    ta.send_keys(ai_answer)
                except Exception as e:
                    print(f"Could not fill Ashby textarea: {e}")

            # 5. Optionally handle selects (dropdowns) if needed

            # 6. Submit the form
            submit_btn = self.browser.find_element(By.XPATH, "//button[contains(@class,'ashby-application-form-submit-button')]")
            submit_btn.click()
            print("Ashby application submitted successfully.")
            time.sleep(2)
            return True

        except Exception as e:
            print(f"Error during Ashby application: {e}")
            return False

    def apply_to_greenhouse(self, jd=""):
        """
        Fills and submits a Greenhouse application form using AI-generated answers.
        :param personal_info: dict with keys 'first_name', 'last_name', 'email', 'phone', 'resume_path', optional: 'cover_letter_path'
        :param jd: (optional) job description to pass into LLM context
        """
        print("Starting Greenhouse Application.")
        personal_info = self.personal_info
        wait = WebDriverWait(self.browser, 15)
        try:
            # Wait for application form
            wait.until(EC.presence_of_element_located((By.ID, "application-form")))

            # Fill core fields
            self.browser.find_element(By.ID, "first_name").send_keys(personal_info['First Name'])
            self.browser.find_element(By.ID, "last_name").send_keys(personal_info['Last Name'])
            self.browser.find_element(By.ID, "email").send_keys(personal_info['Email'])
            try:
                phone_field = self.browser.find_element(By.ID, "phone")
                phone_value = personal_info.get('Mobile Phone Number', '')
                if phone_value:
                    phone_field.send_keys(phone_value)
            except Exception:
                pass

            # Upload Resume
            resume_input = self.browser.find_element(By.ID, "resume")
            resume_input.send_keys(self.resume_dir)
            wait = WebDriverWait(self.browser, 15)

            # Upload Cover Letter (optional)
            try:
                cover_letter_path = self.cover_letter_dir
                if cover_letter_path:
                    cover_letter_input = self.browser.find_element(By.ID, "cover_letter")
                    cover_letter_input.send_keys(cover_letter_path)
                    wait = WebDriverWait(self.browser, 15)
            except Exception:
                pass

            # Answer all question_* inputs dynamically using AI
            question_inputs = self.browser.find_elements(By.XPATH, "//input[starts-with(@id, 'question_')]")
            for inp in question_inputs:
                try:
                    qid = inp.get_attribute('id')
                    # Find associated label
                    label_text = ""
                    try:
                        label_elem = self.browser.find_element(By.XPATH, f"//label[@for='{qid}']")
                        label_text = label_elem.text.strip()
                    except Exception:
                        pass
                    if "linkedin" in label_text.lower():
                        inp.clear()
                        inp.send_keys(personal_info.get("Linkedin", ""))
                    elif "github" in label_text.lower() or "website" in label_text.lower():
                        inp.clear()
                        inp.send_keys(personal_info.get("Website", ""))
                    elif "city" in label_text.lower():
                        inp.clear()
                        inp.send_keys(personal_info.get("City", ""))
                    elif "state" in label_text.lower():
                        inp.clear()
                        inp.send_keys(personal_info.get("State", ""))
                    elif "zip" in label_text.lower() or "postal" in label_text.lower():
                        inp.clear()
                        inp.send_keys(personal_info.get("Zip", ""))
                    elif "visa sponsership" in label_text.lower() or "h1b" in label_text.lower():
                        inp.clear()
                        inp.send_keys("yes")
                    elif "work schedule" in label_text.lower():
                        inp.clear()
                        inp.send_keys("Yes")
                    else:
                    # For checkboxes and radio buttons, you may need additional logic here.
                        input_type = inp.get_attribute('type')
                        if input_type == "checkbox":
                            # Generate yes/no answer
                            ai_answer = self.ai_response_generator.generate_response(label_text, response_type="text", jd="")
                            if ai_answer.strip().lower().startswith("y"):
                                if not inp.is_selected():
                                    inp.click()
                        elif input_type == "radio":
                            ai_answer = self.ai_response_generator.generate_response(label_text, response_type="numeric", jd="")
                            # TODO: Implement if needed
                        else:
                            # Default: treat as text
                            ai_answer = self.ai_response_generator.generate_response(label_text, response_type="text", jd="")
                            inp.clear()
                            inp.send_keys(ai_answer)
                except Exception as e:
                    print(f"Could not fill input {inp.get_attribute('id')}: {e}")

            # Dynamically fill all question_* textareas with AI
            question_textareas = self.browser.find_elements(By.XPATH, "//textarea[starts-with(@id, 'question_')]")
            for ta in question_textareas:
                try:
                    qid = ta.get_attribute('id')
                    label_text = ""
                    try:
                        label_elem = self.browser.find_element(By.XPATH, f"//label[@for='{qid}']")
                        label_text = label_elem.text.strip()
                    except Exception:
                        pass
                    ai_answer = self.ai_response_generator.generate_response(label_text, response_type="text", jd="")
                    ta.clear()
                    ta.send_keys(ai_answer)
                except Exception as e:
                    print(f"Could not fill textarea {ta.get_attribute('id')}: {e}")

            # Wait for uploads to finish
            time.sleep(1)

            # Submit the form
            submit_btn = self.browser.find_element(By.XPATH, "//button[contains(text(), 'Submit application')]")
            submit_btn.click()
            print("Greenhouse application submitted successfully.")
            time.sleep(2)
            return True

        except Exception as e:
            print(f"Error during Greenhouse application: {e}")
            return False
    def apply_to_job(self):
        easy_apply_button = None

        try:
            easy_apply_button = self.browser.find_element(By.CLASS_NAME, 'jobs-apply-button')
        except:
            return False

        try:
            job_description_area = self.browser.find_element(By.ID, "job-details")
            print (f"{job_description_area}")
            self.scroll_slow(job_description_area, end=1600)
            self.scroll_slow(job_description_area, end=1600, step=400, reverse=True)
        except:
            pass

        print("Starting the job application...")
        easy_apply_button.click()
        time.sleep(3)  # Wait for redirect/new tab

        # --- New Logic: Check for External Application ---
        main_window = self.browser.current_window_handle
        all_windows = self.browser.window_handles

        # If a new window/tab is opened, switch to it
        for handle in all_windows:
            if handle != main_window:
                self.browser.switch_to.window(handle)
                current_url = self.browser.current_url
                print("Redirected to:", current_url)
                
                # If it's Greenhouse, handle with a new function
                if "greenhouse.io" in current_url:
                    try:
                        success = self.apply_to_greenhouse()
                        # Optionally close this tab and switch back to LinkedIn
                        self.browser.close()
                        self.browser.switch_to.window(main_window)
                        return success
                    except Exception as e:
                        print("Greenhouse application failed:", e)
                        self.browser.close()
                        self.browser.switch_to.window(main_window)
                        return False
                # --- Ashby ---
                elif "ashbyhq.com" in current_url or "ashby" in current_url:
                    try:
                        success = self.apply_to_ashby()
                        self.browser.close()
                        self.browser.switch_to.window(main_window)
                        return success
                    except Exception as e:
                        print("Ashby application failed:", e)
                        self.browser.close()
                        self.browser.switch_to.window(main_window)
                        return False

                # --- (Other external sites can be added here) ---

                # If no match, just close and switch back
                self.browser.close()
                self.browser.switch_to.window(main_window)
        button_text = ""
        submit_application_text = 'submit application'
        while submit_application_text not in button_text.lower():
            try:
                self.fill_up()
                next_button = self.browser.find_element(By.CLASS_NAME, "artdeco-button--primary")
                button_text = next_button.text.lower()
                if submit_application_text in button_text:
                    try:
                        self.unfollow()
                    except:
                        print("Failed to unfollow company.")
                time.sleep(random.uniform(1.5, 2.5))
                next_button.click()
                time.sleep(random.uniform(3.0, 5.0))

                # Newer error handling
                error_messages = [
                    'enter a valid',
                    'enter a decimal',
                    'Enter a whole number'
                    'Enter a whole number between 0 and 99',
                    'file is required',
                    'whole number',
                    'make a selection',
                    'select checkbox to proceed',
                    'saisissez un numéro',
                    '请输入whole编号',
                    '请输入decimal编号',
                    '长度超过 0.0',
                    'Numéro de téléphone',
                    'Introduce un número de whole entre',
                    'Inserisci un numero whole compreso',
                    'Preguntas adicionales',
                    'Insira um um número',
                    'Cuántos años'
                    'use the format',
                    'A file is required',
                    '请选择',
                    '请 选 择',
                    'Inserisci',
                    'wholenummer',
                    'Wpisz liczb',
                    'zakresu od',
                    'tussen'
                ]

                if any(error in self.browser.page_source.lower() for error in error_messages):
                    raise Exception("Failed answering required questions or uploading required files.")
            except:
                traceback.print_exc()
                self.browser.find_element(By.CLASS_NAME, 'artdeco-modal__dismiss').click()
                time.sleep(random.uniform(3, 5))
                self.browser.find_elements(By.CLASS_NAME, 'artdeco-modal__confirm-dialog-btn')[0].click()
                time.sleep(random.uniform(3, 5))
                raise Exception("Failed to apply to job!")

        closed_notification = False
        time.sleep(random.uniform(3, 5))
        try:
            self.browser.find_element(By.CLASS_NAME, 'artdeco-modal__dismiss').click()
            closed_notification = True
        except:
            pass
        try:
            self.browser.find_element(By.CLASS_NAME, 'artdeco-toast-item__dismiss').click()
            closed_notification = True
        except:
            pass
        try:
            self.browser.find_element(By.CSS_SELECTOR, 'button[data-control-name="save_application_btn"]').click()
            closed_notification = True
        except:
            pass

        time.sleep(random.uniform(3, 5))

        if closed_notification is False:
            raise Exception("Could not close the applied confirmation window!")

        return True

    def home_address(self, form):
        print("Trying to fill up home address fields")
        try:
            groups = form.find_elements(By.CLASS_NAME, 'jobs-easy-apply-form-section__grouping')
            if len(groups) > 0:
                for group in groups:
                    lb = group.find_element(By.TAG_NAME, 'label').text.lower()
                    input_field = group.find_element(By.TAG_NAME, 'input')
                    if 'street' in lb:
                        self.enter_text(input_field, self.personal_info['Street address'])
                    elif 'city' in lb:
                        self.enter_text(input_field, self.personal_info['City'])
                        time.sleep(3)
                        input_field.send_keys(Keys.DOWN)
                        input_field.send_keys(Keys.RETURN)
                    elif 'zip' in lb or 'zip / postal code' in lb or 'postal' in lb:
                        self.enter_text(input_field, self.personal_info['Zip'])
                    elif 'state' in lb or 'province' in lb:
                        self.enter_text(input_field, self.personal_info['State'])
                    else:
                        pass
        except:
            pass

    def get_answer(self, question):
        if self.checkboxes[question]:
            return 'yes'
        else:
            return 'no'

    def additional_questions(self, form):
        print("Trying to fill up additional questions")

        questions = form.find_elements(By.CLASS_NAME, 'fb-dash-form-element')
        for question in questions:
            try:
                # Radio check
                radio_fieldset = question.find_element(By.TAG_NAME, 'fieldset')
                question_span = radio_fieldset.find_element(By.CLASS_NAME, 'fb-dash-form-element__label').find_elements(By.TAG_NAME, 'span')[0]
                radio_text = question_span.text.lower()
                print(f"Radio question text: {radio_text}")

                radio_labels = radio_fieldset.find_elements(By.TAG_NAME, 'label')
                radio_options = [(i, text.text.lower()) for i, text in enumerate(radio_labels)]
                print(f"radio options: {[opt[1] for opt in radio_options]}")
                
                if len(radio_options) == 0:
                    raise Exception("No radio options found in question")

                answer = None

                # Try to determine answer using existing logic
                if 'driver\'s licence' in radio_text or 'driver\'s license' in radio_text:
                    answer = self.get_answer('driversLicence')
                elif any(keyword in radio_text.lower() for keyword in
                         [
                             'Aboriginal', 'native', 'genous', 'tribe', 'first nations',
                             'native american', 'native hawaiian', 'inuit', 'metis', 'maori',
                             'aborigine', 'ancestral', 'native peoples', 'original people',
                             'first people', 'gender', 'race', 'disability', 'latino', 'torres',
                             'do you identify'
                         ]):
                    negative_keywords = ['prefer', 'decline', 'don\'t', 'specified', 'none', 'no']
                    answer = next((option for option in radio_options if
                                   any(neg_keyword in option[1].lower() for neg_keyword in negative_keywords)), None)

                elif 'assessment' in radio_text:
                    answer = self.get_answer("assessment")

                elif 'clearance' in radio_text:
                    answer = self.get_answer("securityClearance")

                elif 'north korea' in radio_text:
                    answer = 'no'

                elif 'previously employ' in radio_text or 'previous employ' in radio_text:
                    answer = 'no'

                elif 'authorized' in radio_text or 'authorised' in radio_text or 'legally' in radio_text:
                    answer = self.get_answer('legallyAuthorized')

                elif any(keyword in radio_text.lower() for keyword in
                         ['certified', 'certificate', 'cpa', 'chartered accountant', 'qualification']):
                    answer = self.get_answer('certifiedProfessional')

                elif 'urgent' in radio_text:
                    answer = self.get_answer('urgentFill')

                elif 'commut' in radio_text or 'on-site' in radio_text or 'hybrid' in radio_text or 'onsite' in radio_text:
                    answer = self.get_answer('commute')

                elif 'remote' in radio_text:
                    answer = self.get_answer('remote')

                elif 'background check' in radio_text:
                    answer = self.get_answer('backgroundCheck')

                elif 'drug test' in radio_text:
                    answer = self.get_answer('drugTest')

                elif 'currently living' in radio_text or 'currently reside' in radio_text or 'right to live' in radio_text:
                    answer = self.get_answer('residency')

                elif 'level of education' in radio_text:
                    for degree in self.checkboxes['degreeCompleted']:
                        if degree.lower() in radio_text:
                            answer = "yes"
                            break

                elif 'experience' in radio_text:
                    if self.experience_default > 0:
                        answer = 'yes'
                    else:
                        for experience in self.experience:
                            if experience.lower() in radio_text:
                                answer = "yes"
                                break

                elif 'data retention' in radio_text:
                    answer = 'no'

                elif 'sponsor' in radio_text:
                    answer = self.get_answer('requireVisa')
                
                to_select = None
                if answer is not None:
                    print(f"Choosing answer: {answer}")
                    i = 0
                    for radio in radio_labels:
                        if answer in radio.text.lower():
                            to_select = radio_labels[i]
                            break
                        i += 1
                    if to_select is None:
                        print("Answer not found in radio options")

                if to_select is None:
                    print("No answer determined")
                    

                    # Since no response can be determined, we use AI to identify the best responseif available, falling back to the final option if the AI response is not available
                    ai_response = self.ai_response_generator.generate_response(
                        question_text,
                        response_type="choice",
                        options=radio_options
                    )
                    if ai_response is not None:
                        to_select = radio_labels[ai_response]
                    else:
                        to_select = radio_labels[len(radio_labels) - 1]
                    self.record_unprepared_question("radio", radio_text,ai_response)
                to_select.click()

                if radio_labels:
                    continue
            except Exception as e:
                print("An exception occurred while filling up radio field")

            # Questions check
            try:
                question_text = question.find_element(By.TAG_NAME, 'label').text.lower()
                print( question_text )  # TODO: Put logging behind debug flag

                txt_field_visible = False
                try:
                    txt_field = question.find_element(By.TAG_NAME, 'input')
                    txt_field_visible = True
                except:
                    try:
                        txt_field = question.find_element(By.TAG_NAME, 'textarea')  # TODO: Test textarea
                        txt_field_visible = True
                    except:
                        raise Exception("Could not find textarea or input tag for question")

                if 'numeric' in txt_field.get_attribute('id').lower():
                    # For decimal and integer response fields, the id contains 'numeric' while the type remains 'text' 
                    text_field_type = 'numeric'
                elif 'text' in txt_field.get_attribute('type').lower():
                    text_field_type = 'text'
                else:
                    raise Exception("Could not determine input type of input field!")

                to_enter = ''
                if 'experience' in question_text or 'how many years in' in question_text:
                    no_of_years = None
                    for experience in self.experience:
                        if experience.lower() in question_text:
                            no_of_years = int(self.experience[experience])
                            break
                    if no_of_years is None:
                        # self.record_unprepared_question(text_field_type, question_text)
                        ai_response = self.ai_response_generator.generate_response(
                                                                    question_text,
                                                                    response_type="numeric"
                                                                )
                        no_of_years = ai_response if ai_response is not None else int(self.experience_default)
                        self.record_unprepared_question(text_field_type, question_text,ai_response)
                    to_enter = no_of_years

                elif 'grade point average' in question_text:
                    to_enter = self.university_gpa

                elif 'first name' in question_text:
                    to_enter = self.personal_info['First Name']

                elif 'last name' in question_text:
                    to_enter = self.personal_info['Last Name']

                elif 'name' in question_text:
                    to_enter = self.personal_info['First Name'] + " " + self.personal_info['Last Name']

                elif 'pronouns' in question_text:
                    to_enter = self.personal_info['Pronouns']

                elif 'phone' in question_text:
                    to_enter = self.personal_info['Mobile Phone Number']

                elif 'linkedin' in question_text:
                    to_enter = self.personal_info['Linkedin']

                elif 'message to hiring' in question_text or 'cover letter' in question_text:
                    to_enter = self.personal_info['MessageToManager']

                    if not to_enter:
                        job_title = self.get_current_job_title()
                        job_description = self.get_current_job_description()
                        self.ai_response_generator.generate_response(
                        question_text,
                        response_type="text",
                        jd=job_description
                    )

                elif 'website' in question_text or 'github' in question_text or 'portfolio' in question_text:
                    to_enter = self.personal_info['Website']

                elif 'notice' in question_text or 'weeks' in question_text:
                    if text_field_type == 'numeric':
                        to_enter = int(self.notice_period)
                    else:
                        to_enter = str(self.notice_period)

                elif 'salary' in question_text or 'expectation' in question_text or 'compensation' in question_text or 'CTC' in question_text:
                    if text_field_type == 'numeric':
                        to_enter = int(self.salary_minimum)
                    else:
                        to_enter = float(self.salary_minimum)
                    

                # Since no response can be determined, we use AI to generate a response if available, falling back to 0 or empty string if the AI response is not available
                if text_field_type == 'numeric':
                    if not isinstance(to_enter, (int, float)):
                        ai_response = self.ai_response_generator.generate_response(
                            question_text,
                            response_type="numeric"
                        )
                        self.record_unprepared_question(text_field_type, question_text,ai_response)
                        to_enter = ai_response if ai_response is not None else 0
                elif to_enter == '':
                    ai_response = self.ai_response_generator.generate_response(
                        question_text,
                        response_type="text"
                    )
                    self.record_unprepared_question(text_field_type, question_text,ai_response)
                    to_enter = ai_response if ai_response is not None else " ‏‏‎ "

                self.enter_text(txt_field, to_enter)
                continue
            except:
                print("An exception occurred while filling up text field")  # TODO: Put logging behind debug flag

            # Date Check
            try:
                date_picker = question.find_element(By.CLASS_NAME, 'artdeco-datepicker__input ')
                date_picker.clear()
                date_picker.send_keys(date.today().strftime("%m/%d/%y"))
                time.sleep(3)
                date_picker.send_keys(Keys.RETURN)
                time.sleep(2)
                continue
            except:
                print("An exception occurred while filling up date picker field")  # TODO: Put logging behind debug flag

            # Dropdown check
            try:
                question_text = question.find_element(By.TAG_NAME, 'label').text.lower()
                print(f"Dropdown question text: {question_text}")  # TODO: Put logging behind debug flag
                dropdown_field = question.find_element(By.TAG_NAME, 'select')

                select = Select(dropdown_field)
                options = [options.text for options in select.options]
                print(f"Dropdown options: {options}")  # TODO: Put logging behind debug flag

                if 'proficiency' in question_text:
                    proficiency = "None"
                    for language in self.languages:
                        if language.lower() in question_text:
                            proficiency = self.languages[language]
                            break
                    self.select_dropdown(dropdown_field, proficiency)

                elif 'clearance' in question_text:
                    answer = self.get_answer('securityClearance')

                    choice = ""
                    for option in options:
                        if answer == 'yes':
                            choice = option
                        else:
                            if 'no' in option.lower():
                                choice = option
                    if choice == "":
                        self.record_unprepared_question(text_field_type, question_text)
                    self.select_dropdown(dropdown_field, choice)

                elif 'assessment' in question_text:
                    answer = self.get_answer('assessment')
                    choice = ""
                    for option in options:
                        if answer == 'yes':
                            choice = option
                        else:
                            if 'no' in option.lower():
                                choice = option
                    # if choice == "":
                    #    choice = options[len(options) - 1]
                    self.select_dropdown(dropdown_field, choice)

                elif 'commut' in question_text or 'on-site' in question_text or 'hybrid' in question_text or 'onsite' in question_text:
                    answer = self.get_answer('commute')

                    choice = ""
                    for option in options:
                        if answer == 'yes':
                            choice = option
                        else:
                            if 'no' in option.lower():
                                choice = option
                    # if choice == "":
                    #    choice = options[len(options) - 1]
                    self.select_dropdown(dropdown_field, choice)

                elif 'country code' in question_text:
                    self.select_dropdown(dropdown_field, self.personal_info['Phone Country Code'])

                elif 'north korea' in question_text:
                    choice = ""
                    for option in options:
                        if 'no' in option.lower():
                            choice = option
                    if choice == "":
                        choice = options[len(options) - 1]
                    self.select_dropdown(dropdown_field, choice)

                elif 'previously employed' in question_text or 'previous employment' in question_text:
                    choice = ""
                    for option in options:
                        if 'no' in option.lower():
                            choice = option
                    if choice == "":
                        choice = options[len(options) - 1]
                    self.select_dropdown(dropdown_field, choice)

                elif 'sponsor' in question_text:
                    answer = self.get_answer('requireVisa')
                    choice = ""
                    for option in options:
                        if answer == 'yes':
                            choice = option
                        else:
                            if 'no' in option.lower():
                                choice = option
                    if choice == "":
                        choice = options[len(options) - 1]
                    self.select_dropdown(dropdown_field, choice)

                elif 'above 18' in question_text.lower():  # Check for "above 18" in the question text
                    choice = ""
                    for option in options:
                        if 'yes' in option.lower():  # Select 'yes' option
                            choice = option
                    if choice == "":
                        choice = options[0]  # Default to the first option if 'yes' is not found
                    self.select_dropdown(dropdown_field, choice)

                elif 'currently living' in question_text or 'currently reside' in question_text:
                    answer = self.get_answer('residency')
                    choice = ""
                    for option in options:
                        if answer == 'yes':
                            choice = option
                        else:
                            if 'no' in option.lower():
                                choice = option
                    if choice == "":
                        choice = options[len(options) - 1]
                    self.select_dropdown(dropdown_field, choice)

                elif 'authorized' in question_text or 'authorised' in question_text:
                    answer = self.get_answer('legallyAuthorized')
                    choice = ""
                    for option in options:
                        if answer == 'yes':
                            # find some common words
                            choice = option
                        else:
                            if 'no' in option.lower():
                                choice = option
                    if choice == "":
                        choice = options[len(options) - 1]
                    self.select_dropdown(dropdown_field, choice)

                elif 'citizenship' in question_text:
                    answer = self.get_answer('legallyAuthorized')
                    choice = ""
                    for option in options:
                        if answer == 'yes':
                            if 'no' in option.lower():
                                choice = option
                    if choice == "":
                        choice = options[len(options) - 1]
                    self.select_dropdown(dropdown_field, choice)

                elif 'clearance' in question_text:
                    answer = self.get_answer('clearance')
                    choice = ""
                    for option in options:
                        if answer == 'yes':
                            choice = option
                        else:
                            if 'no' in option.lower():
                                choice = option
                    if choice == "":
                        choice = options[len(options) - 1]

                    self.select_dropdown(dropdown_field, choice)

                elif any(keyword in question_text.lower() for keyword in
                         [
                             'aboriginal', 'native', 'indigenous', 'tribe', 'first nations',
                             'native american', 'native hawaiian', 'inuit', 'metis', 'maori',
                             'aborigine', 'ancestral', 'native peoples', 'original people',
                             'first people', 'gender', 'race', 'disability', 'latino'
                         ]):
                    negative_keywords = ['prefer', 'decline', 'don\'t', 'specified', 'none']

                    choice = ""
                    choice = next((option for options in option.lower() if
                               any(neg_keyword in option.lower() for neg_keyword in negative_keywords)), None)

                    self.select_dropdown(dropdown_field, choice)

                elif 'email' in question_text:
                    continue  # assume email address is filled in properly by default

                elif 'experience' in question_text or 'understanding' in question_text or 'familiar' in question_text or 'comfortable' in question_text or 'able to' in question_text:
                    answer = 'no'
                    if self.experience_default > 0:
                        answer = 'yes'
                    else:
                        for experience in self.experience:
                            if experience.lower() in question_text and self.experience[experience] > 0:
                                answer = 'yes'
                                break
                    if answer == 'no':
                        # record unlisted experience as unprepared questions
                        self.record_unprepared_question("dropdown", question_text)

                    choice = ""
                    for option in options:
                        if answer in option.lower():
                            choice = option
                    if choice == "":
                        choice = options[len(options) - 1]
                    self.select_dropdown(dropdown_field, choice)

                else:
                    print(f"Unhandled dropdown question: {question_text}")
                    

                    # Since no response can be determined, we use AI to identify the best responseif available, falling back "yes" or the final response if the AI response is not available
                    choice = options[len(options) - 1]
                    choices = [(i, option) for i, option in enumerate(options)]
                    ai_response = self.ai_response_generator.generate_response(
                        question_text,
                        response_type="choice",
                        options=choices
                    )
                    self.record_unprepared_question("dropdown", question_text,ai_response)
                    if ai_response is not None:
                        choice = options[ai_response]
                    else:
                        choice = ""
                        for option in options:
                            if 'yes' in option.lower():
                                choice = option

                    print(f"Selected option: {choice}")
                    self.select_dropdown(dropdown_field, choice)
                continue
            except:
                print("An exception occurred while filling up dropdown field")  # TODO: Put logging behind debug flag

            # Checkbox check for agreeing to terms and service
            try:
                clickable_checkbox = question.find_element(By.TAG_NAME, 'label')
                clickable_checkbox.click()
            except:
                print("An exception occurred while filling up checkbox field")  # TODO: Put logging behind debug flag

    def unfollow(self):
        try:
            follow_checkbox = self.browser.find_element(By.XPATH,
                                                        "//label[contains(.,\'to stay up to date with their page.\')]").click()
            follow_checkbox.click()
        except:
            pass

    def send_resume(self):
        print("Trying to send resume")
        try:
            file_upload_elements = (By.CSS_SELECTOR, "input[name='file']")
            if len(self.browser.find_elements(file_upload_elements[0], file_upload_elements[1])) > 0:
                input_buttons = self.browser.find_elements(file_upload_elements[0], file_upload_elements[1])
                if len(input_buttons) == 0:
                    raise Exception("No input elements found in element")
                for upload_button in input_buttons:
                    upload_type = upload_button.find_element(By.XPATH, "..").find_element(By.XPATH,
                                                                                          "preceding-sibling::*")
                    if 'resume' in upload_type.text.lower():
                        upload_button.send_keys(self.resume_dir)
                    elif 'cover' in upload_type.text.lower():
                        if self.cover_letter_dir != '':
                            upload_button.send_keys(self.cover_letter_dir)
                        elif 'required' in upload_type.text.lower():
                            upload_button.send_keys(self.resume_dir)
        except:
            print("Failed to upload resume or cover letter!")
            pass

    def enter_text(self, element, text):
        element.clear()
        element.send_keys(text)

    def select_dropdown(self, element, text):
        select = Select(element)
        select.select_by_visible_text(text)

    # Radio Select
    def radio_select(self, element, label_text, clickLast=False):
        label = element.find_element(By.TAG_NAME, 'label')
        if label_text in label.text.lower() or clickLast == True:
            label.click()

    # Contact info fill-up
    def contact_info(self, form):
        print("Trying to fill up contact info fields")
        frm_el = form.find_elements(By.TAG_NAME, 'label')
        if len(frm_el) > 0:
            for el in frm_el:
                text = el.text.lower()
                if 'email address' in text:
                    continue
                elif 'phone number' in text:
                    try:
                        country_code_picker = el.find_element(By.XPATH,
                                                              '//select[contains(@id,"phoneNumber")][contains(@id,"country")]')
                        self.select_dropdown(country_code_picker, self.personal_info['Phone Country Code'])
                    except Exception as e:
                        print("Country code " + self.personal_info[
                            'Phone Country Code'] + " not found. Please make sure it is same as in LinkedIn.")
                        print(e)
                    try:
                        phone_number_field = el.find_element(By.XPATH,
                                                             '//input[contains(@id,"phoneNumber")][contains(@id,"nationalNumber")]')
                        self.enter_text(phone_number_field, self.personal_info['Mobile Phone Number'])
                    except Exception as e:
                        print("Could not enter phone number:")
                        print(e)

    def fill_up(self):
        try:
            easy_apply_modal_content = self.browser.find_element(By.CLASS_NAME, "jobs-easy-apply-modal__content")
            form = easy_apply_modal_content.find_element(By.TAG_NAME, 'form')
            try:
                label = form.find_element(By.TAG_NAME, 'h3').text.lower()
                if 'home address' in label:
                    self.home_address(form)
                elif 'contact info' in label:
                    self.contact_info(form)
                elif 'resume' in label:
                    self.send_resume()
                else:
                    self.additional_questions(form)
            except Exception as e:
                print("An exception occurred while filling up the form:")
                print(e)
        except:
            print("An exception occurred while searching for form in modal")

    def write_to_file(self, company, job_title, link, location, search_location):
        to_write = [company, job_title, link, location, search_location, datetime.now()]
        file_path = self.file_name + ".csv"
        print(f'updated {file_path}.')

        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(to_write)

    def record_unprepared_question(self, answer_type, question_text,airesponse=""):
        to_write = [answer_type, question_text,airesponse]
        file_path = self.unprepared_questions_file_name + ".csv"

        try:
            with open(file_path, 'a') as f:
                writer = csv.writer(f)
                writer.writerow(to_write)
                print(f'Updated {file_path} with {to_write}.')
        except:
            print(
                "Special characters in questions are not allowed. Failed to update unprepared questions log.")
            print(question_text)

    def scroll_slow(self, scrollable_element, start=0, end=3600, step=100, reverse=False):
        if reverse:
            start, end = end, start
            step = -step

        for i in range(start, end, step):
            self.browser.execute_script("arguments[0].scrollTo(0, {})".format(i), scrollable_element)
            time.sleep(random.uniform(0.1, .6))

    def avoid_lock(self):
        if self.disable_lock:
            return

        pyautogui.keyDown('ctrl')
        pyautogui.press('esc')
        pyautogui.keyUp('ctrl')
        time.sleep(1.0)
        pyautogui.press('esc')

    def get_base_search_url(self, parameters):
        remote_url = ""
        lessthanTenApplicants_url = ""
        newestPostingsFirst_url = ""

        if parameters.get('remote'):
            remote_url = "&f_WT=2"
        else:
            remote_url = ""
            # TO DO: Others &f_WT= options { WT=1 onsite, WT=2 remote, WT=3 hybrid, f_WT=1%2C2%2C3 }

        if parameters['lessthanTenApplicants']:
            lessthanTenApplicants_url = "&f_EA=true"

        if parameters['newestPostingsFirst']:
            newestPostingsFirst_url += "&sortBy=DD"

        level = 1
        experience_level = parameters.get('experienceLevel', [])
        experience_url = "f_E="
        for key in experience_level.keys():
            if experience_level[key]:
                experience_url += "%2C" + str(level)
            level += 1

        distance_url = "?distance=" + str(parameters['distance'])

        job_types_url = "f_JT="
        job_types = parameters.get('jobTypes', [])
        # job_types = parameters.get('experienceLevel', [])
        for key in job_types:
            if job_types[key]:
                job_types_url += "%2C" + key[0].upper()

        date_url = ""
        dates = {"all time": "", "month": "&f_TPR=r2592000", "week": "&f_TPR=r604800", "24 hours": "&f_TPR=r86400"}
        date_table = parameters.get('date', [])
        for key in date_table.keys():
            if date_table[key]:
                date_url = dates[key]
                break

        easy_apply_url = ""

        extra_search_terms = [distance_url, remote_url, lessthanTenApplicants_url, newestPostingsFirst_url, job_types_url, experience_url]
        extra_search_terms_str = '&'.join(
            term for term in extra_search_terms if len(term) > 0) + easy_apply_url + date_url

        return extra_search_terms_str

    def next_job_page(self, position, location, job_page):
        self.browser.get("https://www.linkedin.com/jobs/search/" + self.base_search_url +
                         "&keywords=" + position + location + "&start=" + str(job_page * 25))

        self.avoid_lock()
