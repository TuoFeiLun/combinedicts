#!/usr/bin/env python3
"""
Test script for the dictionary scraper
"""

import asyncio
import json
import sys
from dictionary_scraper import CombinedDictionaryScraper, LongmanDictionaryScraper, MerriamWebsterScraper

async def test_specific_dictionary(word, dictionary_type="longman"):
    """Run a focused test on a specific dictionary"""
    print(f"Looking up the word '{word}' in {dictionary_type} dictionary...")
    
    # Initialize the scraper
    scraper = CombinedDictionaryScraper()
    try:
        await scraper.initialize()
        
        # Test only the Longman Dictionary if specified
        if dictionary_type.lower() == "longman":
            longman_scraper = None
            for s in scraper.scrapers:
                if isinstance(s, LongmanDictionaryScraper):
                    longman_scraper = s
                    break
            
            if longman_scraper:
                result = await longman_scraper.get_definition(word)
                
                # Save to file
                output_file = f"{word}_longman_definition.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                print(f"✓ Results saved to {output_file}")
                
                # Display detailed results for Longman dictionary
                print("\n=== LONGMAN DICTIONARY RESULTS ===")
                
                # Word family
                if "word_family" in result:
                    print("\n📚 Word Family:")
                    for pos, related_words in result["word_family"].items():
                        print(f"  • {pos}: {', '.join(related_words)}")
                
                # Pronunciation and frequency
                if "pronunciation" in result:
                    print(f"\n🔊 Pronunciation: {result['pronunciation']}")
                
                if "frequency" in result:
                    print(f"📊 Frequency: {', '.join(result['frequency'])}")
                
                # Definitions
                if "definitions" in result and result["definitions"]:
                    print("\n📝 Definitions:")
                    for idx, defn in enumerate(result["definitions"], 1):
                        sense_num = defn.get("sense_number", idx)
                        print(f"\n  {sense_num}. ", end="")
                        
                        if "grammar" in defn:
                            print(f"[{defn['grammar']}] ", end="")
                        
                        if "definition" in defn:
                            print(f"{defn['definition']}")
                        
                        # Examples
                        if "examples" in defn and defn["examples"]:
                            print("     Examples:")
                            for ex in defn["examples"][:2]:  # Limit to 2 examples
                                print(f"     • {ex}")
                        
                        # Grammatical patterns
                        if "grammatical_patterns" in defn and defn["grammatical_patterns"]:
                            print("     Grammatical Patterns:")
                            for pattern in defn["grammatical_patterns"][:2]:  # Limit to 2 patterns
                                print(f"     ◦ {pattern['pattern']}")
                                if "examples" in pattern and pattern["examples"]:
                                    print(f"       {pattern['examples'][0]}")
                        
                        # Collocations
                        if "collocations" in defn and defn["collocations"]:
                            print("     Collocations:")
                            for colloc in defn["collocations"][:2]:  # Limit to 2 collocations
                                colloc_text = f"     ◦ {colloc['phrase']}"
                                if "meaning" in colloc:
                                    colloc_text += f" ({colloc['meaning']})"
                                print(colloc_text)
                                if "examples" in colloc and colloc["examples"]:
                                    print(f"       {colloc['examples'][0]}")
                
                # Corpus examples
                if "corpus_examples" in result and result["corpus_examples"]:
                    print("\n📊 Corpus Examples:")
                    for corpus_section in result["corpus_examples"][:2]:  # Limit to 2 sections
                        print(f"\n  • {corpus_section['title']}:")
                        for example in corpus_section["examples"][:3]:  # Limit to 3 examples
                            print(f"    - {example}")
                
                # Verb forms if available
                if "verb_forms" in result and result["verb_forms"]:
                    print("\n🔄 Verb Forms:")
                    for form, value in result["verb_forms"].items():
                        print(f"  • {form}: {value}")
                
                print("\n=== END OF LONGMAN RESULTS ===")
                
            else:
                print("Longman Dictionary scraper not found!")
        
        # Test Merriam-Webster Dictionary if specified
        elif dictionary_type.lower() in ["merriam", "merriam-webster", "m", "mw"]:
            merriam_scraper = None
            for s in scraper.scrapers:
                if isinstance(s, MerriamWebsterScraper):
                    merriam_scraper = s
                    break
            
            if merriam_scraper:
                result = await merriam_scraper.get_definition(word)
                
                # Save to file
                output_file = f"{word}_merriam_definition.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                print(f"✓ Results saved to {output_file}")
                
                # Display detailed results for Merriam-Webster dictionary
                print("\n=== MERRIAM-WEBSTER DICTIONARY RESULTS ===")
                
                # Definitions grouped by part of speech
                if "definitions" in result and result["definitions"]:
                    # Group definitions by part of speech
                    pos_groups = {}
                    for definition in result["definitions"]:
                        pos = definition.get("pos", "Other")
                        if pos not in pos_groups:
                            pos_groups[pos] = []
                        pos_groups[pos].append(definition)
                    
                    # Display definitions grouped by part of speech
                    for pos, definitions in pos_groups.items():
                        print(f"\n🔠 {pos.upper()}")
                        
                        # Group by sense number
                        current_sense = None
                        for idx, defn in enumerate(definitions):
                            sense_num = defn.get("sense_number", "")
                            sense_letter = defn.get("sense_letter", "")
                            
                            # Format the definition number/letter
                            if sense_num != current_sense:
                                current_sense = sense_num
                                if sense_num:
                                    print(f"\n  {sense_num}. ", end="")
                                else:
                                    print(f"\n  {idx + 1}. ", end="")
                            
                            if sense_letter:
                                print(f"     {sense_letter}. ", end="")
                            elif sense_num == current_sense and sense_num:
                                print(f"     • ", end="")
                                
                            # Print the definition
                            if "definition" in defn:
                                print(f"{defn['definition']}")
                            
                            # Print examples
                            if "examples" in defn and defn["examples"]:
                                print("       Examples:")
                                for ex in defn["examples"][:2]:  # Limit to 2 examples
                                    print(f"       - {ex}")
                
                print("\n=== END OF MERRIAM-WEBSTER RESULTS ===")
                
            else:
                print("Merriam-Webster Dictionary scraper not found!")
        else:
            # Test all dictionaries
            result = await scraper.get_word_data(word)
            
            # Save to file
            output_file = f"{word}_definition.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Results saved to {output_file}")
            
            # Print a summary
            print("\nSummary of results:")
            for source in result["sources"]:
                def_count = len(source.get("definitions", []))
                error = source.get("error", "")
                
                if error:
                    print(f"  - {source['source']}: Error - {error}")
                else:
                    print(f"  - {source['source']}: {def_count} definitions found")
            
            # Print the first definition from each source
            print("\nSample definitions:")
            for source in result["sources"]:
                if "definitions" in source and source["definitions"]:
                    first_def = source["definitions"][0]
                    print(f"\n{source['source']}:")
                    
                    # Handle different formats for different dictionaries
                    if "definition" in first_def:
                        print(f"  Definition: {first_def['definition']}")
                    
                    if "pos" in first_def and first_def["pos"]:
                        print(f"  Part of Speech: {first_def['pos']}")
                    
                    if "examples" in first_def and first_def["examples"]:
                        print(f"  Example: {first_def['examples'][0]}")
                    
                    if "translation" in first_def:
                        print(f"  Translation: {first_def['translation']}")
                    
                    # For Longman specific information
                    if source['source'] == "Longman Dictionary":
                        if "grammatical_patterns" in first_def and first_def["grammatical_patterns"]:
                            pattern = first_def["grammatical_patterns"][0]
                            print(f"  Pattern: {pattern['pattern']}")
                        
                        if "collocations" in first_def and first_def["collocations"]:
                            colloc = first_def["collocations"][0]
                            print(f"  Collocation: {colloc['phrase']}")
    
    finally:
        await scraper.close()

async def test_scraper(word):
    """Run the scraper on a sample word and save the results"""
    print(f"Looking up the word '{word}' in multiple dictionaries...")
    
    # Initialize the scraper
    scraper = CombinedDictionaryScraper()
    try:
        await scraper.initialize()
        result = await scraper.get_word_data(word)
        
        # Save to file
        output_file = f"{word}_definition.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Results saved to {output_file}")
        
        # Print a summary
        print("\nSummary of results:")
        for source in result["sources"]:
            def_count = len(source.get("definitions", []))
            error = source.get("error", "")
            
            if error:
                print(f"  - {source['source']}: Error - {error}")
            else:
                print(f"  - {source['source']}: {def_count} definitions found")
        
        # Print the first definition from each source
        print("\nSample definitions:")
        for source in result["sources"]:
            if "definitions" in source and source["definitions"]:
                first_def = source["definitions"][0]
                print(f"\n{source['source']}:")
                print(f"  Definition: {first_def.get('definition', '(No definition text)')}")
                if "pos" in first_def and first_def["pos"]:
                    print(f"  Part of Speech: {first_def['pos']}")
                if first_def.get("examples"):
                    print(f"  Example: {first_def['examples'][0]}")
                if "translation" in first_def:
                    print(f"  Translation: {first_def['translation']}")
    
    finally:
        await scraper.close()

if __name__ == "__main__":
    # Get word from command line or use default
    word = sys.argv[1] if len(sys.argv) > 1 else "combine"
    
    # Check for specific dictionary mode
    if len(sys.argv) > 2:
        dict_type = sys.argv[2].lower()
        if dict_type in ["longman", "l"]:
            asyncio.run(test_specific_dictionary(word, "longman"))
        elif dict_type in ["merriam", "merriam-webster", "m", "mw"]:
            asyncio.run(test_specific_dictionary(word, "merriam"))
        else:
            print(f"Unknown dictionary type: {dict_type}")
            print("Available options: longman, merriam")
    else:
        asyncio.run(test_scraper(word)) 