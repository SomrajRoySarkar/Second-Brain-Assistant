#!/usr/bin/env python3
"""
PDF Report Generator for Second Brain Assistant
Generates formal, well-formatted PDF reports based on user specifications
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, darkblue, gray
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import textwrap
from google_search import advanced_web_search

class PDFReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    def setup_custom_styles(self):
        """Setup custom styles for formal report formatting"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=darkblue,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=gray,
            fontName='Helvetica'
        ))
        
        # Section heading style - Arial Black, size 12
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            spaceBefore=20,
            alignment=TA_CENTER,
            textColor=black,
            fontName='Helvetica-Bold'  # Using Helvetica-Bold as Arial Black equivalent
        ))
        
        # Subsection heading style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeading',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=16,
            alignment=TA_CENTER,
            textColor=black,
            fontName='Helvetica-Bold'
        ))
        
        # Body text style - Normal classic font, size 12
        self.styles.add(ParagraphStyle(
            name='ReportBody',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            fontName='Times-Roman'  # Classic font
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=gray,
            fontName='Helvetica'
        ))
        
        # Table of Contents heading style
        self.styles.add(ParagraphStyle(
            name='TOCHeading',
            parent=self.styles['SectionHeading'],
            fontSize=12,
            spaceAfter=20,
            spaceBefore=10,
            alignment=TA_CENTER,
            textColor=black,
            fontName='Helvetica-Bold'
        ))

    def create_header_footer(self, canvas, doc):
        """Add header and footer to each page, except title page"""
        if doc.page == 1:
            return
        canvas.saveState()
        
        # Header (removed as per user request)
        # canvas.setFont('Helvetica-Bold', 10)
        # canvas.setFillColor(black)
        # canvas.drawString(inch, letter[1] - 0.5*inch, doc.title)
        
        # Footer (keep if you want page numbers)
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(gray)
        canvas.drawRightString(letter[0] - inch, 0.5*inch, f"Page {doc.page}")
        
        canvas.restoreState()

    def create_title_page(self, story, report_data):
        """Create a professional title page"""
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph(report_data['title'], self.styles['ReportTitle']))
        story.append(Spacer(1, 0.5*inch))
        story.append(PageBreak())

    def parse_report_request(self, user_request, ai_assistant):
        """Parse the user's report request and extract requirements"""
        # Remove the /report prefix
        request = user_request[len('/report'):].strip()
        
        # Default professional report structure
        report_data = {
            'title': 'Research Report',
            'sections': [],
            'format': 'professional',
            'include_toc': True,
            'content': request,
            'topic_only': True,
            'custom_sections': [],
            'filename': 'report'
        }
        
        # Always treat the input as a topic-based request for simplicity
        report_data['content'] = request
        
        # Use AI to intelligently summarize the description for a concise topic name
        report_data['title'] = self.generate_topic_title(request, ai_assistant)
        # Create a clean filename from title (without "Report" suffix)
        clean_title = report_data['title'].replace(' Report', '').replace(' Analysis', '').replace(' Study', '').replace(' Research', '')
        report_data['filename'] = clean_title.lower().replace(' ', '_').replace('/', '_').replace('\\', '_')
        report_data['filename'] = ''.join(c for c in report_data['filename'] if c.isalnum() or c in ('_', '-'))
        
        # Use AI to generate intelligent sections based on content type
        report_data['sections'] = self.generate_intelligent_sections(request, ai_assistant)
        
        return report_data

    def generate_intelligent_sections(self, user_input, ai_assistant):
        """Generate intelligent section headings based on content type and user request"""
        sections_prompt = f"""
        You are an expert report structuring assistant. Based on the user's request/topic, determine the most appropriate section headings for a professional report.
        
        User Request/Topic: "{user_input}"
        
        Instructions:
        - Analyze the content type and subject matter
        - Generate 4-8 appropriate section headings that would best organize this specific report
        - Consider the nature of the content (biography, technical analysis, business report, research study, etc.)
        - Use professional, clear headings that are specific to the content type
        - Always include "Introduction" as the first section and "Conclusion" as the last section
        - Make headings specific and relevant to the actual topic, not generic
        - For example:
          * For a biography: "Early Life", "Career Highlights", "Major Achievements", "Personal Life", "Legacy"
          * For a technical analysis: "Technical Overview", "Current Implementation", "Performance Analysis", "Future Developments"
          * For a business report: "Market Analysis", "Financial Performance", "Strategic Recommendations"
          * For a research study: "Literature Review", "Methodology", "Findings", "Discussion"
        
        Respond with ONLY the section headings, one per line, in the order they should appear:
        """
        
        try:
            response = ai_assistant.model.generate_content(sections_prompt)
            
            # Parse the response to extract section headings
            text = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
            sections = []
            for line in text.strip().split('\n'):
                section = line.strip()
                if section and not section.startswith('*') and not section.startswith('-'):
                    # Clean up any numbering or bullets
                    section = section.lstrip('0123456789. ').strip()
                    if section:
                        sections.append(section)
            
            # Ensure we have at least basic sections
            if not sections:
                sections = ['Introduction', 'Main Content', 'Analysis', 'Conclusion']
            
            # Ensure Introduction is first and Conclusion is last (if not already)
            if 'Introduction' not in sections:
                sections.insert(0, 'Introduction')
            if 'Conclusion' not in sections:
                sections.append('Conclusion')
            
            return sections[:8]  # Limit to 8 sections maximum
            
        except Exception as e:
            # Fallback to content-type based sections
            return self.get_fallback_sections(user_input)
    
    def get_fallback_sections(self, user_input):
        """Generate fallback sections based on content keywords"""
        input_lower = user_input.lower()
        
        # Biography/Person-related
        if any(word in input_lower for word in ['biography', 'life', 'person', 'born', 'died', 'career', 'achievements']):
            return ['Introduction', 'Early Life', 'Career', 'Major Achievements', 'Personal Life', 'Legacy', 'Conclusion']
        
        # Technical/Technology-related
        elif any(word in input_lower for word in ['technology', 'technical', 'software', 'system', 'development', 'programming']):
            return ['Introduction', 'Technical Overview', 'Current State', 'Implementation', 'Analysis', 'Future Prospects', 'Conclusion']
        
        # Business/Market-related
        elif any(word in input_lower for word in ['business', 'market', 'company', 'financial', 'economy', 'strategy']):
            return ['Introduction', 'Market Overview', 'Current Situation', 'Analysis', 'Strategic Recommendations', 'Conclusion']
        
        # Research/Study-related
        elif any(word in input_lower for word in ['research', 'study', 'analysis', 'investigation', 'findings']):
            return ['Introduction', 'Literature Review', 'Methodology', 'Findings', 'Discussion', 'Conclusion']
        
        # Health/Medical-related
        elif any(word in input_lower for word in ['health', 'medical', 'disease', 'treatment', 'medicine', 'healthcare']):
            return ['Introduction', 'Background', 'Current Understanding', 'Treatment Options', 'Future Directions', 'Conclusion']
        
        # Education-related
        elif any(word in input_lower for word in ['education', 'learning', 'school', 'university', 'teaching', 'curriculum']):
            return ['Introduction', 'Current State', 'Challenges', 'Best Practices', 'Recommendations', 'Conclusion']
        
        # Default general sections
        else:
            return ['Introduction', 'Background', 'Current Situation', 'Analysis', 'Key Findings', 'Recommendations', 'Conclusion']

    def generate_topic_title(self, user_input, ai_assistant):
        """Use AI to generate a concise, professional topic title from user input"""
        title_prompt = f"""
        You are a professional report title generator. Given the following user input/description, create a concise, professional title for a report.
        
        User Input: "{user_input}"
        
        Instructions:
        - Create a clear, concise title (maximum 8 words)
        - Make it professional and suitable for a business/academic report
        - Focus on the main topic or subject matter
        - Do NOT include words like "Report", "Analysis", "Study" in the title
        - Extract the core subject/topic from the description
        - Use title case (capitalize first letter of each major word)
        
        Generate only the title, nothing else:
        """
        
        try:
            response = ai_assistant.model.generate_content(title_prompt)
            title = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
            title = title.strip()
            
            # Add "Report" suffix if not already present
            if not any(word in title.lower() for word in ['report', 'analysis', 'study', 'research']):
                title += ' Report'
            
            return title
        except Exception as e:
            # Fallback to simple title generation
            sentences = user_input.split('.')
            title_text = sentences[0].strip().title()[:50]  # First sentence, max 50 chars
            if not any(word in title_text.lower() for word in ['report', 'analysis', 'study', 'research']):
                title_text += ' Report'
            return title_text

    def get_current_information(self, topic, ai_assistant):
        """Get current information about the topic using advanced web search"""
        try:
            # Use advanced web search for best results
            search_results = advanced_web_search(topic, ai_assistant.model, num_results=3)
            if search_results:
                search_info = "\n\nCurrent Information from Web Search:\n"
                for item in search_results:
                    summary = item.get('enriched_snippet') or item.get('snippet') or ''
                    search_info += f"\n• {item.get('title', 'No title')}\n  {summary}\n  Source: {item.get('link', 'No link')}\n"
                return search_info
            else:
                return "\n\nNote: Unable to retrieve current web information at this time."
        except Exception as e:
            return f"\n\nNote: Web search unavailable ({str(e)}). Report based on general knowledge."

    def generate_report_content(self, report_data, ai_assistant):
        """Generate detailed report content using AI assistant with web search"""
        
        # Get current information from web search
        current_info = ""
        if report_data.get('topic_only', False):
            # For topic-only requests, always search for current information
            current_info = self.get_current_information(report_data['content'], ai_assistant)
        else:
            # For structured requests, search if the content suggests current/recent information is needed
            search_keywords = ['current', 'recent', 'latest', 'update', 'today', '2024', '2025', 'now']
            if any(keyword in report_data['content'].lower() for keyword in search_keywords):
                # Extract main topic for search
                topic = report_data['content'][:100]  # First 100 chars as topic
                current_info = self.get_current_information(topic, ai_assistant)
        
        # Enhanced content prompt
        content_prompt = f"""
        You are tasked with creating comprehensive, formal content for a professional report.
        
        Topic/Subject: {report_data['content']}
        
        {current_info}
        
        Please create detailed, professional content with the following structure:
        1. Executive Summary
        2. Introduction
        3. Main Content (organized into logical sections)
        4. Analysis/Findings
        5. Conclusions
        6. Recommendations (if applicable)
        
        Instructions:
        - DO NOT repeat the topic name or title in your response - focus on the content
        - If current web information is provided above, incorporate it into your analysis
        - Use formal, professional language suitable for a business or academic report
        - Include specific details, examples, and data where relevant
        - Ensure the content is comprehensive and well-organized
        - Format with clear headings and subheadings
        - Provide comprehensive coverage of all important aspects
        - Include current trends, developments, and future outlook where applicable
        - Write as if this content will be placed under appropriate section headings
        """
        
        try:
            response = ai_assistant.model.generate_content(content_prompt)
            text = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
            return text.strip()
        except Exception as e:
            return f"Error generating report content: {str(e)}"

    def generate_section_content(self, report_data, ai_assistant, detailed_content):
        """Generate content for each section of the report"""
        section_contents = {}
        
        for section_name in report_data['sections']:
            section_prompt = f"""
            Create detailed content for the '{section_name}' section of a professional report.
            
            Topic/Subject: {report_data['content']}
            
            Instructions for '{section_name}' section:
            - Write 2-3 well-structured paragraphs
            - Use formal, professional language
            - Be specific and detailed
            - Include relevant examples or data if applicable
            - Ensure content is appropriate for this section type
            - DO NOT repeat the topic name or title - focus on substantive content
            - Write as if this will appear under the '{section_name}' heading
            
            Content for {section_name}:
            """
            
            try:
                response = ai_assistant.model.generate_content(section_prompt)
                text = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
                section_contents[section_name] = text.strip()
            except Exception as e:
                section_contents[section_name] = f"Error generating content for {section_name}: {str(e)}"
        
        return section_contents

    def create_pdf_report(self, report_data, ai_assistant, output_path):
        """Create the PDF report"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
            title=report_data['title']
        )
        
        # Story will hold all our content
        story = []
        
        # Create professional title page
        self.create_title_page(story, report_data)
        
        # Generate detailed content using AI
        detailed_content = self.generate_report_content(report_data, ai_assistant)
        
        # Table of Contents (if requested)
        if report_data.get('include_toc', True):
            # Add a formal heading for the Table of Contents
            story.append(Paragraph("Table of Contents", self.styles['SectionHeading']))
            story.append(Spacer(1, 0.3*inch))
            
            # Create a professional table of contents with proper formatting
            toc_data = []
            page_num = 3  # Start from page 3 (after title page and TOC)
            
            for i, section in enumerate(report_data['sections']):
                # Add section without page number and with alignment dots
                toc_entry = [
                    section,
                    '.' * (80 - len(section))
                ]
                toc_data.append(toc_entry)
            
            # Create table with proper styling (only 2 columns now)
            toc_table = Table(toc_data, colWidths=[4*inch, 1.5*inch])
            toc_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('SPACEAFTER', (0, 0), (-1, -1), 8),
            ]))
            
            story.append(toc_table)
            story.append(PageBreak())
        
        # Add main content sections
        section_contents = self.generate_section_content(report_data, ai_assistant, detailed_content)
        
        for i, section_name in enumerate(report_data['sections']):
            # Start each section on a new page with a heading (except the first one)
            if i > 0:  # Don't add PageBreak for the first section
                story.append(PageBreak())
            story.append(Paragraph(section_name, self.styles['SectionHeading']))
            story.append(Spacer(1, 0.1*inch))
            
            # Get content for this section
            section_content = section_contents.get(section_name, f"Content for {section_name} section.")
            
            # Process and add section content
            paragraphs = section_content.split('\n\n')
            for paragraph in paragraphs:
                if paragraph.strip():
                    story.append(Paragraph(paragraph.strip(), self.styles['ReportBody']))
                    story.append(Spacer(1, 0.1*inch))
        
        # Build the PDF
        doc.build(story, onFirstPage=self.create_header_footer, onLaterPages=self.create_header_footer)
        
        return output_path

    def extract_headings(self, content):
        """Extract headings from content for table of contents"""
        headings = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for common heading patterns
            if line.endswith(':') and len(line) > 3 and len(line) < 100:
                headings.append(line[:-1])  # Remove the colon
            elif line.startswith('#'):
                headings.append(line.lstrip('#').strip())
            elif line.isupper() and len(line) > 3 and len(line) < 100:
                headings.append(line.title())
        
        return headings[:10]  # Limit to 10 headings

    def process_content_to_story(self, content, story):
        """Process content text and add to story with proper formatting"""
        lines = content.split('\n')
        current_section = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_section:
                    # Add current section content
                    section_text = ' '.join(current_section)
                    if section_text:
                        story.append(Paragraph(section_text, self.styles['ReportBody']))
                        story.append(Spacer(1, 6))
                    current_section = []
                continue
            
            # Check if line is a heading
            if (line.endswith(':') and len(line) > 3 and len(line) < 100) or \
               (line.startswith('#')) or \
               (line.isupper() and len(line) > 3 and len(line) < 100):
                
                # Add previous section if exists
                if current_section:
                    section_text = ' '.join(current_section)
                    if section_text:
                        story.append(Paragraph(section_text, self.styles['ReportBody']))
                        story.append(Spacer(1, 6))
                    current_section = []
                
                # Add heading
                heading_text = line.rstrip(':').lstrip('#').strip()
                if heading_text.isupper():
                    heading_text = heading_text.title()
                
                story.append(Paragraph(heading_text, self.styles['SectionHeading']))
                story.append(Spacer(1, 6))
            else:
                # Regular content line
                current_section.append(line)
        
        # Add final section
        if current_section:
            section_text = ' '.join(current_section)
            if section_text:
                story.append(Paragraph(section_text, self.styles['ReportBody']))

    def generate_report(self, user_request, ai_assistant):
        """Main method to generate a PDF report"""
        try:
            # Parse the user's request
            report_data = self.parse_report_request(user_request, ai_assistant)
            
            # Create output directory if it doesn't exist
            output_dir = os.path.join(os.getcwd(), 'reports')
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename based on title
            clean_filename = report_data['filename'].replace(' ', '_').replace('/', '_').replace('\\', '_')
            clean_filename = ''.join(c for c in clean_filename if c.isalnum() or c in ('_', '-'))
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{clean_filename}_{timestamp}.pdf"
            output_path = os.path.join(output_dir, filename)
            
            # Create the PDF
            self.create_pdf_report(report_data, ai_assistant, output_path)
            
            return output_path, report_data['title']
            
        except Exception as e:
            return None, f"Error generating report: {str(e)}"

def create_sample_report():
    """Create a sample report for testing"""
    from ai_assistant import SecondBrainAssistant
    
    generator = PDFReportGenerator()
    assistant = SecondBrainAssistant()
    
    sample_request = "/report title: AI Technology Analysis content: Create a comprehensive analysis of artificial intelligence technologies, their current applications, future prospects, and impact on society."
    
    output_path, title = generator.generate_report(sample_request, assistant)
    
    if output_path:
        print(f"Sample report created: {output_path}")
        return output_path
    else:
        print(f"Failed to create sample report: {title}")
        return None

if __name__ == "__main__":
    create_sample_report()
