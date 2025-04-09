#!/usr/bin/env python3
"""
Dictionary Scraper
-----------------
Scrapes definitions and example sentences from multiple dictionary websites
and combines them into a single JSON result.
"""

import asyncio
import json
import sys
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup
import click


class DictionaryScraper:
    """Base class for dictionary scrapers."""
    
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.name = "Base Dictionary"
    
    async def get_definition(self, word: str) -> Dict[str, Any]:
        """Get definition and examples from dictionary."""
        raise NotImplementedError("Subclasses must implement this method")
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean up text from HTML."""
        return " ".join(text.strip().split())
    
    async def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a page, with error handling."""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    print(f"Error fetching {url}: HTTP {response.status}")
                    return None
                html = await response.text()
                return BeautifulSoup(html, 'lxml')
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return None


class MerriamWebsterScraper(DictionaryScraper):
    """Scraper for Merriam-Webster dictionary."""
    
    def __init__(self, session: aiohttp.ClientSession):
        super().__init__(session)
        self.name = "Merriam-Webster"
        self.base_url = "https://www.merriam-webster.com/dictionary/"
    
    async def get_definition(self, word: str) -> Dict[str, Any]:
        """Get definition and examples from Merriam-Webster."""
        try:
            url = f"{self.base_url}{word}"
            soup = await self.fetch_page(url)
            if not soup:
                return {"source": self.name, "error": "Failed to fetch page"}
            
            result = {
                "source": self.name,
                "word": word,
                "url": url,
                "definitions": []
            }
            
            # Find verb/noun/adjective sections
            parts_of_speech_blocks = soup.select(".vg")
            
            if not parts_of_speech_blocks:
                # Fall back to older parsing method if no vg blocks
                return await self._legacy_get_definition(soup, word, url)
            
            # Process each part of speech block
            for pos_block in parts_of_speech_blocks:
                # Get part of speech
                pos_elem = pos_block.select_one(".vd, .important-blue-link")
                word_type = ""
                if pos_elem:
                    word_type = self.clean_text(pos_elem.text).replace("verb", "").strip()
                    # Store raw part of speech
                    if not word_type:
                        # Try to find the href content if it's a link
                        if pos_elem.name == 'a' and 'href' in pos_elem.attrs:
                            href = pos_elem['href']
                            word_type = href.split('/')[-1] if '/' in href else ""
                
                # Find all definition sections (numbered)
                sense_items = pos_block.select(".vg-sseq-entry-item")
                
                # Process each numbered section
                for sense_item in sense_items:
                    # Get sense number if available
                    sense_num = ""
                    sense_label = sense_item.select_one(".vg-sseq-entry-item-label")
                    if sense_label:
                        sense_num = self.clean_text(sense_label.text)
                    
                    # Get letter subsections (a, b, c)
                    subsenses = sense_item.select(".sense.has-sn")
                    
                    # If no subsenses, try to get the main definition
                    if not subsenses:
                        subsenses = [sense_item.select_one(".sense-content")]
                    
                    # Process each subsense
                    for subsense in subsenses:
                        if not subsense:
                            continue
                            
                        # Get letter label if available
                        letter_label = ""
                        letter_elem = subsense.select_one(".letter")
                        if letter_elem:
                            letter_label = self.clean_text(letter_elem.text)
                        
                        # Get definition text
                        definition_text = ""
                        def_elem = subsense.select_one(".dtText")
                        if def_elem:
                            # Remove any colon and leading/trailing whitespace
                            definition_text = self.clean_text(def_elem.text)
                            definition_text = re.sub(r'^:\s*', '', definition_text)
                        
                        # Get examples
                        examples = []
                        example_elems = subsense.select(".ex-sent")
                        for example in example_elems:
                            # Extract only the example text, not the entire block
                            example_text = self.clean_text(example.text)
                            # Clean up any translation or additional content
                            example_text = re.sub(r'<[^>]*>', '', example_text)
                            examples.append(example_text)
                        
                        # Create definition object
                        if definition_text:
                            definition_obj = {
                                "definition": definition_text,
                                "examples": examples,
                                "pos": word_type
                            }
                            
                            # Add sense number and letter if available
                            if sense_num:
                                definition_obj["sense_number"] = sense_num
                            if letter_label:
                                definition_obj["sense_letter"] = letter_label
                                
                            result["definitions"].append(definition_obj)
            
            # If no definitions found with new method, try legacy approach
            if not result["definitions"]:
                return await self._legacy_get_definition(soup, word, url)
                
            return result
                
        except Exception as e:
            return {"source": self.name, "error": str(e), "trace": f"{type(e).__name__} at line {sys.exc_info()[2].tb_lineno}"}
    
    async def _legacy_get_definition(self, soup, word, url):
        """Fall back to legacy definition extraction method."""
        definitions = []
        word_type = ""
        
        # Get part of speech
        part_of_speech = soup.select_one("span.fl")
        if part_of_speech:
            word_type = self.clean_text(part_of_speech.text)
        
        # Find definition sections - improve selector based on the website structure
        def_sections = soup.select("div.sense")
        
        # If no definitions found with direct selector, try alternate selectors
        if not def_sections:
            def_sections = soup.select("span.dt")
        
        for i, section in enumerate(def_sections[:7]):
            # Try multiple possible definition elements
            definition_elem = section.select_one(".dtText") or section.select_one(".dt")
            if not definition_elem and ":" in section.text:
                definition_text = section.text.split(":", 1)[1]
                definition = self.clean_text(definition_text)
            elif definition_elem:
                definition = self.clean_text(definition_elem.text)
            else:
                definition = self.clean_text(section.text)
            
            # Strip numbering from beginning of definitions
            definition = re.sub(r'^\s*\d+\s*[:.)]?\s*', '', definition)
            
            # Find examples - also check for .vis-example selector
            examples = []
            example_elems = section.select(".ex-sent, .t, .vis-example")
            
            for example in example_elems[:3]:
                example_text = self.clean_text(example.text)
                # Remove any "Example:" prefix
                example_text = re.sub(r'^example\s*[:.]\s*', '', example_text, flags=re.IGNORECASE)
                examples.append(example_text)
            
            if definition and not definition.startswith("—"):
                definitions.append({
                    "definition": definition,
                    "examples": examples,
                    "pos": word_type  # Include part of speech
                })
        
        return {
            "source": self.name,
            "word": word,
            "url": url,
            "definitions": definitions
        }


class CambridgeDictionaryScraper(DictionaryScraper):
    """Scraper for Cambridge dictionary."""
    
    def __init__(self, session: aiohttp.ClientSession, language="chinese"):
        super().__init__(session)
        self.name = "Cambridge Dictionary"
        
        # Set base URL and dictionary name based on language
        if language == "chinese":
            self.base_url = "https://dictionary.cambridge.org/dictionary/english-chinese-simplified/"
            self.name = "Cambridge Dictionary (English-Chinese)"
            self.has_translation = True
        elif language == "japanese":
            self.base_url = "https://dictionary.cambridge.org/dictionary/english-japanese/"
            self.name = "Cambridge Dictionary (English-Japanese)"
            self.has_translation = True
        elif language == "korean":
            self.base_url = "https://dictionary.cambridge.org/dictionary/english-korean/"
            self.name = "Cambridge Dictionary (English-Korean)"
            self.has_translation = True
        elif language == "italian":
            self.base_url = "https://dictionary.cambridge.org/dictionary/english-italian/"
            self.name = "Cambridge Dictionary (English-Italian)"
            self.has_translation = True
        else:
            self.base_url = "https://dictionary.cambridge.org/dictionary/english/"
            self.has_translation = False
    
    async def get_definition(self, word: str) -> Dict[str, Any]:
        """Get definition and examples from Cambridge Dictionary."""
        try:
            url = f"{self.base_url}{word}"
            soup = await self.fetch_page(url)
            if not soup:
                return {"source": self.name, "error": "Failed to fetch page"}
            
            definitions = []
            
            # Find all entries (might have multiple word types)
            entries = soup.select(".entry-body__el")
            
            for entry in entries[:2]:  # Process up to 2 main entries
                word_type = ""
                pos_elem = entry.select_one(".pos.dpos")
                if pos_elem:
                    word_type = self.clean_text(pos_elem.text)
                
                # Find all definition blocks within this entry
                def_blocks = entry.select(".def-block, .ddef_block")
                
                for block in def_blocks[:5]:
                    definition_elem = block.select_one(".def, .ddef_d")
                    if definition_elem:
                        definition = self.clean_text(definition_elem.text)
                        
                        # Get translation if available for bilingual dictionaries
                        translation = ""
                        if self.has_translation:
                            trans_elem = block.select_one(".trans.dtrans")
                            if trans_elem:
                                translation = self.clean_text(trans_elem.text)
                        
                        # Find examples
                        examples = []
                        example_elems = block.select(".examp, .dexamp")
                        for example in example_elems[:3]:
                            # Look for English example
                            eng_example = example.select_one(".eg.deg")
                            if eng_example:
                                examples.append(self.clean_text(eng_example.text))
                            else:
                                examples.append(self.clean_text(example.text))
                        
                        def_obj = {
                            "definition": definition,
                            "examples": examples,
                            "pos": word_type
                        }
                        
                        if self.has_translation and translation:
                            def_obj["translation"] = translation
                            
                        definitions.append(def_obj)
            
            return {
                "source": self.name,
                "word": word,
                "url": url,
                "definitions": definitions
            }
                
        except Exception as e:
            return {"source": self.name, "error": str(e), "trace": f"{type(e).__name__} at line {sys.exc_info()[2].tb_lineno}"}


class LongmanDictionaryScraper(DictionaryScraper):
    """Scraper for Longman Dictionary of Contemporary English."""
    
    def __init__(self, session: aiohttp.ClientSession):
        super().__init__(session)
        self.name = "Longman Dictionary"
        self.base_url = "https://www.ldoceonline.com/dictionary/"
    
    async def get_definition(self, word: str) -> Dict[str, Any]:
        """Get definition and examples from Longman Dictionary."""
        try:
            url = f"{self.base_url}{word}"
            soup = await self.fetch_page(url)
            if not soup:
                return {"source": self.name, "error": "Failed to fetch page"}
            
            definitions = []
            word_family = {}
            
            # Get word family if available
            word_fams = soup.select(".wordfams")
            if word_fams:
                fam_items = {}
                for fam in word_fams:
                    pos_spans = fam.select(".pos")
                    word_spans = fam.select(".w, .crossRef.w")
                    
                    current_pos = None
                    for elem in fam.children:
                        if hasattr(elem, 'name'):
                            if elem.name == 'span' and 'pos' in elem.get('class', []):
                                current_pos = self.clean_text(elem.text)
                                if current_pos not in fam_items:
                                    fam_items[current_pos] = []
                            elif (elem.name == 'span' and 'w' in elem.get('class', [])) or \
                                 (elem.name == 'a' and 'crossRef' in elem.get('class', [])):
                                if current_pos and elem.text.strip():
                                    fam_items[current_pos].append(self.clean_text(elem.text))
                
                if fam_items:
                    word_family = fam_items
            
            # Process each dictentry section
            entry_sections = soup.select(".dictentry")
            
            for entry in entry_sections:
                # Get basic information about the word
                headword_info = {}
                
                # Get pronunciation
                pron_elem = entry.select_one(".PRON")
                if pron_elem:
                    headword_info["pronunciation"] = self.clean_text(pron_elem.text)
                
                # Get word frequency
                freq_elems = entry.select(".FREQ")
                if freq_elems:
                    freqs = [self.clean_text(f.get('title', '')) for f in freq_elems]
                    headword_info["frequency"] = freqs
                
                # Get part of speech from main entry
                pos_elem = entry.select_one(".POS")
                entry_pos = ""
                if pos_elem:
                    entry_pos = self.clean_text(pos_elem.text)
                    headword_info["pos"] = entry_pos
                
                # Process each sense/meaning of the word
                sense_blocks = entry.select(".Sense")
                
                for sense_idx, sense in enumerate(sense_blocks, 1):
                    sense_def = {
                        "sense_number": sense_idx,
                        "pos": entry_pos  # Default to entry pos
                    }
                    
                    # Check for sense-specific grammar info
                    gram_elem = sense.select_one(".GRAM")
                    if gram_elem:
                        sense_def["grammar"] = self.clean_text(gram_elem.text.replace('[', '').replace(']', ''))
                    
                    # Get definition 
                    definition_elem = sense.select_one(".DEF")
                    if definition_elem:
                        # Clean up definition - remove reference links but keep their text
                        for ref in definition_elem.select(".defRef"):
                            if ref.string:
                                ref.replace_with(ref.string)
                        
                        sense_def["definition"] = self.clean_text(definition_elem.text)
                        
                        # Find examples
                        examples = []
                        example_elems = sense.select(".EXAMPLE")
                        for example in example_elems:
                            # Clean speaker icons
                            for speaker in example.select(".speaker"):
                                speaker.decompose()
                            
                            # Clean up example - remove COLLOINEXA spans but keep text
                            for collo in example.select(".COLLOINEXA"):
                                if collo.string:
                                    collo.replace_with(collo.string)
                            
                            examples.append(self.clean_text(example.text))
                        
                        sense_def["examples"] = examples
                        
                        # Get grammatical patterns
                        patterns = []
                        pattern_sections = sense.select(".GramExa")
                        for pattern_section in pattern_sections:
                            pattern_form = pattern_section.select_one(".PROPFORM")
                            if pattern_form:
                                pattern = {"pattern": self.clean_text(pattern_form.text)}
                                
                                # Get examples for this pattern
                                pattern_examples = []
                                for ex in pattern_section.select(".EXAMPLE"):
                                    # Clean speaker icons
                                    for speaker in ex.select(".speaker"):
                                        speaker.decompose()
                                    pattern_examples.append(self.clean_text(ex.text))
                                
                                if pattern_examples:
                                    pattern["examples"] = pattern_examples
                                
                                patterns.append(pattern)
                        
                        if patterns:
                            sense_def["grammatical_patterns"] = patterns
                        
                        # Get collocations
                        collocations = []
                        collocation_sections = sense.select(".ColloExa")
                        for coll_section in collocation_sections:
                            coll_phrase = coll_section.select_one(".COLLO")
                            if coll_phrase:
                                collocation = {"phrase": self.clean_text(coll_phrase.text)}
                                
                                # Get gloss/meaning of collocation
                                gloss_elem = coll_section.select_one(".GLOSS")
                                if gloss_elem:
                                    gloss_text = self.clean_text(gloss_elem.text)
                                    # Clean up parentheses if present
                                    gloss_text = re.sub(r'^\s*\(\s*=\s*|\s*\)\s*$', '', gloss_text)
                                    if gloss_text:
                                        collocation["meaning"] = gloss_text
                                
                                # Get examples for this collocation
                                coll_examples = []
                                for ex in coll_section.select(".EXAMPLE"):
                                    # Clean speaker icons
                                    for speaker in ex.select(".speaker"):
                                        speaker.decompose()
                                    coll_examples.append(self.clean_text(ex.text))
                                
                                if coll_examples:
                                    collocation["examples"] = coll_examples
                                
                                collocations.append(collocation)
                        
                        if collocations:
                            sense_def["collocations"] = collocations
                        
                    # Add related words if any
                    related_elem = sense.select_one(".RELATEDWD")
                    if related_elem:
                        related_word = self.clean_text(related_elem.text.replace('→', '').strip())
                        if related_word:
                            sense_def["related_word"] = related_word
                    
                    # Add thesaurus reference if any
                    thes_elem = sense.select_one(".Thesref")
                    if thes_elem:
                        thes_ref = None
                        ref_elem = thes_elem.select_one(".REFHWD")
                        if ref_elem:
                            thes_ref = self.clean_text(ref_elem.text)
                        if thes_ref:
                            sense_def["thesaurus_ref"] = thes_ref
                    
                    # Add only if we have at least a definition
                    if "definition" in sense_def:
                        definitions.append(sense_def)
            
            # Get corpus examples if available
            corpus_examples = []
            corpus_sections = soup.select(".exaGroup")
            
            for corpus_section in corpus_sections:
                title_elem = corpus_section.select_one(".title")
                if title_elem:
                    section_title = self.clean_text(title_elem.text)
                    examples = []
                    
                    for example in corpus_section.select(".exa"):
                        # Clean bullet points and other elements
                        for node in example.select(".neutral"):
                            node.decompose()
                        
                        # Clean up example - preserve highlighted words but remove spans
                        for node in example.select(".NodeW"):
                            if node.string:
                                node.replace_with(f"[{node.string}]")
                        
                        # Remove reference links but keep text
                        for ref in example.select(".defRef"):
                            if ref.string:
                                ref.replace_with(ref.string)
                                
                        examples.append(self.clean_text(example.text))
                    
                    if examples:
                        corpus_examples.append({
                            "title": section_title,
                            "examples": examples
                        })
            
            # Process verb table if available
            verb_forms = {}
            verb_table = soup.select_one("table.verbTable")
            if verb_table:
                rows = verb_table.select("tr")
                for row in rows:
                    form_cell = row.select_one("th")
                    value_cell = row.select_one("td")
                    if form_cell and value_cell:
                        form_name = self.clean_text(form_cell.text)
                        form_value = self.clean_text(value_cell.text)
                        if form_name and form_value:
                            verb_forms[form_name] = form_value
            
            result = {
                "source": self.name,
                "word": word,
                "url": url,
                "definitions": definitions,
            }
            
            if word_family:
                result["word_family"] = word_family
                
            if headword_info:
                result.update(headword_info)
                
            if corpus_examples:
                result["corpus_examples"] = corpus_examples
                
            if verb_forms:
                result["verb_forms"] = verb_forms
                
            return result
                
        except Exception as e:
            return {"source": self.name, "error": str(e), "trace": f"{type(e).__name__} at line {sys.exc_info()[2].tb_lineno}"}





class CombinedDictionaryScraper:
    """Manages multiple dictionary scrapers and combines their results."""
    
    def __init__(self):
        self.scrapers = []
    
    async def initialize(self):
        """Initialize all scrapers with a shared HTTP session."""
        self.session = aiohttp.ClientSession(headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Referer": "https://www.google.com/"
        }, timeout=aiohttp.ClientTimeout(total=30))
        
        # Add dictionary scrapers
        self.scrapers = [
            MerriamWebsterScraper(self.session),
            CambridgeDictionaryScraper(self.session, language="chinese"),
            LongmanDictionaryScraper(self.session),
        ]
    
    async def close(self):
        """Close the HTTP session."""
        if hasattr(self, 'session'):
            await self.session.close()
    
    async def get_word_data(self, word: str) -> Dict[str, Any]:
        """Get dictionary data from all sources."""
        if not self.scrapers:
            await self.initialize()
        
        tasks = [scraper.get_definition(word) for scraper in self.scrapers]
        results = await asyncio.gather(*tasks)
        
        return {
            "word": word,
            "timestamp": datetime.now().isoformat(),
            "sources": results
        }
    
    def get_available_dictionaries(self) -> List[str]:
        """Get names of all available dictionaries."""
        return [scraper.name for scraper in self.scrapers]


@click.command()
@click.argument('word')
@click.option('--output', '-o', help='Output file path for JSON')
@click.option('--dictionary', '-d', multiple=True, help='Specify which dictionaries to use (can be used multiple times)')
def main(word: str, output: Optional[str] = None, dictionary: List[str] = None):
    """Scrape dictionary definitions for a word and output as JSON."""
    async def run():
        scraper = CombinedDictionaryScraper()
        try:
            await scraper.initialize()
            
            # Filter dictionaries if specified
            if dictionary:
                available_dicts = scraper.get_available_dictionaries()
                selected_scrapers = []
                for d in dictionary:
                    # Find any dictionary that contains the specified string (case-insensitive)
                    matching = [s for s in available_dicts if d.lower() in s.lower()]
                    if matching:
                        selected_scrapers.extend(matching)
                
                if selected_scrapers:
                    scraper.scrapers = [s for s in scraper.scrapers if s.name in selected_scrapers]
            
            result = await scraper.get_word_data(word)
            
            # Format the JSON with indentation
            json_result = json.dumps(result, indent=2, ensure_ascii=False)
            
            if output:
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(json_result)
                print(f"Results saved to {output}")
            else:
                print(json_result)
                
        finally:
            await scraper.close()
    
    asyncio.run(run())


if __name__ == "__main__":
    main() 