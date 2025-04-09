#!/usr/bin/env python3
"""
@Author      : Jimmy YJ<leeyujia666@gmail.com>
@Created     : 2025/04/07 13:24  
@Last change : 2025/04/07 13:24  
@ModifiedBy  : Jimmy YJ
@Description : Dictionary GUI Application
@Version     : 0.0.1
@License     : None
"""
 
"""
Dictionary GUI Application
--------------------------
A PyQt6-based graphical interface for the CombineDicts dictionary tool.
"""

import sys
import json
import asyncio
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, 
    QPushButton, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QTextBrowser, QGroupBox, QFormLayout, QSplitter,
    QScrollArea, QFrame, QGridLayout, QStatusBar, QComboBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QFont, QIcon, QPixmap

from dictionary_scraper import CombinedDictionaryScraper, MerriamWebsterScraper, LongmanDictionaryScraper, CambridgeDictionaryScraper

# Worker class for asynchronous dictionary lookups
class DictionaryWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, word, dictionary=None, language=None, search_all=False):
        super().__init__()
        self.word = word
        self.dictionary = dictionary
        self.language = language
        self.search_all = search_all

    async def run_async(self):
        try:
            scraper = CombinedDictionaryScraper()
            await scraper.initialize()
            
            if self.search_all:
                # Search all dictionaries (ensure Cambridge has the right language)
                # First get default Cambridge and remove it
                cambridge_scrapers = [s for s in scraper.scrapers if isinstance(s, CambridgeDictionaryScraper)]
                for s in cambridge_scrapers:
                    scraper.scrapers.remove(s)
                
                # Add Cambridge with selected language
                cambridge_scraper = CambridgeDictionaryScraper(scraper.session, language=self.language or "chinese")
                scraper.scrapers.append(cambridge_scraper)
                
                # Search all dictionaries
                result = await scraper.get_word_data(self.word)
            else:
                # Search specific dictionary
                if self.dictionary.lower() in ["merriam", "merriam-webster", "m", "mw"]:
                    for s in scraper.scrapers:
                        if isinstance(s, MerriamWebsterScraper):
                            result = await s.get_definition(self.word)
                            break
                    else:
                        self.error.emit("Merriam-Webster scraper not found")
                        return
                elif self.dictionary.lower() in ["longman", "l"]:
                    for s in scraper.scrapers:
                        if isinstance(s, LongmanDictionaryScraper):
                            result = await s.get_definition(self.word)
                            break
                    else:
                        self.error.emit("Longman Dictionary scraper not found")
                        return
                elif self.dictionary.lower() in ["cambridge", "c"]:
                    # Create a Cambridge dictionary scraper with the selected language
                    cambridge_scraper = CambridgeDictionaryScraper(scraper.session, language=self.language or "chinese")
                    result = await cambridge_scraper.get_definition(self.word)
                else:
                    self.error.emit(f"Dictionary {self.dictionary} not found")
                    return
                    
            await scraper.close()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.run_async())
            loop.close()
        except Exception as e:
            self.error.emit(str(e))

class DictionaryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CombineDicts Dictionary Tool")
        self.setMinimumSize(800, 600)
        
        # Set up the main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Create the search area
        self.create_search_area()
        
        # Create the results area
        self.create_results_area()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Dictionary worker thread
        self.worker_thread = None
        
        # Dictionary history
        self.search_history = []
        
        # Flag to track if we have results
        self.has_results = False
        
        # Store results data for each dictionary
        self.dictionary_data = {
            "merriam-webster": None,
            "longman": None,
            "cambridge": None
        }
        
        # Current word being searched
        self.current_word = ""
        
    def create_search_area(self):
        """Create the search input area"""
        search_box = QGroupBox("Word Search")
        search_layout = QVBoxLayout()
        
        # Top row with search input and button
        input_row = QHBoxLayout()
        
        # Search input
        self.word_input = QLineEdit()
        self.word_input.setPlaceholderText("Enter a word to search...")
        self.word_input.returnPressed.connect(self.search_all_dictionaries)
        input_row.addWidget(self.word_input, 3)  # Give more space to the input
        
        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_all_dictionaries)
        input_row.addWidget(self.search_button, 1)
        
        search_layout.addLayout(input_row)
        
        # Bottom row with dictionary selectors
        selector_row = QHBoxLayout()
        
        # Dictionary selector - No longer needed as we search all dictionaries
        # but we keep the language selector for Cambridge
        
        # Language selector for Cambridge
        self.lang_selector_label = QLabel("Cambridge Language:")
        selector_row.addWidget(self.lang_selector_label)
        
        self.lang_selector = QComboBox()
        self.lang_selector.addItems(["Chinese", "Japanese", "Korean", "Italian", "English Only"])
        self.lang_selector.currentIndexChanged.connect(self.on_language_changed)
        selector_row.addWidget(self.lang_selector, 2)
        
        search_layout.addLayout(selector_row)
        search_box.setLayout(search_layout)
        self.layout.addWidget(search_box)
        
    def on_language_changed(self):
        """When language is changed and we have results, update Cambridge tab"""
        if self.has_results and self.current_word:
            # Only search Cambridge with the new language
            self.search_cambridge_only()
        
    def create_results_area(self):
        """Create the tabbed results area"""
        self.results_tabs = QTabWidget()
        
        # Tab for Merriam-Webster
        self.merriam_tab = QWidget()
        self.merriam_layout = QVBoxLayout(self.merriam_tab)
        self.merriam_results = QTextBrowser()
        self.merriam_results.setOpenExternalLinks(True)
        self.merriam_layout.addWidget(self.merriam_results)
        self.results_tabs.addTab(self.merriam_tab, "Merriam-Webster")
        
        # Tab for Longman
        self.longman_tab = QWidget()
        self.longman_layout = QVBoxLayout(self.longman_tab)
        self.longman_results = QTextBrowser()
        self.longman_results.setOpenExternalLinks(True)
        self.longman_layout.addWidget(self.longman_results)
        self.results_tabs.addTab(self.longman_tab, "Longman")
        
        # Tab for Cambridge
        self.cambridge_tab = QWidget()
        self.cambridge_layout = QVBoxLayout(self.cambridge_tab)
        self.cambridge_results = QTextBrowser()
        self.cambridge_results.setOpenExternalLinks(True)
        self.cambridge_layout.addWidget(self.cambridge_results)
        self.results_tabs.addTab(self.cambridge_tab, "Cambridge")
        
        # Connect tab change signal
        self.results_tabs.currentChanged.connect(self.on_tab_changed)
        
        self.layout.addWidget(self.results_tabs)
        
    def on_tab_changed(self, index):
        """Handle tab change event"""
        if not self.has_results:
            return
            
        # No need to refresh the content as it's already loaded
        # Just update status bar to inform user
        tab_names = ["Merriam-Webster", "Longman", "Cambridge"]
        if 0 <= index < len(tab_names):
            self.status_bar.showMessage(f"Viewing {tab_names[index]} results for '{self.current_word}'")
            
        # If we switch to Cambridge and the language was changed, maybe refresh
        if index == 2 and self.dictionary_data["cambridge"]:
            # Get language from dictionary data
            source_name = self.dictionary_data["cambridge"].get("source", "")
            if "Chinese" in source_name and self.lang_selector.currentText() != "Chinese":
                self.search_cambridge_only()
            elif "Japanese" in source_name and self.lang_selector.currentText() != "Japanese":
                self.search_cambridge_only()
            elif "Korean" in source_name and self.lang_selector.currentText() != "Korean":
                self.search_cambridge_only()
            elif "Italian" in source_name and self.lang_selector.currentText() != "Italian":
                self.search_cambridge_only()
            elif "English" not in source_name and self.lang_selector.currentText() == "English Only":
                self.search_cambridge_only()
        
    def search_all_dictionaries(self):
        """Search all dictionaries at once"""
        word = self.word_input.text().strip()
        if not word:
            self.status_bar.showMessage("Please enter a word to search")
            return
            
        # Save current word
        self.current_word = word
            
        # Add to search history if not already present
        if word not in self.search_history:
            self.search_history.append(word)
        
        # Get selected language for Cambridge
        selected_lang = self.lang_selector.currentText().lower()
        if selected_lang == "english only":
            selected_lang = "english"
        
        # Update status
        self.status_bar.showMessage(f"Searching for '{word}' in all dictionaries...")
        
        # Clear all results
        self.merriam_results.clear()
        self.longman_results.clear()
        self.cambridge_results.clear()
        
        # Start worker in a separate thread to search all dictionaries
        self.worker = DictionaryWorker(word, "all", selected_lang, search_all=True)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.process_all_results)
        self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
    
    def search_cambridge_only(self):
        """Search only the Cambridge dictionary with current language"""
        if not self.current_word:
            return
            
        # Get selected language for Cambridge
        selected_lang = self.lang_selector.currentText().lower()
        if selected_lang == "english only":
            selected_lang = "english"
        
        # Update status
        self.status_bar.showMessage(f"Updating Cambridge dictionary with language: {selected_lang}...")
        
        # Start worker in a separate thread to search Cambridge only
        self.worker = DictionaryWorker(self.current_word, "cambridge", selected_lang)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.process_cambridge_results)
        self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
    
    def process_all_results(self, result):
        """Process results from all dictionaries"""
        try:
            if "sources" in result:
                # Process individual dictionaries
                for source in result["sources"]:
                    source_name = source.get("source", "Unknown")
                    
                    if "Merriam-Webster" in source_name:
                        self.dictionary_data["merriam-webster"] = source
                        self.display_merriam_results(source)
                    elif "Longman" in source_name:
                        self.dictionary_data["longman"] = source
                        self.display_longman_results(source)
                    elif "Cambridge" in source_name:
                        self.dictionary_data["cambridge"] = source
                        self.display_cambridge_results(source)
                
                # Set results flag
                self.has_results = True
                
                # Show the first tab with results
                self.results_tabs.setCurrentIndex(0)
                
                self.status_bar.showMessage(f"Search completed for '{result.get('word', 'word')}'")
            else:
                self.show_error("Unexpected result format")
            
        except Exception as e:
            self.show_error(f"Error processing results: {str(e)}")
    
    def process_cambridge_results(self, result):
        """Process Cambridge dictionary results only"""
        try:
            self.dictionary_data["cambridge"] = result
            self.display_cambridge_results(result)
            self.status_bar.showMessage(f"Cambridge dictionary updated with new language")
        except Exception as e:
            self.show_error(f"Error processing Cambridge results: {str(e)}")
        
    def display_merriam_results(self, result):
        """Display the Merriam-Webster dictionary results"""
        word = result.get("word", "Unknown")
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 10px; }}
                h1 {{ color: #2C3E50; }}
                h2 {{ color: #C0392B; margin-top: 20px; }}
                .pos {{ font-weight: bold; color: #C0392B; text-transform: uppercase; }}
                .sense-num {{ font-weight: bold; }}
                .sense-letter {{ font-weight: bold; }}
                .definition {{ margin-left: 20px; margin-bottom: 10px; }}
                .examples {{ margin-left: 40px; color: #7F8C8D; font-style: italic; }}
                .example {{ margin-bottom: 5px; }}
                .url {{ color: #3498DB; }}
            </style>
        </head>
        <body>
            <h1>Merriam-Webster Definition: "{word}"</h1>
            <p class="url"><a href="{result.get('url', '#')}">View on Merriam-Webster</a></p>
        """
        
        # Group definitions by part of speech
        pos_groups = {}
        for definition in result.get("definitions", []):
            pos = definition.get("pos", "Other")
            if pos not in pos_groups:
                pos_groups[pos] = []
            pos_groups[pos].append(definition)
            
        # Add each part of speech group
        for pos, definitions in pos_groups.items():
            html += f'<h2 class="pos">{pos}</h2>'
            
            # Track current sense number
            current_sense = None
            
            for definition in definitions:
                sense_num = definition.get("sense_number", "")
                sense_letter = definition.get("sense_letter", "")
                
                html += f'<div class="definition">'
                
                # Only show sense number if it's different from the previous one
                if sense_num != current_sense:
                    current_sense = sense_num
                    if sense_num:
                        html += f'<p><span class="sense-num">{sense_num}.</span> '
                    else:
                        html += '<p>'
                else:
                    html += '<p style="margin-left: 20px;">'
                    
                # Add sense letter if available
                if sense_letter:
                    html += f'<span class="sense-letter">{sense_letter}.</span> '
                    
                # Add definition text
                html += f'{definition.get("definition", "")}</p>'
                
                # Add examples
                if "examples" in definition and definition["examples"]:
                    html += f'<div class="examples">'
                    for example in definition["examples"]:
                        html += f'<p class="example">· {example}</p>'
                    html += '</div>'
                
                html += '</div>'
                
        html += """
        </body>
        </html>
        """
        
        self.merriam_results.setHtml(html)
        
    def display_longman_results(self, result):
        """Display the Longman dictionary results with all its enhanced features"""
        word = result.get("word", "Unknown")
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 10px; }}
                h1 {{ color: #2C3E50; }}
                h2 {{ color: #8E44AD; margin-top: 20px; }}
                h3 {{ color: #16A085; margin-top: 15px; }}
                .pos {{ font-style: italic; color: #7F8C8D; }}
                .grammar {{ font-weight: bold; color: #E67E22; }}
                .definition {{ margin-left: 20px; margin-bottom: 10px; }}
                .examples {{ margin-left: 40px; color: #7F8C8D; font-style: italic; }}
                .example {{ margin-bottom: 5px; }}
                .patterns {{ margin-left: 40px; color: #2980B9; }}
                .pattern {{ margin-bottom: 5px; }}
                .pattern-example {{ margin-left: 20px; color: #7F8C8D; font-style: italic; }}
                .collocation {{ margin-left: 40px; color: #D35400; }}
                .collocation-meaning {{ color: #7F8C8D; }}
                .collocation-example {{ margin-left: 20px; color: #7F8C8D; font-style: italic; }}
                .pronunciation {{ color: #16A085; }}
                .frequency {{ background-color: #E8F8F5; padding: 5px; }}
                .family {{ margin-left: 20px; }}
                .family-pos {{ font-weight: bold; }}
                .corpus {{ background-color: #EFF4FB; padding: 10px; margin-top: 15px; }}
                .corpus-title {{ font-weight: bold; color: #2980B9; }}
                .corpus-example {{ margin-left: 20px; }}
                .highlight {{ font-weight: bold; color: #E74C3C; }}
                .url {{ color: #3498DB; }}
            </style>
        </head>
        <body>
            <h1>Longman Dictionary Definition: "{word}"</h1>
            <p class="url"><a href="{result.get('url', '#')}">View on Longman Dictionary</a></p>
        """
        
        # Add pronunciation and frequency if available
        if "pronunciation" in result:
            html += f'<p class="pronunciation">Pronunciation: {result["pronunciation"]}</p>'
            
        if "frequency" in result:
            html += '<p class="frequency">Frequency: ' + ', '.join(result["frequency"]) + '</p>'
            
        # Add word family if available
        if "word_family" in result and result["word_family"]:
            html += '<h3>Word Family</h3>'
            html += '<div class="family">'
            for pos, words in result["word_family"].items():
                html += f'<p><span class="family-pos">{pos}</span>: {", ".join(words)}</p>'
            html += '</div>'
            
        # Add definitions
        if "definitions" in result and result["definitions"]:
            html += '<h2>Definitions</h2>'
            
            for definition in result["definitions"]:
                sense_num = definition.get("sense_number", "")
                grammar = definition.get("grammar", "")
                pos = definition.get("pos", "")
                
                html += f'<div class="definition">'
                html += f'<p><span class="sense-num">{sense_num}.</span> '
                
                if grammar:
                    html += f'<span class="grammar">[{grammar}]</span> '
                    
                if pos:
                    html += f'<span class="pos">{pos}</span> '
                    
                html += f'{definition.get("definition", "")}</p>'
                
                # Add examples
                if "examples" in definition and definition["examples"]:
                    html += f'<div class="examples">'
                    for example in definition["examples"]:
                        html += f'<p class="example">· {example}</p>'
                    html += '</div>'
                
                # Add grammatical patterns
                if "grammatical_patterns" in definition and definition["grammatical_patterns"]:
                    html += '<div class="patterns">'
                    html += '<p><b>Grammatical Patterns:</b></p>'
                    for pattern in definition["grammatical_patterns"]:
                        html += f'<p class="pattern">◦ {pattern["pattern"]}</p>'
                        if "examples" in pattern and pattern["examples"]:
                            html += f'<p class="pattern-example">{pattern["examples"][0]}</p>'
                    html += '</div>'
                
                # Add collocations
                if "collocations" in definition and definition["collocations"]:
                    html += '<div class="collocation">'
                    html += '<p><b>Collocations:</b></p>'
                    for colloc in definition["collocations"]:
                        html += f'<p class="collocation">◦ {colloc["phrase"]}'
                        if "meaning" in colloc:
                            html += f' <span class="collocation-meaning">({colloc["meaning"]})</span>'
                        html += '</p>'
                        if "examples" in colloc and colloc["examples"]:
                            html += f'<p class="collocation-example">{colloc["examples"][0]}</p>'
                    html += '</div>'
                
                html += '</div>'
                
        # Add corpus examples
        if "corpus_examples" in result and result["corpus_examples"]:
            html += '<h2>Corpus Examples</h2>'
            
            for corpus in result["corpus_examples"]:
                html += '<div class="corpus">'
                html += f'<p class="corpus-title">{corpus["title"]}</p>'
                
                for example in corpus["examples"]:
                    # Highlight the key word by wrapping it in [brackets]
                    highlighted = example.replace('[', '<span class="highlight">').replace(']', '</span>')
                    html += f'<p class="corpus-example">· {highlighted}</p>'
                    
                html += '</div>'
                
        # Add verb forms if available
        if "verb_forms" in result and result["verb_forms"]:
            html += '<h2>Verb Forms</h2>'
            html += '<table border="1" cellpadding="5" style="border-collapse: collapse;">'
            html += '<tr><th>Form</th><th>Word</th></tr>'
            
            for form, word in result["verb_forms"].items():
                html += f'<tr><td>{form}</td><td>{word}</td></tr>'
                
            html += '</table>'
            
        html += """
        </body>
        </html>
        """
        
        self.longman_results.setHtml(html)
        
    def display_cambridge_results(self, result):
        """Display the Cambridge dictionary results"""
        word = result.get("word", "Unknown")
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 10px; }}
                h1 {{ color: #2C3E50; }}
                h2 {{ color: #27AE60; margin-top: 20px; }}
                .pos {{ font-style: italic; color: #7F8C8D; }}
                .definition {{ margin-left: 20px; margin-bottom: 10px; }}
                .examples {{ margin-left: 40px; color: #7F8C8D; font-style: italic; }}
                .example {{ margin-bottom: 5px; }}
                .translation {{ color: #E74C3C; margin-left: 20px; }}
                .url {{ color: #3498DB; }}
            </style>
        </head>
        <body>
            <h1>Cambridge Dictionary Definition: "{word}"</h1>
            <p class="url"><a href="{result.get('url', '#')}">View on Cambridge Dictionary</a></p>
        """
        
        # Add definitions
        if "definitions" in result and result["definitions"]:
            for i, definition in enumerate(result["definitions"], 1):
                pos = definition.get("pos", "")
                
                html += f'<div class="definition">'
                html += f'<h2>{i}. <span class="pos">{pos}</span></h2>'
                html += f'<p>{definition.get("definition", "")}</p>'
                
                # Add translation if available (for non-English versions)
                if "translation" in definition:
                    html += f'<p class="translation">Translation: {definition["translation"]}</p>'
                
                # Add examples
                if "examples" in definition and definition["examples"]:
                    html += f'<div class="examples">'
                    for example in definition["examples"]:
                        html += f'<p class="example">· {example}</p>'
                    html += '</div>'
                
                html += '</div>'
        else:
            html += '<p>No definitions found.</p>'
            
        html += """
        </body>
        </html>
        """
        
        self.cambridge_results.setHtml(html)
        
    def show_error(self, error_message):
        """Display error message"""
        self.status_bar.showMessage(f"Error: {error_message}")
        print(f"Error: {error_message}")  # Also print to console for debugging

def main():
    app = QApplication(sys.argv)
    
    # Set the application style
    app.setStyle("Fusion")
    
    # Create and show the main window
    window = DictionaryApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 