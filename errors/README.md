

### Errors:

    
1. pyexiv2 error
    ```elm
    pyexiv2 Warning: Directory Image, entry 0x0000 has unknown Exif (TIFF) type 0; setting type size 1
    ```

2. pyexiv2 can't read files with cyrillic paths 
    ```elm
    UnicodeDecodeError: 'utf8' codec can't decode byte 0xa7 in position 0: invalid start byte
    ```

3. solving: "PIL.Image.MAX_IMAGE_PIXELS = 933120000" or "PIL.Image.MAX_IMAGE_PIXELS = None"
    ```elm
    PIL\Image.py:2766: DecompressionBombWarning: Image size (150994944 pixels) exceeds limit of 89478485 pixels, could be decompression bomb DOS attack
    ```

4. need to update Pillow
    ```elm
    UserWarning: Possibly corrupt EXIF data.  Expecting to read 264 bytes but only got 0. Skipping tag 37510 " Skipping tag %s" % (size, len(data), tag)
    ```

5. Exiv2 broken exif
    ```elm
    Error: Directory %name% with 12800 entries considered invalid; not read.
    ```

6. error in 'make_timestamp'
    ```elm
    error: 'NoneType' object has no attribute 'timestamp'
    ```

7. error in 'detect_languages', value is not text
    ```elm
    langdetect.lang_detect_exception.LangDetectException: No features in text.
    ```

8. bad exif in photo
    ```elm
    Warning: JPEG format error, rc = 5
    ```


  
