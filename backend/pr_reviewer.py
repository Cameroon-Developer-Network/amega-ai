from typing import List, Dict, Optional

class PRReviewer:
    def __init__(self, llm_manager):
        """
        Initializes the PRReviewer with a language model manager.

        Args:
        	llm_manager: An object responsible for managing interactions with a large language model.
        """
        self.llm_manager = llm_manager

    async def review_changes(self, diff_content: str) -> Dict:
        """
        Analyzes a git diff and returns categorized review feedback using a language model.

        The returned dictionary contains lists of issues, style suggestions, performance considerations, security concerns, and general suggestions extracted from the model's response.

        Args:
        	diff_content: The git diff string representing code changes to review.

        Returns:
        	A dictionary with keys 'ISSUES', 'STYLE', 'PERFORMANCE', 'SECURITY', and 'SUGGESTIONS', each mapping to a list of feedback items.
        """
        # Prepare the prompt for the LLM
        prompt = self._prepare_review_prompt(diff_content)

        # Get review comments from LLM
        review_response = await self.llm_manager.generate_response(
            prompt,
            max_length=1000,
            temperature=0.7
        )

        return self._parse_review_response(review_response)

    def _prepare_review_prompt(self, diff_content: str) -> str:
        """
        Constructs a detailed prompt instructing the LLM to review code changes for issues, style, performance, security, and suggestions.

        Args:
            diff_content: The git diff string representing code changes to be reviewed.

        Returns:
            A formatted prompt string for the LLM to analyze and respond with categorized feedback.
        """
        return f"""Please review the following code changes and provide:
1. Potential issues or bugs
2. Code style improvements
3. Performance considerations
4. Security concerns
5. Suggested improvements

Changes to review:
{diff_content}

Format your response as:
ISSUES:
- [List any potential issues found]

STYLE:
- [List style improvements]

PERFORMANCE:
- [List performance considerations]

SECURITY:
- [List security concerns]

SUGGESTIONS:
- [List specific improvement suggestions]
"""

    def _parse_review_response(self, response: str) -> Dict:
        """
        Parses the LLM's review response into categorized lists of feedback.

        The response is split into sections labeled ISSUES, STYLE, PERFORMANCE, SECURITY, and SUGGESTIONS, with each section containing a list of bullet-pointed items.

        Args:
            response: The multiline string response from the LLM.

        Returns:
            A dictionary mapping each feedback category to a list of extracted suggestions or issues.
        """
        sections = {
            'ISSUES': [],
            'STYLE': [],
            'PERFORMANCE': [],
            'SECURITY': [],
            'SUGGESTIONS': []
        }

        current_section = None
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue

            if line.endswith(':') and line.rstrip(':').upper() in sections:
                current_section = line.rstrip(':').upper()
            elif current_section and line.startswith('-'):
                sections[current_section].append(line[1:].strip())

        return sections

    async def suggest_improvements(self, file_content: str) -> Dict:
        """
        Generates actionable suggestions to improve the provided file content.

        The suggestions focus on code organization, best practices, performance, error handling, and documentation, and are returned as a list of specific recommendations.

        Args:
            file_content: The complete content of the file to analyze.

        Returns:
            A dictionary with a 'suggestions' key containing a list of improvement suggestions.
        """
        prompt = f"""Please suggest improvements for the following code:

{file_content}

Focus on:
1. Code organization
2. Best practices
3. Performance optimizations
4. Error handling
5. Documentation

Provide specific, actionable suggestions."""

        suggestions = await self.llm_manager.generate_response(
            prompt,
            max_length=800,
            temperature=0.7
        )

        return {'suggestions': suggestions.split('\n')} 
