# MetaCopy

![Logo](https://github.com/PratikSonal/MetaCopy/blob/main/Logo.png)

A pure python based cross-platform application utilising Google's Tesseract-OCR to extract text from image. The ultimate copy/paste solution.

**Prerequisites:**
+ Python 3.6+

## Preview
![Alt Text](https://github.com/PratikSonal/MetaCopy/blob/main/Preview.gif)

## Installation

**Windows:**
+ Download and install the relevant version of [tesseract-ocr](https://github.com/UB-Mannheim/tesseract/wiki), keeping the default installation directory.

**Linux:**
+ Install tesseract-ocr with the following command:
```
apt install python3-pil tesseract-ocr libtesseract-dev tesseract-ocr-eng tesseract-ocr-script-latn
```

Install all remaining dependencies with the following command:
```
pip install -r requirements.txt
```

## Usage
+ select capture to take a screen snippet.
+ select upload to use a preexisting file.
