import csv
import json
import logging
import os
import random
import re
import time
import traceback
from datetime import date, datetime
from itertools import product
from pathlib import Path
from typing import Dict, List, Tuple

import faiss
import numpy as np
import ollama
import pyautogui
import PyPDF2
import requests
from dotenv import load_dotenv
from litellm import completion
from pypdf import PdfReader
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

# Add new imports for RAG
from sentence_transformers import SentenceTransformer

load_dotenv()


class AIResponseGenerator:
    def __init__(
        self,
        api_key,
        personal_info,
        experience,
        languages,
        resume_path,
        checkboxes,
        model_name,
        text_resume_path=None,
        debug=False,
    ):
        self.personal_info = personal_info
        self.experience = experience
        self.languages = languages
        self.pdf_resume_path = resume_path
        self.text_resume_path = text_resume_path
        self.checkboxes = checkboxes
        self._resume_content = None
        self._client = True
        self.model_name = model_name
        self.debug = debug
        self.resume_dir = resume_path

        # Initialize RAG components
        self._embedding_model = None
        self._resume_chunks = None
        self._chunk_embeddings = None
        self._faiss_index = None
        self._context_cache = {}
        self._last_ai_response_text = None  # Store last AI response text for CSV
        
        # Setup logging for AI responses
        self._setup_logging()

    @property
    def embedding_model(self):
        """Lazy load the embedding model"""
        if self._embedding_model is None:
            print("Loading embedding model...")
            # Using a small, efficient model
            self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            print("Embedding model loaded successfully")
        return self._embedding_model

    @property
    def resume_chunks(self):
        """Lazy load resume chunks"""
        if self._resume_chunks is None:
            self._resume_chunks = self._create_semantic_chunks()
        return self._resume_chunks

    def _setup_logging(self):
        """Setup file logging for AI responses"""
        # Create output directory if it doesn't exist
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger("AIResponseGenerator")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # File handler for AI responses
        log_file = output_dir / "ai_responses.log"
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info("=" * 80)
        self.logger.info("AI Response Generator initialized")
        self.logger.info("=" * 80)

    def _create_semantic_chunks(self, chunk_size=200, overlap=50) -> List[Dict]:
        """Create semantic chunks from resume content"""
        resume_text = self.resume_content
        if not resume_text:
            return []

        chunks = []

        # Split by common resume sections first
        section_headers = [
            "experience",
            "education",
            "skills",
            "projects",
            "certifications",
            "summary",
            "objective",
            "achievements",
            "publications",
            "work experience",
            "professional experience",
            "technical skills",
            "programming languages",
        ]

        # Split into paragraphs and sections
        paragraphs = [p.strip() for p in resume_text.split("\n\n") if p.strip()]

        current_section = "general"
        for i, paragraph in enumerate(paragraphs):
            # Check if this paragraph is a section header
            is_header = any(header in paragraph.lower() for header in section_headers)
            if is_header:
                current_section = paragraph.lower()

            # Create chunks with context
            words = paragraph.split()
            for j in range(0, len(words), chunk_size - overlap):
                chunk_words = words[j : j + chunk_size]
                chunk_text = " ".join(chunk_words)

                if len(chunk_text.strip()) > 50:  # Only include meaningful chunks
                    chunks.append(
                        {
                            "text": chunk_text,
                            "section": current_section,
                            "paragraph_index": i,
                            "chunk_index": len(chunks),
                        }
                    )

        # Add personal info as a special chunk
        # Include all personal_info fields
        personal_info_fields = ", ".join(
            f"{k}: {v}" for k, v in self.personal_info.items()
        )
        us_citizen = (
            f"US Citizen: {'Yes' if self.checkboxes.get('USCitizen') else 'No'}"
        )
        require_visa = (
            f"Require Visa: {'Yes' if self.checkboxes.get('requireVisa') else 'No'}"
        )
        authorized_us = f"Authorized to work in US: {'Yes' if self.checkboxes.get('legallyAuthorized') else 'No'}"
        current_role = self.experience.get("currentRole", "AI Specialist")
        skills = f"Skills: {', '.join(list(self.experience.keys()))}"
        languages = f"Languages: {', '.join(f'{lang}: {level}' for lang, level in self.languages.items())}"

        personal_chunk = f"{personal_info_fields}, {us_citizen}, {require_visa}, {authorized_us}, Current Role: {current_role}, {skills}, {languages}"

        chunks.insert(
            0,
            {
                "text": personal_chunk,
                "section": "personal_info",
                "paragraph_index": -1,
                "chunk_index": -1,
            },
        )

        print(f"Created {len(chunks)} semantic chunks from resume")
        return chunks

    def _build_vector_index(self):
        """Build FAISS index for semantic search"""
        if self._faiss_index is not None:
            return

        chunks = self.resume_chunks
        if not chunks:
            return

        print("Building vector index...")
        # Get embeddings for all chunks
        chunk_texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embedding_model.encode(chunk_texts, show_progress_bar=False)

        # Create FAISS index
        dimension = embeddings.shape[1]
        self._faiss_index = faiss.IndexFlatIP(
            dimension
        )  # Inner product for cosine similarity

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        self._faiss_index.add(embeddings.astype("float32"))

        self._chunk_embeddings = embeddings
        print(f"Vector index built with {len(chunks)} chunks")

    def _semantic_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Perform semantic search on resume chunks"""
        self._build_vector_index()

        if self._faiss_index is None or not self.resume_chunks:
            return []

        # Encode query
        query_embedding = self.embedding_model.encode([query], show_progress_bar=False)
        faiss.normalize_L2(query_embedding)

        # Search
        scores, indices = self._faiss_index.search(
            query_embedding.astype("float32"), top_k
        )

        # Return relevant chunks with scores
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.resume_chunks):
                chunk = self.resume_chunks[idx].copy()
                chunk["relevance_score"] = float(score)
                results.append(chunk)

        return results

    def _build_context_rag(self, query="", job_description="", max_tokens=2000):
        """
        Build focused context using semantic RAG
        """
        # Create cache key
        cache_key = hash(query + job_description + str(max_tokens))
        if cache_key in self._context_cache:
            return self._context_cache[cache_key]

        context_parts = []

        # Always include personal info (it's the first chunk)
        personal_chunk = self.resume_chunks[0] if self.resume_chunks else None
        if personal_chunk:
            context_parts.append(f"Personal Info: {personal_chunk['text']}")

        # Combine query and job description for search
        search_query = f"{query} {job_description}".strip()

        if search_query:
            # Perform semantic search
            relevant_chunks = self._semantic_search(search_query, top_k=8)

            # Filter out personal info chunk (already included)
            relevant_chunks = [
                chunk for chunk in relevant_chunks if chunk.get("chunk_index", 0) != -1
            ]

            # Group by section and add most relevant content
            sections_added = set()
            total_chars = len(context_parts[0]) if context_parts else 0

            for chunk in relevant_chunks:
                if total_chars >= max_tokens * 4:  # Rough token estimation
                    break

                section = chunk["section"]
                chunk_text = chunk["text"]

                # Add section header if new section
                if section not in sections_added and section != "general":
                    section_header = f"\n{section.title().replace('_', ' ')}:"
                    context_parts.append(section_header)
                    sections_added.add(section)
                    total_chars += len(section_header)

                # Add chunk content
                context_parts.append(chunk_text)
                total_chars += len(chunk_text)

                if self.debug:
                    print(
                        f"Added chunk (score: {chunk['relevance_score']:.3f}): {chunk_text[:100]}..."
                    )

        # Join context
        context = "\n\n".join(context_parts)

        # Truncate if too long
        if len(context) > max_tokens * 4:
            context = context[: max_tokens * 4] + "..."

        # Cache the result
        self._context_cache[cache_key] = context

        if self.debug:
            print(f"Built RAG context with {len(context)} characters")

        return context

    @property
    def resume_content(self):
        if self._resume_content is None:
            # First try to read from text resume if available
            if self.text_resume_path:
                try:
                    with open(self.text_resume_path, "r", encoding="utf-8") as f:
                        self._resume_content = f.read()
                        print("Successfully loaded text resume")
                        return self._resume_content
                except Exception as e:
                    print(f"Could not read text resume: {str(e)}")

            # Fall back to PDF resume if text resume fails or isn't available
            # Ensure this uses self.resume_dir which might be updated
            current_pdf_path = (
                self.resume_dir
                if hasattr(self, "resume_dir") and self.resume_dir
                else self.pdf_resume_path
            )
            try:
                content = []
                # reader = PdfReader(self.pdf_resume_path) # Original line
                reader = PdfReader(current_pdf_path)  # Use current_pdf_path
                for page in reader.pages:
                    content.append(page.extract_text())
                self._resume_content = "\n".join(content)
                print(f"Successfully loaded PDF resume from {current_pdf_path}")
            except Exception as e:
                print(
                    f"Could not extract text from resume PDF ({current_pdf_path}): {str(e)}"
                )
                self._resume_content = ""
        return self._resume_content

    def _build_context(self):
        """Legacy method - now uses RAG by default"""
        return self._build_context_rag()

    def get_tailored_skills_replacements(self, job_description):
        # Step 1: Extract top 10 technical skills from job description
        system_prompt_1 = (
            "You are an expert resume and job description analyst.\n"
            "Your task is to read the job description below and extract the **top 10 technical skills or tools** that are essential for the role.\n"
            "Guidelines:\n"
            "- Return skills exactly as written in the job description (no synonyms, no rewording).\n"
            "- Include programming languages, libraries, frameworks, cloud platforms, APIs, machine learning techniques, tools, and standards mentioned.\n"
            "- Focus on the most important and unique technical terms. Do not include soft skills or generic phrases.\n"
            "- Return the output as a **comma-separated list** of skill keywords, in order of relevance and frequency.\n\n"
            f"Job Description:\n{job_description}"
        )
        try:
            response_1 = completion(
                model=self.model_name,
                messages=[{"role": "system", "content": system_prompt_1}],
            )
            job_skills = response_1.choices[0]["message"]["content"].strip()
        except Exception as e:
            print(f"Error extracting job skills: {str(e)}")
            return None

        # Step 2: Suggest tailored skill replacements
        MAX_SKILL_REPLACEMENTS = 5
        system_prompt_2 = (
            "You are an AI assistant specialized in optimizing resumes for Applicant Tracking Systems (ATS).\n\n"
            "Your task:\n"
            "Given a list of resume skills and a list of job description skills, identify **exactly 5 skills** from the resume that can be replaced with **more relevant skills from the job description** to improve alignment and ATS score.\n\n"
            "Strict Rules:\n"
            '1. Each "old" skill must exist in the resume.\n'
            '2. Each "new" skill must exist in the job description and **must NOT already exist in the resume**.\n'
            "3. DO NOT suggest replacements that are already present in the resume in any form (no duplicates, no synonyms).\n"
            "4. Only suggest replacements where the old and new skills are **semantically similar** — i.e., they belong to the same category or purpose (e.g., frameworks, cloud platforms, dev tools, AI methods, APIs).\n"
            "5. Return **exactly 5 valid replacements**. If there are not enough matches, return fewer — do not force unrelated replacements.\n"
            "6. Your output must be a **JSON array**, in this exact format:\n\n"
            "[\n"
            '{"old": "old_resume_skill", "new": "new_job_description_skill"},\n'
            '{"old": "old_resume_skill", "new": "new_job_description_skill"},\n'
            "...\n"
            "]\n\n"
            "Do not include any explanation, heading, or commentary. Only output the JSON array."
        )
        user_content_2 = f"Job Skills:\n{job_skills}\n\nResume:\n{self.resume_content}"
        try:
            response_2 = completion(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt_2},
                    {"role": "user", "content": user_content_2},
                ],
            )
            answer = response_2.choices[0]["message"]["content"].strip()
            replacements = json.loads(re.search(r"\[.*\]", answer, re.DOTALL).group())
            print(f"AI response: {answer}")
            return replacements[:MAX_SKILL_REPLACEMENTS]
        except Exception as e:
            print(f"Error using AI to generate resume tailoring skills: {str(e)}")
            return None

    def tailor_resume_pdf(self, replacements, input_pdf_path):
        try:
            if not input_pdf_path:
                print("Error: Input PDF path is not provided.")
                return None

            print(f"Starting to tailor PDF: {input_pdf_path}")
            pdf_reader = PyPDF2.PdfReader(input_pdf_path)
            pdf_writer = PyPDF2.PdfWriter()

            modified_texts = []

            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                try:
                    original_text = page.extract_text()
                    if original_text is None:
                        print(
                            f"Warning: Could not extract text from page {page_num + 1}."
                        )
                        # Add original page if text extraction fails
                        pdf_writer.add_page(page)
                        continue

                    modified_page_text = original_text
                    for r in replacements:
                        old_skill = r["old"]
                        new_skill = r["new"]
                        # Use re.compile for case-insensitive search and re.escape for literal matching
                        pattern = re.compile(re.escape(old_skill), re.IGNORECASE)
                        if pattern.search(modified_page_text):
                            modified_page_text = pattern.sub(
                                new_skill, modified_page_text
                            )
                            print(
                                f"  Page {page_num + 1}: Replaced '{old_skill}' (case-insensitively) with '{new_skill}'"
                            )
                        else:
                            if self.debug:
                                print(
                                    f"  Page {page_num + 1}: Skill '{old_skill}' not found for replacement (checked case-insensitively)."
                                )

                    modified_texts.append(
                        {
                            "page": page_num + 1,
                            "original_text_snippet": original_text[:100]
                            + "...",  # Log snippet
                            "modified_text_snippet": modified_page_text[:100]
                            + "...",  # Log snippet
                        }
                    )

                    # Add the original page to the writer, as PyPDF2 doesn't support easy in-place text replacement
                    # The text replacement performed above is on the extracted string and not on the PDF page object directly.
                    pdf_writer.add_page(page)

                except Exception as e:
                    print(f"Error processing page {page_num + 1}: {str(e)}")
                    # Add original page in case of error processing it
                    pdf_writer.add_page(page)

            # Define dynamic output path based on input path
            directory = os.path.dirname(input_pdf_path)
            base_name = os.path.basename(input_pdf_path)
            name, ext = os.path.splitext(base_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_pdf_path = os.path.join(
                directory, f"{name}_tailored_{timestamp}{ext}"
            )

            with open(output_pdf_path, "wb") as output_file:
                pdf_writer.write(output_file)

            self.resume_dir = (
                output_pdf_path  # Update the resume_dir with the path of the new PDF
            )
            self._resume_content = (
                None  # Reset resume content so it's re-read next time
            )

            print(
                f"Resume tailoring process complete. Modified PDF (original structure preserved) saved to: {output_pdf_path}"
            )
            if modified_texts:
                print(
                    "Summary of text modifications (logged, not directly in PDF page content):"
                )
                for mod_text in modified_texts:
                    print(f"  Page {mod_text['page']}:")
                    # print(f"    Original snippet: {mod_text['original_text_snippet']}") # Potentially verbose
                    print(
                        f"    Attempted changes for page {mod_text['page']} logged above during processing."
                    )
            print(
                "Note: PyPDF2 does not support direct in-place text editing of PDF content streams easily. The original PDF structure is preserved. Text replacements are logged."
            )

        except FileNotFoundError:
            print(f"Error: The input PDF file was not found at {input_pdf_path}")
            return None
        except PyPDF2.errors.PdfReadError as pre:
            print(
                f"Error reading PDF {input_pdf_path}. It might be corrupted or password-protected: {str(pre)}"
            )
            return None
        except Exception as e:
            print(f"Error during PDF tailoring: {str(e)}")
            traceback.print_exc()
            return None
        return output_pdf_path

    def generate_response(
        self, question_text, response_type="text", options=None, max_tokens=100, jd=""
    ):
        """
        Generate a response using OpenAI's API with RAG-optimized context
        """
        try:
            # Use RAG context with job description
            context = self._build_context_rag(
                query=question_text, job_description=jd, max_tokens=1500
            )

            system_prompt = {
                "text": "You are a helpful assistant answering job application questions professionally and short. Use the candidate's background information and resume to personalize responses. Pretend you are the candidate. Only give the answer if you are sure from background. Otherwise return NA.",
                "numeric": "You are a helpful assistant providing numeric answers to job application questions. Based on the candidate's experience, provide a single number as your response. No explanation needed.",
                "choice": "You are a helpful assistant selecting the most appropriate answer choice for job application questions. Based on the candidate's background, select the best option by returning only its index number. No explanation needed.",
            }[response_type]

            user_content = f"Using this candidate's background and resume:\n{context}\n\nPlease answer this job application question: {question_text}"
            if response_type == "choice" and options:
                options_text = "\n".join([f"{idx}: {text}" for idx, text in options])
                user_content += f"\n\nSelect the most appropriate answer by providing its index number from these options:\n{options_text}"

            response = completion(
                model="groq/openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
            )

            answer = response.choices[0]["message"]["content"].strip()
            
            # Handle reasoning tags - extract only the actual response
            # Some models return responses in format: <tag>...</tag> Actual answer here
            # Handle both <think> and <think> tags used by different models
            reasoning_tags = [
                ("<think>", "</think>"),
                ("<think>", "</think>"),
            ]
            
            for open_tag, close_tag in reasoning_tags:
                if open_tag in answer and close_tag in answer:
                    # Extract text after the closing tag
                    parts = answer.split(close_tag, 1)
                    if len(parts) > 1:
                        answer = parts[1].strip()
                    else:
                        # Fallback: remove the tags if format is unexpected
                        answer = re.sub(f'{re.escape(open_tag)}.*?{re.escape(close_tag)}', '', answer, flags=re.DOTALL).strip()
                    break  # Only process one type of tag
            
            # Store original answer for CSV logging (before cleaning)
            original_answer = answer
            
            # Log AI response to file and console
            log_message = f"\n{'='*80}\n"
            log_message += f"Question Type: {response_type}\n"
            log_message += f"Question: {question_text}\n"
            if options:
                log_message += f"Options: {options}\n"
            if jd:
                log_message += f"Job Description Context: {jd[:200]}...\n"
            log_message += f"AI Response (cleaned): {answer}\n"
            log_message += f"{'='*80}\n"
            
            self.logger.info(log_message)
            print(f"AI response: {answer}")

            # Store original answer as attribute for CSV logging
            self._last_ai_response_text = original_answer

            if response_type == "numeric":
                numbers = re.findall(r"\d+", answer)
                if numbers:
                    return int(numbers[0])
                return 0
            elif response_type == "choice":
                numbers = re.findall(r"\d+", answer)
                if numbers and options:
                    index = int(numbers[0])
                    if 0 <= index < len(options):
                        return index
                return None

            return answer

        except Exception as e:
            error_msg = f"Error using AI to generate response: {str(e)}\nQuestion: {question_text}\nResponse Type: {response_type}"
            self.logger.error(error_msg)
            print(f"Error using AI to generate response: {str(e)}")
            return None

    def evaluate_job_fit(self, job_title, job_description):
        """
        Evaluate job fit using RAG for more focused comparison
        """
        try:
            # First, get job summary
            system_prompt = "Given Job description summarize it in 120 words, focus on qualifications and years of experience and technical skills. Expertise needed"
            response = completion(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Job: {job_title}\n{job_description}"},
                ],
            )

            job_summary = response.choices[0]["message"]["content"].strip()
            time.sleep(random.uniform(2, 4))

            # Use RAG to get relevant context for the job
            context = self._build_context_rag(
                query=f"{job_title} requirements qualifications",
                job_description=job_summary,
                max_tokens=1200,
            )

            system_prompt = """
                Based on the candidate's resume and the job description, respond with APPLY if the resume matches at least 85 percent of the required qualifications and experience. Otherwise, respond with SKIP.
                
                IMPORTANT: Always put your final decision (APPLY or SKIP) OUTSIDE and AFTER any reasoning tags. 
                Format: <think>your reasoning here</think> APPLY
                or: <think>your reasoning here</think> SKIP
                
                The decision must appear after the closing tag.
            """

            if self.debug:
                system_prompt += """Return APPLY or SKIP followed by a brief explanation. Format response as: <think>reasoning</think> APPLY/SKIP: [brief reason]"""
            else:
                system_prompt += """Return only: <think>reasoning</think> APPLY or <think>reasoning</think> SKIP"""

            response = completion(
                model="groq/qwen/qwen3-32b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Job: {job_title}\n{job_summary}\n\nCandidate:\n{context}",
                    },
                ],
                temperature=0.9,
                # Increase max tokens significantly to accommodate long reasoning tags + decision
                # Models with <think> tags can generate very long reasoning, so we need ample space
                max_completion_tokens=1500 if self.debug else 1000,
            )

            answer = response.choices[0]["message"]["content"].strip()
            raw_answer = answer  # Keep original for logging
            
            # Check if response was truncated (common with long reasoning)
            finish_reason = response.choices[0].get("finish_reason", "")
            was_truncated = finish_reason == "length"  # Token limit reached
            
            # Handle reasoning tags - extract only the actual response
            # Some models return responses in format: <tag>...</tag> Actual answer here
            reasoning_tags = [
                ("<think>", "</think>"),
                ("<think>", "</think>"),
            ]
            
            # First, try to extract decision from after the closing tag
            decision_found = False
            for open_tag, close_tag in reasoning_tags:
                if open_tag in answer and close_tag in answer:
                    # Extract text after the closing tag
                    parts = answer.split(close_tag, 1)
                    if len(parts) > 1:
                        answer_after_tags = parts[1].strip()
                        # Check if decision is in the text after tags
                        answer_upper = answer_after_tags.upper()
                        if "APPLY" in answer_upper:
                            decision = "APPLY"
                            decision_found = True
                            answer = answer_after_tags
                            break
                        elif "SKIP" in answer_upper:
                            decision = "SKIP"
                            decision_found = True
                            answer = answer_after_tags
                            break
                    break  # Only process one type of tag
            
            # If decision not found after tags, search the entire response
            if not decision_found:
                answer_upper = answer.upper()
                if "APPLY" in answer_upper:
                    decision = "APPLY"
                elif "SKIP" in answer_upper:
                    decision = "SKIP"
                else:
                    # Fallback: check if it starts with A (for APPLY) or S (for SKIP)
                    # If truncated and no decision found, default to SKIP (safer)
                    if was_truncated:
                        decision = "SKIP"
                        self.logger.warning(f"Response was truncated and no clear decision found. Defaulting to SKIP.")
                    else:
                        decision = "APPLY" if answer_upper.startswith("A") else "SKIP"
            
            # Warn if response was truncated
            if was_truncated:
                self.logger.warning(f"Response was truncated (finish_reason: {finish_reason}). Decision extracted: {decision}")
            
            # Log job fit evaluation
            log_message = f"\n{'='*80}\n"
            log_message += f"JOB FIT EVALUATION\n"
            log_message += f"Job Title: {job_title}\n"
            log_message += f"Job Description (first 300 chars): {job_description[:300]}...\n"
            log_message += f"AI Evaluation (raw): {response.choices[0]['message']['content'].strip()}\n"
            log_message += f"AI Evaluation (cleaned): {answer}\n"
            log_message += f"Decision: {decision}\n"
            log_message += f"{'='*80}\n"
            
            self.logger.info(log_message)
            print(f"AI evaluation: {answer}")
            print(f"Decision: {decision}")
            time.sleep(random.uniform(2, 4))
            return decision == "APPLY"

        except Exception as e:
            error_msg = f"Error evaluating job fit: {str(e)}\nJob Title: {job_title}"
            self.logger.error(error_msg)
            print(f"Error evaluating job fit: {str(e)}")
            return True
