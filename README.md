# CombineDicts - Dictionary Combination Tool

A Python tool that scrapes multiple English dictionary websites to provide comprehensive word definitions and examples in JSON format.

## Features

- Scrapes definitions and example sentences from multiple dictionary sources:
  - Merriam-Webster Dictionary (Enhanced)
  - Cambridge Dictionary (English)
  - Cambridge Dictionary (English-Chinese)
  - Longman Dictionary of Contemporary English (Enhanced)
- Combines results into a single JSON structure
- Asynchronous requests for faster response times
- Command-line interface for easy usage
- Option to save results to file
- Ability to filter which dictionaries to use
- Improved error handling and detailed tracing
- Part of speech (noun, verb, etc.) included with definitions
- Chinese translations for the Cambridge Dictionary

### Enhanced Longman Dictionary Features

The Longman Dictionary scraper has been enhanced to provide:

- Word family information (related words with different parts of speech)
- Grammatical information and detailed patterns of usage
- Word frequency information
- Collocations with explanations
- Corpus examples showing real-world usage
- Verb tables when available

### Enhanced Merriam-Webster Dictionary Features

The Merriam-Webster Dictionary scraper has been enhanced to provide:

- Proper part of speech categorization (transitive verb, intransitive verb, noun, etc.)
- Structured multi-level definitions with sense numbers and letters (1a, 1b, 2, etc.)
- Clear association between examples and their definitions
- Improved parsing of complex definition structures
- Support for different word forms in the same entry
- Better handling of specialized definition formats

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To look up a word and print the results to the console:

```
python dictionary_scraper.py apple
```

To save the results to a file:

```
python dictionary_scraper.py apple --output apple_definition.json
```

To use only specific dictionaries:

```
python dictionary_scraper.py apple --dictionary merriam --dictionary cambridge
```

### Quick Testing

For a quick test with a summary of the results from all dictionaries:

```
python test_scraper.py combine
```

To test only the enhanced Longman Dictionary features:

```
python test_scraper.py combine longman
```

To test only the enhanced Merriam-Webster Dictionary features:

```
python test_scraper.py combine merriam
```

## Output Format

The tool outputs a JSON object with the following structure:

```json
{
  "word": "camel",
  "timestamp": "2025-04-07T15:30:45.123456",
  "sources": [
    {
      "source": "Merriam-Webster",
      "word": "camel",
      "url": "https://www.merriam-webster.com/dictionary/camel",
      "definitions": [
        {
          "definition": "either of two large ruminant mammals with a humped back, long neck, and cushioned feet",
          "pos": "noun",
          "examples": [
            "They rode camels across the desert."
          ],
          "sense_number": "1",
          "sense_letter": "a"
        }
      ]
    },
    {
      "source": "Longman Dictionary",
      "word": "combine",
      "url": "https://www.ldoceonline.com/dictionary/combine",
      "pronunciation": "kəmˈbaɪn",
      "pos": "verb",
      "frequency": ["Top 3000 spoken words", "Top 2000 written words"],
      "definitions": [
        {
          "sense_number": 1,
          "pos": "verb",
          "grammar": "intransitive, transitive",
          "definition": "if you combine two or more different things, or if they combine, they begin to exist or work together",
          "examples": [
            "Augustine was later to combine elements of this philosophy with the teachings of Christianity.",
            "Diets are most effective when combined with exercise."
          ],
          "grammatical_patterns": [
            {
              "pattern": "combine something with something",
              "examples": [
                "Good carpet wool needs to combine softness with strength."
              ]
            }
          ],
          "collocations": [
            {
              "phrase": "combined effect/effects",
              "meaning": "the result of two or more different things used or mixed together",
              "examples": [
                "The combined effects of the war and the drought resulted in famine."
              ]
            }
          ],
          "related_word": "combination"
        }
      ],
      "corpus_examples": [
        {
          "title": "combine",
          "examples": [
            "Carl has more experience than any of them [combined].",
            "He makes more money than everyone else in the office [combined]."
          ]
        }
      ]
    }
  ]
}
```

## Notes

- This tool is for educational purposes only
- Respect the terms of service of the dictionary websites
- Web scraping may stop working if websites change their structure
- Some websites may block requests that appear automated 